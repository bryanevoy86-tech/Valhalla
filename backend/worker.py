from app.core.config import get_settings
from redis import Redis
from rq import Worker

if __name__ == "__main__":
    s = get_settings()
    url = s.RQ_REDIS_URL or s.REDIS_URL
    conn = Redis.from_url(url)
    w = Worker([s.RQ_QUEUE_NAME], connection=conn)
    w.work(with_scheduler=True)
