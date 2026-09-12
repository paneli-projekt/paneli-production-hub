# -*- coding: utf-8 -*-
"""Zajednički dijelovi mockupa (stil = regal-traka, Paneli projekt)."""

FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&amp;family=IBM+Plex+Mono:wght@500;600&amp;family=IBM+Plex+Sans:wght@400;500;600&amp;display=swap">'

CSS = r"""
:root{--bg:#E7EAEE;--surface:#FFFFFF;--surface2:#F3F5F7;--ink:#14171A;--muted:#5A6470;--line:#C9D1D9;--line2:#E3E8ED;
 --accent:#17546E;--accent-ink:#FFFFFF;--accent-soft:#DCEAF1;--addr-bg:#F5C518;--addr-ink:#1B1706;--addr-line:#8A6D02;
 --ok:#1B6E48;--ok-soft:#DDEFE5;--warn:#9A5B06;--warn-soft:#FBEBD0;--crit:#A32017;--crit-soft:#F6DEDB;
 --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--cond:"Barlow Condensed","IBM Plex Sans",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,Consolas,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:14px;line-height:1.4}
a{color:var(--accent);text-decoration:none} a:hover{color:#0f3a4d;text-decoration:underline}
button,input,select{font:inherit;color:inherit}
.top{background:var(--surface);border-bottom:1px solid var(--line)}
.topin{padding:10px 24px;display:flex;align-items:center;gap:18px;flex-wrap:nowrap}
.brand{display:flex;align-items:baseline;gap:10px;margin-right:auto;flex:none}
.brand b{font-family:var(--cond);font-weight:700;font-size:26px;letter-spacing:.02em;text-transform:uppercase;white-space:nowrap}
.brand span{font-size:12px;color:var(--muted);letter-spacing:.09em;text-transform:uppercase;white-space:nowrap}
.tabs{display:flex;gap:6px;flex:none}
.tab{background:transparent;border:1px solid transparent;border-radius:3px;padding:8px 12px;font-family:var(--cond);font-size:17px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;cursor:pointer;color:var(--muted)}
.tab[aria-current="page"]{background:var(--accent);color:var(--accent-ink)}
.user{font-size:12px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase;border:1px solid var(--line);border-radius:3px;padding:6px 10px;white-space:nowrap}
.ostrip{background:var(--surface);border-bottom:1px solid var(--line)}
.oin{padding:10px 24px;display:flex;align-items:center;gap:18px;flex-wrap:nowrap}
.back{font-size:13px;color:var(--muted);white-space:nowrap}
.oname{display:flex;flex-direction:column;gap:2px;flex:none}
.oname b{font-family:var(--cond);font-size:24px;font-weight:700;letter-spacing:.02em;line-height:1.05}
.oname span{font-size:12px;color:var(--muted);white-space:nowrap}
.steps{display:flex;gap:5px;list-style:none;margin:0 auto;padding:0;flex:none}
.steps li{font-family:var(--cond);font-size:13px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:3px 10px;background:var(--surface);white-space:nowrap}
.steps li.done{border-color:var(--ok);color:var(--ok);background:var(--ok-soft)}
.steps li.cur{border-color:var(--accent);color:var(--accent-ink);background:var(--accent)}
.subtabs{display:flex;gap:4px;padding:0 24px;background:var(--surface);border-bottom:1px solid var(--line)}
.subtab{padding:10px 16px;font-family:var(--cond);font-size:17px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);border-bottom:3px solid transparent;margin-bottom:-1px}
.subtab.on{color:var(--accent);border-bottom-color:var(--accent)}
.wrap{padding:18px 24px 28px}
h2{font-family:var(--cond);font-size:24px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;margin:0;white-space:nowrap}
h3{font-family:var(--cond);font-size:17px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;margin:0 0 10px;color:var(--muted)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:4px;padding:14px 16px}
.row{display:flex;gap:10px;align-items:center}
.btn{background:var(--surface);border:1px solid var(--line);border-radius:3px;padding:8px 14px;font-weight:500;cursor:pointer;white-space:nowrap}
.btn.pri{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:600}
.btn.sm{padding:5px 10px;font-size:13px}
.btn.ghost{border-style:dashed;color:var(--muted)}
.inp{background:var(--surface);border:1px solid var(--line);border-radius:3px;padding:8px 10px;width:100%;min-height:36px;display:flex;align-items:center;gap:8px}
.inp.ro{background:var(--surface2);color:var(--muted)}
.inp .ph{color:#8b95a1}
.inp.big{font-family:var(--cond);font-size:22px;font-weight:600;letter-spacing:.02em;padding:6px 12px}
label.l{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:4px}
.fld{display:flex;flex-direction:column;gap:0}
.mono{font-family:var(--mono);font-size:.92em;letter-spacing:-.01em}
.muted{color:var(--muted)}
.note{font-size:13px;color:var(--muted)}
.tag{display:inline-block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;padding:2px 7px;border-radius:2px;background:var(--surface2);color:var(--muted);border:1px solid var(--line2);white-space:nowrap;font-weight:600}
.tag.acc{background:var(--accent-soft);color:var(--accent);border-color:transparent}
.tag.ok{background:var(--ok-soft);color:var(--ok);border-color:transparent}
.tag.warn{background:var(--warn-soft);color:var(--warn);border-color:transparent}
.tag.crit{background:var(--crit-soft);color:var(--crit);border-color:transparent}
.tag.nest{background:#1E3A4A;color:#fff;border-color:transparent}
.tag.pila{background:#5A6470;color:#fff;border-color:transparent}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:5px 12px;font-size:13px;white-space:nowrap}
.chip.on{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:600}
table{border-collapse:collapse;width:100%}
th{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap;font-weight:600}
td{padding:7px 10px;border-bottom:1px solid var(--line2);vertical-align:middle;font-variant-numeric:tabular-nums}
td.num,th.num{text-align:right}
td.nw{white-space:nowrap}
.btn.wrap{white-space:normal;text-align:left}
tr.sel td{background:var(--accent-soft)}
tr.grp td{background:var(--surface2);font-family:var(--cond);font-size:16px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;color:var(--ink)}
.addr{display:inline-block;background:var(--addr-bg);color:var(--addr-ink);border:1px solid var(--addr-line);border-radius:2px;font-family:var(--cond);font-weight:700;letter-spacing:.06em;padding:1px 8px;font-size:15px;white-space:nowrap}
.kpi{display:flex;flex-direction:column;gap:2px}
.kpi b{white-space:nowrap;font-family:var(--cond);font-size:24px;font-weight:700;letter-spacing:.02em;line-height:1;font-variant-numeric:tabular-nums}
.kpi span{white-space:nowrap;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.rub{display:inline-grid;grid-template-columns:14px 22px 14px;grid-template-rows:12px 16px 12px;gap:1px;vertical-align:middle}
.rub i{display:block;background:var(--line2);border-radius:1px}
.rub i.on{background:var(--accent)}
.rub i.m{background:var(--warn)}
.rub i.c{background:transparent}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--line);margin-right:6px;vertical-align:middle}
.dot.ok{background:var(--ok)} .dot.warn{background:var(--warn)} .dot.crit{background:var(--crit)} .dot.acc{background:var(--accent)}
.stripe{border-left:4px solid var(--accent)}
.stripe.warn{border-left-color:var(--warn)} .stripe.ok{border-left-color:var(--ok)} .stripe.crit{border-left-color:var(--crit)}
.list{display:flex;flex-direction:column;gap:8px}
.kbd{display:inline-block;min-width:20px;text-align:center;background:var(--surface);border:1px solid var(--line);border-radius:3px;padding:0 5px;font-family:var(--mono);font-weight:600;font-size:12px}
.cb{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.cb i{width:16px;height:16px;border:1px solid var(--line);border-radius:3px;background:var(--surface);display:inline-block}
.cb i.on{background:var(--accent);border-color:var(--accent)}
.radio{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.radio i{width:16px;height:16px;border:1px solid var(--line);border-radius:50%;background:var(--surface);display:inline-block}
.radio i.on{border:5px solid var(--accent)}
.foot{font-size:12px;color:var(--muted);padding:10px 24px;border-top:1px solid var(--line2)}
"""


def topbar(active="Nalozi", user="IVANA", theme="regal"):
    tabs = ["Nalozi", "Šifrarnici", "Skladište", "Obračun", "Postavke"]
    t = "".join(
        '<button class="tab"%s>%s</button>' % (' aria-current="page"' if x == active else "", x) for x in tabs
    )
    if theme == "brand":
        brand = ('<div class="brand" style="display: flex; align-items: center; gap: 10px;">'
                 '<img src="logo-mark.png" alt="" style="height: 36px; width: auto; display: block;">'
                 '<b>Paneli<span class="us">_</span> Production Hub</b>'
                 '<span style="margin-left: 8px;">ideja u proizvodnju · mockup v0.2 · varijanta B</span></div>')
    else:
        brand = '<div class="brand"><b>Production Hub</b><span>Paneli projekt · mockup v0.1</span></div>'
    return (
        '<div class="top"><div class="topin">'
        + brand
        + '<nav class="tabs" style="display: flex; gap: 6px;">%s</nav><div class="user">%s</div></div></div>' % (t, user)
    )


STEPS = ["Unos", "Provjera", "Optimirano", "Ponuda", "Proizvodnja", "Zatvoren"]


def order_strip(cur, sub, verzija="v3", save_label="Spremi"):
    """cur = indeks trenutnog koraka; sub = indeks aktivnog pod-taba (0..2)."""
    li = []
    for i, s in enumerate(STEPS):
        cls = "done" if i < cur else ("cur" if i == cur else "")
        li.append('<li class="%s">%s</li>' % (cls, s))
    subs = ["1 · Zaglavlje i elementi", "2 · Pila / nesting i export", "3 · Obračun → ponuda"]
    st = "".join('<div class="subtab%s">%s</div>' % (" on" if i == sub else "", x) for i, x in enumerate(subs))
    return (
        '<div class="ostrip"><div class="oin">'
        '<a class="back" href="#">← Nalozi</a>'
        '<div class="oname"><b>HUMER_2823_OMIS <span class="tag" style="vertical-align: middle;">%s</span></b><span>2026-02823 · Mario Humer · ponuda 26-010-002823</span></div>'
        '<ol class="steps" style="display: flex; gap: 6px;">%s</ol>'
        '<div class="row" style="display: flex; gap: 10px;"><button class="btn">Dnevnik</button><button class="btn pri">%s</button></div>'
        "</div></div>"
        '<div class="subtabs" style="display: flex; gap: 4px;">%s</div>' % (verzija, "".join(li), save_label, st)
    )


FONTS_BRAND = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=IBM+Plex+Mono:wght@500;600&amp;display=swap">'

# Varijanta B — brand iz new_mockup (antracit / drvo / narančasta, Inter). Semantičke boje (ok/warn/crit) ostaju.
BRAND_TOKENS = {
    "--bg:#E7EAEE": "--bg:#EDEBE7", "--surface2:#F3F5F7": "--surface2:#F4F2EE", "--ink:#14171A": "--ink:#1F2326", "--muted:#5A6470": "--muted:#5E646A",
    "--line:#C9D1D9": "--line:#CDC9C2", "--line2:#E3E8ED": "--line2:#E4E1DB",
    # akcija i aktivno stanje = antracit s bijelim tekstom (mirno); narančasta ostaje samo kao tanki naglasak
    "--accent:#17546E": "--accent:#5A5F64", "--accent-ink:#FFFFFF": "--accent-ink:#FFFFFF", "--accent-soft:#DCEAF1": "--accent-soft:#E7E4DE",
    '--sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif': '--sans:"Inter",system-ui,-apple-system,"Segoe UI",sans-serif',
    '--cond:"Barlow Condensed","IBM Plex Sans",system-ui,sans-serif': '--cond:"Inter",system-ui,sans-serif',
}
BRAND_EXTRA = """
.top{background:#5A5F64;border-bottom:1px solid #5A5F64}
.brand b{color:#FFFFFF;letter-spacing:0;text-transform:none;font-size:22px;font-weight:800;line-height:1}
.brand .wm{display:flex;flex-direction:column;gap:1px}
.brand .wm small{color:#FFFFFF;font-size:13px;font-weight:700;letter-spacing:0}
.brand .wm em{font-style:normal;color:#C7CCD1;font-size:9px;letter-spacing:.22em;text-transform:uppercase;margin-top:3px}
.brand .us{color:#F37A20}
.brand span{color:#E1E4E7;text-transform:none;letter-spacing:.02em}
.tab{color:#EDEFF1;text-transform:none;letter-spacing:0;font-size:15px;font-weight:600;border-radius:0;border-bottom:3px solid transparent;padding:9px 10px}
.tab[aria-current="page"]{background:transparent;color:#FFFFFF;border-bottom-color:#F37A20}
.tab:hover{background:#6A6F74;color:#FFFFFF}
.user{color:#F1F2F3;border-color:#858A8F}
h2,h3,.subtab,.steps li,.oname b,.tag,label.l,.kpi span,th{letter-spacing:0;text-transform:none}
h2{font-size:22px;font-weight:700} h3{font-size:14px;font-weight:600;color:var(--muted)}
.subtab{font-size:15px} .subtab.on{color:#1F2326;border-bottom-color:#F37A20}
.steps li{font-size:12px;font-weight:600}
.btn.pri{background:#5A5F64;border-color:#5A5F64;color:#FFFFFF}
.chip.on{background:#5A5F64;border-color:#5A5F64;color:#FFFFFF}
.tag.nest{background:#5A5F64} .tag.pila{background:#8A6D4E}
.tag.acc{background:#E7E4DE;color:#1F2326}
.stripe{border-left-color:#5A5F64}
.inp.big{font-family:var(--sans);font-size:20px}
.kpi b{font-family:var(--sans);font-size:22px}
.addr{background:#D8B892;color:#1B1206;border-color:#B8935F}
.kbd{color:#1F2326}
a{color:#1F2326;text-decoration:underline;text-decoration-color:#F37A20}
"""


def brand_css():
    c = CSS
    for k, v in BRAND_TOKENS.items():
        assert k in c, k
        c = c.replace(k, v)
    return c + BRAND_EXTRA


def page(title, body, height, bg="#E7EAEE", theme="regal"):
    css = CSS if theme == "regal" else brand_css()
    fonts = FONTS if theme == "regal" else FONTS_BRAND
    if theme != "regal":
        bg = "#EDEBE7"
    return (
        "<!doctype html>\n<html>\n<head>\n  <meta charset=\"utf-8\">\n  <script src=\"./support.js\"></script>\n</head>\n<body>\n<x-dc>\n<helmet>\n  <title>%s</title>\n  %s\n  <style>%s</style>\n</helmet>\n"
        '<div style="width: 1440px; min-height: %dpx; background: %s; display: flex; flex-direction: column;">\n%s\n</div>\n</x-dc>\n</body>\n</html>\n'
        % (title, fonts, css, height, bg, body)
    )


def logo_mark(size=30):
    """Plošni znak iz new_mockup: tri ploče (antracit, drvo, narančasta), bez 3D-a — za zaglavlje i male veličine."""
    return (
        '<svg width="%d" height="%d" viewBox="0 0 34 30" style="flex: none;" aria-label="Paneli Production Hub">'
        '<path d="M2 10 L10 5 L10 27 L2 30 Z" fill="#2B2F33"/><path d="M12 8 L20 3 L20 25 L12 28 Z" fill="#D8B892"/><path d="M22 6 L30 1 L30 23 L22 26 Z" fill="#F37A20"/>'
        "</svg>" % (size, size)
    )


# ikone (stroke, 16 px)
def ico(name, size=16, color="currentColor"):
    paths = {
        "search": '<circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5 14 14"/>',
        "plus": '<path d="M8 3v10M3 8h10"/>',
        "upload": '<path d="M8 11V3M4.5 6.5 8 3l3.5 3.5M3 13h10"/>',
        "check": '<path d="M3 8.5 6.5 12 13 4.5"/>',
        "warn": '<path d="M8 2 14.5 13.5h-13L8 2z"/><path d="M8 6.5v3.5M8 12v.5"/>',
        "file": '<path d="M4 2h5l3 3v9H4V2z"/><path d="M9 2v3h3"/>',
        "photo": '<rect x="2" y="3.5" width="12" height="9.5" rx="1"/><circle cx="8" cy="8.5" r="2.5"/><path d="M6 3.5 7 2h2l1 1.5"/>',
        "box": '<path d="M2 5 8 2l6 3v6l-6 3-6-3V5z"/><path d="M2 5l6 3 6-3M8 8v6"/>',
        "arrow": '<path d="M3 8h10M9 4l4 4-4 4"/>',
        "print": '<path d="M4 6V2h8v4M4 12H2V6h12v6h-2"/><rect x="4" y="9" width="8" height="5"/>',
        "lock": '<rect x="3" y="7" width="10" height="7" rx="1"/><path d="M5 7V5a3 3 0 0 1 6 0v2"/>',
    }
    return (
        '<svg width="%d" height="%d" viewBox="0 0 16 16" fill="none" stroke="%s" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" style="flex: none;">%s</svg>'
        % (size, size, color, paths[name])
    )


def rub(d1, k1, d2, k2):
    """mini-skica rubova: gore = duža 1, desno = kraća 1, dolje = duža 2, lijevo = kraća 2.
    Vrijednosti: 'A' (ABS, plavo), 'M' (melamin, žuto-smeđe), '' (bez ruba, sivo)."""
    def col(v):
        return "#17546E" if v == "A" else ("#9A5B06" if v == "M" else "#E3E8ED")
    def w(v):
        return "3" if v else "1"
    return (
        '<svg width="40" height="24" viewBox="0 0 40 24" style="display: block;" role="img" aria-label="rubovi D1 %s, K1 %s, D2 %s, K2 %s">'
        '<rect x="4" y="4" width="32" height="16" fill="#FFFFFF" stroke="#E3E8ED" stroke-width="1"/>'
        '<line x1="4" y1="4" x2="36" y2="4" stroke="%s" stroke-width="%s"/>'
        '<line x1="36" y1="4" x2="36" y2="20" stroke="%s" stroke-width="%s"/>'
        '<line x1="4" y1="20" x2="36" y2="20" stroke="%s" stroke-width="%s"/>'
        '<line x1="4" y1="4" x2="4" y2="20" stroke="%s" stroke-width="%s"/>'
        '</svg>' % (d1, k1, d2, k2, col(d1), w(d1), col(k1), w(k1), col(d2), w(d2), col(k2), w(k2))
    )
