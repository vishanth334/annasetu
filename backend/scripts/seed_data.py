"""Create demo users, organizations, and six months of synthetic kitchen records."""
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import DailyRecord, Kitchen, Ngo, User


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        kitchens = [
            ("Greenfield College Mess", "kitchen@annasetu.demo", 12.9716, 77.5946),
            ("City Tech Canteen", "canteen@annasetu.demo", 12.9352, 77.6245),
            ("Sunrise Catering", "caterer@annasetu.demo", 12.9980, 77.5600),
        ]
        for name, email, lat, lng in kitchens:
            user = db.query(User).filter_by(email=email).first()
            if not user:
                user = User(name=name, email=email, password_hash=hash_password("demo1234"), role="KITCHEN_ADMIN")
                db.add(user)
                db.flush()
                kitchen = Kitchen(user_id=user.id, name=name, latitude=lat, longitude=lng)
                db.add(kitchen)
                db.flush()
            else:
                kitchen = db.query(Kitchen).filter_by(user_id=user.id).first()
            if kitchen and not db.query(DailyRecord).filter_by(kitchen_id=kitchen.id).first():
                rng = random.Random(kitchen.id * 83)
                today = datetime.now(timezone.utc).replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
                for day_offset in range(180, 0, -1):
                    dt = today - timedelta(days=day_offset)
                    baseline = 430 + (60 if dt.weekday() < 5 else -120)
                    holiday = rng.random() < 0.035
                    exam = rng.random() < 0.09
                    demand = max(80, baseline + (70 if exam else 0) - (170 if holiday else 0) + rng.randint(-55, 55))
                    prepared = max(demand, demand + rng.randint(10, 90))
                    db.add(DailyRecord(
                        kitchen_id=kitchen.id, date=dt, meals_prepared=prepared,
                        meals_consumed=min(prepared, demand), is_holiday=holiday,
                        is_exam_day=exam, weather_temp=round(rng.uniform(18, 35), 1),
                    ))
        ngo_specs = [
            ("Helping Hands NGO", "ngo@annasetu.demo", 12.9650, 77.6100),
            ("Community Plate", "ngo2@annasetu.demo", 12.9400, 77.5700),
        ]
        for name, email, lat, lng in ngo_specs:
            user = db.query(User).filter_by(email=email).first()
            if not user:
                user = User(name=name, email=email, password_hash=hash_password("demo1234"), role="NGO")
                db.add(user)
                db.flush()
                db.add(Ngo(user_id=user.id, name=name, latitude=lat, longitude=lng))
        if not db.query(User).filter_by(email="admin@annasetu.demo").first():
            db.add(User(name="AnnaSetu Super Admin", email="admin@annasetu.demo", password_hash=hash_password("demo1234"), role="SUPER_ADMIN"))
        db.commit()
        print("Demo data ready. Login password for all demo users: demo1234")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
