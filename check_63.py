import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details_db = json.load(f)

count_1_bed = 0
count_2_bed = 0
count_other = 0

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

    if guests != -1 and guests <= 4:
        if bedrooms == 1:
            count_1_bed += 1
        elif bedrooms == 2:
            count_2_bed += 1
        else:
            count_other += 1

print("Su 63 appartamenti (Max 4 Ospiti):")
print(f"- 1 camera o monolocale: {count_1_bed}")
print(f"- 2 camere separate: {count_2_bed}")
print(f"- Altro: {count_other}")
