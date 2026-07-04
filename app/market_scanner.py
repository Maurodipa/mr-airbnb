import base64
import json
import os
import random
import time
from datetime import datetime, timedelta
import requests

COMPETITORS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "competitors.txt")
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "banca_dati_airbnb.json")
OUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "market_data_1month.json")

CLEANING_FEES = {
  '1589943047991118285': 50, # Mauro
  '602489771443051475': 50,  # Stefania
  '1280484040857767756': 0,   # Ugo
  '1243259212458138393': 50,  # Navona
  '2153298': 50,              # Elegante
  '1105673287932582735': 50,  # Perla
  '14159837': 120,            # Barbara
  '14290915': 73,             # Blue Navona
  '4050526': 60               # Junior Suite
}
FEE_MULTIPLIER = 1.1637

def fetch_price(listing_id: str, check_in: str, check_out: str):
    url = "https://www.airbnb.com/api/v3/StaysPdpBookItQuery"
    b64_id = base64.b64encode(f"DemandStayListing:{listing_id}".encode()).decode()
    
    payload = {
        "operationName": "StaysPdpBookItQuery",
        "variables": {
            "id": b64_id,
            "dateRange": {"startDate": check_in, "endDate": check_out},
            "guestCounts": {"numberOfAdults": 2},
            "includePdpMigrationBookItCalendarSheetFragment": True,
            "includePdpMigrationBookItFloatingFooterFragment": True,
            "includePdpMigrationBookItNavFragment": True,
            "includePdpMigrationBookItSidebarFragment": True,
            "includePdpMigrationCancellationPolicyPickerModalFragment": True,
            "includeOverviewMerchandisingTipsFragment": True
        },
        "extensions": {"persistedQuery": {"version": 1, "sha256Hash": "9dfddf66545e678cb5cb06e0ce5a327e5cbd13309254d94d11500c91d9fbcd40"}}
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Airbnb-API-Key': 'd306zoyjsyarp7ifhu67rjxn52tv0t20',
        'X-Airbnb-Currency': 'EUR',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    res = requests.post(url, json=payload, headers=headers)
    if res.status_code == 429:
        raise Exception("429")
        
    data = res.json()
    book_it = data.get("data", {}).get("node", {}).get("pdpPresentation", {}).get("bookIt", {})
    
    if book_it.get("availability", {}).get("isAvailable") is False:
        return {"available": False, "raw": None}
        
    price_details = book_it.get("structuredDisplayPrice", {}).get("explanationData", {}).get("priceDetails")
    if not price_details:
        return {"available": False, "raw": None}
        
    return {"available": True, "raw": price_details}

def parse_price(price_string):
    import re
    match = re.search(r'[\d.,]+', price_string)
    if match:
        return float(match.group(0).replace(',', ''))
    return 0.0

def process_data(raw_data):
    processed = {}
    for date, apts in raw_data.items():
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
            
            for group in entry.get('rawResponse', []):
                for item in group.get('items', []):
                    if item.get('__typename') == 'DiscountedExplanationLineItem':
                        has_special_offer = True
                        
                    desc = item.get('description', '')
                    if desc in ('Taxes', 'Tasse'):
                        taxes = parse_price(item.get('priceString', ''))
                        
                    if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                        total_gross = parse_price(item.get('priceString', ''))
                        
            cleaning_fee = CLEANING_FEES.get(apt, 50)
            min_stay = entry.get('minStay', 1)
            
            total_net_with_cleaning = (total_gross - taxes) / FEE_MULTIPLIER
            pure_total = total_net_with_cleaning - cleaning_fee
            pure_nightly = pure_total / min_stay
            
            processed_entry = {
                'status': 'OK',
                'rate': round(pure_nightly),
                'minStay': min_stay,
                'specialOffer': has_special_offer
            }
            if 'collected_at' in entry:
                processed_entry['collected_at'] = entry['collected_at']
                
            processed[date][apt] = processed_entry
            
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)

def run_scan_and_process(start_date_str: str, end_date_str: str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
        
    if not os.path.exists(COMPETITORS_FILE):
        return {"status": "error", "message": "competitors.txt not found"}
        
    with open(COMPETITORS_FILE, "r") as f:
        competitors = [line.strip() for line in f if line.strip()]
        
    market_data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                market_data = json.load(f)
        except json.JSONDecodeError:
            pass
            
    start_execution = time.time()
    
    try:
        for date_str in dates:
            if date_str not in market_data:
                market_data[date_str] = {}
                
            for apt_id in competitors:
                # Incremental update: skip if already present and OK
                if apt_id in market_data[date_str] and market_data[date_str][apt_id].get("status") == "OK":
                    continue
                    
                print(f"[{date_str}] Appartamento: {apt_id}")
                found = False
                current_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                for n in range(1, 8):
                    checkout_date = current_date + timedelta(days=n)
                    checkout_str = checkout_date.strftime("%Y-%m-%d")
                    
                    try:
                        result = fetch_price(apt_id, date_str, checkout_str)
                        if result["available"]:
                            market_data[date_str][apt_id] = {
                                "status": "OK",
                                "minStay": n,
                                "checkout": checkout_str,
                                "rawResponse": result["raw"],
                                "collected_at": datetime.now().isoformat()
                            }
                            print(f"--> Trovato! Soggiorno minimo: {n} notti.")
                            found = True
                            break
                    except Exception as e:
                        if str(e) == "429":
                            print("!!! ERRORE 429 !!! IP Bloccato. Interrompo e salvo.")
                            with open(DATA_FILE, "w", encoding="utf-8") as f:
                                json.dump(market_data, f, indent=2)
                            raise Exception("API rate limit exceeded (429)")
                            
                    time.sleep(random.uniform(0.2, 0.5))
                    
                if not found:
                    market_data[date_str][apt_id] = {
                        "status": "Non disponibile",
                        "collected_at": datetime.now().isoformat()
                    }
                    print("--> Occupato / Minimum Stay superiore a 7 notti.")
                    
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(market_data, f, indent=2)
                    
                time.sleep(random.uniform(1.0, 2.0))
                
    except Exception as e:
        if str(e) != "API rate limit exceeded (429)":
            raise e
            
    # After raw scan, process all data
    process_data(market_data)
    
    elapsed_seconds = round(time.time() - start_execution, 2)
    return {
        "status": "success",
        "message": f"Scan and processing completed for {start_date_str} to {end_date_str}. Pure data saved.",
        "time_taken_seconds": elapsed_seconds
    }
