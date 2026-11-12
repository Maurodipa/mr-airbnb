import os
import re

file_path = 'banca_dati_airbnb_MCPserver.json'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We want to find the last fully complete date entry. 
# The top level keys are dates like "2026-10-15".
# Let's find all occurrences of top-level date keys.
matches = list(re.finditer(r'[\r\n]+ {0,4}"(\d{4}-\d{2}-\d{2})":\s*\{', content))

# The last one is likely the one that was being written and got corrupted.
# Let's truncate right before the last date started.
if len(matches) > 0:
    last_match = matches[-1]
    last_date = last_match.group(1)
    
    # We truncate the string before this last date key
    recovered_content = content[:last_match.start()]
    
    # Now we just need to close the JSON properly.
    # The previous date should have ended with a '},' or similar, but since we are at top level:
    # Actually, the string ends with '},' or just '}'
    recovered_content = recovered_content.rstrip().rstrip(',')
    recovered_content += '\n}'
    
    with open('banca_dati_airbnb_MCPserver.json', 'w', encoding='utf-8') as f:
        f.write(recovered_content)
    print(f"Recovered JSON by removing incomplete date {last_date} and closing.")
    
    # Test if it's valid JSON
    import json
    try:
        with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("Success! JSON is now valid. Keys:", list(data.keys())[-3:])
    except Exception as e:
        print("Still invalid:", e)
else:
    print("No date keys found.")
