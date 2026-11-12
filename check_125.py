import json

with open('banca_dati_airbnb_MCPserver_cleaned.json', encoding='utf-8') as f:
    clean_db = json.load(f)

dates = ['2026-08-02', '2026-08-03', '2026-08-04']
target_range = (115, 135)
results = {}
all_matching_ids = set()

for date in dates:
    results[date] = []
    if date in clean_db:
        for apt, data in clean_db[date].items():
            # exclude user's apartment from count
            if apt == '1589943047991118285':
                continue
            if data.get('status') == 'OK' and 'rate' in data:
                r = data['rate']
                if target_range[0] <= r <= target_range[1]:
                    results[date].append({'id': apt, 'rate': r})
                    all_matching_ids.add(apt)

for date in dates:
    print(f'=== {date} ===')
    print(f'Trovati {len(results[date])} appartamenti tra 115 e 135 euro:')
    for p in results[date]:
        print(f'  - ID {p["id"]}: {p["rate"]} EUR')

print(f'\nIn totale, ci sono {len(all_matching_ids)} appartamenti DISTINTI che si posizionano in questa fascia (115-135€) in quei tre giorni.')
