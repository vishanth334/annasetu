from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_db
from app.models import InventoryItem, Kitchen, SensorReading, User
from app.schemas import InventoryInput, SensorInput
from app.services.logic import inventory_status

router = APIRouter(prefix="/api", tags=["inventory"])


def kitchen_for(db: Session, user: User) -> Kitchen:
    kitchen = db.query(Kitchen).filter(Kitchen.user_id == user.id).first()
    if not kitchen:
        raise HTTPException(404, "No kitchen is linked to this account.")
    return kitchen


def item_response(item: InventoryItem) -> dict:
    return {
        "id": item.id, "name": item.name, "category": item.category,
        "quantity_kg": item.quantity_kg, "prepared_time": item.prepared_time,
        "shelf_life_hours": item.shelf_life_hours, "storage_temp": item.storage_temp,
        "status": inventory_status(item.prepared_time, item.shelf_life_hours),
    }


@router.get("/inventory")
def list_inventory(db: Session = Depends(get_db), user: User = Depends(require_roles("KITCHEN_ADMIN"))):
    kitchen = kitchen_for(db, user)
    return [item_response(item) for item in db.query(InventoryItem).filter(InventoryItem.kitchen_id == kitchen.id).order_by(InventoryItem.prepared_time.desc()).all()]


@router.post("/inventory")
def create_inventory(payload: InventoryInput, db: Session = Depends(get_db), user: User = Depends(require_roles("KITCHEN_ADMIN"))):
    kitchen = kitchen_for(db, user)
    item = InventoryItem(kitchen_id=kitchen.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item_response(item)


@router.put("/inventory/{item_id}")
def update_inventory(item_id: int, payload: InventoryInput, db: Session = Depends(get_db), user: User = Depends(require_roles("KITCHEN_ADMIN"))):
    kitchen = kitchen_for(db, user)
    item = db.query(InventoryItem).filter_by(id=item_id, kitchen_id=kitchen.id).first()
    if not item:
        raise HTTPException(404, "Inventory item not found.")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item_response(item)


@router.delete("/inventory/{item_id}")
def delete_inventory(item_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("KITCHEN_ADMIN"))):
    kitchen = kitchen_for(db, user)
    item = db.query(InventoryItem).filter_by(id=item_id, kitchen_id=kitchen.id).first()
    if not item:
        raise HTTPException(404, "Inventory item not found.")
    db.delete(item)
    db.commit()
    return {"message": "Inventory item deleted."}


@router.post("/sensors")
def sensor_reading(payload: SensorInput, db: Session = Depends(get_db)):
    if not db.query(Kitchen).filter(Kitchen.id == payload.kitchen_id).first():
        raise HTTPException(404, "Kitchen not found.")
    risky = payload.temperature > 8 or payload.humidity > 80 or payload.gas_level > 50
    reading = SensorReading(**payload.model_dump(), spoilage_risk=risky)
    db.add(reading)
    db.commit()
    return {"id": reading.id, "spoilage_risk": risky, "message": "Spoilage risk detected." if risky else "Reading is within safe thresholds."}


@router.post("/quality-check")
async def quality_check(image: UploadFile = File(...), user: User = Depends(require_roles("KITCHEN_ADMIN"))):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(415, "Please upload an image file.")
    content = await image.read(8 * 1024 * 1024 + 1)
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(413, "Image must be 8 MB or smaller.")
    if not content:
        raise HTTPException(400, "The uploaded image is empty.")
    # Mock only: replace this heuristic with a trained YOLOv8/CNN model.
    return {"label": "FRESH", "confidence": 0.72, "mock": True, "message": "Demo result only; connect a YOLOv8/CNN model for real freshness checks."}
