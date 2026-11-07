import time
from ticket_classifier import classify_ticket

# Ticket text and expected category, labelled by us.
TEST_TICKETS = [
    ("I was charged twice for my order.", "Billing"),
    ("Please refund my annual subscription.", "Billing"),
    ("My invoice has the wrong amount.", "Billing"),
    ("My payment failed but money was deducted.", "Billing"),

    ("The app crashes whenever I open settings.", "Technical"),
    ("The website returns a 500 error.", "Technical"),
    ("I cannot upload my PDF file.", "Technical"),
    ("The latest update broke dark mode.", "Technical"),

    ("I forgot my password and cannot log in.", "Account"),
    ("Please change the email on my account.", "Account"),
    ("My account has been locked.", "Account"),
    ("I want to delete my profile.", "Account"),

    ("My package has not arrived yet.", "Shipping"),
    ("The tracking page says delivered, but I received nothing.", "Shipping"),
    ("Can I change the delivery address for my order?", "Shipping"),
    ("My package arrived damaged.", "Shipping"),

    ("Do you offer discounts for students?", "Other"),
    ("Where can I read your company's privacy policy?", "Other"),
    ("I would like to suggest a new feature.", "Other"),
    ("What are your customer support hours?", "Other"),
]


def main():
    correct = 0
    successful = 0
    failed = 0
    total = len(TEST_TICKETS)

    for index, (ticket, expected_category) in enumerate(
        TEST_TICKETS, start=1
    ):
        result = None

        # Retry up to 3 times if rate limited
        for attempt in range(3):
            try:
                result = classify_ticket(ticket)
                break

            except Exception as exc:
                error = str(exc)

                if "429" in error or "RESOURCE_EXHAUSTED" in error:
                    wait_time = 35 * (attempt + 1)

                    print(
                        f"\nRate limit hit on ticket {index}. "
                        f"Waiting {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                else:
                    print(f"\nTicket {index}: ERROR - {exc}")
                    break

        if result is not None:
            successful += 1

            is_correct = result.category == expected_category

            if is_correct:
                correct += 1

            status = "PASS" if is_correct else "FAIL"

            print(f"\nTicket {index}: {status}")
            print(f"Text: {ticket}")
            print(f"Expected: {expected_category}")
            print(f"Predicted: {result.category}")
            print(f"Priority: {result.priority}")
            print(f"Summary: {result.summary}")

        else:
            failed += 1

        # Stay below the 5 requests/minute limit
        if index < total:
            time.sleep(13)

    print("\n--- Evaluation Results ---")
    print(f"Total tickets: {total}")
    print(f"Successful API responses: {successful}")
    print(f"Failed API responses: {failed}")
    print(f"Correct classifications: {correct}")

    if successful > 0:
        accuracy = correct / successful * 100
        print(f"Category accuracy: {accuracy:.1f}%")
    else:
        print("Category accuracy: Not available")


if __name__ == "__main__":
    main()
