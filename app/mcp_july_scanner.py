import asyncio
import json
import os
import random
import time
from datetime import datetime, timedelta

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from app.market_scanner import FEE_MULTIPLIER, load_competitors_config, parse_price

MCP_SERVER_PATH = r"C:\Users\mauro\AppData\Roaming\npm\node_modules\@openbnb\mcp-server-airbnb\dist\index.js"
OUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "july_raw.json")
CLEANED_OUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "july_clean.json")

async def scan_july_async():
    dates = ["2026-07-24", "2026-07-28"]

    competitors, cleaning_fees = load_competitors_config()
    if not competitors:
        print("Errore: competitors non trovati")
        return

    market_data = {}
    
    start_execution = time.time()
    server_params = StdioServerParameters(command="node", args=[MCP_SERVER_PATH], env={"NODE_TLS_REJECT_UNAUTHORIZED": "0"})

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                market_data["static_details"] = {}

                for date_str in dates:
                    market_data[date_str] = {}

                    for apt_id in competitors:
                        print(f"[JULY SCAN] [{date_str}] Appartamento: {apt_id}")
                        found = False
                        current_date = datetime.strptime(date_str, "%Y-%m-%d")

                        for n in range(1, 8):
                            checkout_date = current_date + timedelta(days=n)
                            checkout_str = checkout_date.strftime("%Y-%m-%d")

                            try:
                                result = await session.call_tool("airbnb_listing_price", arguments={"id": apt_id, "checkin": date_str, "checkout": checkout_str})
                                content = json.loads(result.content[0].text)

                                if content.get("available"):
                                    bookIt = content.get("fullBookItData", {})
                                    if bookIt:
                                        if not found:
                                            market_data[date_str][apt_id] = {
                                                "status": "OK",
                                                "minStay": n,
                                                "checkout": checkout_str,
                                                "rawResponse": bookIt,
                                                "collected_at": datetime.now().isoformat(),
                                                "additional_nights": []
                                            }
                                            print(f"--> Trovato! minStay: {n}")
                                            found = True
                                            extra_scans = 0
                                        else:
                                            market_data[date_str][apt_id]["additional_nights"].append({
                                                "minStay": n,
                                                "checkout": checkout_str,
                                                "rawResponse": bookIt
                                            })
                                            extra_scans += 1
                                            if extra_scans >= 2:
                                                break
                            except Exception as e:
                                print(f"Errore MCP: {e}")

                            await asyncio.sleep(random.uniform(0.2, 0.5))

                        if not found:
                            market_data[date_str][apt_id] = {
                                "status": "Non disponibile",
                                "collected_at": datetime.now().isoformat()
                            }
                            print("--> Occupato / MS > 7 notti.")

                        # Write temp so we don't lose data
                        with open(OUT_FILE, "w", encoding="utf-8") as f:
                            json.dump(market_data, f, indent=2)

                        await asyncio.sleep(random.uniform(2.0, 5.0))
    except Exception as e:
        print(f"Server MCP error: {e}")

    # Process data
    processed = {}
    for date, apts in market_data.items():
        if date == "static_details":
            continue
        processed[date] = {}
        for apt, entry in apts.items():
            if not entry or entry.get('status') != 'OK' or not entry.get('rawResponse'):
                processed_entry = {'status': 'Non disponibile'}
                processed[date][apt] = processed_entry
                continue

            total_gross = 0.0
            taxes = 0.0
            book_it = entry.get('rawResponse') or {}
            structured_price = book_it.get("structuredDisplayPrice") or {}
            explanation_data = structured_price.get("explanationData") or {}
            price_details = explanation_data.get("priceDetails") or []

            for group in price_details:
                for item in group.get('items', []):
                    desc = item.get('description', '')
                    if desc in ('Taxes', 'Tasse'):
                        taxes = parse_price(item.get('priceString', ''))
                    if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                        total_gross = parse_price(item.get('priceString', ''))

            cleaning_fee = cleaning_fees.get(apt, 50)
            min_stay = entry.get('minStay', 1)

            total_net_with_cleaning = (total_gross - taxes) / FEE_MULTIPLIER
            pure_total = total_net_with_cleaning - cleaning_fee
            pure_nightly = pure_total / min_stay

            processed_entry = {
                'status': 'OK',
                'rate': round(pure_nightly),
                'minStay': min_stay
            }
            processed[date][apt] = processed_entry

    with open(CLEANED_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)

    elapsed_seconds = round(time.time() - start_execution, 2)
    print(f"Completato in {elapsed_seconds}s")

if __name__ == "__main__":
    asyncio.run(scan_july_async())
