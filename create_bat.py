import json, os

with open('banca_dati_airbnb_MCPserver_cleaned.json', 'r', encoding='utf-8') as f:
    cleaned = json.load(f)

my_id = '1084143873171633493'
all_ids = set()
for v in cleaned.values():
    all_ids.update(v.keys())

ids = [my_id] + [i for i in sorted(all_ids) if i != my_id]
urls = [f'https://www.airbnb.it/rooms/{i}' for i in ids]

bat_path = 'Apri_51_Competitors.bat'

with open(bat_path, 'w') as f:
    f.write('@echo off\n')
    f.write('echo Sto aprendo 51 schede in Chrome...\n')
    f.write(f'start chrome --new-window \"{urls[0]}\"\n')
    f.write('timeout /t 2 /nobreak >nul\n')
    for u in urls[1:]:
        f.write(f'start chrome \"{u}\"\n')

print(f'Script creato in: {os.path.abspath(bat_path)}')
