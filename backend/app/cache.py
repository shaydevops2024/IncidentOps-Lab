import redis
from .config import REDIS_URL

r = redis.from_url(REDIS_URL)

def set_status(service, value):
    r.set(service, value)

def get_status(service):
    return r.get(service)
