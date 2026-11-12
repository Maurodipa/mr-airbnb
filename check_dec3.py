import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
USER_APT = '1589943047991118285'
target_url = f'https://www.airbnb.it/multicalendar/{USER_APT}/edit-selected-dates/2026-12-03/2026-12-03'

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    page = context.pages[0] if context.pages else context.new_page()
    page.goto(target_url, wait_until='domcontentloaded')
    page.wait_for_timeout(2500)
    
    # Try to find price button or input
    inp = page.locator('#PriceInput-nightlyPrice').first
    if not inp.is_visible():
        btn = page.locator('button:has-text("Prezzo per notte")').first
        if btn.is_visible():
            btn.click()
            page.wait_for_timeout(1500)
    
    inp = page.locator('#PriceInput-nightlyPrice').first
    val = inp.input_value() if inp.is_visible() else 'NON_VISIBILE'
    print(f'HOST_CALENDAR_PRICE: {val}')
    
    # Take screenshot of the panel to be 100% sure
    page.screenshot(path='mr-airbnb/dec3_screenshot.png')
    print("Screenshot salvato in mr-airbnb/dec3_screenshot.png")
