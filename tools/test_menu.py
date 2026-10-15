"""Menu visual and interaction smoke using in-memory routed static site."""
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
URL="https://hem-chien-ui.test/"
types={".html":"text/html",".css":"text/css",".js":"application/javascript",".png":"image/png",".webp":"image/webp",".json":"application/json"}
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
    page=browser.new_page(viewport={"width":1500,"height":1030})
    errors=[]
    page.on("pageerror",lambda e:errors.append(str(e)))
    def local(route):
        path=urlparse(route.request.url).path.lstrip("/") or "index.html"
        file=ROOT/path
        if not file.is_file():route.fulfill(status=404,body=path);return
        route.fulfill(status=200,content_type=types.get(file.suffix,"application/octet-stream"),path=str(file))
    page.route("https://hem-chien-ui.test/**",local)
    page.goto(URL,wait_until="domcontentloaded")
    page.wait_for_function("window.__combatDebug && window.__combatDebug().latestArtReady",timeout=30000)
    assert page.locator("#startOverlay").is_visible()
    assert page.locator(".hero-logo").inner_text().replace("\n","")=="HẺMCHIẾN."
    assert page.locator("#startBtn").is_enabled()
    assert page.locator(".hero-showcase").is_visible()
    page.locator(".game-shell").screenshot(path=str(ROOT/"premium-title-preview.png"))
    page.locator("#startBtn").click()
    assert page.evaluate("window.__gameDebug().state")=="fight"
    page.wait_for_timeout(500)
    assert not errors,errors
    print("PREMIUM MENU PASS",{"started":page.evaluate("window.__gameDebug().state"),"artistReady":page.evaluate("window.__combatDebug().latestArtReady")})
    browser.close()
