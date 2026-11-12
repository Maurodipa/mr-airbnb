import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

TODAY = datetime(2026, 11, 10)

with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

# Competitors
competitors = []
with open('competitors.txt', 'r', encoding='utf-8') as f:
    for line in f:
        if '===' in line: break
        parts = line.strip().split(':')
        if parts and parts[0].strip().isdigit():
            apt_id = parts[0].strip()
            if apt_id != '1589943047991118285':
                competitors.append(apt_id)

# Titles
titles = {}
if os.path.exists('titles.txt'):
    with open('titles.txt', 'r', encoding='utf-8') as f:
        for line in f:
            p = line.strip().split(' -- ')
            if len(p) == 2:
                titles[p[0].strip()] = p[1].strip()

nov_dec_dates = sorted([d for d in db.keys() if '2026-11-01' <= d <= '2026-12-31'])
print(f"Total competitors: {len(competitors)}")
print(f"Dates in Nov-Dec: {len(nov_dec_dates)} ({nov_dec_dates[0]} -> {nov_dec_dates[-1]})")

# Analyze per competitor
comp_summary = {}

for cid in competitors:
    comp_summary[cid] = {
        'total_dates': len(nov_dec_dates),
        'booked_dates': 0,
        'avail_dates': 0,
        'booking_times': [], # list of (date, days_ago, category, last_avail, first_booked)
    }
    
    for d in nov_dec_dates:
        apts = db.get(d, {})
        entry = apts.get(cid)
        if not entry:
            continue
            
        status = entry.get('status')
        if status == 'OK':
            comp_summary[cid]['avail_dates'] += 1
            continue
            
        comp_summary[cid]['booked_dates'] += 1
        
        # Build chronological timeline
        timeline = []
        for h in entry.get('history', []):
            if 'collected_at' in h:
                timeline.append((h.get('collected_at'), h.get('status')))
        if 'collected_at' in entry:
            timeline.append((entry.get('collected_at'), entry.get('status')))
            
        # Sort by timestamp
        timeline.sort(key=lambda x: x[0])
        
        # Find transition
        # Case A: always 'Non disponibile' across all scans
        # Case B: was 'OK' at some point, then became 'Non disponibile'
        last_ok_ts = None
        first_booked_ts = None
        
        for ts, st in timeline:
            if st == 'OK':
                last_ok_ts = ts
                first_booked_ts = None # reset if it became free again
            elif st != 'OK' and first_booked_ts is None:
                first_booked_ts = ts
                
        if first_booked_ts is None and timeline:
            first_booked_ts = timeline[0][0]
            
        # Parse timestamp to calculate days ago
        try:
            fb_dt = datetime.fromisoformat(first_booked_ts)
            days_ago = (TODAY - fb_dt).days
        except Exception:
            fb_dt = None
            days_ago = None
            
        is_ancient = (last_ok_ts is None and len(timeline) > 1)
        
        comp_summary[cid]['booking_times'].append({
            'date': d,
            'days_ago': days_ago,
            'first_booked_ts': first_booked_ts[:10] if first_booked_ts else 'N/D',
            'last_ok_ts': last_ok_ts[:10] if last_ok_ts else 'Mai libero',
            'is_ancient': is_ancient
        })

print("\n--- SAMPLE COMPETITOR AGGREGATION ---")
for cid in competitors[:5]:
    cdata = comp_summary[cid]
    title = titles.get(cid, 'Alloggio ' + cid)[:35]
    print(f"\nID {cid} ({title}): Booked {cdata['booked_dates']}/{cdata['total_dates']} dates")
    # Group booking times by time buckets:
    # > 40 giorni fa (Prima del 1 Ottobre)
    # 30-40 giorni fa (1-10 Ottobre)
    # 20-30 giorni fa (11-20 Ottobre)
    # 10-20 giorni fa (21-31 Ottobre)
    # < 10 giorni fa (1-10 Novembre)
    b_ancient = sum(1 for b in cdata['booking_times'] if b['is_ancient'])
    b_recent = [b for b in cdata['booking_times'] if not b['is_ancient']]
    print(f"  Gia' prenotato da > 40 gg (prima delle nostre scansioni): {b_ancient} date")
    if b_recent:
        avg_days = sum(b['days_ago'] for b in b_recent if b['days_ago'] is not None) / len(b_recent)
        print(f"  Prenotati durante il monitoraggio: {len(b_recent)} date (media {avg_days:.1f} giorni fa)")
