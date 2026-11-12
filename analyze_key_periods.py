import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

with open('banca_dati_airbnb_MCPserver_cleaned.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

USER_APT = '1589943047991118285'

key_periods = [
    ('Ponte Immacolata (04-08 Dic)', ['2026-12-04', '2026-12-05', '2026-12-06', '2026-12-07', '2026-12-08']),
    ('Natale & Capodanno (24 Dic - 03 Gen)', [f'2026-12-{d:02d}' for d in range(24, 32)] + ['2027-01-01', '2027-01-02', '2027-01-03']),
    ('Bassa Stagione Gennaio (11-18 Gen)', [f'2027-01-{d:02d}' for d in range(11, 19)]),
    ('Febbraio Inizio Mese (01-07 Feb)', [f'2027-02-{d:02d}' for d in range(1, 8)]),
    ('Febbraio Fine Mese (22-28 Feb)', [f'2027-02-{d:02d}' for d in range(22, 29)])
]

for title, dlist in key_periods:
    print(f"\n--- {title} ---")
    print(f"{'Data':10} | {'Occ%':5} | {'Avail':7} | {'Med Pure':8} | {'Med Cal':7} | {'Med Site':8} | {'User Cal':8}")
    for d in dlist:
        apts = db.get(d, {})
        rates = []
        user_cal = '-'
        user_entry = apts.get(USER_APT)
        if user_entry and user_entry.get('status') == 'OK' and user_entry.get('rate'):
            user_cal = f"{round(user_entry['rate'] / 0.81089)} €"
        elif user_entry and user_entry.get('status') != 'OK':
            user_cal = "🔒 Pren"
            
        for cid, entry in apts.items():
            if cid != USER_APT and entry and entry.get('status') == 'OK' and entry.get('rate'):
                rates.append(entry['rate'])
        tot = len(apts) - 1 if USER_APT in apts else len(apts)
        avail = len(rates)
        occ = ((tot - avail) / tot * 100) if tot > 0 else 0
        rates.sort()
        med_p = rates[len(rates)//2] if rates else 0
        med_c = med_p / 0.81089 if med_p else 0
        med_s = med_c + 59 if med_c else 0
        print(f"{d:10} | {occ:5.1f}% | {avail:2d}/{tot:2d} lib | {med_p:6.1f} € | {med_c:5.0f} € | {med_s:6.0f} € | {user_cal:8}")
