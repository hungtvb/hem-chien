"""Cold-start asset gate E2E — verify old sprite never shown or playable before new atlas loads."""
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE='https://hem-chien-test.local/'
TYPES={'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.webp':'image/webp'}
def run_test(browser,fail_one=False):
    page=browser.new_page(viewport={'width':1440,'height':950})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    def handler(route):
        name=urlparse(route.request.url).path.lstrip('/') or 'index.html'
        if fail_one and name=='assets/sprites/artist/minh-overlay.png':
            route.fulfill(status=503,body='test asset failure');return
        file=ROOT/name
        if not file.is_file():route.fulfill(status=404,body='missing '+name);return
        route.fulfill(status=200,content_type=TYPES.get(file.suffix,'application/octet-stream'),path=str(file))
    page.route('https://hem-chien-test.local/**',handler)
    page.goto(BASE,wait_until='domcontentloaded')
    page.wait_for_function('typeof window.__combatDebug === "function"')
    if fail_one:
        page.wait_for_function("document.getElementById('assetStatus').dataset.state==='error'")
        assert page.locator('#startBtn').is_disabled()
        page.keyboard.press('Enter')
        assert page.evaluate('window.__gameDebug().state')=='menu'
        assert page.locator('#assetRetry').is_visible()
        print('FAILURE CASE PASS — no silent fallback; retry shown')
    else:
        page.wait_for_function('window.__combatDebug().latestArtReady',timeout=30000)
        assert page.locator('#startBtn').is_enabled()
        assert page.locator('#assetStatus').get_attribute('data-state')=='ready'
        page.locator('#startBtn').click()
        assert page.evaluate('window.__gameDebug().state')=='fight'
        print('SUCCESS CASE PASS — newest sprite available before fight')
    assert not errors,errors
    page.close()
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    run_test(browser,True)
    run_test(browser,False)
    browser.close()
