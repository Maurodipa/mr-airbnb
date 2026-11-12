import json

with open("competitors_500m_nov_10_14.json", encoding="utf-8") as f:
    comps = json.load(f)

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details_db = json.load(f)

comps_dict = {apt["id"]: apt for apt in comps}

max_4_guests = []
unknown = []

for apt_id, details in details_db.items():
    if not isinstance(details, list): continue

    guests = None
    for section in details:
        if section.get("sectionComponentType") == "STAYS_PDP_AVAILABILITY_CALENDAR_INLINE":
            sec_data = section.get("section", {})
            if "maxGuestCapacity" in sec_data:
                guests = sec_data["maxGuestCapacity"]
                break

    if guests is not None:
        if guests <= 4:
            apt_info = comps_dict.get(apt_id, {})
            title = apt_info.get("title", "Sconosciuto")
            dist = apt_info.get("distance_meters", 0)
            price = apt_info.get("price", "N/A")
            max_4_guests.append({"id": apt_id, "title": title, "dist": dist, "guests": guests, "price": price})
    else:
        unknown.append(apt_id)

max_4_guests.sort(key=lambda x: x["dist"])

print(f"Appartamenti analizzati: {len(details_db)}")
print(f"Appartamenti con MAX 4 ospiti: {len(max_4_guests)}")
print(f"Impossibile determinare per: {len(unknown)} appartamenti")
print("\nElenco appartamenti (ordinati per vicinanza):")

for apt in max_4_guests:
    print(f"- {apt['title']} (ID: {apt['id']}) - a {apt['dist']:.1f}m - Max {apt['guests']} ospiti")
