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
            p = l.strip().split(':')
            fees[p[0]] = int(p[1])

dates = [f'2026-08-{str(i).zfill(2)}' for i in range(1, 19)]
prezzi = []
occupati = 0
liberi = 0
prices_details = []

for date in dates:
    if date in clean_db:
        for apt, data in clean_db[date].items():
            if apt not in fees: continue
            if data.get('status') == 'OK' and 'rate' in data:
                prezzi.append(data['rate'])
                liberi += 1
                
                raw_entry = raw_db[date][apt]
                book_it = raw_entry.get('rawResponse', {})
                min_stay = data.get('minStay', 1)
                
                total_gross = 0.0
                price_details = book_it.get('structuredDisplayPrice', {}).get('explanationData', {}).get('priceDetails', [])
                for group in price_details:
                    for item in group.get('items', []):
                        desc = item.get('description', '')
                        if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                            total_gross = parse_price(item['priceString'])
                
                raw_nightly = total_gross / min_stay
                prices_details.append({
                    'id': apt,
                    'date': date,
                    'pure_rate': data['rate'],
                    'raw_rate': raw_nightly,
                    'cleaning_fee': fees[apt],
                    'min_stay': min_stay
                })
            else:
                occupati += 1

media = sum(prezzi) / len(prezzi)
print(f'Media: {media:.2f}')
print(f'Minimo: {min(prezzi)}')
print(f'Massimo: {max(prezzi)}')
print(f'Liberi: {liberi}')
print(f'Occupati: {occupati}')
print(f'Occupazione: {(occupati / (liberi + occupati) * 100):.1f}%')

prices_details.sort(key=lambda x: x['pure_rate'])
seen = set()
top_5 = []
for p in prices_details:
    if p['id'] not in seen:
        seen.add(p['id'])
        top_5.append(p)
    if len(top_5) == 5:
        break

print('\nTOP 5:')
for i, p in enumerate(top_5, 1):
    print(f"{i}. ID: {p['id']} - Pura: {p['pure_rate']} - Grezza: {p['raw_rate']:.2f} (su {p['min_stay']} notti) - Pulizia: {p['cleaning_fee']} - Link: https://www.airbnb.it/rooms/{p['id']}")
