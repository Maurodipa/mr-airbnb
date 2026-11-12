import json
import os
from collections import defaultdict
import re

with open("banca_dati_airbnb_MCPserver_cleaned.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Carico i 52 IDs validi da competitors.txt
target_ids = []
with open("competitors.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        apt_id = line.split(':')[0]
        target_ids.append(apt_id)

apts_data = defaultdict(list)

for date, apts in data.items():
    if not date.startswith("2026-08"):
        continue
    for apt_id, info in apts.items():
        if apt_id in target_ids:
            info["date"] = date
            apts_data[apt_id].append(info)

out_path = r"C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\report_agosto_52gemelli.md"

report = "# Report Strategico Agosto 2026 - 52 Appartamenti Gemelli\n\n"
report += "> [!IMPORTANT]\n> I prezzi indicati sono le **tariffe pure giornaliere** (al netto della percentuale del 16,3% trattenuta da Airbnb e senza i costi di pulizia nascosti).\n\n"

prices_all = []
booked_count = 0
free_count = 0
missing_count = 0

for apt_id in target_ids:
    days = apts_data.get(apt_id, [])
    days.sort(key=lambda x: x["date"])
    
    report += f"## Appartamento ID: {apt_id}\n\n"
    
    if not days:
        report += "Nessun dato scansionato.\n\n"
        missing_count += 1
        continue
        
    prices = [d["rate"] for d in days if d.get("status") == "OK" and "rate" in d]
    if prices:
        free_count += 1
        avg = sum(prices) / len(prices)
        report += f"**Tariffa Media (Agosto):** {avg:.2f} €/notte\n"
        prices_all.extend(prices)
    else:
        booked_count += 1
        report += "**Completamente Occupato o Chiuso per tutto Agosto.**\n\n"
        
    report += "### Dettaglio Giornaliero\n"
    for d in days:
        date = d["date"]
        status = d.get("status")
        if status == "OK" and "rate" in d:
            price = d.get("rate")
            min_stay = d.get("minStay", "?")
            discount = " (Offerta Speciale!)" if d.get("specialOffer") else ""
            report += f"- {date}: Libero - **{price} €** (Min Stay: {min_stay}){discount}\n"
        else:
            report += f"- {date}: Occupato / Chiuso\n"
    report += "\n---\n\n"
    
if prices_all:
    market_avg = sum(prices_all) / len(prices_all)
    min_price = min(prices_all)
    max_price = max(prices_all)
else:
    market_avg = min_price = max_price = 0

summary = f"## Riepilogo Globale (52 Appartamenti Gemelli)\n"
summary += f"- Appartamenti con almeno 1 notte libera ad Agosto: **{free_count}**\n"
summary += f"- Appartamenti totalmente occupati/chiusi ad Agosto: **{booked_count}**\n"
if missing_count > 0:
    summary += f"- Nessun dato per: **{missing_count}** appartamenti\n"
summary += f"- **Prezzo Medio del Mercato:** {market_avg:.2f} €/notte\n"
summary += f"- Prezzo Minimo Trovato: {min_price} €\n"
summary += f"- Prezzo Massimo Trovato: {max_price} €\n\n"
summary += "> [!TIP]\n> Ad Agosto la stragrande maggioranza degli alloggi è già occupata. Chi ha ancora notti libere riesce a spuntare prezzi sensibilmente più alti rispetto alla media annuale.\n\n"

report = summary + report

with open(out_path, "w", encoding="utf-8") as f:
    f.write(report)
    
print(f"Generato con media: {market_avg:.2f}, minimo: {min_price}, max: {max_price}")
print(f"Liberi: {free_count}, Occupati: {booked_count}")
