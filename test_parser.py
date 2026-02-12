"""Test the PayPal email parser against the sample email.

Run: python test_parser.py
"""
import sys
import os

from paypal_parser import parse_paypal_email, ParseError


def test_sample_email():
    """Parse docs/paypal-demo.html and verify extracted values match expected output."""
    sample_path = os.path.join(os.path.dirname(__file__), "docs", "paypal-demo.html")

    with open(sample_path, "r") as f:
        html = f.read()

    transaction = parse_paypal_email(html)

    # Expected values from the sample email
    expected = {
        "transaction_id": "8U996209RL780471G",
        "date": "12 February 2026",
        "merchant": "PRET A MANGER",
        "amount": 4.85,
    }

    errors = []
    if transaction.transaction_id != expected["transaction_id"]:
        errors.append(
            f"Transaction ID: expected '{expected['transaction_id']}', "
            f"got '{transaction.transaction_id}'"
        )
    if transaction.date != expected["date"]:
        errors.append(
            f"Date: expected '{expected['date']}', got '{transaction.date}'"
        )
    if transaction.merchant != expected["merchant"]:
        errors.append(
            f"Merchant: expected '{expected['merchant']}', got '{transaction.merchant}'"
        )
    if transaction.amount != expected["amount"]:
        errors.append(
            f"Amount: expected {expected['amount']}, got {transaction.amount}"
        )

    if errors:
        print("FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("PASSED — all fields match expected values:")
    print(f"  Transaction ID: {transaction.transaction_id}")
    print(f"  Date:           {transaction.date}")
    print(f"  Merchant:       {transaction.merchant}")
    print(f"  Amount:         £{transaction.amount}")


def test_malformed_html():
    """Verify that malformed HTML raises ParseError."""
    try:
        parse_paypal_email("<html><body>This is not a PayPal email</body></html>")
        print("FAILED — expected ParseError for malformed HTML, but none was raised")
        sys.exit(1)
    except ParseError as e:
        print(f"PASSED — malformed HTML correctly raises ParseError: {e}")


if __name__ == "__main__":
    test_sample_email()
    test_malformed_html()
    print("\nAll tests passed.")
