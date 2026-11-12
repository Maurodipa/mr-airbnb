import json
from app.mcp_market_scanner import process_mcp_data, load_competitors_config

SAFE_FILE = "banca_dati_airbnb_MCPserver_safe.json"

def main():
    print("Lettura del data lake sicuro...")
    try:
        with open(SAFE_FILE, "r", encoding="utf-8") as f:
            market_data = json.load(f)
    except FileNotFoundError:
        print(f"Errore: {SAFE_FILE} non trovato.")
        return
        
    print("Caricamento configurazione competitors...")
    competitors, cleaning_fees = load_competitors_config()
    
    print("Elaborazione dati e calcolo tariffe pure...")
    process_mcp_data(market_data, cleaning_fees)
    
    print("Database pulito (banca_dati_airbnb_pure.json) aggiornato con successo a partire da _safe.json!")

if __name__ == "__main__":
    main()
