import logging
import time
from fastapi import Request, HTTPException, status
from jose import jwt
from app.config import settings
from app.core.security import ALGORITHM
import redis

logger = logging.getLogger("market-strategist-rate-limiter")

# Initialize Redis client
redis_client = None
try:
    redis_client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
    # Test connection
    redis_client.ping()
except Exception as e:
    logger.warning(
        f"Could not connect to Redis at {settings.REDIS_URL}. "
        f"Rate limiting will fail-safe and be bypassed. Error: {e}"
    )
    redis_client = None

class RateLimiter:
    def __init__(self, limit: int, window: int = 60, limit_by_ip: bool = True):
        self.limit = limit
        self.window = window
        self.limit_by_ip = limit_by_ip

    async def __call__(self, request: Request):
        if not redis_client:
            return

        # Determine identifier: default to client host IP
        key_identifier = request.client.host if request.client else "unknown_ip"
        
        # If limiting by user and request contains Authorization header
        if not self.limit_by_ip:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    payload = jwt.decode(
                        token, settings.SECRET_KEY, algorithms=[ALGORITHM]
                    )
                    user_id = payload.get("sub")
                    if user_id:
                        key_identifier = f"user_{user_id}"
                except Exception:
                    # Ignore JWT validation/decode errors, fallback to client IP
                    pass

        key = f"rate_limit:{request.url.path}:{key_identifier}"

        try:
            # Simple window algorithm based on time blocks
            current_window = int(time.time() / self.window)
            redis_key = f"{key}:{current_window}"
            
            pipe = redis_client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, self.window)
            result = pipe.execute()
            
            requests_count = result[0]
            if requests_count > self.limit:
                logger.warning(f"Rate limit exceeded for key {key}. Requests: {requests_count}/{self.limit}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too Many Requests: Rate limit exceeded. Please try again later."
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Redis rate limiter error, bypassing check: {e}")
            return
