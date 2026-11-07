# Python AI Learning

This repository contains the practical work completed from Day 1 through Day 5 while learning Python backend and AI application development.

## Prerequisites

Install the following:

- Python 3.12 or newer
- Docker Desktop, if Docker examples are required
- A Google Gemini API key, if running Day 3 or Day 4
- PowerShell on Windows

Check installations:

```powershell
python --version
pip --version
docker --version
docker compose version
```

## Python Virtual Environment Setup

From the project directory:

```powershell
cd C:\Varrnit\Python\python-ai-learning
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks activation, use the Python executable directly instead:

```powershell
.\.venv\Scripts\python.exe day1\practice.py
```

To leave the environment:

```powershell
deactivate
```

## What Was Learned

### Day 1: Python Functions and Pydantic

#### Decorators

`day1/decorator.py` demonstrates:

- Passing a function as an argument.
- Calling a function from another function.
- Creating a decorator.
- Using decorator syntax with `@my_decorator`.
- Running code before and after the decorated function.

#### Pydantic Models

`day1/pydanticPractice.py` and `day1/practice.py` demonstrate:

- Creating data models with `BaseModel`.
- Defining fields and constraints with `Field`.
- Validating JSON with `model_validate_json`.
- Automatic type conversion, such as converting `"25"` to `25`.
- Nested models for API responses.
- Lists of typed values.
- Custom validation with `field_validator`.
- Handling invalid data with `ValidationError`.
- Restricting values such as course difficulty to:
  `Beginner`, `Intermediate`, or `Advanced`.

Example:

```python
class Employee(BaseModel):
    name: str = Field(min_length=3)
    age: int = Field(gt=18, lt=60)
    salary: float = Field(gt=0)
    department: str
```

### Day 2: Async Python, HTTPX, FastAPI, and Docker

#### Synchronous and Asynchronous Code

`day2/asyncioaw.py` demonstrates:

- Normal blocking functions using `time.sleep`.
- Async functions using `async def`.
- Pausing without blocking with `await asyncio.sleep`.
- Starting an async program with `asyncio.run`.
- Running independent tasks concurrently with `asyncio.gather`.

Concurrency allows multiple waiting operations to progress together. For example, three two-second tasks can complete in approximately two seconds when run with `asyncio.gather`, rather than approximately six seconds sequentially.

#### HTTPX

`day2/httpxpr.py` demonstrates:

- Making a synchronous HTTP request with `httpx.get`.
- Making an asynchronous request with `httpx.AsyncClient`.
- Reusing one async client for multiple requests.
- Checking failures with `response.raise_for_status`.
- Fetching multiple users concurrently.

#### FastAPI

`day2/fastapi/main.py` provides:

- `GET /health`
- `POST /echo`

`day2/assisgnment_day2/assday2.py` additionally provides:

- `GET /health`
- `POST /echo`
- `GET /users/{user_id}`

FastAPI uses Pydantic request models to validate incoming JSON before the endpoint function runs.

#### Docker

The Day 2 Dockerfiles:

- Start from `python:3.12-slim`.
- Set `/app` as the working directory.
- Install dependencies from `requirements.txt`.
- Copy the application into the image.
- Expose port `8000`.
- Start the app with Uvicorn.

### Day 3: Gemini API, Chatbots, and Streaming

The files in `day3` demonstrate:

- Loading secrets from `.env` with `python-dotenv`.
- Creating a Google Gemini client with `google-genai`.
- Sending a normal request with `generate_content`.
- Receiving output incrementally with `generate_content_stream`.
- Maintaining conversation history.
- Adding user and model messages with `types.Content`.
- Using a system instruction to define the assistant's behavior.
- Setting generation options such as temperature and maximum output tokens.
- Closing the client in a `finally` block.

The Gemini examples use:

```python
http_options=types.HttpOptions(
    api_version="v1beta",
    timeout=10_000,
    retry_options=types.HttpRetryOptions(attempts=1),
)
```

`v1beta` is required in these examples because they use `system_instruction`.

### Day 4: Structured Ticket Classification

`day4/ticket_classifier.py` combines Gemini with Pydantic.

The `TicketClassification` model defines the required output:

```python
class TicketClassification(BaseModel):
    category: Literal[
        "Billing", "Technical", "Account", "Shipping", "Other"
    ]
    priority: Literal["Low", "Medium", "High", "Urgent"]
    summary: str
```

The model is sent to Gemini as a JSON Schema:

```python
response_mime_type="application/json"
response_json_schema=TicketClassification.model_json_schema()
```

- `response_mime_type` requests JSON instead of normal text.
- `response_json_schema` describes the exact fields and allowed values.

The result is validated again in Python:

```python
TicketClassification.model_validate_json(response.text)
```

This gives both structured generation from Gemini and runtime validation with Pydantic.

`day4/test_tickets.py` tests the classifier with multiple billing, technical, and account tickets. `day4/results.txt` contains recorded test output.

### Day 5: Gemini Function Calling and Tool Use

`day5/main.py` demonstrates how to connect Gemini to local Python functions.

The application exposes two tools:

- `calculator` performs addition, subtraction, multiplication, and division.
- `mock_lookup` retrieves customer information from a local mock database.

The tool-calling flow is:

1. Send the user's question and tool declarations to Gemini.
2. Let Gemini decide whether a tool is needed.
3. Read the requested function name and arguments from `response.function_calls`.
4. Find and execute the corresponding Python function.
5. Send the function result back to Gemini.
6. Receive and print Gemini's final natural-language answer.

The `available_functions` dictionary maps model-requested tool names to actual Python functions:

```python
available_functions = {
    "calculator": calculator,
    "mock_lookup": mock_lookup,
}
```

This pattern keeps the model responsible for choosing a tool while Python remains responsible for executing the tool and controlling the data.

Example questions:

```text
What is 25 multiplied by 4?
Look up customer C101.
What is the status and plan of customer C103?
```

Run Day 5 with:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day5
.\.venv-google\Scripts\Activate.ps1
python .\main.py
```

Every tool-enabled question can require more than one Gemini request: one request to select the tool and another request to generate the final answer after the tool result is returned.

#### Day 5 Quota Note

Gemini free-tier projects have request limits. A `429 RESOURCE_EXHAUSTED` error means the configured project has exceeded its quota, not that the local Python tool function necessarily failed. Check the usage and reset time at:

- https://ai.dev/rate-limit
- https://aistudio.google.com/docs/rate-limits

Retrying repeatedly does not resolve a daily quota limit. Wait for the quota reset or use a project with available quota.

## Project Structure

```text
python-ai-learning/
├── day1/
│   ├── decorator.py
│   ├── practice.py
│   └── pydanticPractice.py
├── day2/
│   ├── asyncioaw.py
│   ├── httpxpr.py
│   ├── assisgnment_day2/
│   │   ├── Dockerfile
│   │   ├── assday2.py
│   │   └── requirements.txt
│   └── fastapi/
│       ├── Dockerfile
│       ├── main.py
│       └── requirements.txt
├── day3/
│   ├── chatbot.py
│   ├── firstcall.py
│   └── streaming.py
├── day4/
│   ├── .env
│   ├── ticket_classifier.py
│   ├── test_tickets.py
│   └── results.txt
├── day5/
│   └── main.py
└── README.md
```



## Install Python Libraries

### Day 1

```powershell
python -m pip install pydantic email-validator
```

`email-validator` is useful when using Pydantic's `EmailStr` type.

### Day 2

```powershell
python -m pip install fastapi "uvicorn[standard]" httpx
```

Or install the existing FastAPI project dependencies:

```powershell
cd day2\fastapi
python -m pip install -r requirements.txt
```

For the assignment project:

```powershell
cd ..\assisgnment_day2
python -m pip install -r requirements.txt
```

### Day 3, Day 4, and Day 5

```powershell
python -m pip install google-genai python-dotenv pydantic
```

The `google-genai` package provides the Gemini client, and `python-dotenv` loads values from `.env`.

## Gemini Environment Variables

Create a `.env` file in the directory from which the Gemini script is run. These examples use the `GEMINI_API_KEY` variable.

Example:

```dotenv
GEMINI_API_KEY=replace_with_your_key
```

Do not commit `.env` or expose the API key.

Run Gemini examples from their own directories:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day3
.\.venv-google\Scripts\Activate.ps1
python .\firstcall.py
```

For the Day 4 classifier:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day4
.\.venv-google\Scripts\Activate.ps1
python .\ticket_classifier.py
```

For the Day 5 tool-calling agent:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day5
.\.venv-google\Scripts\Activate.ps1
python .\main.py
```

## Running the Python Examples

```powershell
cd C:\Varrnit\Python\python-ai-learning
.\.venv\Scripts\Activate.ps1

python .\day1\decorator.py
python .\day1\practice.py
python .\day1\pydanticPractice.py
python .\day2\asyncioaw.py
python .\day2\httpxpr.py
```

Run the ticket tests:

```powershell
cd day4
.\.venv-google\Scripts\Activate.ps1
python .\test_tickets.py
```

The test script calls the Gemini API, so it may be affected by API rate limits or temporary service errors.

## Running FastAPI Locally

### Main FastAPI App

```powershell
cd C:\Varrnit\Python\python-ai-learning\day2\fastapi
.\..\..\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

Open:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

Test the echo endpoint from another PowerShell window:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/echo `
  -ContentType "application/json" `
  -Body '{"message":"Hello","user":"Varrnit"}'
```

### Assignment FastAPI App

```powershell
cd C:\Varrnit\Python\python-ai-learning\day2\assisgnment_day2
.\..\..\.venv\Scripts\Activate.ps1
python -m uvicorn assday2:app --reload
```

The assignment app uses the same port and provides the additional `/users/{user_id}` endpoint.

Stop a running local server with `Ctrl+C`.

## Docker Commands

Make sure Docker Desktop is running before using these commands.

### Build and Run the Main FastAPI Image

```powershell
cd C:\Varrnit\Python\python-ai-learning\day2\fastapi
docker build -t python-ai-fastapi .
docker run --name python-ai-fastapi-container -p 8000:8000 python-ai-fastapi
```

Open http://localhost:8000/docs.

Run in detached mode:

```powershell
docker run -d --name python-ai-fastapi-container -p 8000:8000 python-ai-fastapi
```

View logs:

```powershell
docker logs -f python-ai-fastapi-container
```

Stop and remove the container:

```powershell
docker stop python-ai-fastapi-container
docker rm python-ai-fastapi-container
```

### Build and Run the Assignment Image

```powershell
cd C:\Varrnit\Python\python-ai-learning\day2\assisgnment_day2
docker build -t python-ai-assignment .
docker run --name python-ai-assignment-container -p 8000:8000 python-ai-assignment
```

### Useful Docker Commands

```powershell
docker image ls
docker container ls
docker container ls -a
docker inspect python-ai-fastapi-container
docker stop python-ai-fastapi-container
docker rm python-ai-fastapi-container
docker rmi python-ai-fastapi
docker system prune
```

Use `docker system prune` carefully because it removes unused Docker resources.

## Common Terminal Commands

```powershell
# Show the current directory
Get-Location

# List files, including hidden files
Get-ChildItem -Force

# Move to a directory
Set-Location C:\Varrnit\Python\python-ai-learning

# Create a directory
New-Item -ItemType Directory new-folder

# Create a virtual environment
python -m venv .venv

# Activate a Windows PowerShell virtual environment
.\.venv\Scripts\Activate.ps1

# Show the Python executable being used
Get-Command python

# Install a package
python -m pip install package-name

# Install all packages from a requirements file
python -m pip install -r requirements.txt

# Show installed packages
python -m pip list

# Run a Python file
python .\path\to\file.py

# Stop a running program
Ctrl+C
```

## Troubleshooting

### PowerShell Does Not Allow Activation

Use the environment's Python executable directly:

```powershell
.\.venv-google\Scripts\python.exe .\ticket_classifier.py
```

### Gemini `400 INVALID_ARGUMENT`

If the error says that developer instructions are not enabled for API version `v1`, configure the client with:

```python
types.HttpOptions(api_version="v1beta")
```

### Gemini `503 UNAVAILABLE`

The model may be temporarily busy. Wait and retry. This is a service availability problem rather than a Python validation problem.

### Gemini Rate Limits

The API may reject requests after too many calls. Reduce request frequency, wait for the retry window, and avoid repeatedly running the full ticket test set during development.

### Port 8000 Is Already in Use

Use another host port:

```powershell
python -m uvicorn main:app --reload --port 8001
```

Or map a different host port for Docker:

```powershell
docker run --name python-ai-fastapi-container -p 8001:8000 python-ai-fastapi
```

Then open http://localhost:8001/docs.

## Main Takeaways

1. Decorators wrap and extend function behavior.
2. Pydantic validates and structures Python data.
3. Asyncio allows concurrent waiting operations.
4. HTTPX makes synchronous and asynchronous HTTP requests.
5. FastAPI builds validated web APIs quickly.
6. Docker packages an application and its dependencies.
7. Gemini can generate normal, streamed, and structured responses.
8. A Pydantic JSON Schema can constrain an AI response.
9. Pydantic validation should still verify the response received from an AI model.
10. Gemini function calling lets an AI model request controlled local Python tools.
