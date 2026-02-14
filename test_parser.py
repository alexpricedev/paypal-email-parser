"""Test the PayPal email parser against the sample email.

Run: python test_parser.py
"""
import sys
import os

from paypal_parser import parse_paypal_email, ParseError, extract_notes


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


def test_notes_above_delimiter():
    """Notes typed above the Protonmail forwarding delimiter are extracted."""
    plain = "Groceries for the week\n------- Forwarded Message -------\nOriginal email content here"
    assert extract_notes(plain) == "Groceries for the week"
    print("PASSED — notes above delimiter extracted correctly")


def test_notes_multiline():
    """Multiline notes are preserved."""
    plain = "Groceries\nWeekly shop\n------- Forwarded Message -------\nOriginal"
    assert extract_notes(plain) == "Groceries\nWeekly shop"
    print("PASSED — multiline notes preserved correctly")


def test_no_delimiter():
    """No delimiter means no notes (direct email, not forwarded)."""
    plain = "Just some plain text email body"
    assert extract_notes(plain) == ""
    print("PASSED — no delimiter returns empty notes")


def test_delimiter_but_no_notes():
    """Delimiter present but nothing typed above it."""
    plain = "------- Forwarded Message -------\nOriginal email content"
    assert extract_notes(plain) == ""
    print("PASSED — delimiter with no notes returns empty")


def test_whitespace_only_above_delimiter():
    """Only whitespace above delimiter counts as no notes."""
    plain = "  \n\n------- Forwarded Message -------\nOriginal"
    assert extract_notes(plain) == ""
    print("PASSED — whitespace-only above delimiter returns empty")


def test_empty_plain():
    """Empty string input returns empty notes."""
    assert extract_notes("") == ""
    print("PASSED — empty string returns empty notes")


def test_none_plain():
    """None input returns empty notes (defensive — plain field missing from payload)."""
    assert extract_notes(None) == ""
    print("PASSED — None input returns empty notes")


if __name__ == "__main__":
    test_sample_email()
    test_malformed_html()
    test_notes_above_delimiter()
    test_notes_multiline()
    test_no_delimiter()
    test_delimiter_but_no_notes()
    test_whitespace_only_above_delimiter()
    test_empty_plain()
    test_none_plain()
    print("\nAll tests passed.")
