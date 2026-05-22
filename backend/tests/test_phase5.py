import os
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Request

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.rate_limiter import RateLimiter
from app.core.caching import get_cached_val, set_cached_val, invalidate_dashboard_cache

class TestPhase5SecurityAndCaching(unittest.TestCase):
    
    @patch("app.core.rate_limiter.redis_client")
    def test_rate_limiter_under_limit(self, mock_redis):
        # Setup mock pipeline
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [5]  # 5 requests, limit is 10
        
        limiter = RateLimiter(limit=10, window=60, limit_by_ip=True)
        
        # Mock request
        request = MagicMock(spec=Request)
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.url = MagicMock()
        request.url.path = "/api/v1/test"
        request.headers = {}
        
        # Run async function using asyncio.run
        asyncio.run(limiter(request))
        
        mock_redis.pipeline.assert_called_once()
        mock_pipe.incr.assert_called_once()
        mock_pipe.expire.assert_called_once()

    @patch("app.core.rate_limiter.redis_client")
    def test_rate_limiter_over_limit(self, mock_redis):
        # Setup mock pipeline
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [11]  # 11 requests, limit is 10
        
        limiter = RateLimiter(limit=10, window=60, limit_by_ip=True)
        
        # Mock request
        request = MagicMock(spec=Request)
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.url = MagicMock()
        request.url.path = "/api/v1/test"
        request.headers = {}
        
        # Should raise HTTPException with 429 status code
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(limiter(request))
            
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertIn("rate limit exceeded", ctx.exception.detail.lower())

    @patch("app.core.rate_limiter.redis_client", None)
    def test_rate_limiter_fail_safe(self):
        # Rate Limiter should bypass silently if redis is down (None)
        limiter = RateLimiter(limit=10, window=60, limit_by_ip=True)
        request = MagicMock(spec=Request)
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.url = MagicMock()
        request.url.path = "/api/v1/test"
        
        # Should execute successfully without throwing exceptions
        asyncio.run(limiter(request))

    @patch("app.core.caching.redis_client")
    def test_caching_get_set(self, mock_redis):
        mock_redis.get.return_value = b'"cached_data"'
        
        val = get_cached_val("my_key")
        self.assertEqual(val, "cached_data")
        mock_redis.get.assert_called_with("my_key")
        
        set_cached_val("my_key", {"status": "ok"}, ttl=100)
        mock_redis.setex.assert_called_with("my_key", 100, '{"status": "ok"}')

    @patch("app.core.caching.redis_client")
    def test_cache_invalidation(self, mock_redis):
        mock_redis.scan_iter.return_value = [b"dashboard:events:company_1:limit_10"]
        
        invalidate_dashboard_cache(company_id=1)
        
        mock_redis.delete.assert_called_once_with(
            "dashboard:metrics:company_1",
            b"dashboard:events:company_1:limit_10"
        )

if __name__ == "__main__":
    unittest.main()
