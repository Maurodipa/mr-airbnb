import json
import os
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------
# Kaggle Submission Note: 
# This file demonstrates the "MCP Server" Key Concept.
# It exposes our local Airbnb Data Lake using the Model Context Protocol (MCP),
# allowing any MCP-compliant AI Agent to securely read the market data.
# ---------------------------------------------------------

mcp = FastMCP("Airbnb Data Lake Server")

DB_PATH = "banca_dati_airbnb.json"
PROCESSED_DB_PATH = "market_data_1month.json"

@mcp.resource("airbnb://database/raw")
def get_raw_database() -> str:
    """Returns the entire raw JSON Data Lake as a string."""
    if not os.path.exists(DB_PATH):
        return "{}"
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return f.read()

@mcp.tool()
def get_pure_rate(apartment_id: str, date: str) -> str:
    """
    Get the pure rate for a specific apartment on a specific date.
    
    Args:
        apartment_id: The ID of the apartment (e.g., '1589943047991118285')
        date: The target date in YYYY-MM-DD format (e.g., '2026-06-30')
    """
    if not os.path.exists(PROCESSED_DB_PATH):
        return json.dumps({"error": "Processed database not found"})
        
    with open(PROCESSED_DB_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid database format"})
            
    apt_data = data.get(apartment_id)
    if not apt_data:
        return json.dumps({"error": f"Apartment ID {apartment_id} not found."})
        
    date_info = apt_data.get("dates", {}).get(date)
    if not date_info:
        return json.dumps({"error": f"No data found for date {date}."})
        
    return json.dumps({
        "apartment_id": apartment_id,
        "date": date,
        "pure_rate": date_info.get("pure_rate"),
        "original_price": date_info.get("original_price"),
        "special_offer": date_info.get("special_offer", False),
        "collected_at": date_info.get("collected_at")
    })

if __name__ == "__main__":
    # Start the FastMCP server over standard input/output
    mcp.run()
