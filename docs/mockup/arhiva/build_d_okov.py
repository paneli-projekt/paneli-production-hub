# -*- coding: utf-8 -*-
"""Varijanta D — pogled OKOV i OBRADE (isti raspored kao unos elemenata; lijevo se umjesto materijala bira grupa „Okov“).
Podaci: stvarni popis kupca OKOV (48).xlsx (HUMER) i idente iz ponude 26-010-002823."""
from build_d import CSS, FONTS, ico, ANT, OK, WARN, MUTED

# (kupac napisao, kom, ident, naziv u Pantheonu, JM, cijena, status) — status: ok = potvrđeno, ai = prepoznato po nazivu, čeka potvrdu
OKOV = [
    ("Blenda mat crna", 3, "OK001850", "SOKLA 4000X100 MM BIJELA/CRNA MAT", "KOM", "22,40", "ai"),
    ("Drzac blende", 30, "OK000060", "PRIHVAT ZA PVC NOGU", "KOM", "0,09", "ai"),
    ("Kut cokla crni", 4, "OK001176", "MULTICORNER 100MM BIJELI / CRNI", "KOM", "1,00", "ok"),
    ("Noga pvc 10 cm", 60, "OK000218", "PVC NOGA 100", "KOM", "0,32", "ok"),
    ("Blum antaro 500M", 2, "OK001136", "TANDEMBOX BLUM ANTARO M 500MM - KOMPLET", "KPT", "37,60", "ok"),
    ("Blum antaro 500C", 1, "OK001137", "TANDEMBOX BLUM ANTARO C 500MM - KOMPLET", "KPT", "45,88", "ok"),
    ("Blum antaro 500D", 11, "OK001138", "TANDEMBOX BLUM ANTARO D 500MM - KOMPLET", "KPT", "46,40", "ok"),
    ("Prednji dio za INTIVO i ANTARO SB, ZC 09Z31L1036", 1, "OK000376", "FRONTA ZA UNUTARNJU LADICU *BLUM", "KOM", "16,80", "ai"),
    ("Spojnice ravne blum sa usp", 30, "OK000596", "MET.SPOJNICA RAVNA *BLUM BLUMOTION", "KOM", "3,20", "ok"),
    ("Spojnice 170", 12, "OK000347", "MET.SPOJNICA 170° *BLUM", "KOM", "3,77", "ok"),
    ("Spojnice slijepe sa usp", 10, "OK000656", "MET.SPOJNICA SLJEPA *BLUMOTION", "KOM", "5,95", "ok"),
    ("Podloska za slijepe sa reg", 10, "OK000363", "PODLOŠKA SLJEPA/ZGLOBNA *BLUM", "KOM", "0,65", "ok"),
    ("Podloska sa reg", 42, "OK000547", "PODLOŠKA REGULACIJSKA *BLUM", "KOM", "0,56", "ok"),
    ("Košara soft PRO LINE orion siva - 150 mm", 1, "OK004248", "METALNA KOŠARA 150 SIGE PRO LINE 2X", "KOM", "76,00", "ok"),
    ("Nosac polica metalni", 200, "OK000210", "DRŽAČ POLICE MET 5 MM", "KOM", "0,02", "ok"),
    ("Nosac visecih elemenata direktni", 20, "OK000040", "NOSAČ GOR.ELEM. - KUTNIK", "KOM", "0,80", "ok"),
]

rows = []
for i, (txt, kom, ident, naz, jm, cij, st) in enumerate(OKOV, 1):
    badge = '<span class="tag ok">potvrđeno</span>' if st == "ok" else '<span class="tag warn">za potvrdu</span>'
    rows.append(
        '<tr%s><td class="r" style="color: var(--muted); width: 34px;">%d</td><td style="color: var(--muted); max-width: 210px; overflow: hidden; text-overflow: ellipsis;">%s</td>'
        '<td style="max-width: 330px; overflow: hidden; text-overflow: ellipsis;"><span class="mono" style="font-size: 12px;">%s</span> %s</td><td class="r" style="font-weight: 700;">%d</td><td style="color: var(--muted);">%s</td><td>%s</td></tr>'
        % (' class="sel"' if st == "ai" and i == 1 else "", i, txt, ident, naz, kom, jm, badge)
    )

mats = [("IV BIJELI NK 18", "53 · 174 · 50,4 m²", "nesting"), ("IV JELA TAVERNA 19", "35 · 48 · 25,6 m²", "nesting"), ("MDF BIJELI 3", "22 · 27 · 16,1 m²", "pila"),
        ("IV BIJELI NK 16", "10 · 28 · 4,6 m²", "pila"), ("IV HRAST RELIEF CARDAMOM 19", "1 · 1 · 1,9 m²", "pila"), ("RP BASANIT SAND", "2 · 2 · 4,99 m", "pila")]
matl = "".join('<div class="mat"><b>%s</b><span class="m">%s</span></div>' % (n, m) for n, m, p in mats)

body = '''
<div style="display: flex; flex-direction: column; height: 980px;">
  <div class="top">
    <div class="brand"><img src="logo-mark.png" alt="" style="height: 34px; width: auto; display: block;"><b>Paneli<span class="us">_</span> Production Hub</b></div>
    <div style="width: 1px; height: 26px; background: #8A9096;"></div>
    <div class="crumb" style="min-width: 0; overflow: hidden; text-overflow: ellipsis;">Nalozi / <b>HUMER_2823_OMIS</b> · Mario Humer · 18.08.2026 · ponuda 26-010-002823</div>
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
        <div style="max-height: 345px; overflow: hidden;">''' + matl + '''</div>
        <div class="hd" style="border-top: 1px solid var(--line2);"><span class="lbl">Ostalo u nalogu</span></div>
        <div class="mat on"><b>Okov</b><span class="m">16 stavki · 3 za potvrdu</span><span><span class="tag">kupac: OKOV (48).xlsx</span></span></div>
        <div class="mat"><b>Obrade i usluge</b><span class="m">10 stavki · ručno / iz Corpusa</span><span><span class="tag">CNC · bušenje · nut · LED</span></span></div>
        <div style="flex: 1;"></div>
        <div style="padding: 9px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted);">Sve tri grupe idu u istu ponudu (eSlog XML)</div>
      </div>

      <div class="pane">
        <div class="hd">
          <div><div class="lbl">Okov</div><div style="font-weight: 700; font-size: 15px;">Popis okova za nalog <span style="color: var(--muted); font-weight: 500; font-size: 13px;">· izvor: Excel kupca (uvezen 18.08.) · identi prepoznati automatski, potvrđuje unosilac</span></div></div>
          <div style="flex: 1;"></div>
          <button class="btn">Uvezi Excel / foto</button><button class="btn">Iz Corpusa</button>
        </div>
        <div style="display: flex; gap: 8px; padding: 10px 14px; border-bottom: 1px solid var(--line2); background: #FBFAF6; align-items: center;">
          <div class="inp foc" style="flex: 1;"><span class="ph">traži okov: naziv, ident ili kako kupac piše (npr. „spojnice 170“)…</span></div>
          <div class="inp big" style="width: 90px;">1</div>
          <button class="btn pri" style="padding: 9px 14px;">Dodaj <span class="kbd" style="margin-left: 6px;">↵</span></button>
        </div>
        <div style="overflow: hidden;">
          <table style="table-layout: fixed;">
            <thead><tr><th class="r" style="width: 40px;">#</th><th style="width: 200px;">Kupac napisao</th><th>Pantheon ident · naziv</th><th class="r" style="width: 56px;">kom</th><th style="width: 46px;">JM</th><th style="width: 150px;">Status</th></tr></thead>
            <tbody>''' + "".join(rows) + '''</tbody>
          </table>
        </div>
        <div style="flex: 1;"></div>
        <div style="padding: 7px 14px; border-top: 1px solid var(--line2); font-size: 12px; color: var(--muted); display: flex; gap: 14px; flex-wrap: wrap;">
          <span><span class="kbd">Enter</span> dodaj</span><span><span class="kbd">F4</span> promijeni ident u retku</span><span><span class="kbd">P</span> potvrdi prepoznati ident</span><span>Redak bez identa ne ide u ponudu — Hub ga javi u provjerama.</span>
        </div>
      </div>

      <div style="display: flex; flex-direction: column; gap: 12px; min-height: 0;">
        <div class="pane">
          <div class="hd"><span class="lbl">Okov — sažetak</span></div>
          <div style="padding: 8px 14px; display: flex; flex-direction: column; gap: 6px; font-size: 13px;">
            <div><b>16 stavki</b> · 13 potvrđeno · <span style="color: var(--warn); font-weight: 600;">3 za potvrdu</span></div>
            <div>Vrijednost (cjenik, bez rabata): <b>1.068 €</b></div>
            <div style="color: var(--muted); font-size: 12px;">Kupčev popis ima 103 retka (predložak); Hub uzima samo retke s količinom.</div>
          </div>
        </div>
        <div class="pane">
          <div class="hd"><span class="lbl">Kako se prepoznaje ident</span></div>
          <div style="padding: 8px 14px; display: flex; flex-direction: column; gap: 6px; font-size: 12.5px; color: var(--muted);">
            <div>1. alias-tablica okova (kako kupci pišu → ident) — deterministički, bez provjere</div>
            <div>2. bez aliasa → ident se prepozna po nazivu i dobije oznaku <span class="tag warn">za potvrdu</span></div>
            <div>3. potvrđeni par se upiše u alias-tablicu → idući put bez pitanja</div>
            <div style="color: var(--ink);">Ništa ne ide u ponudu bez potvrde unosioca.</div>
          </div>
        </div>
        <div class="pane">
          <div class="hd"><span class="lbl">Obrade i usluge</span><span style="flex: 1;"></span><span class="tag">10</span></div>
          <div style="padding: 8px 14px; display: flex; flex-direction: column; gap: 5px; font-size: 12.5px;">
            <div>US000148 P-bušenja 5/8 mm · <b>569 kom</b></div>
            <div>US000005 rezanje CNC · <b>1,98 m</b> · US000087 nut kant · <b>5,38 m</b></div>
            <div>US002089 urez za LED profil · <b>1,04 m</b> · US000245 glodanje za ručkicu · <b>25 kom</b></div>
            <div>US000303 rezanje radne ploče · <b>2 kom</b> · US000015 spoj · <b>2 kom</b></div>
            <div style="color: var(--muted);">Danas ručno iz napomena elemenata; za Corpus naloge Hub ih predlaže iz CIX-a (bušenja, utori, konture).</div>
          </div>
        </div>
        <div class="pane" style="flex: 1;">
          <div class="hd"><span class="lbl">U ponudu (eSlog)</span></div>
          <div style="padding: 8px 14px; font-size: 12.5px; color: var(--muted); display: flex; flex-direction: column; gap: 4px;">
            <div>1. materijali: ploče + rezanje + trake + kantiranje (po materijalu)</div><div>2. okov (16)</div><div>3. obrade i usluge (10)</div>
            <div style="color: var(--ink);">Jedan XML, redoslijed kao u današnjim ponudama.</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="foot">
    <div class="kpi"><b>123 · 280</b><span>stavki · kom (nalog)</span></div>
    <div class="kpi"><b>16</b><span>okov (3 za potvrdu)</span></div>
    <div class="kpi"><b>10</b><span>obrade i usluge</span></div>
    <div style="flex: 1;"></div>
    <span style="font-size: 13px;"><span class="dot warn"></span>Provjere: 3 stavke okova bez potvrde</span>
    <button class="btn pri">Dalje: pila / nesting →</button>
  </div>
</div>'''

html = (
    "<!doctype html>\n<html>\n<head>\n  <meta charset=\"utf-8\">\n  <script src=\"./support.js\"></script>\n</head>\n<body>\n<x-dc>\n<helmet>\n  <title>Paneli Production Hub — Okov i obrade, varijanta D</title>\n  %s\n  <style>%s</style>\n</helmet>\n"
    '<div style="width: 1440px; min-height: 980px; background: #EDEBE7;">\n%s\n</div>\n</x-dc>\n</body>\n</html>\n' % (FONTS, CSS, body)
)
open("MainDOkov.dc.html", "w", encoding="utf-8").write(html)
print("MainDOkov.dc.html", len(html))
