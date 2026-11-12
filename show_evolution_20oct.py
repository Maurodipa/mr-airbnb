import json

with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

date_target = '2026-10-20'
apts = db.get(date_target, {})

print(f"Evoluzione storica dei prezzi per la notte del {date_target}:")
print("-" * 80)

for apt_id, data in apts.items():
    if isinstance(data, list):
        history = data
    elif isinstance(data, dict):
        history = data.get('history', [])
        if not history:
            history = [data]
    else:
        continue
        
    valid_history = []
    for snapshot in history:
        status = snapshot.get('status')
        collected = snapshot.get('collected_at')
        if collected:
            cd = collected[:10]  
            if status == 'Disponibile':
                price = snapshot.get('price', 'N/D')
                if price != 'N/D':
                    valid_history.append(f"{cd}: {price} EUR")
            else:
                valid_history.append(f"{cd}: Occupato")
                
    if any('EUR' in h for h in valid_history):
        print(f"Appartamento {apt_id}:")
        for record in valid_history:
            print(f"  - {record}")
        print("-" * 40)
