import logging
import secrets
import time
from contextlib import asynccontextmanager
from threading import BoundedSemaphore
from uuid import uuid4
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, StringConstraints
from redis.asyncio import Redis
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.agent import run_agent
from app.config import settings
from app.security import InMemoryRateLimiter, RedisRateLimiter

logger = logging.getLogger("agent-api")
bearer_scheme = HTTPBearer(auto_error=False)
agent_slots = BoundedSemaphore(settings.max_concurrent_agents)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = None
    if settings.redis_url:
        redis_client = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=settings.request_timeout,
            socket_timeout=settings.request_timeout,
        )
        try:
            await redis_client.ping()
        except Exception as exc:
            await redis_client.aclose()
            logger.error(
                "Could not connect to configured Redis service "
                "(error_type=%s).",
                type(exc).__name__,
            )
            raise RuntimeError(
                "Configured Redis service is unavailable."
            ) from exc

        app.state.rate_limiter = RedisRateLimiter(
            redis_client,
            settings.api_requests_per_window,
            settings.api_rate_limit_window_seconds,
        )
    else:
        app.state.rate_limiter = InMemoryRateLimiter(
            settings.api_requests_per_window,
            settings.api_rate_limit_window_seconds,
        )

    app.state.redis_client = redis_client
    try:
        yield
    finally:
        if redis_client is not None:
            await redis_client.aclose()


app = FastAPI(
    title="Gemini AI Agent API",
    description="A multi-tool AI agent built from scratch.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc",
    openapi_url=None if settings.environment == "production" else "/openapi.json",
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)


class AgentRequest(BaseModel):
    task: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=5000),
    ]


class TokenUsage(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class AgentResponse(BaseModel):
    status: Literal[
        "completed",
        "incomplete",
        "timeout",
        "error",
        "max_steps_reached",
    ]
    answer: str
    steps: int = Field(ge=0)
    usage: TokenUsage
    estimated_cost_usd: float = Field(ge=0)
    scratchpad: list[dict[str, Any]]


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = uuid4().hex
    request.state.request_id = request_id
    started_at = time.monotonic()

    if request.method == "POST" and request.url.path == "/agent/run":
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                body_size = int(content_length)
            except ValueError:
                response = JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Invalid Content-Length header.",
                        "request_id": request_id,
                    },
                )
                response.headers["X-Request-ID"] = request_id
                return response

            if body_size > settings.max_request_body_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={
                        "detail": "Request body is too large.",
                        "request_id": request_id,
                    },
                )
                response.headers["X-Request-ID"] = request_id
                return response

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(
            "Unhandled request failure request_id=%s method=%s path=%s "
            "error_type=%s",
            request_id,
            request.method,
            request.url.path,
            type(exc).__name__,
        )
        raise

    response.headers["X-Request-ID"] = request_id
    logger.info(
        "HTTP request request_id=%s method=%s path=%s status=%s duration=%.3fs",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        time.monotonic() - started_at,
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
):
    errors = [
        {
            "location": error["loc"],
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "detail": errors,
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logger.error(
        "Unexpected server error request_id=%s error_type=%s",
        getattr(request.state, "request_id", "unknown"),
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error.",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


async def enforce_api_policy(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    client_ip = request.client.host if request.client else "unknown"
    retry_after = await request.app.state.rate_limiter.retry_after(client_ip)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Request rate limit exceeded.",
            headers={"Retry-After": str(retry_after)},
        )

    expected_token = settings.api_access_token
    if expected_token is None and settings.environment != "production":
        return

    supplied_token = credentials.credentials if credentials else ""
    if (
        not supplied_token.isascii()
        or not secrets.compare_digest(supplied_token, expected_token or "")
    ):
        raise HTTPException(
            status_code=401,
            detail="Valid bearer authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/health")
def health_check():
    """Liveness probe; does not depend on external services."""
    return {
        "status": "healthy",
        "service": "Gemini AI Agent",
    }


@app.get("/health/live")
def liveness_check():
    return {"status": "alive"}


@app.get("/ready")
async def readiness_check(request: Request):
    """Readiness probe for deployment orchestrators."""
    redis_client = request.app.state.redis_client
    if redis_client is not None:
        try:
            await redis_client.ping()
        except Exception as exc:
            logger.error("Readiness check failed: Redis is unavailable.")
            raise HTTPException(
                status_code=503,
                detail="Required rate-limit service is unavailable.",
            ) from exc

    return {"status": "ready"}


@app.post(
    "/agent/run",
    response_model=AgentResponse,
    dependencies=[Depends(enforce_api_policy)],
)
def execute_agent(request: Request, agent_request: AgentRequest):
    if not agent_slots.acquire(blocking=False):
        raise HTTPException(
            status_code=503,
            detail="Agent capacity is busy. Please retry shortly.",
            headers={"Retry-After": "1"},
        )

    started_at = time.monotonic()
    try:
        result = run_agent(agent_request.task)
        if result["status"] == "timeout":
            raise HTTPException(
                status_code=504,
                detail="Agent execution deadline exceeded.",
            )
        if result["status"] == "error":
            raise HTTPException(
                status_code=502,
                detail="The model did not return a usable response.",
            )

        logger.info(
            "Agent request completed request_id=%s duration=%.2fs status=%s",
            request.state.request_id,
            time.monotonic() - started_at,
            result.get("status", "unknown"),
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Agent execution failed error_type=%s",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=502,
            detail="AI agent execution failed. Check the request ID in server logs.",
        ) from exc
    finally:
        agent_slots.release()
