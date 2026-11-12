import json

with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

apts = db.get('2026-10-20', {})

output = ["# Dati Datalake per il 20 Ottobre 2026\n"]
output.append(f"Totale appartamenti monitorati: {len(apts)}\n")

for apt_id, data in apts.items():
    if isinstance(data, list):
        entry = data[-1] if data else {}
    else:
        entry = data
        
    status = entry.get('status', 'Sconosciuto')
    collected = entry.get('collected_at', 'Sconosciuta')
    
    if status == 'Non disponibile':
        output.append(f"- **ID {apt_id}**: Occupato / Non disponibile (Rilevato il: {collected[:10]})")
    else:
        min_stay = entry.get('minStay', '?')
        checkout = entry.get('checkout', '?')
        
        # Try to extract total price from structuredDisplayPrice
        total_price = "N/D"
        raw = entry.get('rawResponse', {})
        try:
            primary = raw.get('structuredDisplayPrice', {}).get('primaryLine', {})
            total_price = primary.get('accessibilityLabel', 'N/D')
        except:
            pass
            
        output.append(f"- **ID {apt_id}**: ?? DISPONIBILE (Rilevato il: {collected[:10]})")
        output.append(f"  - Soggiorno minimo richiesto: {min_stay} notti (Checkout: {checkout})")
        output.append(f"  - Dettaglio prezzi Airbnb: {total_price}")

with open('C:\\Users\\mauro\\.gemini\\antigravity\\brain\\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\\dati_20_ottobre.md', 'w', encoding='utf-8') as f:
    f.write("\n".join(output))

print('Artifact created.')
