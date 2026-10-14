"""Alpha 0.4 browser contract: hit confirm, whiff cancellation and animation telemetry."""
from pathlib import Path
import base64
import shutil
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="styles.css">','').replace('<script src="game.js"></script>','')
css=(ROOT/'styles.css').read_text()
js=(ROOT/'game.js').read_text()
def data(rel,mime):
    return 'data:'+mime+';base64,'+base64.b64encode((ROOT/rel).read_bytes()).decode()
js=js.replace("bg.src='assets/saigon-night.png'", "bg.src='"+data('assets/saigon-night.png','image/png')+"'")
for key,ext,mime in [('sprites','png','image/png'),('portraits','webp','image/webp')]:
    template= f'`assets/{key}/${{kind}}'+('-atlas' if key=='sprites' else '')+f'.{ext}`'
    replace= '({minh:'+repr(data(f'assets/{key}/minh'+('-atlas' if key=='sprites' else '')+f'.{ext}',mime))+',linh:'+repr(data(f'assets/{key}/linh'+('-atlas' if key=='sprites' else '')+f'.{ext}',mime))+'})[kind]'
    assert template in js,template
    js=js.replace(template,replace)
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path=shutil.which('chromium') or pw.chromium.executable_path,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':1024})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html,wait_until='domcontentloaded');page.add_style_tag(content=css);page.add_script_tag(content=js)
    page.wait_for_timeout(350)
    assert all(page.evaluate('window.__combatDebug().atlasReady').values())
    page.locator('#modeSelect').select_option('pvp')
    page.locator('#trainingBtn').click()
    page.wait_for_timeout(1950)
    assert page.evaluate('window.__gameDebug().state')=='fight'
    initial_x=page.evaluate('window.__gameDebug().p1.x')
    # At full-screen distance, a whiffed HP cannot be canceled into a special.
    page.keyboard.press('k');page.wait_for_timeout(180)
    assert page.evaluate('window.__gameDebug().p1.action')=='hp'
    page.keyboard.press('q');page.wait_for_timeout(80)
    assert page.evaluate('window.__gameDebug().p1.action')=='hp', 'A whiffed heavy was erroneously cancelable'
    print('WHIFF CANCEL BLOCKED',page.evaluate('window.__gameDebug().p1.action'))
    page.wait_for_timeout(950)
    # P1 move into range with player two stationary.
    page.keyboard.down('d')
    page.wait_for_function('window.__gameDebug().p1.x >= 800',timeout=5000)
    page.keyboard.up('d')
    x=page.evaluate('window.__gameDebug().p1.x')
    assert x>initial_x+450, x
    hp=page.evaluate('window.__gameDebug().p2.hp')
    page.keyboard.press('k');page.wait_for_timeout(178)
    confirmed=page.evaluate('window.__combatDebug().cancelConfirmed.p1')
    after=page.evaluate('window.__gameDebug().p2.hp')
    print('HIT CONFIRM',hp,'->',after,'confirmed',confirmed)
    assert confirmed and after==hp-85, (hp,after)
    page.keyboard.press('q');page.wait_for_timeout(90)
    assert page.evaluate('window.__gameDebug().p1.action')=='special','HP -> Special did not cancel'
    print('CANCEL HP→SPECIAL PASS')
    stats=page.evaluate('window.__combatDebug().trainingStats')
    assert stats['damage']>0 and stats['combo']>=1,stats
    assert page.evaluate('window.__combatDebug().showTrainingPanel')
    page.keyboard.press('t');assert not page.evaluate('window.__combatDebug().showTrainingPanel')
    page.keyboard.press('t');assert page.evaluate('window.__combatDebug().showTrainingPanel')
    timing=page.evaluate('window.__combatDebug().animationTimings')
    assert len(timing['walk'])==4 and timing['walk'][0]!=timing['walk'][1]
    page.locator('#game').screenshot(path=str(ROOT/'alpha04-gameplay-preview.png'))
    assert not errors,errors
    print('ALPHA 0.4 E2E PASS',{'hp':after,'timeline':timing['walk'],'training':stats,'x':x})
    browser.close()
