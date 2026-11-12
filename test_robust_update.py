import sys
import re
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
USER_APT = '1589943047991118285'
target_url = f'https://www.airbnb.it/multicalendar/{USER_APT}/edit-selected-dates/2026-12-04/2026-12-04'

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    page = context.pages[0]
    
    print("Navigazione a 2026-12-04...")
    page.goto(target_url, wait_until='domcontentloaded')
    
    # Aspetta il pannello laterale
    page.wait_for_timeout(1500)
    
    # 1. Trova il bottone Prezzo per notte
    price_btn = page.locator('button:has-text("Prezzo per notte")').first
    price_btn.wait_for(state="visible", timeout=6000)
    btn_text = price_btn.inner_text()
    print("Testo bottone prezzo:", repr(btn_text.replace('\n', ' ')))
    
    m = re.search(r'(\d+)\s*€', btn_text)
    old_price = int(m.group(1)) if m else None
    print(f"Tariffa precedente estratta: {old_price} €")
    
    # 2. Clicca per aprire il sub-pane
    price_btn.click()
    page.wait_for_timeout(600)
    
    # 3. Input del prezzo
    inp = page.locator('#PriceInput-nightlyPrice').first
    inp.wait_for(state="visible", timeout=4000)
    print("Valore input prima di modifica:", inp.input_value())
    
    # 4. Modifica a 140
    target_price = 140
    inp.click()
    inp.fill(str(target_price))
    page.wait_for_timeout(300)
    
    # 5. Salva
    save_btn = page.locator('button:has-text("Salva")').first
    print("Salva abilitato:", save_btn.is_enabled())
    if save_btn.is_enabled():
        save_btn.click()
        print("Cliccato Salva!")
        
        # Aspetta toast o chiusura sub-pane
        try:
            toast = page.locator('text="Prezzo a notte aggiornato"').first
            toast.wait_for(state="visible", timeout=4000)
            print("✅ Toast confermato: Prezzo a notte aggiornato!")
        except Exception:
            print("Toast non intercettato, ma proseguito.")
            page.wait_for_timeout(1000)
            
    # 6. Chiudi il pannello per pulizia
    close_btn = page.locator('button[aria-label="Chiudi"]').first
    if close_btn.is_visible():
        close_btn.click()
        page.wait_for_timeout(500)
        print("Pannello laterale chiuso.")

    # 7. Verifica sulla griglia
    for b in page.locator('button').all():
        txt = b.inner_text()
        if '4 dic' in txt and 'Prezzo giornaliero' in txt:
            print("RISULTATO A CALENDARIO:", repr(txt.replace('\n', ' ')))
