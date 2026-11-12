import json
from app.market_scanner import parse_price

with open('banca_dati_airbnb_MCPserver.json', encoding='utf-8') as f:
    raw_db = json.load(f)

with open('banca_dati_airbnb_MCPserver_cleaned.json', encoding='utf-8') as f:
    clean_db = json.load(f)

fees = {}
with open('competitors.txt', encoding='utf-8') as f:
    for l in f:
        if ':' in l:
            parts = l.strip().split(':')
            fees[parts[0]] = int(parts[1])

dates = ['2026-08-01', '2026-08-02', '2026-08-03', '2026-08-04']
prices = []

for date in dates:
    if date in clean_db:
        for apt in fees.keys():
            if apt in clean_db[date]:
                clean_entry = clean_db[date][apt]
                if clean_entry.get('status') == 'OK' and 'rate' in clean_entry:
                    raw_entry = raw_db[date][apt]
                    book_it = raw_entry.get("rawResponse", {})
                    min_stay = clean_entry.get("minStay", 1)
                    
                    # Extract Total Gross
                    total_gross = 0.0
                    price_details = book_it.get("structuredDisplayPrice", {}).get("explanationData", {}).get("priceDetails", [])
                    for group in price_details:
                        for item in group.get('items', []):
                            desc = item.get('description', '')
                            if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                                total_gross = parse_price(item['priceString'])
                    
                    raw_nightly = total_gross / min_stay
                    
                    prices.append({
                        'id': apt,
                        'date': date,
                        'pure_rate': clean_entry['rate'],
                        'raw_rate': raw_nightly,
                        'cleaning_fee': fees[apt],
                        'min_stay': min_stay
                    })

# Sort by pure_rate
prices.sort(key=lambda x: x['pure_rate'])

# Get top 5 unique apartments
seen = set()
top_5 = []
for p in prices:
    if p['id'] not in seen:
        seen.add(p['id'])
        top_5.append(p)
    if len(top_5) == 5:
        break

print("=== I 5 APPARTAMENTI PIÙ ECONOMICI (per Tariffa Pura) ===")
for i, p in enumerate(top_5, 1):
    link = f"https://www.airbnb.it/rooms/{p['id']}"
    print(f"{i}. ID: {p['id']} (Disp: {p['date']})")
    print(f"   - Tariffa Pura (host): {p['pure_rate']} €/notte")
    print(f"   - Tariffa Grezza Totale (ospite): {p['raw_rate']:.2f} €/notte (su {p['min_stay']} notti)")
    print(f"   - Spese di Pulizia: {p['cleaning_fee']} €")
    print(f"   - Link: {link}")
    print()
