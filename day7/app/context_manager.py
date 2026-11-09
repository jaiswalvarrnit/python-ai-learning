from collections.abc import Sequence

from google.genai import types


class ContextManager:
    """Build and retain the Gemini conversation history for one agent task."""

    def __init__(self, initial_user_message: str) -> None:
        if not initial_user_message.strip():
            raise ValueError("The initial user message cannot be empty.")

        self._contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=initial_user_message)],
            )
        ]

    def add_model_response(self, content: types.Content) -> None:
        """Append Gemini's response so later requests retain its context."""
        self._contents.append(content)

    def add_tool_responses(self, responses: Sequence[types.Part]) -> None:
        """Append results from executed tools to the conversation."""
        if not responses:
            return

        self._contents.append(
            types.Content(
                role="user",
                parts=list(responses),
            )
        )

    def get_contents(self) -> list[types.Content]:
        """Return a shallow copy of the history for a Gemini request."""
        return list(self._contents)

    @property
    def message_count(self) -> int:
        """Return the number of messages currently in the history."""
        return len(self._contents)