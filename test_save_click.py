import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    page = context.pages[0]
    
    save_btn = page.locator('button:has-text("Salva")').first
    if save_btn.is_enabled():
        print('Clicking Save...')
        save_btn.click()
        page.wait_for_timeout(2000)
    else:
        print('Save button not enabled!')
        
    page.screenshot(path='mr-airbnb/test_after_save.png')
    
    # Reload page or navigate to multicalendar to see if it changed
    page.goto('https://www.airbnb.it/multicalendar/1589943047991118285/edit-selected-dates/2026-12-03/2026-12-03', wait_until='domcontentloaded')
    page.wait_for_timeout(2500)
    
    inp = page.locator('#PriceInput-nightlyPrice').first
    print('Value after reload:', repr(inp.input_value()))
