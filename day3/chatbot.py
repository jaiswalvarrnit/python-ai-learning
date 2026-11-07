
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

MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """
You are a friendly Python and AI engineering tutor.
Explain concepts in simple language.
Use examples and compare concepts with Java when useful.
If you are unsure about something, say so.
"""

messages = []


def stream_reply():
    """Request a streamed reply and save it to conversation history."""
    assistant_parts = []

    try:
        stream = client.models.generate_content_stream(
            model=MODEL,
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=5020,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )

        print("\nGemini: ", end="", flush=True)

        for chunk in stream:
            if chunk.text:
                print(chunk.text, end="", flush=True)
                assistant_parts.append(chunk.text)

        print()

        # Add the assistant reply only after the stream finishes.
        if assistant_parts:
            messages.append(
                types.Content(
                    role="model",
                    parts=[types.Part(text="".join(assistant_parts))],
                )
            )

    except KeyboardInterrupt:
        print("\nStreaming interrupted.")

    except Exception as error:
        print(f"\nGemini request failed: {error}")


def main():
    print("Python AI Tutor")
    print("Type 'exit' to quit.")
    print("Type 'clear' to start a new conversation.")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if user_input.lower() == "clear":
                messages.clear()
                print("Conversation cleared.")
                continue

        if not user_input:
            continue

        messages.append(
            types.Content(
                role="user",
                parts=[types.Part(text=user_input)],
            )
        )

        stream_reply()

    client.close()


if __name__ == "__main__":
    main()
