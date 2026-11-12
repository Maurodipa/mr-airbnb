import json
import math
import os

DATA_FILE = "banca_dati_airbnb_MCPserver.json"
MY_APT_ID = "1589943047991118285"
RADIUS_METERS = 100.0

def haversine(lat1, lon1, lat2, lon2):
    # Raggio della Terra in metri
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    meters = R * c
    return meters

def find_close_competitors():
    if not os.path.exists(DATA_FILE):
        print("Database non trovato.")
        return

    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    static = data.get("static_details", {})
    if MY_APT_ID not in static:
        print(f"I dettagli del tuo appartamento ({MY_APT_ID}) non sono nel database.")
        return

    def extract_coords(obj):
        if isinstance(obj, dict):
            if "lat" in obj and "lng" in obj:
                return obj["lat"], obj["lng"]
            for v in obj.values():
                res = extract_coords(v)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = extract_coords(item)
                if res:
                    return res
        return None

    my_coords = extract_coords(static[MY_APT_ID])
    if not my_coords:
        print("Coordinate del tuo appartamento non trovate.")
        return

    my_lat, my_lng = my_coords

    print(f"Le tue coordinate: {my_lat}, {my_lng}")
    print(f"Cerco competitor entro {RADIUS_METERS} metri...\n")

    close_apts = []

    def extract_title(obj):
        if isinstance(obj, dict):
            if "title" in obj and isinstance(obj["title"], str) and len(obj["title"]) > 3:
                return obj["title"]
            for v in obj.values():
                res = extract_title(v)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = extract_title(item)
                if res:
                    return res
        return None

    for apt_id, details in static.items():
        if apt_id == MY_APT_ID:
            continue

        coords = extract_coords(details)
        if coords:
            lat, lng = coords
            dist = haversine(my_lat, my_lng, lat, lng)
            if dist <= RADIUS_METERS:
                close_apts.append({
                    "id": apt_id,
                    "distance": dist,
                    "title": extract_title(details) or "Titolo sconosciuto"
                })

    # Ordina per distanza crescente
    close_apts.sort(key=lambda x: x["distance"])

    if not close_apts:
        print("Nessun competitor trovato entro il raggio indicato.")
    else:
        for apt in close_apts:
            print(f"- {apt['id']}: {apt['distance']:.1f} metri di distanza. ({apt['title']})")

if __name__ == "__main__":
    find_close_competitors()
