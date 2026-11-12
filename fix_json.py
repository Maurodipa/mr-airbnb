import json

path = 'mr-airbnb/banca_dati_airbnb_MCPserver.json'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

print("Length:", len(text))
pos = text.rfind('collected_at')
print("pos collected_at:", pos)
if pos != -1:
    # Look backward for "\n  {"
    rec_start = text.rfind('\n  {', 0, pos)
    print("rec_start:", rec_start)
    if rec_start != -1:
        clean = text[:rec_start].rstrip().rstrip(',') + '\n]'
        with open(path, 'w', encoding='utf-8') as out:
            out.write(clean)
        data = json.loads(clean)
        print(f"SUCCESS! Total valid records: {len(data)}")
        p3 = [r for r in data if r.get('collected_at', '') >= '2026-09-28T15:15:00']
        print(f"Phase 3 records: {len(p3)}")
