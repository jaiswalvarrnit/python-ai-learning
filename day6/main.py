
from dotenv import load_dotenv

load_dotenv()

from agent import run_agent


def main():

    print("\n=== Gemini AI Agent ===")
    print("Type 'exit' to quit.\n")

    while True:

        user_task = input("\nYou: ").strip()

        if user_task.lower() == "exit":
            print("Goodbye!")
            break

        if not user_task:
            print("Please enter a task.")
            continue

        result = run_agent(user_task)

        print("\n=== AGENT RESULT ===")
        print("Status:", result["status"])
        print("Answer:", result["answer"])
        print("Steps:", result.get("steps", "N/A"))


if __name__ == "__main__":
    main()
