import json
from app.market_scanner import parse_price

with open('banca_dati_airbnb_MCPserver.json', encoding='utf-8') as f:
    db = json.load(f)
entry = db['2026-08-11']['1401938376529553958']

def get_gross_and_taxes(raw_response):
    total_gross = 0.0
    taxes = 0.0
    structured_price = raw_response.get("structuredDisplayPrice") or {}
    explanation_data = structured_price.get("explanationData") or {}
    price_details = explanation_data.get("priceDetails") or []
    for group in price_details:
        for item in group.get('items', []):
            desc = item.get('description', '')
            if desc in ('Taxes', 'Tasse'): taxes = parse_price(item['priceString'])
            if (item.get('__typename') == 'HighlightExplanationLineItem' and desc in ('Total', 'Totale')) or desc == 'Total':
                total_gross = parse_price(item['priceString'])
    return total_gross, taxes

t1_gross, t1_taxes = get_gross_and_taxes(entry['rawResponse'])
t1_net = t1_gross - t1_taxes

t2_gross, t2_taxes = get_gross_and_taxes(entry['additional_nights'][0]['rawResponse'])
t2_net = t2_gross - t2_taxes

print(f"1 Notte: Lordo {t1_gross}, Tasse {t1_taxes} -> Netto Airbnb {t1_net}")
print(f"2 Notti: Lordo {t2_gross}, Tasse {t2_taxes} -> Netto Airbnb {t2_net}")

R = (t2_net - t1_net) / 1.1637
C = (t1_net / 1.1637) - R

print(f"R (Tariffa marginale pura per notte) = ({t2_net} - {t1_net}) / 1.1637 = {R}")
print(f"C (Spese di pulizia) = ({t1_net} / 1.1637) - {R} = {C}")
print(f"Arrotondato: {round(C)}")
