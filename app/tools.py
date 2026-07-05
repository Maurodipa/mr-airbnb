import json
import os
import time

from app.market_scanner import run_scan_and_process

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "market_data_1month.json")

def _load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def run_market_scanner(start_date: str, end_date: str) -> dict:
    """Runs the market-scanner script to fetch and save raw Airbnb data for multiple competitors,
    and then processes it to extract pure rates, minimum stay, and special offers.

    Args:
        start_date: Start date for the scan (e.g., "2026-08-15").
        end_date: End date for the scan (e.g., "2026-08-20").

    Returns:
        dict: A status message indicating success and the time taken.
    """
    try:
        # 1. Run Python native scanner
        result = run_scan_and_process(start_date, end_date)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

def read_airbnb_data() -> dict:
    """Reads all processed historical pricing records from the Airbnb database (market_data_1month.json).
    This contains the processed pure rates, status, availability, and minStay.

    Returns:
        dict: The dictionary of all raw records.
    """
    db = _load_db()
    return {"status": "success", "records": db}
