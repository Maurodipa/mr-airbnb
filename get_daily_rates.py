import json
import re
import argparse
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def parse_price(s):
    if not s: return 0.0
    m = re.search(r'[\d\,\.]+', s.replace('.', '').replace(',', '.'))
    return float(m.group()) if m else 0.0

def main():
    parser = argparse.ArgumentParser(description='Ottieni tariffe esatte per una o più date.')
    parser.add_argument('--date', required=True, help='Data o date separate da virgola nel formato YYYY-MM-DD (es. 2026-10-16,2026-10-20)')
    parser.add_argument('--user-apt', default='1589943047991118285', help='ID appartamento utente')
    args = parser.parse_args()
    
    target_dates = [d.strip() for d in args.date.split(',')]
    user_apt_id = args.user_apt
    
    try:
        with open('banca_dati_airbnb_MCPserver.json', encoding='utf-8') as f:
            d = json.load(f)
    except FileNotFoundError:
        try:
            with open('banca_dati_airbnb_MCPserver_backup.json', encoding='utf-8') as f:
                d = json.load(f)
        except FileNotFoundError:
            print("Errore: Nessun database trovato.")
            return

    cleaning_fees = {}
    valid_competitors = set()
    try:
        with open('competitors.txt', encoding='utf-8') as f:
            reading_fees = False
            for line in f:
                line = line.strip()
                if not line: continue
                if '===CLEANING_FEES===' in line: 
                    reading_fees = True
                    continue
                if reading_fees and '=' in line:
                    parts = line.split('=')
                    cleaning_fees[parts[0]] = float(parts[1])
                elif not reading_fees:
                    apt_id = line.split(':')[0]
                    valid_competitors.add(apt_id)
    except Exception:
        pass

    all_results = []
    
    for t_date in target_dates:
        if t_date not in d:
            continue

        for apt_id, v in d[t_date].items():
            if valid_competitors and apt_id not in valid_competitors:
                continue
            if v.get('status') == 'OK' and v.get('rawResponse'):
                book_it = v['rawResponse']
                price_details = book_it.get('structuredDisplayPrice', {}).get('explanationData', {}).get('priceDetails', [])
                total_gross = 0.0
                taxes = 0.0
                
                for g in price_details:
                    for item in g.get('items', []):
                        desc = item.get('description', '')
                        if desc in ('Taxes', 'Tasse'):
                            taxes = parse_price(item.get('priceString', ''))
                        if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                            total_gross = parse_price(item.get('priceString', ''))
                
                cf_net = cleaning_fees.get(apt_id, 50.0)
                cf_gross = cf_net * 1.18
                min_stay = v.get('minStay', 1)
                if min_stay <= 0: min_stay = 1
                
                if total_gross > 0:
                    calendar_rate = (total_gross - taxes - cf_gross) / min_stay
                    net_profit = calendar_rate * 0.8109
                    site_rate = (total_gross - taxes) / min_stay
                    all_results.append({
                        'date': t_date,
                        'id': apt_id,
                        'calendar': round(calendar_rate),
                        'net': round(net_profit),
                        'site': round(site_rate),
                        'cf': round(cf_net),
                        'cf_gross': round(cf_gross)
                    })
    
    all_results.sort(key=lambda x: (x['date'], x['calendar']))
    
    # Calcolo mediana per ogni data e recupero tariffa utente
    def calculate_percentile(data, percentile):
        n = len(data)
        if n == 0: return 0.0
        k = (n - 1) * percentile
        f = int(k)
        c = f + 1
        if f == c or c >= n: return float(data[f])
        return float(data[f] + (k - f) * (data[c] - data[f]))

    import os
    
    titles_dict = {}
    titles_path = 'titles.txt'
    if os.path.exists(titles_path):
        with open(titles_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.split(' -- ')
                if len(parts) == 2:
                    apt_id = parts[0].strip()
                    title_full = parts[1]
                    if '·' in title_full:
                        clean_title = title_full.split('·')[0].strip()
                    elif ' A ' in title_full:
                        clean_title = title_full.split(' A ')[0].strip()
                    elif ' Â' in title_full:
                        clean_title = title_full.split(' Â')[0].strip()
                    else:
                        clean_title = title_full.strip()
                    titles_dict[apt_id] = clean_title
    
    from collections import defaultdict
    dates_dict = defaultdict(list)
    user_cal_per_date = {}
    user_site_per_date = {}
    
    for r in all_results:
        if r['id'] == user_apt_id:
            user_cal_per_date[r['date']] = r['calendar']
            user_site_per_date[r['date']] = r['site']
        else:
            dates_dict[r['date']].append(r['site'])
            
    medians_per_date = {}
    for d_date, s_rates in dates_dict.items():
        if s_rates:
            s_rates.sort()
            medians_per_date[d_date] = calculate_percentile(s_rates, 0.5)
        else:
            medians_per_date[d_date] = 0.0
    
    print("\n| Data | Appartamento | Competitor Calendario | Tariffa su Airbnb | Tariffa su Airbnb (eq. 1 notte) | Tariffa per le pulizie | Tariffa calendario mio appartamento | Tariffa Airbnb mio appartamento | Tariffa da mettere a calendario per il mio appartamento |")
    print("|---|---|---|---|---|---|---|---|---|")
    
    user_min_stay = 1
    
    for r in all_results:
        is_user = (r['id'] == user_apt_id)
        
        median_site = medians_per_date.get(r['date'], 0.0)
        user_curr_cal = user_cal_per_date.get(r['date'], "-")
        user_curr_site = user_site_per_date.get(r['date'], "-")
        
        target_mio_calendario = median_site - (59.0 / user_min_stay) if median_site > 0 else 0
        
        site_eq_1 = r['calendar'] + r['cf_gross']
        
        display_title = titles_dict.get(str(r['id']), f"Appartamento {r['id']}")
        
        if is_user:
            print(f"| {r['date']} | 👑 **Il Tuo Appartamento** ([Link](https://www.airbnb.it/rooms/{r['id']})) | {r['calendar']} € | {r['site']} € | {round(site_eq_1)} € | {r['cf']} € | **{user_curr_cal} €** | **{user_curr_site} €** | **{round(target_mio_calendario)} €** |")
        else:
            print(f"| {r['date']} | [{display_title}](https://www.airbnb.it/rooms/{r['id']}) | {r['calendar']} € | {r['site']} € | {round(site_eq_1)} € | {r['cf']} € | {user_curr_cal} € | {user_curr_site} € | **{round(target_mio_calendario)} €** |")

if __name__ == '__main__':
    main()
