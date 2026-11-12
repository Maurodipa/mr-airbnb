import base64

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

listing_id = "5791838"
check_in = "2026-11-10"
check_out = "2026-11-12"

b64_id = base64.b64encode(f"DemandStayListing:{listing_id}".encode()).decode()

url = "https://www.airbnb.com/api/v3/StaysPdpBookItQuery"
headers = {
    'Content-Type': 'application/json',
    'X-Airbnb-API-Key': 'd306zoyjsyarp7ifhu67rjxn52tv0t20',
    'X-Airbnb-Currency': 'EUR',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

payload = {
    "operationName": "StaysPdpBookItQuery",
    "variables": {
        "id": b64_id,
        "dateRange": {"startDate": check_in, "endDate": check_out},
        "guestCounts": {"numberOfAdults": 1},
        "includePdpMigrationBookItCalendarSheetFragment": True,
        "includePdpMigrationBookItFloatingFooterFragment": True,
        "includePdpMigrationBookItNavFragment": True,
        "includePdpMigrationBookItSidebarFragment": True,
        "includePdpMigrationCancellationPolicyPickerModalFragment": True,
        "includeOverviewMerchandisingTipsFragment": True
    },
    "extensions": {
        "persistedQuery": {
            "version": 1,
            "sha256Hash": "9dfddf66545e678cb5cb06e0ce5a327e5cbd13309254d94d11500c91d9fbcd40"
        }
    }
}

res = requests.post(url, headers=headers, json=payload, verify=False)
data = res.json()

book_it = data.get("data", {}).get("node", {}).get("pdpPresentation", {}).get("bookIt", {})
price_details = book_it.get("structuredDisplayPrice", {}).get("explanationData", {}).get("priceDetails", [])

for group in price_details:
    for item in group.get("items", []):
        print(f"{item.get('description')}: {item.get('priceString')}")
