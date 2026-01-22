from redis import Redis
from rq import Queue
from .config import settings

def get_redis_connection():
    return Redis.from_url(settings.redis_url)

def get_queue(name="default"):
    conn = get_redis_connection()
    return Queue(name, connection=conn)
