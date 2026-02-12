# PayPal Transaction Parser

Automatically parses PayPal debit card receipt emails and logs transactions to a Google Sheet.

## How It Works

```
PayPal sends receipt email
    → Protonmail (auto-forward rule)
    → CloudMailin (email-to-webhook)
    → Flask app on Railway (parse + write)
    → Google Sheets
```

1. PayPal sends a receipt email for each debit card transaction
2. Protonmail auto-forwards it to a CloudMailin address
3. CloudMailin POSTs the parsed email as JSON to the webhook
4. The Flask app extracts transaction data from the HTML using BeautifulSoup
5. The transaction is deduplicated by ID and appended to a Google Sheet
6. If parsing fails (e.g. PayPal changes their email template), an alert email is sent via Resend

## What Gets Extracted

| Field | Example |
|---|---|
| Date | 12 February 2026 |
| Amount | 4.85 |
| Merchant | PRET A MANGER |
| Transaction ID | 8U996209RL780471G |

## Stack

- **Python** + Flask
- **BeautifulSoup** for HTML parsing
- **gspread** for Google Sheets (service account auth)
- **Resend** for alert emails
- **CloudMailin** for inbound email (free tier)
- **Railway** for hosting

## Setup

See [docs/setup.md](docs/setup.md) for step-by-step instructions covering:

1. Google Cloud service account
2. Google Sheet creation
3. CloudMailin configuration
4. Resend API key
5. Railway deployment
6. Protonmail auto-forwarding

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
python3 test_parser.py

# Run the app locally
python3 app.py
```

## Project Structure

```
app.py               Flask webhook endpoint
paypal_parser.py      PayPal email HTML parser
sheets.py             Google Sheets read/write
alerts.py             Resend alert emails
test_parser.py        Parser tests
requirements.txt      Pinned dependencies
Procfile              Railway/gunicorn entrypoint
.env.example          Environment variable template
docs/setup.md         Setup guide
docs/paypal-demo.html Sample PayPal email for testing
```

## Environment Variables

| Variable | Description |
|---|---|
| `CLOUDMAILIN_USERNAME` | Basic auth username for webhook |
| `CLOUDMAILIN_PASSWORD` | Basic auth password for webhook |
| `RESEND_API_KEY` | Resend API key for alerts |
| `RESEND_FROM_EMAIL` | Verified sender address in Resend |
| `ALERT_EMAIL` | Where to send alerts (your email) |
| `GOOGLE_SHEETS_ID` | Spreadsheet ID from the URL |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Service account key JSON |

## Design Decisions

- **Parse rigidly, fail loudly.** The parser expects a specific HTML structure. If PayPal changes their template, it raises an error and sends an alert rather than guessing.
- **No database.** Google Sheets is the single source of truth.
- **Deduplication by transaction ID.** Checks the sheet before writing to avoid duplicates.
- **Deterministic only.** No LLM or fuzzy parsing. Extraction is exact or it fails.

## License

MIT
