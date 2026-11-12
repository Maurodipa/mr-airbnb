import json

with open("competitori_vicini_500m_nov_10_14_details.json", "r", encoding="utf-8") as f:
    details_db = json.load(f)

with open("competitors.txt", "r", encoding="utf-8") as f:
    ids_54 = [line.strip().split(':')[0] for line in f if line.strip()]

ids_52 = []
private_rooms = []

for apt_id in ids_54:
    details = details_db.get(apt_id, [])
    if not isinstance(details, list): continue
    
    is_private_room = False
    for section in details:
        sharing_title = section.get("section", {}).get("shareSave", {}).get("sharingConfig", {}).get("title", "").lower()
        if sharing_title:
            if "private room" in sharing_title or "camera privata" in sharing_title or "stanza privata" in sharing_title:
                is_private_room = True
                break
                
    if not is_private_room:
        ids_52.append(apt_id)
    else:
        private_rooms.append(apt_id)

print(f"Rimossi {len(private_rooms)} appartamenti perché sono stanze private: {private_rooms}")

with open("competitors.txt", "w", encoding="utf-8") as f:
    for aid in ids_52:
        f.write(f"{aid}:50:Gemello\n")

print(f"Salvato {len(ids_52)} IDs in competitors.txt")
