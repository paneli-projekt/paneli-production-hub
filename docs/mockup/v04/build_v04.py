# -*- coding: utf-8 -*-
"""Mockup v0.4 (12. 9. 2026.) — nastavak v0.3.1 (D-39, D-35). Novo u v0.4: ekran 3 = ponuda iz Huba (D-40: „Pošalji kupcu“ glavna akcija,
eSlog u Pantheon tek uz „Kupac potvrdio“, rabat kupca s dvije stope), dijalog „Kupac potvrdio“ (3b), vremenska crta događaja naloga (3c),
novi ekran „Nabava“ za Sanelu (D-42: potrebe preko svih potvrđenih naloga + narudžbenice), lijeva traka s „Nabava“.
Primjer: stvarni nalog HUMER_OMIS_2823; datumi, statusi, narudžbenice i drugi nalozi su ilustracija. Na ekranima nema oznaka D-xx (strip_dxx)."""
from v04_base import (screen, card, strip_dxx, ORDER_CRUMB, ORDER_CRUMB_HUB, board, rubv, thumb, steps_bar, ico, ACC, ABS, MEL, MEL_SOFT, ABS_SOFT, LINE, MUTED, INK, CRIT, WARN)

W = {}  # datoteka → html


def pane(title, body, extra_hd="", style=""):
    return '<div class="pane" style="%s"><div class="hd"><span class="lbl">%s</span>%s</div>%s</div>' % (style, title, extra_hd, body)


def bd(*lines, size="13px", gap="6px"):
    return '<div class="bd" style="font-size: %s; gap: %s;">%s</div>' % (size, gap, "".join('<div>%s</div>' % l for l in lines))


def eur(x):
    s = "%.2f" % x
    a, b = s.split(".")
    a = "{:,}".format(int(a)).replace(",", ".")
    return a + "," + b


def q(x):
    return ("%.2f" % x).rstrip("0").rstrip(".").replace(".", ",")


# ================================================================ 1. NALOZI (popis)
NALOZI = [
    # naziv (KUPAC_NAZIV_BROJ, D-33), kupac, datum, izradio, mat, stavki, kom, m2, put, ponuda, status, napomena
    ("— novi —", "Bogdanić (rukopis)", "12.09.2026", "GORAN", "—", "—", "—", "—", "", "", "Unos", "rukopis: 4 elementa za provjeru"),
    ("HUMER_OMIS_2823", "Humer", "18.08.2026", "IVANA", "6", "123", "280", "103,1", "nest+pila", "26-010-002823", "Pila / nesting", "čeka voditelja: put za 6 materijala"),
    ("MAZUR_16_3258", "Mazur", "04.09.2026", "IVANA", "7", "71", "186", "57,9", "nesting", "26-010-003258", "Ponuda", "čeka kupca 8 dana"),
    ("BRATEK_3231", "Bratek (Excel)", "27.08.2026", "GORAN", "4", "46", "118", "49,3", "nesting", "26-010-003231", "Ponuda", "čeka kupca 16 dana"),
    ("BLAGO_ADRIJANA_2929", "Blago", "20.08.2026", "IVANA", "8", "75", "159", "53,6", "nesting", "26-010-002929", "Potvrđeno", "skladište: 1 materijal 0 ploča → popis za nabavu"),
    ("BOGDANIC_IVA_3217", "Bogdanić", "01.09.2026", "IVANA", "5", "86", "158", "56,7", "nesting", "26-010-003217", "Proizvodnja", ""),
    ("VARGA_POTNJANI_3213", "Varga", "29.08.2026", "GORAN", "7", "75", "129", "33,9", "nest+pila", "26-010-003213", "Proizvodnja", ""),
    ("BLAGO_JASA_3166", "Blago", "28.08.2026", "IVANA", "2", "18", "32", "6,0", "pila", "26-010-003166", "Zatvoren", ""),
    ("TURALIJA_TUKA_2924", "Turalija", "19.08.2026", "GORAN", "5", "25", "43", "12,7", "pila", "26-010-002924", "Zatvoren", ""),
    ("ROMIC_2423", "Romić", "10.06.2026", "IVANA", "6", "8", "10", "6,7", "pila", "26-010-002423", "Zatvoren", ""),
]
STATUS_TAG = {"Unos": "info", "Ponuda": "abs", "Potvrđeno": "ok", "Skladište": "warn", "Pila / nesting": "nest", "Proizvodnja": "ok", "Zatvoren": ""}
STATUS_TXT = {"Ponuda": "Ponuda · čeka kupca"}


def put_tag(p):
    return {"nesting": '<span class="tag nest">nesting</span>', "pila": '<span class="tag pila">pila</span>',
            "nest+pila": '<span class="tag nest">nesting</span> <span class="tag pila">pila</span>'}.get(p, '<span class="tag">—</span>')


rows = []
for n, k, d, iz, mat, st, kom, m2, put, pon, status, nap in NALOZI:
    sel = ' class="sel"' if n == "HUMER_OMIS_2823" else ""
    name = ('<b class="mono" style="font-size: 13px;">%s</b>' % n) if n != "— novi —" else '<span style="color: var(--muted);">— novi (bez imena) —</span>'
    napc = ('<br><span class="note">%s</span>' % nap) if nap else ""
    rows.append('<tr%s><td style="white-space: normal;">%s%s</td><td style="overflow: hidden; text-overflow: ellipsis;">%s</td><td class="num">%s</td><td>%s</td><td class="r num">%s</td><td class="r num">%s / %s</td><td class="r num">%s</td><td>%s</td><td class="mono" style="font-size: 12px;">%s</td><td><span class="tag %s">%s</span></td></tr>'
                % (sel, name, napc, k, d, iz, mat, st, kom, m2, put_tag(put), pon or '<span style="color: var(--muted);">—</span>', STATUS_TAG[status], STATUS_TXT.get(status, status)))

chips = [("Svi", 10, True), ("Unos", 1, False), ("Ponuda · čeka kupca", 2, False), ("Potvrđeno", 1, False), ("Skladište", 0, False), ("Pila / nesting", 1, False), ("Proizvodnja", 2, False), ("Zatvoren", 3, False)]
chips_h = "".join('<span class="chip%s">%s <span class="n">%d</span></span>' % (" on" if on else "", n, c) for n, c, on in chips)

centre1 = (
    '<div class="pane">'
    '<div class="hd" style="gap: 10px;"><div class="inp" style="flex: 1; min-height: 34px; padding: 4px 10px;">' + ico("search").replace('<svg', '<svg style="width: 16px; height: 16px; color: var(--muted);"') +
    '<span class="ph">traži: nalog, kupac, ponuda, materijal…</span></div>'
    '<span class="chip">Moji (IVANA)</span><span class="chip">Čeka voditelja</span><span class="chip">S upozorenjem <span class="n">2</span></span></div>'
    '<div style="padding: 8px 14px; border-bottom: 1px solid var(--line2); display: flex; gap: 6px; flex-wrap: wrap;">' + chips_h + '</div>'
    '<div style="overflow: hidden;"><table style="table-layout: fixed;"><thead><tr><th style="width: 200px;">Nalog</th><th>Kupac</th><th style="width: 84px;">Datum</th><th style="width: 64px;">Izradio</th><th class="r" style="width: 44px;">Mat.</th><th class="r" style="width: 90px;">Stavki / kom</th><th class="r" style="width: 58px;">m²</th><th style="width: 106px;">Put</th><th style="width: 110px;">Ponuda</th><th style="width: 154px;">Status</th></tr></thead>'
    '<tbody>' + "".join(rows) + '</tbody></table></div>'
    '<div style="flex: 1;"></div>'
    '<div style="padding: 8px 14px; border-top: 1px solid var(--line2);">' + steps_bar(-1).replace('class="step"', 'class="step" style="font-size: 11.5px;"') + '</div>'
    '<div style="padding: 0 14px 9px; font-size: 12px; color: var(--muted);">Jedan redak = jedan nalog kroz cijeli lanac. Naziv = KUPAC_NAZIV_BROJ (kako ga očekuju PW, bNest i naljepnice), Hub broj u pozadini (2026-02823) veže PW program, bNest projekt i ponudu.</div>'
    '</div>'
)
right1 = (
    '<div style="display: flex; flex-direction: column; gap: 12px; min-height: 0;">'
    + pane("Čeka potvrdu kupca", bd('<b>MAZUR_16_3258</b> · poslana 04.09. · 8 dana', '<b>BRATEK_3231</b> · poslana 27.08. · <span style="color: var(--warn); font-weight: 600;">16 dana</span>', '<a href="#">Podsjeti kupca</a>', size="12.5px"), '<span style="flex: 1;"></span><span class="tag abs">2</span>')
    + pane("Potvrđeno → skladište", bd('<b>BLAGO_ADRIJANA_2929</b> · kupac potvrdio 11.09.', '<span class="dot warn"></span>1 materijal 0 ploča → manjak je u <a href="#">Nabavi</a> (Sanela)', size="12.5px"), '<span style="flex: 1;"></span><span class="tag ok">1</span>')
    + pane("Čeka voditelja", bd('<b>HUMER_OMIS_2823</b> · put pila / nesting za 6 materijala', '<span class="note">Hub predložio: 2 nesting · 4 pila — sheme uz svaki materijal</span>', size="12.5px"), '<span style="flex: 1;"></span><span class="tag nest">1</span>')
    + pane("Rezultati sa strojeva", bd('<span class="dot"></span>bNest: 2 nova .mno (HUMER) · 11.09.', '<span class="dot info"></span>pila: 4 CPO poslana u Z:\\Krojne_liste', size="12.5px"))
    + pane("Skladište", bd('<span class="dot"></span>Winstore izvoz 11.09. učitan (374 ploče)', '<span class="dot"></span>restlovi: 1.589 kom · 2 nova prijedloga iz nestinga', size="12.5px"), style="flex: 1;")
    + '</div>'
)
foot1 = ('<div class="kpi"><b>10</b><span>naloga u popisu</span></div><div class="kpi"><b>2</b><span>čekaju kupca</span></div><div class="kpi"><b>1</b><span>čeka voditelja</span></div><div class="kpi"><b>2</b><span>u proizvodnji</span></div>'
         '<div style="flex: 1;"></div><button class="btn">Uvezi CPW / Excel / foto</button><button class="btn pri">+ Novi nalog</button>')
W["v04_Nalozi.dc.html"] = screen("Production Hub v0.4 — Nalozi", "<b>Nalozi</b> · danas 3 nova · ovaj tjedan 41", None,
                                 '<button class="tbtn">Uvezi ▾</button><button class="tbtn pri">+ Novi nalog</button>', "nalozi",
                                 "minmax(0, 1fr) 292px", [centre1, right1], foot1)

# ================================================================ 2. UNOS NALOGA (varijanta D, boje sredine C)
ELEMS = [
    (1, 820, 550, 16, "A", "", "A", "A", "", 1), (2, 820, 520, 4, "A", "", "A", "A", "", 1), (3, 140, 520, 1, "A", "", "A", "A", "134X520", 2),
    (4, 480, 550, 2, "A", "", "A", "A", "", 1), (6, 464, 80, 4, "A", "", "", "", "", 2),
    (27, 1050, 140, 1, "M", "M", "M", "M", "1050X120", 2), (37, 1030, 340, 14, "A", "A", "A", "A", "RASTER 150 64", 1),
]
BAND = {"A": "1/22 JELA TAVERNA", "M": "MEL-ISTI", "": ""}
erows = []
for rb, L, Wd, kom, l, d, g, dol, nap, pr in ELEMS:
    bands = sorted({BAND[x] for x in (l, d, g, dol) if x})
    warn = ' <span class="tag warn">2 prolaza</span>' if pr == 2 else ""
    erows.append('<tr><td class="r" style="color: var(--muted);">%d</td><td class="r" style="font-weight: 700;">%d</td><td class="r" style="font-weight: 700;">%d</td><td class="r">%d</td>'
                 '<td>%s</td><td class="mono" style="font-size: 12px;">%s</td><td style="color: var(--muted);"><span class="mono" style="font-size: 12px;">%s</span>%s</td></tr>'
                 % (rb, L, Wd, kom, rubv(l, d, g, dol), " · ".join(bands) if bands else "—", nap, warn))

MATS = [("IV BIJELI NK 18", "53 st. · 174 kom · 50,4 m²", "nesting"), ("IV JELA TAVERNA 19", "35 · 48 · 25,6 m²", "nesting"),
        ("MDF BIJELI 3", "22 · 27 · 16,1 m²", "pila"), ("IV BIJELI NK 16", "10 · 28 · 4,6 m²", "pila"),
        ("IV HRAST RELIEF CARDAMOM 19", "1 · 1 · 1,9 m²", "pila"), ("RP BASANIT SAND (ploča stola 900)", "2 · 2 · 2 × cijela", "pila")]


def matlist(active=None, extra=None):
    out = []
    for i, (n, m, p) in enumerate(MATS):
        e = (extra[i] if extra else '<span><span class="tag %s">%s</span></span>' % ("nest" if p == "nesting" else "pila", p))
        out.append('<div class="mat%s"><b>%s</b><span class="m">%s</span>%s</div>' % (" on" if i == active else "", n, m, e))
    return "".join(out)


left2 = ('<div class="pane"><div class="hd"><span class="lbl">Materijali</span><span style="flex: 1;"></span><span class="mono" style="font-size: 12px; color: var(--muted);">6</span></div>'
         + matlist(0) +
         '<div style="padding: 10px 14px;"><button class="btn ghost" style="width: 100%;">+ Materijal</button></div>'
         '<div class="hd" style="border-top: 1px solid var(--line2);"><span class="lbl">Ostalo u nalogu</span></div>'
         '<div class="mat"><b>Okov</b><span class="m">16 stavki · 3 za potvrdu</span></div>'
         '<div class="mat"><b>Obrade i usluge</b><span class="m">popunjava ured pri obračunu</span></div>'
         '<div style="flex: 1;"></div><div style="padding: 9px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Nalog: 123 st. · 280 kom · 103,1 m²</div></div>')

entry2 = ('<div style="display: grid; grid-template-columns: 210px minmax(0, 1fr); gap: 14px; padding: 12px 14px; border-bottom: 1px solid var(--line2); background: #FBFAF6;">'
          '<div style="display: flex; flex-direction: column; gap: 8px;">'
          '<div><div class="lbl">1. mjera (god)</div><div class="inp big foc">564</div><div class="note" style="margin-top: 3px;">god: — <span style="opacity: .8;">(materijal bez goda, Winstore Grain = 0)</span></div></div>'
          '<div><div class="lbl">2. mjera</div><div class="inp big">520</div></div>'
          '<div><div class="lbl">Kom</div><div class="inp big" style="width: 110px;">2</div></div>'
          '<div><div class="lbl">Napomena · etiketa 14 znakova</div><div class="inp"><span class="ph">gotova mjera, CNC skica…</span><span class="mono" style="margin-left: auto; font-size: 11px; color: var(--muted);">0/14</span></div></div>'
          '<div style="display: flex; gap: 6px; margin-top: 2px;"><button class="btn pri" style="flex: 1; padding: 9px;">Prihvati <span class="kbd" style="margin-left: 6px;">↵</span></button><button class="btn">Ažuriraj</button><button class="btn">Obriši</button></div>'
          '</div>'
          '<div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">'
          '<div style="display: flex; justify-content: space-between; width: 520px;">'
          '<div><div class="lbl" style="color: var(--mel);">MEL-ISTI · ista boja 0,5 mm</div><div class="inp" style="min-height: 32px; padding: 4px 10px; width: 200px;"><span class="mono">MEL-ISTI</span><span style="margin-left: auto; color: var(--muted);">▾</span></div></div>'
          '<div><div class="lbl" style="color: var(--abs);">ABS · zadano ABS-ISTI = 1 mm</div><div class="inp" style="min-height: 32px; padding: 4px 10px; width: 220px;"><span class="mono">ABS-ISTI</span><span style="margin-left: auto; color: var(--muted);">▾</span></div></div>'
          '</div>' + board(564, 520, "A", "", "A", "M", {"A": "ABS-ISTI", "M": "MEL-ISTI", "": ""}) + '</div></div>')

centre2 = ('<div class="pane"><div class="hd"><div style="min-width: 0;"><div class="lbl">Aktivni materijal</div>'
           '<div style="font-weight: 700; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">IV000090 · IVERAL BIJELI NK W908 ST2 18 MM <span style="color: var(--muted); font-weight: 500; font-size: 13px;">18 mm · bez goda · W908ST2-18</span></div></div>'
           '<div style="flex: 1;"></div><span class="tag nest">nesting</span><span class="tag">Winstore 13</span></div>'
           + entry2 +
           '<div style="overflow: hidden;"><table><thead><tr><th class="r">#</th><th class="r">1. mjera</th><th class="r">2. mjera</th><th class="r">kom</th><th>Rubovi</th><th>Traka</th><th>Napomena (etiketa)</th></tr></thead>'
           '<tbody>' + "".join(erows) + '<tr><td colspan="7" style="text-align: center; color: var(--muted); padding: 6px;">… još 47 redaka (53 stavke, 174 kom) · <a href="#">sve</a></td></tr></tbody></table></div>'
           '<div style="flex: 1;"></div>'
           '<div style="padding: 7px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted); display: flex; gap: 14px; flex-wrap: wrap;">'
           '<span><span class="kbd">Enter</span> prihvati (mjere ostaju — serije)</span><span><span class="kbd">Tab</span> sljedeće polje</span><span>rubovi: klik mišem na M / A uz dasku</span><span>klik na redak → daska ga prikaže</span>'
           '<span style="margin-left: auto; color: var(--acc);">primjer: 564 × 520 · L i G = ABS-ISTI (1 mm) · B = MEL-ISTI (0,5) · D bez ruba</span></div></div>')

right2 = ('<div style="display: flex; flex-direction: column; gap: 12px; min-height: 0;">'
          + pane("Trake ovog materijala", '<div class="bd" style="gap: 7px;">'
                 '<div style="display: flex; justify-content: space-between; gap: 8px;"><span><span class="dot mel"></span><span class="mono">MEL-ISTI</span></span><span class="mono" style="font-size: 12px; color: var(--muted);">TR000017 · 0,5</span></div>'
                 '<div style="display: flex; justify-content: space-between; gap: 8px;"><span><span class="dot abs"></span><span class="mono">ABS-ISTI</span></span><span class="mono" style="font-size: 12px; color: var(--muted);">TR000168 · 1 mm ▾</span></div>'
                 '<div style="display: flex; justify-content: space-between; gap: 8px;"><span><span class="dot abs"></span><span class="mono">1/22 JELA TAVERNA</span></span><span class="mono" style="font-size: 12px; color: var(--muted);">TR001254 <span class="addr">R2-07-A</span></span></div>'
                 '<div style="color: var(--muted);">+ druga boja… <span style="font-size: 12px;">traži ident</span></div></div>')
          + pane("Materijal", bd('Ploča <b>2800 × 2070</b> · glodalo <b>8D</b> · 2 prolaza', '<span class="dot"></span>Winstore <b>13</b> ploča (izvoz 11.09.) · restlovi 0',
                                  '<span class="dot info"></span>Put: prijedlog <span class="tag nest">nesting</span> <span style="color: var(--muted);">(50 m² ≫ 1 ploča)</span>',
                                  '<span class="note">Aliasi: IV BIJELI NK 18MM · IV_BIJELI_NK_18_MM</span>'))
          + pane("Ovaj materijal", bd('<b>53 st. · 174 kom</b> · 50,37 m²', 'Trake: <b>208,2 m</b> ABS · <b>21,8 m</b> MEL (PW metri)', 'Obračun: <b>10 pl. · 57,96 m²</b> (PW-metoda)', '<span class="dot warn"></span>2 elementa &lt; 200 mm → 2 prolaza'))
          + pane("Provjere", bd('<span class="dot"></span>Winstore kod i ploča za sve materijale', '<span class="dot"></span>sve trake mapirane na TR ident', '<span class="dot"></span>0 elemenata s oznakom PROVJERI',
                                 '<span class="dot info"></span>IV JELA TAVERNA 19: Winstore 0 — skladište se provjerava nakon potvrde kupca', size="12.5px", gap="5px"),
                 '<span style="flex: 1;"></span><span class="tag ok">sve u redu</span>', style="flex: 1;")
          + '</div>')
foot2 = ('<div class="kpi"><b>123 · 280</b><span>stavki · kom (nalog)</span></div><div class="kpi"><b>103,1 m²</b><span>dijelova</span></div><div class="kpi"><b>6</b><span>materijala · 2 nesting · 4 pila</span></div>'
         '<div style="flex: 1;"></div><button class="btn">Spremi kao nacrt</button><button class="btn pri">Dalje: ponuda →</button>')
ACT2 = '<button class="tbtn">Uvoz ▾</button><button class="tbtn">Zaglavlje</button><button class="tbtn pri">Spremi</button>'
W["Main.dc.html"] = screen("Production Hub v0.4 — Unos naloga", ORDER_CRUMB, 0, ACT2, "nalozi", "236px minmax(0, 1fr) 292px", [left2, centre2, right2], foot2)

# ================================================================ 3. OKOV I OBRADE (isti raspored)
OKOV = [
    ("Blenda mat crna", 3, "OK001850", "SOKLA 4000X100 MM BIJELA/CRNA MAT", "KOM", "ai"),
    ("Drzac blende", 30, "OK000060", "PRIHVAT ZA PVC NOGU", "KOM", "ai"),
    ("Kut cokla crni", 4, "OK001176", "MULTICORNER 100MM BIJELI / CRNI", "KOM", "ok"),
    ("Noga pvc 10 cm", 60, "OK000218", "PVC NOGA 100", "KOM", "ok"),
    ("Blum antaro 500M", 2, "OK001136", "TANDEMBOX BLUM ANTARO M 500MM - KOMPLET", "KPT", "ok"),
    ("Blum antaro 500C", 1, "OK001137", "TANDEMBOX BLUM ANTARO C 500MM - KOMPLET", "KPT", "ok"),
    ("Blum antaro 500D", 11, "OK001138", "TANDEMBOX BLUM ANTARO D 500MM - KOMPLET", "KPT", "ok"),
    ("Prednji dio za INTIVO i ANTARO SB, ZC 09Z31L1036", 1, "OK000376", "FRONTA ZA UNUTARNJU LADICU *BLUM", "KOM", "ai"),
    ("Spojnice ravne blum sa usp", 30, "OK000596", "MET.SPOJNICA RAVNA *BLUM BLUMOTION", "KOM", "ok"),
    ("Spojnice 170", 12, "OK000347", "MET.SPOJNICA 170° *BLUM", "KOM", "ok"),
    ("Spojnice slijepe sa usp", 10, "OK000656", "MET.SPOJNICA SLJEPA *BLUMOTION", "KOM", "ok"),
    ("Podloska za slijepe sa reg", 10, "OK000363", "PODLOŠKA SLJEPA/ZGLOBNA *BLUM", "KOM", "ok"),
    ("Podloska sa reg", 42, "OK000547", "PODLOŠKA REGULACIJSKA *BLUM", "KOM", "ok"),
    ("Košara soft PRO LINE orion siva - 150 mm", 1, "OK004248", "METALNA KOŠARA 150 SIGE PRO LINE 2X", "KOM", "ok"),
    ("Nosac polica metalni", 200, "OK000210", "DRŽAČ POLICE MET 5 MM", "KOM", "ok"),
    ("Nosac visecih elemenata direktni", 20, "OK000040", "NOSAČ GOR.ELEM. - KUTNIK", "KOM", "ok"),
]
orows = []
for i, (txt, kom, ident, naz, jm, st) in enumerate(OKOV, 1):
    badge = '<span class="tag ok">potvrđeno</span>' if st == "ok" else '<span class="tag warn">za potvrdu</span>'
    orows.append('<tr%s><td class="r" style="color: var(--muted);">%d</td><td style="color: var(--muted); overflow: hidden; text-overflow: ellipsis;">%s</td>'
                 '<td style="overflow: hidden; text-overflow: ellipsis;"><span class="mono" style="font-size: 12px;">%s</span> %s</td><td class="r" style="font-weight: 700;">%d</td><td style="color: var(--muted);">%s</td><td>%s</td></tr>'
                 % (' class="sel"' if i == 1 else "", i, txt, ident, naz, kom, jm, badge))
left3 = ('<div class="pane"><div class="hd"><span class="lbl">Materijali</span><span style="flex: 1;"></span><span class="mono" style="font-size: 12px; color: var(--muted);">6</span></div>'
         '<div style="max-height: 345px; overflow: hidden;">' + matlist(None, extra=[""] * 6) + '</div>'
         '<div class="hd" style="border-top: 1px solid var(--line2);"><span class="lbl">Ostalo u nalogu</span></div>'
         '<div class="mat on"><b>Okov</b><span class="m">16 stavki · 3 za potvrdu</span><span><span class="tag">kupac: OKOV (48).xlsx</span></span></div>'
         '<div class="mat"><b>Obrade i usluge</b><span class="m">10 stavki · ured pri obračunu</span><span><span class="tag">CNC · bušenje · nut · LED</span></span></div>'
         '<div style="flex: 1;"></div><div style="padding: 9px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Sve tri grupe idu u istu ponudu (eSlog XML)</div></div>')
centre3 = ('<div class="pane"><div class="hd"><div><div class="lbl">Okov</div><div style="font-weight: 700; font-size: 15px;">Popis okova za nalog <span style="color: var(--muted); font-weight: 500; font-size: 13px;">· izvor: Excel kupca (uvezen 18.08.) · identi prepoznati automatski, potvrđuje unosilac</span></div></div>'
           '<div style="flex: 1;"></div><button class="btn">Uvezi Excel / foto</button><button class="btn">Iz Corpusa</button></div>'
           '<div style="display: flex; gap: 8px; padding: 10px 14px; border-bottom: 1px solid var(--line2); background: #FBFAF6; align-items: center;">'
           '<div class="inp foc" style="flex: 1;"><span class="ph">traži okov: naziv, ident ili kako kupac piše (npr. „spojnice 170“)…</span></div><div class="inp big" style="width: 90px;">1</div>'
           '<button class="btn pri" style="padding: 9px 14px;">Dodaj <span class="kbd" style="margin-left: 6px;">↵</span></button></div>'
           '<div style="overflow: hidden;"><table style="table-layout: fixed;"><thead><tr><th class="r" style="width: 40px;">#</th><th style="width: 200px;">Kupac napisao</th><th>Pantheon ident · naziv</th><th class="r" style="width: 56px;">kom</th><th style="width: 46px;">JM</th><th style="width: 118px;">Status</th></tr></thead>'
           '<tbody>' + "".join(orows) + '</tbody></table></div><div style="flex: 1;"></div>'
           '<div style="padding: 7px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted); display: flex; gap: 14px; flex-wrap: wrap;">'
           '<span><span class="kbd">Enter</span> dodaj</span><span>ident u retku mijenja se klikom na njega</span><span>Redak bez identa ne ide u ponudu — Hub ga javi u provjerama.</span></div></div>')
right3 = ('<div style="display: flex; flex-direction: column; gap: 12px; min-height: 0;">'
          + pane("Okov — sažetak", bd('<b>16 stavki</b> · 13 potvrđeno · <span style="color: var(--warn); font-weight: 600;">3 za potvrdu</span>', 'Vrijednost (cjenik, bez rabata): <b>1.068 €</b>', '<span class="note">Kupčev popis ima 103 retka (predložak); Hub uzima samo retke s količinom.</span>'))
          + pane("Kako se prepoznaje ident", bd('1. alias-tablica okova (kako kupci pišu → ident) — bez pitanja', '2. bez aliasa → ident se prepozna po nazivu i dobije oznaku <span class="tag warn">za potvrdu</span>', '3. potvrđeni par se upiše u alias-tablicu → idući put bez pitanja', '<span style="color: var(--ink);">Ništa ne ide u ponudu bez potvrde unosioca.</span>', size="12.5px"))
          + pane("Obrade i usluge", bd('US000148 P-bušenja 5/8 mm · <b>569 kom</b>', 'US000005 rezanje CNC · <b>1,98 m</b> · US000087 nut kant · <b>5,38 m</b>', 'US002089 urez za LED profil · <b>1,04 m</b> · US000245 glodanje za ručkicu · <b>25 kom</b>', 'US000303 rezanje radne ploče · <b>2 kom</b> · US000015 spoj · <b>2 kom</b>', '<span class="note">Upisuje ured pri obračunu (D-38); za Corpus naloge Hub ih predlaže iz CIX-a.</span>', size="12.5px", gap="5px"), '<span style="flex: 1;"></span><span class="tag">10</span>')
          + pane("U ponudu (eSlog)", bd('1. materijali: ploče + rezanje + trake + kantiranje', '2. okov (16)', '3. obrade i usluge (10)', '<span style="color: var(--ink);">Jedan XML, redoslijed kao u današnjim ponudama.</span>', size="12.5px", gap="4px"), style="flex: 1;")
          + '</div>')
foot3 = ('<div class="kpi"><b>123 · 280</b><span>stavki · kom (nalog)</span></div><div class="kpi"><b>16</b><span>okov (3 za potvrdu)</span></div><div class="kpi"><b>10</b><span>obrade i usluge</span></div>'
         '<div style="flex: 1;"></div><span style="font-size: 13px;"><span class="dot warn"></span>Provjere: 3 stavke okova bez potvrde</span><button class="btn pri">Dalje: ponuda →</button>')
W["v04_Okov.dc.html"] = screen("Production Hub v0.4 — Okov i obrade", ORDER_CRUMB, 0, ACT2, "nalozi", "236px minmax(0, 1fr) 292px", [left3, centre3, right3], foot3)

# ================================================================ 4. PONUDA IZ HUBA (obračun → ponuda → „Pošalji kupcu“; D-40)
STAVKE = [
    ("IV BIJELI NK 18 — 10 ploča (PW-metoda) · W908ST2-18", [
        ("IV000090", "IVERAL BIJELI NK W908 ST2 18 MM", 57.96, "M2", 14.34, "10 × 5,796 m² − korisni ostatci"),
        ("US000002", "USLUGA REZANJA", 57.96, "M2", 2.55, "= m² ploča"),
        ("TR001254", "ABS 1/22 JELA CLAY", 209, "M", 1.20, "PW 208,2 m → naviše na metar"),
        ("US000011", "USLUGA KANTIRANJA 2/22", 208.2, "M", 1.30, "točno PW metri"),
        ("TR000017", "ABS 0,5/22 BIJELI NK", 22, "M", 0.25, "PW 21,8 m → naviše"),
        ("US000003", "USLUGA KANTIRANJA 0,5/22", 21.8, "M", 0.87, "")]),
    ("IV JELA TAVERNA 19 — 6 ploča, uzdužno (god) · K2665AI-19", [
        ("IV001210", "IVERAL JELA TAVERNA K2665 AI 19MM", 30.16, "M2", 31.00, "PW brojka; ručni ispravci više nisu mogući"),
        ("US000002", "USLUGA REZANJA", 30.16, "M2", 2.55, ""),
        ("TR001254", "ABS 1/22 JELA CLAY", 152, "M", 1.20, "PW 151,3 m → naviše"),
        ("US000011", "USLUGA KANTIRANJA 2/22", 151.3, "M", 1.30, ""),
        ("TR001258", "ABS 1/44 JELA CLAY", 7, "M", 5.25, "PW 6,8 m → naviše"),
        ("US000012", "USLUGA KANTIRANJA 2/44", 6.8, "M", 2.40, "")]),
    ("MDF BIJELI 3 — 4 ploče", [("IV000054", "MDF BIJELI 3 MM", 18.49, "M2", 5.00, ""), ("US000013", "USLUGA REZANJA MDF", 18.49, "M2", 1.25, "")]),
    ("IV BIJELI NK 16 — 1 ploča", [("IV000002", "IVERAL BIJELI NK W908 ST2 16MM", 5.80, "M2", 14.50, ""), ("US000002", "USLUGA REZANJA", 5.80, "M2", 2.55, ""),
                                  ("TR000017", "ABS 0,5/22 BIJELI NK", 51, "M", 0.25, "PW 50,9 m → naviše"), ("US000003", "USLUGA KANTIRANJA 0,5/22", 50.9, "M", 0.87, "")]),
    ("IV HRAST RELIEF CARDAMOM 19 — 1 ploča (god)", [("IV001219", "IVERAL HRAST RELIEF CARDAMOM K2776 GR 19MM", 2.73, "M2", 22.00, ""),
                                                            ("US000002", "USLUGA REZANJA", 2.73, "M2", 2.55, ""), ("TR001213", "ABS 1/22 HRAST RELIEF PIMENTO", 7, "M", 1.20, "PW 6,6 m → naviše"),
                                                            ("US000011", "USLUGA KANTIRANJA 2/22", 6.6, "M", 1.30, "")]),
    ("RP BASANIT SAND — ploča stola 900 mm: 2880 i 2110 → 2 × cijela", [
        ("RP000136", "PLOČA STOLA CIJELA · BASANIT SAND 2880X900 1K + 2110X900 1K", 2, "KOM", 330.00, "900 mm: pola / cijela — oba elementa > 2,05 m")]),
]
USLUGE = [("US000148", "USLUGA P-BUŠENJA 5/8 MM", 569, "KOM", 0.275), ("US000005", "USLUGA REZANJA CNC", 1.98, "M", 6.49), ("US000087", "USLUGA NUT KANT", 5.38, "M", 1.75),
          ("US002089", "USLUGA UREZIVANJA ZA LED PROFIL", 1.04, "M", 5.80), ("US000007", "USLUGA LJEPLJENJA PLOČA", 1.10, "M2", 8.75), ("US000245", "USLUGA GLODANJA ZA RUČKICU", 25, "KOM", 1.33),
          ("US000686", "USLUGA PLASTIFICIRANJA", 8.20, "M", 7.20), ("US000055", "ALU. VRATA PO SPECIFIKACIJI", 1, "KPT", 184.00), ("US000303", "USLUGA REZANJA RADNE PLOČE", 2, "KOM", 3.00),
          ("US000015", "USLUGA SPOJ RADNE PLOČE", 2, "KOM", 9.00)]
OKOV_SUM = 1068.0
# rabat kupca (D-40): dvije stope po kupcu iz šifrarnika kupaca Huba — Humer: 15 % materijal + okov + ostalo, 20 % rezanje i kantiranje (ponuda 2823)
RAB_USL = {"US000002", "US000003", "US000011", "US000012", "US000013", "US000303"}
RAB_M, RAB_U = 0.15, 0.20


def rab(ident):
    return RAB_U if ident in RAB_USL else RAB_M


def net(kol, cij, ident):
    return round(kol * cij * (1 - rab(ident)), 2)


def pct(r):
    return "%d %%" % round(r * 100)


mat_total = sum(net(k, c, i) for _, items in STAVKE for i, _, k, _, c, _ in items)
okov_total = round(OKOV_SUM * (1 - RAB_M), 2)
usl_total = sum(net(k, c, i) for i, _, k, _, c in USLUGE)
neto = mat_total + okov_total + usl_total
pdv = round(neto * 0.25, 2)
r4 = []
COLLAPSE = {"MDF BIJELI 3 — 4 ploče", "IV BIJELI NK 16 — 1 ploča", "IV HRAST RELIEF CARDAMOM 19 — 1 ploča (god)"}
for grp, items in STAVKE:
    gsum = sum(net(k, c, i) for i, _, k, _, c, _ in items)
    if grp in COLLAPSE:
        r4.append('<tr class="grp"><td colspan="2" style="overflow: hidden; text-overflow: ellipsis;">%s <span class="note" style="font-weight: 500;">· %d stavke</span></td><td colspan="3" class="r"><span class="note">sažeto · <a href="#">otvori</a></span></td><td class="r num">%s</td><td></td></tr>' % (grp, len(items), eur(gsum)))
        continue
    r4.append('<tr class="grp"><td colspan="7">%s</td></tr>' % grp)
    show = items if grp.startswith("IV BIJELI NK 18") else items[:2]
    for ident, naz, kol, jm, cij, nap in show:
        r4.append('<tr><td class="mono" style="font-size: 12px;">%s</td><td style="overflow: hidden; text-overflow: ellipsis;">%s</td><td class="r num"><b>%s</b> %s</td><td class="r num">%s</td><td class="r num" style="color: var(--muted);">%s</td><td class="r num">%s</td><td style="overflow: hidden; text-overflow: ellipsis;"><span class="note">%s</span></td></tr>'
                  % (ident, naz, q(kol), jm, q(cij), pct(rab(ident)), eur(net(kol, cij, ident)), nap))
    if len(show) < len(items):
        r4.append('<tr><td colspan="5" style="color: var(--muted); padding: 4px 10px;">… još %d stavke (trake, kantiranje)</td><td class="r num" style="color: var(--muted);">Σ %s</td><td></td></tr>' % (len(items) - len(show), eur(gsum)))
r4.append('<tr class="grp"><td colspan="7">Okov — 16 stavki iz kupčevog popisa (OKOV (48).xlsx) · <span class="tag warn">3 za potvrdu</span> · <a href="#">otvori Okov</a></td></tr>')
r4.append('<tr><td class="mono" style="font-size: 12px;">OK…</td><td style="overflow: hidden; text-overflow: ellipsis;">16 stavki (Blum, Tandembox, noge, sokla…)</td><td class="r num"></td><td class="r num"></td><td class="r num" style="color: var(--muted);">%s</td><td class="r num">%s</td><td style="overflow: hidden; text-overflow: ellipsis;"><span class="note">cjenik %s − 15 %%</span></td></tr>' % (pct(RAB_M), eur(okov_total), eur(OKOV_SUM)))
r4.append('<tr class="grp"><td colspan="7">Obrade i usluge — 10 stavki · upisuje ured pri obračunu <span class="tag">IVANA · 18.08.</span></td></tr>')
for ident, naz, kol, jm, cij in USLUGE[:2]:
    r4.append('<tr><td class="mono" style="font-size: 12px;">%s</td><td>%s</td><td class="r num"><b>%s</b> %s</td><td class="r num">%s</td><td class="r num" style="color: var(--muted);">%s</td><td class="r num">%s</td><td></td></tr>' % (ident, naz, q(kol), jm, q(cij), pct(rab(ident)), eur(net(kol, cij, ident))))
r4.append('<tr><td colspan="5" style="color: var(--muted); padding: 4px 10px; overflow: hidden; text-overflow: ellipsis;">… još 8 stavki (nut, LED urez, ljepljenje, ručkice, plastificiranje, ALU vrata, RP — rezanje RP 20 %%)</td><td class="r num" style="color: var(--muted);">Σ %s</td><td></td></tr>' % eur(usl_total))

left4 = ('<div class="pane"><div class="hd"><span class="lbl">Ponuda</span><span style="flex: 1;"></span><span class="tag info">2026-02823 · v3</span></div>'
         '<div class="mat on"><b>Sve stavke</b><span class="m">materijali · okov · usluge</span></div>'
         '<div class="mat"><b>Materijali</b><span class="m">6 grupa · %s €</span></div>'
         '<div class="mat"><b>Okov</b><span class="m">16 stavki · %s € · 3 za potvrdu</span></div>'
         '<div class="mat"><b>Obrade i usluge</b><span class="m">10 stavki · %s €</span></div>'
         '<div class="hd" style="border-top: 1px solid var(--line2);"><span class="lbl">Verzije</span></div>'
         '<div class="bd" style="gap: 5px; font-size: 12.5px;"><div><span class="mono">v1</span> 18.08. poslana · Ivana</div><div><span class="mono">v2</span> 20.08. poslana · kupac dodao okov</div><div><span class="mono">v3</span> <b>nacrt</b> · radna ploča 2 × cijela</div>'
         '<div class="note">Svaka poslana verzija čuva svoj PDF i tekst maila.</div></div>'
         '<div class="hd" style="border-top: 1px solid var(--line2);"><span class="lbl">Količine iz</span></div>'
         '<div class="bd" style="gap: 6px;"><span class="radio"><i class="on"></i> PanelWizard (paralelni rad)</span><span class="radio"><i></i> Hub optimizator <span class="note">(+3,6 %%)</span></span></div>'
         '<div style="flex: 1;"></div><div style="padding: 9px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Cijene iz Pantheona (sinkronizacija svako jutro) — u Hubu se ne mijenjaju. Rabat po kupcu iz šifrarnika kupaca Huba.</div></div>'
         % (eur(mat_total), eur(okov_total), eur(usl_total)))
centre4 = ('<div class="pane"><div class="hd"><div style="min-width: 0;"><div class="lbl">Stavke ponude</div><div style="font-weight: 700; font-size: 15px;">2026-02823 · v3 <span style="color: var(--muted); font-weight: 500; font-size: 13px;">· cijene Pantheon 12.09. 06:00 · rabat kupca Humer: <b style="color: var(--ink);">15 %</b> materijal, okov i ostalo · <b style="color: var(--ink);">20 %</b> rezanje i kantiranje</span></div></div>'
           '<div style="flex: 1;"></div><span class="tag info">nacrt · nije poslana</span></div>'
           '<div style="overflow: hidden;"><table style="table-layout: fixed;"><thead><tr><th style="width: 84px;">Ident</th><th>Naziv (Pantheon)</th><th class="r" style="width: 94px;">Količina</th><th class="r" style="width: 60px;">Cijena</th><th class="r" style="width: 54px;">Rabat</th><th class="r" style="width: 82px;">Iznos €</th><th style="width: 176px;">Pravilo / napomena</th></tr></thead>'
           '<tbody>' + "".join(r4) + '</tbody></table></div><div style="flex: 1;"></div>'
           '<div style="padding: 7px 14px; border-top: 1px solid var(--line2); display: flex; gap: 14px; align-items: baseline; font-size: 12px; color: var(--muted); white-space: nowrap;">'
           '<span>materijali <b>%s</b> · okov <b>%s</b> · usluge <b>%s</b></span>'
           '<span style="margin-left: auto; color: var(--ink); font-size: 13px;">Bez PDV-a <b>%s</b></span><span style="color: var(--ink); font-size: 13px;">PDV 25 %% <b>%s</b></span><span style="font-size: 15px; color: var(--ink);">Ukupno <b>%s €</b></span></div></div>'
           % (eur(mat_total), eur(okov_total), eur(usl_total), eur(neto), eur(pdv), eur(neto + pdv)))
right4 = ('<div style="display: flex; flex-direction: column; gap: 12px; min-height: 0;">'
          + pane("Slanje kupcu", '<div class="bd" style="gap: 5px; font-size: 12.5px;">'
                 '<div class="inp" style="min-height: 32px; padding: 4px 10px; font-size: 13px;"><span class="lbl" style="margin-right: 2px;">Za</span>Humer · e-mail iz šifrarnika<span style="margin-left: auto; color: var(--muted);">▾</span></div>'
                 '<div><span class="lbl">Od</span> <span class="mono" style="font-size: 12px;">ponuda@paneliprojekt.hr</span> <span class="note">· odgovori na paneli@</span></div>'
                 '<div><span class="lbl">Predmet</span> Ponuda 2026-02823 — HUMER_OMIS_2823 (v3)</div>'
                 '<div><span class="lbl">Privitak</span> <span class="mono" style="font-size: 12px;">Ponuda_2026-02823_v3.pdf</span> <span class="note">· tekst iz predloška</span></div>'
                 '<button class="btn pri" style="margin-top: 3px; padding: 9px;">Pošalji kupcu</button>'
                 '<div class="note">Hub čuva točan PDF i tekst uz verziju. Šalju Ivana i Goran.</div></div>', '<span style="flex: 1;"></span><span class="tag ok">spremna</span>')
          + pane("Stanje ponude", '<div class="bd" style="gap: 6px;">'
                 '<div><span class="step wrap"><span class="s done">✓</span>Nacrt v3 · obračun PW-metodom (Ivana)</span></div>'
                 '<div><span class="step wrap"><span class="s now">2</span><b>Pošalji kupcu</b> · PDF + e-mail iz Huba</span></div>'
                 '<div><span class="step wrap"><span class="s">3</span>Čeka potvrdu kupca · podsjetnik nakon 7 dana</span></div>'
                 '<div><span class="step wrap"><span class="s">4</span>Kupac potvrdio → datum, način, rok → eSlog u Pantheon → skladište</span></div>'
                 '<div class="note">Do potvrde ništa se ne rezervira i ništa ne ide u Pantheon.</div></div>')
          + pane("Provjere", bd('<span class="dot"></span>svaki materijal ima stavku (6 / 6) · ploče = PW brojke · trake naviše na metar', '<span class="dot"></span>rabat kupca 15 % / 20 % · e-mail kupca u šifrarniku',
                                 '<span class="dot warn"></span>okov: 3 stavke čekaju potvrdu identa', size="12.5px", gap="5px"), '<span style="flex: 1;"></span><span class="tag warn">1</span>')
          + pane("Pantheon", bd('eSlog ponude ide sam uz „Kupac potvrdio“ (ponuda → račun); Pantheonov broj vraća se u nalog.', '<span class="note">Hub nikad ne piše u Pantheon bazu. <a href="#">Pošalji u Pantheon odmah</a> — iznimka.</span>', size="12.5px", gap="5px"), style="flex: 1;")
          + '</div>')
foot4 = ('<div class="kpi"><b>%s €</b><span>materijali (ploče, rezanje, trake)</span></div><div class="kpi"><b>%s €</b><span>okov</span></div><div class="kpi"><b>%s €</b><span>obrade i usluge</span></div><div class="kpi"><b>%s €</b><span>bez PDV-a</span></div><div class="kpi"><b>%s €</b><span>s PDV-om</span></div>'
         '<div style="flex: 1;"></div><button class="btn">Nova verzija</button><button class="btn pri">Pošalji kupcu</button>'
         % (eur(mat_total), eur(okov_total), eur(usl_total), eur(neto), eur(neto + pdv)))
ACT4 = '<button class="tbtn">Pregled PDF</button><button class="tbtn">Excel</button><button class="tbtn pri">Pošalji kupcu</button>'
W["v04_Ponuda.dc.html"] = screen("Production Hub v0.4 — Obračun → ponuda iz Huba", ORDER_CRUMB_HUB, 1, ACT4, "nalozi", "236px minmax(0, 1fr) 292px", [left4, centre4, right4], foot4)

# ================================================================ 4b. DIJALOG „KUPAC POTVRDIO“ (ured; D-40 + rokovi/osobe iz 10 §4)
def fld(label, value, w="100%", foc=False, note=""):
    return ('<div style="display: flex; flex-direction: column; gap: 4px; width: %s;"><div class="lbl">%s</div><div class="inp%s" style="min-height: 36px;">%s</div>%s</div>'
            % (w, label, " foc" if foc else "", value, ('<div class="note">%s</div>' % note) if note else ""))


potvrda_body = (
    '<div style="display: flex; flex-direction: column; gap: 14px;">'
    '<div style="display: flex; align-items: flex-start; gap: 12px;"><div style="min-width: 0;"><div class="lbl">Kupac potvrdio ponudu</div>'
    '<div style="font-weight: 700; font-size: 18px;">2026-02823 · v3 <span style="color: var(--muted); font-weight: 500; font-size: 13px;">· HUMER_OMIS_2823</span></div>'
    '<div class="note">poslana 11.09. 14:20 (Ivana) · kupac odgovorio nakon 1 dana</div></div><span style="flex: 1;"></span><span class="tag abs">čeka potvrdu kupca</span></div>'
    '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">'
    + fld("Datum potvrde", '<b>12.09.2026</b>', foc=True)
    + '<div style="display: flex; flex-direction: column; gap: 4px;"><div class="lbl">Način</div><div style="display: flex; gap: 14px; min-height: 36px; align-items: center;"><span class="radio"><i></i> e-mail</span><span class="radio"><i class="on"></i> telefon</span><span class="radio"><i></i> osobno</span></div></div>'
    + fld("Rok obećan kupcu · službeni", '<b>26.09.2026</b><span style="margin-left: auto;" class="note">10 radnih dana</span>', note="po njemu planira proizvodnja")
    + fld("Rok koji kupac traži · napomena", '<span style="color: var(--ink);">„do kraja mjeseca“</span>')
    + fld("Prioritet", 'normalan<span style="margin-left: auto; color: var(--muted);">▾</span>')
    + fld("Potvrdio", 'IVANA <span class="note" style="margin-left: 8px;">12.09. 08:15 · automatski iz prijave</span>')
    + '</div>'
    '<div style="border: 1px solid var(--line); border-radius: 8px; background: #FBFAF6; padding: 10px 12px; display: flex; flex-direction: column; gap: 6px; font-size: 12.5px;">'
    '<div class="lbl" style="color: var(--acc);">Što Hub napravi na „Potvrdi“</div>'
    '<div><span class="dot"></span>ponuda v3 zaključana · status <b>Potvrđeno</b> · zapis u dnevniku događaja</div>'
    '<div><span class="dot"></span>eSlog ponude → Pantheon (ponuda → račun), cijena i rabat po stavci iz Huba · Pantheonov broj ponude vraća se u nalog</div>'
    '<div><span class="dot"></span>provjera skladišta: rezervacija za ovaj nalog, upozorenje i manjak u Nabavu</div></div>'
    '<div style="display: flex; align-items: center; gap: 8px; font-size: 13px;"><span style="width: 16px; height: 16px; border-radius: 3px; background: var(--acc); color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700;">✓</span>Pošalji eSlog u Pantheon odmah <span class="note">(inače kasnije iz ponude)</span></div>'
    '<div style="display: flex; gap: 8px; justify-content: flex-end; border-top: 1px solid var(--line2); padding-top: 12px;"><button class="btn">Odustani</button><button class="btn pri" style="padding: 9px 16px;">Potvrdi → skladište</button></div>'
    '</div>'
)
W["v04_Potvrda.dc.html"] = card("Production Hub v0.4 — Kupac potvrdio (dijalog)", 620, 620,
                                '<div class="pane" style="margin: 24px; padding: 18px 20px; box-shadow: 0 12px 32px rgba(28, 42, 51, .14);">%s</div>' % potvrda_body)

# ================================================================ 4c. DOGAĐAJI NALOGA — vremenska crta (na klik iz Zaglavlja; 10 §1, §4)
DOG = [
    # kada, tko, iz → u, opis, stil
    ("18.08. 09:12", "IVANA", "— → Unos", "nalog otvoren · uvoz CPW iz PPW-a: 6 materijala, 123 stavke", ""),
    ("18.08. 13:40", "IVANA", "Unos → Ponuda", "v1 poslana kupcu (PDF + e-mail iz Huba)", ""),
    ("20.08. 10:05", "IVANA", "Ponuda", "nova verzija v2 — kupac dodao okov · poslana", ""),
    ("27.08. 07:00", "Hub", "Ponuda", "podsjetnik kupcu: 7 dana bez odgovora", "info"),
    ("11.09. 14:20", "IVANA", "Ponuda", "v3 — radna ploča 2 × cijela · poslana", ""),
    ("12.09. 08:15", "IVANA", "Ponuda → Potvrđeno", "telefon · rok obećan 26.09. · eSlog → Pantheon 26-010-002823", "ok"),
    ("12.09. 08:15", "Hub", "Potvrđeno → Skladište", "2 materijala bez ploča (7 pl.) → rezervacija za 4 · manjak u Nabavu", "warn"),
    ("12.09. 09:30", "SANELA", "Skladište", "narudžbenica N-2026-043 IVERPAN poslana · očekivano 16.09.", ""),
    ("12.09. 10:02", "VP", "Skladište → Pila / nesting", "put potvrđen: 2 nesting · 4 pila (2 materijala čekaju dobavu)", "ok"),
]
drows = []
for kada, tko, iz_u, opis, st in DOG:
    dot = '<span class="dot %s"></span>' % st if st else '<span class="dot info"></span>'
    drows.append('<tr><td class="mono" style="font-size: 12px; color: var(--muted);">%s</td><td><span class="tag%s">%s</span></td><td style="font-weight: 600; white-space: normal;">%s%s</td><td style="white-space: normal; color: var(--muted);">%s</td></tr>'
                 % (kada, " info" if tko == "Hub" else "", tko, dot, iz_u, opis))
drows.append('<tr><td class="mono" style="font-size: 12px; color: #B8BDC2;">—</td><td></td><td style="color: #B8BDC2; white-space: normal;">Pila / nesting → Proizvodnja → Zatvoren</td><td style="color: #B8BDC2; white-space: normal;">upisuje praćenje proizvodnje (izrezano, kantirano, isporučeno)</td></tr>')
dog_body = (
    '<div class="pane" style="margin: 20px; overflow: hidden;">'
    '<div class="hd"><div style="min-width: 0; white-space: nowrap;"><div class="lbl">Događaji naloga</div><div style="font-weight: 700; font-size: 16px;">HUMER_OMIS_2823 <span style="color: var(--muted); font-weight: 500; font-size: 13px;">· vremenska crta · otvara se iz Zaglavlja</span></div></div>'
    '<div style="flex: 1;"></div><span class="tag nest">Pila / nesting</span></div>'
    '<div style="padding: 8px 14px; border-bottom: 1px solid var(--line2);">' + steps_bar(4).replace('class="step"', 'class="step" style="font-size: 11.5px;"').replace("gap: 14px", "gap: 10px") + '</div>'
    '<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; padding: 10px 14px; border-bottom: 1px solid var(--line2); background: #FBFAF6; font-size: 12.5px;">'
    '<div><div class="lbl">Rok obećan</div><b>26.09.2026</b><div class="note">Ivana · pri potvrdi</div></div>'
    '<div><div class="lbl">Rok kupca</div>„do kraja mjeseca“<div class="note">napomena</div></div>'
    '<div><div class="lbl">Potvrda kupca</div><b>12.09.</b> · telefon<div class="note">1 dan nakon v3</div></div>'
    '<div><div class="lbl">Prioritet</div>normalan<div class="note">voditelj može promijeniti</div></div></div>'
    '<table style="table-layout: fixed;"><thead><tr><th style="width: 96px;">Kada</th><th style="width: 74px;">Tko</th><th style="width: 190px;">Status</th><th>Što</th></tr></thead><tbody>' + "".join(drows) + '</tbody></table>'
    '<div style="padding: 9px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted); display: flex; flex-direction: column; gap: 3px;">'
    '<div>Osobe po koraku: unio <b>IVANA</b> · poslao <b>IVANA</b> · potvrdio <b>IVANA</b> · nabava <b>SANELA</b> · put <b>VP</b> · operateri upisuje praćenje proizvodnje</div>'
    '<div>Događaji se ne brišu; praćenje proizvodnje i „naplaćeno vs potrošeno“ čitaju ih preko API-ja.</div></div></div>'
)
W["v04_Dogadjaji.dc.html"] = card("Production Hub v0.4 — Događaji naloga", 760, 740, dog_body)

# ================================================================ 5. SKLADIŠTE (nakon potvrde kupca)
SKL = [
    # materijal, kod, potrebno, stanje (html), restl, manjak, akcija
    ("IV BIJELI NK 18", "W908ST2-18", "10 pl.", '<span class="dot"></span>Winstore <b>13</b>', "0", "—", '<span class="tag ok">rezerviraj 10</span>'),
    ("IV JELA TAVERNA 19", "K2665AI-19", "6 pl.", '<span class="dot crit"></span>Winstore <b>0</b>', '2 kand. <span class="addr">C006</span> ?', '<b style="color: var(--crit);">6</b>', '<span class="tag crit">nabava 6</span>'),
    ("MDF BIJELI 3", "—", "4 pl.", '<span class="dot"></span>skladište <b>26</b>', "0", "—", '<span class="tag ok">rezerviraj 4</span>'),
    ("IV BIJELI NK 16", "W908ST2-16", "1 pl.", '<span class="dot crit"></span>Winstore <b>0</b>', "0", '<b style="color: var(--crit);">1</b>', '<span class="tag crit">nabava 1</span>'),
    ("IV HRAST RELIEF CARDAMOM 19", "K2776GR-19", "1 pl.", '<span class="dot"></span>skladište <b>1</b>', "nema", "—", '<span class="tag ok">rezerviraj 1</span>'),
    ("RP BASANIT SAND (900)", "—", "2 cijele", '<span class="dot"></span>skladište <b>3</b>', "—", "—", '<span class="tag ok">rezerviraj 2</span>'),
]
srows = "".join('<tr><td style="overflow: hidden; text-overflow: ellipsis;"><b>%s</b><br><span class="note mono">%s</span></td><td class="r num">%s</td><td>%s</td><td class="num">%s</td><td class="r num">%s</td><td style="overflow: hidden;">%s</td></tr>' % r for r in SKL)
TRAKE = [("TR001254", "ABS 1/22 JELA CLAY", "361 m", "2 role", "R2-07-A", '<span class="tag warn">provjeri</span>'), ("TR000017", "ABS 0,5/22 BIJELI NK", "73 m", "3 role", "R1-02-B", '<span class="tag ok">dovoljno</span>'),
         ("TR001258", "ABS 1/44 JELA CLAY", "7 m", "1 rola", "R2-07-B", '<span class="tag ok">dovoljno</span>'), ("TR001213", "ABS 1/22 HRAST RELIEF PIMENTO", "7 m", "1 rola", "R3-11-A", '<span class="tag ok">dovoljno</span>')]
trows = "".join('<tr><td style="overflow: hidden; text-overflow: ellipsis;"><span class="mono" style="font-size: 12px;">%s</span> %s</td><td class="r num"><b>%s</b></td><td class="num">%s</td><td><span class="addr">%s</span></td><td>%s</td></tr>' % r for r in TRAKE)
nab = [("IV JELA TAVERNA 19", "K2665AI-19", "6", "2800 × 2070 × 19", "IVERPAN d.o.o.", '<span class="tag crit">za naručiti</span>'),
       ("IV BIJELI NK 16", "W908ST2-16", "1", "2800 × 2070 × 16", "IVERPAN d.o.o.", '<span class="tag crit">za naručiti</span>'),
       ("ABS 1/22 JELA CLAY (TR001254)", '<span class="addr">R2-07-A</span>', "361 m", "regal: 2 role · 275 m", "Blažič", '<span class="tag abs">u dolasku 15.09.</span>')]
nrows = "".join('<tr><td style="overflow: hidden; text-overflow: ellipsis;"><b>%s</b></td><td class="mono" style="font-size: 12px;">%s</td><td class="r num"><b>%s</b></td><td style="overflow: hidden; text-overflow: ellipsis;">%s</td><td style="overflow: hidden; text-overflow: ellipsis;">%s</td><td>%s</td></tr>' % r for r in nab)
sk_extra = ['<span><span class="dot"></span>13 ≥ 10</span>', '<span><span class="dot crit"></span>0 → nabava 6</span>', '<span><span class="dot"></span>26 ≥ 4</span>',
            '<span><span class="dot crit"></span>0 → nabava 1</span>', '<span><span class="dot"></span>1 ≥ 1</span>', '<span><span class="dot"></span>3 ≥ 2</span>']
left5 = ('<div class="pane"><div class="hd"><span class="lbl">Materijali</span><span style="flex: 1;"></span><span class="tag crit">2 u nabavi</span></div>' + matlist(None, extra=sk_extra) +
         '<div class="hd" style="border-top: 1px solid var(--line2);"><span class="lbl">Trake</span></div>'
         '<div class="mat"><b>4 trake</b><span class="m">TR001254 · TR000017 · TR001258 · TR001213</span><span><span class="dot warn"></span>1 za provjeru</span></div>'
         '<div style="flex: 1;"></div><div style="padding: 9px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Kupac potvrdio 12.09. (Ivana) → Hub provjerio skladište</div></div>')
centre5 = ('<div class="pane"><div class="hd"><div style="min-width: 0;"><div class="lbl">Provjera skladišta</div><div style="font-weight: 700; font-size: 15px;">Nakon potvrde kupca <span style="color: var(--muted); font-weight: 500; font-size: 13px;">· Winstore izvoz 11.09. · restlovi Hub · regal-traka</span></div></div>'
           '<div style="flex: 1;"></div><span class="tag crit">2 materijala bez ploča</span></div>'
           '<div style="overflow: hidden;"><table style="table-layout: fixed; font-size: 13px;"><thead><tr><th>Materijal</th><th class="r" style="width: 86px;">Potrebno</th><th style="width: 128px;">Stanje</th><th style="width: 118px;">Restlovi</th><th class="r" style="width: 58px;">Manjak</th><th style="width: 154px;">Hub prijedlog</th></tr></thead><tbody>' + srows + '</tbody></table></div>'
           '<div class="hd" style="border-top: 1px solid var(--line2); margin-top: 2px;"><span class="lbl">Trake (regal-traka)</span><span class="note">metri PW-metodom · role i adrese iz regal-trake</span></div>'
           '<div style="overflow: hidden;"><table style="table-layout: fixed; font-size: 13px;"><thead><tr><th>Traka</th><th class="r" style="width: 86px;">Potrebno</th><th style="width: 128px;">Na regalu</th><th style="width: 118px;">Adresa</th><th style="width: 212px;">Status</th></tr></thead><tbody>' + trows + '</tbody></table></div>'
           '<div class="hd" style="border-top: 1px solid var(--line2); margin-top: 2px;"><span class="lbl" style="white-space: nowrap;">Manjak za nalog</span><span class="note">Hub ga složi sam → u Nabavi (Sanela) postaje narudžbenica po dobavljaču</span><span style="flex: 1;"></span><button class="btn sm">Excel</button><button class="btn sm pri">Otvori u Nabavi →</button></div>'
           '<div style="overflow: hidden;"><table style="table-layout: fixed; font-size: 13px;"><thead><tr><th>Stavka</th><th style="width: 100px;">Kod / adresa</th><th class="r" style="width: 60px;">Kom</th><th style="width: 144px;">Ploča</th><th style="width: 112px;">Dobavljač</th><th style="width: 118px;">Status</th></tr></thead><tbody>' + nrows + '</tbody></table></div>'
           '<div style="flex: 1;"></div>'
           '<div style="padding: 8px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Do potvrde kupca Hub ništa ne rezervira (D-35). Rezervacija vrijedi za ovaj nalog; Pantheon ostaje financijska istina, Hub skladište = količine (D-02).</div></div>')
right5 = ('<div style="display: flex; flex-direction: column; gap: 12px; min-height: 0;">'
          + pane("Upozorenje", bd('<b style="color: var(--crit);">Proizvodnja ne može krenuti</b> — 2 materijala bez ploča: IV JELA TAVERNA 19 (6), IV BIJELI NK 16 (1).', 'Dobava IVERPAN: 2–3 radna dana → planirano od 16.09.', '<span class="note">Pila / nesting se može potvrditi za ostala 4 materijala odmah.</span>', size="12.5px"), '<span style="flex: 1;"></span><span class="tag crit">!</span>')
          + pane("Restlovi", bd('IV JELA: 2 kandidata <span class="addr">C006</span> 2800 × 981 · 2405 × 447 <span class="tag warn">provjeri dekor</span>', '<button class="btn sm">Rezerviraj restl za ovaj nalog</button>', size="12.5px"))
          + pane("Rezervacije za ovaj nalog", bd('10 × W908ST2-18 (od 13) · 4 × MDF 3 · 1 × HRAST · 2 × RP', 'Trake: 361 m TR001254 · 73 m TR000017 · 7 m TR001258 · 7 m TR001213', '<span class="note">Rezervacija se oslobađa kad stigne rezultat sa stroja (.mno / CPO).</span>', size="12.5px"))
          + pane("Što dalje", bd('1. manjak je već u Nabavi — Sanela šalje narudžbenicu IVERPAN-u', '2. potvrdi skladište → voditelj bira put pila / nesting', '3. primka iz Knjige zatvori narudžbenicu → Hub javi voditelju', size="12.5px", gap="4px"), style="flex: 1;")
          + '</div>')
foot5 = ('<div class="kpi"><b>4 / 6</b><span>materijala pokriveno</span></div><div class="kpi"><b>7 ploča</b><span>u nabavi (2 materijala)</span></div><div class="kpi"><b>24 pl. · 115,1 m²</b><span>potrebno (PW-metoda)</span></div>'
         '<div style="flex: 1;"></div><button class="btn">Otvori u Nabavi</button><button class="btn pri">Potvrdi skladište · dalje: pila / nesting →</button>')
ACT5 = '<button class="tbtn">Nabava</button><button class="tbtn pri">Potvrdi skladište</button>'
W["v04_Skladiste.dc.html"] = screen("Production Hub v0.4 — Skladište nakon potvrde", ORDER_CRUMB, 2, ACT5, "nalozi", "236px minmax(0, 1fr) 292px", [left5, centre5, right5], foot5)

# ================================================================ 6. PILA / NESTING (voditelj)
pn_extra = ['<span><span class="tag nest">nesting</span> <span class="note">.mno 9 pl.</span></span>', '<span><span class="tag nest">nesting</span> <span class="note">.mno 5 pl.</span></span>',
            '<span><span class="tag pila">pila</span> <span class="note">CPO poslan</span></span>', '<span><span class="tag pila">pila</span> <span class="note">čeka nabavu</span></span>',
            '<span><span class="tag pila">pila</span> <span class="note">CPO poslan</span></span>', '<span><span class="tag pila">pila</span> <span class="note">CPO poslan</span></span>']
left6 = ('<div class="pane"><div class="hd"><span class="lbl">Materijali</span><span style="flex: 1;"></span><span class="note">2 nesting · 4 pila</span></div>' + matlist(1, extra=pn_extra) +
         '<div style="flex: 1;"></div><div style="padding: 9px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Pravilo: pila = MDF 3 mm, radne / zidne / compact ploče, restlovi, &lt; 1 ploče; ostalo nesting. Voditelj potvrđuje.</div></div>')
pw_thumbs = "".join(thumb(11 + i, u, "%d · %s %%" % (i + 1, p), fill=MEL_SOFT, w=118, h=88) for i, (u, p) in enumerate([(0.93, "93"), (0.92, "92"), (0.9, "90"), (0.9, "90"), (0.88, "88"), (0.55, "55")]))
nest_thumbs = "".join(thumb(21 + i, u, "%d · %s %%" % (i + 1, p), w=118, h=88) for i, (u, p) in enumerate([(0.95, "94,9"), (0.94, "93,8"), (0.93, "93,2"), (0.92, "92,1"), (0.67, "67,2")]))
PN = [("IV BIJELI NK 18", "nest", "10 · 57,96 m²", 'CSV + CIX <span class="mono">H0001201–1253</span>', '<span class="dot"></span>.mno 9 pl. · 95,4 %'),
      ("IV JELA TAVERNA 19", "nest", "6 · 30,16 m²", 'CSV + CIX <span class="mono">H0001254–1288</span>', '<span class="dot"></span>.mno 5 pl. · 88,2 %'),
      ("MDF BIJELI 3", "pila", "4 · 18,49 m²", 'CPO <span class="mono">HUB_00904</span> → Z:', '<span class="dot info"></span>na pili (OSI)'),
      ("IV BIJELI NK 16", "pila", "1 · 5,80 m²", 'CPO <span class="mono">HUB_00905</span> → Z:', '<span class="dot warn"></span>čeka nabavu (1 pl.)'),
      ("IV HRAST RELIEF CARDAMOM 19", "pila", "1 · 2,73 m²", 'CPO <span class="mono">HUB_00906</span> → Z:', '<span class="dot info"></span>na pili (OSI)'),
      ("RP BASANIT SAND (900)", "pila", "2 cijele", 'CPO <span class="mono">HUB_00907</span> · obrub 0', '<span class="dot info"></span>na pili (OSI)')]
PN_ROWS = "".join('<tr%s><td style="overflow: hidden; text-overflow: ellipsis;"><b>%s</b></td><td><span class="tag %s">%s</span></td><td class="r num">%s</td><td style="overflow: hidden; text-overflow: ellipsis;">%s</td><td style="overflow: hidden; text-overflow: ellipsis;">%s</td></tr>'
                  % (' class="sel"' if i == 1 else "", n, "nest" if p == "nest" else "pila", "nesting" if p == "nest" else "pila", pl, ex, rz) for i, (n, p, pl, ex, rz) in enumerate(PN))
centre6 = ('<div class="pane"><div class="hd"><div style="min-width: 0;"><div class="lbl">Aktivni materijal</div><div style="font-weight: 700; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">IV001210 · IVERAL JELA TAVERNA K2665 AI 19MM <span style="color: var(--muted); font-weight: 500; font-size: 13px;">19 mm · god · K2665AI-19</span></div></div>'
           '<div style="flex: 1;"></div><span class="tag nest">nesting</span><span class="tag crit">Winstore 0 · nabava 6</span></div>'
           '<div style="display: flex; align-items: center; gap: 16px; padding: 10px 14px; border-bottom: 1px solid var(--line2); background: #FBFAF6;">'
           '<div><div class="lbl">Put</div><div style="font-size: 13px;">Hub prijedlog: <b>nesting</b> <span class="note">— iveral s godom, 25,6 m² ≫ 1 ploča</span></div></div><div style="flex: 1;"></div>'
           '<span class="radio"><i></i> Pila</span><span class="radio"><i class="on"></i> Nesting</span><button class="btn pri sm">Potvrdi put</button></div>'
           '<div style="padding: 8px 14px 4px; display: flex; align-items: baseline; gap: 10px;"><span class="lbl">Sheme za obračun · PW-metoda</span><span class="note">6 ploča · 30,16 m² · uzdužno (god) · uvijek vidljive</span><span style="flex: 1;"></span><a href="#" style="font-size: 12px;">PNG</a></div>'
           '<div style="display: flex; gap: 8px; padding: 0 14px 8px;">' + pw_thumbs + '</div>'
           '<div style="padding: 6px 14px 4px; border-top: 1px solid var(--line2); display: flex; align-items: baseline; gap: 10px;"><span class="lbl">Rezultat s nestinga</span><span class="note">.mno 11.09. 08:40 · <b style="color: var(--ink);">5 ploča · 88,2 %</b> · zadnja ploča: ostatak ≥ 400 × 400 → prijedlog restla</span></div>'
           '<div style="display: flex; gap: 8px; padding: 0 14px 8px;">' + nest_thumbs + '<div style="flex: 1;"></div><div class="thumb" style="justify-content: center;"><button class="btn sm">Upiši restl</button></div></div>'
           '<div style="margin: 0 14px; padding: 8px 12px; border: 1px solid var(--line); border-radius: 8px; background: var(--acc-soft); display: flex; gap: 18px; align-items: center; font-size: 13px;">'
           '<span class="lbl" style="color: var(--acc);">Naplaćeno vs potrošeno</span><span>naplaćeno <b>6 pl. · 30,16 m²</b></span><span>potrošeno <b>5 pl. · 28,98 m²</b></span><span style="color: var(--acc); font-weight: 700;">+1 ploča = 5,80 m² ≈ 180 €</span><span class="note" style="margin-left: auto;">vidljivo tek nakon .mno · ne mijenja ponudu (D-18)</span></div>'
           '<div style="padding: 10px 14px 4px; display: flex; flex-direction: column; gap: 5px; font-size: 12.5px;">'
           '<div><span class="dot"></span>bNest: CSV + CIX <span class="mono">H0001254–H0001288</span> · 11.09. 08:32 → <span class="mono">C:\\PPNESTING\\Humer\\NESTING\\</span> <span class="note">(operater radi iz mape, kao danas)</span></div>'
           '<div><span class="dot"></span>PanelWizard (paralelni rad): CPW <span class="mono">I_01915</span> generiran automatski</div></div>'
           '<div class="hd" style="border-top: 1px solid var(--line2); margin-top: 6px;"><span class="lbl">Svi materijali naloga</span><span class="note">put · ploče PW-metodom · export · rezultat sa stroja</span></div>'
           '<div style="overflow: hidden;"><table style="table-layout: fixed; font-size: 12.5px;"><thead><tr><th>Materijal</th><th style="width: 92px;">Put</th><th class="r" style="width: 96px;">Ploče (PW)</th><th style="width: 200px;">Export</th><th style="width: 190px;">Rezultat</th></tr></thead><tbody>' + PN_ROWS + '</tbody></table></div>'
           '<div style="flex: 1;"></div>'
           '<div style="padding: 7px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Element s CNC obradom uvijek ide na nesting (D-29). Stvarna potrošba s nestinga se evidentira uz nalog, ponuda ostaje (D-18).</div></div>')
right6 = ('<div style="display: flex; flex-direction: column; gap: 12px; min-height: 0;">'
          + pane("Skladište", bd('<span class="dot crit"></span>Winstore <b>0</b> · nabava 6 ploča naručena 12.09. (Sanela) · dobava 16.09.', '<span class="dot warn"></span>restl <span class="addr">C006</span> 2800 × 981 rezerviran — provjeri dekor', size="12.5px"))
          + pane("Export — nalog", bd('<span class="dot"></span>bNest CSV + CIX: 2 / 2 materijala', '<span class="dot"></span>pila CPO: 4 / 4 → <span class="mono">Z:\\Krojne_liste</span> (HUB_00904–00907)', '<span class="dot"></span>PanelWizard CPW: 6 / 6 automatski', '<span class="note">Nazivi bez Š Č Ć; kerf 16 za obračun, u CPO 5 (D-21).</span>', size="12.5px", gap="5px"))
          + pane("Rezultati sa strojeva", bd('<span class="mono note">11.09. 08:40</span> bNest .mno K2665AI-19: 5 pl., 88,2 %', '<span class="mono note">11.09. 08:31</span> bNest .mno W908ST2-18: 9 pl., 95,4 %', '<span class="mono note">11.09. 08:20</span> CPO HUB_00904 zapisan (MDF 3 mm, 4 pl.)', '<span class="note">Watcher na mape; potvrda „izrezano“ ostaje praćenju proizvodnje (D-34).</span>', size="12px", gap="5px"))
          + pane("Naplaćeno vs potrošeno — nalog", '<div class="bd" style="font-size: 12px; gap: 0;"><table style="table-layout: fixed;"><thead><tr><th>Materijal</th><th class="r" style="width: 44px;">Napl.</th><th class="r" style="width: 44px;">Nest.</th><th class="r" style="width: 76px;">Razlika</th></tr></thead><tbody>'
                 '<tr><td>BIJELI NK 18</td><td class="r">10</td><td class="r">9</td><td class="r" style="color: var(--acc);">+5,80 m²</td></tr><tr><td>JELA TAVERNA 19</td><td class="r">6</td><td class="r">5</td><td class="r" style="color: var(--acc);">+5,80 m²</td></tr>'
                 '<tr><td><b>Ukupno</b></td><td></td><td></td><td class="r"><b>+11,59 m²<br>≈ 263 €</b></td></tr></tbody></table><div class="note" style="margin-top: 6px;">Vidi operater nestinga nakon optimizacije, kao danas (D-38).</div></div>', style="flex: 1;")
          + '</div>')
foot6 = ('<div class="kpi"><b>2 · 4</b><span>nesting · pila</span></div><div class="kpi"><b>24 pl. · 115,14 m²</b><span>naplata (PW-metoda)</span></div><div class="kpi"><b>14 pl.</b><span>potrošeno na nestingu</span></div>'
         '<div style="flex: 1;"></div><button class="btn">Pošalji na pilu (4 CPO)</button><button class="btn pri">Potvrdi put za sve materijale</button>')
ACT6 = '<button class="tbtn">Sheme PNG</button><button class="tbtn">Export ▾</button><button class="tbtn pri">Potvrdi put</button>'
W["v04_PilaNesting.dc.html"] = screen("Production Hub v0.4 — Pila / nesting", ORDER_CRUMB, 3, ACT6, "nalozi", "236px minmax(0, 1fr) 292px", [left6, centre6, right6], foot6, user="VP")

# ================================================================ 7. NABAVA (Sanela) — potrebe preko svih potvrđenih naloga + narudžbenice (D-42, 10 §3 i §6)
POTREBE = [
    # materijal, kod · ident · dobavljač, potrebno, nalozi, fizičko, rezervirano, naručeno, raspoloživo, manjak, prijedlog
    ("IV JELA TAVERNA 19", "K2665AI-19 · IVERPAN", "6 pl.", "HUMER_OMIS_2823", "0", "0", "0", "0", "6", '<span class="tag crit">naruči 6</span>'),
    ("IV HRAST HALIFAX 18", "H1180ST37-18 · IVERPAN", "4 pl.", "BLAGO_ADRIJANA_2929", "0", "0", "0", "0", "4", '<span class="tag crit">naruči 4</span>'),
    ("IV BIJELI NK 16", "W908ST2-16 · IVERPAN", "1 pl.", "HUMER_OMIS_2823", "0", "0", "0", "0", "1", '<span class="tag crit">naruči 1</span><br><span class="note">iskustveno 5</span>'),
    ("IV BIJELI NK 18", "W908ST2-18 · IVERPAN", "15 pl.", "HUMER 10 · BLAGO 5", "13", "10", "0", "3", "2", '<span class="tag crit">naruči 2</span><br><span class="note">iskustveno 10</span>'),
    ("ABS 1/22 JELA CLAY", "TR001254 · Blažič", "361 m", "HUMER_OMIS_2823", "275 m", "0", "150 m", "425 m", "—", '<span class="tag abs">u dolasku 15.09.</span>'),
    ("MDF BIJELI 3", "IV000054 · IVERPAN", "7 pl.", "HUMER 4 · VARGA 3", "26", "7", "0", "19", "—", '<span class="tag ok">dovoljno</span>'),
    ("RP BASANIT SAND (900)", "RP000136 · Frischeis", "2 cijele", "HUMER_OMIS_2823", "3", "2", "0", "1", "—", '<span class="tag ok">dovoljno</span>'),
    ("IV HRAST RELIEF CARDAMOM 19", "K2776GR-19 · IVERPAN", "1 pl.", "HUMER_OMIS_2823", "1", "1", "0", "0", "—", '<span class="tag ok">dovoljno</span><br><span class="note">zadnja ploča</span>'),
]
prow = []
for i, (m, kod, pot, nal, fiz, rez, nar, rasp, manj, prij) in enumerate(POTREBE):
    crit = manj != "—"
    prow.append('<tr%s><td style="overflow: hidden; text-overflow: ellipsis;"><b>%s</b><br><span class="note mono">%s</span></td><td class="r num"><b>%s</b></td><td style="overflow: hidden; text-overflow: ellipsis; font-size: 12px;">%s</td>'
                '<td class="r num">%s</td><td class="r num" style="color: var(--muted);">%s</td><td class="r num" style="color: var(--muted);">%s</td><td class="r num">%s</td><td class="r num">%s</td><td style="overflow: hidden; white-space: normal; line-height: 1.25;">%s</td></tr>'
                % (' class="sel"' if i == 0 else "", m, kod, pot, nal, fiz, rez, nar, rasp, ('<b style="color: var(--crit);">%s</b>' % manj) if crit else manj, prij))
prow.append('<tr><td colspan="9" style="text-align: center; color: var(--muted); padding: 5px;">… još 14 materijala bez manjka · <a href="#">svi</a></td></tr>')

NARST = [
    ("IV JELA TAVERNA 19", "IV001210", "6", "2800 × 2070 × 19", "HUMER_OMIS_2823", ""),
    ("IV HRAST HALIFAX 18", "IV001188", "4", "2800 × 2070 × 18", "BLAGO_ADRIJANA_2929", "dekor po narudžbi"),
    ("IV BIJELI NK 16", "IV000002", "5", "2800 × 2070 × 16", "HUMER 1 + zaliha 4", "iskustveno"),
    ("IV BIJELI NK 18", "IV000090", "10", "2800 × 2070 × 18", "HUMER 2 + zaliha 8", "2–3 naloga tjedno"),
]
nsrows = "".join('<tr><td style="overflow: hidden; text-overflow: ellipsis;"><b>%s</b></td><td class="mono" style="font-size: 12px;">%s</td><td class="r num"><b>%s</b></td><td>%s</td><td style="overflow: hidden; text-overflow: ellipsis;">%s</td><td><span class="note">%s</span></td></tr>' % r for r in NARST)
left7 = ('<div class="pane"><div class="hd"><span class="lbl">Nabava</span><span style="flex: 1;"></span><span class="tag crit">4 za naručiti</span></div>'
         '<div class="mat on"><b>Potrebe · manjak</b><span class="m">preko svih potvrđenih naloga</span></div>'
         '<div class="mat"><b>Narudžbenice</b><span class="m">3 otvorene · 1 nacrt</span></div>'
         '<div class="mat"><b>Očekivane dobave</b><span class="m">ovaj tjedan 2 · <span style="color: var(--crit);">1 kasni</span></span></div>'
         '<div class="mat"><b>Zaprimljeno</b><span class="m">primke iz Knjige · 7 dana: 3</span></div>'
         '<div class="hd" style="border-top: 1px solid var(--line2);"><span class="lbl">Dobavljači</span></div>'
         '<div class="mat"><b>IVERPAN d.o.o.</b><span class="m">ploče · 2 narudžbe · 1 kasni</span></div>'
         '<div class="mat"><b>Blažič</b><span class="m">trake · N-042 u dolasku</span></div>'
         '<div class="mat"><b>Frischeis</b><span class="m">radne ploče · —</span></div>'
         '<div class="mat"><b>Elgrad</b><span class="m">ploče · —</span></div>'
         '<div style="flex: 1;"></div><div style="padding: 9px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Raspoloživo = fizičko − rezervirano + naručeno. Manjak = Σ potrebno (potvrđeni nalozi) − raspoloživo.</div></div>')
chips7 = "".join('<span class="chip%s">%s <span class="n">%s</span></span>' % (" on" if on else "", n, c) for n, c, on in [("Svi materijali", 22, False), ("Manjak", 4, True), ("Ploče", 3, False), ("Trake", 1, False), ("Radne ploče", 0, False)])
centre7 = ('<div class="pane"><div class="hd"><div style="min-width: 0;"><div class="lbl">Potrebe</div><div style="font-weight: 700; font-size: 15px;">Preko svih potvrđenih naloga <span style="color: var(--muted); font-weight: 500; font-size: 13px;">· 5 naloga u toku · Winstore izvoz 11.09. · Hub skladište · regal-traka</span></div></div>'
           '<div style="flex: 1;"></div><span class="tag crit">4 stavke za naručiti · 13 ploča</span></div>'
           '<div style="padding: 8px 14px; border-bottom: 1px solid var(--line2); display: flex; gap: 6px; align-items: center;">' + chips7 + '<div class="inp" style="margin-left: auto; min-height: 30px; padding: 3px 10px; width: 210px;">' + ico("search").replace('<svg', '<svg style="width: 14px; height: 14px; color: var(--muted);"') + '<span class="ph">traži materijal, nalog…</span></div></div>'
           '<div style="overflow: hidden;"><table style="table-layout: fixed; font-size: 12.5px;"><thead><tr><th>Materijal</th><th class="r" style="width: 62px;">Treba</th><th style="width: 112px;">Nalozi</th><th class="r" style="width: 46px;">Fiz.</th><th class="r" style="width: 44px;">Rez.</th><th class="r" style="width: 52px;">Naruč.</th><th class="r" style="width: 54px;">Raspol.</th><th class="r" style="width: 52px;">Manjak</th><th style="width: 128px;">Prijedlog</th></tr></thead><tbody>' + "".join(prow) + '</tbody></table></div>'
           '<div class="hd" style="border-top: 1px solid var(--line2); margin-top: 2px;"><div style="min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"><span class="lbl">Narudžbenica · nacrt</span> <b style="margin-left: 6px;">N-2026-043 · IVERPAN</b> <span class="note">· iz manjka + zaliha · Sanela</span></div>'
           '<span style="flex: 1;"></span><span class="note" style="white-space: nowrap;">očekivano <b style="color: var(--ink);">16.09.</b></span><button class="btn sm">Excel</button><button class="btn sm pri">Pošalji dobavljaču (e-mail)</button></div>'
           '<div style="overflow: hidden;"><table style="table-layout: fixed; font-size: 12.5px;"><thead><tr><th>Stavka</th><th style="width: 84px;">Ident</th><th class="r" style="width: 50px;">Kom</th><th style="width: 130px;">Ploča</th><th style="width: 200px;">Za naloge</th><th style="width: 150px;">Napomena</th></tr></thead><tbody>' + nsrows + '</tbody></table></div>'
           '<div style="padding: 6px 14px; display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--muted);"><span class="lbl">Status</span>' + "".join('<span class="chip%s" style="padding: 2px 9px; font-size: 11.5px;">%s</span>' % (" on" if i == 0 else "", n) for i, n in enumerate(["nacrt", "poslana", "djelomično zaprimljena", "zaprimljena"])) + '<span style="margin-left: auto;">stavka može biti i bez naloga (zaliha unaprijed)</span></div>'
           '<div style="flex: 1;"></div>'
           '<div style="padding: 8px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Narudžbenica se zatvara sama: kad Knjiga uveze račun dobavljača, isti eSlog primke puni Hub skladište, Hub spoji stavke (ident + kom) s otvorenom narudžbenicom istog dobavljača i rezervacija naloga postaje fizička ploča. Knjiga se ne mijenja.</div></div>')
right7 = ('<div style="display: flex; flex-direction: column; gap: 12px; min-height: 0;">'
          + pane("Kasni", bd('<b style="color: var(--crit);">N-2026-041 IVERPAN</b> — očekivano 12.09., stiglo 2 / 3: <b>IV BIJELI NK 18 × 8</b> nije na primci PR-1187.', 'Čeka: VARGA_POTNJANI_3213 (pila)', '<button class="btn sm">Pitaj dobavljača (e-mail)</button>', size="12.5px"), '<span style="flex: 1;"></span><span class="tag crit">1</span>')
          + pane("Otvorene narudžbenice", bd('<span class="mono">N-041</span> IVERPAN · 10.09. · <span class="tag warn">djelomično 2 / 3</span>', '<span class="mono">N-042</span> Blažič · 11.09. · očekivano 15.09. · <span class="tag abs">poslana</span>', '<span class="mono">N-043</span> IVERPAN · <span class="tag info">nacrt</span> · očekivano 16.09.', '<span class="note">Zadnja primka: PR-1187 IVERPAN 12.09. → N-041 djelomično. <a href="#">Sve narudžbenice</a></span>', size="12.5px", gap="5px"), '<span style="flex: 1;"></span><span class="tag">3</span>')
          + pane("Nalozi koji čekaju nabavu", bd('<b>HUMER_OMIS_2823</b> · 2 materijala · 7 pl. · rok 26.09.', '<b>BLAGO_ADRIJANA_2929</b> · 1 materijal · 4 pl. · rok 24.09.', '<b>VARGA_POTNJANI_3213</b> · 8 pl. u dolasku <span style="color: var(--crit);">(kasni)</span>', '<span class="note">Kad roba stigne, Hub javi voditelju — put se može potvrditi.</span>', size="12.5px", gap="5px"), '<span style="flex: 1;"></span><span class="tag warn">3</span>')
          + pane("Kako Hub računa", bd('Potrebno = Σ po materijalu iz <b>potvrđenih</b> naloga (PW-metoda)', 'Raspoloživo = fizičko − rezervirano + naručeno', 'Fizičko: Winstore (ploče za nesting) · Hub skladište (pila) · regal-traka (metri po roli)', 'Naručiti se može i bez naloga — zaliha unaprijed, iskustveno kao dosad', size="12.5px", gap="5px"), style="flex: 1;")
          + '</div>')
foot7 = ('<div class="kpi"><b>4 st. · 13 pl.</b><span>za naručiti</span></div><div class="kpi"><b>3</b><span>otvorene narudžbenice</span></div><div class="kpi"><b>3</b><span>naloga čeka nabavu</span></div><div class="kpi"><b>1</b><span>dobava kasni</span></div>'
         '<div style="flex: 1;"></div><button class="btn">Excel potreba</button><button class="btn pri">Pošalji N-2026-043 IVERPAN-u</button>')
ACT7 = '<button class="tbtn">Excel</button><button class="tbtn pri">+ Narudžbenica</button>'
W["v04_Nabava.dc.html"] = screen("Production Hub v0.4 — Nabava", "<b>Nabava</b> · potrebe preko svih potvrđenih naloga · narudžbenice · dobave", None, ACT7, "nabava", "236px minmax(0, 1fr) 292px", [left7, centre7, right7], foot7, user="SA")

# ================================================================ zapis (na ekranima nema D-xx / I-xx ni riječi „AI“)
import re
bad = []
for fn, html in W.items():
    html = strip_dxx(html)
    chk = html.replace("K2665AI", "").replace("K2665 AI", "")  # Winstore kod / Pantheon naziv dekora, nije oznaka
    if re.search(r"(?<![A-Z0-9])[DI]-\d{2}\b", chk) or re.search(r"\bAI\b", chk):
        bad.append(fn)
    open(fn, "w", encoding="utf-8").write(html)
    print(fn, len(html))
print("materijali", eur(mat_total), "okov", eur(okov_total), "usluge", eur(usl_total), "neto", eur(neto), "pdv", eur(pdv), "ukupno", eur(neto + pdv))
if bad:
    raise SystemExit("OZNAKE NA EKRANU: %s" % bad)
