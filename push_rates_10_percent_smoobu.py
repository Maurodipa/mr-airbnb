import os
import sys
import json
import base64
import hmac
import hashlib
import datetime
import uuid
import urllib.request

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '.agents', 'skills', 'price-recommender', 'scripts'))
from recommend import calculate_percentile, extract_nightly_rate, load_cleaning_fees

def get_recommended_rates_10_percent(start_date, end_date):
    with open('mr-airbnb/banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    dates = [d for d in db.keys() if start_date <= d <= end_date]
    dates.sort()
    
    valid_competitors = set()
    if os.path.exists('mr-airbnb/competitors.txt'):
        with open('mr-airbnb/competitors.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if '===' in line: break
                parts = line.split(':')
                if parts[0].strip().isdigit():
                    valid_competitors.add(parts[0].strip())
    
    cleaning_fees = load_cleaning_fees()
    host_cleaning = 50.0
    guest_cleaning = 59.0
    user_apt = "1589943047991118285"
    
    rates_list = []
    
    for d in dates:
        apts = db[d]
        if not isinstance(apts, dict): continue
        
        site_rates = []
        user_entry = apts.get(user_apt)
        user_min_stay = 1
        if user_entry:
            e = user_entry[-1] if isinstance(user_entry, list) else user_entry
            user_min_stay = e.get("minStay", 1) if isinstance(e, dict) else 1
            if user_min_stay <= 0: user_min_stay = 1
            
        for apt_id, entry in apts.items():
            if apt_id == user_apt: continue
            if valid_competitors and apt_id not in valid_competitors: continue
            rate, s_rate = extract_nightly_rate(entry, apt_id, cleaning_fees, host_cleaning)
            if rate is not None and rate > 0 and s_rate:
                site_rates.append(s_rate)
                
        if not site_rates:
            continue
            
        site_rates.sort()
        median_site_rate = calculate_percentile(site_rates, 0.5)
        
        airbnb_10_percent = median_site_rate * 0.90
        user_cal_for_site_10 = airbnb_10_percent - (guest_cleaning / user_min_stay)
        
        rates_list.append({
            'date': d,
            'price': round(user_cal_for_site_10)
        })
        
    return rates_list

def send_smoobu_rates(api_key, api_secret, apartment_id, rates_list):
    url = 'https://login.smoobu.com/api/rates'
    
    for i in range(0, len(rates_list), 10):
        batch = rates_list[i:i+10]
        body = {
            'apartments': [int(apartment_id)],
            'operations': []
        }
        
        for r in batch:
            body['operations'].append({
                'dates': [r['date']],
                'daily_price': r['price']
            })
            
        body_json = json.dumps(body)
        
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        nonce = str(uuid.uuid4())
        
        body_hash = hashlib.sha256(body_json.encode('utf-8')).hexdigest()
        
        canonical_string = f'POST\n/api/rates\n\n{timestamp}\n{nonce}\n{body_hash}\n{api_key}'
        
        signature = base64.b64encode(
            hmac.new(
                api_secret.encode('utf-8'),
                canonical_string.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        req = urllib.request.Request(url, data=body_json.encode('utf-8'), method='POST')
        req.add_header('X-API-Key', api_key)
        req.add_header('X-Timestamp', timestamp)
        req.add_header('X-Nonce', nonce)
        req.add_header('X-Signature', signature)
        req.add_header('Content-Type', 'application/json')
        
        print(f"Invio batch (da {batch[0]['date']} a {batch[-1]['date']}) a Smoobu (Prezzi -10% - App {apartment_id})...")
        
        try:
            with urllib.request.urlopen(req) as response:
                print('Successo! Risposta:', response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print('Errore HTTP:', e.code, e.reason)
            print('Dettaglio:', e.read().decode('utf-8'))

if __name__ == '__main__':
    api_key = sys.argv[1]
    api_secret = sys.argv[2]
    apartment_id = sys.argv[3]
    start_date = sys.argv[4]
    end_date = sys.argv[5]
    
    try:
        rates = get_recommended_rates_10_percent(start_date, end_date)
        if not rates:
            print("Nessuna tariffa calcolata per questo periodo.")
            sys.exit(0)
            
        send_smoobu_rates(api_key, api_secret, apartment_id, rates)
    except Exception as e:
        import traceback
        traceback.print_exc()
