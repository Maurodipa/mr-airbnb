import json

with open('competitori_vicini_500m_nov_10_14_details.json', encoding='utf-8') as f:
    db = json.load(f)
count = 0
for apt_id, details in db.items():
    if not isinstance(details, list): continue
    for section in details:
        if section.get('id') == 'POLICIES_DEFAULT':
            print(f'RULES for {apt_id}: {section.get("houseRulesSections", "")}')
            count += 1
    if count >= 3: break
