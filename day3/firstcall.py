
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    http_options=types.HttpOptions(
        api_version="v1beta",
        timeout=10_000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)

try:
    print("Sending request to Gemini...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            "Explain Python dictionaries by comparing them with Java HashMap. "
            "Do not greet me or ask questions. Start directly with the explanation. "
            "Include a short code example in both Python and Java."
        ),
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a friendly programming tutor. "
                "Explain concepts simply with examples."
            ),
            temperature=0.3,
            max_output_tokens=500,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    print(response.text)
except Exception as exc:
    print(f"Gemini request failed: {exc}")
finally:
    client.close()
    print("Request finished. Exiting.")
