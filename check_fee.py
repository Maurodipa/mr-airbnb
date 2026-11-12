import json

with open("C:/Docs/Personnel et confidentiel/Corsi e Formazioni/2026-06-14 Kaggle_5-Day AI Agents/agy2-projects/my-first-project/.agents/skills/market-scanner/banca_dati_airbnb.json", encoding="utf-8") as f:
    data = json.load(f)

apt = "5791838"
date = "2026-11-10"

if date in data and apt in data[date]:
    raw = data[date][apt].get("rawResponse", [])
    for group in raw:
        if "items" in group:
            for item in group["items"]:
                print(f"{item.get('description')}: {item.get('priceString')}")
else:
    print("Non trovato")
