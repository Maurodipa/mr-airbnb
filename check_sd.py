import json

db = json.load(open('banca_dati_airbnb.json', encoding='utf-8'))
sd = db.get('static_details', {})
print("banca_dati_airbnb.json static_details count:", len(sd))
for k, v in list(sd.items())[:3]:
    print(k, "-->", v)
