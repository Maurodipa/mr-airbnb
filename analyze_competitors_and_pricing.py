import sys
import json
from collections import Counter
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

with open('banca_dati_airbnb_MCPserver_cleaned.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

with open('competitors.txt', 'r', encoding='utf-8') as f:
    comp_lines = [l.strip().split(':') for l in f if l.strip() and not l.startswith('===')]

comps = {parts[0]: {'fee': float(parts[1]) if len(parts) > 1 else 50.0, 'tag': parts[2] if len(parts) > 2 else ''} for parts in comp_lines}
USER_APT = '1589943047991118285'

dates = sorted([k for k in db.keys() if '2026-11-01' <= k <= '2027-02-28'])
print(f"Total dates analyzed: {len(dates)} (from {dates[0]} to {dates[-1]})")

comp_stats = {}
for cid in comps:
    comp_stats[cid] = {'avail_days': 0, 'booked_days': 0, 'rates': [], 'min_stays': []}

# Monthly breakdown of occupancy and rates
monthly_stats = {}
for d in dates:
    m = d[:7]
    if m not in monthly_stats:
        monthly_stats[m] = {'total_slots': 0, 'booked_slots': 0, 'pure_rates': [], 'site_rates': []}

for d in dates:
    m = d[:7]
    apts = db.get(d, {})
    for cid in comps:
        entry = apts.get(cid)
        monthly_stats[m]['total_slots'] += 1
        rate = entry.get('rate') if entry else None
        if entry and entry.get('status') == 'OK' and rate is not None and rate > 0:
            comp_stats[cid]['avail_days'] += 1
            comp_stats[cid]['rates'].append(rate)
            if 'minStay' in entry and entry['minStay']:
                comp_stats[cid]['min_stays'].append(entry['minStay'])
            if cid != USER_APT:
                monthly_stats[m]['pure_rates'].append(rate)
        else:
            comp_stats[cid]['booked_days'] += 1
            monthly_stats[m]['booked_slots'] += 1

print("\n=== MONTHLY MARKET OVERVIEW ===")
for m, st in sorted(monthly_stats.items()):
    occ = (st['booked_slots'] / st['total_slots'] * 100) if st['total_slots'] > 0 else 0
    avg_pure = (sum(st['pure_rates']) / len(st['pure_rates'])) if st['pure_rates'] else 0
    st['pure_rates'].sort()
    med_pure = st['pure_rates'][len(st['pure_rates'])//2] if st['pure_rates'] else 0
    # Equivalent calendar rate for median pure:
    med_cal = med_pure / 0.81089 if med_pure else 0
    print(f"Month: {m} | Cluster Occupancy: {occ:5.1f}% | Median Pure Rate: {med_pure:5.1f} € | Equiv Calendar Rate: {med_cal:5.1f} € | Data points: {len(st['pure_rates'])}")

print("\n=== TOP COMPETITORS RANKED BY OCCUPANCY (SOLD-OUT PRESSURE) ===")
sorted_comps = sorted(comp_stats.items(), key=lambda x: x[1]['booked_days'] / (x[1]['booked_days'] + x[1]['avail_days']), reverse=True)

for cid, st in sorted_comps:
    tot = st['booked_days'] + st['avail_days']
    occ_pct = (st['booked_days'] / tot * 100) if tot > 0 else 0
    avg_rate = (sum(st['rates']) / len(st['rates'])) if st['rates'] else 0
    min_stay_mode = Counter(st['min_stays']).most_common(1)[0][0] if st['min_stays'] else '-'
    st['rates'].sort()
    med_rate = st['rates'][len(st['rates'])//2] if st['rates'] else 0
    label = "👑 [TUO APPARTAMENTO]" if cid == USER_APT else f"ID: {cid}"
    print(f"{label:30} | Occ: {occ_pct:5.1f}% ({st['booked_days']:2d}/{tot:2d} gg) | Avg Pure: {avg_rate:5.1f} € | Med Pure: {med_rate:5.1f} € | Mode MinStay: {min_stay_mode} | Cleaning: {comps[cid]['fee']:4.1f} €")

# Distribution of Min Stay
all_min_stays = [Counter(st['min_stays']).most_common(1)[0][0] for cid, st in comp_stats.items() if st['min_stays'] and cid != USER_APT]
min_stay_dist = Counter(all_min_stays)
print("\n=== MINIMUM STAY DISTRIBUTION (BENCHMARK) ===")
for ms, count in sorted(min_stay_dist.items()):
    print(f"Minimum Stay {ms} notte/i: {count} listings ({count/len(all_min_stays)*100:.1f}%)")

# Distribution of Cleaning Fees
all_cleaning = [comps[cid]['fee'] for cid in comps if cid != USER_APT]
clean_dist = Counter(all_cleaning)
print("\n=== CLEANING FEE DISTRIBUTION (BENCHMARK) ===")
for cf, count in sorted(clean_dist.items()):
    print(f"Cleaning Fee {cf:4.1f} €: {count} listings ({count/len(all_cleaning)*100:.1f}%)")
