import unittest

from app.security import InMemoryRateLimiter, RedisRateLimiter


class FakeRedis:
    def __init__(self):
        self.calls = []
        self.result = [1, 0]

    async def eval(self, *args):
        self.calls.append(args)
        return self.result


class SecurityTests(unittest.TestCase):
    def test_in_memory_limiter_allows_then_rejects_with_retry(self):
        import asyncio

        limiter = InMemoryRateLimiter(limit=1, window_seconds=60)

        self.assertIsNone(asyncio.run(limiter.retry_after("client-a")))
        self.assertGreaterEqual(
            asyncio.run(limiter.retry_after("client-a")),
            1,
        )
        self.assertIsNone(asyncio.run(limiter.retry_after("client-b")))

    def test_redis_limiter_uses_shared_atomic_script(self):
        import asyncio

        redis_client = FakeRedis()
        limiter = RedisRateLimiter(redis_client, limit=5, window_seconds=60)

        result = asyncio.run(limiter.retry_after("client-a"))

        self.assertIsNone(result)
        self.assertEqual(len(redis_client.calls), 1)
        self.assertEqual(redis_client.calls[0][1], 1)
        self.assertEqual(redis_client.calls[0][3], 60_000)
        self.assertEqual(redis_client.calls[0][4], 5)

    def test_redis_limiter_returns_retry_after(self):
        import asyncio

        redis_client = FakeRedis()
        redis_client.result = [0, 7]
        limiter = RedisRateLimiter(redis_client, limit=1, window_seconds=60)

        self.assertEqual(asyncio.run(limiter.retry_after("client-a")), 7)


if __name__ == "__main__":
    unittest.main()
