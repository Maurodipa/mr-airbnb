import glob
import json

for f in glob.glob('*competitor*.json'):
    try:
        with open(f, encoding='utf-8') as file:
            data = json.load(file)
            print(f"{f}: {len(data)}")
    except Exception as e:
        print(f"Error reading {f}: {e}")
