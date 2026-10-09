"""Capture full-page screenshots with headless Chromium (Playwright).
usage: python tools/shots.py URL out.png [--wake]   (--wake presses Space and waits, for apps with an intro overlay)
Set CHROME=/path/to/chrome to use a system browser, otherwise run `playwright install chromium` first."""
import sys,os
from playwright.sync_api import sync_playwright
url,out=sys.argv[1],sys.argv[2]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME') or None)
    pg=b.new_page(viewport={'width':1440,'height':1000}); pg.goto(url,wait_until='networkidle'); pg.wait_for_timeout(3000)
    if '--wake' in sys.argv: pg.keyboard.press('Space'); pg.wait_for_timeout(9000)
    pg.screenshot(path=out,full_page=True); b.close()
