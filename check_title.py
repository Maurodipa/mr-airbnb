import json
import re

with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

val = d.get('2026-11-02', {}).get('1589943047991118285')
if val:
    s = json.dumps(val)
    print(re.findall(r'"title"\s*:\s*"([^"]+)"', s, re.IGNORECASE))
