# Paneli Production Hub — 19: Rezultati natrag u Hub — sheme rezanja i potrošnja s nestinga (kralježnica korak 3d)

Stanje 15. 9. 2026. navečer. Do sada je Hub samo slao na strojeve (CSV + CIX, CPW, CPO). Sada čita i ono što se vrati: sheme rezanja
crta kao slike uz svaki materijal (D-34: sheme uvijek vidljive), a bNestov rezultat (`.mno`) knjiži kao **stvarnu potrošnju ploča** —
prvi put se uz nalog vidi *naplaćeno (PW-metoda) vs potrošeno (nesting)* (D-38), a spojeni posao iz više naloga (D-54) razdijeli se
natrag po nalozima. Ostaje još samo stvarno spajanje (jedan zajednički CSV + CIX paket), pa je korak 3 zatvoren.

## 1. Sheme rezanja → PNG (`hub/nalozi/sheme.py`)

Pri svakom izvozu na pilu Hub uz CPO nacrta **po jednu sliku po shemi** (`HUB_00005_S1.png`, `_S2.png` …) u istoj mapi `<NALOG>\PILA\`.
Na slici: ploča, dijelovi s rednim brojem i mjerama (i napomenom kad je ima), otpad točkasto; u naslovu program, materijal, mjere ploče,
„shema 1/6 × 1 kom“, broj dijelova i iskorištenje te sheme. Geometrija je ista kao u provjeri stabla rezova (`cpo_rw.validate`),
pa slika pokazuje točno ono što pila reže. Slike se bilježe kao dokumenti naloga (`png`) i u `optimizacija.sheme_json`, pa ih ekran
naloga može pokazati uz materijal bez ikakvog klika. `py -m hub.nalozi.sheme datoteka.cpo` crta i bilo koji PW-ov CPO.
Bez matplotliba izvoz radi dalje, samo bez slika (vrati upozorenje). Probe: `30_NOVI_PROGRAM\docs\sheme_proba\`.

## 2. Rezultat nestinga → potrošnja (`hub/nalozi/rezultat_nesting.py`)

    py -m hub.nalozi.rezultat_nesting --db hub.db --mno "C:\...\OUT\HUMER_OMIS_9_IV_BIJELI_NK_18_….mno"
    py -m hub.nalozi.rezultat_nesting --db hub.db --mapa C:\bNest\projekti        (svi .mno ispod mape; već uvezeni se preskaču)
    POST /api/rezultat/nesting {put | mapa, suho, tko}      GET /api/nalog/{id}/rezultati      GET /api/slika?put=

bNest za svaki posao zapiše `<projekt>\OUT\<projekt>.mno` — XML koji nosi sve što Hub treba:

| U `.mno` | Što je | Hub koristi za |
|---|---|---|
| `FOGLIO` + `SheetInfo DX/DY/DZ/Materiale/Resto`, `QTY` | ploča (mjere, Winstore šifra, je li restl, ponavljanja) | broj ploča, m² bruto |
| `StatisticInfo PartUsedArea` | m² dijelova na ploči | iskorištenje |
| `PROFILO` → `OptimizedSourceName`, `LPX/LPY`, `POS X/Y/DEG` | dio: ime CIX-a, mjere, položaj | veza na element Huba (registar imena, D-23) |
| `CUSTOM_DESCR_2 … _23` | stupci CSV-a: **2 = RN (naziv naloga)**, 3 cjelina, 4 pozicija, 5 šifra materijala, 11 CIX, 12/13 programi, 22 količina | razdioba spojenog posla po nalozima |

Hub svaki dio veže na element po imenu CIX-a (najprije `element.cix_ime`, pa registar), zbroji po **materijalu naloga** i upiše u
`optimizacija` red s `engine = bNest`: ploče (udio × ploče posla, po kvadraturi dijelova — D-38), iskorištenje, m² dijelova i ploča,
te u `sheme_json` cijeli rezultat (ploče, dijelovi s položajima, razdioba po nalogu). Kad je posao spojen iz više naloga, svaki nalog
dobije svoj red s `nacin = spojeno` i udjelom. Materijal naloga dobije `status_opt = nesting_gotov`. Isti `.mno` (hash) drugi put se
preskače; `.mno` čiji nijedan dio nije u Hubu ne upisuje ništa (upozorenje); dio bez elementa u Hubu je upozorenje s popisom CIX-ova;
razlika šifre materijala (bNest rezao drugo nego što nalog nosi) je upozorenje. `--suho` pročita i poveže bez upisa.

`GET /api/nalog/{id}/rezultati` daje po materijalu zadnji Hubov izvoz na pilu (ploče, naplata, sheme) i zadnji bNest rezultat s
razlikom ploča — to je ono što mockup crta iza rezultata nestinga (07, D-38).

## 3. Mjera uspjeha — stvarni podaci

**HUMER_2823_OMIS** (jedini nalog s bNest projektima, `03_NESTING_APLIKACIJA\export_za_nesting`): PPNEST CSV uvezen u Hub, Hub složio pilu,
pa učitana dva `.mno`:

| Materijal | Hub pila (PW-metoda) | bNest stvarno | Razlika |
|---|---|---|---|
| IV BIJELI NK 18 | 11 ploča | **9 ploča**, isk. 95,4 %, 168 dijelova (od 177 u nalogu — bNest posao je bio iz ranijeg izvoza) | −2 |
| IV JELA TAVERNA 19 | 6 ploča | **5 ploča**, isk. 88,2 %, 48 dijelova | −1 |

To je točno ono što dokument 03 §3.2 mjerio ručno — sada Hub to zna sam, po nalogu. Brojke iz `.mno` (5 ploča / 88,2 %) su iste kao u 03.

**TEST BUSENJE** (Corpus uzorak): nakon uvoza paketa (dokument 18) učitana oba bNest projekta iz `04_export_nesting`: IV SIVI TAMNI 19 →
1 ploča, 3/3 dijela; IV BIJELI NK 18 → 8 od 10 dijelova vezano (dvije police u bNest projektu nose imena iz *drugog* Corpusovog izvoza
istog projekta — `1446A088F7E`/`F86` umjesto `1446A6B3FD0`/`FD8`), pa Hub upiše udio 0,81 ploče i upozorenje s popisom. To je ispravno
ponašanje: Hub ne pogađa, nego kaže što ne može vezati.

## 4. Testovi

`tests/test_rezultati.py` — sheme PNG uz izvoz na pilu (datoteke, dokumenti, `sheme_json`, geometrija), sintetički `.mno` s dva naloga u
jednom poslu (razdioba po kvadraturi, napomena „u poslu je 2 od 3 komada“, preskakanje istog `.mno`, usporedba Hub ↔ bNest, loš XML, mapa s
greškom po datoteci), API (`/izvoz/pila` → `/slika`, `/rezultat/nesting`, `/rezultati`), i stvarni Corpus uzorak s `.mno`. **98 testova prolazi**
sa stvarnim podacima.

## 5. Što ostaje u koraku 3

Stvarno spajanje malih naloga (D-54/B): jedan zajednički CSV + CIX paket za više naloga — izvoz već piše naziv naloga u RN, `.mno` ga vraća
u `CUSTOM_DESCR_2`, a razdioba potrošnje po nalogu (§2) već radi, pa je ostalo samo sastaviti paket iz više naloga i zabilježiti u svakom
da je rezan u spojenom poslu. Nakon toga korak 4 (obračun + ponuda), gdje `.mno` potrošnja postaje osnova za „korekciju po stvarnom stanju“
kod vlastite proizvodnje (D-56).
