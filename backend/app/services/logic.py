import math
from datetime import datetime, timezone


def inventory_status(prepared_time: datetime, shelf_life_hours: float, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if prepared_time.tzinfo is not None:
        prepared_time = prepared_time.astimezone(timezone.utc).replace(tzinfo=None)
    if now.tzinfo is not None:
        now = now.astimezone(timezone.utc).replace(tzinfo=None)
    remaining = shelf_life_hours - (now - prepared_time).total_seconds() / 3600
    if remaining <= 0:
        return "EXPIRED"
    if remaining <= 2:
        return "EXPIRING"
    if remaining <= 6:
        return "USE_SOON"
    return "FRESH"


def is_safe_until(safe_until: datetime, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    if safe_until.tzinfo is not None:
        safe_until = safe_until.astimezone(timezone.utc).replace(tzinfo=None)
    if now.tzinfo is not None:
        now = now.astimezone(timezone.utc).replace(tzinfo=None)
    return safe_until > now


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def nearest_neighbor(stops: list[dict], start: tuple[float, float] | None = None) -> tuple[list[dict], float]:
    remaining = list(stops)
    ordered = []
    current = start or ((remaining[0]["latitude"], remaining[0]["longitude"]) if remaining else (0, 0))
    distance = 0.0
    while remaining:
        next_stop = min(remaining, key=lambda s: haversine_km(*current, s["latitude"], s["longitude"]))
        distance += haversine_km(*current, next_stop["latitude"], next_stop["longitude"])
        ordered.append(next_stop)
        current = (next_stop["latitude"], next_stop["longitude"])
        remaining.remove(next_stop)
    return ordered, round(distance, 2)
