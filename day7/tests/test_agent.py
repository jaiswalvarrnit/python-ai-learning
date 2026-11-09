import unittest
from types import SimpleNamespace
from unittest.mock import patch

from google.genai import types

from app import agent


def model_response(function_calls=None, text=None):
    content = types.Content(
        role="model",
        parts=[types.Part(text=text or "Agent action.")],
    )
    usage = SimpleNamespace(
        prompt_token_count=10,
        candidates_token_count=5,
        total_token_count=15,
    )
    return SimpleNamespace(
        candidates=[SimpleNamespace(content=content)],
        function_calls=function_calls or [],
        text=text,
        usage_metadata=usage,
    )


class AgentTests(unittest.TestCase):
    @patch.object(agent, "generate_with_retry")
    def test_runs_tool_and_returns_final_answer(self, generate):
        generate.side_effect = [
            model_response([
                SimpleNamespace(
                    name="calculator",
                    args={"operation": "multiply", "a": 25, "b": 4},
                )
            ]),
            model_response([
                SimpleNamespace(
                    name="final_answer",
                    args={"answer": "25 multiplied by 4 is 100."},
                )
            ]),
        ]

        result = agent.run_agent("What is 25 multiplied by 4?")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["answer"], "25 multiplied by 4 is 100.")
        self.assertEqual(result["steps"], 2)
        self.assertEqual(result["usage"]["input_tokens"], 20)
        self.assertEqual(result["usage"]["output_tokens"], 10)
        self.assertIn("estimated_cost_usd", result)
        self.assertEqual(result["scratchpad"][0]["observation"]["result"], 100)

    @patch.object(agent, "generate_with_retry")
    def test_returns_incomplete_response_with_full_result_shape(self, generate):
        generate.return_value = model_response(text="Plain text answer.")

        result = agent.run_agent("Say hello.")

        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["answer"], "Plain text answer.")
        self.assertEqual(result["steps"], 1)
        self.assertEqual(
            set(result),
            {
                "status",
                "answer",
                "steps",
                "usage",
                "estimated_cost_usd",
                "scratchpad",
            },
        )

    @patch.object(agent, "generate_with_retry", side_effect=TimeoutError("deadline"))
    def test_returns_timeout_result(self, generate):
        result = agent.run_agent("Do a task.")

        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["answer"], "deadline")
        self.assertEqual(result["steps"], 0)

    @patch.object(agent, "generate_with_retry")
    def test_stops_after_maximum_steps(self, generate):
        generate.return_value = model_response([
            SimpleNamespace(
                name="calculator",
                args={"operation": "add", "a": 2, "b": 2},
            )
        ])

        result = agent.run_agent("Calculate 2 + 2.", max_steps=1)

        self.assertEqual(result["status"], "max_steps_reached")
        self.assertEqual(result["steps"], 1)
        self.assertEqual(len(result["scratchpad"]), 1)

    @patch.object(agent, "generate_with_retry")
    def test_tool_failure_is_recorded_for_the_model(self, generate):
        generate.side_effect = [
            model_response([
                SimpleNamespace(
                    name="mock_lookup",
                    args={"customer_id": "C999"},
                )
            ]),
            model_response([
                SimpleNamespace(
                    name="final_answer",
                    args={"answer": "Customer C999 was not found."},
                )
            ]),
        ]

        result = agent.run_agent("Find customer C999.")

        self.assertEqual(result["status"], "completed")
        observation = result["scratchpad"][0]["observation"]
        self.assertFalse(observation["success"])
        self.assertIn("C999", observation["error"])

    def test_rejects_empty_task_and_nonpositive_step_limit(self):
        with self.assertRaises(ValueError):
            agent.run_agent(" ")

        with self.assertRaises(ValueError):
            agent.run_agent("Calculate 2 + 2.", max_steps=0)


class RateLimiterTests(unittest.TestCase):
    def test_waits_until_rolling_window_expires(self):
        limiter = agent.RequestRateLimiter(max_requests=1, window_seconds=0.01)

        limiter.wait()
        limiter.wait()

        self.assertEqual(len(limiter.request_times), 1)

    def test_fails_if_rate_limit_wait_exceeds_timeout(self):
        limiter = agent.RequestRateLimiter(max_requests=1, window_seconds=60)
        limiter.wait()

        with self.assertRaises(TimeoutError):
            limiter.wait(timeout=0)


if __name__ == "__main__":
    unittest.main()
