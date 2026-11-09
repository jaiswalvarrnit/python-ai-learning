import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main
from app.main import app


class AgentApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_readiness_and_liveness(self):
        readiness = self.client.get("/ready")
        liveness = self.client.get("/health/live")

        self.assertEqual(readiness.status_code, 200)
        self.assertEqual(liveness.json(), {"status": "alive"})

    def test_api_rate_limit_returns_retry_after(self):
        class RejectingLimiter:
            async def retry_after(self, key):
                return 9

        original_limiter = app.state.rate_limiter
        app.state.rate_limiter = RejectingLimiter()
        try:
            response = self.client.post(
                "/agent/run",
                json={"task": "Calculate 2 + 2."},
            )
        finally:
            app.state.rate_limiter = original_limiter

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["Retry-After"], "9")

    @patch("app.main.run_agent")
    def test_agent_endpoint_returns_usage_and_cost(self, run_agent):
        run_agent.return_value = {
            "status": "completed",
            "answer": "The answer is 4.",
            "steps": 2,
            "usage": {
                "input_tokens": 10,
                "output_tokens": 4,
                "total_tokens": 14,
            },
            "estimated_cost_usd": 0.0001,
            "scratchpad": [],
        }

        response = self.client.post(
            "/agent/run",
            json={"task": "Calculate 2 + 2."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "The answer is 4.")
        self.assertEqual(response.json()["usage"]["total_tokens"], 14)
        self.assertTrue(response.headers["X-Request-ID"])

    @patch("app.main.run_agent")
    def test_agent_timeout_maps_to_gateway_timeout(self, run_agent):
        run_agent.return_value = {
            "status": "timeout",
            "answer": "deadline exceeded",
            "steps": 0,
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            },
            "estimated_cost_usd": 0.0,
            "scratchpad": [],
        }

        response = self.client.post(
            "/agent/run",
            json={"task": "Run a slow task."},
        )

        self.assertEqual(response.status_code, 504)

    def test_agent_endpoint_validates_task(self):
        response = self.client.post("/agent/run", json={"task": ""})

        self.assertEqual(response.status_code, 422)
        self.assertNotIn("input", response.text)

    def test_agent_endpoint_rejects_oversized_request_body(self):
        response = self.client.post(
            "/agent/run",
            content=b"x" * (main.settings.max_request_body_bytes + 1),
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(response.status_code, 413)
        self.assertTrue(response.headers["X-Request-ID"])

    @patch("app.main.run_agent")
    def test_requires_bearer_token_when_configured(self, run_agent):
        token = "test-api-token-that-is-at-least-32-characters"
        run_agent.return_value = {
            "status": "completed",
            "answer": "The answer is 4.",
            "steps": 1,
            "usage": {
                "input_tokens": 1,
                "output_tokens": 1,
                "total_tokens": 2,
            },
            "estimated_cost_usd": 0.0,
            "scratchpad": [],
        }

        with patch.object(main.settings, "api_access_token", token):
            unauthorized = self.client.post(
                "/agent/run",
                json={"task": "Calculate 2 + 2."},
            )
            authorized = self.client.post(
                "/agent/run",
                json={"task": "Calculate 2 + 2."},
                headers={"Authorization": f"Bearer {token}"},
            )

        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(authorized.status_code, 200)
        run_agent.assert_called_once()


if __name__ == "__main__":
    unittest.main()
