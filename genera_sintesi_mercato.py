import json
import os
import re
import sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

DB_FILE = os.path.join(os.path.dirname(__file__), "banca_dati_airbnb_MCPserver.json")
COMP_FILE = os.path.join(os.path.dirname(__file__), "competitors.txt")

def parse_price_str(price_string):
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

def load_cleaning_fees():
    fees = {}
    if os.path.exists(COMP_FILE):
        with open(COMP_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) >= 2:
                    try:
                        fees[parts[0].strip()] = float(parts[1].strip())
                    except ValueError:
                        pass
    return fees

def extract_net_nightly_rate(entry, apt_id, cleaning_fees):
    if isinstance(entry, list) and entry:
        entry = entry[-1]
    if not isinstance(entry, dict):
        return None
    
    # Check if direct rate exists
    if "rate" in entry:
        try:
            return float(entry["rate"])
        except (ValueError, TypeError):
            pass
            
    raw = entry.get("rawResponse")
    if not raw or not isinstance(raw, dict):
        return None
        
    avail = raw.get("availability", {})
    if isinstance(avail, dict) and not avail.get("isAvailable", True):
        return None # Booked/Occupied
        
    spd = raw.get("structuredDisplayPrice", {})
    if not spd or not isinstance(spd, dict):
        return None
        
    primary = spd.get("primaryLine", {})
    if not primary or not isinstance(primary, dict):
        return None
        
    raw_price_str = primary.get("discountedPrice") or primary.get("originalPrice") or primary.get("price")
    if not raw_price_str:
        return None
        
    tot = parse_price_str(raw_price_str)
    if tot <= 0:
        return None
        
    taxes = 0.0
    explanation_data = spd.get("explanationData") or {}
    for group in explanation_data.get("priceDetails", []):
        for item in group.get("items", []):
            desc = item.get("description", "")
            if desc in ("Taxes", "Tasse"):
                taxes = parse_price_str(item.get("priceString", ""))
        
    min_stay = entry.get("minStay", 1)
    try:
        min_stay = int(min_stay)
        if min_stay <= 0:
            min_stay = 1
    except (ValueError, TypeError):
        min_stay = 1
        
    c_fee_net = cleaning_fees.get(str(apt_id), 50.0)
    c_fee_gross = c_fee_net * 1.18
    
    calendar_total = tot - taxes - c_fee_gross
    pure_tot = calendar_total * 0.8109
    
    if pure_tot > 0:
        return pure_tot / min_stay
    return None

def generate_market_summary():
    if not os.path.exists(DB_FILE):
        return "Database non trovato."
        
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    cleaning_fees = load_cleaning_fees()
    
    dates = sorted([k for k in data.keys() if k != "static_details"])
    if not dates:
        return "Nessuna data presente nel database."
        
    all_apts = set()
    for d in dates:
        for apt in data[d].keys():
            all_apts.add(apt)
            
    # Group by month
    monthly_stats = {}
    for d_str in dates:
        month_key = d_str[:7] # YYYY-MM
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                "dates": [],
                "total_slots": 0,
                "available_slots": 0,
                "booked_slots": 0,
                "rates": []
            }
        monthly_stats[month_key]["dates"].append(d_str)
        
        day_dict = data[d_str]
        for apt_id, entry in day_dict.items():
            monthly_stats[month_key]["total_slots"] += 1
            rate = extract_net_nightly_rate(entry, apt_id, cleaning_fees)
            
            # Check availability
            is_avail = False
            if isinstance(entry, list) and entry:
                raw = entry[-1].get("rawResponse", {})
                avail = raw.get("availability", {})
                is_avail = avail.get("isAvailable", False) if isinstance(avail, dict) else False
            elif isinstance(entry, dict):
                raw = entry.get("rawResponse", {})
                avail = raw.get("availability", {})
                is_avail = avail.get("isAvailable", False) if isinstance(avail, dict) else False
                
            if is_avail and rate is not None:
                monthly_stats[month_key]["available_slots"] += 1
                monthly_stats[month_key]["rates"].append(rate)
            else:
                monthly_stats[month_key]["booked_slots"] += 1

    report_lines = []
    report_lines.append("# SINTESI DEI DATI RACCOLTI (DATA LAKE AIRBNB)")
    report_lines.append(f"\n* **Orizzonte temporale rilevato:** `{dates[0]}` ➔ `{dates[-1]}` ({len(dates)} date)")
    report_lines.append(f"* **Appartamenti monitorati nel cluster:** {len(all_apts)}")
    report_lines.append(f"* **Totale slot monitorati (giorni x alloggi):** {sum(s['total_slots'] for s in monthly_stats.values()):,}")
    
    report_lines.append("\n## 1. Analisi Mensile: Occupazione e Tariffe Medie Nette")
    report_lines.append("| Mese | Date Rilevate | Alloggi Monitorati | Tasso Occupazione | Prezzo Min | 25° Perc | Tariffa Calendario Mediana Competitor | 75° Perc | Prezzo Max | Tuo Prezzo Calendario Consigliato |")
    report_lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    
    for m_key, s in sorted(monthly_stats.items()):
        occ_rate = (s["booked_slots"] / s["total_slots"] * 100) if s["total_slots"] > 0 else 0
        rates = s["rates"]
        if rates:
            p_min = np.min(rates)
            p25 = np.percentile(rates, 25)
            p50 = np.percentile(rates, 50)
            p75 = np.percentile(rates, 75)
            p_max = np.max(rates)
            
            tariffa_calendario = (p50 + (59 * 0.1891)) / 0.8109
            
            report_lines.append(f"| **{m_key}** | {len(s['dates'])} gg | {s['total_slots']} | **{occ_rate:.1f}%** | {p_min:.0f} € | {p25:.0f} € | **{p50:.0f} €** | {p75:.0f} € | {p_max:.0f} € | **{tariffa_calendario:.0f} €** |")
        else:
            report_lines.append(f"| **{m_key}** | {len(s['dates'])} gg | {s['total_slots']} | **{occ_rate:.1f}%** | N/D | N/D | N/D | N/D | N/D | N/D |")
            
    report_lines.append("\n## 2. Dettaglio Giorni Speciali e Picchi di Domanda")
    special_dates = ["2026-10-31", "2026-12-24", "2026-12-25", "2026-12-31", "2027-01-01", "2027-01-06"]
    report_lines.append("| Data Speciale | Festività / Evento | Occupazione | Mediana Prezzo Netto | Tariffa Calendario | Alloggi Rimasti Liberi |")
    report_lines.append("| :--- | :--- | :---: | :---: | :---: | :---: |")
    
    for sp_date in special_dates:
        if sp_date in data:
            day_dict = data[sp_date]
            tot_day = len(day_dict)
            free_cnt = 0
            day_rates = []
            for apt_id, entry in day_dict.items():
                r = extract_net_nightly_rate(entry, apt_id, cleaning_fees)
                is_avail = False
                if isinstance(entry, list) and entry:
                    raw = entry[-1].get("rawResponse", {})
                    avail = raw.get("availability", {})
                    is_avail = avail.get("isAvailable", False) if isinstance(avail, dict) else False
                elif isinstance(entry, dict):
                    raw = entry.get("rawResponse", {})
                    avail = raw.get("availability", {})
                    is_avail = avail.get("isAvailable", False) if isinstance(avail, dict) else False
                if is_avail and r is not None:
                    free_cnt += 1
                    day_rates.append(r)
            occ_day = ((tot_day - free_cnt) / tot_day * 100) if tot_day > 0 else 0
            med_p = np.median(day_rates) if day_rates else 0
            
            tariffa_calendario_sp = 0
            if med_p > 0:
                tariffa_calendario_sp = (med_p + (59 * 0.1891)) / 0.8109
                
            label = "Halloween" if "10-31" in sp_date else ("Vigilia Natale" if "12-24" in sp_date else ("Natale" if "12-25" in sp_date else ("Capodanno" if "12-31" in sp_date else ("Capodanno (1 gen)" if "01-01" in sp_date else "Epifania"))))
            report_lines.append(f"| `{sp_date}` | {label} | **{occ_day:.1f}%** | {med_p:.0f} € | **{tariffa_calendario_sp:.0f} €** | {free_cnt} su {tot_day} |")
            
    report_lines.append("\n## 3. Confronto Struttura dei Costi: Tuo Appartamento vs Mercato")
    report_lines.append("Questa tabella confronta la tua configurazione fissa delle pulizie con la media dei competitor nel tuo cluster (51 appartamenti).")
    report_lines.append("| Metrica | Il Tuo Appartamento | Mediana Competitor |")
    report_lines.append("| :--- | :---: | :---: |")
    
    comp_cleanings = list(cleaning_fees.values())
    med_comp_clean_net = np.median(comp_cleanings) if comp_cleanings else 50.0
    med_comp_clean_gross = med_comp_clean_net * 1.18
    
    your_clean_net = 50.0
    your_clean_gross = your_clean_net * 1.18
    
    report_lines.append(f"| **Costi Pulizia (Tariffa mostrata a Calendario)** | {your_clean_gross:.2f} € | {med_comp_clean_gross:.2f} € |")
    report_lines.append(f"| **Costi Pulizia (Rimborso Netto in tasca)** | **{your_clean_net:.2f} €** | **{med_comp_clean_net:.2f} €** |")
    
    summary_text = "\n".join(report_lines).replace("Mediana (50°)", "Guadagno Netto (Mediana)").replace("Mediana Prezzo Netto", "Guadagno Netto (Mediana)")
    return summary_text

if __name__ == "__main__":
    report = generate_market_summary()
    print(report)
    out_path = os.path.join(os.path.dirname(__file__), "sintesi_dati_mercato.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nSintesi salvata con successo in: {out_path}")
