import json
import re
from datetime import datetime

with open('mr-airbnb/banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

apt_id = '40027959'

def parse_price(s):
    if not s: return 0.0
    m = re.search(r'[\d\,\.]+', s.replace('.', '').replace(',', '.'))
    return float(m.group()) if m else 0.0

def extract_prices(v):
    if not v or v.get('status') != 'OK' or not v.get('rawResponse'):
        return None
    book_it = v['rawResponse']
    price_details = book_it.get('structuredDisplayPrice', {}).get('explanationData', {}).get('priceDetails', [])
    total_gross = 0.0
    taxes = 0.0
    for g in price_details:
        for item in g.get('items', []):
            desc = item.get('description', '')
            if desc in ('Taxes', 'Tasse'):
                taxes = parse_price(item.get('priceString', ''))
            if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                total_gross = parse_price(item.get('priceString', ''))
    min_stay = v.get('minStay', 1)
    if min_stay <= 0: min_stay = 1
    cf_gross = 50.0 * 1.18
    cal = (total_gross - taxes - cf_gross) / min_stay if total_gross > 0 else 0
    site = (total_gross - taxes) / min_stay if total_gross > 0 else 0
    return {
        'total': total_gross,
        'cal': round(cal),
        'site': round(site),
        'minStay': min_stay,
        'collected_at': v.get('collected_at')
    }

# Analizziamo tutte le date nel DB
report = {}
all_collected_dates = set()

for d, listings in sorted(db.items()):
    if d in ('static_details', 'summary'): continue
    if apt_id in listings:
        curr = listings[apt_id]
        hist = curr.get('history', [])
        all_snaps = hist + [curr]
        
        snaps_info = []
        for s in all_snaps:
            p = extract_prices(s)
            c_at = s.get('collected_at', '')
            st = s.get('status', 'UNKNOWN')
            if p:
                snaps_info.append({'date_scan': c_at[:10], 'cal': p['cal'], 'site': p['site'], 'minStay': p['minStay'], 'status': 'OK'})
            else:
                snaps_info.append({'date_scan': c_at[:10], 'cal': None, 'site': None, 'minStay': None, 'status': st})
        report[d] = snaps_info

print(f"Totale date tracciate per 40027959: {len(report)}")

# Vediamo date con variazioni di prezzo
price_changes = []
status_changes = []

for d, snaps in report.items():
    cal_prices = [s['cal'] for s in snaps if s['cal'] is not None]
    statuses = [s['status'] for s in snaps]
    if len(set(cal_prices)) > 1:
        price_changes.append((d, snaps))
    if len(set(statuses)) > 1:
        status_changes.append((d, snaps))

print(f"Date con variazione di prezzo nel tempo: {len(price_changes)}")
print(f"Date con variazione di disponibilità (es. da libero a occupato o viceversa): {len(status_changes)}")

# Stampa esempi di variazioni di prezzo
print("\n--- Esempi di variazioni di prezzo per data di soggiorno ---")
for d, snaps in price_changes[:10]:
    evo = " -> ".join([f"{s['date_scan']}: {s['cal']}€" if s['cal'] else f"{s['date_scan']}: {s['status']}" for s in snaps])
    print(f"{d}: {evo}")

# Stampa esempi di cambio status (occupazione)
print("\n--- Esempi di prenotazioni avvenute (cambio status da OK a OCCUPATO) ---")
for d, snaps in status_changes[:10]:
    evo = " -> ".join([f"{s['date_scan']}: {s['cal']}€" if s['cal'] else f"{s['date_scan']}: {s['status']}" for s in snaps])
    print(f"{d}: {evo}")
