from datetime import datetime
from typing import List, Optional

from .schemas import UserActivityOut, UserActivityIn


class AnalyticsService:
    def log_user_activity(self, user_id: str, action: str, metadata: Optional[dict] = None) -> UserActivityOut:
        ts = datetime.utcnow().isoformat()
        # Placeholder logging; in production, write to a table or stream
        print(f"[analytics] user={user_id} action={action} ts={ts} meta={metadata}")
        return UserActivityOut(user_id=user_id, action=action, timestamp=ts, metadata=metadata)

    def get_user_activity(self, user_id: str) -> List[UserActivityOut]:
        # Placeholder: return a sample event
        return [UserActivityOut(user_id=user_id, action="login", timestamp=datetime.utcnow().isoformat())]
