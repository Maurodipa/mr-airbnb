import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    page = context.pages[0]
    
    btn = page.locator('button:has-text("Prezzo per notte")').first
    if btn.is_visible():
        print('BUTTON TEXT:', repr(btn.inner_text()))
        btn.click()
        page.wait_for_timeout(1000)
    else:
        print('Button not visible!')
        
    page.screenshot(path='mr-airbnb/after_click_price.png')
    print('INPUTS AFTER CLICK:', [(i.get_attribute('id'), i.get_attribute('value'), i.is_visible()) for i in page.locator('input').all()])
    print('BUTTONS AFTER CLICK:', [b.inner_text().replace('\n', ' ') for b in page.locator('button').all() if b.is_visible() and ('Salva' in b.inner_text() or 'Prezzo' in b.inner_text())])
