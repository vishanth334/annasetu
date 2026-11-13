from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import Kitchen, Ngo, User
from app.schemas import LoginInput, RegisterInput

router = APIRouter(prefix="/api/auth", tags=["auth"])


def public_user(user: User, db: Session) -> dict:
    kitchen = db.query(Kitchen).filter(Kitchen.user_id == user.id).first()
    ngo = db.query(Ngo).filter(Ngo.user_id == user.id).first()
    organization = kitchen or ngo
    return {
        "id": user.id, "name": user.name, "email": user.email, "role": user.role,
        "organization_id": organization.id if organization else None,
        "organization_name": organization.name if organization else None,
        "latitude": organization.latitude if organization else None,
        "longitude": organization.longitude if organization else None,
    }


@router.post("/register")
def register(payload: RegisterInput, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists.")
    if payload.role == "SUPER_ADMIN":
        raise HTTPException(400, "Super Admin accounts are created by the system administrator.")
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.flush()
    org_name = (payload.organization_name or payload.name).strip()
    if payload.role == "KITCHEN_ADMIN":
        db.add(Kitchen(user_id=user.id, name=org_name, latitude=payload.latitude, longitude=payload.longitude))
    else:
        db.add(Ngo(user_id=user.id, name=org_name, latitude=payload.latitude, longitude=payload.longitude))
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user), "token_type": "bearer", "user": public_user(user, db)}


@router.post("/login")
def login(payload: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password.")
    return {"access_token": create_access_token(user), "token_type": "bearer", "user": public_user(user, db)}
