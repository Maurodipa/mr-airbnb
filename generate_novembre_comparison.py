import json
import sys
import os

sys.path.append('app')
from market_scanner import parse_price, FEE_MULTIPLIER

db_rec = json.load(open('banca_dati_airbnb_MCPserver_recovered.json', encoding='utf-8'))
db_mcp = json.load(open('banca_dati_airbnb_MCPserver.json', encoding='utf-8'))

db = {}
db.update(db_rec)
db.update(db_mcp)

my_free_nov = [d for d, apts in db.items() if d != 'static_details' and d.startswith('2026-11-') and d <= '2026-11-22' and apts.get('1589943047991118285', {}).get('status') == 'OK']
my_free_nov.sort()

fees = {}
with open('competitors.txt', encoding='utf-8') as f:
    for line in f:
        parts = line.strip().split(':')
        if len(parts) >= 3:
            fees[parts[0]] = float(parts[1])

lines = [
    '# Confronto Medio vs Mediano: 1-22 Novembre 2026\n',
    'Questa tabella mostra per ciascuna delle tue date libere dal 1 al 22 Novembre il numero di concorrenti liberi, il guadagno netto medio e mediano della zona, e le relative tariffe da inserire a calendario.\n',
    '| Data | Concorrenti Liberi | Guadagno Netto Mediano | **Calendario Mediano** | Guadagno Netto Medio | **Calendario Medio** |',
    '|---|---|---|---|---|---|'
]

def to_calendar(net):
    return ((net + 50) / 0.81089) - 59

for d in my_free_nov:
    apts = db.get(d, {})
    processed = {}
    for apt, entry in apts.items():
        if not entry or entry.get('status') != 'OK' or not entry.get('rawResponse'):
            continue
        
        total_gross = 0.0
        taxes = 0.0
        book_it = entry.get('rawResponse') or {}
        structured_price = book_it.get('structuredDisplayPrice') or {}
        explanation_data = structured_price.get('explanationData') or {}
        price_details = explanation_data.get('priceDetails') or []
        for group in price_details:
            for item in group.get('items', []):
                desc = item.get('description', '')
                if desc in ('Taxes', 'Tasse'):
                    taxes = parse_price(item.get('priceString', ''))
                if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc in ('Total', 'Totale'):
                    total_gross = parse_price(item.get('priceString', ''))
        
        cleaning_fee = fees.get(apt, 50.0)
        min_stay = entry.get('minStay', 1)
        
        if total_gross > 0:
            total_net = (total_gross - taxes) / FEE_MULTIPLIER
            pure_total = total_net - cleaning_fee
            pure_nightly = pure_total / min_stay
            processed[apt] = round(pure_nightly)

    avail = [(apt, net) for apt, net in processed.items() if apt != '1589943047991118285']
    avail = [x for x in avail if x[1] > 0]
    if not avail:
        continue
        
    num_avail = len(avail)
    rates = sorted([r for _, r in avail])
    
    avg_net = sum(rates) / num_avail
    
    n_rates = len(rates)
    if n_rates % 2 == 1:
        median_net = rates[n_rates // 2]
    else:
        median_net = (rates[n_rates // 2 - 1] + rates[n_rates // 2]) / 2.0

    cal_avg = to_calendar(avg_net)
    cal_median = to_calendar(median_net)

    lines.append(f'| **{d}** | {num_avail} | {median_net:.0f} € | **{cal_median:.0f} €** | {avg_net:.0f} € | **{cal_avg:.0f} €** |')

out_path = r'C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\confronto_medio_mediano_novembre.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
