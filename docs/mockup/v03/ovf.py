import sys, asyncio, pathlib
from playwright.async_api import async_playwright
files = sys.argv[1:]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1440, "height": 900})
        for f in files:
            html = pathlib.Path(f).read_text(encoding="utf-8").replace('<script src="./support.js"></script>', "")
            await pg.set_content(html, wait_until="networkidle")
            res = await pg.evaluate("""() => {
              const out=[]; document.querySelectorAll('*').forEach(e=>{const r=e.getBoundingClientRect(); if(r.right>1441 && r.width<1400){out.push([e.tagName, (e.className||'').toString().slice(0,30), Math.round(r.left), Math.round(r.right), (e.textContent||'').trim().slice(0,40)])}});
              return {w: document.documentElement.scrollWidth, items: out.slice(0,12)} }""")
            print(f, res)
        await b.close()
asyncio.run(main())
