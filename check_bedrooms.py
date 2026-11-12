import json

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
        if section.get("sectionComponentType") == "STAYS_PDP_AVAILABILITY_CALENDAR_INLINE":
            desc_items = section.get("section", {}).get("descriptionItems", [])
            for item in desc_items:
                title = item.get("title", "").lower()
                if "bedroom" in title or "camera" in title:
                    try:
                        bedrooms = int(title.split(" ")[0])
                    except:
                        pass
                elif "studio" in title or "monolocale" in title:
                    bedrooms = 1
                elif "private room" in title or "stanza privata" in title:
                    bedrooms = 1

    apt_info = comps_dict.get(apt_id, {})
    title = apt_info.get("title", "Sconosciuto")
    dist = apt_info.get("distance_meters", 0)
    price = apt_info.get("price", "N/A")
    apt_data = {"id": apt_id, "title": title, "dist": dist, "bedrooms": bedrooms, "price": price}

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
        print(f"- {apt['title']} (ID: {apt['id']}) - a {apt['dist']:.1f}m - Camere: {apt['bedrooms']}")

print_list(list_1_bed, "UNA CAMERA O MONOLOCALE")
print_list(list_2_beds, "DUE CAMERE SEPARATE")
print_list(list_other, "ALTRO / NON DETERMINATO")
