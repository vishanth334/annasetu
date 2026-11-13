import logging

from sqlalchemy.orm import Session

from app.models import Notification, User

logger = logging.getLogger(__name__)


def notify_user(db: Session, user_id: int, message: str, listing_id: int | None = None) -> None:
    db.add(Notification(user_id=user_id, message=message, listing_id=listing_id))


def send_external_alert_stub(destination: str, message: str) -> None:
    """Twilio SMS/WhatsApp integration point; intentionally sends nothing."""
    logger.info("Twilio stub: would send alert to %s: %s", destination, message)
