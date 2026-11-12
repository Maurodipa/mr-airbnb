import json
import os
import re

DATA_FILE = "banca_dati_airbnb_MCPserver.json"
OUT_FILE = "cleaning_fees_estimated.json"
FEE_MULTIPLIER = 1.1637

def parse_price(price_str: str) -> float:
    if not price_str:
        return 0.0
    # Sostituiamo i punti delle migliaia con niente, e la virgola dei decimali con il punto
    clean_str = re.sub(r'[^\d,\.]', '', price_str)
    
    # Se c'è sia punto che virgola, presumiamo che il punto sia migliaia e virgola decimali
    if '.' in clean_str and ',' in clean_str:
        clean_str = clean_str.replace('.', '').replace(',', '.')
    # Se c'è solo virgola, presumiamo siano decimali
    elif ',' in clean_str:
        clean_str = clean_str.replace(',', '.')
        
    try:
        return float(clean_str)
    except:
        return 0.0

def estimate_cleaning_fees():
    if not os.path.exists(DATA_FILE):
        return {"status": "error", "message": "Database non trovato."}

    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    points_by_apt_date = {}
    if "static_details" in data:
        for apt_id in data["static_details"]:
            points_by_apt_date[apt_id] = {}

    for date_str, apts in data.items():
        if date_str == "static_details":
            continue

        for apt_id, apt_data in apts.items():
            if apt_data.get("status") == "OK" and "rawResponse" in apt_data:
                raw = apt_data["rawResponse"]
                min_stay = apt_data.get("minStay", 1)

                # Helper function to extract net price
                def get_net_price(raw_resp):
                    lines = raw_resp.get("structuredDisplayPrice", {}).get("explanationData", {}).get("priceDetails", [])
                    t_gross = 0.0
                    t_taxes = 0.0
                    for group in lines:
                        for item in group.get("items", []):
                            desc = item.get("description", "").lower()
                            price_val = parse_price(item.get("priceString", ""))
                            if desc == "total" or "totale" in desc:
                                t_gross = price_val
                            elif "taxes" in desc or "tasse" in desc:
                                t_taxes = price_val
                    if t_gross == 0.0:
                        try:
                            primary = raw_resp.get("structuredDisplayPrice", {}).get("primaryLine", {}).get("price", "")
                            t_gross = parse_price(primary)
                        except:
                            pass
                    if t_gross > 0:
                        return (t_gross - t_taxes) / FEE_MULTIPLIER
                    return None

                net_price = get_net_price(raw)
                if net_price is not None:
                    if apt_id not in points_by_apt_date:
                        points_by_apt_date[apt_id] = {}
                    if date_str not in points_by_apt_date[apt_id]:
                        points_by_apt_date[apt_id][date_str] = []
                    points_by_apt_date[apt_id][date_str].append((min_stay, net_price))

                # Aggiungo i data point delle notti addizionali
                for extra in apt_data.get("additional_nights", []):
                    extra_net = get_net_price(extra["rawResponse"])
                    if extra_net is not None:
                        points_by_apt_date[apt_id][date_str].append((extra["minStay"], extra_net))

    results = {}

    import statistics

    for apt_id, dates_dict in points_by_apt_date.items():
        q_estimates = []
        for date_str, points in dates_dict.items():
            # Ordinare per numero di notti
            points = sorted(list(set(points)), key=lambda p: p[0])
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i+1]
                dx = x2 - x1
                dy = y2 - y1
                if dx > 0:
                    m = dy / dx
                    q = y1 - (m * x1)
                    q_estimates.append(q)

        if not q_estimates:
            results[apt_id] = 50.0 # Valore di fallback
            continue

        # Calcola la mediana
        median_q = statistics.median(q_estimates)

        # Round to nearest 5
        estimated_cleaning = max(0.0, round(median_q / 5.0) * 5.0)

        results[apt_id] = estimated_cleaning

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return {
        "status": "success",
        "message": f"Stima calcolata per {len(results)} appartamenti.",
        "file": OUT_FILE,
        "data": results
    }

if __name__ == "__main__":
    print(estimate_cleaning_fees())
