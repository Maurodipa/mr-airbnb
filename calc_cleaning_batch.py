import base64
import json
import requests
import urllib3
import time
import random
from datetime import datetime, timedelta

urllib3.disable_warnings()

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
    try:
        res = requests.post(url, json=payload, headers=headers, verify=False, timeout=10)
        data = res.json()
        book_it = data.get("data", {}).get("node", {}).get("pdpPresentation", {}).get("bookIt", {})
        if book_it.get("availability", {}).get("isAvailable") is False:
            return None
        price_details = book_it.get("structuredDisplayPrice", {}).get("explanationData", {}).get("priceDetails")
        if not price_details: return None

        total_gross = 0.0
        taxes = 0.0
        for group in price_details:
            if 'items' in group:
                for item in group['items']:
                    desc = item.get('description', '')
                    if desc in ('Taxes', 'Tasse'):
                        taxes = float(item['priceString'].replace('€', '').replace(',', '').strip())
                    if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                        total_gross = float(item['priceString'].replace('€', '').replace(',', '').strip())
        return total_gross - taxes
    except Exception as e:
        return None

def calc_cleaning_fee(apt_id, date_str):
    start_date = datetime.strptime(date_str, "%Y-%m-%d")
    for min_stay in range(1, 8):
        checkout1 = (start_date + timedelta(days=min_stay)).strftime("%Y-%m-%d")
        checkout2 = (start_date + timedelta(days=min_stay+1)).strftime("%Y-%m-%d")
        
        t1 = fetch_price(apt_id, date_str, checkout1)
        if t1 is not None:
            time.sleep(random.uniform(0.5, 1.0)) # Anti-ban
            t2 = fetch_price(apt_id, date_str, checkout2)
            if t2 is not None:
                R = (t2 - t1) / 1.1637
                C = (t1 / 1.1637) - (min_stay * R)
                return max(0, round(C))
            break # Se min_stay è libero ma min_stay+1 è occupato, non possiamo calcolare.
        time.sleep(random.uniform(0.5, 1.0))
    return None

def main():
    with open('competitors.txt', 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    
    dates_to_test = ["2026-08-01", "2026-08-02", "2026-08-03", "2026-08-04"]
    new_lines = []
    
    print("Inizio estrazione spese di pulizia per 50 appartamenti...")
    
    for line in lines:
        if not line.strip(): continue
        parts = line.split(':')
        apt_id = parts[0]
        current_fee = parts[1]
        name = parts[2] if len(parts) > 2 else "Gemello"
        
        found_fee = None
        for date_str in dates_to_test:
            fee = calc_cleaning_fee(apt_id, date_str)
            if fee is not None:
                found_fee = fee
                break
        
        if found_fee is not None:
            print(f"{apt_id} -> Trovata: {found_fee} EUR (prima era {current_fee})")
            new_lines.append(f"{apt_id}:{int(found_fee)}:{name}")
        else:
            print(f"{apt_id} -> Nessun dato utile per estrarre la pulizia nei 4 giorni. Mantengo: {current_fee} EUR")
            new_lines.append(line)
            
    with open('competitors.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines) + '\n')
    print("File competitors.txt aggiornato con successo!")

if __name__ == "__main__":
    main()
