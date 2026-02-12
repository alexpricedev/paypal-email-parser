import json
import logging
import os

import gspread

logger = logging.getLogger(__name__)


def get_sheets_client():
    """Create a gspread client authenticated via service account."""
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")
    creds = json.loads(creds_json)
    return gspread.service_account_from_dict(creds)


def get_worksheet():
    """Open the configured Google Sheet and return the first worksheet."""
    gc = get_sheets_client()
    sheet_id = os.environ.get("GOOGLE_SHEETS_ID")
    if not sheet_id:
        raise RuntimeError("GOOGLE_SHEETS_ID environment variable not set")
    sh = gc.open_by_key(sheet_id)
    return sh.sheet1


def is_duplicate(worksheet, transaction_id: str) -> bool:
    """Check if a transaction ID already exists in the sheet.

    Fetches only the Transaction ID column (column D) rather than
    the entire sheet, so this stays fast as the sheet grows.
    """
    # Column 4 = Transaction ID (columns: Date, Amount, Merchant, Transaction ID)
    existing_ids = worksheet.col_values(4)
    return transaction_id in existing_ids


def append_transaction(
    worksheet, date: str, amount: float, merchant: str, transaction_id: str
):
    """Append a transaction row to the sheet."""
    worksheet.append_row(
        [date, amount, merchant, transaction_id],
        value_input_option="USER_ENTERED",
    )
    logger.info(f"Appended transaction {transaction_id} to sheet")
