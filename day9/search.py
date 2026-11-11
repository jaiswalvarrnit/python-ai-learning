
from embeddings import generate_embedding
from db import get_connection
from pgvector import Vector


def search_similar_chunks(
    question: str,
    limit: int = 3
):

    # Convert the user's question into a query embedding.
    query_embedding = generate_embedding(
        question,
        task_type="RETRIEVAL_QUERY"
    )
    query_vector = Vector(query_embedding)

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    content,
                    source,
                    page,
                    section,
                    embedding <=> %s AS distance
                FROM document_chunks
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (
                    query_vector,
                    query_vector,
                    limit
                )
            )

            results = cur.fetchall()

    for result in results:

        chunk_id, content, source, page, section, distance = result

        print("\n" + "=" * 60)
        print(f"Chunk ID: {chunk_id}")
        print(f"Source: {source}")
        print(f"Page: {page}")
        print(f"Section: {section}")
        print(f"Cosine distance: {distance:.4f}")
        print(f"Similarity: {1 - distance:.4f}")
        print(f"\nContent:\n{content}")


if __name__ == "__main__":

    question = "How many days do I have to return a product?"

    search_similar_chunks(question)
