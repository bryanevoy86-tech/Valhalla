from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from app.db.base_class import Base
import datetime


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)          # "api", "worker", "weweb", "heimdall", etc.
    location = Column(String)                        # module/function/file hint
    severity = Column(String, default="error")       # error / warn / critical

    message = Column(String, nullable=False)         # short message
    stacktrace = Column(Text)                        # full traceback or error context
    context = Column(Text)                           # JSON/text context

    resolved = Column(Boolean, default=False)
    resolved_note = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime)
