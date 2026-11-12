import base64
import json
import requests
from datetime import datetime, timedelta

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
    import urllib3
    urllib3.disable_warnings()
    res = requests.post(url, json=payload, headers=headers, verify=False)
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

def calc_cleaning_fee(apt_id, date_str):
    start_date = datetime.strptime(date_str, "%Y-%m-%d")
    for min_stay in range(1, 8):
        checkout1 = (start_date + timedelta(days=min_stay)).strftime("%Y-%m-%d")
        checkout2 = (start_date + timedelta(days=min_stay+1)).strftime("%Y-%m-%d")
        
        t1 = fetch_price(apt_id, date_str, checkout1)
        if t1 is not None:
            t2 = fetch_price(apt_id, date_str, checkout2)
            if t2 is not None:
                R = (t2 - t1) / 1.1637
                C = (t1 / 1.1637) - (min_stay * R)
                return C
    return None

c1 = calc_cleaning_fee("812115552598995560", "2026-08-01")
print(f"Costo pulizie VERO per 812115552598995560: {c1} EUR")

c2 = calc_cleaning_fee("54301473", "2026-08-02")
print(f"Costo pulizie VERO per 54301473: {c2} EUR")
