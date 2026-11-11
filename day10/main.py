
from rag import answer_question


def main():

    print("=" * 60)
    print("       PDF QUESTION ANSWERING SYSTEM")
    print("=" * 60)

    print("\nAsk questions about your five PDF documents.")
    print("Type 'exit' to quit.")

    while True:

        question = input("\nYou: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            print("Please enter a question.")
            continue

        try:

            result = answer_question(
                question=question,
                top_k=5
            )

            print("\n" + "=" * 60)
            print("ANSWER")
            print("=" * 60)

            print(result["answer"])

            print("\n" + "-" * 60)
            print("CITATION DETAILS")
            print("-" * 60)

            for citation in result["citations"]:

                print(
                    f"Chunk ID: {citation['chunk_id']} | "
                    f"Source: {citation['source']} | "
                    f"Page: {citation['page']} | "
                    f"Section: {citation['section']}"
                )

        except ValueError as error:

            print("\nAnswer rejected:")
            print(error)

        except Exception as error:

            print("\nSomething went wrong:")
            print(error)


if __name__ == "__main__":
    main()
