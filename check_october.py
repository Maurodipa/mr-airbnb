import json

DATA_FILE = "banca_dati_airbnb_MCPserver.json"
CLEANING_FILE = "cleaning_fees_estimated.json"
MY_APT = "1589943047991118285"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

with open(CLEANING_FILE, "r", encoding="utf-8") as f:
    cleaning_fees = json.load(f)

def get_net_rate(entry, apt_id):
    if isinstance(entry, list) and entry:
        entry = entry[-1]
    if not isinstance(entry, dict): return None
    raw = entry.get("rawResponse", {})
    avail = raw.get("availability", {})
    if isinstance(avail, dict) and not avail.get("isAvailable", True): return None
    
    spd = raw.get("structuredDisplayPrice", {})
    primary = spd.get("primaryLine", {})
    raw_price_str = primary.get("discountedPrice") or primary.get("originalPrice") or primary.get("price")
    if not raw_price_str: return None
    
    import re
    clean_str = re.sub(r'[^\d,\.]', '', raw_price_str)
    if '.' in clean_str and ',' in clean_str:
        clean_str = clean_str.replace('.', '').replace(',', '.')
    elif ',' in clean_str:
        clean_str = clean_str.replace(',', '.')
    try:
        tot = float(clean_str)
    except:
        return None
        
    c_fee = float(cleaning_fees.get(str(apt_id), 50.0))
    pure_tot = (tot / 1.1637) - c_fee
    
    min_stay = entry.get("minStay", 1)
    if isinstance(min_stay, str) and min_stay.isdigit(): min_stay = int(min_stay)
    if not isinstance(min_stay, int) or min_stay <= 0: min_stay = 1
        
    if pure_tot > 0:
        return pure_tot / min_stay
    return None

oct_dates = sorted([d for d in data.keys() if d.startswith("2026-10") and d != "static_details"])

for d in oct_dates:
    my_entry = data[d].get(MY_APT)
    if not my_entry: continue
    my_net = get_net_rate(my_entry, MY_APT)
    if my_net is not None:
        print(f"\n=== DATA: {d} ===")
        my_c_fee_net = float(cleaning_fees.get(MY_APT, 50.0))
        my_cal_rate = (my_net + (my_c_fee_net * 0.1891)) / 0.8109
        print(f"Il tuo appartamento è LIBERO. (Tua Tariffa Calendario dedotta: {my_cal_rate:.2f} €)")
        print("Competitor liberi:")
        comps = []
        for apt_id, entry in data[d].items():
            if apt_id == MY_APT: continue
            net_rate = get_net_rate(entry, apt_id)
            if net_rate is not None:
                c_fee_net = float(cleaning_fees.get(apt_id, 50.0))
                cal_rate = (net_rate + (c_fee_net * 0.1891)) / 0.8109
                link = f"https://www.airbnb.it/rooms/{apt_id}"
                comps.append((apt_id, cal_rate, link))
        
        if comps:
            comps.sort(key=lambda x: x[1])
            for apt_id, cal_rate, link in comps:
                print(f"- ID {apt_id}: {cal_rate:.2f} € (Link: {link})")
        else:
            print("Nessun competitor disponibile in questa data!")
