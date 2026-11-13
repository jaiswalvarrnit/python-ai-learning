from search import vector_search, hybrid_search
from retrieval_pipeline import retrieve_with_reranking

QUESTIONS = [
    "How many days do I have to return a product?",
    "When do API tokens expire?",
    "Find the exact token expiry value in seconds.",
    "How much annual paid leave do employees receive?",
    "What is overfitting?",
    "What should an engineer do after a major production outage?",
    "What does the refund policy say about damaged products?",
    "Which HTTP status code indicates an unauthorized request?",
    "What is the procedure for escalating a critical incident?",
    "What is the company's process for handling an employee resignation?"
]

for question in QUESTIONS:

    print("\n" + "=" * 80)
    print("QUESTION:", question)

    # A: Vector-only
    vector_results = vector_search(question, top_k=5)

    # B: Hybrid
    hybrid_results = hybrid_search(question, top_k=5)

    # C: Query rewriting + hybrid + reranking
    advanced_results = retrieve_with_reranking(
        question,
        candidate_k=20,
        final_k=5,
        use_query_rewriting=True
    )

    print("\nA. VECTOR-ONLY")
    for chunk in vector_results:
        print(chunk["id"], chunk["content"][:120])

    print("\nB. HYBRID")
    for chunk in hybrid_results:
        print(chunk["id"], chunk["content"][:120])

    print("\nC. QUERY REWRITE + RERANK")
    for chunk in advanced_results:
        print(
            chunk["id"],
            round(chunk["rerank_score"], 4),
            chunk["content"][:120]
        )