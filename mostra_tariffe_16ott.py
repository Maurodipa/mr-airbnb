import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_FILE = os.path.join(os.path.dirname(__file__), "banca_dati_airbnb_MCPserver.json")
COMP_FILE = os.path.join(os.path.dirname(__file__), "competitors.txt")

with open(DB_FILE, "r", encoding="utf-8") as f:
    db = json.load(f)

date = "2026-10-16"
if date not in db:
    print(f"Data {date} non trovata nel database.")
    sys.exit(0)

day_data = db[date]
static = db.get("static_details", {})
fees = {}
if os.path.exists(COMP_FILE):
    with open(COMP_FILE, "r", encoding="utf-8") as f:
        for line in f:
            p = line.strip().split(":")
            if len(p) >= 2:
                try:
                    fees[p[0].strip()] = float(p[1].strip())
                except ValueError:
                    pass

def parse_p(val):
    if not val:
        return 0.0
    m = re.search(r'[\d.,]+', str(val))
    if not m:
        return 0.0
    s = m.group(0)
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and len(s.split(",")[-1]) <= 2:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0

results = []
for apt_id, entry in day_data.items():
    st = static.get(apt_id, {})
    title = "N/D"
    if isinstance(st, dict):
        details = st.get("details", [])
        for d in details:
            if isinstance(d, dict) and "title" in d:
                title = d["title"]
                break
    elif isinstance(st, list):
        for d in st:
            if isinstance(d, dict) and "title" in d:
                title = d["title"]
                break

    raw = None
    min_stay = 1
    hist = []
    if isinstance(entry, dict):
        raw = entry.get("rawResponse", {})
        min_stay = entry.get("minStay", 1)
        hist = entry.get("history", [])
    elif isinstance(entry, list) and entry:
        raw = entry[-1].get("rawResponse", {})
        min_stay = entry[-1].get("minStay", 1)

    is_avail = False
    gross_price = 0.0
    net_nightly = None

    if raw:
        avail = raw.get("availability", {})
        is_avail = avail.get("isAvailable", False) if isinstance(avail, dict) else False
        spd = raw.get("structuredDisplayPrice", {})
        if spd and isinstance(spd, dict):
            prim = spd.get("primaryLine", {})
            if prim and isinstance(prim, dict):
                p_str = prim.get("discountedPrice") or prim.get("originalPrice") or prim.get("price")
                gross_price = parse_p(p_str)

    c_fee = fees.get(str(apt_id), 50.0)
    if is_avail and gross_price > 0:
        pure_tot = (gross_price / 1.1637) - c_fee
        if pure_tot > 0:
            net_nightly = pure_tot / max(1, int(min_stay))

    results.append({
        "id": apt_id,
        "title": title,
        "is_avail": is_avail,
        "min_stay": min_stay,
        "gross": gross_price,
        "c_fee": c_fee,
        "net_nightly": net_nightly,
        "history_count": len(hist),
        "history": hist
    })

avail_count = sum(1 for r in results if r["is_avail"] and r["net_nightly"])
occ_count = len(results) - avail_count

print(f"=== DETTAGLIO RILEVAZIONI PER IL 16 OTTOBRE 2026 ===")
print(f"Totale alloggi nel cluster: {len(results)}")
print(f"Liberi (con tariffa calcolata): {avail_count}")
print(f"Occupati / Non disponibili: {occ_count}")
print(f"Tasso di occupazione per il 16 ottobre: {(occ_count / len(results) * 100):.1f}%\n")

# Sort available by net nightly price ascending, then occupied
avail_results = [r for r in results if r["is_avail"] and r["net_nightly"]]
avail_results.sort(key=lambda x: x["net_nightly"])

occ_results = [r for r in results if not (r["is_avail"] and r["net_nightly"])]

print("--- ALLOGGI DISPONIBILI (Ordinati per Tariffa Netta a Notte) ---")
for i, r in enumerate(avail_results, 1):
    hist_info = f" [Rilevazioni storiche: {r['history_count']}]" if r['history_count'] > 0 else ""
    is_ours = " <--- IL TUO APPARTAMENTO" if r["id"] == "1589943047991118285" else ""
    print(f"{i:2d}. ID: {r['id']} | Netto: {r['net_nightly']:6.1f} €/nt | Lordo Airbnb: {r['gross']:6.0f} € (MinStay: {r['min_stay']} nt, Pulizie host: {r['c_fee']:.0f} €) | {r['title']}{hist_info}{is_ours}")

print("\n--- ALLOGGI OCCUPATI / NON DISPONIBILI (500m) ---")
for i, r in enumerate(occ_results, 1):
    is_ours = " <--- IL TUO APPARTAMENTO" if r["id"] == "1589943047991118285" else ""
    print(f"{i:2d}. ID: {r['id']} | OCCUPATO | {r['title']}{is_ours}")
