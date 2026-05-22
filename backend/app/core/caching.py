import json
import logging
from typing import Any, Optional
import redis
from app.config import settings

logger = logging.getLogger("market-strategist-caching")

redis_client = None
try:
    redis_client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
    redis_client.ping()
except Exception as e:
    logger.warning(
        f"Could not connect to Redis at {settings.REDIS_URL}. "
        f"Caching will fail-safe and be bypassed. Error: {e}"
    )
    redis_client = None

def get_cached_val(key: str) -> Optional[Any]:
    if not redis_client:
        return None
    try:
        val = redis_client.get(key)
        if val:
            return json.loads(val)
    except Exception as e:
        logger.warning(f"Failed to read from cache for key '{key}': {e}")
    return None

def set_cached_val(key: str, val: Any, ttl: int = 300) -> None:
    if not redis_client:
        return
    try:
        redis_client.setex(key, ttl, json.dumps(val))
    except Exception as e:
        logger.warning(f"Failed to write to cache for key '{key}': {e}")

def invalidate_dashboard_cache(company_id: int) -> None:
    if not redis_client:
        return
    try:
        # Delete metrics and events keys
        keys_to_delete = []
        metrics_key = f"dashboard:metrics:company_{company_id}"
        events_pattern = f"dashboard:events:company_{company_id}:*"
        
        # Add metrics key directly
        keys_to_delete.append(metrics_key)
        
        # Scan for matching events keys
        for key in redis_client.scan_iter(events_pattern):
            keys_to_delete.append(key)
            
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)
            logger.info(f"Invalidated {len(keys_to_delete)} cache keys for company {company_id}")
    except Exception as e:
        logger.warning(f"Failed to invalidate dashboard cache for company {company_id}: {e}")
