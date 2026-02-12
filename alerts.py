import logging
import os
from datetime import datetime, timezone

import resend

logger = logging.getLogger(__name__)

# Set API key once at module load, not on every call
resend.api_key = os.environ.get("RESEND_API_KEY", "")


def send_alert(subject: str, body: str) -> bool:
    """Send an alert email via Resend. Returns True if sent successfully."""
    if not resend.api_key:
        logger.error("RESEND_API_KEY not set — cannot send alert")
        return False

    from_email = os.environ.get("RESEND_FROM_EMAIL")
    to_email = os.environ.get("ALERT_EMAIL")

    if not from_email:
        logger.error("RESEND_FROM_EMAIL not set — cannot send alert")
        return False
    if not to_email:
        logger.error("ALERT_EMAIL not set — cannot send alert")
        return False

    params: resend.Emails.SendParams = {
        "from": from_email,
        "to": [to_email],
        "subject": f"[PayPal Parser] {subject}",
        "text": (
            f"Time: {datetime.now(timezone.utc).isoformat()}\n\n"
            f"{body}"
        ),
    }

    try:
        response = resend.Emails.send(params)
        logger.info(f"Alert email sent: {response['id']}")
        return True
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")
        return False
