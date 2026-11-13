import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def rewrite_query(question: str) -> str:

    prompt = f"""
You are a search query rewriting assistant.

Rewrite the user's question into one clear, detailed
search query suitable for searching a company knowledge base.

Rules:
1. Preserve the original meaning.
2. Do not invent facts, dates, names, numbers or policies.
3. Expand abbreviations only when their meaning is clear.
4. Include useful synonyms where appropriate.
5. Do not answer the question.
6. Return only the rewritten query.

Original question:
{question}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
        )
    )

    rewritten = (response.text or "").strip()

    if not rewritten:
        return question

    return rewritten