from datetime import datetime, timedelta, timezone

from app.services.logic import is_safe_until


def test_safety_timer_rejects_food_at_or_past_safe_time():
    now = datetime(2026, 5, 1, 12)
    assert is_safe_until(now + timedelta(minutes=1), now)
    assert not is_safe_until(now, now)
    assert not is_safe_until(now - timedelta(seconds=1), now)


def test_safety_timer_accepts_timezone_aware_timestamps():
    now = datetime(2026, 5, 1, 12, tzinfo=timezone.utc)
    assert is_safe_until(now + timedelta(minutes=1), now)
