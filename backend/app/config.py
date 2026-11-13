import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./annasetu.db")
SECRET_KEY = os.getenv("SECRET_KEY", "local-development-secret-change-me")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "1440"))
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
]
CO2_KG_PER_KG_FOOD = float(os.getenv("CO2_KG_PER_KG_FOOD", "2.5"))
COST_SAVED_PER_KG = float(os.getenv("COST_SAVED_PER_KG", "80"))
