# Setup Guide

Step-by-step instructions to get the PayPal transaction parser running.

## Prerequisites

- A Google account (for Google Sheets and Google Cloud)
- A CloudMailin account (free tier)
- A Resend account with a verified domain
- A Railway account
- Python 3.10+

---

## 1. Google Cloud — Service Account

This creates a non-human identity that can read/write your Google Sheet.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (e.g., `paypal-finance-tracker`)
3. Enable two APIs:
   - Go to **APIs & Services > Library**
   - Search for and enable **Google Sheets API**
   - Search for and enable **Google Drive API**
4. Create a service account:
   - Go to **APIs & Services > Credentials**
   - Click **Create Credentials > Service Account**
   - Name it (e.g., `sheets-writer`)
   - Skip the optional role/access steps
   - Click **Done**
5. Download the JSON key:
   - Click on the service account email in the credentials list
   - Go to the **Keys** tab
   - Click **Add Key > Create new key > JSON**
   - Save the downloaded file — this is a secret

You'll need the entire contents of this JSON file as an environment variable later.

---

## 2. Google Sheet

1. Create a new Google Sheet
2. Add a header row in row 1 with these columns:
   ```
   Date | Amount | Merchant | Transaction ID
   ```
3. Share the sheet with your service account:
   - Click **Share**
   - Paste the service account email (looks like `sheets-writer@your-project.iam.gserviceaccount.com`)
   - Give it **Editor** access
   - Uncheck "Notify people"
4. Copy the spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/THIS_IS_THE_ID/edit
   ```

---

## 3. CloudMailin

1. Sign up at [cloudmailin.com](https://www.cloudmailin.com) (free tier: 200 emails/month)
2. Create a new address — you'll get something like `abc123@cloudmailin.net`
3. Set the format to **JSON (Normalized)**
4. Set the target URL to your Railway app's URL (you'll get this in step 5):
   ```
   https://USERNAME:PASSWORD@your-app.up.railway.app/webhook/incoming-email
   ```
   Replace `USERNAME` and `PASSWORD` with values you choose. These must match the `CLOUDMAILIN_USERNAME` and `CLOUDMAILIN_PASSWORD` environment variables.

---

## 4. Resend

1. Log into [resend.com](https://resend.com)
2. Make sure you have a verified sending domain
3. Copy your API key from the dashboard
4. Note the "from" address you'll use (e.g., `alerts@yourdomain.com`)

---

## 5. Railway Deployment

1. Push this repo to GitHub (if not already)
2. Log into [railway.app](https://railway.app)
3. Click **New Project > Deploy from GitHub Repo**
4. Select this repository
5. Railway will auto-detect Python and use the `Procfile`
6. Go to **Variables** and add:

   | Variable | Value |
   |---|---|
   | `CLOUDMAILIN_USERNAME` | Username you chose in step 3 |
   | `CLOUDMAILIN_PASSWORD` | Password you chose in step 3 |
   | `RESEND_API_KEY` | Your Resend API key |
   | `RESEND_FROM_EMAIL` | Your verified Resend sender (e.g., `alerts@yourdomain.com`) |
   | `ALERT_EMAIL` | Your Protonmail address |
   | `GOOGLE_SHEETS_ID` | The spreadsheet ID from step 2 |
   | `GOOGLE_SERVICE_ACCOUNT_JSON` | The entire contents of the JSON key file from step 1 |

7. Deploy. Railway will give you a public URL like `your-app.up.railway.app`
8. Go back to CloudMailin and update the target URL with your Railway URL

### Verify deployment

```bash
curl https://your-app.up.railway.app/health
```

Should return:
```json
{"status": "ok", "timestamp": "2026-02-12T..."}
```

---

## 6. Protonmail Auto-Forwarding (Recommended)

This eliminates manual forwarding — emails from PayPal are automatically sent to CloudMailin.

**Requires a paid Protonmail plan (Mail Plus or Proton Unlimited).**

1. Open Protonmail web
2. Go to **Settings > All settings > Proton Mail > Auto-reply and forward**
3. Click **Forward emails > Add forwarding rule**
4. Set:
   - **Condition:** From equals `service@paypal.co.uk`
   - **Forward to:** Your CloudMailin address (e.g., `abc123@cloudmailin.net`)
5. CloudMailin will send a verification email to the forwarding address — since it's an inbound-only address, you may need to check the CloudMailin dashboard to confirm delivery, or temporarily point it at an inbox you can read for verification
6. Once verified, PayPal receipt emails will be automatically forwarded

If auto-forwarding isn't available on your plan, manually forward PayPal receipt emails to your CloudMailin address.

---

## 7. Testing

### Test the parser locally

```bash
python3 test_parser.py
```

### Test the webhook locally

Start the app:
```bash
python3 app.py
```

Send a test email payload (requires `GOOGLE_*` env vars to be set for the Sheets write):

```bash
curl -X POST http://localhost:8080/webhook/incoming-email \
  -H "Content-Type: application/json" \
  -d '{
    "headers": {
      "subject": "Receipt for your PayPal Debit Card purchase"
    },
    "html": "'"$(cat docs/paypal-demo.html | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')"'"
  }'
```

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `CLOUDMAILIN_USERNAME` | No* | Basic auth username for webhook. *If unset, auth is disabled (dev only). |
| `CLOUDMAILIN_PASSWORD` | No* | Basic auth password for webhook. |
| `RESEND_API_KEY` | Yes | Resend API key for alert emails |
| `RESEND_FROM_EMAIL` | Yes | Verified sender address in Resend |
| `ALERT_EMAIL` | Yes | Where to send alerts (your Protonmail) |
| `GOOGLE_SHEETS_ID` | Yes | Spreadsheet ID from the Google Sheet URL |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes | Full JSON contents of the service account key file |
