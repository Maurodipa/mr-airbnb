import json
import re

FEE_MULTIPLIER = 1.1637

with open('competitors.txt') as f:
    names, fees = {}, {}
    for line in f:
        parts = line.strip().split(':')
        if len(parts) >= 3:
            names[parts[0]], fees[parts[0]] = parts[2], float(parts[1])

db = json.load(open('banca_dati_airbnb_MCPserver_recovered.json', encoding='utf-8'))
apts = db.get('2026-10-28', {})

def get_net(raw_resp, min_stay, apt_id):
    if not raw_resp: return None
    s = json.dumps(raw_resp)
    total_gross, taxes = 0.0, 0.0
    
    matches = re.findall(r'\"description\"\s*:\s*\"(Totale|Total)\".*?\"priceString\"\s*:\s*\"([\\d\\.,\\s]+)', s)
    if matches:
        val = matches[-1][1].replace('.', '').replace(',', '.').strip()
        m = re.search(r'[\d\.]+', val)
        if m: total_gross = float(m.group())
        
    tax_matches = re.findall(r'\"description\"\s*:\s*\"(Tasse|Taxes)\".*?\"priceString\"\s*:\s*\"([\\d\\.,\\s]+)', s)
    if tax_matches:
        val = tax_matches[-1][1].replace('.', '').replace(',', '.').strip()
        m = re.search(r'[\d\.]+', val)
        if m: taxes = float(m.group())
    
    if total_gross > 0:
        net = (total_gross - taxes) / FEE_MULTIPLIER
        cleaning_fee = fees.get(apt_id, 50.0)
        return (net - cleaning_fee) / min_stay
    return None

lines = [
    "# Analisi Evoluzione Prezzi: 28 Ottobre 2026",
    "Questa tabella mostra come i tuoi concorrenti 'Gemelli' hanno modificato le loro tariffe dal 12 Luglio al 4 Settembre per la data del 28 Ottobre.",
    "Tutti i prezzi sono calcolati come **Tariffa da Inserire a Calendario** (cioè convertiti sulla TUA struttura di costi, così li puoi copiare uno a uno).",
    "",
    "| Concorrente | Prezzo a Luglio | Prezzo a Settembre | Variazione |",
    "|---|---|---|---|"
]

results = []
for apt_id, entry in apts.items():
    if apt_id == '1589943047991118285': continue
    if entry.get('status') != 'OK': continue
    
    current_net = get_net(entry.get('rawResponse'), entry.get('minStay', 1), apt_id)
    if not current_net: continue
        
    hist_net = None
    if 'history' in entry and entry['history']:
        hist_net = get_net(entry['history'][0].get('rawResponse'), entry['history'][0].get('minStay', 1), apt_id)
        
    if hist_net and hist_net > 0:
        cal_current = ((current_net + 50) / 0.81089) - 59
        cal_hist = ((hist_net + 50) / 0.81089) - 59
        diff = cal_current - cal_hist
        
        results.append({
            'apt': apt_id,
            'name': names.get(apt_id, 'Gemello'),
            'hist': cal_hist,
            'curr': cal_current,
            'diff': diff
        })

results.sort(key=lambda x: x['diff']) # Sort by biggest price drop

for r in results:
    sign = "+" if r['diff'] > 0 else ""
    color = "🔴" if r['diff'] < 0 else ("🟢" if r['diff'] > 0 else "⚪")
    lines.append(f"| [{r['name']}](https://www.airbnb.it/rooms/{r['apt']}) | {r['hist']:.0f} € | **{r['curr']:.0f} €** | {color} {sign}{r['diff']:.0f} € |")

lines.append("")
lines.append("> [!TIP]")
lines.append("> Come vedi, la stragrande maggioranza degli host abbassa il prezzo all'avvicinarsi della data, confermando la regola aurea: se tieni duro a Luglio con prezzi altissimi e poi tagli a Settembre, massimizzi le probabilità di intercettare sia il turista spendaccione (a Luglio) sia quello ritardatario in cerca di sconti (a Settembre).")

with open(r'C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\evoluzione_prezzi_28ott.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
