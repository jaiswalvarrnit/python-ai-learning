# agent.py

import json
import logging
import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import AVAILABLE_TOOLS


load_dotenv()

MODEL = "gemini-3.5-flash-lite"
MAX_STEPS = 6

client = genai.Client()


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

    def wait(self):
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

            logger.info(
                "Gemini rate limit reached; waiting %.1f seconds.",
                delay,
            )
            time.sleep(delay)


def _requests_per_minute():
    value = os.getenv("GEMINI_REQUESTS_PER_MINUTE", "4")
    try:
        requests = int(value)
    except ValueError as exc:
        raise ValueError(
            "GEMINI_REQUESTS_PER_MINUTE must be an integer"
        ) from exc

    if requests < 1:
        raise ValueError("GEMINI_REQUESTS_PER_MINUTE must be at least 1")

    return requests


RATE_LIMITER = RequestRateLimiter(_requests_per_minute())


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


# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Every run gets its own log file
LOG_FILE = LOG_DIR / (
    f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger("agent")



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
    """Log the current agent scratchpad."""

    logger.info("SCRATCHPAD: %s", json.dumps(
        scratchpad, ensure_ascii=False, default=str
    ))


def run_agent(user_task: str, max_steps: int = MAX_STEPS):

    logger.info("=" * 60)
    logger.info("NEW AGENT TASK: %s", user_task)

    # Conversation history sent to Gemini
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=user_task)]
        )
    ]

    # Internal record of actions and observations
    scratchpad = []

    step_count = 0

    while step_count < max_steps:

        logger.info("AGENT STEP %s/%s", step_count + 1, max_steps)

        # Ask Gemini what to do next
        RATE_LIMITER.wait()
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=TOOL_DECLARATIONS,
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0
            )
        )

        if not response.candidates:
            logger.error("Gemini returned no candidates.")
            return {
                "status": "error",
                "answer": "The model returned no response.",
                "scratchpad": scratchpad
            }

        # Preserve the complete model response in conversation history
        model_content = response.candidates[0].content
        contents.append(model_content)

        function_calls = response.function_calls

        # Model responded without requesting a function
        if not function_calls:
            logger.warning(
                "Model did not call final_answer. "
                "Treating this as an incomplete agent response."
            )

            return {
                "status": "incomplete",
                "answer": response.text or "No final answer produced.",
                "scratchpad": scratchpad
            }

        step_count += 1

        function_responses = []

        for call in function_calls:

            tool_name = call.name
            arguments = dict(call.args or {})

            logger.info("TOOL REQUESTED: %s", tool_name)
            logger.info("TOOL ARGUMENTS: %s", arguments)

            # Special terminal tool
            if tool_name == "final_answer":

                answer = arguments.get("answer")

                if not isinstance(answer, str) or not answer.strip():
                    logger.error("Empty or invalid final answer.")
                    return {
                        "status": "error",
                        "answer": "The agent produced an invalid final answer.",
                        "scratchpad": scratchpad
                    }

                scratchpad.append({
                    "step": step_count,
                    "action": "final_answer",
                    "observation": answer
                })

                logger.info("FINAL ANSWER: %s", answer)
                log_scratchpad(scratchpad)

                return {
                    "status": "completed",
                    "answer": answer,
                    "scratchpad": scratchpad,
                    "steps": step_count
                }

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

                logger.info(
                    "TOOL SUCCESS: %s",
                    json.dumps(result, default=str)
                )

            except Exception as exc:

                # Return a safe error to Gemini instead of crashing
                observation = {
                    "success": False,
                    "error": str(exc)
                }

                logger.exception("TOOL FAILED: %s", tool_name)

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
        if function_responses:
            contents.append(
                types.Content(
                    role="user",
                    parts=function_responses
                )
            )

    # Maximum step limit reached
    logger.warning("MAXIMUM STEP LIMIT REACHED")

    return {
        "status": "max_steps_reached",
        "answer": (
            f"Could not complete the task within "
            f"{max_steps} agent steps."
        ),
        "scratchpad": scratchpad,
        "steps": step_count
    }
