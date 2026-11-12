import json

with open('banca_dati_airbnb_MCPserver.json', encoding='utf-8') as f:
    db = json.load(f)

for d in db:
    if d == 'static_details': continue
    if '1401938376529553958' in db[d] and db[d]['1401938376529553958'].get('status') == 'OK':
        entry = db[d]['1401938376529553958']
        if entry.get('additional_nights'):
            print(f'Data base: {d}, minStay: {entry.get("minStay")}')
            print('N notti raw:', str(entry.get('rawResponse'))[:500])
            print('N+1 notti raw:', str(entry.get('additional_nights')[0])[:500])
