import json

historic_competitors = {}
with open("competitors.txt", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("1589943047991118285"):
            continue
        parts = line.split(":")
        if len(parts) >= 3:
            historic_competitors[parts[0]] = parts[2]

with open("competitors_500m_nov_10_14.json", encoding="utf-8") as f:
    new_competitors = json.load(f)

print(f"Appartamenti totali trovati (10-14 Nov): {len(new_competitors)}")

new_ids = {apt["id"]: apt for apt in new_competitors}

intersection = []
for hist_id, name in historic_competitors.items():
    if hist_id in new_ids:
        intersection.append((name, hist_id, new_ids[hist_id]["distance_meters"]))

print(f"Competitors storici trovati in questa ricerca: {len(intersection)}")
for name, apt_id, dist in intersection:
    print(f"- {name} ({apt_id}) a {dist:.1f} metri")
