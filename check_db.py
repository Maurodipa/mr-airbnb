import json
import math

MY_LAT = 41.8987
MY_LNG = 12.4698

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def extract_coords(obj):
    if isinstance(obj, dict):
        if 'latitude' in obj and 'longitude' in obj:
            return obj['latitude'], obj['longitude']
        if 'lat' in obj and 'lng' in obj:
            return obj['lat'], obj['lng']
        for v in obj.values():
            res = extract_coords(v)
            if res: return res
    elif isinstance(obj, list):
        for item in obj:
            res = extract_coords(item)
            if res: return res
    return None

for f_name in ['banca_dati_airbnb.json', 'banca_dati_airbnb_MCPserver.json']:
    print(f"\nAnalizzo {f_name}...")
    try:
        with open(f_name, encoding='utf-8') as f:
            data = json.load(f)

            # Extract apartments depending on structure
            apts = []
            if isinstance(data, list):
                apts = data
            elif isinstance(data, dict):
                # If keys are apt_ids?
                if all(k.isdigit() for k in data.keys() if k != 'static_details'):
                    apts = list(data.values())
                else:
                    # Maybe it's a calendar structure, not an apartment list
                    print(f"La struttura di {f_name} non sembra un DB di appartamenti.")
                    continue

            print(f"Trovati {len(apts)} elementi in {f_name}.")
            for comp in apts:
                if not isinstance(comp, dict): continue
                apt_id = comp.get('id', 'sconosciuto')
                coords = extract_coords(comp)
                if coords:
                    dist = haversine(MY_LAT, MY_LNG, coords[0], coords[1])
                    print(f"  Appartamento {apt_id}: {dist:.1f} metri")
                else:
                    print(f"  Appartamento {apt_id}: coordinate non trovate")
    except Exception as e:
        print(f"Errore su {f_name}: {e}")
