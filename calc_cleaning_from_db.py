import json
from app.market_scanner import parse_price

def get_gross_and_taxes(raw_response):
    total_gross = 0.0
    taxes = 0.0
    structured_price = raw_response.get("structuredDisplayPrice") or {}
    explanation_data = structured_price.get("explanationData") or {}
    price_details = explanation_data.get("priceDetails") or []
    
    for group in price_details:
        for item in group.get('items', []):
            desc = item.get('description', '')
            if desc in ('Taxes', 'Tasse'):
                taxes = parse_price(item['priceString'])
            if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                total_gross = parse_price(item['priceString'])
                
    return total_gross - taxes

def extract_fee(entry):
    if entry.get("status") != "OK" or not entry.get("rawResponse"):
        return None
    
    additional = entry.get("additional_nights", [])
    if not additional:
        return None
        
    min_stay = entry.get("minStay", 1)
    t1 = get_gross_and_taxes(entry["rawResponse"])
    
    # Prendi la prima notte aggiuntiva (N+1)
    next_night = additional[0]
    # Assicuriamoci che sia effettivamente N+1
    if next_night.get("minStay") == min_stay + 1:
        t2 = get_gross_and_taxes(next_night["rawResponse"])
        if t2 > 0 and t1 > 0:
            R = (t2 - t1) / 1.1637
            C = (t1 / 1.1637) - (min_stay * R)
            return max(0, round(C))
            
    return None

def main():
    with open('banca_dati_airbnb_MCPserver.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
        
    with open('competitors.txt', 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
        
    dates_to_test = [f"2026-08-{str(i).zfill(2)}" for i in range(1, 19)]
    new_lines = []
    
    print("Estrazione spese di pulizia dal database locale...")
    
    for line in lines:
        if not line.strip(): continue
        parts = line.split(':')
        apt_id = parts[0]
        current_fee = parts[1]
        name = parts[2] if len(parts) > 2 else "Gemello"
        
        found_fee = None
        for date_str in dates_to_test:
            if date_str in db and apt_id in db[date_str]:
                fee = extract_fee(db[date_str][apt_id])
                if fee is not None:
                    found_fee = fee
                    break
                    
        if found_fee is not None:
            print(f"{apt_id} -> Trovata: {found_fee} EUR (prima era {current_fee})")
            new_lines.append(f"{apt_id}:{int(found_fee)}:{name}")
        else:
            print(f"{apt_id} -> Nessun dato 'additional_nights' nei 4 giorni. Mantengo: {current_fee} EUR")
            new_lines.append(line)
            
    with open('competitors.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines) + '\n')
    print("File competitors.txt aggiornato con i dati estratti dal DB!")

if __name__ == "__main__":
    main()
