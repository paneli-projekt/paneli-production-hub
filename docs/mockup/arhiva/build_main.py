# -*- coding: utf-8 -*-
"""Ekran 2 — Unos naloga, v0.2 (kompaktno: bitno na ekranu, ostalo na klik; unos elementa s grafikom daske kao PW/PPNEST).
Generira Main.dc.html (radni ekran) i MainPaneli.dc.html (što se otvara na klik)."""
from shared import topbar, order_strip, page, ico
import os

THEME = os.environ.get("HUB_THEME", "regal")   # regal = kao Regal traka (v0.1/v0.2) · brand = varijanta B iz new_mockup
ACC = "#17546E" if THEME == "regal" else "#5A5F64"
OK = "#1B6E48"; WARN = "#9A5B06"; LINE = "#C9D1D9"; LINE2 = "#E3E8ED"; MUTED = "#5A6470"

# ---------- stvarni elementi HUMER_2823_OMIS · IV BIJELI NK 18 (PPNEST CSV 10.9.) ----------
# rb, L, W, kom, lijevo, desno, gore, dolje (A = ABS 1/22 JELA TAVERNA, M = MEL-ISTI, '' = bez), napomena, prolaza
ELEMS = [
    (1, 820, 550, 16, "A", "", "A", "A", "", 1),
    (2, 820, 520, 4, "A", "", "A", "A", "", 1),
    (3, 140, 520, 1, "A", "", "A", "A", "134X520", 2),
    (4, 480, 550, 2, "A", "", "A", "A", "", 1),
    (5, 464, 520, 1, "A", "", "", "", "", 1),
    (6, 464, 80, 4, "A", "", "", "", "", 2),
    (22, 1830, 557, 2, "A", "", "A", "A", "RASTER 150 64-64 150", 1),
    (26, 544, 557, 8, "A", "", "", "", "CNC SKICA 1", 1),
    (27, 1050, 140, 1, "M", "M", "M", "M", "1050X120", 2),
    (31, 460, 190, 1, "M", "M", "M", "M", "", 2),
    (37, 1030, 340, 14, "A", "A", "A", "A", "RASTER 150 64-64 150", 1),
    (46, 272, 340, 2, "A", "", "A", "", "", 1),
]
BAND = {"A": "1/22 JELA TAVERNA", "M": "MEL-ISTI", "": ""}


def edge_color(v):
    return OK if v == "A" else (WARN if v == "M" else LINE2)


def edge_w(v):
    return "3" if v else "1"


def rubv(l, d, g, dol):
    """mini-skica daske u tablici: okomita daska kao u PPNEST-u (lijevo/desno = duže stranice, gore/dolje = kraće)."""
    return (
        '<svg width="26" height="32" viewBox="0 0 26 32" style="display: block;" aria-label="rubovi L %s D %s G %s Dolje %s">'
        '<rect x="6" y="4" width="14" height="24" fill="#FFFFFF" stroke="%s" stroke-width="1"/>'
        '<line x1="6" y1="4" x2="6" y2="28" stroke="%s" stroke-width="%s"/>'
        '<line x1="20" y1="4" x2="20" y2="28" stroke="%s" stroke-width="%s"/>'
        '<line x1="6" y1="4" x2="20" y2="4" stroke="%s" stroke-width="%s"/>'
        '<line x1="6" y1="28" x2="20" y2="28" stroke="%s" stroke-width="%s"/>'
        "</svg>" % (l, d, g, dol, LINE2, edge_color(l), edge_w(l), edge_color(d), edge_w(d), edge_color(g), edge_w(g), edge_color(dol), edge_w(dol))
    )


def toggle(x, y, letter, on):
    fill = ACC if on else "#FFFFFF"
    stroke = ACC if on else LINE
    col = "#FFFFFF" if on else MUTED
    return (
        '<rect x="%d" y="%d" width="20" height="20" rx="3" fill="%s" stroke="%s"/>'
        '<text x="%d" y="%d" text-anchor="middle" font-family="Barlow Condensed, sans-serif" font-weight="700" font-size="13" fill="%s">%s</text>'
        % (x, y, fill, stroke, x + 10, y + 14, col, letter)
    )


def board_svg(L, W, l, d, g, dol):
    """Grafika daske za unos: okomita daska (1. mjera = god = okomito); uz svaki rub par prekidača M/A i naziv trake;
    zeleni rub = ABS, smeđi = melamin, tanki sivi = bez ruba (kao u PPNEST-u, samo kompaktnije)."""
    bx, by, bw, bh = 200, 60, 130, 230
    cx = bx + bw // 2
    cy = by + bh // 2
    mono = 'font-family="IBM Plex Mono, monospace" font-size="11"'
    s = ['<svg width="540" height="352" viewBox="0 0 540 352" style="display: block;">']
    s.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#FBFBF7" stroke="%s" stroke-width="1"/>' % (bx, by, bw, bh, LINE))
    for x1, y1, x2, y2, v in ((bx, by, bx, by + bh, l), (bx + bw, by, bx + bw, by + bh, d), (bx, by, bx + bw, by, g), (bx, by + bh, bx + bw, by + bh, dol)):
        s.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (x1, y1, x2, y2, edge_color(v), "5" if v else "1"))
    # 2. mjera (gore) — kutija iznad daske, prekidači lijevo od nje, naziv trake desno
    s.append('<rect x="%d" y="%d" width="56" height="22" rx="3" fill="#FFFFFF" stroke="%s"/>' % (cx - 28, by - 34, LINE))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Barlow Condensed, sans-serif" font-weight="700" font-size="16" fill="#14171A">%d</text>' % (cx, by - 18, W))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="IBM Plex Sans, sans-serif" font-size="10" fill="%s">2. MJERA</text>' % (cx, by - 40, MUTED))
    s.append(toggle(cx - 80, by - 35, "M", g == "M")); s.append(toggle(cx - 57, by - 35, "A", g == "A"))
    s.append('<text x="%d" y="%d" %s fill="%s">%s</text>' % (cx + 36, by - 19, mono, "#14171A" if g else MUTED, BAND[g] or "—"))
    # 1. mjera (lijevo) — kutija lijevo od daske, prekidači ispod nje, naziv trake ispod prekidača
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="IBM Plex Sans, sans-serif" font-size="10" fill="%s">1. MJERA (GOD)</text>' % (bx - 60, cy - 26, MUTED))
    s.append('<rect x="%d" y="%d" width="56" height="22" rx="3" fill="#FFFFFF" stroke="%s"/>' % (bx - 88, cy - 20, LINE))
    s.append('<text x="%d" y="%d" text-anchor="middle" font-family="Barlow Condensed, sans-serif" font-weight="700" font-size="16" fill="#14171A">%d</text>' % (bx - 60, cy - 4, L))
    s.append(toggle(bx - 92, cy + 12, "M", l == "M")); s.append(toggle(bx - 69, cy + 12, "A", l == "A"))
    s.append('<text x="%d" y="%d" text-anchor="end" %s fill="%s">%s</text>' % (bx - 12, cy + 50, mono, "#14171A" if l else MUTED, BAND[l] or "—"))
    # desno — prekidači desno od daske, naziv ispod
    s.append(toggle(bx + bw + 12, cy + 12, "M", d == "M")); s.append(toggle(bx + bw + 35, cy + 12, "A", d == "A"))
    s.append('<text x="%d" y="%d" %s fill="%s">%s</text>' % (bx + bw + 12, cy + 50, mono, "#14171A" if d else MUTED, BAND[d] or "—"))
    # dolje — prekidači ispod daske, naziv desno od njih
    s.append(toggle(cx - 23, by + bh + 12, "M", dol == "M")); s.append(toggle(cx, by + bh + 12, "A", dol == "A"))
    s.append('<text x="%d" y="%d" %s fill="%s">%s</text>' % (cx + 28, by + bh + 27, mono, "#14171A" if dol else MUTED, BAND[dol] or "—"))
    s.append('<text x="%d" y="%d" font-family="IBM Plex Sans, sans-serif" font-size="10" fill="%s">M = MEL-ISTI (ista boja, 0,5 mm) · A = ABS-ISTI (ista boja, 1 mm) ili traka druge boje</text>' % (bx - 92, by + bh + 52, MUTED))
    s.append('<text x="%d" y="%d" font-family="IBM Plex Sans, sans-serif" font-size="10" fill="%s">rijetko „ABS-ISTI 2mm“ (bira se u izborniku ABS) · tanki rub = bez trake</text>' % (bx - 92, by + bh + 66, MUTED))
    s.append("</svg>")
    return "".join(s)


# ---------- retci tablice ----------
erows = []
for rb, L, W, kom, l, d, g, dol, nap, pr in ELEMS:
    bands = sorted({BAND[x] for x in (l, d, g, dol) if x})
    tr = " · ".join(bands) if bands else "—"
    flag = (' <span class="tag warn">' + ico("warn", 11) + " 2 prolaza</span>") if pr == 2 else ""
    erows.append(
        '<tr><td class="num muted">%d</td><td class="num"><b>%d</b></td><td class="num"><b>%d</b></td><td class="num">%d</td>'
        '<td>%s</td><td class="mono nw">%s</td><td>%s%s</td><td class="muted">%s</td></tr>'
        % (rb, L, W, kom, rubv(l, d, g, dol), tr, nap, flag, ico("check", 14, OK))
    )

mats = [("IV BIJELI NK 18", "53 · 174", True), ("IV JELA TAVERNA 19", "35 · 48", False), ("MDF BIJELI 3", "22 · 27", False),
        ("IV BIJELI NK 16", "10 · 28", False), ("IV HRAST RELIEF CARD. 19", "1 · 1", False), ("RP BASANIT SAND", "2 · 2", False)]
chips = "".join(
    '<span class="chip%s" style="padding: 7px 14px; font-size: 14px;">%s <span style="opacity: .7; font-size: 12px;">%s</span></span>' % (" on" if on else "", n, c)
    for n, c, on in mats
)


def kv(label, value, mono=False, width=None):
    st = ' style="min-width: %dpx;"' % width if width else ""
    return '<div class="fld"%s><label class="l" style="margin-bottom: 1px;">%s</label><div style="font-size: 14px;%s">%s</div></div>' % (
        st, label, " font-family: IBM Plex Mono, monospace; font-size: 13px;" if mono else "", value)


body_main = topbar("Nalozi", theme=THEME) + order_strip(cur=0, sub=0, verzija="v3 · IVANA 18.08.") + '''
<div class="wrap" style="display: flex; flex-direction: column; gap: 12px;">

  <div class="card" style="display: flex; gap: 28px; align-items: center; padding: 10px 16px;">
    ''' + kv("Kupac", "<b>Mario Humer</b> · Omiš") + kv("Nalog", "HUMER_2823_OMIS", mono=True) + kv("Datum", "18.08.2026") + kv("Izradio", "IVANA") + kv("Napomena naloga", "Radne ploče + fronte po skici; okov u Excelu (48 st.)") + '''
    <div style="flex: 1;"></div>
    <button class="btn sm">Zaglavlje ▾</button>
    <button class="btn sm">''' + ico("upload", 14) + ''' Uvoz ▾</button>
  </div>

  <div class="row" style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
    <span class="note" style="letter-spacing: .08em; text-transform: uppercase; font-size: 11px; margin-right: 4px;">Materijali</span>''' + chips + '''
    <button class="btn ghost sm">''' + ico("plus", 13) + ''' Materijal</button>
    <span class="note" style="margin-left: auto;">6 materijala · 123 st. · 280 kom · 103,1 m²</span>
  </div>

  <div class="card" style="display: flex; flex-direction: column; gap: 0; padding: 0;">
    <div style="display: flex; gap: 14px; align-items: center; padding: 10px 16px; border-bottom: 1px solid #E3E8ED; background: #F3F5F7;">
      <span class="mono" style="font-weight: 600;">IV000090</span><b style="font-family: Barlow Condensed, sans-serif; font-size: 20px; letter-spacing: .02em;">IVERAL BIJELI NK W908 ST2 18 MM</b>
      <span class="note">18 mm · bez goda · Winstore <span class="mono">W908ST2-18</span> · 13 ploča na skladištu</span>
      <span class="tag nest">nesting</span>
      <div style="flex: 1;"></div>
      <button class="btn sm">Detalji materijala ▾</button><button class="btn sm">Trake ▾</button><button class="btn sm">Promijeni</button>
    </div>

    <div style="display: grid; grid-template-columns: 260px minmax(0, 1fr) 300px; gap: 20px; padding: 14px 16px;">
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <div class="fld"><label class="l">1. mjera (god)</label><div class="inp big" style="justify-content: flex-end;">820</div></div>
        <div class="fld"><label class="l">2. mjera</label><div class="inp big" style="justify-content: flex-end;">550</div></div>
        <div class="fld"><label class="l">Kom</label><div class="inp big" style="justify-content: flex-end; width: 120px;">16</div></div>
        <div class="fld"><label class="l">Napomena (etiketa + CSV)</label><div class="inp"><span class="ph">npr. gotova mjera, CNC skica…</span></div></div>
        <div class="row" style="display: flex; gap: 8px; margin-top: 6px;">
          <button class="btn pri" style="flex: 1; min-height: 40px;">Prihvati <span class="kbd" style="margin-left: 6px; color: #17546E;">↵</span></button>
          <button class="btn">Ažuriraj</button><button class="btn">Obriši</button>
        </div>
      </div>

      <div style="display: flex; flex-direction: column; align-items: center; gap: 6px;">
        <div style="display: flex; justify-content: space-between; width: 540px;">
          <div class="fld"><label class="l" style="color: #9A5B06;">MEL-ISTI · ista boja 0,5 mm</label><div class="inp" style="min-height: 32px; padding: 4px 10px; width: 190px;"><span class="mono">MEL-ISTI</span><span class="muted" style="margin-left: auto;">▾</span></div></div>
          <div class="fld"><label class="l" style="color: #1B6E48;">ABS · zadano ABS-ISTI = 1 mm</label><div class="inp" style="min-height: 32px; padding: 4px 10px; width: 210px;"><span class="mono">1/22 JELA TAVERNA</span><span class="muted" style="margin-left: auto;">▾</span></div></div>
        </div>
        ''' + board_svg(820, 550, "A", "", "A", "A") + '''
      </div>

      <div style="display: flex; flex-direction: column; gap: 10px; justify-content: flex-start;">
        <div class="card stripe" style="background: #F3F5F7; padding: 10px 12px;">
          <label class="l">Tipke</label>
          <div class="note"><span class="kbd">Enter</span> prihvati · <span class="kbd">Tab</span> sljedeće polje · <span class="kbd">L</span> <span class="kbd">D</span> <span class="kbd">G</span> <span class="kbd">B</span> uključi rub (2× = melamin) · <span class="kbd">F2</span> ispravi zadnji · <span class="kbd">Esc</span> očisti</div>
        </div>
        <div class="card" style="padding: 10px 12px;">
          <label class="l">Ovaj element</label>
          <div class="note">0,45 m² · rubovi 2,19 m ABS · 2 prolaza: ne</div>
        </div>
        <div class="card" style="padding: 10px 12px;">
          <label class="l">Zadane trake materijala</label>
          <div class="note"><span class="mono">MEL-ISTI</span> (0,5 mm) → TR000017 · <span class="mono">ABS-ISTI</span> (1 mm) → TR000168 · <span class="mono">ABS-ISTI 2mm</span> → TR000016 · druga boja <span class="mono">1/22 JELA TAVERNA</span> → TR001254 <a href="#">promijeni</a></div>
        </div>
      </div>
    </div>
  </div>

  <div class="card" style="padding: 0;">
    <table>
      <thead><tr><th class="num">rb</th><th class="num">1. mjera</th><th class="num">2. mjera</th><th class="num">kom</th><th>Rubovi</th><th>Traka</th><th>Napomena</th><th></th></tr></thead>
      <tbody>''' + "".join(erows) + '''
        <tr><td colspan="8" class="muted" style="text-align: center; padding: 8px;">… još 41 redak (53 stavke, 174 kom) · <a href="#">prikaži sve</a></td></tr>
      </tbody>
    </table>
  </div>

  <div class="card" style="display: flex; gap: 22px; align-items: center; padding: 10px 16px;">
    <div class="kpi"><b>53 · 174</b><span>stavki · kom</span></div>
    <div class="kpi"><b>50,37 m²</b><span>dijelova</span></div>
    <div class="kpi"><b>208,2 + 21,8 m</b><span>ABS · melamin (PW metri)</span></div>
    <div class="kpi"><b>10 pl. · 57,96 m²</b><span>za obračun (PW-metoda)</span></div>
    <div style="flex: 1;"></div>
    <button class="btn sm"><span class="dot ok"></span>Provjere: sve u redu ▾</button>
    <button class="btn">Spremi</button>
    <button class="btn pri">Dalje: pila / nesting ''' + ico("arrow", 14, "#fff") + '''</button>
  </div>
</div>'''

# ---------- 2b: paneli koji se otvaraju na klik ----------
panel = lambda title, inner, w=430: (
    '<div class="card" style="width: %dpx; display: flex; flex-direction: column; gap: 10px; box-shadow: 0 6px 22px rgba(20,23,26,.12);">'
    '<div class="row" style="display: flex; justify-content: space-between;"><h3 style="margin: 0;">%s</h3><span class="muted">✕</span></div>%s</div>' % (w, title, inner))

p_zaglavlje = panel("Zaglavlje ▾", '''
  <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px;">
    <div class="fld" style="grid-column: span 2;"><label class="l">Kupac (Pantheon subjekt)</label><div class="inp">''' + ico("search", 14, MUTED) + '''<b>Mario Humer</b><span class="muted">· Omiš</span></div></div>
    <div class="fld"><label class="l">Naziv naloga (PW / bNest)</label><div class="inp mono">HUMER_2823_OMIS</div></div>
    <div class="fld"><label class="l">Hub broj</label><div class="inp ro mono">2026-02823</div></div>
    <div class="fld"><label class="l">Datum</label><div class="inp">18.08.2026</div></div>
    <div class="fld"><label class="l">Izradio</label><div class="inp ro">IVANA</div></div>
    <div class="fld"><label class="l">Ponuda (Pantheon)</label><div class="inp ro mono">26-010-002823</div></div>
    <div class="fld"><label class="l">Kerf za obračun</label><div class="inp">16 mm ▾</div></div>
    <div class="fld" style="grid-column: span 2;"><label class="l">Napomena naloga</label><div class="inp">Radne ploče + fronte po skici; okov u Excelu (48 stavki)</div></div>
  </div>''')

p_uvoz = panel("Uvoz ▾", '''
  <button class="btn" style="text-align: left;">''' + ico("file") + ''' CPW iz klijentske aplikacije (PPW) <span class="tag ok" style="margin-left: 8px;">5 učitano</span></button>
  <button class="btn" style="text-align: left;">''' + ico("upload") + ''' Excel narudžba (predložak)</button>
  <button class="btn" style="text-align: left;">''' + ico("photo") + ''' Foto / sken rukopisa → prepoznavanje <span class="tag warn" style="margin-left: 8px;">za provjeru</span></button>
  <button class="btn" style="text-align: left;">''' + ico("box") + ''' Corpus paket (CPW + CSV + CIX) <span class="tag" style="margin-left: 8px;">D-29</span></button>
  <div class="note">Elementi prepoznati iz rukopisa dolaze s oznakom ZA PROVJERU i ne idu u export dok ih čovjek ne potvrdi.</div>''', 400)

p_mat = panel("Detalji materijala ▾", '''
  <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px;">
    <div class="fld"><label class="l">Winstore kod</label><div class="inp ro mono">W908ST2-18</div></div>
    <div class="fld"><label class="l">Ploča</label><div class="inp ro">2800 × 2070</div></div>
    <div class="fld"><label class="l">Glodalo (CIX)</label><div class="inp ro">8D · 2 prolaza</div></div>
  </div>
  <div class="note">Aliasi: <span class="mono">IV BIJELI NK 18MM</span> · <span class="mono">IV_BIJELI_NK_18_MM</span> · <span class="mono">IVERAL BIJELI NK W908 ST2 18 MM</span> — Hub ih prepozna, u CSV ide Winstore kod (D-24).</div>
  <div><span class="dot ok"></span>Skladište: Winstore <b>13</b> ploča (izvoz 11.09.) · restlovi za ovaj dekor: 0</div>
  <div><span class="dot acc"></span>Put: Hub predlaže <span class="tag nest">nesting</span> (iveral, 50 m² ≫ 1 ploča) — potvrđuje voditelj na koraku 2</div>''', 520)

p_trake = panel("Trake ▾", '''
  <table>
    <thead><tr><th>Oznaka u nalogu</th><th>Pantheon ident</th><th>Regal traka</th></tr></thead>
    <tbody>
      <tr><td><span class="mono">MEL-ISTI</span> <span class="tag warn">0,5 mm ista boja</span></td><td><span class="mono">TR000017</span> ABS 0,5/22 BIJELI NK</td><td><span class="addr">R1-03-C</span></td></tr>
      <tr><td><span class="mono">ABS-ISTI</span> <span class="tag ok">1 mm ista boja · zadano</span></td><td><span class="mono">TR000168</span> ABS 1/22 BIJELI NK</td><td><span class="addr">R1-03-A</span></td></tr>
      <tr><td><span class="mono">ABS-ISTI 2mm</span> <span class="tag">2 mm · rijetko</span></td><td><span class="mono">TR000016</span> ABS 2/22 BIJELI NK</td><td><span class="addr">R1-03-B</span></td></tr>
      <tr><td><span class="mono">1/22 JELA TAVERNA</span> <span class="tag ok">druga boja</span></td><td><span class="mono">TR001254</span> ABS 1/22 JELA CLAY</td><td><span class="addr">R2-07-A</span></td></tr>
      <tr><td><span class="muted">+ nova oznaka</span></td><td class="muted">traži ident…</td><td></td></tr>
    </tbody>
  </table>
  <div class="note">Na naljepnici (D-31): <span class="mono">MEL-ISTI</span> = 0,5 mm · <span class="mono">ABS-ISTI</span> = 1 mm (95 % slučajeva) · <span class="mono">ABS-ISTI 2mm</span> samo kad je 2 mm · druga boja = naziv trake iz Pantheona. Metri po traci = Σ stranica × 1,10 (kao PW); u ponudu naviše na metar (D-20); potrošnja ide u regal-traku.</div>''', 520)

p_provjere = panel("Provjere ▾", '''
  <div><span class="dot ok"></span>svi materijali imaju Winstore kod i dimenziju ploče</div>
  <div><span class="dot ok"></span>sve trake mapirane na TR ident</div>
  <div><span class="dot ok"></span>0 elemenata s oznakom PROVJERI</div>
  <div><span class="dot warn"></span>IV JELA TAVERNA 19: Winstore 0 ploča — javiti voditelju</div>
  <div class="row" style="display: flex; gap: 8px; margin-top: 4px;"><button class="btn sm">Spremi kao nacrt</button><button class="btn pri sm">Pošalji na provjeru</button></div>''', 400)

p_abs = panel("ABS ▾ (padajući izbornik iznad daske)", '''
  <div class="note">Tko: onaj tko unosi nalog (Ivana / Goran). Kada: pri dodavanju materijala, prije elemenata; zadano je <b>ABS-ISTI = 1 mm</b> (95 % slučajeva) pa se u pravilu ništa ne bira. Samo kad kupac traži 2 mm izabere se „ABS-ISTI 2mm“ — i usred unosa, ako se debljina mijenja po elementima. Prekidač <b>A</b> na dasci od tada stavlja tu traku; tekst na naljepnici Hub slaže sam iz odabranog identa (D-31).</div>
  <div class="list" style="display: flex; flex-direction: column; gap: 6px;">
    <div class="row" style="display: flex; gap: 10px; padding: 8px 10px; background: #DCEAF1; border-radius: 3px;"><span class="mono" style="min-width: 150px;"><b>ABS-ISTI</b></span><span>TR000168 ABS 1/22 BIJELI NK · 1 mm</span><span class="tag acc" style="margin-left: auto;">zadano</span></div>
    <div class="row" style="display: flex; gap: 10px; padding: 8px 10px; border: 1px solid #E3E8ED; border-radius: 3px;"><span class="mono" style="min-width: 150px;">ABS-ISTI 2mm</span><span>TR000016 ABS 2/22 BIJELI NK</span><span class="tag" style="margin-left: auto;">rijetko · izlazi iz upotrebe</span></div>
    <div class="row" style="display: flex; gap: 10px; padding: 8px 10px; border: 1px solid #E3E8ED; border-radius: 3px;"><span class="mono" style="min-width: 150px;">ABS-ISTI 1/44</span><span>ABS 1/44 iste boje (radne ploče)</span></div>
    <div class="row" style="display: flex; gap: 10px; padding: 8px 10px; border: 1px solid #E3E8ED; border-radius: 3px;"><span class="mono" style="min-width: 150px;">1/22 JELA TAVERNA</span><span>TR001254 ABS 1/22 JELA CLAY</span><span class="tag" style="margin-left: auto;">druga boja · u ovom nalogu</span></div>
    <div class="row" style="display: flex; gap: 10px; padding: 8px 10px; border: 1px dashed #C9D1D9; border-radius: 3px; color: #5A6470;"><span class="mono" style="min-width: 150px;">druga boja…</span><span>traži ident u šifrarniku traka</span></div>
  </div>
  <div class="note">Uvezeni CPW s „ABS-ISTI“ znači 1 mm — ništa se ne pita. Ponuda (TR ident) i naljepnica nastaju iz istog izbora, pa se uvijek slažu.</div>''', 560)

body_paneli = '''
<div style="padding: 22px 24px; display: flex; flex-direction: column; gap: 14px;">
  <div><h2>Unos naloga — što se otvara na klik</h2><div class="note">Ovo NIJE na radnom ekranu; svaki panel se otvori gumbom u zaglavlju / traci materijala i zatvori s ✕ ili Esc. Radni ekran ostaje: zaglavlje u jednom retku, materijali, unos elementa s daskom, tablica, sažetak.</div></div>
  <div style="display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">''' + p_zaglavlje + p_uvoz + p_provjere + '''</div>
  <div style="display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">''' + p_mat + p_trake + '''</div>
  <div style="display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">''' + p_abs + '''</div>
</div>'''

if THEME == "regal":
    pages = {
        "Main.dc.html": page("Production Hub — Unos naloga", body_main, 1240),
        "MainPaneli.dc.html": page("Production Hub — Unos naloga, paneli na klik", body_paneli, 1320),
    }
else:
    pages = {"MainBrandB.dc.html": page("Paneli Production Hub — Unos naloga, varijanta B (brand, mirna)", body_main, 1240, theme="brand")}
for fn, html in pages.items():
    with open(fn, "w", encoding="utf-8") as f:
        f.write(html)
    print(fn, len(html))
