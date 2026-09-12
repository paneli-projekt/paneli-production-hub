# -*- coding: utf-8 -*-
"""Varijanta C — neovisan UX prijedlog (bez oslanjanja na PPNEST raspored, Regal traku ni brand ploče).
Načelo: sve za unos na JEDNOM ekranu bez skrolanja (1440×980): lijevo materijali, u sredini tablica elemenata
s redom za unos na vrhu (tipkovnica: Tab/Enter, rubovi jednim slovom), desno inspektor s daskom koji prati
odabrani redak. Jedan naglasak (mahovina zelena), topla papirnata pozadina, brojevi u monospace."""

INK = "#1C2A33"; MUTED = "#66727C"; LINE = "#DDD8CF"; LINE2 = "#EBE7DF"; PAPER = "#F6F4EF"; SURF = "#FFFFFF"
ACC = "#2E6B57"; ACC_SOFT = "#E3EFE9"; ABS = "#2F5D8C"; MEL = "#B7791F"; WARN = "#B7791F"; CRIT = "#A63D2F"

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&amp;family=JetBrains+Mono:wght@500;600&amp;display=swap">'

CSS = """
:root{--ink:%(ink)s;--muted:%(muted)s;--line:%(line)s;--line2:%(line2)s;--paper:%(paper)s;--surf:%(surf)s;--acc:%(acc)s;--acc-soft:%(accsoft)s;--abs:%(abs)s;--mel:%(mel)s}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Public Sans",system-ui,-apple-system,"Segoe UI",sans-serif;font-size:14px;line-height:1.4}
a{color:var(--acc)} a:hover{color:#1F4E3F}
.num{font-family:"JetBrains Mono",ui-monospace,Consolas,monospace;font-variant-numeric:tabular-nums}
.rail{width:76px;background:var(--surf);border-right:1px solid var(--line);display:flex;flex-direction:column;align-items:center;padding:14px 0;gap:6px}
.rail .it{width:62px;padding:8px 0 6px;border-radius:8px;display:flex;flex-direction:column;align-items:center;gap:4px;font-size:10.5px;font-weight:600;color:var(--muted);letter-spacing:.02em}
.rail .it.on{background:var(--acc-soft);color:var(--acc)}
.rail .it svg{width:20px;height:20px}
.topbar{height:52px;background:var(--surf);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:14px;padding:0 20px}
.crumb{color:var(--muted);font-size:13px} .crumb b{color:var(--ink);font-weight:700;font-size:16px}
.pill{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:3px 10px;font-size:12px;font-weight:600;color:var(--muted);background:var(--surf)}
.pill.on{background:var(--acc);border-color:var(--acc);color:#fff}
.pill.done{border-color:var(--acc);color:var(--acc)}
.btn{background:var(--surf);border:1px solid var(--line);border-radius:6px;padding:7px 12px;font-weight:600;font-size:13px;color:var(--ink)}
.btn.pri{background:var(--acc);border-color:var(--acc);color:#fff}
.btn.ghost{border-style:dashed;color:var(--muted);font-weight:500}
.lbl{font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:700}
.pane{background:var(--surf);border:1px solid var(--line);border-radius:10px;display:flex;flex-direction:column;min-height:0}
.pane .hd{padding:10px 14px;border-bottom:1px solid var(--line2);display:flex;align-items:center;gap:8px}
.mat{padding:10px 14px;border-bottom:1px solid var(--line2);display:flex;flex-direction:column;gap:3px;cursor:pointer}
.mat.on{background:var(--acc-soft);box-shadow:inset 3px 0 0 var(--acc)}
.mat b{font-size:13.5px} .mat .m{font-size:12px;color:var(--muted)}
.tag{display:inline-block;white-space:nowrap;font-size:10.5px;font-weight:700;letter-spacing:.04em;padding:1px 6px;border-radius:4px;background:var(--line2);color:var(--muted)}
.tag.nest{background:#1C2A33;color:#fff} .tag.pila{background:#8C7A63;color:#fff} .tag.warn{background:#F6E7C9;color:#7A4E10} .tag.ok{background:var(--acc-soft);color:var(--acc)}
table{border-collapse:collapse;width:100%%}
th{font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap;font-weight:700}
td{padding:6px 10px;border-bottom:1px solid var(--line2);vertical-align:middle;white-space:nowrap}
td.r,th.r{text-align:right}
tr.entry td{background:#FBFAF6;border-bottom:2px solid var(--acc);padding:8px 10px}
tr.sel td{background:var(--acc-soft)}
.cell{display:inline-block;min-width:74px;border:1px solid var(--line);border-radius:6px;padding:5px 8px;background:var(--surf);font-size:16px;text-align:right}
.cell.foc{border-color:var(--acc);box-shadow:0 0 0 3px var(--acc-soft)}
.cell.txt{text-align:left;min-width:180px;font-size:13px;color:var(--muted)}
.e{display:inline-flex;width:26px;height:24px;align-items:center;justify-content:center;border-radius:5px;font-size:12px;font-weight:700;border:1px solid var(--line2);color:var(--muted)}
.e.A{background:var(--abs);border-color:var(--abs);color:#fff} .e.M{background:var(--mel);border-color:var(--mel);color:#fff}
.kbd{display:inline-block;min-width:18px;text-align:center;border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;padding:0 5px;font-family:"JetBrains Mono",monospace;font-size:11px;font-weight:600;background:var(--surf)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:6px;overflow:hidden}
.seg span{padding:3px 9px;font-size:12px;font-weight:700;color:var(--muted);border-right:1px solid var(--line)} .seg span:last-child{border-right:0}
.seg span.on{background:var(--ink);color:#fff}
.seg span.A.on{background:var(--abs)} .seg span.M.on{background:var(--mel)}
.foot{height:60px;background:var(--surf);border-top:1px solid var(--line);display:flex;align-items:center;gap:26px;padding:0 20px}
.kpi b{font-size:18px;font-weight:700} .kpi span{display:block;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:700}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%%;margin-right:6px;vertical-align:middle;background:var(--acc)}
.dot.warn{background:%(warn)s}
""" % dict(ink=INK, muted=MUTED, line=LINE, line2=LINE2, paper=PAPER, surf=SURF, acc=ACC, accsoft=ACC_SOFT, abs=ABS, mel=MEL, warn=WARN)


def ico(name):
    p = {
        "nalozi": '<path d="M5 3h10l4 4v14H5z"/><path d="M15 3v4h4M8 12h8M8 16h8"/>',
        "sifr": '<path d="M4 6h16M4 12h16M4 18h10"/>',
        "sklad": '<path d="M3 9 12 4l9 5v11H3z"/><path d="M9 20v-7h6v7"/>',
        "obr": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 11h8M8 15h5"/>',
        "post": '<circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.3.9a7 7 0 0 0-1.7-1L14.5 3h-5l-.4 2.5a7 7 0 0 0-1.7 1L5.1 5.6l-2 3.4L5.1 10.5a7 7 0 0 0 0 2L3.1 14l2 3.4 2.3-.9a7 7 0 0 0 1.7 1l.4 2.5h5l.4-2.5a7 7 0 0 0 1.7-1l2.3.9 2-3.4-2-1.5c.1-.3.1-.7.1-1z"/>',
    }[name]
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % p


# stvarni elementi HUMER_2823_OMIS · IV BIJELI NK 18 (rb, L, W, kom, L-rub, D-rub, G-rub, Dolje-rub, napomena, prolaza)
ELEMS = [
    (1, 820, 550, 16, "A", "", "A", "A", "", 1), (2, 820, 520, 4, "A", "", "A", "A", "", 1), (3, 140, 520, 1, "A", "", "A", "A", "134X520", 2),
    (4, 480, 550, 2, "A", "", "A", "A", "", 1), (5, 464, 520, 1, "A", "", "", "", "", 1), (6, 464, 80, 4, "A", "", "", "", "", 2),
    (22, 1830, 557, 2, "A", "", "A", "A", "RASTER 150 64-64 150", 1), (26, 544, 557, 8, "A", "", "", "", "CNC SKICA 1", 1),
    (27, 1050, 140, 1, "M", "M", "M", "M", "1050X120", 2), (31, 460, 190, 1, "M", "M", "M", "M", "", 2),
    (37, 1030, 340, 14, "A", "A", "A", "A", "RASTER 150 64-64 150", 1), (46, 272, 340, 2, "A", "", "A", "", "", 1),
]
BAND = {"A": "ABS-ISTI", "M": "MEL-ISTI", "": "—"}


def e(v):
    return '<span class="e %s">%s</span>' % (v, v or "·")


rows = []
for i, (rb, L, W, kom, l, d, g, dol, nap, pr) in enumerate(ELEMS):
    sel = ' class="sel"' if rb == 1 else ""
    bands = sorted({BAND[x] for x in (l, d, g, dol) if x})
    warn = ' <span class="tag warn">2 prolaza</span>' if pr == 2 else ""
    rows.append(
        '<tr%s><td class="r num" style="color: var(--muted);">%d</td><td class="r num" style="font-size: 15px; font-weight: 600;">%d</td><td class="r num" style="font-size: 15px; font-weight: 600;">%d</td><td class="r num">%d</td>'
        '<td>%s %s %s %s</td><td class="num" style="font-size: 12px;">%s</td><td style="color: var(--muted);">%s%s</td></tr>'
        % (sel, rb, L, W, kom, e(l), e(d), e(g), e(dol), " · ".join(bands) if bands else "—", nap, warn)
    )

mats = [("IV BIJELI NK 18", "53 st. · 174 kom · 50,4 m²", "nesting", True), ("IV JELA TAVERNA 19", "35 · 48 · 25,6 m²", "nesting", False),
        ("MDF BIJELI 3", "22 · 27 · 16,1 m²", "pila", False), ("IV BIJELI NK 16", "10 · 28 · 4,6 m²", "pila", False),
        ("IV HRAST RELIEF CARDAMOM 19", "1 · 1 · 1,9 m²", "pila", False), ("RP BASANIT SAND", "2 · 2 · 4,99 m", "pila", False)]
matl = "".join('<div class="mat%s"><b>%s</b><span class="m">%s</span><span><span class="tag %s">%s</span></span></div>'
               % (" on" if on else "", n, m, "nest" if p == "nesting" else "pila", p) for n, m, p, on in mats)


def board(L, W, l, d, g, dol):
    bx, by, bw, bh = 70, 40, 116, 186
    col = lambda v: ABS if v == "A" else (MEL if v == "M" else LINE)
    w = lambda v: "6" if v else "1.5"
    s = ['<svg width="260" height="262" viewBox="0 0 260 262" style="display: block;">']
    s.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#F6F4EF" stroke="%s"/>' % (bx, by, bw, bh, LINE))
    for x1, y1, x2, y2, v in ((bx, by, bx, by + bh, l), (bx + bw, by, bx + bw, by + bh, d), (bx, by, bx + bw, by, g), (bx, by + bh, bx + bw, by + bh, dol)):
        s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%s" stroke-linecap="square"/>' % (x1, y1, x2, y2, col(v), w(v)))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="JetBrains Mono, monospace" font-weight="600" font-size="15" fill="%s">%d</text>' % (bx + bw // 2, by - 14, INK, W))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="JetBrains Mono, monospace" font-weight="600" font-size="15" fill="%s" transform="rotate(-90 %d %d)">%d</text>' % (bx - 22, by + bh // 2, INK, bx - 22, by + bh // 2, L))
    # oznake strana
    for x, y, t in ((bx + bw // 2, by + bh + 20, "B"), (bx + bw + 22, by + bh // 2 + 5, "D"), (bx - 46, by + bh // 2 + 5, "L"), (bx + bw // 2 + 40, by - 14, "G")):
        s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Public Sans, sans-serif" font-weight="700" font-size="11" fill="%s">%s</text>' % (x, y, MUTED, t))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Public Sans, sans-serif" font-size="11" fill="%s">god ↕ (1. mjera)</text>' % (bx + bw // 2, by + bh // 2 + 4, MUTED))
    s.append("</svg>")
    return "".join(s)


def seg(v):
    return '<span class="seg"><span class="%s">—</span><span class="A%s">A</span><span class="M%s">M</span></span>' % (
        " on" if v == "" else "", " on" if v == "A" else "", " on" if v == "M" else "")


body = '''
<div style="display: flex; height: 980px;">
  <nav class="rail">
    <div style="width: 40px; height: 40px; border-radius: 10px; background: var(--ink); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 15px; margin-bottom: 8px;">PH</div>
    <div class="it on">''' + ico("nalozi") + '''Nalozi</div>
    <div class="it">''' + ico("sifr") + '''Šifrarnici</div>
    <div class="it">''' + ico("sklad") + '''Skladište</div>
    <div class="it">''' + ico("obr") + '''Obračun</div>
    <div class="it">''' + ico("post") + '''Postavke</div>
    <div style="flex: 1;"></div>
    <div style="width: 36px; height: 36px; border-radius: 50%; background: var(--acc-soft); color: var(--acc); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px;">IV</div>
  </nav>

  <div style="flex: 1; min-width: 0; display: flex; flex-direction: column;">
    <div class="topbar">
      <div class="crumb">Nalozi / <b>HUMER_2823_OMIS</b> <span style="margin-left: 8px;">Mario Humer · 18.08.2026 · ponuda 26-010-002823</span></div>
      <div style="flex: 1;"></div>
      <span class="pill on">1 Unos</span><span class="pill">2 Pila / nesting</span><span class="pill">3 Obračun</span>
      <span style="width: 10px;"></span>
      <button class="btn">Uvoz ▾</button><button class="btn">Zaglavlje</button><button class="btn pri">Spremi</button>
    </div>

    <div style="flex: 1; min-height: 0; display: grid; grid-template-columns: 250px minmax(0, 1fr) 320px; gap: 14px; padding: 14px 16px;">

      <div class="pane">
        <div class="hd"><span class="lbl">Materijali</span><span style="flex: 1;"></span><span class="num" style="font-size: 12px; color: var(--muted);">6</span></div>
        ''' + matl + '''
        <div style="padding: 10px 14px;"><button class="btn ghost" style="width: 100%;">+ Materijal</button></div>
        <div style="flex: 1;"></div>
        <div style="padding: 10px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Nalog: 123 st. · 280 kom · 103,1 m²</div>
      </div>

      <div class="pane">
        <div class="hd">
          <div><div class="lbl">Elementi</div><div style="font-weight: 700; font-size: 15px;">IV000090 · IVERAL BIJELI NK W908 ST2 18 MM <span style="color: var(--muted); font-weight: 500; font-size: 13px;">18 mm · bez goda · W908ST2-18</span></div></div>
          <div style="flex: 1;"></div>
          <span class="tag nest">nesting</span><span class="tag">Winstore 13</span>
        </div>
        <div style="overflow: hidden;">
        <table>
          <thead><tr><th class="r">#</th><th class="r">1. mjera</th><th class="r">2. mjera</th><th class="r">kom</th><th>Rubovi L · D · G · B</th><th>Traka</th><th>Napomena</th></tr></thead>
          <tbody>
            <tr class="entry"><td class="r num" style="color: var(--acc); font-weight: 700;">+</td>
              <td class="r"><span class="cell num foc">820</span></td><td class="r"><span class="cell num">550</span></td><td class="r"><span class="cell num" style="min-width: 56px;">16</span></td>
              <td>''' + e("A") + " " + e("") + " " + e("A") + " " + e("A") + '''</td>
              <td class="num" style="font-size: 12px;">ABS-ISTI</td>
              <td><span class="cell txt">napomena…</span></td></tr>
            ''' + "".join(rows) + '''
            <tr><td colspan="7" style="text-align: center; color: var(--muted); padding: 8px;">… još 41 redak · <a href="#">sve</a></td></tr>
          </tbody>
        </table>
        </div>
        <div style="flex: 1;"></div>
        <div style="padding: 8px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted); display: flex; gap: 14px; flex-wrap: wrap;">
          <span><span class="kbd">Tab</span> sljedeća ćelija</span><span><span class="kbd">Enter</span> potvrdi i novi red (mjere ostaju — serije)</span><span><span class="kbd">L</span><span class="kbd">D</span><span class="kbd">G</span><span class="kbd">B</span> rub: — → A → M</span><span><span class="kbd">↑</span><span class="kbd">↓</span> odabir retka (daska desno prati)</span>
        </div>
      </div>

      <div class="pane">
        <div class="hd"><span class="lbl">Element</span><span style="font-weight: 700; white-space: nowrap;">#1 · 820×550 · 16 kom</span><span style="flex: 1;"></span><span class="tag ok">novi</span></div>
        <div style="padding: 10px 14px; display: flex; flex-direction: column; gap: 12px;">
          <div style="display: flex; justify-content: center;">''' + board(820, 550, "A", "", "A", "A") + '''</div>
          <div style="display: grid; grid-template-columns: 26px 1fr auto; gap: 6px 10px; align-items: center; font-size: 13px;">
            <b>L</b><span class="num" style="font-size: 12px; color: var(--muted);">ABS-ISTI · 1 mm</span>''' + seg("A") + '''
            <b>D</b><span class="num" style="font-size: 12px; color: var(--muted);">—</span>''' + seg("") + '''
            <b>G</b><span class="num" style="font-size: 12px; color: var(--muted);">ABS-ISTI · 1 mm</span>''' + seg("A") + '''
            <b>B</b><span class="num" style="font-size: 12px; color: var(--muted);">ABS-ISTI · 1 mm</span>''' + seg("A") + '''
          </div>
          <div style="border-top: 1px solid var(--line2); padding-top: 10px; display: flex; flex-direction: column; gap: 6px;">
            <div class="lbl">Trake ovog materijala</div>
            <div style="display: flex; justify-content: space-between; font-size: 13px;"><span><span class="e A" style="width: 18px; height: 18px; font-size: 10px;">A</span> ABS-ISTI</span><span class="num" style="font-size: 12px; color: var(--muted);">TR000168 · 1 mm ▾</span></div>
            <div style="display: flex; justify-content: space-between; font-size: 13px;"><span><span class="e M" style="width: 18px; height: 18px; font-size: 10px;">M</span> MEL-ISTI</span><span class="num" style="font-size: 12px; color: var(--muted);">TR000017 · 0,5 mm</span></div>
            <div style="display: flex; justify-content: space-between; font-size: 13px;"><span style="color: var(--muted);">+ druga boja…</span><span class="num" style="font-size: 12px; color: var(--muted);">traži ident</span></div>
          </div>
          <div style="border-top: 1px solid var(--line2); padding-top: 10px; font-size: 12px; color: var(--muted);">0,45 m² · rubovi 2,19 m · CNC: ne · 2 prolaza: ne</div>
          <button class="btn pri" style="width: 100%; padding: 10px;">Potvrdi element <span class="kbd" style="margin-left: 6px; color: var(--ink);">↵</span></button>
        </div>
      </div>
    </div>

    <div class="foot">
      <div class="kpi"><b class="num">53 · 174</b><span>stavki · kom</span></div>
      <div class="kpi"><b class="num">50,37 m²</b><span>dijelova</span></div>
      <div class="kpi"><b class="num">208,2 + 21,8 m</b><span>ABS · MEL (PW metri)</span></div>
      <div class="kpi"><b class="num">10 pl. · 57,96 m²</b><span>za obračun</span></div>
      <div style="flex: 1;"></div>
      <span style="font-size: 13px;"><span class="dot"></span>Provjere: sve u redu</span>
      <button class="btn pri">Dalje: pila / nesting →</button>
    </div>
  </div>
</div>'''

html = (
    "<!doctype html>\n<html>\n<head>\n  <meta charset=\"utf-8\">\n  <script src=\"./support.js\"></script>\n</head>\n<body>\n<x-dc>\n<helmet>\n  <title>Production Hub — Unos naloga, varijanta C</title>\n  %s\n  <style>%s</style>\n</helmet>\n"
    '<div style="width: 1440px; min-height: 980px; background: #F6F4EF;">\n%s\n</div>\n</x-dc>\n</body>\n</html>\n' % (FONTS, CSS, body)
)
open("MainC.dc.html", "w", encoding="utf-8").write(html)
print("MainC.dc.html", len(html))
