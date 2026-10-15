"""Alpha 0.9: check movement and defense poses load from the artist overlay and hit logic remains intact.

Uses inlined game assets so browser tests don't depend on localhost networking.
"""
import base64
import shutil
from pathlib import Path
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
POSES = ('idle','walk','jump','crouch','block','lp','hp','lk','hk','hit')

def data(path, mime):
    return f'data:{mime};base64,'+base64.b64encode((ROOT/path).read_bytes()).decode()

for fighter in ('minh','linh'):
    for pose in ('crouch','jump','block','hit'):
        images=[]
        for frame in range(4):
            path=ROOT/'art-source'/fighter/pose/f'{frame:02d}.png'
            with Image.open(path) as im:
                assert im.mode=='RGBA' and im.size==(448,360),(fighter,pose,frame)
                bounds=im.getchannel('A').getbbox()
                assert bounds and bounds[0]>2 and bounds[1]>2 and bounds[2]<445 and bounds[3]<357,(fighter,pose,frame,bounds)
                images.append(im.copy())
        assert any(ImageChops.difference(images[0],img).getbbox() for img in images[1:]),(fighter,pose,'static animation')

html=(ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="styles.css">','').replace('<script src="game.js"></script>','')
js=(ROOT/'game.js').read_text()
js=js.replace("bg.src='assets/saigon-night.png'", "bg.src='"+data('assets/saigon-night.png','image/png')+"'")
js=js.replace('`assets/sprites/${kind}-atlas.png`',"({minh:'"+data('assets/sprites/minh-atlas.png','image/png')+"',linh:'"+data('assets/sprites/linh-atlas.png','image/png')+"'})[kind]")
js=js.replace('`assets/portraits/${kind}.webp`',"({minh:'"+data('assets/portraits/minh.webp','image/webp')+"',linh:'"+data('assets/portraits/linh.webp','image/webp')+"'})[kind]")
js=js.replace('`assets/sprites/artist/${kind}-overlay.png`',"({minh:'"+data('assets/sprites/artist/minh-overlay.png','image/png')+"',linh:'"+data('assets/sprites/artist/linh-overlay.png','image/png')+"'})[kind]")
manifest=(ROOT/'assets/sprites/artist/manifest.json').read_text()

with sync_playwright() as pw:
    exe=shutil.which('chromium') or pw.chromium.executable_path
    browser=pw.chromium.launch(headless=True,executable_path=exe,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':960})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html,wait_until='domcontentloaded')
    page.add_style_tag(content=(ROOT/'styles.css').read_text())
    page.evaluate('(value)=>{window.fetch=()=>Promise.resolve({ok:true,json:async()=>JSON.parse(value)})}',manifest)
    page.add_script_tag(content=js)
    page.wait_for_function('window.__combatDebug && window.__combatDebug().artistReady.minh && window.__combatDebug().artistReady.linh',timeout=30000)
    debug=page.evaluate('window.__combatDebug()')
    for fighter in ('minh','linh'):
        assert set(POSES).issubset(set(debug['artistPoseCoverage'][fighter])),debug['artistPoseCoverage']
        assert debug['atlasReady'][fighter]
    page.locator('#modeSelect').select_option('pvp')
    page.locator('#startBtn').click()
    page.wait_for_timeout(2500)
    page.keyboard.down('s')
    page.wait_for_timeout(150)
    assert page.evaluate('window.__gameDebug().p1.action') == 'crouch'
    page.keyboard.up('s')
    page.keyboard.down('w')
    page.wait_for_timeout(180)
    assert page.evaluate('window.__gameDebug().p1.action') == 'jump'
    page.keyboard.up('w')
    page.wait_for_timeout(700)
    page.keyboard.down('d')
    page.wait_for_timeout(2350)
    page.keyboard.up('d')
    before=page.evaluate('window.__gameDebug().p2.hp')
    page.keyboard.press('k')
    page.wait_for_timeout(470)
    after=page.evaluate('window.__gameDebug().p2.hp')
    assert before-after==85,(before,after)
    page.locator('#game').screenshot(path=str(ROOT/'alpha09-gameplay-preview.png'))
    assert not errors,errors
    print('ALPHA 0.9 E2E PASS',{'artPoses':debug['artistPoseCoverage'],'hpBefore':before,'hpAfter':after,'errors':errors})
    browser.close()
