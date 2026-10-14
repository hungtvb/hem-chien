"""Bake the 4-frame/12-state 2D pose atlases from the vector placeholder.

This is a technical animation pipeline, not a hand-drawn production art exporter.
"""
from pathlib import Path
import base64
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'assets' / 'sprites'
OUTPUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as playwright:
    executable = os.environ.get('CHROMIUM_PATH')
    launch_opts = {'headless': True, 'args': ['--no-sandbox', '--disable-dev-shm-usage']}
    if executable:
        launch_opts['executable_path'] = executable
    browser = playwright.chromium.launch(**launch_opts)
    page = browser.new_page(viewport={'width': 1440, 'height': 960})
    html = (ROOT / 'index.html').read_text().replace('<link rel="stylesheet" href="styles.css">', '').replace('<script src="game.js"></script>', '')
    page.set_content(html, wait_until='domcontentloaded')
    page.add_style_tag(content=(ROOT / 'styles.css').read_text())
    page.add_script_tag(content=(ROOT / 'game.js').read_text())
    page.wait_for_function('typeof window.makeSpriteAtlas === "function"')
    for kind in ('minh', 'linh'):
        data = page.evaluate('(kind) => window.makeSpriteAtlas(kind).split(",")[1]', kind)
        result = OUTPUT / f'{kind}-atlas.png'
        result.write_bytes(base64.b64decode(data))
        assert result.stat().st_size > 20000, f'Empty sprite atlas: {kind}'
        print(f'{kind} sprite atlas: {result.stat().st_size:,} bytes')
    browser.close()