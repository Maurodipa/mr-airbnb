import json

with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

apts = db.get('2026-10-20', {})

with open('C:\\Users\\mauro\\.gemini\\antigravity\\brain\\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\\datalake_grezzo_20_ottobre.md', 'w', encoding='utf-8') as f:
    f.write("# Datalake Grezzo - 20 Ottobre 2026\n\n")
    f.write("`json\n")
    f.write(json.dumps(apts, indent=2, ensure_ascii=False))
    f.write("\n`")

print('Raw Artifact created.')
