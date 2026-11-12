import json

with open("C:/Docs/Personnel et confidentiel/Corsi e Formazioni/2026-06-14 Kaggle_5-Day AI Agents/agy2-projects/my-first-project/.agents/skills/market-scanner/banca_dati_airbnb.json", encoding="utf-8") as f:
    data = json.load(f)

apt = "5791838"

def get_gross_total(date):
    if date in data and apt in data[date]:
        raw = data[date][apt].get("rawResponse", [])
        for group in raw:
            if "items" in group:
                for item in group["items"]:
                    if item.get("description") == "Total" or item.get("description") == "Totale":
                        s = item.get("priceString").replace(",", "")
                        import re
                        m = re.search(r'[\d\.]+', s)
                        if m:
                            return float(m.group(0))
    return None

price_1_night = get_gross_total("2026-11-10") # 1 night
price_2_nights = get_gross_total("2026-11-11") # Wait, the data for 2026-11-11 in the db is ALSO 1 night checkout!
# scan_raw.js checks exactly 1 night if minStay is 1. It only checks multiple nights if minStay > 1.
print(f"Price 1 night: {price_1_night}")
