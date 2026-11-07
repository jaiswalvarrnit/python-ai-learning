
# main.py

def calculator(operation: str, a: float, b: float):
    """Perform a mathematical operation."""

    if operation == "add":
        return a + b

    elif operation == "subtract":
        return a - b

    elif operation == "multiply":
        return a * b

    elif operation == "divide":
        if b == 0:
            return {"error": "Cannot divide by zero"}
        return a / b

    return {"error": "Unsupported operation"}


# Mock customer database
CUSTOMERS = {
    "C101": {
        "name": "Rahul",
        "plan": "Premium",
        "status": "Active"
    },
    "C102": {
        "name": "Priya",
        "plan": "Basic",
        "status": "Inactive"
    },
    "C103": {
        "name": "Amit",
        "plan": "Enterprise",
        "status": "Active"
    }
}


def mock_lookup(customer_id: str):
    """Look up a customer in the mock database."""

    customer = CUSTOMERS.get(customer_id)

    if customer is None:
        return {"error": "Customer not found"}

    return customer


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

tools = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="calculator",
                description="Perform basic mathematical calculations.",
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "operation": {
                            "type": "STRING",
                            "enum": [
                                "add",
                                "subtract",
                                "multiply",
                                "divide"
                            ]
                        },
                        "a": {
                            "type": "NUMBER",
                            "description": "First number"
                        },
                        "b": {
                            "type": "NUMBER",
                            "description": "Second number"
                        }
                    },
                    "required": ["operation", "a", "b"]
                }
            ),

            types.FunctionDeclaration(
                name="mock_lookup",
                description="Look up a customer using their customer ID.",
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "customer_id": {
                            "type": "STRING",
                            "description": "Customer ID, for example C101"
                        }
                    },
                    "required": ["customer_id"]
                }
            )
        ]
    )
]


# Map tool names to actual Python functions
available_functions = {
    "calculator": calculator,
    "mock_lookup": mock_lookup
}


def run_agent(user_question: str):

    # First request to Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_question,
        config=types.GenerateContentConfig(
            tools=tools,
            system_instruction=(
                "You are a helpful assistant. "
                "Use the calculator for mathematical calculations. "
                "Use mock_lookup when customer information is requested. "
                "Never invent customer information."
            )
        )
    )

    # Manually handle tool calls
    while response.function_calls:

        # Preserve Gemini's tool-call message in the conversation
        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=user_question)]
            ),
            response.candidates[0].content
        ]

        function_responses = []

        for function_call in response.function_calls:

            tool_name = function_call.name
            arguments = dict(function_call.args or {})

            print(f"\nGemini requested tool: {tool_name}")
            print(f"Arguments: {arguments}")

            # Find and execute the Python function
            function_to_call = available_functions.get(tool_name)

            if function_to_call is None:
                result = {"error": "Unknown tool"}
            else:
                result = function_to_call(**arguments)

            print(f"Tool result: {result}")

            # Prepare result to send back to Gemini
            function_responses.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response={"result": result}
                )
            )

        # Send tool results back to Gemini
        contents.append(
            types.Content(
                role="user",
                parts=function_responses
            )
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                tools=tools,
                system_instruction=(
                    "You are a helpful assistant. "
                    "Use the calculator for mathematical calculations. "
                    "Use mock_lookup when customer information is requested. "
                    "Never invent customer information."
                )
            )
        )

    # Print final response
    print("\nGemini:", response.text)


if __name__ == "__main__":
    question = input("You: ")
    run_agent(question)


