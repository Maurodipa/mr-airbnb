import json
import re

import folium

MY_LAT = 41.8987
MY_LNG = 12.4698

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details_db = json.load(f)

with open("competitors_500m_nov_10_14.json", encoding="utf-8") as f:
    comps = json.load(f)

comps_dict = {apt["id"]: apt for apt in comps}

competitors_2_beds = []

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

    if guests != -1 and guests <= 4 and bedrooms == 2:
        apt_info = comps_dict.get(apt_id, {})
        lat = apt_info.get("lat")
        lng = apt_info.get("lng")
        if lat and lng:
            competitors_2_beds.append({
                "id": apt_id,
                "lat": lat,
                "lng": lng,
                "dist": apt_info.get("distance_meters", 0)
            })

# Create the map
m = folium.Map(location=[MY_LAT, MY_LNG], zoom_start=16)

# Add the user's apartment
folium.Marker(
    [MY_LAT, MY_LNG],
    popup="Il Tuo Appartamento",
    tooltip="Tuo Appartamento",
    icon=folium.Icon(color="red", icon="star")
).add_to(m)

# Add the competitors
for apt in competitors_2_beds:
    folium.Marker(
        [apt["lat"], apt["lng"]],
        popup=f"Competitor ID: {apt['id']}<br>Distanza: {apt['dist']:.1f}m",
        tooltip=f"Competitor (2 Camere) - {apt['dist']:.1f}m",
        icon=folium.Icon(color="blue", icon="home")
    ).add_to(m)

out_file = r"C:\Users\mauro\.gemini\antigravity\brain\b63ef745-8fc3-4ec8-a1a4-9341f241e9c5\mappa_2_camere.html"
m.save(out_file)
print(f"Mappa salvata in {out_file}")
