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

titles_map = {}
with open('titles.txt', encoding='utf-8') as f:
    for line in f:
        parts = line.strip().split(' -- ')
        if len(parts) >= 2:
            apt_id = parts[0].strip()
            raw_desc = parts[1].strip()
            desc_parts = raw_desc.split(' · ')
            type_str = desc_parts[0].replace(' in Rome', '') if len(desc_parts) > 0 else 'Gemello'
            rating_str = desc_parts[1] if len(desc_parts) > 1 else ''
            unique_name = f"Gemello #{apt_id[-4:]} ({type_str} {rating_str})".strip()
            titles_map[apt_id] = unique_name

lines = [
    '# Sommario Raccomandazioni Prezzi: 1-22 Novembre 2026\n',
    'Questo sommario mostra le date in cui il tuo appartamento è libero nel periodo 1-22 Novembre, il prezzo consigliato da inserire a calendario, il livello di concorrenza rimasto e 3 esempi di concorrenti con tariffe molto simili.\n',
    '| Data | **Tariffa da Inserire a Calendario** | Concorrenti Liberi | 3 Concorrenti con Tariffe Simili |',
    '|---|---|---|---|'
]

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
    occ_rate = (50 - num_avail) / 50
    if occ_rate > 0.90: target = rates[int(len(rates) * 0.8)]
    elif occ_rate > 0.75: target = rates[int(len(rates) * 0.6)]
    elif occ_rate > 0.50: target = rates[int(len(rates) * 0.4)]
    else: target = rates[0]
        
    cal_price = ((target + 50) / 0.81089) - 59

    comp_list = []
    for apt, net in avail:
        comp_cal = ((net + 50) / 0.81089) - 59
        diff = abs(comp_cal - cal_price)
        name = titles_map.get(apt, f"Gemello #{apt[-4:]}")
        comp_list.append((diff, name, apt, comp_cal))

    comp_list.sort(key=lambda x: x[0])
    top_3 = comp_list[:3]
    
    similar_str_list = [f"[{name}](https://www.airbnb.it/rooms/{apt}) ({comp_cal:.0f} €)" for _, name, apt, comp_cal in top_3]
    similar_str = "<br>".join(similar_str_list)

    lines.append(f'| **{d}** | **{cal_price:.0f} €** | {num_avail} (Occ: {occ_rate*100:.0f}%) | {similar_str} |')

out_path = r'C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\sommario_raccomandazioni_novembre.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
