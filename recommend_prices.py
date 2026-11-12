import json
import statistics

with open('banca_dati_airbnb_MCPserver_cleaned.json', encoding='utf-8') as f:
    db = json.load(f)

# Generiamo le raccomandazioni
results = []
for d, apts in db.items():
    if d == 'static_details' or d < '2026-09-06' or d > '2026-11-30':
        continue
    rates = []
    occ = 0
    avail = 0
    for apt, data in apts.items():
        if apt == '1589943047991118285': continue # Escludi l'utente
        if data.get('status') == 'OK' and 'rate' in data:
            rates.append(data['rate'])
            avail += 1
        else:
            occ += 1
    
    total = avail + occ
    occ_rate = occ / total if total > 0 else 0
    if not rates:
        continue
        
    rates.sort()
    avg = sum(rates) / len(rates)
    
    # Simple recommendation logic
    if occ_rate > 0.90:
        target = rates[int(len(rates) * 0.8)] # 80th percentile (High)
    elif occ_rate > 0.75:
        target = rates[int(len(rates) * 0.6)] # 60th percentile
    elif occ_rate > 0.50:
        target = rates[int(len(rates) * 0.4)] # 40th percentile
    else:
        target = rates[0] # Lowest if very empty
        
    # Calcolo prezzo calendario utente (netto -> base)
    # Net = (Base + 59) * 0.81089 - 50 -> Base = ((Net + 50) / 0.81089) - 59
    cal_price = ((target + 50) / 0.81089) - 59
    
    results.append({
        'date': d, 
        'occ': occ_rate * 100, 
        'avg': avg, 
        'target_net': target,
        'target_cal': cal_price
    })

results.sort(key=lambda x: x['date'])

with open('raccomandazioni_autunno.md', 'w', encoding='utf-8') as f:
    f.write("# Strategia Prezzi: Autunno 2026 (Fino al 30 Novembre)\n\n")
    f.write("Ecco i prezzi esatti da impostare nel calendario di Airbnb per i tuoi giorni vuoti. La colonna **Prezzo Calendario** include già i calcoli per compensare il 18,9% di commissioni e le tue pulizie.\n\n")
    f.write("| Data | Occupazione Zona | Tariffa Media | **Tuo Guadagno Netto** | **DA INSERIRE A CALENDARIO** |\n")
    f.write("|---|---|---|---|---|\n")
    
    for r in results:
        # Bold weekends
        dt = r['date']
        is_weekend = False # Simplified for now
        f.write(f"| {dt} | {r['occ']:.1f}% | {r['avg']:.0f} € | **{r['target_net']:.0f} €** | **{r['target_cal']:.0f} €** |\n")
