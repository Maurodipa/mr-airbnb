import json

titles_map = {}
with open('titles.txt', encoding='utf-8') as f:
    for line in f:
        parts = line.strip().split(' -- ')
        if len(parts) >= 2:
            apt_id = parts[0].strip()
            raw_desc = parts[1].strip()
            # Clean up raw_desc to get a short unique name
            # e.g. "Rental unit in Rome · ★4.96 · 1 bedroom · 2 beds · 1 bath" -> "Rental unit (★4.96)"
            desc_parts = raw_desc.split(' · ')
            type_str = desc_parts[0].replace(' in Rome', '') if len(desc_parts) > 0 else 'Gemello'
            rating_str = desc_parts[1] if len(desc_parts) > 1 else ''
            
            unique_name = f"Gemello {apt_id[-4:]} ({type_str} {rating_str})".strip()
            titles_map[apt_id] = unique_name

print("Total unique titles created:", len(titles_map))
for k, v in list(titles_map.items())[:10]:
    print(k, "->", v)
