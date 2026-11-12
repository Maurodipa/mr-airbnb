import sys
import json
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

# Load DB
with open('banca_dati_airbnb_MCPserver_cleaned.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

# Load competitors
with open('competitors.txt', 'r', encoding='utf-8') as f:
    comp_lines = [l.strip().split(':') for l in f if l.strip() and not l.startswith('===')]

comps = {parts[0]: {'fee': float(parts[1]) if len(parts) > 1 else 50.0} for parts in comp_lines}
USER_APT = '1589943047991118285'

# Load titles
titles = {}
with open('titles.txt', 'r', encoding='utf-8') as f:
    for line in f:
        p = line.strip().split(' -- ')
        if len(p) == 2:
            titles[p[0].strip()] = p[1].strip()

dates = sorted([k for k in db.keys() if '2026-11-01' <= k <= '2027-02-28'])

# Collect stats
stats = {}
for cid in comps:
    stats[cid] = {
        'avail': 0, 'booked': 0,
        'rates': [], 'min_stays': [],
        'months': {'2026-11': [0,0], '2026-12': [0,0], '2027-01': [0,0], '2027-02': [0,0]} # [avail, booked]
    }

for d in dates:
    m = d[:7]
    apts = db.get(d, {})
    for cid in comps:
        entry = apts.get(cid)
        rate = entry.get('rate') if entry else None
        if entry and entry.get('status') == 'OK' and rate is not None and rate > 0:
            stats[cid]['avail'] += 1
            stats[cid]['rates'].append(rate)
            if entry.get('minStay'):
                stats[cid]['min_stays'].append(entry['minStay'])
            stats[cid]['months'][m][0] += 1
        else:
            stats[cid]['booked'] += 1
            stats[cid]['months'][m][1] += 1

print(f"Stats processed for {len(stats)} listings across {len(dates)} dates.\n")

# Classify competitors into tiers based on median pure rate:
# Tier 1: Low-Cost / Aggressive Volume (< 105 €)
# Tier 2: Mid-Market Core (105 € - 150 €)
# Tier 3: Premium / High Margin (> 150 €)

t1, t2, t3 = [], [], []

for cid, st in stats.items():
    if cid == USER_APT:
        continue
    st['rates'].sort()
    med_rate = st['rates'][len(st['rates'])//2] if st['rates'] else 0
    tot = st['avail'] + st['booked']
    occ = (st['booked'] / tot * 100) if tot > 0 else 0
    ms_mode = Counter(st['min_stays']).most_common(1)[0][0] if st['min_stays'] else 1
    t_full = titles.get(cid, 'Unknown')
    
    # parse rating & beds
    rating = '-'
    beds = '-'
    room_type = 'Apartment'
    if 'A·' in t_full:
        parts = [x.strip() for x in t_full.split('A·')]
        if len(parts) >= 1: room_type = parts[0]
        if len(parts) >= 2: rating = parts[1].replace('~.', '').replace('★', '').strip()
        if len(parts) >= 3: beds = parts[2]
        if len(parts) >= 4: beds += ' / ' + parts[3]
    
    info = {
        'id': cid,
        'title': room_type,
        'rating': rating,
        'beds': beds,
        'occ': occ,
        'booked': st['booked'],
        'avail': st['avail'],
        'med_pure': med_rate,
        'avg_pure': sum(st['rates'])/len(st['rates']) if st['rates'] else 0,
        'equiv_cal': round(med_rate / 0.81089) if med_rate else 0,
        'min_stay': ms_mode,
        'cleaning': comps[cid]['fee'],
        'nov_occ': st['months']['2026-11'][1] / 30 * 100,
        'dec_occ': st['months']['2026-12'][1] / 31 * 100,
        'jan_occ': st['months']['2027-01'][1] / 31 * 100,
        'feb_occ': st['months']['2027-02'][1] / 28 * 100,
    }
    
    if med_rate < 105:
        t1.append(info)
    elif med_rate <= 150:
        t2.append(info)
    else:
        t3.append(info)

print(f"Tier 1 (Budget / High Volume < 105 €): {len(t1)} listings")
for x in sorted(t1, key=lambda i: i['occ'], reverse=True):
    print(f"  {x['id']:19} | Occ: {x['occ']:5.1f}% (Nov {x['nov_occ']:4.0f}% Dec {x['dec_occ']:4.0f}%) | MedPure: {x['med_pure']:3.0f} € (Cal ~{x['equiv_cal']:3.0f} €) | MS: {x['min_stay']}n | Clean: {x['cleaning']:2.0f} € | {x['title']}")

print(f"\nTier 2 (Mid-Market Core 105 € - 150 €): {len(t2)} listings")
for x in sorted(t2, key=lambda i: i['occ'], reverse=True):
    print(f"  {x['id']:19} | Occ: {x['occ']:5.1f}% (Nov {x['nov_occ']:4.0f}% Dec {x['dec_occ']:4.0f}%) | MedPure: {x['med_pure']:3.0f} € (Cal ~{x['equiv_cal']:3.0f} €) | MS: {x['min_stay']}n | Clean: {x['cleaning']:2.0f} € | {x['title']}")

print(f"\nTier 3 (Premium / High Yield > 150 €): {len(t3)} listings")
for x in sorted(t3, key=lambda i: i['occ'], reverse=True):
    print(f"  {x['id']:19} | Occ: {x['occ']:5.1f}% (Nov {x['nov_occ']:4.0f}% Dec {x['dec_occ']:4.0f}%) | MedPure: {x['med_pure']:3.0f} € (Cal ~{x['equiv_cal']:3.0f} €) | MS: {x['min_stay']}n | Clean: {x['cleaning']:2.0f} € | {x['title']}")
