from db import get_connection
from embeddings import generate_embedding
from pgvector import Vector


def vector_search(question: str, top_k: int = 5) -> list[dict]:
    """Retrieve chunks using embedding similarity."""

    query_embedding = generate_embedding(
        question,
        task_type="RETRIEVAL_QUERY"
    )
    query_vector = Vector(query_embedding)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, content, source, page, section,
                       embedding <=> %s AS distance
                FROM document_chunks
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (query_vector, query_vector, top_k)
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "content": row[1],
            "source": row[2],
            "page": row[3],
            "section": row[4],
            "distance": float(row[5]),
        }
        for row in rows
    ]


def keyword_search(question: str, top_k: int = 5) -> list[dict]:
    """Retrieve chunks using PostgreSQL full-text search."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, content, source, page, section,
                       ts_rank_cd(
                           content_tsv,
                           websearch_to_tsquery('english', %s)
                       ) AS score
                FROM document_chunks
                WHERE content_tsv @@ websearch_to_tsquery('english', %s)
                ORDER BY score DESC
                LIMIT %s
                """,
                (question, question, top_k)
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "content": row[1],
            "source": row[2],
            "page": row[3],
            "section": row[4],
            "score": float(row[5]),
        }
        for row in rows
    ]

def reciprocal_rank_fusion(
    vector_results: list[dict],
    keyword_results: list[dict],
    top_k: int = 5,
    rrf_k: int = 60,
) -> list[dict]:

    scores = {}
    chunk_data = {}

    # Process vector search rankings
    for rank, chunk in enumerate(vector_results, start=1):
        chunk_id = chunk["id"]

        scores[chunk_id] = scores.get(chunk_id, 0) + (
            1 / (rrf_k + rank)
        )
        chunk_data[chunk_id] = chunk

    # Process keyword search rankings
    for rank, chunk in enumerate(keyword_results, start=1):
        chunk_id = chunk["id"]

        scores[chunk_id] = scores.get(chunk_id, 0) + (
            1 / (rrf_k + rank)
        )
        chunk_data[chunk_id] = chunk_data.get(chunk_id, chunk)

    # Sort chunks by their fused score
    ranked_ids = sorted(
        scores,
        key=lambda chunk_id: scores[chunk_id],
        reverse=True
    )

    results = []

    for chunk_id in ranked_ids[:top_k]:
        chunk = chunk_data[chunk_id].copy()
        chunk["rrf_score"] = scores[chunk_id]
        results.append(chunk)

    return results


def hybrid_search(question: str, top_k: int = 5) -> list[dict]:

    vector_results = vector_search(question, top_k=top_k)
    keyword_results = keyword_search(question, top_k=top_k)

    return reciprocal_rank_fusion(
        vector_results,
        keyword_results,
        top_k=top_k
    )