import json

with open('banca_dati_airbnb_MCPserver_cleaned.json', encoding='utf-8') as f:
    clean_db = json.load(f)

sept_dates = [f"2026-09-{str(i).zfill(2)}" for i in range(1, 31)]

daily_stats = {}
all_rates = []
total_available = 0
total_occupied = 0

for d in sept_dates:
    if d in clean_db:
        rates = []
        occ = 0
        avail = 0
        for apt, data in clean_db[d].items():
            if data.get('status') == 'OK' and 'rate' in data:
                rates.append(data['rate'])
                all_rates.append(data['rate'])
                avail += 1
            else:
                occ += 1
        
        total_available += avail
        total_occupied += occ
        if rates:
            daily_stats[d] = {
                'avg': sum(rates) / len(rates),
                'min': min(rates),
                'max': max(rates),
                'avail': avail,
                'occ': occ,
                'occ_rate': (occ / (avail + occ)) * 100 if (avail + occ) > 0 else 0
            }

print(f"=== SINTESI SETTEMBRE 2026 ===")
print(f"Media generale Tariffa Pura: {sum(all_rates)/len(all_rates):.2f} €")
print(f"Minimo assoluto: {min(all_rates)} €")
print(f"Massimo assoluto: {max(all_rates)} €")
total_slots = total_available + total_occupied
print(f"Occupazione totale mese: {(total_occupied / total_slots * 100):.1f}% ({total_occupied} occupati su {total_slots} slot)")
print("\n--- DETTAGLIO GIORNALIERO ---")
for d, s in daily_stats.items():
    print(f"{d}: Media {s['avg']:.1f} € | Min {s['min']} € | Max {s['max']} € | Occupazione {s['occ_rate']:.1f}% ({s['occ']}/{s['occ']+s['avail']})")
