import json
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

with open("dump.json", encoding="utf-8") as f:
    apt = json.load(f)

def search_dict(d, target, path=""):
    if isinstance(d, dict):
        for k, v in d.items():
            search_dict(v, target, f"{path}.{k}")
    elif isinstance(d, list):
        for i, v in enumerate(d):
            search_dict(v, target, f"{path}[{i}]")
    elif isinstance(d, str):
        if target.lower() in d.lower():
            print(f"FOUND in {path}: {d}")

print("--- Searching 'bedroom' ---")
search_dict(apt, "bedroom")
print("--- Searching 'studio' ---")
search_dict(apt, "studio")
print("--- Searching 'camera' ---")
search_dict(apt, "camera")
print("--- Searching 'bed' ---")
search_dict(apt, "bed")
