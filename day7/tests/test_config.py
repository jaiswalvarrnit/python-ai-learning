import os
import unittest
from unittest.mock import patch

from app.config import Settings


class SettingsTests(unittest.TestCase):
    def test_production_requires_api_authentication_and_redis(self):
        env = {
            "APP_ENV": "production",
            "GEMINI_API_KEY": "test-key",
            "API_ACCESS_TOKEN": "a" * 40,
            "ALLOWED_HOSTS": "api.example.com",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, "REDIS_URL"):
                Settings()

    def test_production_requires_explicit_allowed_hosts(self):
        env = {
            "APP_ENV": "production",
            "GEMINI_API_KEY": "test-key",
            "API_ACCESS_TOKEN": "a" * 40,
            "REDIS_URL": "redis://redis.internal:6379/0",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, "ALLOWED_HOSTS"):
                Settings()

    def test_production_accepts_required_secure_configuration(self):
        env = {
            "APP_ENV": "production",
            "GEMINI_API_KEY": "test-key",
            "API_ACCESS_TOKEN": "a" * 40,
            "REDIS_URL": "redis://redis.internal:6379/0",
            "ALLOWED_HOSTS": "api.example.com",
        }
        with patch.dict(os.environ, env, clear=True):
            configured = Settings()

        self.assertEqual(configured.environment, "production")
        self.assertEqual(configured.allowed_hosts, ["api.example.com"])

    def test_rejects_non_finite_timeout(self):
        env = {
            "GEMINI_API_KEY": "test-key",
            "REQUEST_TIMEOUT": "nan",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, "REQUEST_TIMEOUT"):
                Settings()


if __name__ == "__main__":
    unittest.main()
