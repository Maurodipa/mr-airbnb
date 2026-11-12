import json
import re

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
    return {'cal': round(cal), 'site': round(site), 'minStay': min_stay}

months = ['2026-11', '2026-12', '2027-01', '2027-02']
summary = {}

for m in months:
    total_days = 0
    available_days = 0
    booked_days = 0
    prices = []
    
    for d, listings in sorted(db.items()):
        if not d.startswith(m): continue
        total_days += 1
        if apt_id in listings:
            p = extract_prices(listings[apt_id])
            if p:
                available_days += 1
                prices.append((d, p['cal'], p['site'], p['minStay']))
            else:
                booked_days += 1
        else:
            booked_days += 1
            
    summary[m] = {
        'total': total_days,
        'available': available_days,
        'booked': booked_days,
        'occupancy': round((booked_days / total_days * 100), 1) if total_days else 0,
        'prices': prices
    }

for m, s in summary.items():
    print(f"=== MESE {m} ===")
    print(f"Giorni totali: {s['total']}, Liberi: {s['available']}, Occupati: {s['booked']}, Occupazione: {s['occupancy']}%")
    cal_list = [p[1] for p in s['prices']]
    if cal_list:
        print(f"Prezzi calendario: Min {min(cal_list)} €, Max {max(cal_list)} €, Media {round(sum(cal_list)/len(cal_list))} €")
        print("Esempi date libere e prezzi:")
        for item in s['prices'][:10]:
            print(f"  {item[0]}: Cal {item[1]} € (Sito {item[2]} €, MinStay {item[3]} notti)")
    else:
        print("Nessun giorno libero (100% occupato o non aperto)")
    print("")
