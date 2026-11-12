import json
import os

from app.cleaning_estimator import estimate_cleaning_fees
from app.market_scanner import run_scan_and_process
from app.mcp_market_scanner import run_mcp_scan_and_process

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "banca_dati_airbnb_MCPserver_cleaned.json")

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

def run_mcp_market_scanner(start_date: str, end_date: str) -> dict:
    """Runs the market-scanner script using the MCP server to fetch and save raw Airbnb data for multiple competitors,
    and then processes it to extract pure rates, minimum stay, and special offers.

    Args:
        start_date: Start date for the scan (e.g., "2026-08-15").
        end_date: End date for the scan (e.g., "2026-08-20").

    Returns:
        dict: A status message indicating success and the time taken.
    """
    try:
        # Run MCP-based scanner
        result = run_mcp_scan_and_process(start_date, end_date)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_cleaning_estimator() -> dict:
    """Estimates the fixed cleaning fee for each apartment using linear regression on the raw data.
    Reads from banca_dati_airbnb_MCPserver.json and writes to cleaning_fees_estimated.json.
    
    Returns:
        dict: A status message containing the estimated fees.
    """
    try:
        return estimate_cleaning_fees()
    except Exception as e:
        return {"status": "error", "message": str(e)}
