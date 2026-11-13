from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_db
from app.models import Ngo, Pickup, SurplusListing, User
from app.services.logic import is_safe_until
from app.services.routing import optimize_route

router = APIRouter(prefix="/api/routes", tags=["routes"])


class RouteInput(BaseModel):
    listing_ids: list[int] | None = None
    start_latitude: float | None = None
    start_longitude: float | None = None


@router.post("/plan")
def plan_route(payload: RouteInput, db: Session = Depends(get_db), user: User = Depends(require_roles("NGO"))):
    ngo = db.query(Ngo).filter_by(user_id=user.id).first()
    if not ngo:
        raise HTTPException(404, "No NGO is linked to this account.")
    query = db.query(SurplusListing).filter_by(accepted_by=ngo.id, status="ACCEPTED")
    if payload.listing_ids:
        query = query.filter(SurplusListing.id.in_(payload.listing_ids))
    listings = query.all()
    active_listings = []
    for listing in listings:
        if not is_safe_until(listing.safe_until):
            listing.status = "EXPIRED"
            pickup = db.query(Pickup).filter_by(listing_id=listing.id, ngo_id=ngo.id).first()
            if pickup:
                pickup.status = "EXPIRED"
        else:
            active_listings.append(listing)
    if len(active_listings) != len(listings):
        db.commit()
    listings = active_listings
    stops = [{
        "listing_id": item.id, "item": item.item, "quantity_kg": item.quantity_kg,
        "latitude": item.latitude, "longitude": item.longitude,
    } for item in listings]
    start = None
    if payload.start_latitude is not None and payload.start_longitude is not None:
        start = (payload.start_latitude, payload.start_longitude)
    else:
        start = (ngo.latitude, ngo.longitude)
    ordered, distance, method = optimize_route(stops, start)
    # Estimate urban travel at 25 km/h, plus 10 minutes for handling each stop.
    eta_minutes = round(distance / 25 * 60 + len(ordered) * 10)
    return {"stops": ordered, "total_distance_km": distance, "eta_minutes": eta_minutes, "method": method}
