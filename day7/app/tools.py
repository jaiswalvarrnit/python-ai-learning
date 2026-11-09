# tools.py

CUSTOMERS = {
    "C101": {
        "name": "Rahul",
        "plan": "Premium",
        "monthly_fee": 2000,
        "status": "Active"
    },
    "C102": {
        "name": "Priya",
        "plan": "Basic",
        "monthly_fee": 500,
        "status": "Inactive"
    },
    "C103": {
        "name": "Amit",
        "plan": "Enterprise",
        "monthly_fee": 5000,
        "status": "Active"
    },
    "C104": {
        "name": "Neha",
        "plan": "Premium",
        "monthly_fee": 2000,
        "status": "Active"
    },
    "C105": {
        "name": "Vikram",
        "plan": "Basic",
        "monthly_fee": 500,
        "status": "Inactive"
    },
    "C106": {
        "name": "Ananya",
        "plan": "Enterprise",
        "monthly_fee": 5000,
        "status": "Active"
    },
    "C107": {
        "name": "Rohan",
        "plan": "Basic",
        "monthly_fee": 500,
        "status": "Active"
    }
}


def calculator(operation: str, a: float, b: float):
    """Perform basic arithmetic."""

    if operation == "add":
        return a + b

    if operation == "subtract":
        return a - b

    if operation == "multiply":
        return a * b

    if operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    if operation == "modulo":
        if b == 0:
            raise ValueError("Cannot calculate modulo by zero")
        return a % b

    if operation == "power":
        return a ** b

    if operation == "floor_divide":
        if b == 0:
            raise ValueError("Cannot floor-divide by zero")
        return a // b

    raise ValueError(f"Unsupported operation: {operation}")


def mock_lookup(customer_id: str):
    """Retrieve a customer from the mock database."""

    customer = CUSTOMERS.get(customer_id)

    if customer is None:
        raise ValueError(f"Customer {customer_id} not found")

    return customer


def text_analyzer(text: str):
    """Return basic text statistics."""

    words = text.split()
    lowercase_text = text.lower()

    return {
        "character_count": len(text),
        "character_count_without_spaces": len("".join(text.split())),
        "word_count": len(words),
        "unique_word_count": len({word.lower().strip(".,!?;:'\"()[]{}") for word in words}),
        "line_count": len(text.splitlines()) or 1,
        "digit_count": sum(character.isdigit() for character in text),
        "vowel_count": sum(character in "aeiou" for character in lowercase_text),
        "punctuation_count": sum(
            not character.isalnum() and not character.isspace()
            for character in text
        ),
        "uppercase_text": text.upper(),
        "lowercase_text": lowercase_text,
    }


# Allowlist of executable tools
AVAILABLE_TOOLS = {
    "calculator": calculator,
    "mock_lookup": mock_lookup,
    "text_analyzer": text_analyzer
}
