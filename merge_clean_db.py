import json

# 1. Load summer data (Aug 1 - Sept 15)
with open('banca_dati_airbnb_MCPserver_cleaned_BACKUP.json', 'r', encoding='utf-8') as f:
    summer_data = json.load(f)

# 2. Load autumn data (Sept 16 - Nov 30)
with open('banca_dati_airbnb_MCPserver_cleaned.json', 'r', encoding='utf-8') as f:
    autumn_data = json.load(f)

# 3. Merge them. The keys are dates like "2026-08-01".
merged_data = {}
merged_data.update(summer_data)
merged_data.update(autumn_data)

# 4. Save the unified database
with open('banca_dati_airbnb_MCPserver_cleaned_UNIFIED.json', 'w', encoding='utf-8') as f:
    json.dump(merged_data, f, indent=2)

# Verify
dates = sorted(list(merged_data.keys()))
print(f"Merge completato! Trovate {len(dates)} date univoche.")
print(f"Inizio: {dates[0]} - Fine: {dates[-1]}")
