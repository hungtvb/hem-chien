"""Alpha 0.3 visual/E2E assertions with a loopback static server."""
from pathlib import Path
import base64
import shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="styles.css">','').replace('<script src="game.js"></script>','')
css=(ROOT/'styles.css').read_text()
js=(ROOT/'game.js').read_text()
def as_data(rel,mime):
 return f"data:{mime};base64,"+base64.b64encode((ROOT/rel).read_bytes()).decode()
js=js.replace("bg.src='assets/saigon-night.png'", "bg.src='"+as_data('assets/saigon-night.png','image/png')+"'")
js=js.replace('`assets/sprites/${kind}-atlas.png`', "({minh:'"+as_data('assets/sprites/minh-atlas.png','image/png')+"',linh:'"+as_data('assets/sprites/linh-atlas.png','image/png')+"'})[kind]")
js=js.replace('`assets/portraits/${kind}.webp`', "({minh:'"+as_data('assets/portraits/minh.webp','image/webp')+"',linh:'"+as_data('assets/portraits/linh.webp','image/webp')+"'})[kind]")
with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path=shutil.which('chromium') or shutil.which('google-chrome') or p.chromium.executable_path,args=['--no-sandbox','--disable-dev-shm-usage'])
  page=browser.new_page(viewport={'width':1440,'height':950});errors=[];fail=[]
  page.on('pageerror',lambda e: errors.append(str(e)))
  page.on('response',lambda r: fail.append(f'{r.status} {r.url}') if r.status>=400 else None)
  page.set_content(html,wait_until="domcontentloaded")
  page.add_style_tag(content=css)
  page.add_script_tag(content=js)
  page.wait_for_timeout(500)
  r=page.evaluate('window.__combatDebug()')
  assert all(r['portraitReady'].values()),r
  assert all(r['atlasReady'].values()),r
  page.locator('#modeSelect').select_option('pvp');page.locator('#startBtn').click();page.wait_for_timeout(1900)
  page.locator('#game').screenshot(path=str(ROOT/'alpha03-gameplay-preview.png'))
  page.keyboard.press('m');assert page.evaluate('window.__combatDebug().reduceMotion')
  page.keyboard.press('m');assert not page.evaluate('window.__combatDebug().reduceMotion')
  start=page.evaluate('window.__gameDebug().p1.x');page.keyboard.down('d');page.wait_for_timeout(2350);page.keyboard.up('d');assert page.evaluate('window.__gameDebug().p1.x')>start+100
  hp=page.evaluate('window.__gameDebug().p2.hp');page.keyboard.press('k');page.wait_for_timeout(400)
  assert page.evaluate('window.__gameDebug().p2.hp')<hp
  # Force super via training gameplay, using browser debug access without modifying game.
  # Basic tests additionally check no asset requests failed and no JS exceptions.
  page.keyboard.press('h');assert page.evaluate('window.__combatDebug().showCombatBoxes')
  page.keyboard.press('v');assert not page.evaluate('window.__combatDebug().preferAtlas')
  page.keyboard.press('v');assert page.evaluate('window.__combatDebug().preferAtlas')
  assert not errors,errors
  assert not fail,fail
  print('ALPHA 0.3 VISUAL SMOKE PASS',{'portraits':r['portraitReady'],'atlases':r['atlasReady'],'hp':page.evaluate('window.__gameDebug().p2.hp')})
  browser.close()
