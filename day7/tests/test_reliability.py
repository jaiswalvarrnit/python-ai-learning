import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.reliability import generate_with_retry


class TemporaryAPIError(Exception):
    code = 503


class DailyQuotaError(Exception):
    code = 429


class ReliabilityTests(unittest.TestCase):
    @patch("app.reliability.time.sleep")
    @patch("app.reliability.random.uniform", return_value=0)
    def test_retries_transient_failure(self, _jitter, _sleep):
        expected = object()
        client = SimpleNamespace(
            models=SimpleNamespace(
                generate_content=Mock(
                    side_effect=[TemporaryAPIError("service unavailable"), expected]
                )
            )
        )

        response = generate_with_retry(
            client=client,
            model="test-model",
            contents=[],
            config=None,
            max_retries=1,
        )

        self.assertIs(response, expected)
        self.assertEqual(client.models.generate_content.call_count, 2)

    @patch("app.reliability.time.sleep")
    def test_does_not_retry_daily_quota_exhaustion(self, sleep):
        client = SimpleNamespace(
            models=SimpleNamespace(
                generate_content=Mock(
                    side_effect=DailyQuotaError(
                        "Daily quota exceeded for this project."
                    )
                )
            )
        )

        with self.assertRaises(DailyQuotaError):
            generate_with_retry(
                client=client,
                model="test-model",
                contents=[],
                config=None,
            )

        client.models.generate_content.assert_called_once()
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
