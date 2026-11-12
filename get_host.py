import json
import re

with open('banca_dati_airbnb_MCPserver.json', encoding='utf-8') as f:
    db = json.load(f)

for i in ['1401938376529553958', '5791838']:
    s = json.dumps(db.get('static_details', {}).get(i, {}))
    
    titles = re.findall(r'"title"\s*:\s*"([^"]+)"', s)
    title = titles[0] if titles else "Unknown"
    
    print(f'ID {i} Title: {title}')
