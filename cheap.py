import json

with open('banca_dati_airbnb_MCPserver_cleaned.json', encoding='utf-8') as f:
    d = json.load(f)

with open('competitors.txt') as f:
    ids = [l.split(':')[0] for l in f if l.strip()]

dates = ['2026-08-01', '2026-08-02', '2026-08-03', '2026-08-04']
prices = []

for date in dates:
    if date in d:
        for apt in ids:
            if apt in d[date]:
                if d[date][apt].get('status') == 'OK' and 'rate' in d[date][apt]:
                    prices.append({
                        'id': apt,
                        'date': date,
                        'rate': d[date][apt]['rate']
                    })

prices.sort(key=lambda x: x['rate'])
print("I 5 prezzi più bassi:")
for p in prices[:5]:
    print(f"{p['rate']} € - ID: {p['id']} - Data: {p['date']}")
