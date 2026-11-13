from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(pattern="^(KITCHEN_ADMIN|NGO|SUPER_ADMIN)$")
    organization_name: Optional[str] = None
    latitude: float = Field(default=12.9716, ge=-90, le=90)
    longitude: float = Field(default=77.5946, ge=-180, le=180)

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class DailyRecordInput(BaseModel):
    date: datetime
    meals_prepared: int = Field(ge=0)
    meals_consumed: int = Field(ge=0)
    is_holiday: bool = False
    is_exam_day: bool = False
    weather_temp: float = 22

    @model_validator(mode="after")
    def consumed_meals_cannot_exceed_prepared(self):
        if self.meals_consumed > self.meals_prepared:
            raise ValueError("Meals consumed cannot exceed meals prepared.")
        return self

class InventoryInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = "Other"
    quantity_kg: float = Field(gt=0)
    prepared_time: datetime
    shelf_life_hours: float = Field(gt=0)
    storage_temp: float = 4

class SurplusInput(BaseModel):
    item: str = Field(min_length=1, max_length=160)
    quantity_kg: float = Field(gt=0)
    safe_until: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

class SensorInput(BaseModel):
    kitchen_id: int
    temperature: float
    humidity: float = Field(ge=0, le=100)
    gas_level: float = Field(ge=0)
