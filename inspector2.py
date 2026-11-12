import json

with open('competitori_vicini_500m_nov_10_14_details.json', encoding='utf-8') as f:
    db = json.load(f)

first_apt = list(db.values())[0]
print(json.dumps(first_apt, indent=2))
