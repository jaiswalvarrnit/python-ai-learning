
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "gemini-embedding-001"
)

DIMENSIONS = 768


def generate_embedding(
    text: str,
    task_type: str = "RETRIEVAL_DOCUMENT"
) -> list[float]:

    response = client.models.embed_content(
        model=MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=DIMENSIONS
        )
    )

    return response.embeddings[0].values


if __name__ == "__main__":

    text = "Customers can request refunds within 30 days."

    vector = generate_embedding(text)

    print("Embedding dimensions:", len(vector))
    print("First 10 values:", vector[:10])
