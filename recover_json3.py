import re

file_path = 'banca_dati_airbnb_MCPserver.json'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Total lines:", len(lines))
date_keys = []
for i, line in enumerate(lines):
    if '"2026-' in line and '{' in line:
        date_keys.append((i, line))

print(f"Found {len(date_keys)} lines matching '2026-' and '{{'")
if date_keys:
    print("First match:", date_keys[0])
    print("Last match:", date_keys[-1])

    # Truncate to just before the last date match
    last_idx = date_keys[-1][0]
    # Keep lines up to last_idx - 1
    # Actually, we need to see how the previous block ended.
    # Usually the previous block ends with "  },"
    
    recovered_lines = lines[:last_idx]
    
    # We must ensure it ends with }
    # So we join, strip, strip comma, add \n}
    recovered_content = "".join(recovered_lines).rstrip().rstrip(',')
    recovered_content += '\n}'
    
    with open('banca_dati_airbnb_MCPserver_recovered.json', 'w', encoding='utf-8') as f:
        f.write(recovered_content)
    
    import json
    try:
        with open('banca_dati_airbnb_MCPserver_recovered.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("Success! Keys:", list(data.keys())[-3:])
    except Exception as e:
        print("Still invalid:", e)
