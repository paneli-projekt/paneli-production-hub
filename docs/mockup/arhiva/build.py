# -*- coding: utf-8 -*-
"""Generira artboarde 1, 3 i 4 mockupa Production Huba (nalog HUMER_2823_OMIS, stvarne brojke iz audita).
Ekran 2 (Unos naloga) od v0.2 generira build_main.py; body2 ovdje je zadržan kao v0.1 (ne piše se)."""
from shared import CSS, topbar, order_strip, page, ico, rub

# ---------------------------------------------------------------- 1. NALOZI
nalozi = [
    # nalog, kupac, datum, izradio, mat, stavki, kom, m2, put, ponuda, status, napomena
    ("— novi —", "Bogdanić (rukopis, 3 str.)", "11.09.2026", "GORAN", "—", "—", "—", "—", "", "", "Unos", "Rukopis: 4 elementa za provjeru"),
    ("HUMER_2823_OMIS", "Mario Humer", "18.08.2026", "IVANA", "6", "123", "280", "103,1", "nest+pila", "26-010-002823", "Optimirano", ""),
    ("MAZUR_3258_16", "Mazur", "04.09.2026", "IVANA", "7", "71", "186", "57,9", "nesting", "26-010-003258", "Ponuda", ""),
    ("BRATEK_3231", "Bratek (Excel narudžba)", "27.08.2026", "GORAN", "4", "46", "118", "49,3", "nesting", "26-010-003231", "Ponuda", ""),
    ("BOGDANIC_3217_IVA", "Bogdanić", "01.09.2026", "IVANA", "5", "86", "158", "56,7", "nesting", "26-010-003217", "Proizvodnja", ""),
    ("VARGA_3213_POTNJANI", "Varga", "29.08.2026", "GORAN", "7", "75", "129", "33,9", "nest+pila", "26-010-003213", "Proizvodnja", ""),
    ("BLAGO_3166_JASA", "Blago", "28.08.2026", "IVANA", "2", "18", "32", "6,0", "pila", "26-010-003166", "Zatvoren", ""),
    ("BLAGO_2929_ADRIJANA", "Blago", "20.08.2026", "IVANA", "8", "75", "159", "53,6", "nesting", "26-010-002929", "Ponuda", "2 materijala bez stavke u ponudi"),
    ("TURALIJA_2924_TUKA", "Turalija", "19.08.2026", "GORAN", "5", "25", "43", "12,7", "pila", "26-010-002924", "Zatvoren", ""),
    ("ROMIC_2423", "Romić", "10.06.2026", "IVANA", "6", "8", "10", "6,7", "pila", "26-010-002423", "Zatvoren", ""),
]
STATUS_CLS = {"Unos": "warn", "Provjera": "warn", "Optimirano": "acc", "Ponuda": "acc", "Proizvodnja": "ok", "Zatvoren": ""}


def put_tag(p):
    if p == "nesting":
        return '<span class="tag nest">nesting</span>'
    if p == "pila":
        return '<span class="tag pila">pila</span>'
    if p == "nest+pila":
        return '<span class="tag nest">nesting</span> <span class="tag pila">pila</span>'
    return '<span class="tag">—</span>'


rows = []
for n, k, d, iz, mat, st, kom, m2, put, pon, status, nap in nalozi:
    sel = ' class="sel"' if n == "HUMER_2823_OMIS" else ""
    name = ('<b class="mono" style="font-size: 14px;">%s</b>' % n) if n != "— novi —" else '<span class="muted">— novi (bez imena) —</span>'
    napc = (' <span class="tag warn">' + ico("warn", 12) + " " + nap + "</span>") if nap else ""
    pon_c = ('<span class="mono">%s</span>' % pon) if pon else '<span class="muted">—</span>'
    rows.append(
        "<tr%s><td>%s%s</td><td>%s</td><td>%s</td><td>%s</td><td class=\"num\">%s</td><td class=\"num\">%s / %s</td><td class=\"num\">%s</td><td class=\"nw\">%s</td><td>%s</td><td><span class=\"tag %s\">%s</span></td></tr>"
        % (sel, name, napc, k, d, iz, mat, st, kom, m2, put_tag(put), pon_c, STATUS_CLS[status], status)
    )

body1 = topbar("Nalozi") + '''
<div class="wrap" style="display: flex; flex-direction: column; gap: 14px;">
  <div class="row" style="display: flex; gap: 12px; align-items: center;">
    <h2>Nalozi</h2>
    <span class="note">danas 3 nova · ovaj tjedan 41 · u proizvodnji 2</span>
    <div style="flex: 1;"></div>
    <div class="inp" style="width: 300px;">''' + ico("search", 16, "#5A6470") + '''<span class="ph">traži: nalog, kupac, ponuda, materijal…</span></div>
    <button class="btn">''' + ico("upload") + ''' Uvezi CPW / Excel / foto</button>
    <button class="btn pri">''' + ico("plus") + ''' Novi nalog</button>
  </div>
  <div class="chips" style="display: flex; gap: 6px;">
    <span class="chip on">Svi 10</span><span class="chip">Unos 1</span><span class="chip">Provjera 0</span><span class="chip">Optimirano 1</span><span class="chip">Ponuda 3</span><span class="chip">Proizvodnja 2</span><span class="chip">Zatvoren 3</span>
    <span style="width: 18px;"></span>
    <span class="chip">Moji (IVANA)</span><span class="chip">Čeka odluku pila/nesting</span><span class="chip">S upozorenjem</span>
  </div>
  <div class="card" style="padding: 0;">
    <table>
      <thead><tr><th>Nalog</th><th>Kupac</th><th>Datum</th><th>Izradio</th><th class="num">Mat.</th><th class="num">Stavki / kom</th><th class="num">m² dijelova</th><th>Put</th><th>Ponuda (Pantheon)</th><th>Status</th></tr></thead>
      <tbody>''' + "".join(rows) + '''</tbody>
    </table>
    <div class="foot">Jedan redak = jedan nalog kroz cijeli lanac (unos → pila/nesting → obračun → ponuda). Nalog, PW program, bNest projekt i ponuda vezani su Hub brojem (2026-02823), ne samo imenom PREZIME_BROJ.</div>
  </div>
  <div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px;">
    <div class="card stripe warn"><h3>Čeka odluku</h3><div class="note">HUMER_2823_OMIS — voditelj: pila ili nesting za 6 materijala (Hub predložio)</div></div>
    <div class="card stripe crit"><h3>Upozorenja</h3><div class="note">BLAGO_2929_ADRIJANA — 2 materijala izrezana, a bez stavke u ponudi (24,1 m²)</div></div>
    <div class="card stripe acc"><h3>Rezultati sa strojeva</h3><div class="note">bNest: 2 nova .mno (HUMER) · pila: 4 CPO poslana u Z:\\Krojne_liste</div></div>
    <div class="card stripe ok"><h3>Skladište</h3><div class="note">Winstore izvoz 11.09. učitan (374 ploče) · restlovi: 1.589 kom, 2 nova prijedloga iz nestinga</div></div>
  </div>
</div>'''

# ---------------------------------------------------------------- 2. UNOS NALOGA
elems = [
    # rb, L, W, kom, d1,k1,d2,k2, traka, prolaza, napomena, izvor
    (1, 1050, 340, 1, "A", "A", "A", "A", "ABS-ISTI", 1, "CNC NUT ZA FLEXY", "CPW"),
    (2, 1012, 564, 1, "A", "A", "A", "A", "ABS-ISTI", 1, "", "CPW"),
    (3, 564, 340, 2, "A", "A", "A", "A", "ABS-ISTI", 1, "", "CPW"),
    (4, 2780, 320, 1, "A", "A", "A", "A", "ABS-ISTI", 1, "CNC SKICA NUT ZA GOLU", "CPW"),
    (5, 2600, 320, 1, "A", "A", "A", "A", "ABS-ISTI", 1, "CNC SKICA NUT ZA GOLU", "CPW"),
    (6, 1050, 360, 1, "A", "A", "A", "A", "ABS-ISTI", 1, "", "CPW"),
    (7, 1047, 627, 1, "A", "A", "A", "A", "ABS-ISTI", 1, "", "CPW"),
    (8, 1047, 597, 1, "A", "A", "A", "A", "ABS-ISTI", 1, "", "CPW"),
    (9, 1047, 497, 2, "A", "A", "A", "A", "ABS-ISTI", 1, "", "CPW"),
    (10, 1047, 268, 2, "A", "A", "A", "A", "ABS-ISTI", 1, "", "CPW"),
    (14, 657, 647, 1, "A", "A", "A", "A", "ABS-ISTI", 1, "SKICA NUT 647", "CPW"),
    (15, 167, 477, 1, "A", "A", "A", "A", "ABS-ISTI", 2, "SKICA NUT 477", "CPW"),
    (16, 817, 640, 2, "A", "A", "A", "A", "ABS-ISTI", 1, "", "CPW"),
]
erows = []
for rb, L, W, kom, d1, k1, d2, k2, tr, pr, nap, izv in elems:
    warn = (' <span class="tag warn">' + ico("warn", 11) + " &lt; 200 mm → 2 prolaza</span>") if pr == 2 else ""
    erows.append(
        '<tr><td class="num muted">%d</td><td class="mono">%d_ELEMENT</td><td class="num"><b>%d</b></td><td class="num"><b>%d</b></td><td class="num">%d</td>'
        '<td>%s</td><td><span class="mono">%s</span></td><td class="num">%d</td><td>%s%s</td><td><span class="tag">%s</span></td><td>%s</td></tr>'
        % (rb, rb, L, W, kom, rub(d1, k1, d2, k2), tr, pr, nap, warn, izv, ico("check", 14, "#1B6E48"))
    )

mat_chips = [
    ("IV BIJELI NK 18", "53 st. · 174 kom", "nesting", False),
    ("IV JELA TAVERNA 19", "35 st. · 48 kom", "nesting", True),
    ("MDF BIJELI 3", "22 st. · 27 kom", "pila", False),
    ("IV BIJELI NK 16", "10 st. · 28 kom", "pila", False),
    ("IV HRAST RELIEF CARD. 19", "1 st. · 1 kom", "pila", False),
    ("RP BASANIT SAND", "2 st. · 2 kom", "pila", False),
]
mc = []
for n, s, p, on in mat_chips:
    mc.append(
        '<div style="display: flex; flex-direction: column; gap: 3px; padding: 8px 12px; border: 1px solid %s; border-radius: 4px; background: %s; min-width: 168px;">'
        '<b style="font-family: Barlow Condensed, sans-serif; font-size: 17px; letter-spacing: .02em; color: %s;">%s</b>'
        '<span style="font-size: 12px; color: %s;">%s</span><span>%s</span></div>'
        % ("#17546E" if on else "#C9D1D9", "#17546E" if on else "#FFFFFF", "#FFFFFF" if on else "#14171A", n,
           "#DCEAF1" if on else "#5A6470", s, put_tag(p))
    )

body2 = topbar("Nalozi") + order_strip(cur=0, sub=0, verzija="v3 · IVANA 18.08.") + '''
<div class="wrap" style="display: flex; flex-direction: column; gap: 14px;">

  <div style="display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: 14px;">
    <div class="card" style="display: flex; flex-direction: column; gap: 12px;">
      <h3>Zaglavlje naloga</h3>
      <div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px;">
        <div class="fld" style="grid-column: span 2;"><label class="l">Kupac (Pantheon subjekt)</label><div class="inp">''' + ico("search", 14, "#5A6470") + '''<b>Mario Humer</b><span class="muted">· Omiš · šifra subjekta iz Pantheona</span></div></div>
        <div class="fld"><label class="l">Naziv naloga (PW / bNest)</label><div class="inp mono">HUMER_2823_OMIS</div></div>
        <div class="fld"><label class="l">Hub broj (automatski)</label><div class="inp ro mono">2026-02823</div></div>
        <div class="fld"><label class="l">Datum</label><div class="inp">18.08.2026</div></div>
        <div class="fld"><label class="l">Izradio</label><div class="inp ro">IVANA</div></div>
        <div class="fld"><label class="l">Kerf za slaganje i obračun</label><div class="inp">16 mm <span class="muted">▾</span><span class="note" style="margin-left: auto;">u CPO ide 5</span></div></div>
        <div class="fld"><label class="l">Ponuda (Pantheon)</label><div class="inp ro mono">26-010-002823</div></div>
        <div class="fld" style="grid-column: span 4;"><label class="l">Napomena naloga</label><div class="inp">Radne ploče + fronte po skici; okov u Excelu (48 stavki); rok: dogovor s kupcem</div></div>
      </div>
    </div>
    <div class="card" style="display: flex; flex-direction: column; gap: 10px;">
      <h3>Uvoz elemenata</h3>
      <div class="row" style="display: flex; gap: 8px;"><button class="btn" style="flex: 1; text-align: left;">''' + ico("file") + ''' CPW iz klijentske aplikacije (PPW)</button><span class="tag ok">5 datoteka</span></div>
      <div class="row" style="display: flex; gap: 8px;"><button class="btn" style="flex: 1; text-align: left;">''' + ico("upload") + ''' Excel narudžba (predložak BRATEK)</button><span class="tag">—</span></div>
      <div class="row" style="display: flex; gap: 8px;"><button class="btn" style="flex: 1; text-align: left;">''' + ico("photo") + ''' Foto / sken rukopisa → prepoznavanje</button><span class="tag warn">provjera</span></div>
      <div class="note">Elementi prepoznati iz rukopisa dolaze s oznakom ZA PROVJERU (original + prepoznato uz svaki redak) i ne ulaze u export dok ih čovjek ne potvrdi.</div>
    </div>
  </div>

  <div class="row" style="display: flex; gap: 8px; align-items: stretch; flex-wrap: wrap;">''' + "".join(mc) + '''
    <button class="btn ghost" style="align-self: center;">''' + ico("plus") + ''' Materijal</button>
    <div style="flex: 1;"></div>
    <div class="kpi" style="align-self: center; text-align: right; flex: none; margin-left: auto;"><b>123 st. · 280 kom</b><span>6 materijala · 103,1 m² dijelova</span></div>
  </div>

  <div class="card" style="display: flex; flex-direction: column; gap: 12px;">
    <div style="display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 16px;">
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <h3>Materijal 2 / 6 — IV JELA TAVERNA 19</h3>
        <div class="fld"><label class="l">Pantheon ident ili naziv (šifrarnik s aliasima)</label><div class="inp big">''' + ico("search", 16, "#5A6470") + '''<span class="mono" style="font-size: 16px;">IV001210</span> IVERAL JELA TAVERNA K2665 AI 19MM</div></div>
        <div style="display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px;">
          <div class="fld"><label class="l">Winstore kod (za bNest)</label><div class="inp ro mono">K2665AI-19</div></div>
          <div class="fld"><label class="l">Ploča iz šifrarnika</label><div class="inp ro">2800 × 2070</div></div>
          <div class="fld"><label class="l">Debljina</label><div class="inp ro">19 mm</div></div>
          <div class="fld"><label class="l">God</label><div class="inp ro">DA — uzdužno</div></div>
          <div class="fld"><label class="l">Glodalo (CIX)</label><div class="inp ro">8D · 2 prolaza</div></div>
        </div>
        <div class="note">Aliasi u šifrarniku: <span class="mono">IV JELA TAVERNA 19MM</span> · <span class="mono">IV_JELA_TAVERNA_19</span> · <span class="mono">JELA TAVERNA</span> (kako pišu PW, PPNEST, kupci) — Hub ih sve prepozna, u CSV upiše Winstore kod (D-24).</div>
        <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px;">
          <div class="card stripe" style="background: #F3F5F7;"><label class="l">Put (Hub predlaže, voditelj potvrđuje)</label>
            <div class="row" style="display: flex; gap: 14px; margin-top: 4px;"><span class="radio"><i></i> Pila</span><span class="radio"><i class="on"></i> Nesting</span><span class="tag nest">prijedlog: nesting</span></div>
            <div class="note" style="margin-top: 6px;">iveral, 25,6 m² dijelova (≫ 1 ploča) → nesting; pila = MDF 3 mm, radne/zidne/compact ploče, restlovi, &lt; 1 ploče</div></div>
          <div class="card stripe warn" style="background: #F3F5F7;"><label class="l">Skladište (Warehouse)</label>
            <div style="margin-top: 4px;"><span class="dot warn"></span>Winstore: <b>0</b> cijelih ploča <span class="muted">(izvoz 11.09.)</span> → nabava / restl</div>
            <div style="margin-top: 4px;"><span class="dot acc"></span>Restlovi: 2 kandidata „IV JELA“ <span class="addr">C006</span> 2800×981 · 2405×447 <span class="tag warn">provjeri dekor</span></div></div>
        </div>
      </div>
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <h3>Zadane trake za ovaj materijal</h3>
        <table>
          <thead><tr><th>Oznaka u nalogu</th><th>Pantheon ident</th><th>Regal traka</th></tr></thead>
          <tbody>
            <tr><td><span class="mono">ABS-ISTI</span></td><td><span class="mono">TR001254</span> ABS 1/22 JELA CLAY</td><td><span class="addr">R2-07-A</span> 2 role</td></tr>
            <tr><td><span class="mono">1-44 ISTI</span></td><td><span class="mono">TR001258</span> ABS 1/44 JELA CLAY</td><td><span class="addr">R2-07-B</span> 1 rola</td></tr>
            <tr><td><span class="mono">MEL-ISTI</span></td><td><span class="muted">— (nema melamin trake za ovaj dekor)</span></td><td><span class="muted">—</span></td></tr>
          </tbody>
        </table>
        <div class="note">Element naslijedi zadanu traku; iznimka se mijenja u retku elementa. Metri po dekoru računaju se kao u PW-u (Σ stranica × 1,10) i šalju u regal-traku kao potrošnja po nalogu.</div>
        <div class="row" style="display: flex; gap: 8px;"><button class="btn sm">''' + ico("plus", 14) + ''' Traka</button><button class="btn sm">Kopiraj iz materijala 1</button></div>
      </div>
    </div>

    <div class="card stripe" style="background: #F3F5F7; display: flex; flex-direction: column; gap: 8px;">
      <div class="row" style="display: flex; gap: 10px; align-items: flex-end;">
        <div class="fld" style="width: 110px;"><label class="l">Duljina L</label><div class="inp big" style="justify-content: flex-end;">1050</div></div>
        <div class="fld" style="width: 110px;"><label class="l">Širina W</label><div class="inp big" style="justify-content: flex-end;">340</div></div>
        <div class="fld" style="width: 80px;"><label class="l">Kom</label><div class="inp big" style="justify-content: flex-end;">1</div></div>
        <div class="fld"><label class="l">Rubovi (duža1 · kraća1 · duža2 · kraća2)</label>
          <div class="row" style="display: flex; gap: 10px; min-height: 36px;">
            <span class="cb"><i class="on"></i> D1 <span class="tag acc">A</span></span><span class="cb"><i class="on"></i> K1 <span class="tag acc">A</span></span><span class="cb"><i class="on"></i> D2 <span class="tag acc">A</span></span><span class="cb"><i class="on"></i> K2 <span class="tag acc">A</span></span>
            <span class="muted">traka:</span><span class="inp" style="width: 150px; min-height: 32px; padding: 4px 8px;"><span class="mono">ABS-ISTI</span> ▾</span>
          </div></div>
        <div class="fld" style="flex: 1;"><label class="l">Napomena (ide na etiketu i u CSV)</label><div class="inp">CNC NUT ZA FLEXY</div></div>
        <div class="fld"><label class="l">CNC</label><div class="row" style="display: flex; min-height: 36px; align-items: center;"><span class="cb"><i class="on"></i> da</span></div></div>
        <button class="btn pri" style="min-height: 38px;">Prihvati <span class="kbd" style="margin-left: 6px; color: #17546E;">↵</span></button>
      </div>
      <div class="note">Isti ritam kao u PPNEST-u: mjere → kom → rubovi → napomena → <span class="kbd">Enter</span>. <span class="kbd">A</span>/<span class="kbd">M</span> mijenja vrstu ruba, <span class="kbd">Tab</span> sljedeće polje, <span class="kbd">F2</span> ispravi zadnji redak. Vrijednosti: mjera 1 = duljina (uz god), mjera 2 = širina; god se naslijedi od materijala.</div>
    </div>

    <table>
      <thead><tr><th class="num">rb</th><th>Naziv</th><th class="num">L</th><th class="num">W</th><th class="num">kom</th><th>Rubovi</th><th>Traka</th><th class="num">Prol.</th><th>Napomena / CNC</th><th>Izvor</th><th></th></tr></thead>
      <tbody>''' + "".join(erows) + '''
        <tr><td colspan="11" class="muted" style="text-align: center; padding: 10px;">… još 22 retka (35 stavki, 48 kom) · <a href="#">prikaži sve</a></td></tr>
      </tbody>
    </table>

    <div style="display: flex; gap: 40px; flex-wrap: wrap;">
      <div class="kpi"><b>35 · 48</b><span>stavki · komada</span></div>
      <div class="kpi"><b>25,57 m²</b><span>dijelova</span></div>
      <div class="kpi"><b>151,3 + 6,8 m</b><span>ABS 1/22 · ABS 1/44 (PW metri)</span></div>
      <div class="kpi"><b>6 ploča · 30,16 m²</b><span>PW-metoda, uzdužno (god) — za obračun</span></div>
      <div class="kpi"><b>2 · 0</b><span>elementa &lt; 200 mm · za provjeru</span></div>
    </div>
  </div>

  <div class="card stripe ok" style="display: flex; gap: 24px; align-items: center;">
    <h3 style="margin: 0;">Provjere prije spremanja</h3>
    <span><span class="dot ok"></span>svaki materijal ima Winstore kod i dimenziju ploče</span>
    <span><span class="dot ok"></span>sve trake mapirane na TR ident</span>
    <span><span class="dot ok"></span>0 elemenata s oznakom PROVJERI</span>
    <span><span class="dot warn"></span>K2665AI-19: Winstore 0 ploča — javiti voditelju</span>
    <div style="flex: 1;"></div>
    <button class="btn">Spremi kao nacrt</button><button class="btn pri">Spremi i pošalji na provjeru ''' + ico("arrow", 14, "#fff") + '''</button>
  </div>
</div>'''

# ---------------------------------------------------------------- 3. PILA / NESTING I EXPORT
mats3 = [
    # naziv, ident, winstore kod, st/kom, m2, prijedlog, razlog, put, ploče, skladište(html), export(html), rezultat(html)
    ("IV BIJELI NK 18", "IV000090", "W908ST2-18", "53 / 174", "50,37", "nesting", "iveral, 50 m² ≫ 1 ploča", "nesting", "10 · 57,96 m²",
     '<span class="dot ok"></span>Winstore <b>13</b> ploča',
     '<span class="tag ok">CSV + CIX</span> <span class="mono">H0001201–H0001253</span><br><span class="note">11.09. 08:17 · IV_BIJELI_NK_18 · 53 CIX</span>',
     '<span class="dot ok"></span><b>9 ploča</b> · 95,4 % <span class="note">(.mno 11.09. 08:31)</span><br><span class="note">ostatak zadnje ploče → prijedlog restla</span>'),
    ("IV JELA TAVERNA 19", "IV001210", "K2665AI-19", "35 / 48", "25,57", "nesting", "iveral s godom, 25,6 m²", "nesting", "6 · 30,16 m²",
     '<span class="dot warn"></span>Winstore <b>0</b> ploča · restl „IV JELA“ 2×',
     '<span class="tag ok">CSV + CIX</span> <span class="mono">H0001254–H0001288</span><br><span class="note">11.09. 08:32 · 35 CIX · god = 1</span>',
     '<span class="dot ok"></span><b>5 ploča</b> · 88,2 % <span class="note">(.mno 11.09. 08:40)</span><br><span class="note">po ploči 94,9 / 93,8 / 93,2 / 92,1 / 67,2 %</span>'),
    ("MDF BIJELI 3", "IV000054", "XXX", "22 / 27", "16,09", "pila", "MDF 3 mm uvijek pila", "pila", "4 · 18,49 m²",
     '<span class="dot ok"></span>skladište ploča: <b>26</b> · restl 0',
     '<span class="tag ok">CPO</span> <span class="mono">HUB_00904</span> → <span class="mono">Z:\\Krojne_liste</span><br><span class="note">kerf 5 u CPO, shema kao za obračun (D-21) · PNG sheme</span>',
     '<span class="dot acc"></span>na pili (OSI) — čeka se rezanje<br><span class="note">etikete printa OSI (D-25)</span>'),
    ("IV BIJELI NK 16", "IV000002", "W908ST2-16", "10 / 28", "4,60", "pila", "&lt; 1 ploče (4,6 m²)", "pila", "1 · 5,80 m²",
     '<span class="dot warn"></span>Winstore <b>0</b> · restl 0 → <a href="#">rezerviraj / nabavi</a>',
     '<span class="tag">CPO</span> <span class="mono">HUB_00905</span> <span class="note">— generira se nakon potvrde</span>',
     '<span class="muted">—</span>'),
    ("IV HRAST RELIEF CARDAMOM 19", "IV001219", "K2776GR-19", "1 / 1", "1,95", "pila", "1 element, 1,95 m²", "pila", "1 · 2,73 m²",
     '<span class="dot warn"></span>restl za ovaj dekor: <b>nema</b> → cijela ploča',
     '<span class="tag">CPO</span> <span class="mono">HUB_00906</span>',
     '<span class="muted">—</span>'),
    ("RP BASANIT SAND", "RP000259", "—", "2 / 2", "4,99 m", "pila", "radna ploča 4100 × 600", "pila", "2 kom",
     '<span class="dot ok"></span>RP na skladištu: <b>3</b>',
     '<span class="tag">CPO</span> <span class="mono">HUB_00907</span> <span class="note">obrub 0 (radna ploča)</span>',
     '<span class="muted">—</span>'),
]
r3 = []
for n, ident, wk, sk, m2, pri, raz, put, pl, skl, exp, rez in mats3:
    sel_p = '<span class="radio"><i class="%s"></i> Pila</span>' % ("on" if put == "pila" else "")
    sel_n = '<span class="radio"><i class="%s"></i> Nesting</span>' % ("on" if put == "nesting" else "")
    r3.append(
        '<tr><td class="nw"><b>%s</b><br><span class="note mono">%s · %s</span></td><td class="num nw">%s</td><td class="num">%s</td>'
        '<td>%s<br><span class="note">%s</span></td><td><div class="row" style="display: flex; gap: 10px;">%s %s</div></td>'
        '<td class="num">%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
        % (n, ident, wk, sk, m2, put_tag(pri), raz, sel_p, sel_n, pl, skl, exp, rez)
    )

body3 = topbar("Nalozi") + order_strip(cur=2, sub=1, verzija="v3", save_label="Potvrdi put") + '''
<div class="wrap" style="display: flex; flex-direction: column; gap: 14px;">
  <div class="row" style="display: flex; gap: 12px; align-items: center;">
    <h2>Pila / nesting i export</h2>
    <span class="note">Hub predlaže put po materijalu (pravilo iz prakse), voditelj proizvodnje potvrđuje; export nastaje iz istog naloga bez prekucavanja.</span>
    <div style="flex: 1;"></div>
    <span class="user">voditelj proizvodnje</span>
  </div>
  <div class="card" style="padding: 0;">
    <table>
      <thead><tr><th>Materijal</th><th class="num">Stavki / kom</th><th class="num">m² dijelova</th><th>Hub prijedlog</th><th>Put (voditelj)</th><th class="num">Ploče (PW-metoda)</th><th>Skladište</th><th>Export</th><th>Rezultat sa stroja</th></tr></thead>
      <tbody>''' + "".join(r3) + '''</tbody>
    </table>
    <div class="foot">Pravilo (odgovor 8, 11.9.): pila = MDF 3 mm, radne / zidne / compact ploče, restlovi i nalozi ispod jedne pune ploče; sve ostalo nesting. Ploče za obračun uvijek PW-metodom (D-18), bez obzira na put.</div>
  </div>

  <div style="display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 14px;">
    <div class="card" style="display: flex; flex-direction: column; gap: 10px;">
      <h3>Export datoteka (iz naloga, ne iz PPNEST-a)</h3>
      <div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px;">
        <div class="card stripe" style="background: #F3F5F7; display: flex; flex-direction: column; gap: 6px;">
          <b>bNest — nesting</b>
          <span class="note">CSV (28 stupaca, SIFRA MAT = Winstore kod) + 1 CIX po elementu u stilu operatera: ulaz na L/2, 8D ≤ 19 mm / 14 do 26 mm, 2 prolaza. Imena CIX iz globalnog brojača <span class="mono">H0001234</span>, nikad se ne ponavljaju (D-23).</span>
          <span class="note">Mapa: <span class="mono">C:\\PPNESTING\\Humer\\NESTING\\</span></span>
          <button class="btn pri sm wrap">Generiraj CSV + CIX (2 materijala)</button>
        </div>
        <div class="card stripe" style="background: #F3F5F7; display: flex; flex-direction: column; gap: 6px;">
          <b>Pila — OSI (Sektor 450)</b>
          <span class="note">Hub složi shemu (kerf 16 za obračun, u CPO upisuje 5) i piše <span class="mono">HUB_00904.cpo</span> izravno u <span class="mono">Z:\\Krojne_liste</span>; uz CPO ide PNG sheme za operatera. Nazivi bez Š Č Ć (PW/OSI).</span>
          <span class="note">Brojač programa: <span class="mono">HUB_xxxxx</span>, neovisan o I_/SA_ (D-22)</span>
          <button class="btn pri sm wrap">Pošalji na pilu (4 materijala)</button>
        </div>
        <div class="card stripe" style="background: #F3F5F7; display: flex; flex-direction: column; gap: 6px;">
          <b>PanelWizard — paralelni rad</b>
          <span class="note">Dok traje paralelni rad (D-11, najmanje 1 mjesec) Hub piše i CPW za PW (zaglavlje jednom, rubovi duža1·kraća1·duža2·kraća2). Ponuda u tom razdoblju iz PW brojki.</span>
          <span class="note">Provjera: PW količine = Hub količine → 50 naloga bez razlike = prekidač</span>
          <button class="btn sm wrap">Generiraj CPW (6 datoteka)</button>
        </div>
      </div>
    </div>
    <div class="card" style="display: flex; flex-direction: column; gap: 8px;">
      <h3>Rezultati sa strojeva (watcher na mape)</h3>
      <div class="list" style="display: flex; flex-direction: column; gap: 8px;">
        <div class="row" style="display: flex; gap: 10px;"><span class="note mono" style="width: 100px; white-space: nowrap; flex: none;">11.09. 08:40</span><span class="dot ok"></span><span>bNest .mno <b>K2665AI-19</b>: 5 ploča, 88,2 % — 1 ostatak ≥ 400×400 → <a href="#">predloži restl</a></span></div>
        <div class="row" style="display: flex; gap: 10px;"><span class="note mono" style="width: 100px; white-space: nowrap; flex: none;">11.09. 08:31</span><span class="dot ok"></span><span>bNest .mno <b>W908ST2-18</b>: 9 ploča, 95,4 %</span></div>
        <div class="row" style="display: flex; gap: 10px;"><span class="note mono" style="width: 100px; white-space: nowrap; flex: none;">11.09. 08:20</span><span class="dot acc"></span><span>CPO <b>HUB_00904</b> zapisan u Z:\\Krojne_liste (MDF 3 mm, 4 ploče)</span></div>
        <div class="row" style="display: flex; gap: 10px;"><span class="note mono" style="width: 100px; white-space: nowrap; flex: none;">18.08. 17:52</span><span class="dot"></span><span>PW CPO I_01911–I_01916 učitani (paralelni rad): 24 ploče, 115,14 m² za naplatu</span></div>
      </div>
      <div class="note">Stvarna potrošnja (nesting 9 + 5 ploča) evidentira se uz nalog, ali ne mijenja ponudu (D-18) — razlika je interni izvještaj.</div>
      <div class="row" style="display: flex; gap: 8px;"><button class="btn sm">''' + ico("box", 14) + ''' Restlovi za upis (2)</button><button class="btn sm">''' + ico("print", 14) + ''' Sheme PNG</button></div>
    </div>
  </div>
</div>'''

# ---------------------------------------------------------------- 4. OBRAČUN → PONUDA
stavke = [
    ("IV BIJELI NK 18 — 10 ploča (PW-metoda) · W908ST2-18", [
        ("IV000090", "IVERAL BIJELI NK W908 ST2 18 MM", "57,96", "M2", "14,34", "831,15", "10 × 5,796 m² − korisni ostatci"),
        ("US000002", "USLUGA REZANJA", "57,96", "M2", "2,55", "147,80", "= m² ploča"),
        ("TR001254", "ABS 1/22 JELA CLAY", "209", "M", "1,20", "250,80", "PW 208,2 m → naviše na metar (D-20)"),
        ("US000011", "USLUGA KANTIRANJA 2/22", "208,2", "M", "1,30", "270,66", "točno PW metri"),
        ("TR000017", "ABS 0,5/22 BIJELI NK", "22", "M", "0,25", "5,50", "PW 21,8 m → naviše"),
        ("US000003", "USLUGA KANTIRANJA 0,5/22", "21,8", "M", "0,87", "18,97", ""),
    ]),
    ("IV JELA TAVERNA 19 — 6 ploča, uzdužno (god) · K2665AI-19", [
        ("IV001210", "IVERAL JELA TAVERNA K2665 AI 19MM", "30,16", "M2", "31,00", "934,96", "ponuda 2823 imala 30,97 (ručno +0,81)"),
        ("US000002", "USLUGA REZANJA", "30,16", "M2", "2,55", "76,91", ""),
        ("TR001254", "ABS 1/22 JELA CLAY", "152", "M", "1,20", "182,40", "PW 151,3 m → naviše (ponuda: 180 m)"),
        ("US000011", "USLUGA KANTIRANJA 2/22", "151,3", "M", "1,30", "196,69", ""),
        ("TR001258", "ABS 1/44 JELA CLAY", "7", "M", "5,25", "36,75", "PW 6,8 m → naviše"),
        ("US000012", "USLUGA KANTIRANJA 2/44", "6,8", "M", "2,40", "16,32", ""),
    ]),
    ("MDF BIJELI 3 — 4 ploče", [
        ("IV000054", "MDF BIJELI 3 MM", "18,49", "M2", "5,00", "92,45", ""),
        ("US000013", "USLUGA REZANJA MDF", "18,49", "M2", "1,25", "23,11", ""),
    ]),
    ("IV BIJELI NK 16 — 1 ploča", [
        ("IV000002", "IVERAL BIJELI NK W908 ST2 16MM", "5,80", "M2", "14,50", "84,10", ""),
        ("US000002", "USLUGA REZANJA", "5,80", "M2", "2,55", "14,79", ""),
        ("TR000017", "ABS 0,5/22 BIJELI NK", "51", "M", "0,25", "12,75", "PW 50,9 m → naviše"),
        ("US000003", "USLUGA KANTIRANJA 0,5/22", "50,9", "M", "0,87", "44,28", ""),
    ]),
    ("IV HRAST RELIEF CARDAMOM 19 — 1 ploča, uzdužno (god)", [
        ("IV001219", "IVERAL HRAST RELIEF CARDAMOM K2776 GR 19MM", "2,73", "M2", "22,00", "60,06", "ponuda 2823: 2,98 (ručno +0,25)"),
        ("US000002", "USLUGA REZANJA", "2,73", "M2", "2,55", "6,96", ""),
        ("TR001213", "ABS 1/22 HRAST RELIEF PIMENTO", "7", "M", "1,20", "8,40", "PW 6,6 m → naviše"),
        ("US000011", "USLUGA KANTIRANJA 2/22", "6,6", "M", "1,30", "8,58", ""),
    ]),
    ("RP BASANIT SAND — 2 kom (radna ploča 4100 × 600)", [
        ("RP000259", "RADNA PLOČA BASANIT SAND K2875CN", "4,99", "M", "42,00", "209,58", "⚠ pravilo za RP nije potvrđeno (ponuda 2823: 2,4 m)"),
        ("US000303", "USLUGA REZANJA RADNE PLOČE", "2", "KOM", "3,00", "6,00", ""),
        ("US000015", "USLUGA SPOJ RADNE PLOČE", "2", "KOM", "9,00", "18,00", ""),
    ]),
]
r4 = []
for grp, items in stavke:
    r4.append('<tr class="grp"><td colspan="7">%s</td></tr>' % grp)
    for ident, naz, kol, jm, cij, izn, nap in items:
        cls = "warn" if nap.startswith("⚠") else ""
        napc = ('<span class="tag %s">%s</span>' % (cls, nap)) if nap else ""
        r4.append(
            '<tr><td class="mono nw">%s</td><td>%s</td><td class="num nw"><b>%s</b></td><td>%s</td><td class="num">%s</td><td class="num nw">%s</td><td>%s</td></tr>'
            % (ident, naz, kol, jm, cij, izn, napc)
        )
r4.append('<tr class="grp"><td colspan="7">Okov — 42 stavke iz upita kupca (OKOV (48).xlsx) · prepoznati identi, ručna potvrda <span class="tag warn">6 za provjeru</span></td></tr>')
r4.append('<tr><td colspan="7" class="note">Prikaz sažet — otvori „Okov“ za stavke. Hub okov ne računa, samo mapira i provjerava (D-07).</td></tr>')
r4.append('<tr class="grp"><td colspan="7">Ručne usluge — CNC, bušenje, LED urez, nut, ljepljenje, glodanje za ručkicu (8 stavki) <span class="tag">ručno</span></td></tr>')
r4.append('<tr><td colspan="7" class="note">npr. US000148 USLUGA P-BUŠENJA 5/8 MM 569 KOM · US000005 USLUGA REZANJA CNC 1,98 M · US002089 UREZIVANJE ZA LED PROFIL 1,04 M — kao dosad, s upisom tko je unio.</td></tr>')

body4 = topbar("Nalozi") + order_strip(cur=3, sub=2, verzija="v3", save_label="Zaključaj ponudu") + '''
<div class="wrap" style="display: flex; flex-direction: column; gap: 14px;">
  <div class="row" style="display: flex; gap: 12px; align-items: center;">
    <h2>Obračun → ponuda</h2>
    <span class="note">Količine PW-metodom za svaki nalog (D-18): m² za naplatu s pravilom korisnog ostatka, usluga rezanja, metri traka i kantiranja (D-20).</span>
    <div style="flex: 1;"></div>
    <div class="row" style="display: flex; gap: 12px; border: 1px solid #C9D1D9; border-radius: 3px; padding: 6px 10px; background: #fff;">
      <span class="note">Količine iz:</span><span class="radio"><i class="on"></i> PanelWizard (paralelni rad)</span><span class="radio"><i></i> Hub optimizator <span class="muted">(119,27 m², +3,6 %)</span></span>
    </div>
  </div>

  <div style="display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 14px; align-items: start;">
    <div class="card" style="padding: 0;">
      <table>
        <thead><tr><th>Ident</th><th>Naziv (Pantheon)</th><th class="num">Količina</th><th>JM</th><th class="num">Cijena</th><th class="num">Iznos €</th><th>Pravilo / napomena</th></tr></thead>
        <tbody>''' + "".join(r4) + '''
          <tr><td colspan="5" style="text-align: right; font-family: Barlow Condensed, sans-serif; font-size: 18px; font-weight: 600; letter-spacing: .03em; text-transform: uppercase;">Ploče, rezanje, trake, kantiranje</td><td class="num" style="font-family: Barlow Condensed, sans-serif; font-size: 20px; font-weight: 700;">3.557,97</td><td class="note">bez okova i ručnih usluga · cijene iz šifrarnika, bez rabata</td></tr>
        </tbody>
      </table>
    </div>

    <div style="display: flex; flex-direction: column; gap: 14px;">
      <div class="card stripe ok" style="display: flex; flex-direction: column; gap: 8px;">
        <h3>Provjere</h3>
        <div><span class="dot ok"></span>svaki materijal naloga ima stavku (6 / 6)<div class="note" style="margin-left: 15px;">spriječilo bi slučaj 2929 (2 materijala bez stavke)</div></div>
        <div><span class="dot ok"></span>trake po D-20: ident naviše na metar, usluga točno PW metri</div>
        <div><span class="dot ok"></span>ploče = PW brojke (3 materijala točno; JELA i HRAST u ponudi ručno +0,81 / +0,25)</div>
        <div><span class="dot warn"></span>RP BASANIT SAND: pravilo za dužne metre nije potvrđeno</div>
        <div><span class="dot warn"></span>okov: 6 stavki čeka potvrdu identa</div>
      </div>
      <div class="card stripe" style="display: flex; flex-direction: column; gap: 8px;">
        <h3>Naplaćeno vs potrošeno (interno)</h3>
        <table>
          <thead><tr><th>Materijal</th><th class="num">Naplaćeno</th><th class="num">Nesting</th><th class="num">Razlika</th></tr></thead>
          <tbody>
            <tr><td>IV BIJELI NK 18</td><td class="num">10 pl.</td><td class="num">9 pl.</td><td class="num" style="color: #1B6E48;">+1 pl.<br>5,80 m²</td></tr>
            <tr><td>IV JELA TAVERNA 19</td><td class="num">6 pl.</td><td class="num">5 pl.</td><td class="num" style="color: #1B6E48;">+1 pl.<br>5,80 m²</td></tr>
            <tr><td><b>Ukupno</b></td><td></td><td></td><td class="num"><b>+11,59 m²<br>≈ 263 €</b></td></tr>
          </tbody>
        </table>
        <div class="note">Prvi put vidljivo po nalogu; ne mijenja ponudu (D-18).</div>
      </div>
      <div class="card" style="display: flex; flex-direction: column; gap: 8px;">
        <h3>Izlaz</h3>
        <button class="btn pri">''' + ico("file", 14, "#fff") + ''' eSlog XML ponude → Pantheon</button>
        <button class="btn">''' + ico("print", 14) + ''' PDF ponude za kupca</button>
        <button class="btn">Excel stavki (kao skill krojna-ponuda)</button>
        <div class="note">Hub nikad ne piše u Pantheon bazu (D-06); broj ponude <span class="mono">26-010-00xxxx</span> dodjeljuje Pantheon pri uvozu i vraća se u nalog.</div>
      </div>
    </div>
  </div>
</div>'''

pages = {
    "Nalozi.dc.html": page("Production Hub — Nalozi", body1, 860),
    "PilaNesting.dc.html": page("Production Hub — Pila / nesting i export", body3, 1040),
    "Obracun.dc.html": page("Production Hub — Obračun → ponuda", body4, 1330),
}
for fn, html in pages.items():
    with open(fn, "w", encoding="utf-8") as f:
        f.write(html)
    print(fn, len(html))
