import unittest

from google.genai import types

from app.context_manager import ContextManager


class ContextManagerTests(unittest.TestCase):
    def test_initializes_with_user_message(self):
        context = ContextManager("Find customer C101.")

        contents = context.get_contents()
        self.assertEqual(context.message_count, 1)
        self.assertEqual(contents[0].role, "user")
        self.assertEqual(contents[0].parts[0].text, "Find customer C101.")

    def test_adds_model_and_tool_messages(self):
        context = ContextManager("Calculate 2 + 2.")
        model_response = types.Content(
            role="model",
            parts=[types.Part(text="Calling calculator.")],
        )
        tool_response = types.Part.from_function_response(
            name="calculator",
            response={"success": True, "result": 4},
        )

        context.add_model_response(model_response)
        context.add_tool_responses([tool_response])

        contents = context.get_contents()
        self.assertEqual(context.message_count, 3)
        self.assertEqual(contents[1], model_response)
        self.assertEqual(contents[2].parts, [tool_response])

    def test_returns_copy_of_history(self):
        context = ContextManager("Hello")

        contents = context.get_contents()
        contents.clear()

        self.assertEqual(context.message_count, 1)

    def test_rejects_empty_initial_message(self):
        with self.assertRaises(ValueError):
            ContextManager("  ")


if __name__ == "__main__":
    unittest.main()
