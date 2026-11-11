
from rag import validate_citations

chunks = [
    {"id": 12},
    {"id": 13},
    {"id": 15}
]

# Test 1: Valid citation
answer1 = "You can return the product within 30 days [chunk_id: 12]."

validate_citations(answer1, chunks)


# Test 2: Invalid citation
answer2 = "You can return the product within 60 days [chunk_id: 999]."

try:
    validate_citations(answer2, chunks)
except ValueError as error:
    print("Expected rejection:", error)


# Test 3: Missing citation
answer3 = "You can return the product within 30 days."

try:
    validate_citations(answer3, chunks)
except ValueError as error:
    print("Expected rejection:", error)
