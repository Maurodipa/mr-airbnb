import re

file_path = 'banca_dati_airbnb_MCPserver.json'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Look for exactly newline, two spaces, quote, 2026-, then month and day, quote, colon, space, brace
matches = list(re.finditer(r'\n  "2026-\d{2}-\d{2}": \{', content))
print(f"Found {len(matches)} date keys using \\n")

if len(matches) == 0:
    matches = list(re.finditer(r'\r\n  "2026-\d{2}-\d{2}": \{', content))
    print(f"Found {len(matches)} date keys using \\r\\n")

if len(matches) > 0:
    last_match = matches[-1]
    # The date is characters 4 to 14 of the matched string e.g. "2026-09-16"
    print("Last match string:", repr(last_match.group(0)))
    
    # Truncate
    recovered_content = content[:last_match.start()]
    recovered_content = recovered_content.rstrip().rstrip(',')
    recovered_content += '\n}'
    
    with open('banca_dati_airbnb_MCPserver_recovered.json', 'w', encoding='utf-8') as f:
        f.write(recovered_content)
    print("Wrote to banca_dati_airbnb_MCPserver_recovered.json")
    
    import json
    try:
        with open('banca_dati_airbnb_MCPserver_recovered.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("Success! Keys:", list(data.keys())[-3:])
    except Exception as e:
        print("Still invalid:", e)
