import json
import re

MY_LAT = 41.8987
MY_LNG = 12.4698

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details_db = json.load(f)

with open("competitors_500m_nov_10_14.json", encoding="utf-8") as f:
    comps = json.load(f)

comps_dict = {apt["id"]: apt for apt in comps}

competitors = []

for apt_id, details in details_db.items():
    if not isinstance(details, list): continue

    guests = -1
    bedrooms = -1

    for section in details:
        if section.get("sectionComponentType") == "STAYS_PDP_AVAILABILITY_CALENDAR_INLINE":
            guests = section.get("section", {}).get("maxGuestCapacity", -1)

        sharing_title = section.get("section", {}).get("shareSave", {}).get("sharingConfig", {}).get("title", "").lower()
        if sharing_title:
            match = re.search(r'(\d+)\s+bedroom', sharing_title)
            if match:
                bedrooms = int(match.group(1))
            elif "studio" in sharing_title or "monolocale" in sharing_title:
                bedrooms = 1

    if guests != -1 and guests <= 4 and bedrooms == 1:
        apt_info = comps_dict.get(apt_id, {})
        lat = apt_info.get("lat")
        lng = apt_info.get("lng")
        if lat and lng:
            competitors.append({
                "id": apt_id,
                "lat": lat,
                "lng": lng,
                "dist": apt_info.get("distance_meters", 0)
            })

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Mappa 54 Appartamenti (1 Camera/Monolocale, Max 4 Ospiti)</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        #map {{ height: 100vh; width: 100vw; margin: 0; padding: 0; }}
        body {{ margin: 0; padding: 0; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([{MY_LAT}, {MY_LNG}], 16);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }}).addTo(map);

        // Custom icon for user
        var redIcon = new L.Icon({{
          iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
          shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
          iconSize: [25, 41],
          iconAnchor: [12, 41],
          popupAnchor: [1, -34],
          shadowSize: [41, 41]
        }});

        L.marker([{MY_LAT}, {MY_LNG}], {{icon: redIcon}}).addTo(map)
            .bindPopup('<b>Il Tuo Appartamento</b>')
            .openPopup();

"""

for apt in competitors:
    html_content += f"""
        L.marker([{apt['lat']}, {apt['lng']}]).addTo(map)
            .bindPopup('Competitor ID: <b>{apt['id']}</b><br>Distanza: {apt['dist']:.1f}m<br>1 Camera/Monolocale');
"""

html_content += """
    </script>
</body>
</html>
"""

out_file = r"C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\mappa_competitor_54_gemelli.html"
with open(out_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Mappa salvata in {out_file} con {len(competitors)} appartamenti.")
