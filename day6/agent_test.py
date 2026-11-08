
from agent import run_agent


TEST_TASKS = [
    # 1. Basic arithmetic
    "Calculate 4500 multiplied by 12.",

    # 2. New calculator operators
    "Calculate the remainder when 987 is divided by 23, then calculate "
    "2 to the power of 8 and floor-divide 100 by 9.",

    # 3. Customer lookup with a newly added customer
    "Find customer C106 and report their name, plan, monthly fee, and status.",

    # 4. Customer lookup plus annual calculation
    "Find C104, then calculate their annual subscription fee from the "
    "monthly fee. Include the customer's plan and status.",

    # 5. Multiple tools plus text analysis
    "Find C102, create a sentence containing their name, plan, and status, "
    "then analyze that sentence and report its word and character counts.",

    # 6. Multi-step arithmetic
    "Calculate (2500 multiplied by 12) plus 5000, then floor-divide the "
    "result by 7.",

    # 7. Unknown customer
    "Find customer C999 and tell me their plan.",

    # 8. Division by zero
    "Calculate 100 divided by zero.",

    # 9. Text analysis with punctuation and numbers
    "Analyze this exact text: Release 6.2: AI tools are useful, useful, "
    "and fast!",

    # 10. Mixed task with a missing customer
    "Find customer C999 and calculate their annual fee. "
    "Do not invent any customer details.",

    # 11. Several customer comparisons
    "Look up C101, C105, and C107. Compare their plans, statuses, and "
    "monthly fees without inventing any missing details.",

    # 12. Combined customer and arithmetic reasoning
    "Find C103 and C106. Calculate their combined monthly fee and annual "
    "fee, and identify whether both customers are active.",

    # 13. Text analysis with multiple lines
    "Analyze this two-line text and report all available statistics: "
    "Customer C101 is Active.\nCustomer C102 is Inactive.",

    # 14. Unsupported external-data request
    "Tell me the current weather in Bangalore. Do not guess or use "
    "information that is not available in the tools.",

    # 15. Invalid arithmetic operation
    "Use the calculator with an unsupported square-root operation. "
    "Report the tool error instead of guessing."
]


def main():

    results = []

    for index, task in enumerate(TEST_TASKS, start=1):

        print(f"\n{'=' * 60}")
        print(f"TEST {index}/{len(TEST_TASKS)}")
        print("Task:", task)

        try:
            result = run_agent(task, max_steps=6)

            results.append({
                "test": index,
                "status": result["status"],
                "answer": result["answer"]
            })

            print("\nStatus:", result["status"])
            print("Answer:", result["answer"])

        except Exception as exc:
            results.append({
                "test": index,
                "status": "api_error",
                "answer": str(exc)
            })

            print("Test failed:", exc)

        # The agent's request limiter controls every Gemini request.
        if index < len(TEST_TASKS):
            print("\nThe agent rate limiter controls the next request.")

    print("\n\n========== TEST SUMMARY ==========")

    for result in results:
        print(
            f"Test {result['test']}: "
            f"{result['status']}"
        )


if __name__ == "__main__":
    main()
