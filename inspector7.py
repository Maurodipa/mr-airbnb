import json

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details_db = json.load(f)

first_apt = list(details_db.values())[0]

for section in first_apt:
    print(f"{section.get('sectionComponentType')} / {section.get('sectionId')}")
