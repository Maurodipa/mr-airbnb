import json

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details_db = json.load(f)

for apt_id, details in details_db.items():
    if not isinstance(details, list): continue
    for section in details:
        if section.get("sectionId") == "OVERVIEW_DEFAULT_V2":
            print(f"ID {apt_id}: {json.dumps(section, indent=2)}")
    break
