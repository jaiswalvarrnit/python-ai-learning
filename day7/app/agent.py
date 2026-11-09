# agent.py

import logging
import time
from collections import deque
from threading import Lock

from google import genai
from google.genai import types

from app.config import settings
from app.context_manager import ContextManager
from app.cost_tracker import track_cost
from app.reliability import generate_with_retry
from app.tools import AVAILABLE_TOOLS


MODEL = settings.model
MAX_STEPS = settings.max_agent_steps

client = genai.Client(
    api_key=settings.gemini_api_key,
    http_options=types.HttpOptions(
        timeout=int(settings.request_timeout * 1000),
        retry_options=types.HttpRetryOptions(attempts=1),
    )
)

logger = logging.getLogger("agent")


class RequestRateLimiter:
    """Limit Gemini requests made by this process in a rolling time window."""

    def __init__(self, max_requests: int, window_seconds: float = 60.0):
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times = deque()
        self.lock = Lock()

    def wait(self, timeout: float | None = None):
        """Wait until another request is allowed."""

        while True:
            with self.lock:
                now = time.monotonic()

                while (
                    self.request_times
                    and now - self.request_times[0] >= self.window_seconds
                ):
                    self.request_times.popleft()

                if len(self.request_times) < self.max_requests:
                    self.request_times.append(now)
                    return

                delay = (
                    self.window_seconds
                    - (now - self.request_times[0])
                )

                if timeout is not None and delay > timeout:
                    raise TimeoutError(
                        "Agent execution deadline exceeded while waiting "
                        "for the request rate limit."
                    )

            logger.info(
                "Gemini rate limit reached; waiting %.1f seconds.",
                delay,
            )
            time.sleep(delay)


RATE_LIMITER = RequestRateLimiter(settings.gemini_requests_per_minute)


def create_tool_declarations():

    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="calculator",
                    description="Perform arithmetic calculations.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "operation": {
                                "type": "STRING",
                                "enum": [
                                    "add", "subtract",
                                    "multiply", "divide",
                                    "modulo", "power",
                                    "floor_divide"
                                ]
                            },
                            "a": {"type": "NUMBER"},
                            "b": {"type": "NUMBER"}
                        },
                        "required": ["operation", "a", "b"]
                    }
                ),

                types.FunctionDeclaration(
                    name="mock_lookup",
                    description="Find customer details using customer ID.",
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "customer_id": {"type": "STRING"}
                        },
                        "required": ["customer_id"]
                    }
                ),

                types.FunctionDeclaration(
                    name="text_analyzer",
                    description=(
                        "Analyze text and return character, word, unique word, "
                        "line, digit, vowel, punctuation, uppercase, and lowercase statistics."
                    ),
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "text": {"type": "STRING"}
                        },
                        "required": ["text"]
                    }
                ),

                types.FunctionDeclaration(
                    name="final_answer",
                    description=(
                        "Call this when you have completed the task. "
                        "Provide the final answer to the user."
                    ),
                    parameters={
                        "type": "OBJECT",
                        "properties": {
                            "answer": {"type": "STRING"}
                        },
                        "required": ["answer"]
                    }
                )
            ]
        )
    ]


TOOL_DECLARATIONS = create_tool_declarations()

SYSTEM_INSTRUCTION = """
You are a helpful AI agent.

You have three operational tools:
1. calculator: perform arithmetic.
2. mock_lookup: retrieve customer information.
3. text_analyzer: analyze text.

You also have a final_answer tool.

Rules:
- Use tools when the task requires them.
- You may call multiple tools to complete a task.
- Use the results of previous tools when deciding the next action.
- Never invent customer information or tool results.
- If a tool fails, understand the error and decide whether
  you can recover or should report the failure.
- Do not repeatedly call a tool with identical failing arguments.
- Always finish by calling final_answer.
- Do not call final_answer until the task is complete
  or you have determined that it cannot be completed.
"""


def log_scratchpad(scratchpad):
    """Log only action names, not user data, arguments, or tool results."""
    actions = [entry.get("action", "unknown") for entry in scratchpad]
    logger.info("Agent trace contains %s actions: %s", len(actions), actions)


def run_agent(user_task: str, max_steps: int = MAX_STEPS):
    if not isinstance(user_task, str) or not user_task.strip():
        raise ValueError("user_task must be a non-empty string.")
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1.")

    logger.info("=" * 60)
    logger.info("New agent task received.")

    # Conversation history sent to Gemini
    context = ContextManager(user_task)

    # Internal record of actions and observations
    scratchpad = []
    step_count = 0
    deadline = time.monotonic() + settings.agent_deadline_seconds
    usage_totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }
    estimated_cost_usd = 0.0

    def build_result(status: str, answer: str) -> dict:
        return {
            "status": status,
            "answer": answer,
            "steps": step_count,
            "usage": usage_totals.copy(),
            "estimated_cost_usd": round(estimated_cost_usd, 8),
            "scratchpad": scratchpad,
        }

    while step_count < max_steps:

        logger.info("AGENT STEP %s/%s", step_count + 1, max_steps)

        try:
            response = generate_with_retry(
                client=client,
                model=MODEL,
                contents=context.get_contents(),
                config=types.GenerateContentConfig(
                    tools=TOOL_DECLARATIONS,
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0,
                ),
                before_attempt=lambda: RATE_LIMITER.wait(
                    timeout=max(0.0, deadline - time.monotonic())
                ),
                deadline=deadline,
            )
        except TimeoutError as exc:
            logger.warning("AGENT DEADLINE EXCEEDED: %s", exc)
            return build_result("timeout", str(exc))

        step_count += 1
        usage = track_cost(response)
        if usage is not None:
            for key in usage_totals:
                usage_totals[key] += usage[key]
            estimated_cost_usd += usage["estimated_cost_usd"]

        if not response.candidates:
            logger.error("Gemini returned no candidates.")
            return build_result("error", "The model returned no response.")

        # Preserve the complete model response in conversation history
        model_content = response.candidates[0].content
        if model_content is None:
            logger.error("Gemini returned a candidate without content.")
            return build_result("error", "The model returned no response content.")
        context.add_model_response(model_content)

        function_calls = response.function_calls

        # Model responded without requesting a function
        if not function_calls:
            logger.warning(
                "Model did not call final_answer. "
                "Treating this as an incomplete agent response."
            )

            return build_result(
                "incomplete",
                response.text or "No final answer produced.",
            )

        function_responses = []

        for call in function_calls:

            tool_name = call.name
            arguments = dict(call.args or {})

            logger.info("TOOL REQUESTED: %s", tool_name)
            logger.debug(
                "Tool argument names: %s",
                sorted(arguments),
            )

            # Special terminal tool
            if tool_name == "final_answer":

                answer = arguments.get("answer")

                if not isinstance(answer, str) or not answer.strip():
                    logger.error("Empty or invalid final answer.")
                    return build_result(
                        "error",
                        "The agent produced an invalid final answer.",
                    )

                scratchpad.append({
                    "step": step_count,
                    "action": "final_answer",
                    "observation": answer
                })

                logger.info("Final answer generated.")
                log_scratchpad(scratchpad)

                return build_result("completed", answer)

            # Execute only allowlisted tools
            try:
                function = AVAILABLE_TOOLS.get(tool_name)

                if function is None:
                    raise ValueError(f"Unknown tool: {tool_name}")

                result = function(**arguments)

                observation = {
                    "success": True,
                    "result": result
                }

                logger.info("Tool succeeded: %s", tool_name)

            except Exception as exc:

                # Return a safe error to Gemini instead of crashing
                observation = {
                    "success": False,
                    "error": str(exc)
                }

                logger.error(
                    "Tool failed: %s (error_type=%s)",
                    tool_name,
                    type(exc).__name__,
                )

            # Save action and observation in scratchpad
            scratchpad.append({
                "step": step_count,
                "action": tool_name,
                "arguments": arguments,
                "observation": observation
            })

            log_scratchpad(scratchpad)

            # Prepare the tool result for Gemini
            function_responses.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response=observation
                )
            )

        # Give Gemini all the tool results from this round
        context.add_tool_responses(function_responses)

    # Maximum step limit reached
    logger.warning("MAXIMUM STEP LIMIT REACHED")
    return build_result(
        "max_steps_reached",
        f"Could not complete the task within {max_steps} agent steps.",
    )
