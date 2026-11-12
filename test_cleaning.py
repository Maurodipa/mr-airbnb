import sys

sys.path.append('app')
import cleaning_estimator

cleaning_estimator.DATA_FILE = '../.agents/skills/market-scanner/banca_dati_airbnb.json'
res = cleaning_estimator.estimate_cleaning_fees()
print(res["data"].get("5791838", "Nessun dato per questo ID (usa fallback 50)"))
