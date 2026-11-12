import json
import re

with open("competitors_500m_nov_10_14.json", encoding="utf-8") as f:
    comps = json.load(f)

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details_db = json.load(f)

comps_dict = {apt["id"]: apt for apt in comps}

list_1_bed = []
list_2_beds = []
list_other = []

for apt_id, details in details_db.items():
    if not isinstance(details, list): continue

    bedrooms = -1

    for section in details:
        sharing_title = section.get("section", {}).get("shareSave", {}).get("sharingConfig", {}).get("title", "").lower()
        if sharing_title:
            # Example: "guesthouse in rome · ★4.81 · 1 bedroom · 1 bed · 1 private bath"
            match = re.search(r'(\d+)\s+bedroom', sharing_title)
            if match:
                bedrooms = int(match.group(1))
            elif "studio" in sharing_title:
                bedrooms = 1
            elif "monolocale" in sharing_title:
                bedrooms = 1
            break

    apt_info = comps_dict.get(apt_id, {})
    title = apt_info.get("title", "Sconosciuto")
    dist = apt_info.get("distance_meters", 0)

    # We only care about max 4 guests apartments from previous check, but user didn't explicitly say "out of the 63"
    # But usually "di questi appartamenti" implies the 82 total.
    apt_data = {"id": apt_id, "title": title, "dist": dist, "bedrooms": bedrooms}

    if bedrooms == 1:
        list_1_bed.append(apt_data)
    elif bedrooms == 2:
        list_2_beds.append(apt_data)
    else:
        list_other.append(apt_data)

list_1_bed.sort(key=lambda x: x["dist"])
list_2_beds.sort(key=lambda x: x["dist"])

def print_list(lst, name):
    print(f"\n=== {name} ({len(lst)} appartamenti) ===")
    for apt in lst:
        print(f"- {apt['title']} (ID: {apt['id']}) - a {apt['dist']:.1f}m")

print_list(list_1_bed, "UNA CAMERA O MONOLOCALE (1 Bedroom / Studio)")
print_list(list_2_beds, "DUE CAMERE SEPARATE (2 Bedrooms)")
print_list(list_other, "ALTRO / SCONOSCIUTO (0 o 3+ camere, oppure non specificato)")
