import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    page = context.pages[0]
    
    btns = page.locator('button:has-text("Salva")').all()
    print('TOTAL SALVA BUTTONS:', len(btns))
    for i, b in enumerate(btns):
        print(f'Button {i}: visible={b.is_visible()}, enabled={b.is_enabled()}, bounding={b.bounding_box()}, text={repr(b.inner_text())}')
