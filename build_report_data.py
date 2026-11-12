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

competitors = []
comp_tags = {}
comp_cleaning = {}
with open('competitors.txt', 'r', encoding='utf-8') as f:
    for line in f:
        if '===' in line: break
        parts = line.strip().split(':')
        if parts and parts[0].strip().isdigit():
            apt_id = parts[0].strip()
            if apt_id != '1589943047991118285':
                competitors.append(apt_id)
                comp_cleaning[apt_id] = float(parts[1]) if len(parts) > 1 else 50.0
                comp_tags[apt_id] = parts[2] if len(parts) > 2 else ''

titles = {}
if os.path.exists('titles.txt'):
    with open('titles.txt', 'r', encoding='utf-8') as f:
        for line in f:
            p = line.strip().split(' -- ')
            if len(p) == 2:
                titles[p[0].strip()] = p[1].strip()

nov_dates = sorted([d for d in db.keys() if '2026-11-01' <= d <= '2026-11-30'])
dec_dates = sorted([d for d in db.keys() if '2026-12-01' <= d <= '2026-12-31'])
all_dates = nov_dates + dec_dates

comp_data = {}

for cid in competitors:
    nov_booked = 0
    dec_booked = 0
    booked_entries = []
    
    for d in all_dates:
        entry = db.get(d, {}).get(cid)
        if not entry: continue
        status = entry.get('status')
        if status == 'OK': continue
        
        is_nov = (d in nov_dates)
        if is_nov: nov_booked += 1
        else: dec_booked += 1
        
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
        
        days_ago = (TODAY - fb_dt).days if fb_dt else 0
        lead_time = (stay_dt - fb_dt).days if fb_dt else 0
        is_ancient = (last_ok_ts is None and len(timeline) > 1)
        
        booked_entries.append({
            'date': d,
            'is_nov': is_nov,
            'stay_dt': stay_dt,
            'fb_dt': fb_dt,
            'days_ago': days_ago,
            'lead_time': lead_time,
            'is_ancient': is_ancient,
            'fb_ts_str': first_booked_ts[:10] if first_booked_ts else 'N/D'
        })
        
    # Group by timing category
    ancient_cnt = sum(1 for b in booked_entries if b['is_ancient'])
    oct_cnt = sum(1 for b in booked_entries if not b['is_ancient'] and 15 <= b['days_ago'] < 40)
    recent_cnt = sum(1 for b in booked_entries if not b['is_ancient'] and b['days_ago'] < 15)
    
    # Average days ago for bookings that happened during our monitoring
    monitored = [b for b in booked_entries if not b['is_ancient']]
    avg_days_ago = (sum(b['days_ago'] for b in monitored) / len(monitored)) if monitored else None
    avg_lead_time = (sum(b['lead_time'] for b in booked_entries) / len(booked_entries)) if booked_entries else None
    
    comp_data[cid] = {
        'nov_booked': nov_booked,
        'dec_booked': dec_booked,
        'total_booked': nov_booked + dec_booked,
        'ancient_cnt': ancient_cnt,
        'oct_cnt': oct_cnt,
        'recent_cnt': recent_cnt,
        'avg_days_ago': avg_days_ago,
        'avg_lead_time': avg_lead_time,
        'booked_entries': booked_entries
    }

print("Statistiche calcolate per tutti i competitor.")

# Check key periods:
key_periods = {
    'Weekend Novembre (Ven-Sab)': [d for d in nov_dates if datetime.strptime(d, '%Y-%m-%d').weekday() in (4,5)],
    'Ponte Immacolata (05-08 Dic)': ['2026-12-05', '2026-12-06', '2026-12-07', '2026-12-08'],
    'Natale (24-26 Dic)': ['2026-12-24', '2026-12-25', '2026-12-26'],
    'Capodanno (30 Dic - 01 Gen)': ['2026-12-30', '2026-12-31']
}

print("\n=== KEY PERIODS TIMING ANALYSIS ===")
for pname, pdates in key_periods.items():
    p_booked = 0
    p_ancient = 0
    p_oct = 0
    p_recent = 0
    p_free = 0
    for d in pdates:
        for cid in competitors:
            entry = db.get(d, {}).get(cid, {})
            if entry.get('status') == 'OK':
                p_free += 1
            else:
                p_booked += 1
                # check when
                b_match = [b for b in comp_data[cid]['booked_entries'] if b['date'] == d]
                if b_match:
                    b = b_match[0]
                    if b['is_ancient']: p_ancient += 1
                    elif b['days_ago'] >= 15: p_oct += 1
                    else: p_recent += 1
    total_slots = p_booked + p_free
    print(f"{pname} (tot {total_slots} slot):")
    print(f"  Prenotati: {p_booked}/{total_slots} ({p_booked/total_slots*100:.1f}%) | Liberi: {p_free} ({p_free/total_slots*100:.1f}%)")
    if p_booked > 0:
        print(f"    - Già prenotati con largo anticipo (> 40 gg fa): {p_ancient} ({p_ancient/p_booked*100:.1f}%)")
        print(f"    - Prenotati a Ottobre (15-40 gg fa): {p_oct} ({p_oct/p_booked*100:.1f}%)")
        print(f"    - Prenotati di recente (< 15 gg fa): {p_recent} ({p_recent/p_booked*100:.1f}%)")
