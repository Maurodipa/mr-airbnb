import json

with open('competitors_500m_nov.json', encoding='utf-8') as f:
    data = json.load(f)
print(f'Trovati {len(data)} appartamenti!')
for apt in data[:10]:
    price = apt.get('price', 'Sconosciuto')
    print(f'ID {apt["id"]} a {apt["distance_meters"]:.1f}m - Prezzo: {price}')
