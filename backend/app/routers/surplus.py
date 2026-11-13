from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_roles
from app.database import get_db
from app.models import Kitchen, Ngo, Notification, Pickup, SurplusListing, SurplusRejection, User
from app.schemas import SurplusInput
from app.services.logic import haversine_km, is_safe_until
from app.services.notifications import notify_user

router = APIRouter(prefix="/api/surplus", tags=["surplus"])


def organization(db: Session, user: User, model):
    org = db.query(model).filter(model.user_id == user.id).first()
    if not org:
        raise HTTPException(404, "No organization is linked to this account.")
    return org


def listing_dict(db: Session, listing: SurplusListing) -> dict:
    kitchen = db.query(Kitchen).filter(Kitchen.id == listing.kitchen_id).first()
    return {
        "id": listing.id, "kitchen_id": listing.kitchen_id,
        "kitchen_name": kitchen.name if kitchen else "Kitchen",
        "item": listing.item, "quantity_kg": listing.quantity_kg,
        "safe_until": listing.safe_until, "latitude": listing.latitude,
        "longitude": listing.longitude, "status": listing.status,
        "distance_km": None,
    }


@router.post("")
def post_surplus(payload: SurplusInput, db: Session = Depends(get_db), user: User = Depends(require_roles("KITCHEN_ADMIN"))):
    kitchen = organization(db, user, Kitchen)
    if not is_safe_until(payload.safe_until):
        raise HTTPException(422, "This food has passed its safe window and cannot be listed.")
    listing = SurplusListing(kitchen_id=kitchen.id, **payload.model_dump(), status="POSTED")
    db.add(listing)
    db.flush()
    ngos = db.query(Ngo).all()
    ranked = sorted(ngos, key=lambda ngo: haversine_km(payload.latitude, payload.longitude, ngo.latitude, ngo.longitude))
    for ngo in ranked[:5]:
        if ngo.user_id:
            km = haversine_km(payload.latitude, payload.longitude, ngo.latitude, ngo.longitude)
            notify_user(db, ngo.user_id, f"{payload.quantity_kg:g} kg of {payload.item} is available from {kitchen.name} ({km:.1f} km away).", listing.id)
    db.commit()
    return {**listing_dict(db, listing), "notified_ngos": min(len(ranked), 5)}


@router.get("")
def list_surplus(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(SurplusListing).order_by(SurplusListing.created_at.desc())
    if user.role == "NGO":
        ngo = organization(db, user, Ngo)
        query = query.filter(
            or_(
                SurplusListing.status == "POSTED",
                SurplusListing.accepted_by == ngo.id,
            ),
            ~SurplusListing.id.in_(
                db.query(SurplusRejection.listing_id).filter(SurplusRejection.ngo_id == ngo.id)
            ),
        )
        listings = query.all()
        result = []
        for listing in listings:
            if listing.status in {"POSTED", "ACCEPTED"} and not is_safe_until(listing.safe_until):
                listing.status = "EXPIRED"
                pickup = db.query(Pickup).filter_by(listing_id=listing.id).first()
                if pickup:
                    pickup.status = "EXPIRED"
                continue
            item = listing_dict(db, listing)
            item["distance_km"] = round(haversine_km(ngo.latitude, ngo.longitude, listing.latitude, listing.longitude), 2)
            result.append(item)
        db.commit()
        return sorted(result, key=lambda row: row["distance_km"])
    if user.role == "KITCHEN_ADMIN":
        kitchen = organization(db, user, Kitchen)
        query = query.filter(SurplusListing.kitchen_id == kitchen.id)
    return [listing_dict(db, item) for item in query.all()]


@router.post("/{listing_id}/accept")
def accept_surplus(listing_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("NGO"))):
    ngo = organization(db, user, Ngo)
    listing = db.query(SurplusListing).filter_by(id=listing_id).with_for_update().first()
    if not listing:
        raise HTTPException(404, "Surplus listing not found.")
    if db.query(SurplusRejection).filter_by(listing_id=listing.id, ngo_id=ngo.id).first():
        raise HTTPException(409, "Your NGO has already declined this listing.")
    if listing.status != "POSTED" or not is_safe_until(listing.safe_until):
        if listing.status == "POSTED" and not is_safe_until(listing.safe_until):
            listing.status = "EXPIRED"
            db.commit()
        raise HTTPException(409, "This listing is no longer available or has expired.")
    listing.status, listing.accepted_by = "ACCEPTED", ngo.id
    pickup = Pickup(listing_id=listing.id, ngo_id=ngo.id, status="ACCEPTED")
    db.add(pickup)
    kitchen = db.query(Kitchen).filter_by(id=listing.kitchen_id).first()
    if kitchen and kitchen.user_id:
        notify_user(db, kitchen.user_id, f"{ngo.name} accepted your {listing.item} listing.", listing.id)
    db.commit()
    return {"message": "Surplus accepted. Plan a pickup route when ready.", "listing": listing_dict(db, listing)}


@router.post("/{listing_id}/reject")
def reject_surplus(listing_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("NGO"))):
    ngo = organization(db, user, Ngo)
    listing = db.query(SurplusListing).filter_by(id=listing_id).first()
    if not listing or listing.status != "POSTED":
        raise HTTPException(404, "Available listing not found.")
    if not is_safe_until(listing.safe_until):
        listing.status = "EXPIRED"
        db.commit()
        raise HTTPException(409, "This listing has expired.")
    if not db.query(SurplusRejection).filter_by(listing_id=listing.id, ngo_id=ngo.id).first():
        db.add(SurplusRejection(listing_id=listing.id, ngo_id=ngo.id))
        db.commit()
    return {"message": f"Listing declined for {ngo.name}; it remains available to other NGOs."}


@router.post("/{listing_id}/status")
def update_status(
    listing_id: int,
    status: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("NGO")),
):
    ngo = organization(db, user, Ngo)
    listing = db.query(SurplusListing).filter_by(id=listing_id, accepted_by=ngo.id).first()
    if not listing:
        raise HTTPException(404, "This listing is not assigned to your NGO.")
    transitions = {"ACCEPTED": {"PICKED_UP"}, "PICKED_UP": {"DELIVERED"}}
    if status not in transitions.get(listing.status, set()):
        raise HTTPException(409, f"Cannot move a {listing.status} listing to {status}.")
    if status == "PICKED_UP" and not is_safe_until(listing.safe_until):
        listing.status = "EXPIRED"
        pickup = db.query(Pickup).filter_by(listing_id=listing.id, ngo_id=ngo.id).first()
        if pickup:
            pickup.status = "EXPIRED"
        db.commit()
        raise HTTPException(409, "The food's safe window has passed; this pickup cannot proceed.")
    listing.status = status
    pickup = db.query(Pickup).filter_by(listing_id=listing.id, ngo_id=ngo.id).first()
    if pickup:
        pickup.status = status
        if status == "DELIVERED":
            pickup.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    kitchen = db.query(Kitchen).filter_by(id=listing.kitchen_id).first()
    if kitchen and kitchen.user_id:
        notify_user(db, kitchen.user_id, f"Pickup update: {listing.item} is now {status.lower().replace('_', ' ')}.", listing.id)
    db.commit()
    return {"message": f"Listing marked {status}.", "listing": listing_dict(db, listing)}


@router.get("/notifications")
def notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Notification).filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(50).all()
    return [{"id": n.id, "message": n.message, "listing_id": n.listing_id, "is_read": n.is_read, "created_at": n.created_at} for n in rows]


@router.post("/notifications/{notification_id}/read")
def read_notification(notification_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    notification = db.query(Notification).filter_by(id=notification_id, user_id=user.id).first()
    if not notification:
        raise HTTPException(404, "Notification not found.")
    notification.is_read = True
    db.commit()
    return {"message": "Notification marked as read."}
