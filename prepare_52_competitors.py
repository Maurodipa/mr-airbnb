import json
import re

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details_db = json.load(f)

ids_54 = []

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
        ids_54.append(apt_id)

out_file = "competitors.txt"
with open(out_file, "w") as f:
    for aid in ids_54:
        f.write(f"{aid}:50:Gemello\n")

print(f"Salvato {len(ids_54)} IDs in {out_file}")
