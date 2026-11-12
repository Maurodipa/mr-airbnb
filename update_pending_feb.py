import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Diccionario delle nuove tariffe febbraio 2027 (-5%)
feb_rates_5pct = {
    '2027-02-01': 104,
    '2027-02-02': 114,
    '2027-02-03': 113,
    '2027-02-04': 113,
    '2027-02-05': 115,
    '2027-02-06': 113,
    '2027-02-07': 114,
    '2027-02-08': 104,
    '2027-02-09': 113,
    '2027-02-10': 104,
    '2027-02-11': 114,
    '2027-02-12': 114,
    '2027-02-13': 114,
    '2027-02-14': 104,
    '2027-02-15': 113,
    '2027-02-16': 104,
    '2027-02-17': 104,
    '2027-02-18': 98,
    '2027-02-19': 100,
    '2027-02-20': 98,
    '2027-02-21': 113,
    '2027-02-22': 96,
    '2027-02-23': 98,
    '2027-02-24': 104,
    '2027-02-25': 98,
    '2027-02-26': 113,
    '2027-02-27': 113,
    '2027-02-28': 122
}

# Aggiorna pending_price_updates.json
pending_path = 'pending_price_updates.json'
with open(pending_path, 'r', encoding='utf-8') as f:
    pending = json.load(f)

updated_count = 0
for item in pending:
    d = item['date']
    if d in feb_rates_5pct:
        item['price'] = feb_rates_5pct[d]
        item['action'] = f"🎯 Ricalcolo -5%: {feb_rates_5pct[d]} €"
        updated_count += 1

with open(pending_path, 'w', encoding='utf-8') as f:
    json.dump(pending, f, indent=2, ensure_ascii=False)

print(f"Aggiornate {updated_count} date in {pending_path} con tariffe -5%.")
