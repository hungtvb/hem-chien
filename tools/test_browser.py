"""Browser smoke test without localhost; environment may restrict browser navigation."""
from pathlib import Path
import base64
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="styles.css">','').replace('<script src="game.js"></script>','')
css=(ROOT/'styles.css').read_text()
js=(ROOT/'game.js').read_text()
stage='data:image/png;base64,'+base64.b64encode((ROOT/'assets'/'saigon-night.png').read_bytes()).decode()
js=js.replace("bg.src='assets/saigon-night.png'", "bg.src='"+stage+"'")
with sync_playwright() as pl:
    browser=pl.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
    page=browser.new_page(viewport={'width':1440,'height':1090},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.set_content(html,wait_until='domcontentloaded')
    page.add_style_tag(content=css)
    page.add_script_tag(content=js)
    assert page.title().startswith('HẺM CHIẾN')
    assert page.evaluate('window.__gameDebug().state')=='menu'
    page.locator('#modeSelect').select_option('pvp')
    page.locator('#startBtn').click()
    page.wait_for_timeout(2050)
    assert page.evaluate('window.__gameDebug().state')=='fight'
    start_x=page.evaluate('window.__gameDebug().p1.x')
    page.keyboard.down('d');page.wait_for_timeout(2300);page.keyboard.up('d')
    new_x=page.evaluate('window.__gameDebug().p1.x')
    assert new_x>start_x+130,(start_x,new_x)
    before_hp=page.evaluate('window.__gameDebug().p2.hp')
    page.keyboard.press('k');page.wait_for_timeout(320)
    after_hp=page.evaluate('window.__gameDebug().p2.hp')
    print('HIT TEST',before_hp,'->',after_hp, 'positions',page.evaluate('window.__gameDebug().p1.x'),page.evaluate('window.__gameDebug().p2.x'))
    assert after_hp<before_hp, 'Heavy punch did not connect, collision or range issue'
    # Pause stops simulation and resumes after toggling P.
    page.keyboard.press('p');page.wait_for_timeout(140)
    assert page.evaluate('window.__gameDebug().state')=='paused'
    page.keyboard.press('p');page.wait_for_timeout(140)
    assert page.evaluate('window.__gameDebug().state')=='fight'
    # Complete attack recovery before jump, then verify airborne state.
    page.wait_for_timeout(450)
    page.keyboard.down('w');page.wait_for_timeout(190);page.keyboard.up('w')
    assert page.evaluate('window.__gameDebug().p1.action')=='jump'
    page.wait_for_timeout(750)
    # P2 faces left; moving right holds BACK to block a mid special.
    guard_hp=page.evaluate('window.__gameDebug().p2.hp')
    page.keyboard.down('ArrowRight');page.keyboard.press('q');page.wait_for_timeout(480);page.keyboard.up('ArrowRight')
    after_guard=page.evaluate('window.__gameDebug().p2.hp')
    print('BLOCK TEST',guard_hp,'->',after_guard)
    assert after_guard==guard_hp, 'Blocking mid special should avoid HP damage'
    # Atlas generation must work and have usable, nonzero byte sizes.
    for kind in ['minh','linh']:
        data=page.evaluate('(kind)=>window.makeSpriteAtlas(kind)',kind)
        raw=base64.b64decode(data.split(',')[1]);assert len(raw)>15000
        (ROOT/'assets'/f'{kind}-sprite-atlas.png').write_bytes(raw)
        print('ATLAS',kind,len(raw))
    page.screenshot(path=str(ROOT/'screenshot-preview.png'),full_page=True)
    page.locator('#game').screenshot(path=str(ROOT/'gameplay-preview.png'))
    assert not errors,'JS errors: '+str(errors)
    print('SMOKE TEST PASSED',page.evaluate('window.__gameDebug()'))
    browser.close()
