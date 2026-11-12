import asyncio
import json
import os
import random
import re
import time
from datetime import datetime, timedelta

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from app.market_scanner import FEE_MULTIPLIER, load_competitors_config, parse_price

MCP_SERVER_PATH = r"C:\Users\mauro\AppData\Roaming\npm\node_modules\@openbnb\mcp-server-airbnb\dist\index.js"
OUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "banca_dati_airbnb_MCPserver.json")
CLEANED_OUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "banca_dati_airbnb_MCPserver_cleaned.json")

async def scan_via_mcp_async(start_date_str: str, end_date_str: str, resume: bool = False):
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not date_pattern.match(start_date_str) or not date_pattern.match(end_date_str):
        return {"status": "error", "message": "Security Error: Invalid date format. Must be YYYY-MM-DD."}

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    competitors, cleaning_fees = load_competitors_config()
    if not competitors:
        return {"status": "error", "message": "competitors.txt not found or invalid format"}

    market_data = {}
    consecutive_errors = 0
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, encoding="utf-8") as f:
                market_data = json.load(f)
        except json.JSONDecodeError:
            pass

    session_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".current_scan_session.json")
    if resume and os.path.exists(session_file):
        try:
            with open(session_file, "r", encoding="utf-8") as sf:
                session_info = json.load(sf)
                scan_session_start = session_info.get("start_time", datetime.now().isoformat())
        except Exception:
            scan_session_start = datetime.now().isoformat()
    else:
        scan_session_start = datetime.now().isoformat()
        try:
            with open(session_file, "w", encoding="utf-8") as sf:
                json.dump({"start_time": scan_session_start, "range": [start_date_str, end_date_str]}, sf)
        except Exception:
            pass

    start_execution = time.time()
    resume = True
    server_params = StdioServerParameters(command="node", args=[MCP_SERVER_PATH], env={"NODE_TLS_REJECT_UNAUTHORIZED": "0"})

    while True:
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    if "static_details" not in market_data:
                        market_data["static_details"] = {}

                    import hashlib
                    def get_hash(obj):
                        return hashlib.md5(json.dumps(obj, sort_keys=True).encode()).hexdigest()

                    for apt_id in competitors:
                        print(f"[MCP] Checking for updates to static details for: {apt_id}")
                        try:
                            static_res = await session.call_tool("airbnb_listing_details", arguments={"id": apt_id, "ignoreRobotsText": True})
                            static_content = json.loads(static_res.content[0].text)
                            new_details = static_content.get("details", [])

                            old_hash = get_hash(market_data["static_details"].get(apt_id, []))
                            new_hash = get_hash(new_details)

                            if old_hash != new_hash:
                                print(f"[MCP] Static details changed for {apt_id}. Updating.")
                                market_data["static_details"][apt_id] = new_details
                            else:
                                print(f"[MCP] Static details for {apt_id} have not changed.")
                        except Exception as e:
                            print(f"Errore recupero dettagli statici MCP: {e}")

                    for date_str in dates:
                        if date_str not in market_data:
                            market_data[date_str] = {}

                        for apt_id in competitors:
                            c_at = market_data[date_str].get(apt_id, {}).get("collected_at", "")
                            if resume and c_at >= scan_session_start:
                                print(f"[MCP] [{date_str}] Appartamento: {apt_id} (Gia completato in questa sessione, salto!)", flush=True)
                                continue

                            old_history = []
                            if apt_id in market_data[date_str]:
                                old_entry = market_data[date_str][apt_id]
                                old_history = old_entry.pop("history", [])
                                if "collected_at" in old_entry:
                                    old_history.append(old_entry)

                            print(f"[MCP] [{date_str}] Appartamento: {apt_id}", flush=True)
                            found = False
                            current_date = datetime.strptime(date_str, "%Y-%m-%d")

                            for n in range(1, 8):
                                checkout_date = current_date + timedelta(days=n)
                                checkout_str = checkout_date.strftime("%Y-%m-%d")

                                try:
                                    result = await session.call_tool("airbnb_listing_price", arguments={"id": apt_id, "checkin": date_str, "checkout": checkout_str})
                                    content = json.loads(result.content[0].text)

                                    if content.get("available"):
                                        # the bookIt structure is fully returned now!
                                        bookIt = content.get("fullBookItData", {})
                                        if bookIt:
                                            if not found:
                                                market_data[date_str][apt_id] = {
                                                    "status": "OK",
                                                    "minStay": n,
                                                    "checkout": checkout_str,
                                                    "rawResponse": bookIt,
                                                    "collected_at": datetime.now().isoformat(),
                                                    "additional_nights": [],
                                                    "history": old_history
                                                }
                                                print(f"--> Trovato! Soggiorno minimo: {n} notti. Cerco le 2 notti successive.")
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
                                    consecutive_errors += 1
                                    if consecutive_errors >= 5:
                                        print("[PAUSA SICUREZZA] 5 errori consecutivi rilevati! Raffreddamento IP per 120 secondi e riconnessione MCP...")
                                        await asyncio.sleep(120)
                                        consecutive_errors = 0
                                        raise RuntimeError("Troppi errori consecutivi MCP, forzo riconnessione...")
                                else:
                                    consecutive_errors = 0

                                await asyncio.sleep(random.uniform(1.5, 4.0))

                            if not found:
                                market_data[date_str][apt_id] = {
                                    "status": "Non disponibile",
                                    "collected_at": datetime.now().isoformat(),
                                    "history": old_history
                                }
                                print("--> Occupato / Minimum Stay superiore a 7 notti.")

                            tmp_file = OUT_FILE + ".tmp"
                            with open(tmp_file, "w", encoding="utf-8") as f:
                                json.dump(market_data, f, indent=2)
                            os.replace(tmp_file, OUT_FILE)

                            await asyncio.sleep(random.uniform(10.0, 20.0))
                    break
        except Exception as e:
            print(f"Server MCP error: {e}. Riconnessione automatica in 5 secondi...")
            await asyncio.sleep(5)

    # Process data to calculate pure nightly rate
    process_mcp_data(market_data, cleaning_fees)

    elapsed_seconds = round(time.time() - start_execution, 2)
    return {
        "status": "success",
        "message": f"MCP Scan and processing completed for {start_date_str} to {end_date_str}. Raw data saved to {os.path.basename(OUT_FILE)} and pure data saved to {os.path.basename(CLEANED_OUT_FILE)}.",
        "time_taken_seconds": elapsed_seconds
    }

def process_mcp_data(raw_data, cleaning_fees):
    processed = {}
    for date, apts in raw_data.items():
        if date == "static_details":
            continue
        processed[date] = {}
        for apt, entry in apts.items():
            if not entry or entry.get('status') != 'OK' or not entry.get('rawResponse'):
                processed_entry = {'status': 'Non disponibile'}
                if 'collected_at' in entry:
                    processed_entry['collected_at'] = entry['collected_at']
                processed[date][apt] = processed_entry
                continue

            total_gross = 0.0
            taxes = 0.0
            has_special_offer = False

            book_it = entry.get('rawResponse') or {}
            structured_price = book_it.get("structuredDisplayPrice") or {}
            explanation_data = structured_price.get("explanationData") or {}
            price_details = explanation_data.get("priceDetails") or []

            if not price_details:
                pass

            for group in price_details:
                for item in group.get('items', []):
                    if item.get('__typename') == 'DiscountedExplanationLineItem':
                        has_special_offer = True

                    desc = item.get('description', '')
                    if desc in ('Taxes', 'Tasse'):
                        taxes = parse_price(item.get('priceString', ''))

                    if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                        total_gross = parse_price(item.get('priceString', ''))

            cleaning_fee_net = cleaning_fees.get(apt, 50)
            cleaning_fee_gross = cleaning_fee_net * 1.18
            min_stay = entry.get('minStay', 1)
            if not isinstance(min_stay, int) or min_stay <= 0:
                min_stay = 1

            if total_gross > 0:
                calendar_rate_total = total_gross - taxes - cleaning_fee_gross
                pure_total = calendar_rate_total * 0.8109
                pure_nightly = pure_total / min_stay
                rate_val = round(pure_nightly)
            else:
                rate_val = None

            processed_entry = {
                'status': 'OK',
                'rate': rate_val,
                'minStay': min_stay,
                'specialOffer': has_special_offer
            }
            if 'collected_at' in entry:
                processed_entry['collected_at'] = entry['collected_at']

            processed[date][apt] = processed_entry

    with open(CLEANED_OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)

import threading


def run_in_new_loop(coro):
    result = None
    exception = None

    def runner():
        nonlocal result, exception
        try:
            result = asyncio.run(coro)
        except Exception as e:
            exception = e

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()

    if exception:
        raise exception
    return result

def run_mcp_scan_and_process(start_date_str: str, end_date_str: str, resume: bool = False) -> dict:
    return run_in_new_loop(scan_via_mcp_async(start_date_str, end_date_str, resume=resume))

async def scan_via_mcp_custom_dates_async(dates_list: list):
    competitors, cleaning_fees = load_competitors_config()
    if not competitors:
        return {"status": "error", "message": "competitors.txt not found or invalid format"}

    market_data = {}
    consecutive_errors = 0
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, encoding="utf-8") as f:
                market_data = json.load(f)
        except json.JSONDecodeError:
            pass

    start_execution = time.time()
    resume = True
    server_params = StdioServerParameters(command="node", args=[MCP_SERVER_PATH], env={"NODE_TLS_REJECT_UNAUTHORIZED": "0"})

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                if "static_details" not in market_data:
                    market_data["static_details"] = {}

                import hashlib
                def get_hash(obj):
                    return hashlib.md5(json.dumps(obj, sort_keys=True).encode()).hexdigest()

                for apt_id in competitors:
                    print(f"[MCP] Checking for updates to static details for: {apt_id}")
                    try:
                        static_res = await session.call_tool("airbnb_listing_details", arguments={"id": apt_id, "ignoreRobotsText": True})
                        static_content = json.loads(static_res.content[0].text)
                        new_details = static_content.get("details", [])

                        old_hash = get_hash(market_data["static_details"].get(apt_id, []))
                        new_hash = get_hash(new_details)

                        if old_hash != new_hash:
                            print(f"--> Static details changed for {apt_id}! Saving history snapshot.")
                            old_entry = market_data["static_details"].get(apt_id)
                            if old_entry:
                                if "history" not in old_entry:
                                    old_entry["history"] = []
                                old_entry["history"].append({"details": old_entry.get("details", []), "updated_at": old_entry.get("updated_at")})
                                new_details_with_history = {"details": new_details, "updated_at": datetime.now().isoformat(), "history": old_entry["history"]}
                            else:
                                new_details_with_history = {"details": new_details, "updated_at": datetime.now().isoformat(), "history": []}
                            market_data["static_details"][apt_id] = new_details_with_history
                        else:
                            print(f"--> Static details unchanged for {apt_id}.")
                    except Exception as e:
                        print(f"Errore static details per {apt_id}: {e}")

                with open(OUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(market_data, f, indent=2)

                for date_str in dates_list:
                    print(f"\n=== Inizio scansione per la data: {date_str} ===")
                    if date_str not in market_data:
                        market_data[date_str] = {}

                    for apt_id in competitors:
                        c_at = market_data[date_str].get(apt_id, {}).get("collected_at", "")
                        if resume and c_at >= scan_session_start:
                            print(f"[MCP] [{date_str}] Appartamento: {apt_id} (Gia completato in questa sessione, salto!)", flush=True)
                            continue

                        old_history = []
                        if apt_id in market_data[date_str]:
                            old_entry = market_data[date_str][apt_id]
                            old_history = old_entry.pop("history", [])
                            if "collected_at" in old_entry:
                                old_history.append(old_entry)

                        print(f"[MCP] [{date_str}] Appartamento: {apt_id}", flush=True)
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
                                                "additional_nights": [],
                                                "history": old_history
                                            }
                                            print(f"--> Trovato! Soggiorno minimo: {n} notti.")
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
                                consecutive_errors += 1
                                if consecutive_errors >= 5:
                                    print("[PAUSA SICUREZZA] 5 errori consecutivi rilevati! Raffreddamento IP per 120 secondi...")
                                    await asyncio.sleep(120)
                                    consecutive_errors = 0
                            else:
                                consecutive_errors = 0

                            await asyncio.sleep(random.uniform(1.5, 4.0))

                        if not found:
                            market_data[date_str][apt_id] = {
                                "status": "Non disponibile",
                                "collected_at": datetime.now().isoformat(),
                                "history": old_history
                            }
                            print("--> Occupato / Minimum Stay superiore a 7 notti.")

                        with open(OUT_FILE, "w", encoding="utf-8") as f:
                            json.dump(market_data, f, indent=2)

                        await asyncio.sleep(random.uniform(10.0, 20.0))

        processed = {}
        for date, apts in market_data.items():
            if date == "static_details":
                continue
            processed[date] = {}
            for apt, entry in apts.items():
                if entry.get("status") != "OK":
                    processed[date][apt] = {"status": "Non disponibile", "rate": None, "minStay": None}
                    continue

                total_gross = 0.0
                taxes = 0.0
                has_special_offer = False

                book_it = entry.get('rawResponse') or {}
                structured_price = book_it.get("structuredDisplayPrice") or {}
                explanation_data = structured_price.get("explanationData") or {}
                price_details = explanation_data.get("priceDetails") or []

                for group in price_details:
                    for item in group.get('items', []):
                        if item.get('__typename') == 'DiscountedExplanationLineItem':
                            has_special_offer = True

                        desc = item.get('description', '')
                        if desc in ('Taxes', 'Tasse'):
                            taxes = parse_price(item.get('priceString', ''))

                        if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                            total_gross = parse_price(item.get('priceString', ''))

                cleaning_fee_net = cleaning_fees.get(apt, 50)
                cleaning_fee_gross = cleaning_fee_net * 1.18
                min_stay = entry.get('minStay', 1)
                if not isinstance(min_stay, int) or min_stay <= 0:
                    min_stay = 1

                if total_gross > 0:
                    calendar_rate_total = total_gross - taxes - cleaning_fee_gross
                    pure_total = calendar_rate_total * 0.8109
                    pure_nightly = pure_total / min_stay
                    rate_val = round(pure_nightly)
                else:
                    rate_val = None

                processed_entry = {
                    'status': 'OK',
                    'rate': rate_val,
                    'minStay': min_stay,
                    'specialOffer': has_special_offer
                }
                if 'collected_at' in entry:
                    processed_entry['collected_at'] = entry['collected_at']

                processed[date][apt] = processed_entry

        with open(CLEANED_OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(processed, f, indent=2)

        return {"status": "success", "message": "Custom dates scan completed"}
    except Exception as e:
        print(f"Errore critico MCP: {e}")
        return {"status": "error", "message": str(e)}

def run_mcp_custom_dates(dates_list: list) -> dict:
    return run_in_new_loop(scan_via_mcp_custom_dates_async(dates_list))
