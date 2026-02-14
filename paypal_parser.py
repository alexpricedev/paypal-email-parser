import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


class ParseError(Exception):
    """Raised when the email template doesn't match the expected structure."""
    pass


@dataclass
class Transaction:
    transaction_id: str
    date: str
    merchant: str
    amount: float
    notes: str = ""


PROTONMAIL_DELIMITER = "------- Forwarded Message -------"


def extract_notes(plain_text: str | None) -> str:
    """Extract user-typed notes from above the Protonmail forwarding delimiter.

    When the user forwards a PayPal receipt from Protonmail, any text they type
    above the forwarded content appears before the delimiter in the plain text body.
    Returns empty string if no notes are found.
    """
    if not plain_text:
        return ""
    parts = plain_text.split(PROTONMAIL_DELIMITER, 1)
    if len(parts) < 2:
        return ""
    return parts[0].strip()


def parse_paypal_email(html: str) -> Transaction:
    """Parse a PayPal debit card receipt email and extract transaction data.

    Expects the PayPal "Receipt for your PayPal Debit Card purchase" email
    format with table elements using id="transactionRow". Each row has two
    <tr> elements: a bold label and a value.

    Returns a Transaction with the extracted fields.
    Raises ParseError if the template structure doesn't match expectations.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Find all transactionRow tables — each contains a label/value pair
    rows = soup.find_all("table", id="transactionRow")
    if not rows:
        raise ParseError(
            "No transactionRow tables found in email HTML. "
            "PayPal may have changed their email template."
        )

    # Extract label → value pairs
    fields = {}
    for row in rows:
        trs = row.find_all("tr")
        if len(trs) < 2:
            continue

        label = trs[0].get_text(strip=True)
        value_td = trs[1].find("td")
        if value_td is None:
            continue

        # Transaction ID value is inside an <a> tag — extract link text, not href
        a_tag = value_td.find("a")
        if a_tag:
            value = a_tag.get_text(strip=True)
        else:
            value = value_td.get_text(strip=True)

        fields[label] = value

    # Validate all required fields are present
    required = ["Transaction ID", "Transaction date", "Merchant", "Total amount"]
    missing = [f for f in required if f not in fields]
    if missing:
        raise ParseError(
            f"Missing expected fields: {missing}. "
            f"Found fields: {list(fields.keys())}. "
            f"PayPal may have changed their email template."
        )

    # Parse amount: "£4.85 GBP" or "£1,234.56 GBP" → float
    amount_str = fields["Total amount"]
    amount_match = re.search(r"£([\d,.]+)", amount_str)
    if not amount_match:
        raise ParseError(
            f"Could not parse amount from '{amount_str}'. "
            f"Expected format like '£4.85 GBP'."
        )
    amount = float(amount_match.group(1).replace(",", ""))

    return Transaction(
        transaction_id=fields["Transaction ID"],
        date=fields["Transaction date"],
        merchant=fields["Merchant"],
        amount=amount,
    )
