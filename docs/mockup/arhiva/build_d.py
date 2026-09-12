# -*- coding: utf-8 -*-
"""Varijanta D — HIBRID: raspored iz C (jedan ekran 1440×980, lijeva traka, materijali lijevo, desni stupac uvijek vidljiv)
+ unos kroz dasku kao u B / PPNEST-u (mjere, kom, napomena, MELAMIN/ABS izbornici, daska s M/A prekidačima po rubu, Prihvati = Enter)
+ brand iz B (logo u jednom retku, antracit #5A5F64 zaglavlje i gumbi, narančasta samo kao tanki naglasak, Inter)."""

INK = "#1F2326"; MUTED = "#5E646A"; LINE = "#CDC9C2"; LINE2 = "#E4E1DB"; PAPER = "#EDEBE7"; SURF = "#FFFFFF"
ANT = "#5A5F64"; ANT_SOFT = "#E7E4DE"; OR = "#F37A20"; OK = "#1B6E48"; WARN = "#9A5B06"; WOOD = "#D8B892"

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=IBM+Plex+Mono:wght@500;600&amp;display=swap">'

CSS = """
:root{--ink:%(ink)s;--muted:%(muted)s;--line:%(line)s;--line2:%(line2)s;--paper:%(paper)s;--surf:%(surf)s;--ant:%(ant)s;--ant-soft:%(antsoft)s;--or:%(orange)s;--ok:%(ok)s;--warn:%(warn)s}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Inter",system-ui,-apple-system,"Segoe UI",sans-serif;font-size:14px;line-height:1.4}
a{color:var(--ink);text-decoration:underline;text-decoration-color:var(--or)}
.mono{font-family:"IBM Plex Mono",ui-monospace,Consolas,monospace;font-variant-numeric:tabular-nums}
.top{height:54px;background:var(--ant);color:#fff;display:flex;align-items:center;gap:12px;padding:0 16px}
.top .brand{display:flex;align-items:center;gap:10px;margin-right:6px}
.top .brand b{font-size:18px;font-weight:800;white-space:nowrap} .top .brand .us{color:var(--or)}
.top .crumb{color:#E1E4E7;font-size:13px;white-space:nowrap;flex:1 1 auto} .top .crumb b{color:#fff;font-size:15px}
.pill{display:inline-flex;align-items:center;gap:6px;border:1px solid #8A9096;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:600;color:#E1E4E7;white-space:nowrap}
.pill.on{background:#fff;border-color:#fff;color:var(--ink)}
.pill.done{border-color:#C9E3D3;color:#C9E3D3}
.tbtn{background:transparent;border:1px solid #8A9096;border-radius:6px;padding:6px 12px;font-weight:600;font-size:13px;color:#fff;white-space:nowrap}
.tbtn.pri{background:#fff;border-color:#fff;color:var(--ink)}
.rail{width:76px;background:var(--surf);border-right:1px solid var(--line);display:flex;flex-direction:column;align-items:center;padding:12px 0;gap:6px}
.rail .it{width:62px;padding:8px 0 6px;border-radius:8px;display:flex;flex-direction:column;align-items:center;gap:4px;font-size:10.5px;font-weight:600;color:var(--muted)}
.rail .it.on{background:var(--ant);color:#fff}
.rail .it svg{width:20px;height:20px}
.btn{background:var(--surf);border:1px solid var(--line);border-radius:6px;padding:7px 12px;font-weight:600;font-size:13px;color:var(--ink);white-space:nowrap}
.btn.pri{background:var(--ant);border-color:var(--ant);color:#fff}
.btn.ghost{border-style:dashed;color:var(--muted);font-weight:500}
.lbl{font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);font-weight:700}
.pane{background:var(--surf);border:1px solid var(--line);border-radius:10px;display:flex;flex-direction:column;min-height:0}
.pane .hd{padding:9px 14px;border-bottom:1px solid var(--line2);display:flex;align-items:center;gap:8px}
.mat{padding:9px 14px;border-bottom:1px solid var(--line2);display:flex;flex-direction:column;gap:2px}
.mat.on{background:var(--ant-soft);box-shadow:inset 3px 0 0 var(--ant)}
.mat b{font-size:13px} .mat .m{font-size:12px;color:var(--muted)}
.tag{display:inline-block;white-space:nowrap;font-size:10.5px;font-weight:700;letter-spacing:.03em;padding:1px 6px;border-radius:4px;background:var(--line2);color:var(--muted)}
.tag.nest{background:var(--ant);color:#fff} .tag.pila{background:#8A6D4E;color:#fff} .tag.warn{background:#FBEBD0;color:#7A4E10} .tag.ok{background:#DDEFE5;color:var(--ok)}
table{border-collapse:collapse;width:100%%}
th{font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);white-space:nowrap;font-weight:700}
td{padding:5px 10px;border-bottom:1px solid var(--line2);vertical-align:middle;white-space:nowrap}
td.r,th.r{text-align:right}
tr.sel td{background:var(--ant-soft)}
.inp{background:var(--surf);border:1px solid var(--line);border-radius:6px;padding:7px 10px;min-height:38px;display:flex;align-items:center;gap:8px;font-size:14px}
.inp.big{font-size:22px;font-weight:700;justify-content:flex-end;font-variant-numeric:tabular-nums}
.inp.foc{border-color:var(--ant);box-shadow:0 0 0 3px var(--ant-soft)}
.inp .ph{color:#9AA0A6;font-size:13px}
.kbd{display:inline-block;min-width:18px;text-align:center;border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;padding:0 5px;font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;background:var(--surf);color:var(--ink)}
.foot{height:58px;background:var(--surf);border-top:1px solid var(--line);display:flex;align-items:center;gap:24px;padding:0 20px}
.kpi b{font-size:18px;font-weight:700;white-space:nowrap} .kpi span{display:block;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);font-weight:700;white-space:nowrap}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%%;margin-right:6px;vertical-align:middle;background:var(--ok)}
.dot.warn{background:var(--warn)}
.addr{display:inline-block;background:%(wood)s;color:#1B1206;border-radius:3px;padding:0 7px;font-weight:700;font-size:12px}
""" % dict(ink=INK, muted=MUTED, line=LINE, line2=LINE2, paper=PAPER, surf=SURF, ant=ANT, antsoft=ANT_SOFT, orange=OR, ok=OK, warn=WARN, wood=WOOD)


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
    (27, 1050, 140, 1, "M", "M", "M", "M", "1050X120", 2), (37, 1030, 340, 14, "A", "A", "A", "A", "RASTER 150 64-64 150", 1),
]
BAND = {"A": "1/22 JELA TAVERNA", "M": "MEL-ISTI", "": ""}


def ecol(v):
    return OK if v == "A" else (WARN if v == "M" else LINE2)


def rubv(l, d, g, dol):
    return (
        '<svg width="24" height="30" viewBox="0 0 24 30" style="display: block;"><rect x="5" y="3" width="14" height="24" fill="#fff" stroke="%s"/>'
        '<line x1="5" y1="3" x2="5" y2="27" stroke="%s" stroke-width="%s"/><line x1="19" y1="3" x2="19" y2="27" stroke="%s" stroke-width="%s"/>'
        '<line x1="5" y1="3" x2="19" y2="3" stroke="%s" stroke-width="%s"/><line x1="5" y1="27" x2="19" y2="27" stroke="%s" stroke-width="%s"/></svg>'
        % (LINE2, ecol(l), "3" if l else "1", ecol(d), "3" if d else "1", ecol(g), "3" if g else "1", ecol(dol), "3" if dol else "1")
    )


def toggle(x, y, letter, on):
    return ('<rect x="%d" y="%d" width="20" height="20" rx="4" fill="%s" stroke="%s"/>'
            '<text x="%d" y="%d" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="12" fill="%s">%s</text>'
            % (x, y, ANT if on else "#fff", ANT if on else LINE, x + 10, y + 14, "#fff" if on else MUTED, letter))


def board(L, W, l, d, g, dol, names=None):
    names = names or BAND
    bx, by, bw, bh = 200, 52, 120, 210
    cx = bx + bw // 2; cy = by + bh // 2
    mono = 'font-family="IBM Plex Mono, monospace" font-size="11"'
    s = ['<svg width="520" height="318" viewBox="0 0 520 318" style="display: block;">']
    s.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#FBFAF6" stroke="%s"/>' % (bx, by, bw, bh, LINE))
    for x1, y1, x2, y2, v in ((bx, by, bx, by + bh, l), (bx + bw, by, bx + bw, by + bh, d), (bx, by, bx + bw, by, g), (bx, by + bh, bx + bw, by + bh, dol)):
        s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (x1, y1, x2, y2, ecol(v), "5" if v else "1"))
    # 2. mjera gore
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="%s">2. MJERA</text>' % (cx, by - 36, MUTED))
    s.append('<rect x="%d" y="%d" width="56" height="22" rx="4" fill="#fff" stroke="%s"/>' % (cx - 28, by - 30, LINE))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="15" fill="%s">%d</text>' % (cx, by - 14, INK, W))
    s.append(toggle(cx - 80, by - 31, "M", g == "M")); s.append(toggle(cx - 57, by - 31, "A", g == "A"))
    s.append('<text x="%d" y="%d" %s fill="%s">%s</text>' % (cx + 36, by - 15, mono, INK if g else MUTED, names[g] or "—"))
    # 1. mjera lijevo
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="%s">1. MJERA (GOD)</text>' % (bx - 60, cy - 26, MUTED))
    s.append('<rect x="%d" y="%d" width="56" height="22" rx="4" fill="#fff" stroke="%s"/>' % (bx - 88, cy - 20, LINE))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="15" fill="%s">%d</text>' % (bx - 60, cy - 4, INK, L))
    s.append(toggle(bx - 92, cy + 12, "M", l == "M")); s.append(toggle(bx - 69, cy + 12, "A", l == "A"))
    s.append('<text x="%d" y="%d" text-anchor="end" %s fill="%s">%s</text>' % (bx - 12, cy + 50, mono, INK if l else MUTED, names[l] or "—"))
    # desno
    s.append(toggle(bx + bw + 12, cy + 12, "M", d == "M")); s.append(toggle(bx + bw + 35, cy + 12, "A", d == "A"))
    s.append('<text x="%d" y="%d" %s fill="%s">%s</text>' % (bx + bw + 12, cy + 50, mono, INK if d else MUTED, names[d] or "—"))
    # dolje
    s.append(toggle(cx - 23, by + bh + 12, "M", dol == "M")); s.append(toggle(cx, by + bh + 12, "A", dol == "A"))
    s.append('<text x="%d" y="%d" %s fill="%s">%s</text>' % (cx + 28, by + bh + 27, mono, INK if dol else MUTED, names[dol] or "—"))
    s.append('<text x="%d" y="%d" font-family="Inter, sans-serif" font-size="10" fill="%s">M = MEL-ISTI 0,5 mm · A = ABS-ISTI 1 mm ili traka druge boje · tanki rub = bez trake</text>' % (bx - 92, by + bh + 50, MUTED))
    s.append("</svg>")
    return "".join(s)


rows = []
for rb, L, W, kom, l, d, g, dol, nap, pr in ELEMS:
    sel = ""
    bands = sorted({BAND[x] for x in (l, d, g, dol) if x})
    warn = ' <span class="tag warn">2 prolaza</span>' if pr == 2 else ""
    rows.append('<tr%s><td class="r" style="color: var(--muted);">%d</td><td class="r" style="font-weight: 700;">%d</td><td class="r" style="font-weight: 700;">%d</td><td class="r">%d</td>'
                '<td>%s</td><td class="mono" style="font-size: 12px;">%s</td><td style="color: var(--muted);">%s%s</td></tr>'
                % (sel, rb, L, W, kom, rubv(l, d, g, dol), " · ".join(bands) if bands else "—", nap, warn))

mats = [("IV BIJELI NK 18", "53 st. · 174 kom · 50,4 m²", "nesting", True), ("IV JELA TAVERNA 19", "35 · 48 · 25,6 m²", "nesting", False),
        ("MDF BIJELI 3", "22 · 27 · 16,1 m²", "pila", False), ("IV BIJELI NK 16", "10 · 28 · 4,6 m²", "pila", False),
        ("IV HRAST RELIEF CARDAMOM 19", "1 · 1 · 1,9 m²", "pila", False), ("RP BASANIT SAND", "2 · 2 · 4,99 m", "pila", False)]
matl = "".join('<div class="mat%s"><b>%s</b><span class="m">%s</span><span><span class="tag %s">%s</span></span></div>'
               % (" on" if on else "", n, m, "nest" if p == "nesting" else "pila", p) for n, m, p, on in mats)

body = '''
<div style="display: flex; flex-direction: column; height: 980px;">
  <div class="top">
    <div class="brand"><img src="logo-mark.png" alt="" style="height: 34px; width: auto; display: block;"><b>Paneli<span class="us">_</span> Production Hub</b></div>
    <div style="width: 1px; height: 26px; background: #8A9096;"></div>
    <div class="crumb" style="min-width: 0; overflow: hidden; text-overflow: ellipsis;">Nalozi / <b>HUMER_2823_OMIS</b> · Mario Humer · 18.08.2026 · ponuda 26-010-002823</div>
    <div style="flex: 1;"></div>
    <span class="pill on">1 Unos</span><span class="pill">2 Pila/nesting</span><span class="pill">3 Obračun</span>
    <button class="tbtn">Uvoz ▾</button><button class="tbtn">Zaglavlje</button><button class="tbtn pri">Spremi</button>
  </div>

  <div style="flex: 1; min-height: 0; display: flex;">
    <nav class="rail">
      <div class="it on">''' + ico("nalozi") + '''Nalozi</div>
      <div class="it">''' + ico("sifr") + '''Šifrarnici</div>
      <div class="it">''' + ico("sklad") + '''Skladište</div>
      <div class="it">''' + ico("obr") + '''Obračun</div>
      <div class="it">''' + ico("post") + '''Postavke</div>
      <div style="flex: 1;"></div>
      <div style="width: 36px; height: 36px; border-radius: 50%; background: var(--ant); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px;">IV</div>
    </nav>

    <div style="flex: 1; min-width: 0; display: grid; grid-template-columns: 236px minmax(0, 1fr) 292px; gap: 12px; padding: 12px 14px;">

      <div class="pane">
        <div class="hd"><span class="lbl">Materijali</span><span style="flex: 1;"></span><span class="mono" style="font-size: 12px; color: var(--muted);">6</span></div>
        ''' + matl + '''
        <div style="padding: 10px 14px;"><button class="btn ghost" style="width: 100%;">+ Materijal</button></div>
        <div style="flex: 1;"></div>
        <div style="padding: 9px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Nalog: 123 st. · 280 kom · 103,1 m²</div>
      </div>

      <div class="pane">
        <div class="hd">
          <div style="min-width: 0;"><div class="lbl">Aktivni materijal</div><div style="font-weight: 700; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">IV000090 · IVERAL BIJELI NK W908 ST2 18 MM <span style="color: var(--muted); font-weight: 500; font-size: 13px;">18 mm · bez goda · W908ST2-18</span></div></div>
          <div style="flex: 1;"></div><span class="tag nest">nesting</span><span class="tag">Winstore 13</span>
        </div>

        <div style="display: grid; grid-template-columns: 210px minmax(0, 1fr); gap: 14px; padding: 12px 14px; border-bottom: 1px solid var(--line2); background: #FBFAF6;">
          <div style="display: flex; flex-direction: column; gap: 8px;">
            <div><div class="lbl">1. mjera (god)</div><div class="inp big foc">564</div></div>
            <div><div class="lbl">2. mjera</div><div class="inp big">520</div></div>
            <div><div class="lbl">Kom</div><div class="inp big" style="width: 110px;">2</div></div>
            <div><div class="lbl">Napomena (etiketa + CSV)</div><div class="inp"><span class="ph">gotova mjera, CNC skica…</span></div></div>
            <div style="display: flex; gap: 6px; margin-top: 2px;"><button class="btn pri" style="flex: 1; padding: 9px;">Prihvati <span class="kbd" style="margin-left: 6px;">↵</span></button><button class="btn">Ažuriraj</button><button class="btn">Obriši</button></div>
          </div>
          <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
            <div style="display: flex; justify-content: space-between; width: 520px;">
              <div><div class="lbl" style="color: var(--warn);">MEL-ISTI · ista boja 0,5 mm</div><div class="inp" style="min-height: 32px; padding: 4px 10px; width: 200px;"><span class="mono">MEL-ISTI</span><span style="margin-left: auto; color: var(--muted);">▾</span></div></div>
              <div><div class="lbl" style="color: var(--ok);">ABS · zadano ABS-ISTI = 1 mm</div><div class="inp" style="min-height: 32px; padding: 4px 10px; width: 220px;"><span class="mono">ABS-ISTI</span><span style="margin-left: auto; color: var(--muted);">▾</span></div></div>
            </div>
            ''' + board(564, 520, "A", "", "A", "M", {"A": "ABS-ISTI", "M": "MEL-ISTI", "": ""}) + '''
          </div>
        </div>

        <div style="overflow: hidden;">
          <table>
            <thead><tr><th class="r">#</th><th class="r">1. mjera</th><th class="r">2. mjera</th><th class="r">kom</th><th>Rubovi</th><th>Traka</th><th>Napomena</th></tr></thead>
            <tbody>''' + "".join(rows) + '''
              <tr><td colspan="7" style="text-align: center; color: var(--muted); padding: 6px;">… još 43 retka (53 stavke, 174 kom) · <a href="#">sve</a></td></tr>
            </tbody>
          </table>
        </div>
        <div style="flex: 1;"></div>
        <div style="padding: 7px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted); display: flex; gap: 14px; flex-wrap: wrap;">
          <span><span class="kbd">Enter</span> prihvati (mjere ostaju — serije)</span><span><span class="kbd">Tab</span> sljedeće polje</span><span><span class="kbd">L</span><span class="kbd">D</span><span class="kbd">G</span><span class="kbd">B</span> rub: — → A → M</span><span><span class="kbd">↑</span><span class="kbd">↓</span> odaberi redak (daska ga prikaže)</span><span style="margin-left: auto; color: var(--ok);">primjer unosa: 564 × 520 · L i G = ABS-ISTI (1 mm) · B = MEL-ISTI (0,5) · D bez ruba</span>
        </div>
      </div>

      <div style="display: flex; flex-direction: column; gap: 12px; min-height: 0;">
        <div class="pane">
          <div class="hd"><span class="lbl">Trake ovog materijala</span></div>
          <div style="padding: 8px 14px; display: flex; flex-direction: column; gap: 7px; font-size: 13px;">
            <div style="display: flex; justify-content: space-between; gap: 8px;"><span><span class="dot" style="background: var(--warn);"></span><span class="mono">MEL-ISTI</span></span><span class="mono" style="font-size: 12px; color: var(--muted);">TR000017 · 0,5</span></div>
            <div style="display: flex; justify-content: space-between; gap: 8px;"><span><span class="dot"></span><span class="mono">ABS-ISTI</span></span><span class="mono" style="font-size: 12px; color: var(--muted);">TR000168 · 1 mm ▾</span></div>
            <div style="display: flex; justify-content: space-between; gap: 8px;"><span><span class="dot"></span><span class="mono">1/22 JELA TAVERNA</span></span><span class="mono" style="font-size: 12px; color: var(--muted);">TR001254 <span class="addr">R2-07-A</span></span></div>
            <div style="color: var(--muted);">+ druga boja… <span style="font-size: 12px;">traži ident</span></div>
          </div>
        </div>
        <div class="pane">
          <div class="hd"><span class="lbl">Materijal</span></div>
          <div style="padding: 8px 14px; display: flex; flex-direction: column; gap: 6px; font-size: 13px;">
            <div>Ploča <b>2800 × 2070</b> · glodalo <b>8D</b> · 2 prolaza</div>
            <div><span class="dot"></span>Winstore <b>13</b> ploča · restlovi 0</div>
            <div><span class="dot" style="background: var(--ant);"></span>Put: prijedlog <span class="tag nest">nesting</span> <span style="color: var(--muted);">(50 m² ≫ 1 ploča)</span></div>
            <div style="color: var(--muted); font-size: 12px;">Aliasi: IV BIJELI NK 18MM · IV_BIJELI_NK_18_MM</div>
          </div>
        </div>
        <div class="pane">
          <div class="hd"><span class="lbl">Ovaj materijal</span></div>
          <div style="padding: 8px 14px; display: flex; flex-direction: column; gap: 6px; font-size: 13px;">
            <div><b>53 st. · 174 kom</b> · 50,37 m²</div>
            <div>Trake: <b>208,2 m</b> ABS · <b>21,8 m</b> MEL (PW metri)</div>
            <div>Obračun: <b>10 pl. · 57,96 m²</b> (PW-metoda)</div>
            <div><span class="dot" style="background: var(--warn);"></span>2 elementa &lt; 200 mm → 2 prolaza</div>
          </div>
        </div>
        <div class="pane" style="flex: 1;">
          <div class="hd"><span class="lbl">Provjere</span><span style="flex: 1;"></span><span class="tag ok">sve u redu</span></div>
          <div style="padding: 8px 14px; display: flex; flex-direction: column; gap: 5px; font-size: 12.5px; color: var(--muted);">
            <div><span class="dot"></span>Winstore kod i ploča za sve materijale</div><div><span class="dot"></span>sve trake mapirane na TR ident</div><div><span class="dot"></span>0 elemenata s oznakom PROVJERI</div>
            <div><span class="dot warn"></span>IV JELA TAVERNA 19: Winstore 0 ploča</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="foot">
    <div class="kpi"><b>123 · 280</b><span>stavki · kom (nalog)</span></div>
    <div class="kpi"><b>103,1 m²</b><span>dijelova</span></div>
    <div class="kpi"><b>6</b><span>materijala · 2 nesting · 4 pila</span></div>
    <div style="flex: 1;"></div>
    <button class="btn">Spremi kao nacrt</button>
    <button class="btn pri">Dalje: pila / nesting →</button>
  </div>
</div>'''

html = (
    "<!doctype html>\n<html>\n<head>\n  <meta charset=\"utf-8\">\n  <script src=\"./support.js\"></script>\n</head>\n<body>\n<x-dc>\n<helmet>\n  <title>Paneli Production Hub — Unos naloga, varijanta D (hibrid)</title>\n  %s\n  <style>%s</style>\n</helmet>\n"
    '<div style="width: 1440px; min-height: 980px; background: #EDEBE7;">\n%s\n</div>\n</x-dc>\n</body>\n</html>\n' % (FONTS, CSS, body)
)
open("MainD.dc.html", "w", encoding="utf-8").write(html)
print("MainD.dc.html", len(html))
