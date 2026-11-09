
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# USD per million tokens.
# Configure these from the current Gemini pricing page.
INPUT_RATE = settings.gemini_input_usd_per_million
OUTPUT_RATE = settings.gemini_output_usd_per_million


def track_cost(response: Any) -> dict[str, int | float] | None:

    usage = getattr(response, "usage_metadata", None)

    if usage is None:
        logger.warning("Gemini did not return usage metadata.")
        return None

    input_tokens = getattr(usage, "prompt_token_count", None) or 0
    output_tokens = getattr(usage, "candidates_token_count", None) or 0
    total_tokens = getattr(usage, "total_token_count", None) or 0

    estimated_cost = (
        input_tokens * INPUT_RATE
        + output_tokens * OUTPUT_RATE
    ) / 1_000_000

    details = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(estimated_cost, 8)
    }

    logger.info("GEMINI USAGE: %s", details)
    return details
