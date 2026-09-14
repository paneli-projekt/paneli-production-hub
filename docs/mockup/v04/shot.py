import sys, asyncio, pathlib
from playwright.async_api import async_playwright

files = sys.argv[1:] or ["Nalozi.dc.html", "Main.dc.html", "PilaNesting.dc.html", "Obracun.dc.html"]
out = pathlib.Path("shots"); out.mkdir(exist_ok=True)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        for f in files:
            html = pathlib.Path(f).read_text(encoding="utf-8").replace('<script src="./support.js"></script>', "")
            tmp = pathlib.Path("shots") / ("_tmp_" + f.replace(".dc.html", ".html"))
            tmp.write_text(html.replace('src="logo-mark.png"', 'src="../logo-mark.png"'), encoding="utf-8")
            await pg.goto("file://" + str(tmp.resolve()), wait_until="networkidle")
            h = await pg.evaluate("document.body.scrollHeight")
            root_h = await pg.evaluate("document.querySelector('x-dc > div').getBoundingClientRect().height")
            await pg.screenshot(path=str(out / (f.replace(".dc.html", ".png"))), full_page=True)
            print(f, "scrollHeight", h, "root", root_h)
        await b.close()

asyncio.run(main())
