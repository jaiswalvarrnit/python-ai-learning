
import os
import math
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = os.getenv(
    "ENV_FILE",
    str(Path(__file__).resolve().parents[1] / ".env"),
)
load_dotenv(ENV_FILE)


class Settings:

    def __init__(self):
        raw_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_api_key = raw_api_key.strip() if raw_api_key else None
        self.environment = os.getenv("APP_ENV", "development").strip().lower()
        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash-lite"
        ).strip()
        self.max_agent_steps = self._positive_int("MAX_AGENT_STEPS", 6)
        self.request_timeout = self._positive_float("REQUEST_TIMEOUT", 60)
        self.agent_deadline_seconds = self._positive_float(
            "AGENT_DEADLINE_SECONDS",
            180,
        )
        self.gemini_requests_per_minute = self._positive_int(
            "GEMINI_REQUESTS_PER_MINUTE",
            4,
        )
        self.api_requests_per_window = self._positive_int(
            "API_REQUESTS_PER_WINDOW",
            30,
        )
        self.api_rate_limit_window_seconds = self._positive_float(
            "API_RATE_LIMIT_WINDOW_SECONDS",
            60,
        )
        self.max_concurrent_agents = self._positive_int(
            "MAX_CONCURRENT_AGENTS",
            4,
        )
        self.max_request_body_bytes = self._positive_int(
            "MAX_REQUEST_BODY_BYTES",
            65_536,
        )
        raw_allowed_hosts = os.getenv("ALLOWED_HOSTS")
        self.allowed_hosts = [
            host.strip()
            for host in (
                raw_allowed_hosts or "127.0.0.1,localhost,testserver"
            ).split(",")
            if host.strip()
        ]
        raw_access_token = os.getenv("API_ACCESS_TOKEN")
        self.api_access_token = (
            raw_access_token.strip() if raw_access_token else None
        )
        raw_redis_url = os.getenv("REDIS_URL")
        self.redis_url = raw_redis_url.strip() if raw_redis_url else None
        self.gemini_input_usd_per_million = self._nonnegative_float(
            "GEMINI_INPUT_USD_PER_MILLION",
            0,
        )
        self.gemini_output_usd_per_million = self._nonnegative_float(
            "GEMINI_OUTPUT_USD_PER_MILLION",
            0,
        )

        if self.environment not in {"development", "test", "production"}:
            raise ValueError(
                "APP_ENV must be development, test, or production."
            )

        if self.api_access_token is not None and (
            not self.api_access_token.isascii()
            or len(self.api_access_token) < 32
        ):
            raise ValueError(
                "API_ACCESS_TOKEN must be ASCII and at least 32 characters."
            )

        if not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing from environment."
            )
        if not self.model:
            raise ValueError("GEMINI_MODEL cannot be empty.")

        if self.environment == "production":
            if not self.api_access_token:
                raise ValueError(
                    "Production requires API_ACCESS_TOKEN."
                )
            if not self.redis_url:
                raise ValueError(
                    "Production requires REDIS_URL for shared API rate limiting."
                )
            if (
                not raw_allowed_hosts
                or not self.allowed_hosts
                or "*" in self.allowed_hosts
            ):
                raise ValueError(
                    "Production requires explicit ALLOWED_HOSTS entries."
                )

    @staticmethod
    def _positive_int(name: str, default: int) -> int:
        try:
            value = int(os.getenv(name, str(default)))
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer.") from exc

        if value < 1:
            raise ValueError(f"{name} must be at least 1.")

        return value

    @staticmethod
    def _positive_float(name: str, default: float) -> float:
        try:
            value = float(os.getenv(name, str(default)))
        except ValueError as exc:
            raise ValueError(f"{name} must be a number.") from exc

        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a finite number greater than zero.")

        return value

    @staticmethod
    def _nonnegative_float(name: str, default: float) -> float:
        try:
            value = float(os.getenv(name, str(default)))
        except ValueError as exc:
            raise ValueError(f"{name} must be a number.") from exc

        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a finite nonnegative number.")

        return value


settings = Settings()
