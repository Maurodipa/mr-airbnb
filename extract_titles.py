import json
import re

db = json.load(open('banca_dati_airbnb_MCPserver_recovered.json', encoding='utf-8'))

titles_map = {}

# Check static_details
static_details = db.get('static_details', {})
for apt, info in static_details.items():
    if isinstance(info, dict):
        title = info.get('name') or info.get('title') or info.get('p3SummaryTitle')
        if title:
            titles_map[apt] = title
    elif isinstance(info, list):
        for item in info:
            if isinstance(item, dict):
                title = item.get('name') or item.get('title') or item.get('p3SummaryTitle')
                if title:
                    titles_map[apt] = title

print("From static_details:", len(titles_map))

# Check legacy database banca_dati_airbnb.json as well if needed
try:
    db_legacy = json.load(open('banca_dati_airbnb.json', encoding='utf-8'))
    for apt, info in db_legacy.get('static_details', {}).items():
        if apt not in titles_map and isinstance(info, dict):
            t = info.get('name') or info.get('title')
            if t: titles_map[apt] = t
except Exception as e:
    print("Legacy db error:", e)

# Also check rawResponse in db
for date, apts in db.items():
    if date == 'static_details': continue
    for apt, data in apts.items():
        if apt in titles_map: continue
        raw = data.get('rawResponse') or {}
        s = json.dumps(raw)
        m = re.search(r'\"(title|name|p3SummaryTitle)\"\s*:\s*\"([^\"]+)\"', s)
        if m:
            titles_map[apt] = m.group(2)

print("Total titles found:", len(titles_map))
for k, v in list(titles_map.items())[:15]:
    print(k, "->", v)
