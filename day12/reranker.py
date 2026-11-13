from sentence_transformers import CrossEncoder

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Load once, not once per question.
reranker = CrossEncoder(MODEL_NAME)


def rerank(
    question: str,
    candidates: list[dict],
    top_k: int = 5
) -> list[dict]:

    if not candidates:
        return []

    pairs = [
        (question, chunk["content"])
        for chunk in candidates
    ]

    scores = reranker.predict(pairs)

    ranked = []

    for chunk, score in zip(candidates, scores):
        result = chunk.copy()
        result["rerank_score"] = float(score)
        ranked.append(result)

    ranked.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    return ranked[:top_k]