import json
import os
import sys
from datetime import datetime
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

TODAY = datetime(2026, 11, 10)

with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

# Competitors
competitors = []
comp_tags = {}
with open('competitors.txt', 'r', encoding='utf-8') as f:
    for line in f:
        if '===' in line: break
        parts = line.strip().split(':')
        if parts and parts[0].strip().isdigit():
            apt_id = parts[0].strip()
            if apt_id != '1589943047991118285':
                competitors.append(apt_id)
                comp_tags[apt_id] = parts[2] if len(parts) > 2 else ''

# Titles
titles = {}
if os.path.exists('titles.txt'):
    with open('titles.txt', 'r', encoding='utf-8') as f:
        for line in f:
            p = line.strip().split(' -- ')
            if len(p) == 2:
                titles[p[0].strip()] = p[1].strip()

nov_dec_dates = sorted([d for d in db.keys() if '2026-11-01' <= d <= '2026-12-31'])

# Data structures
# per competitor:
# booked dates list with details:
# {
#   date: '2026-11-08',
#   booking_date: datetime,
#   days_ago: int,
#   lead_time_days: int (stay_date - booking_date),
#   window_str: str ('Prima del 30/09', 'Tra 01/10 e 10/10', etc.)
# }

comp_details = {}

for cid in competitors:
    booked_entries = []
    avail_entries = []
    
    for d in nov_dec_dates:
        apts = db.get(d, {})
        entry = apts.get(cid)
        if not entry:
            continue
            
        status = entry.get('status')
        if status == 'OK':
            avail_entries.append(d)
            continue
            
        timeline = []
        for h in entry.get('history', []):
            if 'collected_at' in h:
                timeline.append((h.get('collected_at'), h.get('status')))
        if 'collected_at' in entry:
            timeline.append((entry.get('collected_at'), entry.get('status')))
            
        timeline.sort(key=lambda x: x[0])
        
        last_ok_ts = None
        first_booked_ts = None
        
        for ts, st in timeline:
            if st == 'OK':
                last_ok_ts = ts
                first_booked_ts = None
            elif st != 'OK' and first_booked_ts is None:
                first_booked_ts = ts
                
        if first_booked_ts is None and timeline:
            first_booked_ts = timeline[0][0]
            
        fb_dt = datetime.fromisoformat(first_booked_ts) if first_booked_ts else None
        stay_dt = datetime.strptime(d, '%Y-%m-%d')
        
        days_ago = (TODAY - fb_dt).days if fb_dt else None
        lead_time = (stay_dt - fb_dt).days if fb_dt else None
        
        # Categorize timing
        if last_ok_ts is None and len(timeline) > 1:
            timing_cat = "> 40 gg fa (ante 30/09)"
            window_str = f"Prima del {timeline[0][0][:10]}"
        else:
            if days_ago is not None:
                if days_ago >= 30:
                    timing_cat = "30-40 gg fa (Inizio Ottobre)"
                elif days_ago >= 15:
                    timing_cat = "15-30 gg fa (Metà-Fine Ottobre)"
                elif days_ago >= 5:
                    timing_cat = "5-14 gg fa (Inizio Novembre)"
                else:
                    timing_cat = "< 5 gg fa (Last-Minute)"
                window_str = f"Circa {days_ago} gg fa ({first_booked_ts[:10]})"
            else:
                timing_cat = "N/D"
                window_str = "N/D"
                
        booked_entries.append({
            'date': d,
            'stay_dt': stay_dt,
            'fb_dt': fb_dt,
            'days_ago': days_ago,
            'lead_time': lead_time,
            'timing_cat': timing_cat,
            'window_str': window_str,
            'is_ancient': (last_ok_ts is None and len(timeline) > 1)
        })
        
    comp_details[cid] = {
        'total': len(nov_dec_dates),
        'booked': len(booked_entries),
        'avail': len(avail_entries),
        'booked_entries': booked_entries
    }

print("Elaborazione completata per tutti i 36 competitor.")

# Print overall summary of booking time windows across all booked nights in Nov-Dec
cat_counts = defaultdict(int)
total_booked_nights = 0
for cid, data in comp_details.items():
    for b in data['booked_entries']:
        cat_counts[b['timing_cat']] += 1
        total_booked_nights += 1

print(f"\nTotale notti prenotate nel cluster a Nov-Dic: {total_booked_nights} su {36*61} notti totali ({total_booked_nights/(36*61)*100:.1f}% occupazione complessiva)")
for cat, cnt in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {cat:35}: {cnt:4d} notti ({cnt/total_booked_nights*100:5.1f}%)")
