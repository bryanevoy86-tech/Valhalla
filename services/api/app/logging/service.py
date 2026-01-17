import logging
from datetime import datetime
from sqlalchemy.orm import Session

from .schemas import LogEntry


class LoggingService:
    def __init__(self, db: Session):
        self.db = db
        # Basic config; in production route to proper handlers/formatters
        logging.basicConfig(level=logging.INFO)

    def log_action(self, user_id: str, action: str, details: str) -> LogEntry:
        ts = datetime.utcnow()
        entry = LogEntry(timestamp=ts, action=action, user_id=user_id, details=details)
        logging.info(f"{ts.isoformat()} - {user_id} - {action}: {details}")
        # Persist to DB or external sink here if needed
        return entry
