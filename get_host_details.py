import json
import re

with open('banca_dati_airbnb_MCPserver.json', encoding='utf-8') as f:
    db = json.load(f)

for i in ['1401938376529553958', '5791838', '972140881572377308', '974327786872931594', '1045445565885243855']:
    s = json.dumps(db.get('static_details', {}).get(i, {}))
    
    # Try to find user IDs or host names
    host_ids = re.findall(r'"hostId"\s*:\s*"?(\d+)"?', s)
    user_ids = re.findall(r'"userId"\s*:\s*"?(\d+)"?', s)
    
    names = re.findall(r'"hostName"\s*:\s*"([^"]+)"', s)
    names2 = re.findall(r'"smartName"\s*:\s*"([^"]+)"', s)
    
    print(f'ID {i}:')
    print(f'  Host IDs: {set(host_ids)}')
    print(f'  User IDs: {set(user_ids)}')
    print(f'  Names: {set(names)}')
    print(f'  Smart Names: {set(names2)}')
