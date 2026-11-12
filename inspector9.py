import json

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    details = json.load(f)
apt = list(details.values())[0]
with open("dump.json", "w", encoding="utf-8") as out:
    json.dump(apt, out, indent=2)
