import json

with open('banca_dati_airbnb_MCPserver_cleaned_FINAL_BACKUP.json', encoding='utf-8') as f:
    db_july = json.load(f)

with open('banca_dati_airbnb_MCPserver_cleaned.json', encoding='utf-8') as f:
    db_sept = json.load(f)

dates = [f"2026-09-{str(i).zfill(2)}" for i in range(5, 22)]

increased = 0
decreased = 0
same = 0
newly_booked = 0

changes = []

for d in dates:
    if d not in db_july or d not in db_sept:
        continue
    for apt, july_data in db_july[d].items():
        sept_data = db_sept[d].get(apt, {})
        
        july_status = july_data.get('status')
        sept_status = sept_data.get('status')
        
        if july_status == 'OK' and sept_status == 'OK':
            rate_july = july_data.get('rate')
            rate_sept = sept_data.get('rate')
            if rate_july and rate_sept:
                diff = rate_sept - rate_july
                if diff > 0:
                    increased += 1
                elif diff < 0:
                    decreased += 1
                else:
                    same += 1
                
                if abs(diff) > 10:
                    changes.append({'date': d, 'apt': apt, 'old': rate_july, 'new': rate_sept, 'diff': diff})
                    
        elif july_status == 'OK' and sept_status != 'OK':
            newly_booked += 1

print("=== CONFRONTO STRATEGIA PREZZI ===")
print("Snapshot 1: metà Luglio (circa 2 mesi prima)")
print("Snapshot 2: inizio Settembre (pochi giorni prima)")
print(f"Prezzo Aumentato (sotto data): {increased} volte")
print(f"Prezzo Diminuito (sotto data / last minute): {decreased} volte")
print(f"Prezzo Invariato: {same} volte")
print(f"Posti liberi a Luglio che sono stati prenotati nel frattempo: {newly_booked}")

print("\n--- CASI SPECIFICI INTERESSANTI ---")
# Sort by biggest drops
drops = sorted([c for c in changes if c['diff'] < 0], key=lambda x: x['diff'])
print("I più grandi SCONTI last-minute (Host in preda al panico):")
for c in drops[:5]:
    print(f"[{c['date']}] Apt {c['apt']}: {c['old']} € -> {c['new']} € (Scarto: {c['diff']} €)")

# Sort by biggest hikes
hikes = sorted([c for c in changes if c['diff'] > 0], key=lambda x: x['diff'], reverse=True)
print("\nI più grandi AUMENTI last-minute (Host ottimisti/opportunisti):")
for c in hikes[:5]:
    print(f"[{c['date']}] Apt {c['apt']}: {c['old']} € -> {c['new']} € (Scarto: +{c['diff']} €)")
