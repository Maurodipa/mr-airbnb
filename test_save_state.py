import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
USER_APT = '1589943047991118285'
target_url = f'https://www.airbnb.it/multicalendar/{USER_APT}/edit-selected-dates/2026-12-04/2026-12-04'

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    page = context.pages[0]
    page.goto(target_url, wait_until='domcontentloaded')
    page.wait_for_timeout(1500)
    
    price_btn = page.locator('button:has-text("Prezzo per notte")').first
    if price_btn.is_visible():
        price_btn.click()
        page.wait_for_timeout(600)
        
    inp = page.locator('#PriceInput-nightlyPrice').first
    print('Initial input val:', repr(inp.input_value()))
    
    save_btn = page.locator('button:has-text("Salva")').first
    print('Save enabled before fill:', save_btn.is_enabled())
    
    inp.fill('140')
    print('Save enabled immediately after fill:', save_btn.is_enabled())
    page.wait_for_timeout(300)
    print('Save enabled after 300ms:', save_btn.is_enabled())
    
    # What if we click save?
    if save_btn.is_enabled():
        save_btn.click()
        print('Clicked save!')
        page.wait_for_timeout(1500)
        page.screenshot(path='mr-airbnb/dec4_after_save.png')
