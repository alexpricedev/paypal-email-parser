import base64
import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone

from flask import Flask, request, jsonify

from paypal_parser import parse_paypal_email, ParseError, extract_notes
from sheets import get_worksheet, is_duplicate, append_transaction
from alerts import send_alert

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1MB max payload

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def verify_auth() -> bool:
    """Verify Basic Auth credentials from CloudMailin."""
    username = os.environ.get("CLOUDMAILIN_USERNAME", "")
    password = os.environ.get("CLOUDMAILIN_PASSWORD", "")

    if not username:
        # Auth not configured — allow all requests (development only)
        return True

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        return False

    try:
        decoded = base64.b64decode(auth_header.split(" ", 1)[1]).decode("utf-8")
        req_user, req_pass = decoded.split(":", 1)
        return (hmac.compare_digest(req_user, username) and
                hmac.compare_digest(req_pass, password))
    except Exception:
        return False


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/webhook/incoming-email", methods=["POST"])
def incoming_email():
    """Receive a forwarded PayPal email from CloudMailin, parse it, and write to Google Sheets."""

    # Authenticate
    if not verify_auth():
        logger.warning("Unauthorized webhook request")
        return jsonify({"error": "Unauthorized"}), 401

    # Extract payload
    payload = request.get_json()
    if not payload:
        logger.error("No JSON payload received")
        return jsonify({"error": "No payload"}), 400

    html = payload.get("html", "")
    plain = payload.get("plain", "")
    headers = payload.get("headers", {})
    subject = headers.get("subject", "")
    email_hash = hashlib.sha256(html.encode()).hexdigest()[:16] if html else "no-html"

    logger.info(f"Received email: subject='{subject}' hash={email_hash}")

    # Validate subject line
    if "Receipt for your PayPal Debit Card purchase" not in subject:
        msg = f"Unexpected email subject: '{subject}'"
        logger.warning(msg)
        send_alert("Unexpected Email Received", f"{msg}\n\nEmail hash: {email_hash}")
        # Return 200 so CloudMailin doesn't retry — this isn't a transient error
        return jsonify({"status": "skipped", "reason": "unexpected subject"}), 200

    if not html:
        msg = "PayPal receipt email has no HTML body"
        logger.error(msg)
        send_alert("Missing HTML Body", f"{msg}\n\nSubject: {subject}\nEmail hash: {email_hash}")
        return jsonify({"error": "No HTML body"}), 200

    # Parse the email
    try:
        transaction = parse_paypal_email(html)
    except ParseError as e:
        msg = str(e)
        logger.error(f"Parse failed: {msg}")
        notes_context = extract_notes(plain)
        send_alert(
            "Template Change Detected",
            f"{msg}\n\n"
            f"Email hash: {email_hash}\n\n"
            + (f"Notes from forwarded email: {notes_context}\n\n" if notes_context else "")
            + "This likely means PayPal has changed their email template. "
            "The parser code needs updating.",
        )
        # Return 200 — retrying won't help if the template changed
        return jsonify({"error": msg}), 200

    notes = extract_notes(plain)
    transaction.notes = notes

    logger.info(
        f"Parsed transaction: id={transaction.transaction_id} "
        f"date={transaction.date} merchant={transaction.merchant} "
        f"amount=£{transaction.amount}"
        + (f" notes='{transaction.notes}'" if transaction.notes else "")
    )

    # Write to Google Sheets
    try:
        worksheet = get_worksheet()

        if is_duplicate(worksheet, transaction.transaction_id):
            logger.info(f"Duplicate skipped: {transaction.transaction_id}")
            return jsonify({
                "status": "duplicate",
                "transaction_id": transaction.transaction_id,
                "email_hash": email_hash,
            }), 200

        append_transaction(
            worksheet,
            transaction.date,
            transaction.amount,
            transaction.merchant,
            transaction.transaction_id,
            transaction.notes,
        )
        logger.info(f"Written to sheet: {transaction.transaction_id}")

    except Exception as e:
        msg = f"Google Sheets write failed: {e}"
        logger.error(msg)
        alert_sent = send_alert(
            "Google Sheets Error",
            f"{msg}\n\n"
            f"Transaction ID: {transaction.transaction_id}\n"
            f"Date: {transaction.date}\n"
            f"Merchant: {transaction.merchant}\n"
            f"Amount: £{transaction.amount}\n\n"
            f"Email hash: {email_hash}",
        )
        if not alert_sent:
            logger.critical(
                f"DUAL FAILURE: Sheets write failed AND alert email failed. "
                f"Transaction {transaction.transaction_id} needs manual attention."
            )
        # Return 500 so CloudMailin retries — Sheets may be temporarily unavailable
        return jsonify({"error": "Sheets write failed"}), 500

    return jsonify({
        "status": "success",
        "transaction_id": transaction.transaction_id,
        "email_hash": email_hash,
        "notes": transaction.notes,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
