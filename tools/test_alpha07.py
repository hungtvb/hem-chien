"""End-to-end Alpha 0.7 regression: concept cutout overlay + gameplay fallback."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
import base64

def b64(path,mime):
    return f'data:{mime};base64,'+base64.b64encode((ROOT/path).read_bytes()).decode()

html=(ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="styles.css">','').replace('<script src="game.js"></script>','')
js=(ROOT/'game.js').read_text()
js=js.replace("bg.src='assets/saigon-night.png'", "bg.src='"+b64('assets/saigon-night.png','image/png')+"'")
js=js.replace('`assets/sprites/${kind}-atlas.png`', "({minh:'"+b64('assets/sprites/minh-atlas.png','image/png')+"',linh:'"+b64('assets/sprites/linh-atlas.png','image/png')+"'})[kind]")
js=js.replace('`assets/portraits/${kind}.webp`', "({minh:'"+b64('assets/portraits/minh.webp','image/webp')+"',linh:'"+b64('assets/portraits/linh.webp','image/webp')+"'})[kind]")
js=js.replace('`assets/sprites/artist/${kind}-overlay.png`', "({minh:'"+b64('assets/sprites/artist/minh-overlay.png','image/png')+"',linh:'"+b64('assets/sprites/artist/linh-overlay.png','image/png')+"'})[kind]")
manifest=(ROOT/'assets/sprites/artist/manifest.json').read_text()

with sync_playwright() as playwright:
    import shutil
    browser=playwright.chromium.launch(headless=True,executable_path=shutil.which('chromium') or playwright.chromium.executable_path,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':960})
    errors=[]
    page.on('pageerror',lambda err:errors.append(str(err)))
    page.set_content(html,wait_until='domcontentloaded')
    page.add_style_tag(content=(ROOT/'styles.css').read_text())
    page.evaluate('(value)=>{window.fetch=()=>Promise.resolve({ok:true,json:async()=>JSON.parse(value)})}',manifest)
    page.add_script_tag(content=js)
    page.wait_for_function('()=>window.__combatDebug && window.__combatDebug().artistReady.minh && window.__combatDebug().artistReady.linh',timeout=15000)
    info=page.evaluate('window.__combatDebug()')
    for fighter in ('minh','linh'):
        assert sorted(info['artistPoseCoverage'][fighter])==['idle','walk'],(fighter,info)
        assert info['atlasReady'][fighter],(fighter,info)
    assert not errors,errors
    page.locator('#modeSelect').select_option('pvp')
    page.locator('#startBtn').click()
    page.wait_for_timeout(1850)
    page.locator('#game').screenshot(path=str(ROOT/'alpha07-gameplay-preview.png'))
    initial=page.evaluate('window.__gameDebug().p1.x')
    page.keyboard.down('d');page.wait_for_timeout(2300);page.keyboard.up('d')
    assert page.evaluate('window.__gameDebug().p1.x')>initial+100
    before=page.evaluate('window.__gameDebug().p2.hp')
    page.keyboard.press('k');page.wait_for_timeout(420)
    after=page.evaluate('window.__gameDebug().p2.hp')
    assert after==before-85,(before,after)
    assert not errors,errors
    print('ALPHA 0.7 E2E PASS:',info['artistPoseCoverage'],'damage',before-after,'fallback atlas ready')
    browser.close()
