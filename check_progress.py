import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

with open('.current_scan_session.json', 'r', encoding='utf-8') as f:
    sess = json.load(f)
s_time = sess.get('start_time')

print(f"Session start: {s_time}")
dates = sorted([d for d in db.keys() if '2026-11-08' <= d <= '2027-02-28'])
print(f"Total dates in DB range: {len(dates)}")

completed_dates = []
in_progress_date = None

for d in dates:
    scanned_sess = sum(1 for apt, v in db[d].items() if v.get('collected_at', '') >= s_time)
    if scanned_sess == 37:
        completed_dates.append(d)
    else:
        in_progress_date = (d, scanned_sess)
        print(f"In progress: {d} ({scanned_sess}/37)")
        break

print(f"Fully completed dates count: {len(completed_dates)}")
if completed_dates:
    print(f"Range completed: {completed_dates[0]} -> {completed_dates[-1]}")
