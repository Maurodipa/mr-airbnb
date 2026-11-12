import json
import os
from collections import defaultdict
from app.mcp_market_scanner import process_mcp_data
from app.market_scanner import load_competitors_config

# 1. Carichiamo i dati raw aggiornati
raw_file = "banca_dati_airbnb_MCPserver.json"
try:
    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
except Exception as e:
    print(f"Errore caricamento dati: {e}")
    exit(1)

# 2. Riprocessiamo i dati per calcolare le tariffe pure
_, fees = load_competitors_config()
# Questo sovrascrive banca_dati_airbnb_MCPserver_cleaned.json con i dati attuali
process_mcp_data(raw_data, fees)

# 3. Leggiamo i dati puliti
clean_file = "banca_dati_airbnb_MCPserver_cleaned.json"
with open(clean_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Carico i 50 IDs validi da competitors.txt
target_ids = []
with open("competitors.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        apt_id = line.split(':')[0]
        target_ids.append(apt_id)

apts_data = defaultdict(list)
allowed_dates = ["2026-08-01", "2026-08-02", "2026-08-03", "2026-08-04"]

for date, apts in data.items():
    if date not in allowed_dates:
        continue
    for apt_id, info in apts.items():
        if apt_id in target_ids:
            info["date"] = date
            apts_data[apt_id].append(info)

out_path = r"C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\report_agosto_1_4_50gemelli.md"

report = "# Report Strategico (1-4 Agosto 2026) - 50 Appartamenti Gemelli\n\n"
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
        report += "Nessun dato scansionato per queste date.\n\n"
        missing_count += 1
        continue
        
    prices = [d["rate"] for d in days if d.get("status") == "OK" and "rate" in d]
    if prices:
        free_count += 1
        avg = sum(prices) / len(prices)
        report += f"**Tariffa Media (1-4 Agosto):** {avg:.2f} €/notte\n"
        prices_all.extend(prices)
    else:
        booked_count += 1
        report += "**Completamente Occupato o Chiuso.**\n\n"
        
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

summary = f"## Riepilogo Globale (50 Appartamenti Gemelli)\n"
summary += f"- Appartamenti con almeno 1 notte libera (1-4 Ago): **{free_count}**\n"
summary += f"- Appartamenti totalmente occupati/chiusi (1-4 Ago): **{booked_count}**\n"
if missing_count > 0:
    summary += f"- Nessun dato per: **{missing_count}** appartamenti\n"
summary += f"- **Prezzo Medio del Mercato:** {market_avg:.2f} €/notte\n"
summary += f"- Prezzo Minimo Trovato: {min_price} €\n"
summary += f"- Prezzo Massimo Trovato: {max_price} €\n\n"

report = summary + report

with open(out_path, "w", encoding="utf-8") as f:
    f.write(report)
    
print(f"Report generato! Media: {market_avg:.2f} €, Minimo: {min_price} €, Massimo: {max_price} €")
print(f"Liberi: {free_count}, Occupati: {booked_count}, Mancanti: {missing_count}")
