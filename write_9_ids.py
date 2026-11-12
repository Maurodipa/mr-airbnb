import json
import re

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details_db = json.load(f)

ids_2bed = []

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
        ids_2bed.append(apt_id)

out_file = r"C:\Docs\Personnel et confidentiel\Corsi e Formazioni\2026-06-14 Kaggle_5-Day AI Agents\agy2-projects\my-first-project\.agents\skills\market-scanner\competitors.txt"
with open(out_file, "w") as f:
    for aid in ids_2bed:
        f.write(aid + "\n")

print(f"Salvato {len(ids_2bed)} IDs in {out_file}")
