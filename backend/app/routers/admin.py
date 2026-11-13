from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_db
from app.models import Kitchen, Ngo, User
from app.routers.analytics import summary

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(require_roles("SUPER_ADMIN"))):
    return {
        "impact": summary(db),
        "kitchens": [
            {"id": item.id, "name": item.name, "latitude": item.latitude, "longitude": item.longitude}
            for item in db.query(Kitchen).order_by(Kitchen.name).all()
        ],
        "ngos": [
            {"id": item.id, "name": item.name, "latitude": item.latitude, "longitude": item.longitude}
            for item in db.query(Ngo).order_by(Ngo.name).all()
        ],
    }
