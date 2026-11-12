import json
import os
from datetime import datetime

with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

print("DB loaded.")
sample_dates = ['2026-11-08', '2026-11-15', '2026-11-25', '2026-12-08', '2026-12-25', '2026-12-31']
for d in sample_dates:
    if d in db:
        print(f"\n=== Date: {d} ===")
        found_hist = 0
        booked_count = 0
        for apt, v in db[d].items():
            if apt == 'static_details': continue
            status = v.get('status')
            hist = v.get('history', [])
            if status != 'OK':
                booked_count += 1
            if hist:
                found_hist += 1
        print(f"Total apts: {len(db[d])}, Booked (status!=OK): {booked_count}, Apts with history: {found_hist}")
        
        # print details of 2 booked apts with history
        shown = 0
        for apt, v in db[d].items():
            if v.get('status') != 'OK' and v.get('history'):
                print(f"  Apt {apt}: Current status={v.get('status')} at {v.get('collected_at')}")
                for h in v.get('history'):
                    print(f"    Past: status={h.get('status')} at {h.get('collected_at')}")
                shown += 1
                if shown >= 2: break
