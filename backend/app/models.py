from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False)
    created_at = Column(DateTime, default=utcnow_naive, nullable=False)

class Kitchen(Base):
    __tablename__ = "kitchens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(160), nullable=False)
    latitude = Column(Float, default=12.9716, nullable=False)
    longitude = Column(Float, default=77.5946, nullable=False)

class Ngo(Base):
    __tablename__ = "ngos"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(160), nullable=False)
    latitude = Column(Float, default=12.9716, nullable=False)
    longitude = Column(Float, default=77.5946, nullable=False)

class DailyRecord(Base):
    __tablename__ = "daily_records"
    id = Column(Integer, primary_key=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), index=True, nullable=False)
    date = Column(DateTime, nullable=False)
    meals_prepared = Column(Integer, nullable=False)
    meals_consumed = Column(Integer, nullable=False)
    is_holiday = Column(Boolean, default=False, nullable=False)
    is_exam_day = Column(Boolean, default=False, nullable=False)
    weather_temp = Column(Float, default=22, nullable=False)

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), index=True, nullable=False)
    name = Column(String(120), nullable=False)
    category = Column(String(80), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    prepared_time = Column(DateTime, nullable=False)
    shelf_life_hours = Column(Float, nullable=False)
    storage_temp = Column(Float, default=4, nullable=False)

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    gas_level = Column(Float, nullable=False)
    spoilage_risk = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=utcnow_naive, nullable=False)

class SurplusListing(Base):
    __tablename__ = "surplus_listings"
    id = Column(Integer, primary_key=True)
    kitchen_id = Column(Integer, ForeignKey("kitchens.id"), nullable=False)
    item = Column(String(160), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    safe_until = Column(DateTime, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(30), default="POSTED", index=True, nullable=False)
    accepted_by = Column(Integer, ForeignKey("ngos.id"), nullable=True)
    created_at = Column(DateTime, default=utcnow_naive, nullable=False)

class Pickup(Base):
    __tablename__ = "pickups"
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("surplus_listings.id"), nullable=False)
    ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=False)
    status = Column(String(30), default="ACCEPTED", nullable=False)
    completed_at = Column(DateTime, nullable=True)

class SurplusRejection(Base):
    __tablename__ = "surplus_rejections"
    __table_args__ = (UniqueConstraint("listing_id", "ngo_id"),)
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("surplus_listings.id"), nullable=False)
    ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow_naive, nullable=False)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String(500), nullable=False)
    listing_id = Column(Integer, ForeignKey("surplus_listings.id"), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow_naive, nullable=False)
