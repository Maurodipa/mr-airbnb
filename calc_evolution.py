import json
import re

FEE_MULTIPLIER = 1.1637
cleaning_fee = 70.0
with open('competitors.txt') as f:
    for line in f:
        if '1303527950935439382' in line:
            cleaning_fee = float(line.split(':')[1])

db = json.load(open('banca_dati_airbnb_MCPserver_recovered.json', encoding='utf-8'))
d = db.get('2026-10-28', {}).get('1303527950935439382', {})

def get_net(raw_resp, min_stay):
    s = json.dumps(raw_resp)
    total_gross = 0
    taxes = 0
    
    matches = re.findall(r'\"description\"\s*:\s*\"(Totale|Total)\".*?\"priceString\"\s*:\s*\"([\\d\\.,\\s]+)', s)
    if matches:
        val = matches[-1][1].replace('.', '').replace(',', '.').strip()
        total_gross = float(re.search(r'[\d\.]+', val).group())
        
    tax_matches = re.findall(r'\"description\"\s*:\s*\"(Tasse|Taxes)\".*?\"priceString\"\s*:\s*\"([\\d\\.,\\s]+)', s)
    if tax_matches:
        val = tax_matches[-1][1].replace('.', '').replace(',', '.').strip()
        taxes = float(re.search(r'[\d\.]+', val).group())
    
    if total_gross > 0:
        net = (total_gross - taxes) / FEE_MULTIPLIER
        return (net - cleaning_fee) / min_stay
    return 0

print(f'Cleaning fee: {cleaning_fee}')
current_net = get_net(d['rawResponse'], d['minStay'])
print(f'Current (Sept 4): {current_net:.2f} EUR -> Calendar: {((current_net+50)/0.81089)-59:.2f}')

if 'history' in d and len(d['history']) > 0:
    hist = d['history'][0]
    hist_net = get_net(hist['rawResponse'], hist['minStay'])
    print(f'History ({hist.get("collected_at", "Unknown")}): {hist_net:.2f} EUR -> Calendar: {((hist_net+50)/0.81089)-59:.2f}')
