import json
import re

with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

date_keys = [k for k in db.keys() if re.match(r'^\d{4}-\d{2}-\d{2}$', k)]
last_date = max(date_keys)
print('Ultima data a calendario:', last_date)

collected_at = None
for apt_id, data in db[last_date].items():
    if isinstance(data, list) and len(data) > 0:
        collected_at = data[-1].get('collected_at')
        if collected_at: break
    elif isinstance(data, dict):
        collected_at = data.get('collected_at')
        if collected_at: break

print('Data in cui e stata registrata:', collected_at)
