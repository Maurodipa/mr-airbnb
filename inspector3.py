import json

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    db = json.load(f)

for apt_id, details in db.items():
    if not isinstance(details, list): continue
    for section in details:
        sid = section.get("sectionId", "")
        if sid in ("TITLE_DEFAULT", "OVERVIEW_DEFAULT", "AVAILABILITY_CALENDAR_INLINE"):
            print(f"--- {sid} ---")
            print(json.dumps(section.get("section", {}), indent=2))
    break
