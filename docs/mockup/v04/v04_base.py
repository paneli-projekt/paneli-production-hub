# -*- coding: utf-8 -*-
"""Mockup v0.4 — zajednički dio: paleta, CSS, ljuska ekrana, daska, ikone, mini-sheme, dijalog.
v0.4 (12. 9. 2026.): lijeva traka dobiva „Nabava“ (modul nabava, D-42); kartica za male ekrane (dijalog, vremenska crta);
na ekranima nema oznaka odluka (D-xx) ni riječi „AI“ — strip_dxx() to jamči pri zapisu.
Dizajn = varijanta D (D-39): raspored iz C, unos kroz dasku iz B / PPNEST-a, zaglavlje iz B (antracit + logo).
Igorova dopuna 12. 9.: boje SREDIŠNJEG dijela ekrana u nijansama varijante C (papir, mahovina zelena kao naglasak,
ABS plavo / MEL jantar), zaglavlje ostaje nepromijenjeno."""

# zaglavlje (varijanta B / D) — nepromijenjeno
ANT = "#5A5F64"; OR = "#F37A20"
# sredina — nijanse varijante C
INK = "#1C2A33"; MUTED = "#66727C"; LINE = "#DDD8CF"; LINE2 = "#EBE7DF"; PAPER = "#F6F4EF"; SURF = "#FFFFFF"
ACC = "#2E6B57"; ACC_SOFT = "#E3EFE9"; ABS = "#2F5D8C"; ABS_SOFT = "#E4ECF5"; MEL = "#B7791F"; MEL_SOFT = "#F6E7C9"
WARN = "#B7791F"; CRIT = "#A63D2F"; CRIT_SOFT = "#F5E1DC"; WOOD = "#D8B892"

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=IBM+Plex+Mono:wght@500;600&amp;family=Barlow+Condensed:wght@700&amp;display=swap">'

CSS = """
:root{--ink:%(ink)s;--muted:%(muted)s;--line:%(line)s;--line2:%(line2)s;--paper:%(paper)s;--surf:%(surf)s;--ant:%(ant)s;--or:%(orange)s;
--acc:%(acc)s;--acc-soft:%(accsoft)s;--abs:%(abs)s;--abs-soft:%(abssoft)s;--mel:%(mel)s;--mel-soft:%(melsoft)s;--warn:%(warn)s;--crit:%(crit)s;--crit-soft:%(critsoft)s}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Inter",system-ui,-apple-system,"Segoe UI",sans-serif;font-size:14px;line-height:1.4}
a{color:var(--acc);text-decoration:underline;text-decoration-color:var(--acc)}
.mono{font-family:"IBM Plex Mono",ui-monospace,Consolas,monospace;font-variant-numeric:tabular-nums}
.num{font-variant-numeric:tabular-nums}
/* zaglavlje — varijanta D, nepromijenjeno */
.top{height:54px;background:var(--ant);color:#fff;display:flex;align-items:center;gap:12px;padding:0 16px;flex:none}
.top .brand{display:flex;align-items:center;gap:10px;margin-right:6px}
.top .brand b{font-size:18px;font-weight:800;white-space:nowrap} .top .brand .us{color:var(--or)}
.top .crumb{color:#E1E4E7;font-size:13px;white-space:nowrap;flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis} .top .crumb b{color:#fff;font-size:15px}
.pill{display:inline-flex;align-items:center;gap:6px;border:1px solid #8A9096;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:600;color:#E1E4E7;white-space:nowrap}
.pill.on{background:#fff;border-color:#fff;color:var(--ink)}
.pill.done{border-color:#C9E3D3;color:#C9E3D3}
.tbtn{background:transparent;border:1px solid #8A9096;border-radius:6px;padding:6px 12px;font-weight:600;font-size:13px;color:#fff;white-space:nowrap}
.tbtn.pri{background:#fff;border-color:#fff;color:var(--ink)}
/* lijeva traka */
.rail{width:76px;background:var(--surf);border-right:1px solid var(--line);display:flex;flex-direction:column;align-items:center;padding:12px 0;gap:6px;flex:none}
.rail .it{width:62px;padding:8px 0 6px;border-radius:8px;display:flex;flex-direction:column;align-items:center;gap:4px;font-size:10.5px;font-weight:600;color:var(--muted)}
.rail .it.on{background:var(--acc-soft);color:var(--acc)}
.rail .it svg{width:20px;height:20px}
/* sredina */
.btn{background:var(--surf);border:1px solid var(--line);border-radius:6px;padding:7px 12px;font-weight:600;font-size:13px;color:var(--ink);white-space:nowrap}
.btn.pri{background:var(--acc);border-color:var(--acc);color:#fff}
.btn.ghost{border-style:dashed;color:var(--muted);font-weight:500}
.btn.sm{padding:5px 9px;font-size:12px}
.lbl{font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);font-weight:700}
.pane{background:var(--surf);border:1px solid var(--line);border-radius:10px;display:flex;flex-direction:column;min-height:0}
.pane .hd{padding:9px 14px;border-bottom:1px solid var(--line2);display:flex;align-items:center;gap:8px}
.pane .bd{padding:8px 14px;display:flex;flex-direction:column;gap:6px;font-size:13px}
.mat{padding:9px 14px;border-bottom:1px solid var(--line2);display:flex;flex-direction:column;gap:2px}
.mat.on{background:var(--acc-soft);box-shadow:inset 3px 0 0 var(--acc)}
.mat b{font-size:13px} .mat .m{font-size:12px;color:var(--muted)}
.tag{display:inline-block;white-space:nowrap;font-size:10.5px;font-weight:700;letter-spacing:.03em;padding:1px 6px;border-radius:4px;background:var(--line2);color:var(--muted)}
.tag.nest{background:#DAEBEC;color:#1E6E76} .tag.pila{background:#F0E4D6;color:#7A5230} .tag.warn{background:var(--mel-soft);color:#7A4E10} .tag.ok{background:var(--acc-soft);color:var(--acc)}
.tag.crit{background:var(--crit-soft);color:var(--crit)} .tag.abs{background:var(--abs-soft);color:var(--abs)} .tag.info{background:#E8ECF0;color:#3D4A55}
table{border-collapse:collapse;width:100%%}
th{font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);white-space:nowrap;font-weight:700}
td{padding:5px 10px;border-bottom:1px solid var(--line2);vertical-align:middle;white-space:nowrap}
td.r,th.r{text-align:right}
tr.sel td{background:var(--acc-soft)}
tr.grp td{background:#E9ECEF;border-top:1px solid #D3D9DE;border-bottom:1px solid #D3D9DE;font-weight:700;font-size:12.5px;padding:6px 10px}
.inp{background:var(--surf);border:1px solid var(--line);border-radius:6px;padding:7px 10px;min-height:38px;display:flex;align-items:center;gap:8px;font-size:14px}
.inp.big{font-size:22px;font-weight:700;justify-content:flex-end;font-variant-numeric:tabular-nums}
.inp.foc{border-color:var(--acc);box-shadow:0 0 0 3px var(--acc-soft)}
.inp .ph{color:#9AA0A6;font-size:13px}
.kbd{display:inline-block;min-width:18px;text-align:center;border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;padding:0 5px;font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;background:var(--surf);color:var(--ink)}
.foot{height:58px;background:var(--surf);border-top:1px solid var(--line);display:flex;align-items:center;gap:24px;padding:0 20px;flex:none}
.kpi b{font-size:18px;font-weight:700;white-space:nowrap} .kpi span{display:block;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);font-weight:700;white-space:nowrap}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%%;margin-right:6px;vertical-align:middle;background:var(--acc)}
.dot.warn{background:var(--warn)} .dot.crit{background:var(--crit)} .dot.info{background:#8A9096} .dot.abs{background:var(--abs)} .dot.mel{background:var(--mel)}
.addr{display:inline-block;background:#F5C518;color:#1B1706;border:1px solid #8A6D02;border-radius:2px;font-family:"Barlow Condensed","Arial Narrow",sans-serif;font-weight:700;letter-spacing:.06em;padding:0 8px;font-size:14px;line-height:19px;white-space:nowrap}
.chip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:4px 11px;font-size:12px;font-weight:600;color:var(--muted);background:var(--surf);white-space:nowrap}
.chip.on{background:var(--acc);border-color:var(--acc);color:#fff}
.chip .n{font-family:"IBM Plex Mono",monospace;font-size:11px;opacity:.8}
.radio{display:inline-flex;align-items:center;gap:6px;font-weight:600;font-size:13px} .radio i{width:14px;height:14px;border-radius:50%%;border:1.5px solid var(--line);display:inline-block;background:#fff}
.radio i.on{border-color:var(--acc);box-shadow:inset 0 0 0 3.5px var(--acc)}
.step{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);white-space:nowrap} .step b{color:var(--ink)} .step.wrap{white-space:normal;align-items:flex-start;line-height:1.35} .step.wrap .s{flex:none;margin-top:1px}
.step .s{width:20px;height:20px;border-radius:50%%;border:1.5px solid var(--line);display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;background:#fff}
.step .s.done{background:var(--acc);border-color:var(--acc);color:#fff} .step .s.now{border-color:var(--acc);color:var(--acc);box-shadow:0 0 0 3px var(--acc-soft)}
.thumb{display:flex;flex-direction:column;gap:3px;align-items:center;font-size:11px;color:var(--muted);white-space:nowrap}
.thumb svg{display:block;border:1px solid var(--line);border-radius:3px;background:#fff}
.note{font-size:12px;color:var(--muted)}
""" % dict(ink=INK, muted=MUTED, line=LINE, line2=LINE2, paper=PAPER, surf=SURF, ant=ANT, orange=OR, acc=ACC, accsoft=ACC_SOFT,
           abs=ABS, abssoft=ABS_SOFT, mel=MEL, melsoft=MEL_SOFT, warn=WARN, crit=CRIT, critsoft=CRIT_SOFT, wood=WOOD)


def ico(name):
    p = {
        "nalozi": '<path d="M5 3h10l4 4v14H5z"/><path d="M15 3v4h4M8 12h8M8 16h8"/>',
        "sifr": '<path d="M4 6h16M4 12h16M4 18h10"/>',
        "sklad": '<path d="M3 9 12 4l9 5v11H3z"/><path d="M9 20v-7h6v7"/>',
        "obr": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 11h8M8 15h5"/>',
        "post": '<circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.3.9a7 7 0 0 0-1.7-1L14.5 3h-5l-.4 2.5a7 7 0 0 0-1.7 1L5.1 5.6l-2 3.4L5.1 10.5a7 7 0 0 0 0 2L3.1 14l2 3.4 2.3-.9a7 7 0 0 0 1.7 1l.4 2.5h5l.4-2.5a7 7 0 0 0 1.7-1l2.3.9 2-3.4-2-1.5c.1-.3.1-.7.1-1z"/>',
        "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
        "nabava": '<path d="M4 8h16v12H4z"/><path d="M4 8l2.5-4h11L20 8M12 11v6M9 14h6"/>',
    }[name]
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % p


STEPS = ["1 Unos", "2 Ponuda", "3 Skladište", "4 Pila / nesting"]


def pills(step):
    """koraci naloga u zaglavlju (D-35): 1 Unos → 2 Ponuda (čeka kupca) → 3 Skladište → 4 Pila / nesting; proizvodnja je izvan Huba"""
    out = []
    for i, s in enumerate(STEPS):
        cls = "on" if i == step else ("done" if i < step else "")
        out.append('<span class="pill %s">%s</span>' % (cls, s))
    return "".join(out)


def rail(active, user="IV"):
    items = [("nalozi", "Nalozi"), ("sifr", "Šifrarnici"), ("sklad", "Skladište"), ("nabava", "Nabava"), ("obr", "Obračun"), ("post", "Postavke")]
    s = ['<nav class="rail">']
    for k, n in items:
        s.append('<div class="it%s">%s%s</div>' % (" on" if k == active else "", ico(k), n))
    s.append('<div style="flex: 1;"></div>')
    s.append('<div style="width: 36px; height: 36px; border-radius: 50%%; background: var(--ant); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px;">%s</div>' % user)
    s.append("</nav>")
    return "".join(s)


def top(crumb, step=None, actions=""):
    return ('<div class="top">'
            '<div class="brand"><img src="logo-mark.png" alt="" style="height: 34px; width: auto; display: block;"><b>Paneli<span class="us">_</span> Production Hub</b></div>'
            '<div style="width: 1px; height: 26px; background: #8A9096; flex: none;"></div>'
            '<div class="crumb">%s</div>%s%s</div>'
            % (crumb, pills(step) if step is not None else "", actions))


ORDER_CRUMB = 'Nalozi / <b>HUMER_OMIS_2823</b> · Humer · 18.08.2026 · ponuda 26-010-002823'
ORDER_CRUMB_HUB = 'Nalozi / <b>HUMER_OMIS_2823</b> · Humer · 18.08.2026 · ponuda 2026-02823 · v3'


def screen(title, crumb, step, actions, rail_active, grid_cols, columns, foot, user="IV"):
    """cijeli ekran 1440×980: zaglavlje, lijeva traka, sredina (grid), podnožje"""
    body = ('<div style="display: flex; flex-direction: column; height: 980px;">%s'
            '<div style="flex: 1; min-height: 0; display: flex;">%s'
            '<div style="flex: 1; min-width: 0; display: grid; grid-template-columns: %s; gap: 12px; padding: 12px 14px;">%s</div>'
            '</div><div class="foot">%s</div></div>'
            % (top(crumb, step, actions), rail(rail_active, user), grid_cols, "".join(columns), foot))
    return (
        "<!doctype html>\n<html>\n<head>\n  <meta charset=\"utf-8\">\n  <script src=\"./support.js\"></script>\n</head>\n<body>\n<x-dc>\n<helmet>\n  <title>%s</title>\n  %s\n  <style>%s</style>\n</helmet>\n"
        '<div style="width: 1440px; min-height: 980px; background: %s;">\n%s\n</div>\n</x-dc>\n</body>\n</html>\n' % (title, FONTS, CSS, PAPER, body)
    )


# ---------------------------------------------------------------- daska (unos elementa) — rubovi: A = ABS plavo, M = MEL jantar
def ecol(v):
    return ABS if v == "A" else (MEL if v == "M" else LINE2)


def rubv(l, d, g, dol):
    """mini-daska u retku tablice"""
    return (
        '<svg width="24" height="30" viewBox="0 0 24 30" style="display: block;"><rect x="5" y="3" width="14" height="24" fill="#fff" stroke="%s"/>'
        '<line x1="5" y1="3" x2="5" y2="27" stroke="%s" stroke-width="%s"/><line x1="19" y1="3" x2="19" y2="27" stroke="%s" stroke-width="%s"/>'
        '<line x1="5" y1="3" x2="19" y2="3" stroke="%s" stroke-width="%s"/><line x1="5" y1="27" x2="19" y2="27" stroke="%s" stroke-width="%s"/></svg>'
        % (LINE2, ecol(l), "3" if l else "1", ecol(d), "3" if d else "1", ecol(g), "3" if g else "1", ecol(dol), "3" if dol else "1")
    )


def toggle(x, y, letter, on):
    col = ABS if letter == "A" else MEL
    return ('<rect x="%d" y="%d" width="20" height="20" rx="4" fill="%s" stroke="%s"/>'
            '<text x="%d" y="%d" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="12" fill="%s">%s</text>'
            % (x, y, col if on else "#fff", col if on else LINE, x + 10, y + 14, "#fff" if on else MUTED, letter))


def board(L, W, l, d, g, dol, names):
    """okomita daska s mjerama i parom prekidača M / A uz svaki rub (klik mišem, D-36)"""
    bx, by, bw, bh = 200, 52, 120, 210
    cx = bx + bw // 2; cy = by + bh // 2
    mono = 'font-family="IBM Plex Mono, monospace" font-size="11"'
    s = ['<svg width="520" height="326" viewBox="0 0 520 326" style="display: block;">']
    s.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#FBFAF6" stroke="%s"/>' % (bx, by, bw, bh, LINE))
    for x1, y1, x2, y2, v in ((bx, by, bx, by + bh, l), (bx + bw, by, bx + bw, by + bh, d), (bx, by, bx + bw, by, g), (bx, by + bh, bx + bw, by + bh, dol)):
        s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (x1, y1, x2, y2, ecol(v), "5" if v else "1"))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="%s">2. MJERA</text>' % (cx, by - 36, MUTED))
    s.append('<rect x="%d" y="%d" width="56" height="22" rx="4" fill="#fff" stroke="%s"/>' % (cx - 28, by - 30, LINE))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="15" fill="%s">%d</text>' % (cx, by - 14, INK, W))
    s.append(toggle(cx - 80, by - 31, "M", g == "M")); s.append(toggle(cx - 57, by - 31, "A", g == "A"))
    s.append('<text x="%d" y="%d" %s fill="%s">%s</text>' % (cx + 36, by - 15, mono, INK if g else MUTED, names[g] or "—"))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="%s">1. MJERA (GOD)</text>' % (bx - 60, cy - 26, MUTED))
    s.append('<rect x="%d" y="%d" width="56" height="22" rx="4" fill="#fff" stroke="%s"/>' % (bx - 88, cy - 20, LINE))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Inter, sans-serif" font-weight="700" font-size="15" fill="%s">%d</text>' % (bx - 60, cy - 4, INK, L))
    s.append(toggle(bx - 92, cy + 12, "M", l == "M")); s.append(toggle(bx - 69, cy + 12, "A", l == "A"))
    s.append('<text x="%d" y="%d" text-anchor="end" %s fill="%s">%s</text>' % (bx - 12, cy + 50, mono, INK if l else MUTED, names[l] or "—"))
    s.append(toggle(bx + bw + 12, cy + 12, "M", d == "M")); s.append(toggle(bx + bw + 35, cy + 12, "A", d == "A"))
    s.append('<text x="%d" y="%d" %s fill="%s">%s</text>' % (bx + bw + 12, cy + 50, mono, INK if d else MUTED, names[d] or "—"))
    s.append(toggle(cx - 23, by + bh + 12, "M", dol == "M")); s.append(toggle(cx, by + bh + 12, "A", dol == "A"))
    s.append('<text x="%d" y="%d" %s fill="%s">%s</text>' % (cx + 28, by + bh + 27, mono, INK if dol else MUTED, names[dol] or "—"))
    s.append('<text x="%d" y="%d" font-family="Inter, sans-serif" font-size="10" fill="%s">klik na M ili A uz rub · M = MEL-ISTI 0,5 mm · A = ABS-ISTI 1 mm ili traka druge boje</text>' % (bx - 92, by + bh + 46, MUTED))
    s.append('<text x="%d" y="%d" font-family="Inter, sans-serif" font-size="10" fill="%s">tanki rub = bez trake · god se nasljeđuje iz Winstorea (gašenje uz potvrdu)</text>' % (bx - 92, by + bh + 58, MUTED))
    s.append("</svg>")
    return "".join(s)


# ---------------------------------------------------------------- mini-sheme ploča (ilustracija krojne sheme / nestinga)
def sheet_svg(seed, util, w=132, h=98, fill=None, label=None):
    """deterministična ilustracija sheme: trake (stupci) s pravokutnicima; util = udio iskorištenja 0–1"""
    fill = fill or ABS_SOFT
    rnd = (seed * 9301 + 49297) % 233280
    def nxt(lo, hi):
        nonlocal rnd
        rnd = (rnd * 9301 + 49297) % 233280
        return lo + (hi - lo) * rnd / 233280.0
    s = ['<svg width="%d" height="%d" viewBox="0 0 %d %d">' % (w, h, w, h), '<rect x="0" y="0" width="%d" height="%d" fill="#F8F6F1"/>' % (w, h)]
    x = 3.0
    area = 0.0; total = (w - 6) * (h - 6)
    while x < w - 12:
        cw = min(nxt(18, 42), w - 3 - x)
        y = 3.0
        while y < h - 10 and area / total < util:
            ch = min(nxt(10, 34), h - 3 - y)
            s.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="%s" stroke-width="0.8"/>' % (x, y, cw - 1.2, ch - 1.2, fill, ABS if fill == ABS_SOFT else "#8C7A63"))
            area += cw * ch
            y += ch
        x += cw
    s.append("</svg>")
    return "".join(s)


def thumb(seed, util, caption, fill=None, w=132, h=98):
    return '<div class="thumb">%s<span>%s</span></div>' % (sheet_svg(seed, util, w, h, fill), caption)


def steps_bar(now):
    """tok naloga (D-35) kao mali prikaz koraka: 0 Unos, 1 Ponuda, 2 Potvrđeno, 3 Skladište, 4 Pila/nesting, 5 Proizvodnja, 6 Zatvoren"""
    names = ["Unos", "Ponuda", "Potvrđeno", "Skladište", "Pila / nesting", "Proizvodnja", "Zatvoren"]
    out = []
    for i, n in enumerate(names):
        cls = "done" if i < now else ("now" if i == now else "")
        out.append('<span class="step"><span class="s %s">%s</span>%s</span>' % (cls, "✓" if i < now else str(i + 1), ("<b>%s</b>" % n) if i == now else n))
    return '<div style="display: flex; align-items: center; gap: 14px;">%s</div>' % "".join(out)


def card(title, w, h, body, pad="0"):
    """mali artboard: kartica (dijalog, panel na klik) na papirnatoj pozadini, isti CSS kao ekrani"""
    return (
        "<!doctype html>\n<html>\n<head>\n  <meta charset=\"utf-8\">\n  <script src=\"./support.js\"></script>\n</head>\n<body>\n<x-dc>\n<helmet>\n  <title>%s</title>\n  %s\n  <style>%s</style>\n</helmet>\n"
        '<div style="width: %dpx; min-height: %dpx; background: %s; padding: %s;">\n%s\n</div>\n</x-dc>\n</body>\n</html>\n' % (title, FONTS, CSS, w, h, PAPER, pad, body)
    )


import re as _re


def strip_dxx(html):
    """na ekranima nema oznaka odluka (D-xx / I-xx) — ostaju u dokumentima i bilješkama na platnu"""
    html = html.replace(" po D-20:", ":").replace(" po D-37:", ":")
    html = _re.sub(r"\s*\((?:D|I)-\d{2}[a-z]?(?:\s*[,/]\s*(?:D|I)-\d{2}[a-z]?)*\)", "", html)
    return html
