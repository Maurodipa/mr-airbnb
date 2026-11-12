import json
from datetime import datetime
from app.market_scanner import process_mcp_data

def main():
    with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
        raw_db = json.load(f)
        
    fees = {}
    with open('competitors.txt', 'r', encoding='utf-8') as f:
        for l in f:
            if ':' in l:
                parts = l.strip().split(':')
                fees[parts[0]] = int(parts[1])
                
    # Ricalcola la pulizia (aggiorna banca_dati_airbnb_MCPserver_cleaned.json)
    process_mcp_data(raw_db, fees)
    
    with open('banca_dati_airbnb_MCPserver_cleaned.json', 'r', encoding='utf-8') as f:
        clean_db = json.load(f)
        
    dates = [f"2026-08-{str(i).zfill(2)}" for i in range(1, 19)]
    
    prezzi = []
    occupati = 0
    liberi = 0
    
    for date in dates:
        if date in clean_db:
            for apt, data in clean_db[date].items():
                if data.get('status') == 'OK' and 'rate' in data:
                    prezzi.append(data['rate'])
                    liberi += 1
                else:
                    occupati += 1
                    
    if prezzi:
        media = sum(prezzi) / len(prezzi)
        minimo = min(prezzi)
        massimo = max(prezzi)
        
        report = f"""# Analisi Mercato (1-18 Agosto 2026)

## Statistiche Generali (Tariffe Pure per Notte)
- **Appartamenti Disponibili (Slot totali nei 18 giorni):** {liberi}
- **Appartamenti Saturi (Slot totali nei 18 giorni):** {occupati}
- **Media del Mercato:** {media:.2f} €
- **Prezzo Minimo:** {minimo} €
- **Prezzo Massimo:** {massimo} €

## Tasso di Occupazione
- **Occupazione stimata:** {(occupati / (liberi + occupati) * 100):.1f}%
"""
        with open('artifacts/report_agosto_1_18_50gemelli.md', 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report generato! Media: {media:.2f} €, Minimo: {minimo} €, Massimo: {massimo} €")
        
if __name__ == "__main__":
    main()
