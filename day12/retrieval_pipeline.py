import logging

from google.genai.errors import ServerError
from query_rewriter import rewrite_query
from search import hybrid_search
from reranker import rerank


logger = logging.getLogger(__name__)


def retrieve_with_reranking(
    question: str,
    candidate_k: int = 20,
    final_k: int = 5,
    use_query_rewriting: bool = True
) -> list[dict]:

    # Step 1: Rewrite the search query
    if use_query_rewriting:
        try:
            search_query = rewrite_query(question)
        except ServerError as error:
            if error.code != 503:
                raise
            logger.warning(
                "Gemini query rewriting returned HTTP 503; continuing "
                "with the original question."
            )
            search_query = question
    else:
        search_query = question

    print("\nOriginal question:", question)
    print("Search query:", search_query)

    # Step 2: Retrieve more candidates than we need
    candidates = hybrid_search(
        search_query,
        top_k=candidate_k
    )

    print("Retrieved candidates:", len(candidates))

    # Step 3: Rerank using the ORIGINAL user question
    results = rerank(
        question,
        candidates,
        top_k=final_k
    )

    return results