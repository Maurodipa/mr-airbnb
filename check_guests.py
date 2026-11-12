import json
import re

with open("competitors_500m_nov_10_14.json", encoding="utf-8") as f:
    comps = json.load(f)

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details_db = json.load(f)

comps_dict = {apt["id"]: apt for apt in comps}

max_4_guests = []
unknown = []

for apt_id, details in details_db.items():
    if not isinstance(details, list): continue

    guests_found = False
    for section in details:
        if section.get("id") == "POLICIES_DEFAULT":
            rules = section.get("houseRulesSections", "")
            match = re.search(r'(\d+)\s+(guests? maximum|ospiti? massim[oi])', rules, re.IGNORECASE)
            if match:
                guests_found = True
                guest_count = int(match.group(1))
                if guest_count <= 4:
                    # Get title and distance
                    apt_info = comps_dict.get(apt_id, {})
                    title = apt_info.get("title", "Sconosciuto")
                    dist = apt_info.get("distance_meters", 0)
                    max_4_guests.append({"id": apt_id, "title": title, "dist": dist, "guests": guest_count})
                break
    if not guests_found:
        unknown.append(apt_id)

max_4_guests.sort(key=lambda x: x["dist"])

print(f"Appartamenti analizzati: {len(details_db)}")
print(f"Appartamenti con max 4 ospiti: {len(max_4_guests)}")
print(f"Impossibile determinare per: {len(unknown)} appartamenti")

for apt in max_4_guests:
    print(f"- {apt['title']} (ID: {apt['id']}) - a {apt['dist']:.1f}m - Max {apt['guests']} ospiti")
