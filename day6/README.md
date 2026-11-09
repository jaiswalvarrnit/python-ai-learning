# Day 6: Gemini Multi-Tool Agent

This lesson builds an AI agent that can use controlled Python functions instead of only generating text.

The agent can:

- Perform calculations.
- Look up mock customer records.
- Analyze text.
- Decide which tool to use.
- Use multiple tools for one task.
- Return a controlled final answer.
- Log its actions.
- Limit Gemini API request frequency.
- Stop after a maximum number of steps.

## Files

```text
day6/
├── agent.py
├── agent_test.py
├── app.py
├── main.py
├── requirements.txt
└── tools.py
```

- [`agent.py`](./agent.py) contains the agent loop and Gemini tool declarations.
- [`tools.py`](./tools.py) contains the real Python functions.
- [`main.py`](./main.py) provides the interactive command-line interface.
- [`app.py`](./app.py) provides the browser-based Streamlit interface.
- [`agent_test.py`](./agent_test.py) runs realistic test tasks.
- [`requirements.txt`](./requirements.txt) lists external packages.

## Installation

From PowerShell:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day6
python -m pip install -r requirements.txt
```

## Browser UI

The Streamlit app lets you submit tasks, see the final answer, check the status and step count, and expand the agent scratchpad.

Start it with:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day6
python -m pip install -r requirements.txt
python -m streamlit run .\app.py
```

Streamlit opens the app in your browser, usually at:

```text
http://localhost:8501
```

Stop the UI with `Ctrl+C` in the terminal.

Create a `.env` file in the Day 6 directory:

```dotenv
GEMINI_API_KEY=your_api_key
```

Never commit the real API key.

## Running the Agent

```powershell
cd C:\Varrnit\Python\python-ai-learning\day6
python .\main.py
```

The program displays:

```text
=== Gemini AI Agent ===
Type 'exit' to quit.
```

Example questions:

```text
Calculate 25 multiplied by 4.
Find customer C106 and tell me their plan.
Find C103 and calculate their annual subscription fee.
Analyze this text: AI tools are useful and powerful.
```

## 1. Imports

At the top of `agent.py`:

```python
import json
import logging
import os
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock
```

These are standard-library modules:

- `json` converts Python data into JSON for logs.
- `logging` records agent activity and errors.
- `os` reads environment variables.
- `time` measures elapsed time and pauses the rate limiter.
- `deque` stores recent request timestamps.
- `datetime` creates timestamped log filenames.
- `Path` manages the logs directory.
- `Lock` protects rate-limiter state when multiple threads are used.

External and local imports:

```python
from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import AVAILABLE_TOOLS
```

- `load_dotenv` loads `GEMINI_API_KEY` from `.env`.
- `genai` creates the Gemini client.
- `types` provides Gemini request and tool types.
- `AVAILABLE_TOOLS` is the allowlist of executable Python functions.

## 2. Loading the API Key

```python
load_dotenv()
```

This must run before:

```python
client = genai.Client()
```

When Python imports `agent.py`, the Gemini client is created immediately. Loading `.env` first ensures the client can find `GEMINI_API_KEY`.

If the order is reversed, the program can fail with:

```text
ValueError: No API key was provided
```

## 3. Configuration

```python
MODEL = "gemini-3.5-flash-lite"
MAX_STEPS = 6
client = genai.Client()
```

- `MODEL` selects the Gemini model.
- `MAX_STEPS` prevents an endless agent loop.
- `client` is the object used to send Gemini requests.

## 4. Rate Limiting

The `RequestRateLimiter` class limits Gemini requests made by the current Python process.

```python
class RequestRateLimiter:
```

It uses a rolling time window. With four requests per minute:

```text
Request 1: allowed
Request 2: allowed
Request 3: allowed
Request 4: allowed
Request 5: waits until the oldest request expires
```

### Constructor

```python
def __init__(self, max_requests: int, window_seconds: float = 60.0):
```

The constructor validates both values:

```python
if max_requests < 1:
    raise ValueError(...)

if window_seconds <= 0:
    raise ValueError(...)
```

Recent request times are stored in a queue:

```python
self.request_times = deque()
```

The lock protects the queue:

```python
self.lock = Lock()
```

### `wait()`

Before every Gemini request, the agent calls:

```python
RATE_LIMITER.wait()
```

The method:

1. Gets a monotonic timestamp.
2. Removes timestamps older than the time window.
3. Allows the request if capacity is available.
4. Otherwise calculates a delay.
5. Sleeps and checks again.

`time.monotonic()` is used because it measures elapsed time reliably even if the system clock changes.

### Configuration

The default limit is four requests per minute:

```python
value = os.getenv("GEMINI_REQUESTS_PER_MINUTE", "4")
```

Change it in PowerShell before starting the application:

```powershell
$env:GEMINI_REQUESTS_PER_MINUTE = "3"
python .\main.py
```

The limiter controls request frequency, but it does not increase Gemini's daily quota. A provider-side `429 RESOURCE_EXHAUSTED` error still requires waiting for the quota reset or using a project with available quota.

## 5. Tool Declarations

The `create_tool_declarations()` function describes tools to Gemini.

```python
TOOL_DECLARATIONS = create_tool_declarations()
```

A declaration tells Gemini:

- The tool name.
- What the tool does.
- Which arguments it accepts.
- The type of each argument.
- Which arguments are required.

The declaration does not execute Python code. It only describes what Gemini may request.

## 6. Calculator Tool

The calculator declaration accepts:

```text
add
subtract
multiply
divide
modulo
power
floor_divide
```

It requires:

```text
operation
a
b
```

A request can look conceptually like:

```json
{
  "name": "calculator",
  "args": {
    "operation": "multiply",
    "a": 25,
    "b": 4
  }
}
```

The real function is in `tools.py`. The agent executes it only after finding it in `AVAILABLE_TOOLS`.

## 7. Customer Lookup Tool

The `mock_lookup` declaration accepts one required string:

```text
customer_id
```

Example:

```json
{
  "name": "mock_lookup",
  "args": {
    "customer_id": "C106"
  }
}
```

The function retrieves data from the local mock database. It raises an error when the customer does not exist.

## 8. Text Analyzer Tool

The `text_analyzer` declaration accepts:

```text
text
```

The tool returns:

- Character count.
- Character count without spaces.
- Word count.
- Unique word count.
- Line count.
- Digit count.
- Vowel count.
- Punctuation count.
- Uppercase text.
- Lowercase text.

## 9. Final Answer Tool

The `final_answer` tool is different from the other tools. It ends the agent loop.

It accepts one required field:

```text
answer
```

Gemini should call it only when the task is complete or cannot be completed.

Example:

```json
{
  "name": "final_answer",
  "args": {
    "answer": "Customer C106 is Ananya and has an Enterprise plan."
  }
}
```

## 10. Logging

The agent creates a `logs` directory:

```python
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
```

Each run receives a timestamped log file:

```text
logs/agent_20261108_123500.log
```

Logging is sent to both:

- The terminal.
- The log file.

The log records:

- New tasks.
- Agent steps.
- Requested tools.
- Tool arguments.
- Successful results.
- Tool errors.
- Final answers.
- Rate-limit waits.

## 11. System Instructions

`SYSTEM_INSTRUCTION` tells Gemini how to behave:

```text
Use tools when the task requires them.
You may call multiple tools.
Never invent customer information or tool results.
Understand tool failures.
Always finish with final_answer.
```

The model decides which tool is appropriate, but Python controls which functions can actually execute.

## 12. The Scratchpad

The scratchpad is a Python list that records the agent's actions:

```python
scratchpad = []
```

An entry can look like:

```python
{
    "step": 1,
    "action": "mock_lookup",
    "arguments": {
        "customer_id": "C106"
    },
    "observation": {
        "success": True,
        "result": {
            "name": "Ananya",
            "plan": "Enterprise",
            "monthly_fee": 5000,
            "status": "Active"
        }
    }
}
```

The scratchpad is:

- Logged for debugging.
- Returned to the caller.
- Useful for understanding the agent's decisions.

It is separate from `contents`, which is the conversation history sent to Gemini.

## 13. `run_agent()`

The main function is:

```python
def run_agent(user_task: str, max_steps: int = MAX_STEPS):
```

It accepts:

- `user_task`: the user's request.
- `max_steps`: the maximum number of decision rounds.

It returns a dictionary containing:

```python
{
    "status": "...",
    "answer": "...",
    "scratchpad": [...],
    "steps": 3
}
```

## 14. Conversation History

The initial conversation contains the user request:

```python
contents = [
    types.Content(
        role="user",
        parts=[types.Part(text=user_task)]
    )
]
```

As the agent works, `contents` receives:

1. The original user request.
2. Gemini's tool-call response.
3. Python's tool result.
4. Later Gemini responses.

This history lets Gemini understand the results of previous actions.

## 15. The Agent Loop

The main loop is bounded:

```python
while step_count < max_steps:
```

Each iteration:

1. Waits for rate-limit permission.
2. Sends the conversation and tool descriptions to Gemini.
3. Checks the response.
4. Executes requested tools.
5. Sends tool results back to Gemini.
6. Repeats until `final_answer`.

The Gemini request is:

```python
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
```

`temperature=0` makes tool selection more predictable.

## 16. Response Validation

The agent checks whether Gemini returned candidates:

```python
if not response.candidates:
```

If no candidate exists, it returns an error instead of accessing an empty list.

The complete model response is preserved:

```python
model_content = response.candidates[0].content
contents.append(model_content)
```

Then the requested function calls are read:

```python
function_calls = response.function_calls
```

If Gemini returns normal text without a function call, the agent returns:

```python
{
    "status": "incomplete",
    "answer": response.text or "No final answer produced."
}
```

The system instruction asks Gemini to call `final_answer`, but this check handles cases where it does not.

## 17. Executing Tools Safely

The requested name is looked up in the allowlist:

```python
function = AVAILABLE_TOOLS.get(tool_name)
```

Unknown tools are rejected:

```python
if function is None:
    raise ValueError(f"Unknown tool: {tool_name}")
```

This prevents the model from executing arbitrary Python functions.

Valid tools are called with the model's arguments:

```python
result = function(**arguments)
```

Successful results are wrapped as:

```python
{
    "success": True,
    "result": result
}
```

## 18. Tool Error Handling

Tool execution occurs inside a `try` block:

```python
try:
    ...
except Exception as exc:
```

If a tool fails, the agent sends a safe observation back to Gemini:

```python
{
    "success": False,
    "error": str(exc)
}
```

For example, division by zero produces:

```python
{
    "success": False,
    "error": "Cannot divide by zero"
}
```

Gemini can then explain the failure or choose another valid action. The Python process does not immediately crash.

## 19. Sending Tool Results Back

The result is converted into a Gemini function-response part:

```python
types.Part.from_function_response(
    name=tool_name,
    response=observation
)
```

All responses from the current round are added to the conversation:

```python
contents.append(
    types.Content(
        role="user",
        parts=function_responses
    )
)
```

The next loop iteration sends this updated conversation to Gemini.

## 20. Complete Example Flow

Suppose the user asks:

```text
Find C106 and calculate their annual subscription fee.
```

### Step 1: Lookup

Gemini requests:

```text
mock_lookup(customer_id="C106")
```

Python returns:

```python
{
    "name": "Ananya",
    "plan": "Enterprise",
    "monthly_fee": 5000,
    "status": "Active"
}
```

### Step 2: Calculation

Gemini uses the result and requests:

```text
calculator(operation="multiply", a=5000, b=12)
```

Python returns:

```text
60000
```

### Step 3: Final answer

Gemini requests:

```text
final_answer(
    answer="C106 is Ananya. The annual subscription fee is 60000."
)
```

The agent returns:

```python
{
    "status": "completed",
    "answer": "C106 is Ananya. The annual subscription fee is 60000.",
    "steps": 3
}
```

The complete cycle is:

```text
User request
    ↓
Gemini selects a tool
    ↓
Python executes the allowlisted function
    ↓
Python returns the result to Gemini
    ↓
Gemini selects the next action
    ↓
final_answer ends the loop
```

## 21. Maximum Step Protection

If the agent does not finish within `max_steps`, it returns:

```python
{
    "status": "max_steps_reached",
    "answer": "Could not complete the task within 6 agent steps.",
    "scratchpad": scratchpad,
    "steps": step_count
}
```

This prevents endless loops and limits API usage.

## 22. Agent Architecture

```text
main.py
   ↓
run_agent(user_task)
   ↓
Gemini chooses a tool
   ↓
AVAILABLE_TOOLS allowlist
   ↓
Python function executes
   ↓
Tool result returns to Gemini
   ↓
Repeat until final_answer
```

| Component | Responsibility |
|---|---|
| Gemini | Decide what action is needed |
| Tool declarations | Describe available tools |
| `AVAILABLE_TOOLS` | Restrict executable functions |
| Python functions | Perform trusted operations |
| Scratchpad | Record actions and observations |
| Rate limiter | Control request frequency |
| `MAX_STEPS` | Prevent endless loops |
| Logging | Monitor and debug execution |
| `final_answer` | End the agent process |

## 23. Run the Tests

The test file contains scenarios for:

- Basic arithmetic.
- Modulo, power, and floor division.
- Customer lookup.
- Annual subscription calculations.
- Multiple tools in one task.
- Text analysis.
- Unknown customers.
- Division by zero.
- Unsupported requests.
- Invalid operations.

Run it with:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day6
python .\agent_test.py
```

The tests call Gemini and therefore consume API quota. The local rate limiter controls request frequency, but provider-side daily limits still apply.

## Main Lesson

The most important principle is:

> Gemini decides what should happen, but Python controls what is actually executed.

This is safer and more reliable than asking the model to invent calculations or customer information in plain text.
