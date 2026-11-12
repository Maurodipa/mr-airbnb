import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    page = context.pages[0]
    
    inp = page.locator('#PriceInput-nightlyPrice').first
    print('Current input value:', repr(inp.input_value()))
    
    # Try click and fill
    inp.click()
    page.wait_for_timeout(300)
    inp.fill("140")
    page.wait_for_timeout(500)
    
    print('Input value after fill:', repr(inp.input_value()))
    
    save_btn = page.locator('button:has-text("Salva")').first
    print('Save button visible:', save_btn.is_visible())
    print('Save button enabled:', save_btn.is_enabled())
    
    page.screenshot(path='mr-airbnb/test_fill_140.png')
