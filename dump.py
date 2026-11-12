import json
with open('competitors.txt') as f:
    ids = [l.split(':')[0] for l in f if l.strip()]
with open('competitori_vicini_500m_nov_10_14_details.json', encoding='utf-8') as f:
    d = json.load(f)
lines = []
for i in ids:
    for s in d.get(i, []):
        if isinstance(s, dict):
            title = s.get('section', {}).get('shareSave', {}).get('sharingConfig', {}).get('title')
            if title:
                lines.append(f"{i} -- {title}")
with open('titles.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
