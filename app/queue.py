import json
from redis import Redis
from app.config import settings


def enqueue_incident(incident_id: str) -> bool:
    try:
        client = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=1)
        client.rpush("aimsp:incident_queue", json.dumps({"incident_id": incident_id}))
        return True
    except Exception:
        return False
