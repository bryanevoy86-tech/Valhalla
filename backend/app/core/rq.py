from __future__ import annotations

from redis import Redis
from rq import Queue

from .config import get_settings


def get_queue() -> Queue:
    s = get_settings()
    url = s.RQ_REDIS_URL or s.REDIS_URL
    conn = Redis.from_url(url)
    return Queue(s.RQ_QUEUE_NAME, connection=conn)
