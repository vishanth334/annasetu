from datetime import datetime, timedelta

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_roles
from app.database import get_db
from app.models import DailyRecord, Kitchen, User
from app.schemas import DailyRecordInput

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


class ForecastInput(BaseModel):
    records: list[DailyRecordInput] | None = None


def kitchen_for_user(db: Session, user: User) -> Kitchen:
    kitchen = db.query(Kitchen).filter(Kitchen.user_id == user.id).first()
    if not kitchen:
        raise HTTPException(404, "No kitchen is linked to this account.")
    return kitchen


@router.post("/records")
def add_record(payload: DailyRecordInput, db: Session = Depends(get_db), user: User = Depends(require_roles("KITCHEN_ADMIN"))):
    kitchen = kitchen_for_user(db, user)
    record = DailyRecord(kitchen_id=kitchen.id, **payload.model_dump())
    db.add(record)
    db.commit()
    return {"id": record.id, "message": "Daily record saved."}


@router.post("")
def get_forecast(
    payload: ForecastInput | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("KITCHEN_ADMIN", "SUPER_ADMIN")),
):
    kitchen = kitchen_for_user(db, user) if user.role != "SUPER_ADMIN" else db.query(Kitchen).first()
    if not kitchen:
        raise HTTPException(404, "No kitchen data is available yet.")
    records = payload.records if payload and payload.records else db.query(DailyRecord).filter(
        DailyRecord.kitchen_id == kitchen.id
    ).order_by(DailyRecord.date).all()
    if len(records) < 7:
        raise HTTPException(422, "At least 7 daily records are required. Seed demo data or add more records.")
    rows = []
    for r in records:
        dt = r.date
        rows.append({
            "day": dt.weekday(), "month": dt.month, "holiday": r.is_holiday,
            "exam": r.is_exam_day, "temp": r.weather_temp,
            "consumed": r.meals_consumed, "prepared": r.meals_prepared,
        })
    frame = pd.DataFrame(rows)
    features = ["day", "month", "holiday", "exam", "temp"]
    model = RandomForestRegressor(n_estimators=120, random_state=42, min_samples_leaf=2)
    model.fit(frame[features], frame["consumed"])
    prepared_model = RandomForestRegressor(n_estimators=100, random_state=42, min_samples_leaf=2)
    prepared_model.fit(frame[features], frame["prepared"])
    last_date = max(r.date for r in records).date()
    predictions = []
    for offset in range(1, 8):
        target = last_date + timedelta(days=offset)
        x = pd.DataFrame([{
            "day": target.weekday(), "month": target.month, "holiday": False,
            "exam": False, "temp": 24.0,
        }])
        demand = max(0, round(float(model.predict(x[features])[0])))
        recommended = max(demand, round(float(prepared_model.predict(x[features])[0])))
        predictions.append({
            "date": target.isoformat(), "predicted_meals": demand,
            "recommended_to_cook": recommended,
            "expected_surplus": max(0, recommended - demand),
        })
    return {"kitchen_id": kitchen.id, "model": "RandomForestRegressor", "forecast": predictions}
