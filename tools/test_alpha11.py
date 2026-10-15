"""Alpha 1.1 browser checks: neutral pose transition and diagnostic render telemetry."""
import base64
import json
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
def uri(path, mime):
    return 'data:'+mime+';base64,'+base64.b64encode((ROOT/path).read_bytes()).decode('ascii')

html=(ROOT/'index.html').read_text().replace('<link rel="stylesheet" href="styles.css">','').replace('<script src="game.js"></script>','')
js=(ROOT/'game.js').read_text()
js=js.replace("bg.src='assets/saigon-night.png'", "bg.src='"+uri('assets/saigon-night.png','image/png')+"'")
js=js.replace('`assets/sprites/${kind}-atlas.png`',"({minh:'"+uri('assets/sprites/minh-atlas.png','image/png')+"',linh:'"+uri('assets/sprites/linh-atlas.png','image/png')+"'})[kind]")
js=js.replace('`assets/portraits/${kind}.webp`',"({minh:'"+uri('assets/portraits/minh.webp','image/webp')+"',linh:'"+uri('assets/portraits/linh.webp','image/webp')+"'})[kind]")
js=js.replace('`assets/sprites/artist/${kind}-overlay.png`',"({minh:'"+uri('assets/sprites/artist/minh-overlay.png','image/png')+"',linh:'"+uri('assets/sprites/artist/linh-overlay.png','image/png')+"'})[kind]")
manifest=(ROOT/'assets/sprites/artist/manifest.json').read_text()
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=shutil.which('chromium') or p.chromium.executable_path,args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':960})
    errors=[]
    page.on('pageerror',lambda err:errors.append(str(err)))
    page.set_content(html,wait_until='domcontentloaded')
    page.add_style_tag(content=(ROOT/'styles.css').read_text())
    page.evaluate('(payload)=>{window.fetch=()=>Promise.resolve({ok:true,json:async()=>JSON.parse(payload)})}',manifest)
    page.add_script_tag(content=js)
    page.wait_for_function('window.__perfDebug && window.__combatDebug().artistReady.minh && window.__combatDebug().artistReady.linh',timeout=30000)
    page.locator('#modeSelect').select_option('pvp')
    page.locator('#startBtn').click()
    page.wait_for_timeout(2050)
    page.keyboard.down('d')
    page.wait_for_timeout(160)
    page.keyboard.up('d')
    page.wait_for_function("window.__perfDebug().visual.minh.action==='idle' && window.__perfDebug().visual.minh.previous==='walk' && window.__perfDebug().visual.minh.remaining>0",timeout=3000)
    visual=page.evaluate('window.__perfDebug().visual.minh')
    assert 1<=visual['remaining']<=5,visual
    page.keyboard.press('b')
    assert page.evaluate('window.__perfDebug().profilerVisible')
    page.keyboard.press('m')
    assert page.evaluate('window.__perfDebug().motionReduced')
    page.keyboard.press('m')
    assert not page.evaluate('window.__perfDebug().motionReduced')
    page.wait_for_timeout(1100)
    metrics=page.evaluate('window.__perfDebug()')
    assert metrics['samples']>=10,metrics
    assert metrics['drawP95Ms']>0 and metrics['frameP95Ms']>0,metrics
    assert not errors,errors
    (ROOT/'alpha11-benchmark.json').write_text(json.dumps({k:metrics[k] for k in ['meanFps','drawP95Ms','drawMedianMs','frameP95Ms','slowFrames','frames','samples']},indent=2))
    page.locator('#game').screenshot(path=str(ROOT/'alpha11-gameplay-preview.png'))
    print('ALPHA 1.1 POLISH + PERF PASS',{'fps':round(metrics['meanFps'],1),'drawP95Ms':round(metrics['drawP95Ms'],1),'frameP95Ms':round(metrics['frameP95Ms'],1),'transition':visual})
    browser.close()
