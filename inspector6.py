import json

with open("competitori_vicini_500m_nov_10_14_details.json", encoding="utf-8") as f:
    db = json.load(f)

first_apt = list(db.values())[0]

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
search_dict(first_apt, "bedroom")
print("--- Searching 'studio' ---")
search_dict(first_apt, "studio")
print("--- Searching 'camera' ---")
search_dict(first_apt, "camera")
print("--- Searching 'guest' ---")
search_dict(first_apt, "guest")
