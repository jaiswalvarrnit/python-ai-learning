
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load the API key from .env
load_dotenv()

# Create Gemini client with a bounded, single-attempt request.
client = genai.Client(
    http_options=types.HttpOptions(
        api_version="v1beta",
        timeout=10_000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)

try:
    while True:
        user_message = input("You: ")
        if user_message.strip().lower() == "exit":
            break

        try:
            stream = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=user_message,
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

            print("Gemini: ", end="", flush=True)
            for chunk in stream:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            print()
        except Exception as exc:
            print(f"Gemini request failed: {exc}")

except Exception as exc:
    print(f"\nGemini streaming request failed: {exc}")
finally:
    client.close()
    print("Request finished. Exiting.")
