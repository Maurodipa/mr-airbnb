import json
import os
import re
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'banca_dati_airbnb_MCPserver.json'
COMPETITORS_PATH = 'competitors.txt'
USER_APT = '1589943047991118285'
ARTIFACT_PATH = r'C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\raccomandazioni_prezzi_totali_nov26_feb27.md'

print("Caricamento database...")
with open(DB_PATH, 'r', encoding='utf-8') as f:
    db = json.load(f)

print("Caricamento competitors e pulizie...")
competitors = []
cleaning_fees = {}
if os.path.exists(COMPETITORS_PATH):
    with open(COMPETITORS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if '===' in line: break
            parts = line.strip().split(':')
            if parts and parts[0].strip().isdigit():
                apt_id = parts[0].strip()
                if apt_id != USER_APT:
                    competitors.append(apt_id)
                if len(parts) >= 2:
                    try:
                        cleaning_fees[apt_id] = float(parts[1].strip())
                    except ValueError:
                        pass

print(f"Competitor caricati: {len(competitors)}")

def parse_price(price_string):
    if not price_string:
        return 0.0
    match = re.search(r'[\d.,]+', str(price_string))
    if match:
        num_str = match.group(0)
        if '.' in num_str and ',' in num_str:
            num_str = num_str.replace('.', '').replace(',', '.')
        elif ',' in num_str and len(num_str.split(',')[-1]) <= 2:
            num_str = num_str.replace(',', '.')
        else:
            num_str = num_str.replace(',', '')
        try:
            return float(num_str)
        except ValueError:
            return 0.0
    return 0.0

def extract_nightly_rate(entry, apt_id, fees_dict, default_cleaning=50.0):
    if isinstance(entry, list) and entry:
        entry = entry[-1]
    if not isinstance(entry, dict):
        return None, None
    if entry.get("status") != "OK":
        return None, None

    if "rate" in entry and isinstance(entry["rate"], (int, float)) and entry["rate"] > 0:
        return float(entry["rate"]), float(entry["rate"]) / 0.81089

    raw = entry.get("rawResponse")
    if not raw or not isinstance(raw, dict):
        return None, None

    structured_price = raw.get("structuredDisplayPrice") or {}
    explanation_data = structured_price.get("explanationData") or {}
    price_details = explanation_data.get("priceDetails") or []

    taxes = 0.0
    total_gross = 0.0
    for group in price_details:
        for item in group.get("items", []):
            desc = item.get("description", "")
            price_str = item.get("priceString", "")
            if desc in ("Taxes", "Tasse"):
                taxes = parse_price(price_str)
            if (item.get("__typename") == "HighlightExplanationLineItem" and desc in ("Total", "Totale")) or desc in ("Total", "Totale"):
                total_gross = parse_price(price_str)

    min_stay = entry.get("minStay", 1)
    if min_stay <= 0:
        min_stay = 1

    cleaning_fee_net = fees_dict.get(apt_id, default_cleaning)
    cleaning_fee_gross = cleaning_fee_net * 1.18

    if total_gross > 0:
        calendar_total = total_gross - taxes - cleaning_fee_gross
        pure_total = calendar_total * 0.81089
        pure_nightly = pure_total / min_stay
        site_rate = (total_gross - taxes) / min_stay
        if pure_nightly > 0:
            return pure_nightly, site_rate

    return None, None

def calculate_percentile(sorted_list, p):
    if not sorted_list:
        return 0.0
    idx = int(round(p * (len(sorted_list) - 1)))
    idx = max(0, min(idx, len(sorted_list) - 1))
    return sorted_list[idx]

# Intervallo completo da fine ottobre 2026 a fine febbraio 2027
start_date = '2026-10-30'
end_date = '2027-02-28'

all_dates = sorted([k for k in db.keys() if k != 'static_details' and len(k) == 10 and start_date <= k <= end_date])
print(f"Date da analizzare: {len(all_dates)} ({all_dates[0]} -> {all_dates[-1]})")

results_by_month = {}
weekday_it = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]

for d in all_dates:
    month_key = d[:7]
    if month_key not in results_by_month:
        results_by_month[month_key] = []

    apts = db[d]
    if not isinstance(apts, dict):
        continue

    rates = []
    site_rates = []
    
    # Dati appartamento utente
    user_entry = apts.get(USER_APT)
    user_curr_rate, user_site_rate = None, None
    user_min_stay = 1
    user_is_booked = True
    
    if user_entry:
        if isinstance(user_entry, list) and user_entry:
            user_entry = user_entry[-1]
        if isinstance(user_entry, dict) and user_entry.get("status") == "OK":
            user_curr_rate, user_site_rate = extract_nightly_rate(user_entry, USER_APT, cleaning_fees, 50.0)
            user_min_stay = user_entry.get("minStay", 1) or 1
            if user_curr_rate and user_curr_rate > 0:
                user_is_booked = False

    avail = 0
    occ = 0
    for apt_id in competitors:
        entry = apts.get(apt_id)
        if entry:
            rate, s_rate = extract_nightly_rate(entry, apt_id, cleaning_fees, 50.0)
            if rate is not None and rate > 0:
                rates.append(rate)
                if s_rate:
                    site_rates.append(s_rate)
                avail += 1
            else:
                occ += 1
        else:
            occ += 1

    total_comps = avail + occ
    occ_rate = (occ / total_comps * 100.0) if total_comps > 0 else 0.0

    dt = datetime.strptime(d, "%Y-%m-%d")
    giorno_str = weekday_it[dt.weekday()]
    is_weekend = dt.weekday() in (4, 5) # Ven o Sab
    if is_weekend:
        giorno_str = f"**{giorno_str}**"

    if not rates:
        results_by_month[month_key].append({
            "date": d,
            "giorno": giorno_str,
            "dt": dt,
            "is_weekend": is_weekend,
            "occ": occ_rate,
            "avail": avail,
            "total": total_comps,
            "median_cal": None,
            "median_site": None,
            "user_curr_cal": None,
            "user_site": None,
            "target_cal": None,
            "target_net": None,
            "user_is_booked": user_is_booked,
            "action": "Dati non disp."
        })
        continue

    rates.sort()
    site_rates.sort()
    median_cal = calculate_percentile(rates, 0.5) / 0.81089
    median_site = calculate_percentile(site_rates, 0.5) if site_rates else 0.0

    # Raccomandazione tariffa calendario host: Mediana sito - (59 € pulizie)
    target_cal = round(median_site - 59.0) if median_site > 59.0 else round(median_cal)
    # Ricalcolo strategico per Febbraio 2027: riduzione del 5%
    if month_key == '2027-02':
        target_cal = round(target_cal * 0.95)
    target_net = round(target_cal * 0.81089)

    user_curr_cal = round(user_curr_rate / 0.81089) if user_curr_rate else None
    user_site_str = f"{round(user_site_rate)} €" if user_site_rate else "-"

    if user_is_booked:
        action = "🔒 Già Prenotato"
    elif user_curr_cal is not None:
        diff = target_cal - user_curr_cal
        if abs(diff) <= 3:
            action = "✅ Allineato"
        elif diff > 3:
            action = f"🔺 Aumenta (+{diff} €)"
        else:
            action = f"🔻 Riduci ({diff} €)"
    else:
        action = f"🎯 Imposta {target_cal} €"

    results_by_month[month_key].append({
        "date": d,
        "giorno": giorno_str,
        "dt": dt,
        "is_weekend": is_weekend,
        "occ": occ_rate,
        "avail": avail,
        "total": total_comps,
        "median_cal": round(median_cal),
        "median_site": round(median_site),
        "user_curr_cal": user_curr_cal,
        "user_site": user_site_str,
        "target_cal": target_cal,
        "target_net": target_net,
        "user_is_booked": user_is_booked,
        "action": action
    })

# Generazione Documento Markdown
doc = []
doc.append("# 📊 Raccomandazioni Strategiche Prezzi Airbnb: Novembre 2026 – Febbraio 2027\n")
doc.append("- **Database analizzato:** `banca_dati_airbnb_MCPserver.json` (Cluster 36 competitor diretti entro 500m)")
doc.append(f"- **ID Alloggio Host:** `{USER_APT}`")
doc.append("- **Formula a Calendario:** $\\text{Tariffa Airbnb (Mediana)} - 59\\ \\text{€}$ (con pulizie host a 50 € e 1 notte minima; **per Febbraio 2027 applicata riduzione strategica del 5%**)")
doc.append("- **Netto Host Stimato:** $\\text{Tariffa Calendario} \\times 0{,}81089$\n")
doc.append("---\n")

month_names = {
    '2026-10': 'Fine Ottobre 2026 (Ponte di Ognissanti)',
    '2026-11': 'Novembre 2026 (1 – 30 Novembre)',
    '2026-12': 'Dicembre 2026 (1 – 31 Dicembre)',
    '2027-01': 'Gennaio 2027 (1 – 31 Gennaio)',
    '2027-02': 'Febbraio 2027 (1 – 28 Febbraio) [Ricalcolato -5%]'
}

for m_key in sorted(results_by_month.keys()):
    m_data = results_by_month[m_key]
    if not m_data:
        continue

    m_title = month_names.get(m_key, m_key)
    doc.append(f"## 📅 {m_title}\n")

    # Calcolo statistiche mese
    valid_days = [r for r in m_data if r['target_cal'] is not None]
    if valid_days:
        avg_occ = sum(r['occ'] for r in valid_days) / len(valid_days)
        weekend_days = [r for r in valid_days if r['is_weekend']]
        weekday_days = [r for r in valid_days if not r['is_weekend']]
        
        avg_cal_we = sum(r['target_cal'] for r in weekend_days) / len(weekend_days) if weekend_days else 0
        avg_cal_wd = sum(r['target_cal'] for r in weekday_days) / len(weekday_days) if weekday_days else 0
        booked_count = sum(1 for r in m_data if r['user_is_booked'])
        
        doc.append(f"**Panoramica del mese:**")
        doc.append(f"- **Occupazione media del cluster:** {avg_occ:.1f}%")
        doc.append(f"- **Tariffa raccomandata feriali (media):** {avg_cal_wd:.0f} € a calendario ({avg_cal_wd * 0.81089:.0f} € netto)")
        doc.append(f"- **Tariffa raccomandata weekend (media):** {avg_cal_we:.0f} € a calendario ({avg_cal_we * 0.81089:.0f} € netto)")
        doc.append(f"- **Notti già vendute / bloccate per il tuo alloggio:** {booked_count} su {len(m_data)} notti\n")

    doc.append("| Data | Giorno | Occupazione Cluster | Mediana Competitor Calendario | Mediana Competitor Airbnb | Tua Tariffa Attuale Calendario | Tua Tariffa Attuale Airbnb | **Tariffa Raccomandata Calendario** | Netto Stimato Host | Azione Consigliata |")
    doc.append("|---|---|---|---|---|---|---|---|---|---|")

    for r in m_data:
        d = r['date']
        giorno = r['giorno']
        occ_str = f"{r['occ']:.1f}% ({r['avail']}/{r['total']} liberi)"
        
        if r['target_cal'] is None:
            doc.append(f"| {d} | {giorno} | {occ_str} | - | - | - | - | **-** | - | {r['action']} |")
            continue

        med_cal_str = f"{r['median_cal']} €"
        med_site_str = f"{r['median_site']} €"
        
        if r['user_is_booked']:
            user_cal_str = "🔒 Prenotato"
            user_site_str = "-"
        else:
            user_cal_str = f"{r['user_curr_cal']} €" if r['user_curr_cal'] else "-"
            user_site_str = r['user_site']

        target_cal_str = f"**{r['target_cal']} €**"
        target_net_str = f"{r['target_net']} €"
        action_str = r['action']

        doc.append(f"| {d} | {giorno} | {occ_str} | {med_cal_str} | {med_site_str} | {user_cal_str} | {user_site_str} | {target_cal_str} | {target_net_str} | {action_str} |")

    doc.append("\n---\n")

# Scrivi artifact
full_text = "\n".join(doc)
with open(ARTIFACT_PATH, 'w', encoding='utf-8') as f:
    f.write(full_text)

print(f"Artifact generato con successo: {ARTIFACT_PATH}")
print(f"Dimensione file: {len(full_text)} caratteri")
