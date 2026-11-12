import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details_db = json.load(f)

print("Analisi dei 10 appartamenti 'ALTRO':")

count = 0
for apt_id, details in details_db.items():
    if not isinstance(details, list): continue

    bedrooms = -1
    sharing_title = ""
    guests = -1

    for section in details:
        if section.get("sectionComponentType") == "STAYS_PDP_AVAILABILITY_CALENDAR_INLINE":
            guests = section.get("section", {}).get("maxGuestCapacity", -1)

        stitle = section.get("section", {}).get("shareSave", {}).get("sharingConfig", {}).get("title", "").lower()
        if stitle:
            sharing_title = stitle
            match = re.search(r'(\d+)\s+bedroom', stitle)
            if match:
                bedrooms = int(match.group(1))
            elif "studio" in stitle or "monolocale" in stitle:
                bedrooms = 1

    if bedrooms not in (1, 2):
        print(f"\nID: {apt_id}")
        print(f"Titolo Share: '{sharing_title}'")
        print(f"Max Ospiti: {guests}")
        count += 1

print(f"\nTotale: {count}")
