import json
import os

DB_PATH = "banca_dati_airbnb.json"

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return
        
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    updated = 0
    for date, apts in data.items():
        for apt_id, entry in apts.items():
            if entry.get("status") == "OK" and "collected_at" not in entry:
                entry["collected_at"] = "2026-06-20T00:00:00"
                updated += 1
                
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    print(f"Migration completed. Updated {updated} records.")

if __name__ == "__main__":
    migrate()
