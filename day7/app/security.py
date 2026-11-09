import math
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Any
from uuid import uuid4


class InMemoryRateLimiter:
    """Sliding-window limiter for single-process development deployments."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def retry_after(self, key: str) -> int | None:
        now = time.monotonic()
        with self._lock:
            requests = self._requests[key]
            cutoff = now - self.window_seconds
            while requests and requests[0] <= cutoff:
                requests.popleft()

            if len(requests) >= self.limit:
                return max(
                    1,
                    math.ceil(self.window_seconds - (now - requests[0])),
                )

            requests.append(now)
            if len(self._requests) > 10_000:
                for client_key, client_requests in list(self._requests.items()):
                    while client_requests and client_requests[0] <= cutoff:
                        client_requests.popleft()
                    if not client_requests:
                        self._requests.pop(client_key, None)
            return None


class RedisRateLimiter:
    """Atomic sliding-window rate limiter shared across API workers."""

    _SCRIPT = """
local time_parts = redis.call('TIME')
local now_ms = (time_parts[1] * 1000) + math.floor(time_parts[2] / 1000)
local window_ms = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local member = ARGV[3]
local cutoff = now_ms - window_ms

redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', cutoff)
local count = redis.call('ZCARD', KEYS[1])

if count >= limit then
    local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
    local retry_ms = tonumber(oldest[2]) + window_ms - now_ms
    return {0, math.ceil(retry_ms / 1000)}
end

redis.call('ZADD', KEYS[1], now_ms, member)
redis.call('PEXPIRE', KEYS[1], window_ms)
return {1, 0}
"""

    def __init__(self, redis_client: Any, limit: int, window_seconds: float) -> None:
        self.redis_client = redis_client
        self.limit = limit
        self.window_seconds = window_seconds

    async def retry_after(self, key: str) -> int | None:
        window_ms = max(1, round(self.window_seconds * 1000))
        result = await self.redis_client.eval(
            self._SCRIPT,
            1,
            f"agent-api-rate:{key}",
            window_ms,
            self.limit,
            uuid4().hex,
        )
        if int(result[0]) == 1:
            return None
        return max(1, int(result[1]))
