# Day 7: Gemini Agent API

Day 7 builds a FastAPI service around a Gemini tool-using agent. It includes managed conversation history, transient-error retries, request throttling, execution deadlines, token usage, and estimated-cost reporting.

## Project files

- `app/agent.py` runs the Gemini agent and its tool loop.
- `app/context_manager.py` stores the conversation sent to the model.
- `app/config.py` loads and validates environment settings.
- `app/reliability.py` retries transient API failures.
- `app/cost_tracker.py` collects token usage and estimates API cost.
- `app/tools.py` defines local Python tools.
- `app/main.py` exposes health and agent endpoints through FastAPI.
- `app/security.py` provides local and Redis-backed API rate limits.
- `tests/` contains offline unit and API tests.
- `Dockerfile` builds a non-root container image.

## Setup

From PowerShell:

```powershell
cd C:\Varrnit\Python\python-ai-learning\day7
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your values:

```dotenv
GEMINI_API_KEY=your_api_key
APP_ENV=development
GEMINI_MODEL=gemini-3.5-flash-lite
MAX_AGENT_STEPS=6
REQUEST_TIMEOUT=60
AGENT_DEADLINE_SECONDS=180
GEMINI_REQUESTS_PER_MINUTE=4
API_REQUESTS_PER_WINDOW=30
API_RATE_LIMIT_WINDOW_SECONDS=60
MAX_CONCURRENT_AGENTS=4
MAX_REQUEST_BODY_BYTES=65536
GEMINI_INPUT_USD_PER_MILLION=0
GEMINI_OUTPUT_USD_PER_MILLION=0
```

Set the input and output token prices using the current Gemini pricing for your model. Estimated cost remains zero when the prices are left at zero. In development, the API bearer token is optional. When `API_ACCESS_TOKEN` is configured, send it as a bearer token.

Generate a suitable API bearer token for production with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Start the API

Run Uvicorn from the `day7` directory:

```powershell
python -m uvicorn app.main:app --reload
```

Endpoints:

- `GET http://127.0.0.1:8000/health`
- `POST http://127.0.0.1:8000/agent/run`
- `GET http://127.0.0.1:8000/ready`
- `GET http://127.0.0.1:8000/health/live`
- Interactive API docs: `http://127.0.0.1:8000/docs`

Example request:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/agent/run `
  -ContentType "application/json" `
  -Body '{"task":"Find customer C106 and calculate their annual fee."}'
```

## Run offline tests

Tests mock Gemini responses, so they do not consume API quota:

```powershell
python -m unittest discover -s tests -v
```

The test suite checks conversation history, tool execution, failure reporting, result fields, API request validation, rate limiting, and retry behavior.

## Production settings

Production mode is fail-closed. Set `APP_ENV=production` and configure:

- `API_ACCESS_TOKEN`: ASCII bearer secret with at least 32 characters.
- `REDIS_URL`: shared Redis service for rate limits across API worker processes.
- `ALLOWED_HOSTS`: comma-separated hostnames served by this deployment.
- `GEMINI_API_KEY`: supplied through a deployment secret manager.

The API uses bearer authentication and a sliding-window per-client request limit. Requests exceeding the limit receive `429` and a `Retry-After` header. Concurrent agent runs are bounded per worker. The request limiter uses Redis in production; development uses an in-memory limiter.

Liveness (`/health/live`) does not depend on Redis. Readiness (`/ready`) checks that configured Redis is reachable. API documentation endpoints are disabled in production. Request IDs are returned in `X-Request-ID` and logs avoid user prompts, tool arguments, customer results, and generated answers.

Example production configuration:

```dotenv
APP_ENV=production
API_ACCESS_TOKEN=use-a-random-secret-of-at-least-32-ascii-characters
REDIS_URL=redis://redis-host:6379/0
ALLOWED_HOSTS=api.example.com
```

For trusted reverse proxies, configure Uvicorn's proxy-header handling with only the trusted proxy IPs. Do not trust forwarded headers from arbitrary clients.

## Docker

Build from the Day 7 directory:

```powershell
docker build -t gemini-agent-api .
```

Run locally with the `.env` file supplied at runtime:

```powershell
docker run --rm --env-file .env -p 8000:8000 gemini-agent-api
```

Do not bake `.env` or API credentials into the image. A production deployment must provide Redis and production environment settings.

## Configuration and reliability

- `GEMINI_MODEL` selects the model.
- `MAX_AGENT_STEPS` limits model/tool decision rounds.
- `REQUEST_TIMEOUT` sets the Gemini request timeout in seconds.
- `AGENT_DEADLINE_SECONDS` bounds the overall workflow between requests and retry waits. An active HTTP request is separately bounded by `REQUEST_TIMEOUT`.
- `GEMINI_REQUESTS_PER_MINUTE` configures the process-local rolling request limit.
- `API_REQUESTS_PER_WINDOW` and `API_RATE_LIMIT_WINDOW_SECONDS` configure API request limits per client.
- `MAX_CONCURRENT_AGENTS` bounds active agent runs per worker.
- `MAX_REQUEST_BODY_BYTES` bounds the JSON payload accepted by the agent endpoint.
- `API_ACCESS_TOKEN` enables bearer authentication; it is mandatory in production.
- `REDIS_URL` configures the shared production rate-limit store.
- `ALLOWED_HOSTS` configures the host header allowlist.
- `GEMINI_INPUT_USD_PER_MILLION` and `GEMINI_OUTPUT_USD_PER_MILLION` configure estimated cost reporting.

Transient server errors and short-term rate limits may be retried. Daily quota exhaustion is not retried because waiting briefly cannot restore a daily quota. The agent response includes `status`, `answer`, `steps`, token `usage`, `estimated_cost_usd`, and the tool `scratchpad`.
