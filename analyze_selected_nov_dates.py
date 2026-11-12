import json
import re
from datetime import datetime

with open('mr-airbnb/banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

with open('mr-airbnb/pricing_audit_log.json', 'r', encoding='utf-8') as f:
    audit_log = json.load(f)

apt_user = '1589943047991118285'
apt_target = '40027959'

def parse_price(s):
    if not s: return 0.0
    m = re.search(r'[\d\,\.]+', s.replace('.', '').replace(',', '.'))
    return float(m.group()) if m else 0.0

cleaning_fees = {}
try:
    with open('mr-airbnb/competitors.txt', encoding='utf-8') as f:
        reading_fees = False
        for line in f:
            line = line.strip()
            if not line: continue
            if '===CLEANING_FEES===' in line: reading_fees = True; continue
            if reading_fees and '=' in line:
                parts = line.split('=')
                cleaning_fees[parts[0]] = float(parts[1])
except Exception: pass

target_dates = [
    '2026-11-12',
    '2026-11-15',
    '2026-11-16',
    '2026-11-23',
    '2026-11-24',
    '2026-11-25',
    '2026-11-26',
    '2026-11-27',
    '2026-11-28',
    '2026-11-29',
    '2026-11-30'
]

days_it = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]

results = []

for d in target_dates:
    dt = datetime.strptime(d, "%Y-%m-%d")
    wd = days_it[dt.weekday()]
    
    day_data = db.get(d, {})
    total_competitors = 37
    free_listings = []
    
    status_40027959 = "🔒 Occupato"
    price_40027959 = "-"
    
    for apt_id, v in day_data.items():
        if apt_id in ('summary', 'static_details'): continue
        if v.get('status') == 'OK' and v.get('rawResponse'):
            book_it = v['rawResponse']
            price_details = book_it.get('structuredDisplayPrice', {}).get('explanationData', {}).get('priceDetails', [])
            total_gross = 0.0
            taxes = 0.0
            for g in price_details:
                for item in g.get('items', []):
                    desc = item.get('description', '')
                    if desc in ('Taxes', 'Tasse'): taxes = parse_price(item.get('priceString', ''))
                    if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                        total_gross = parse_price(item.get('priceString', ''))
            cf_net = cleaning_fees.get(apt_id, 50.0)
            cf_gross = cf_net * 1.18
            min_stay = v.get('minStay', 1)
            if min_stay <= 0: min_stay = 1
            if total_gross > 0:
                calendar_rate = (total_gross - taxes - cf_gross) / min_stay
                site_rate = (total_gross - taxes) / min_stay
                free_listings.append({
                    'id': apt_id,
                    'cal': round(calendar_rate),
                    'site': round(site_rate),
                    'minStay': min_stay
                })
                if apt_id == apt_target:
                    status_40027959 = f"🟢 Libero (MinStay {min_stay}n)"
                    price_40027959 = f"{round(calendar_rate)} € (Sito {round(site_rate)} €)"
    
    free_count = len(free_listings)
    booked_count = total_competitors - free_count
    occ_pct = round((booked_count / total_competitors) * 100, 1)
    
    site_rates = sorted([x['site'] for x in free_listings if x['id'] != apt_user])
    if site_rates:
        mid = len(site_rates)//2
        median_site = site_rates[mid] if len(site_rates)%2!=0 else round((site_rates[mid-1]+site_rates[mid])/2)
        rec_cal = median_site - 59
    else:
        median_site = 0
        rec_cal = 0
        
    audit_item = audit_log.get(d, {})
    current_cal_user = audit_item.get('new_price', 'N/D')
    user_status = audit_item.get('status', 'N/D')
    
    results.append({
        'date': d,
        'weekday': wd,
        'free': free_count,
        'occ': occ_pct,
        'median_site': median_site,
        'rec_cal': rec_cal,
        'user_cal': current_cal_user,
        'user_status': user_status,
        'status_40027959': status_40027959,
        'price_40027959': price_40027959,
        'top_competitors': sorted(free_listings, key=lambda x: x['cal'])
    })

print(json.dumps(results, indent=2))
