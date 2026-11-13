from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_ORIGINS
from app.database import Base, engine
from app.routers import admin, analytics, auth, forecast, inventory, routes, surplus

Base.metadata.create_all(bind=engine)
app = FastAPI(title="AnnaSetu API", description="Food waste prediction, safety monitoring, and redistribution.", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for api_router in (auth.router, forecast.router, inventory.router, surplus.router, routes.router, analytics.router, admin.router):
    app.include_router(api_router)


@app.get("/")
def root():
    return {"name": "AnnaSetu API", "docs": "/docs", "status": "ready"}


@app.get("/health")
def health():
    return {"status": "ok"}
