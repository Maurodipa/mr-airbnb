import json
import re
import datetime

def parse_price(s):
    if not s: return 0.0
    m = re.search(r'[\d\,\.]+', s.replace('.', '').replace(',', '.'))
    return float(m.group()) if m else 0.0

with open('competitors.txt', 'r', encoding='utf-8') as f:
    comp_lines = [l.strip().split(':') for l in f if l.strip() and not l.startswith('#')]
    comps = {c[0]: {'cf': float(c[1]) if len(c)>1 else 50.0} for c in comp_lines}

user_id = '1589943047991118285'
with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

start_dt = datetime.date(2026, 11, 8)
end_dt = datetime.date(2026, 11, 30)
cur = start_dt

weekday_it = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
rows = []

while cur <= end_dt:
    ds = cur.strftime('%Y-%m-%d')
    giorno_sett = weekday_it[cur.weekday()]
    is_weekend = cur.weekday() in (4, 5, 6)
    
    day_data = db.get(ds, {})
    total_comps = len(comps)
    
    comp_rates = []
    comp_site_rates = []
    
    user_status = 'Occupato'
    user_cal = None
    user_site = None
    
    ue = day_data.get(user_id, {})
    if ue.get('status') == 'OK':
        user_status = 'Libero'
        raw = ue.get('rawResponse', {})
        disp = raw.get('structuredDisplayPrice', {})
        price_details = disp.get('explanationData', {}).get('priceDetails', [])
        total_gross = 0.0
        taxes = 0.0
        for g in price_details:
            for item in g.get('items', []):
                desc = item.get('description', '')
                if desc in ('Taxes', 'Tasse'):
                    taxes = parse_price(item.get('priceString', ''))
                if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                    total_gross = parse_price(item.get('priceString', ''))
        if total_gross > 0:
            user_cal = round(total_gross - taxes - 59.0)
            user_site = round(total_gross - taxes)
        else:
            prim = disp.get('primaryLine', {})
            p_str = prim.get('discountedPrice') or prim.get('price') or ''
            user_site = parse_price(p_str)
            user_cal = round(user_site - 59.0) if user_site else None

    avail_count = 0
    occ_count = 0
    for cid in comps:
        if cid == user_id:
            continue
        entry = day_data.get(cid, {})
        if entry.get('status') == 'OK':
            avail_count += 1
            raw = entry.get('rawResponse', {})
            disp = raw.get('structuredDisplayPrice', {})
            price_details = disp.get('explanationData', {}).get('priceDetails', [])
            total_gross = 0.0
            taxes = 0.0
            for g in price_details:
                for item in g.get('items', []):
                    desc = item.get('description', '')
                    if desc in ('Taxes', 'Tasse'):
                        taxes = parse_price(item.get('priceString', ''))
                    if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                        total_gross = parse_price(item.get('priceString', ''))
            cf_net = comps[cid]['cf']
            cf_gross = cf_net * 1.18
            ms = entry.get('minStay', 1)
            if ms <= 0: ms = 1
            if total_gross > 0:
                cal_rate = (total_gross - taxes - cf_gross) / ms
                site_rate = (total_gross - taxes) / ms
                comp_rates.append(cal_rate)
                comp_site_rates.append(site_rate)
        else:
            occ_count += 1
            
    tot_competitors = avail_count + occ_count
    occ_rate = (occ_count / tot_competitors * 100) if tot_competitors else 0.0
    
    comp_rates.sort()
    comp_site_rates.sort()
    
    def pct(lst, p):
        if not lst: return 0.0
        idx = int(round(p * (len(lst) - 1)))
        return lst[idx]
        
    median_cal = pct(comp_rates, 0.5)
    median_site = pct(comp_site_rates, 0.5)
    
    cal_recom = round(median_site - 59.0) if median_site > 0 else 0
    net_recom_simple = round(cal_recom * 0.81089)
    
    action = '-'
    diff = 0
    if user_status == 'Libero' and user_cal:
        diff = cal_recom - user_cal
        if abs(diff) <= 3:
            action = '✅ Allineato'
        elif diff > 3:
            action = f'🔺 Aumenta (+{diff} €)'
        else:
            action = f'🔻 Riduci ({diff} €)'
    elif user_status == 'Occupato':
        action = '🔒 Già Prenotato'

    rows.append({
        'date': ds,
        'day': giorno_sett,
        'is_we': is_weekend,
        'occ': occ_rate,
        'avail': avail_count,
        'total': tot_competitors,
        'median_site': round(median_site),
        'median_cal': round(median_cal),
        'user_status': user_status,
        'user_cal': user_cal,
        'user_site': user_site,
        'cal_recom': cal_recom,
        'net_recom': net_recom_simple,
        'action': action,
        'diff': diff
    })
    cur += datetime.timedelta(days=1)

print('| Data | Giorno | Occupazione Cluster | Mediana Competitor Calendario | Mediana Competitor Airbnb | Tua Tariffa Attuale Calendario | Tua Tariffa Attuale Airbnb | **Tariffa Raccomandata a Calendario** | Netto Stimato Host | Azione Consigliata |')
print('|---|---|---|---|---|---|---|---|---|---|')
for r in rows:
    g = f"**{r['day']}**" if r['is_we'] else r['day']
    u_cal_str = f"{r['user_cal']} €" if r['user_cal'] else ("🔒 Prenotato" if r['user_status']=='Occupato' else "-")
    u_site_str = f"{r['user_site']} €" if r['user_site'] else "-"
    rec_str = f"**{r['cal_recom']} €**" if r['user_status']=='Libero' else "-"
    net_str = f"{r['net_recom']} €" if r['user_status']=='Libero' else "-"
    print(f"| {r['date']} | {g} | {r['occ']:.1f}% ({r['avail']}/{r['total']} liberi) | {r['median_cal']} € | {r['median_site']} € | {u_cal_str} | {u_site_str} | {rec_str} | {net_str} | {r['action']} |")
