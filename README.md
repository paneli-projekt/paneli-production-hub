# Paneli Production Hub

Vlastiti modularni sustav Paneli projekt d.o.o. za pripremu proizvodnje pločastog namještaja:
**standardni nalog → materijali / trake / okov / usluge → pila (Selco Sektor 450, OSI) ili nesting (Biesse Rover B, bNest + Winstore)
→ centralni Warehouse (ploče, restlovi, trake) → obračun → eSlog ponuda za Pantheon.** Dugoročno zamjenjuje PanelWizard,
koji ostaje referenca i benchmark (bez kopiranja koda).

Stanje: **faza 1 (audit) zatvorena 11. 9. 2026.** (D-28), faza 2 = mockup ekrana + kralježnica aplikacije.
Odluke: [`docs/DECISIONS.md`](docs/DECISIONS.md) · parking ideja: [`docs/IDEJE_KASNIJE.md`](docs/IDEJE_KASNIJE.md) · audit: `docs/00…06`.

## Što već radi (provjereno na stvarnim datotekama, D-10 testovi prošli na strojevima)

| Modul | Datoteka | Što |
|---|---|---|
| formati | `hub/formati/cpo_rw.py` | Selco OSI `.cpo` — čitanje i pisanje bajt-po-bajt (50/50 PW datoteka identično), validacija stabla rezova |
| formati | `hub/formati/nalog_io.py` | standardni nalog ↔ PPNEST TXT/CSV, CIX za bNest (postavke operatera, alat 8D/14), CPW za PanelWizard |
| formati | `hub/formati/parseri.py` | CPW, CPO, PPNEST CSV/TXT, bNest `.mno`, `_lbl.xml` |
| optimizacija | `hub/optimizacija/obracun.py` | kalkulator količina PW-metodom: korisni ostatak, m² za naplatu, metri trake (točno kao PW PDF) |
| optimizacija | `hub/optimizacija/pila_optimizator.py` | giljotinski optimizator (uzdužno / poprečno / trake) + izbor po D-19 + CPO za pilu |
| alati | `hub/alati/benchmark_optimizator.py` | Hub vs PanelWizard na svim testnim nalozima (11. 9.: +4,0 % m², 104 vs 102 ploče) |
| alati | `hub/alati/cpo_crtaj.py`, `d09_tri_naloga.py`, `benchmark_nalozi.py` | slike shema iz CPO-a, D-09 dokument, benchmark naloga |

## Pokretanje

```bat
py -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
set HUB_TEST_DATA=C:\Users\Administrator\Desktop\IGOR\CLAUDE_COWORK\Paneli_Production_Hub\05_NALOZI_ZA_TEST
py -m pytest -q
py -m hub.alati.benchmark_optimizator %HUB_TEST_DATA%
```

Stvarni nalozi kupaca (CPO, CSV, PDF) **nisu** u repozitoriju — ostaju u `Paneli_Production_Hub\05_NALOZI_ZA_TEST`.

## Pravila rada

- PanelWizard se ne mijenja i ne dekompilira; formati su izvedeni iz izlaznih datoteka (D-07, D-16).
- Svaka odluka ide u `docs/DECISIONS.md` (status ODLUČENO / PREDLOŽENO), ideje u `docs/IDEJE_KASNIJE.md` (D-13).
- Nazivi prema pili i PanelWizardu bez dijakritika; imena CIX datoteka jedinstvena zauvijek (D-23); programi pile `HUB_xxxxx` (D-22).
- Warehouse Huba je izvor istine za količine ploča/restlova/traka, Pantheon je financijska istina (D-02).

## Plan faze 2 (iz `docs/04 §4`)

1. Šifrarnici (kupci iz Pantheona, materijali s aliasima: Pantheon ident ↔ Winstore MaterialCode ↔ PW/PPNEST tekst, trake, usluge) — D-12, D-24
2. Nalog: unos elemenata (mockup s voditeljem proizvodnje, D-14), uvoz CPW/Excel, standardni zapis
3. Export: CSV+CIX (bNest), CPW (PW, paralelni rad D-11), CPO (pila) — kod iz `hub/formati`
4. Obračun i eSlog ponuda (skill `krojna-ponuda` kao osnova, pravila D-18/D-19/D-20)
5. Warehouse: ploče (Winstore XML), restlovi (migracija Excel V3), trake (regal-traka API)
6. API + `ai` modul (D-15)
