import json

with open('competitori_vicini_500m_nov_10_14_details.json', encoding='utf-8') as f:
    data = json.load(f)

gemelli = []
for apt_id, apt in data.items():
    room_type = apt.get('roomType')
    beds = apt.get('beds')
    capacity = apt.get('personCapacity', 2)
    # the user defined "gemelli" as 52 apartments
    # Usually it's Entire home/apt, 1 bed, capacity 2 or similar
    if room_type == 'Entire home/apt' and beds == 1:
        gemelli.append(apt_id)

print(f"Trovati {len(gemelli)} appartamenti gemelli!")

with open('competitors.txt', 'w', encoding='utf-8') as f:
    for apt_id in gemelli:
        f.write(f"{apt_id}:50:Gemello_{apt_id}\n")
