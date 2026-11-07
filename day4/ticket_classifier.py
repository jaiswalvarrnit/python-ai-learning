
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

client = genai.Client(
    http_options=types.HttpOptions(
        api_version="v1beta",
        timeout=10_000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)


# 1. Define the output schema
class TicketClassification(BaseModel):
    category: Literal[
        "Billing", "Technical", "Account", "Shipping", "Other"
    ] = Field(description="The main category of the support ticket.")

    priority: Literal[
        "Low", "Medium", "High", "Urgent"
    ] = Field(description="How urgently the ticket needs attention.")

    summary: str = Field(
        description="A concise, one-sentence summary of the customer's issue."
    )


# 2. Ask Gemini to classify one ticket
def classify_ticket(ticket: str) -> TicketClassification:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Classify this customer support ticket:\n\n{ticket}",
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a customer support ticket classifier. "
                "Choose the most appropriate category and priority. "
                "Use Urgent for immediate severe issues, High for "
                "significant problems, Medium for ordinary issues, "
                "and Low for minor requests. "
                "Do not invent facts not present in the ticket."
            ),
            response_mime_type="application/json",
            response_json_schema=TicketClassification.model_json_schema(),
            temperature=0,
        ),
    )

    # 3. Validate Gemini's JSON with Pydantic
    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return TicketClassification.model_validate_json(response.text)


if __name__ == "__main__":
    ticket = (
        "I was charged twice for my subscription. "
        "Please refund the extra payment."
    )

    result = classify_ticket(ticket)

    print(result.model_dump_json(indent=2))
