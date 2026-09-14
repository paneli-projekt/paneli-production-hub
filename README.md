# Paneli Production Hub

Vlastiti modularni sustav Paneli projekt d.o.o. za pripremu proizvodnje pločastog namještaja:
**standardni nalog → materijali / trake / okov / usluge → pila (Selco Sektor 450, OSI) ili nesting (Biesse Rover B, bNest + Winstore)
→ centralni Warehouse (ploče, restlovi, trake) → obračun → eSlog ponuda za Pantheon.** Dugoročno zamjenjuje PanelWizard,
koji ostaje referenca i benchmark (bez kopiranja koda).

Stanje: **faza 1 (audit) zatvorena 11. 9. 2026.** (D-28), faza 2 = mockup ekrana (v0.4) + kralježnica aplikacije — **korak 1 (šifrarnik) gotov 12. 9., korak 2 (kupci, nalog, elementi, uvoz CPW/CSV) gotov 13. 9.**
Odluke: [`docs/DECISIONS.md`](docs/DECISIONS.md) · parking ideja: [`docs/IDEJE_KASNIJE.md`](docs/IDEJE_KASNIJE.md) · audit i nalazi: `docs/00…12`.

## Što već radi (provjereno na stvarnim datotekama)

| Modul | Datoteka | Što |
|---|---|---|
| baza | `hub/schema.sql`, `hub/db.py` | SQLite shema v2 (04 §2 + 10 §4): šifrarnici, kupci, nalog, elementi, obračun, skladište, nabava, dnevnik; migracije starijih baza automatski |
| šifrarnici | `hub/sifrarnici/pantheon.py` | uvoz `ph_identi.csv` → `pantheon_ident`, `materijal` (IV*/RP*), `traka` (TR* + „ABS …“ pod OK/US) |
| šifrarnici | `hub/sifrarnici/winstore.py` | uvoz Winstore XML inventara → `winstore_ploca` + povezivanje MaterialCode ↔ materijal (D-24) |
| šifrarnici | `hub/sifrarnici/nazivi.py` | normalizacija naziva: vrsta, debljina, riječi dekora, kodovi dekora (W908 ST2, K2665 AI, VSM-06), oznake traka |
| šifrarnici | `hub/sifrarnici/prepoznaj.py` | tekst iz naloga → Pantheon ident: alias → Winstore kod → naziv; nesigurno = „za potvrdu“ s kandidatima (D-32) |
| šifrarnici | `hub/sifrarnici/aliasi.py` | alias-tablica (369 parova iz skilla krojna-ponuda + potvrde iz ponuda), zadane trake po materijalu (D-31) |
| šifrarnici | `hub/sifrarnici/uvoz.py`, `provjera.py` | naredbe: dnevni uvoz šifrarnika; provjera na testnim nalozima (47/50 CPO, 40/40 vs ponuda) |
| nalozi | `hub/nalozi/kupci.py` | kupci iz `ph_subjekti.csv` (3 619 aktivnih kupaca), pretraga bez dijakritike, Hub-polja (e-mail, rabat, dani plaćanja) |
| nalozi | `hub/nalozi/nalozi.py` | nalog `KUPAC_NAZIV_BROJ` (D-33), materijali sa zadanim trakama (D-31), elementi s rubovima, tok statusa + događaji (D-35, D-42), popis „za potvrdu“ (D-32) |
| nalozi | `hub/nalozi/uvoz_datoteka.py`, `provjera.py` | uvoz CPW (kupac / PW / Corpus) i PPNEST CSV u nalog kroz šifrarnik; provjera na 9 testnih naloga (CPW ↔ CSV isti elementi) |
| api | `hub/api/app.py`, `hub/api/nalozi_api.py` | FastAPI: šifrarnik (pretraga, prepoznavanje, aliasi) + kupci, nalozi, materijali, elementi, statusi, upload datoteke (`/docs`) |
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

### Šifrarnik i nalozi (koraci 1 i 2 kralježnice)

```bat
rem 1. dnevni uvoz iz Pantheona i Winstorea (identi, materijali, trake, aliasi, kupci; ~5 s; ne briše ono što je čovjek potvrdio)
py -m hub.sifrarnici.uvoz --db hub.db --pantheon ..\..\ph_identi.csv --winstore ..\04_STROJEVI\NESTING\11092026.XML --kupci ..\..\ph_subjekti.csv --poste ..\..\ph_poste.csv

rem 2. provjera šifrarnika na testnim nalozima (CPO, CPW, PPNEST CSV, trake) + Markdown izvještaj
py -m hub.sifrarnici.provjera --db hub.db --nalozi ..\05_NALOZI_ZA_TEST --benchmark ..\20_ANALIZA\benchmark_nalozi.csv --md provjera.md

rem 3. provjera uvoza naloga (CPW ↔ CSV svih 9 testnih naloga kroz šifrarnik); --obrisi briše probne naloge iz baze
py -m hub.nalozi.provjera --db hub.db --nalozi ..\05_NALOZI_ZA_TEST --md provjera_nalozi.md --obrisi

rem 4. API (probno): http://localhost:8765/docs
set HUB_DB=hub.db
py -m uvicorn hub.api.app:app --host 0.0.0.0 --port 8765
```

Baza `hub.db` je jedna SQLite datoteka (u `.gitignore`); shema se primjenjuje automatski pri prvom otvaranju.
Alias-tablica iz skilla krojna-ponuda je kopirana u `hub/sifrarnici/podaci/alias_krojna_ponuda.csv` (izvor ostaje skill).

Stvarni nalozi kupaca (CPO, CSV, PDF) i `ph_identi.csv` **nisu** u repozitoriju — ostaju u `Paneli_Production_Hub\05_NALOZI_ZA_TEST` i `CLAUDE_COWORK\`.

## Pravila rada

- PanelWizard se ne mijenja i ne dekompilira; formati su izvedeni iz izlaznih datoteka (D-07, D-16).
- Svaka odluka ide u `docs/DECISIONS.md` (status ODLUČENO / PREDLOŽENO), ideje u `docs/IDEJE_KASNIJE.md` (D-13).
- Nazivi prema pili i PanelWizardu bez dijakritika; imena CIX datoteka jedinstvena zauvijek (D-23); programi pile `HUB_xxxxx` (D-22).
- Warehouse Huba je izvor istine za količine ploča/restlova/traka, Pantheon je financijska istina (D-02); Hub u Pantheon piše samo eSlog datoteke.
- Prepoznavanje naziva je determinističko (bez LLM-a); što čovjek jednom potvrdi ulazi u alias-tablicu i više se ne pita (D-32).

## Plan faze 2 (iz `docs/04 §4`)

1. ✅ Šifrarnici: materijali s aliasima (Pantheon ident ↔ Winstore MaterialCode ↔ PW/PPNEST tekst), trake, usluge — D-12, D-24, D-31 (`docs/11`)
2. ✅ Nalog: kupci iz Pantheona, nalog + materijali + elementi, uvoz CPW / PPNEST CSV kroz šifrarnik, statusi i događaji, API (`docs/12`); slijedi: Excel / rukopis kupca, okov (D-32), Corpus paket (D-29)
3. Export: CSV+CIX (bNest), CPW (PW, paralelni rad D-11), CPO (pila) — kod iz `hub/formati`
4. Obračun i eSlog ponuda (skill `krojna-ponuda` kao osnova, pravila D-18/D-19/D-20, D-40)
5. Warehouse: ploče (Winstore XML), restlovi (migracija Excel V3), trake (regal-traka API); nabava (D-42)
6. API + web ekrani (mockup v0.4) + `ai` modul (D-15)
