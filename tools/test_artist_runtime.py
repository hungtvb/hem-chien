"""Smoke test Alpha 0.6 artist overlay loading and backwards-compatible gameplay."""
import base64
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="styles.css">','').replace('<script src="game.js"></script>','')
css=(ROOT/'styles.css').read_text()
js=(ROOT/'game.js').read_text()
def data(path,mime):
    return f"data:{mime};base64,"+base64.b64encode((ROOT/path).read_bytes()).decode()
js=js.replace("bg.src='assets/saigon-night.png'", "bg.src='"+data('assets/saigon-night.png','image/png')+"'")
js=js.replace('`assets/sprites/${kind}-atlas.png`',"({minh:'"+data('assets/sprites/minh-atlas.png','image/png')+"',linh:'"+data('assets/sprites/linh-atlas.png','image/png')+"'})[kind]")
js=js.replace('`assets/portraits/${kind}.webp`',"({minh:'"+data('assets/portraits/minh.webp','image/webp')+"',linh:'"+data('assets/portraits/linh.webp','image/webp')+"'})[kind]")
# This test uses the production no-art manifest; no placeholder poster is presented as art.
manifest=(ROOT/'assets/sprites/artist/manifest.json').read_text()
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':950})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html,wait_until='domcontentloaded')
    page.add_style_tag(content=css)
    page.evaluate('(value)=>{window.fetch=()=>Promise.resolve({ok:true,json:async()=>JSON.parse(value)})}',manifest)
    page.add_script_tag(content=js)
    page.wait_for_timeout(500)
    d=page.evaluate('window.__combatDebug()')
    assert d['artistPoseCoverage']=={'minh':[],'linh':[]},d
    assert all(d['atlasReady'].values()),d
    assert d['spriteRevision']=='artist-overlay-v0.6',d
    assert not errors,errors
    page.locator('#modeSelect').select_option('pvp')
    page.locator('#startBtn').click()
    page.wait_for_timeout(1800)
    page.keyboard.down('d');page.wait_for_timeout(2400);page.keyboard.up('d')
    before=page.evaluate('window.__gameDebug().p2.hp')
    page.keyboard.press('k');page.wait_for_timeout(400)
    after=page.evaluate('window.__gameDebug().p2.hp')
    assert after<before,(before,after)
    print('Alpha 0.6 artist fallback PASS',{ 'coverage':d['artistPoseCoverage'],'damage':before-after,'atlasReady':d['atlasReady']})
    browser.close()