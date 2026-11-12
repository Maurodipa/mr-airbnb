import sys
import json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
USER_APT = '1589943047991118285'

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    page = context.pages[0]
    
    # Read all calendar day buttons
    grid_prices = {}
    buttons = page.locator('button').all()
    for b in buttons:
        txt = b.inner_text()
        if 'Prezzo giornaliero' in txt:
            # txt example: "giovedì 3 dic 3 Prezzo giornaliero 140 € selezionata"
            lines = [l.strip() for l in txt.split('\n') if l.strip()]
            grid_prices[txt] = lines

    print(f"Found {len(grid_prices)} day buttons with 'Prezzo giornaliero'")
    for k, v in list(grid_prices.items())[:20]:
        print(v)
