import json
from pathlib import Path

from search import (
    keyword_search,
    reciprocal_rank_fusion,
    vector_search,
)


QUESTIONS = {
    "1": "How many days do I have to return a product?",
    "2": "When do API tokens expire?",
    "3": "Find the exact token expiry value in seconds.",
    "4": "How much annual paid leave do employees receive?",
    "5": "What is overfitting?",
    "6": "What should an engineer do after a major production outage?",
    "7": "What does the refund policy say about damaged products?",
    "8": "Which HTTP status code indicates an unauthorized request?",
    "9": "What is the procedure for escalating a critical incident?",
    "10": "What is the company's process for handling an employee resignation?",
}

TOP_K = 5
GROUND_TRUTH_PATH = Path(__file__).with_name("ground_truth.json")


def load_ground_truth() -> dict[str, set[int]]:
    with GROUND_TRUTH_PATH.open(encoding="utf-8") as file:
        raw_ground_truth = json.load(file)

    if not isinstance(raw_ground_truth, dict):
        raise ValueError("ground_truth.json must contain a JSON object.")

    if set(raw_ground_truth) != set(QUESTIONS):
        raise ValueError(
            "Ground-truth question IDs must exactly match the questions "
            f"in evaluate.py: {sorted(QUESTIONS)}."
        )

    ground_truth: dict[str, set[int]] = {}
    for question_id, chunk_ids in raw_ground_truth.items():
        if not isinstance(chunk_ids, list) or any(
            type(chunk_id) is not int for chunk_id in chunk_ids
        ):
            raise ValueError(
                f"Ground truth for question {question_id} must be a list "
                "of integer chunk IDs."
            )
        ground_truth[question_id] = set(chunk_ids)

    return ground_truth


def recall_at_k(relevant_ids: set[int], retrieved_ids: list[int]) -> float | None:
    if not relevant_ids:
        return None
    return len(relevant_ids.intersection(retrieved_ids)) / len(relevant_ids)


def format_recall(relevant_ids: set[int], retrieved_ids: list[int]) -> str:
    recall = recall_at_k(relevant_ids, retrieved_ids)
    if recall is None:
        return "N/A"
    hits = len(relevant_ids.intersection(retrieved_ids))
    return f"{hits}/{len(relevant_ids)} ({recall:.0%})"


def main() -> None:
    ground_truth = load_ground_truth()
    vector_recalls: list[float] = []
    keyword_recalls: list[float] = []
    hybrid_recalls: list[float] = []

    print(f"Retrieval evaluation (Recall@{TOP_K})")
    print("Empty ground-truth questions are shown but excluded from averages.")
    print()

    for question_id, question in QUESTIONS.items():
        relevant_ids = ground_truth[question_id]

        vector_results = vector_search(question, top_k=TOP_K)
        keyword_results = keyword_search(question, top_k=TOP_K)
        hybrid_results = reciprocal_rank_fusion(
            vector_results,
            keyword_results,
            top_k=TOP_K,
        )

        vector_ids = [chunk["id"] for chunk in vector_results]
        keyword_ids = [chunk["id"] for chunk in keyword_results]
        hybrid_ids = [chunk["id"] for chunk in hybrid_results]

        vector_recall = recall_at_k(relevant_ids, vector_ids)
        keyword_recall = recall_at_k(relevant_ids, keyword_ids)
        hybrid_recall = recall_at_k(relevant_ids, hybrid_ids)
        if (
            vector_recall is not None
            and keyword_recall is not None
            and hybrid_recall is not None
        ):
            vector_recalls.append(vector_recall)
            keyword_recalls.append(keyword_recall)
            hybrid_recalls.append(hybrid_recall)

        relevant_label = (
            ", ".join(str(chunk_id) for chunk_id in sorted(relevant_ids))
            if relevant_ids else "none"
        )
        print(f"Q{question_id}: {question}")
        print(f"  Relevant IDs: {relevant_label}")
        print(
            f"  Vector: {format_recall(relevant_ids, vector_ids)} "
            f"| top {TOP_K}: {vector_ids}"
        )
        print(
            f"  Keyword: {format_recall(relevant_ids, keyword_ids)} "
            f"| top {TOP_K}: {keyword_ids}"
        )
        print(
            f"  Hybrid: {format_recall(relevant_ids, hybrid_ids)} "
            f"| top {TOP_K}: {hybrid_ids}"
        )

    print()
    if vector_recalls and keyword_recalls and hybrid_recalls:
        vector_average = sum(vector_recalls) / len(vector_recalls)
        keyword_average = sum(keyword_recalls) / len(keyword_recalls)
        hybrid_average = sum(hybrid_recalls) / len(hybrid_recalls)
        print(
            f"Macro Recall@{TOP_K} over {len(vector_recalls)} answerable "
            f"questions: vector={vector_average:.1%}, "
            f"keyword={keyword_average:.1%}, "
            f"hybrid={hybrid_average:.1%}"
        )
    else:
        print("No questions with relevant chunks; recall averages unavailable.")


if __name__ == "__main__":
    main()
