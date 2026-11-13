from datetime import datetime, timedelta, timezone

from app.services.logic import inventory_status


def test_inventory_expiry_status_boundaries():
    now = datetime(2026, 1, 1, 12)
    assert inventory_status(now - timedelta(hours=12), 12, now) == "EXPIRED"
    assert inventory_status(now - timedelta(hours=10.5), 12, now) == "EXPIRING"
    assert inventory_status(now - timedelta(hours=8), 12, now) == "USE_SOON"
    assert inventory_status(now - timedelta(hours=2), 12, now) == "FRESH"


def test_inventory_status_normalizes_timezone_aware_inputs():
    now = datetime(2026, 1, 1, 12)
    prepared = (now - timedelta(hours=2)).replace(tzinfo=timezone.utc)
    assert inventory_status(prepared, 12, now.replace(tzinfo=timezone.utc)) == "FRESH"
