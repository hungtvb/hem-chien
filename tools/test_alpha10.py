"""Alpha 1.0: verify the final 4 special/super pose rows and combat regression.
These sprites use concept cutout/rig deformation, NOT independently hand-drawn art.
"""
import base64
import shutil
from pathlib import Path
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
POSES=('idle','walk','jump','crouch','block','lp','hp','lk','hk','special','super','hit')

def uri(path, mime):
    return 'data:'+mime+';base64,'+base64.b64encode((ROOT/path).read_bytes()).decode('ascii')

for kind in ('minh','linh'):
    for pose in ('special','super'):
        frames=[]
        for i in range(4):
            p=ROOT/'art-source'/kind/pose/f'{i:02d}.png'
            with Image.open(p) as img:
                assert img.mode=='RGBA' and img.size==(448,360),p
                b=img.getchannel('A').getbbox()
                assert b and b[0]>=3 and b[1]>=3 and b[2]<=445 and b[3]<=357,(p,b)
                frames.append(img.copy())
        assert len({f.tobytes() for f in frames})==4,(kind,pose,'duplicate keyframes')
        assert ImageChops.difference(frames[0],frames[2]).getbbox(),(kind,pose,'no motion')

html=(ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="styles.css">','').replace('<script src="game.js"></script>','')
js=(ROOT/'game.js').read_text()
js=js.replace("bg.src='assets/saigon-night.png'", "bg.src='"+uri('assets/saigon-night.png','image/png')+"'")
js=js.replace('`assets/sprites/${kind}-atlas.png`',"({minh:'"+uri('assets/sprites/minh-atlas.png','image/png')+"',linh:'"+uri('assets/sprites/linh-atlas.png','image/png')+"'})[kind]")
js=js.replace('`assets/portraits/${kind}.webp`',"({minh:'"+uri('assets/portraits/minh.webp','image/webp')+"',linh:'"+uri('assets/portraits/linh.webp','image/webp')+"'})[kind]")
js=js.replace('`assets/sprites/artist/${kind}-overlay.png`',"({minh:'"+uri('assets/sprites/artist/minh-overlay.png','image/png')+"',linh:'"+uri('assets/sprites/artist/linh-overlay.png','image/png')+"'})[kind]")
manifest=(ROOT/'assets/sprites/artist/manifest.json').read_text()
with sync_playwright() as playwright:
    exe=shutil.which('chromium') or playwright.chromium.executable_path
    browser=playwright.chromium.launch(headless=True,executable_path=exe,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':960})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html,wait_until='domcontentloaded')
    page.add_style_tag(content=(ROOT/'styles.css').read_text())
    page.evaluate('(json)=>{window.fetch=()=>Promise.resolve({ok:true,json:async()=>JSON.parse(json)})}',manifest)
    page.add_script_tag(content=js)
    page.wait_for_function('window.__combatDebug && window.__combatDebug().artistReady.minh && window.__combatDebug().artistReady.linh',timeout=30000)
    d=page.evaluate('window.__combatDebug()')
    for kind in ('minh','linh'):
        assert sorted(d['artistPoseCoverage'][kind])==sorted(POSES),(kind,d['artistPoseCoverage'])
        assert d['atlasReady'][kind]
    page.locator('#modeSelect').select_option('pvp')
    page.locator('#startBtn').click()
    page.wait_for_timeout(2650)
    # Special animation must still trigger from Q; sprite art must not alter damage logic.
    page.keyboard.press('q')
    page.wait_for_timeout(120)
    assert page.evaluate('window.__gameDebug().p1.action')=='special','Special did not trigger'
    page.wait_for_timeout(900)
    page.keyboard.down('d')
    page.wait_for_timeout(2320)
    page.keyboard.up('d')
    before=page.evaluate('window.__gameDebug().p2.hp')
    page.keyboard.press('k')
    page.wait_for_timeout(460)
    after=page.evaluate('window.__gameDebug().p2.hp')
    assert before-after==85,(before,after)
    page.locator('#game').screenshot(path=str(ROOT/'alpha10-gameplay-preview.png'))
    assert not errors,errors
    print('ALPHA 1.0 E2E PASS',{'coverage':{k:len(v) for k,v in d['artistPoseCoverage'].items()},'hpDelta':before-after,'errors':errors})
    browser.close()
