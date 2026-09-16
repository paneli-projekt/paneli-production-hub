# Paneli Production Hub

Vlastiti modularni sustav Paneli projekt d.o.o. za pripremu proizvodnje pločastog namještaja:
**standardni nalog → materijali / trake / okov / usluge → pila (Selco Sektor 450, OSI) ili nesting (Biesse Rover B, bNest + Winstore)
→ centralni Warehouse (ploče, restlovi, trake) → obračun → eSlog ponuda za Pantheon.** Dugoročno zamjenjuje PanelWizard,
koji ostaje referenca i benchmark (bez kopiranja koda).

Stanje: **faza 1 (audit) zatvorena 11. 9. 2026.** (D-28), faza 2 = mockup ekrana (v0.4) + kralježnica aplikacije — **korak 1 (šifrarnik) gotov 12. 9., korak 2 (kupci, nalog, elementi, uvoz CPW/CSV) gotov 13. 9.; 14. 9. dorada: ambalaža izvan stanja (D-49), debljina iz Winstorea, brojač naloga od 1 (D-47), ispravci ureda u Hubu (D-51), debljina po vrsti i redoslijed prednosti (D-52), nalazi šifrarnika (13)**
Odluke: [`docs/DECISIONS.md`](docs/DECISIONS.md) · parking ideja: [`docs/IDEJE_KASNIJE.md`](docs/IDEJE_KASNIJE.md) · audit i nalazi: `docs/00…12`.

## Što već radi (provjereno na stvarnim datotekama)

| Modul | Datoteka | Što |
|---|---|---|
| baza | `hub/schema.sql`, `hub/db.py` | SQLite shema v8 (04 §2 + 10 §4): šifrarnici, kupci, nalog, elementi, obračun, skladište, nabava, dnevnik; migracije starijih baza automatski |
| šifrarnici | `hub/sifrarnici/pantheon.py` | uvoz `ph_identi.csv` → `pantheon_ident`, `materijal` (IV*/RP*), `traka` (TR* + „ABS …“ pod OK/US) |
| šifrarnici | `hub/sifrarnici/winstore.py` | uvoz Winstore XML inventara → `winstore_ploca` + povezivanje MaterialCode ↔ materijal (D-24) |
| šifrarnici | `hub/sifrarnici/nazivi.py` | normalizacija naziva: vrsta, debljina (iz naziva i iz dimenzije `4100X640X8MM`, zadana 38 mm za radne ploče — D-52), riječi dekora, kodovi dekora (W908 ST2, K2665 AI, VSM-06), oznake traka |
| šifrarnici | `hub/sifrarnici/prepoznaj.py` | tekst iz naloga → Pantheon ident: alias → Winstore kod → naziv; nesigurno = „za potvrdu“ s kandidatima (D-32) |
| šifrarnici | `hub/sifrarnici/aliasi.py` | alias-tablica (369 parova iz skilla krojna-ponuda + potvrde iz ponuda), zadane trake po materijalu (D-31) |
| šifrarnici | `hub/sifrarnici/ispravci.py` | odluke ureda koje Pantheon nema (D-51): debljina, „ne koristi se“, ručna veza Winstore kod ↔ ident — preživljavaju svaki uvoz |
| šifrarnici | `hub/sifrarnici/uvoz.py`, `provjera.py`, `nalazi.py` | naredbe: dnevni uvoz šifrarnika; provjera na testnim nalozima (47/50 CPO, 40/40 vs ponuda); nalazi za ured (identi bez debljine, Winstore kodovi bez identa) |
| nalozi | `hub/nalozi/kupci.py` | kupci iz `ph_subjekti.csv` (3 619 aktivnih kupaca), pretraga bez dijakritike, Hub-polja (e-mail, rabat, dani plaćanja) |
| nalozi | `hub/nalozi/nalozi.py` | nalog `KUPAC_NAZIV_BROJ` (D-33), materijali sa zadanim trakama (D-31), elementi s rubovima, tok statusa + događaji (D-35, D-42), popis „za potvrdu“ (D-32) |
| nalozi | `hub/nalozi/spajanje.py` | prijedlozi spajanja malih naloga u jedan nesting posao (D-54): isti materijal u više naloga, uvjet ≥ 1 ploča |
| nalozi | `hub/nalozi/export_nesting.py` | izvoz na nesting: CSV + CIX za bNest po materijalu (D-23 registar imena, D-24 Winstore kod u `SIFRA MAT`); HUMER: isti elementi kao PPNEST |
| nalozi | `hub/nalozi/export_pw.py` | izvoz CPW za PanelWizard (paralelni rad D-11): svi materijali naloga, zaglavlje kao kod PPNEST-a |
| nalozi | `hub/nalozi/export_pila.py` | izvoz na pilu: optimizacija (D-19) + CPO za Selco OSI, programi `HUB_xxxxx` (D-22), kerf po D-21 |
| nalozi | `hub/nalozi/uvoz_datoteka.py`, `provjera.py` | uvoz CPW (kupac / PW / Corpus) i PPNEST CSV u nalog kroz šifrarnik; provjera na 9 testnih naloga (CPW ↔ CSV isti elementi) |
| api | `hub/api/app.py`, `hub/api/nalozi_api.py` | FastAPI: šifrarnik (pretraga, prepoznavanje, aliasi) + kupci, nalozi, materijali, elementi, statusi, upload datoteke (`/docs`) |
| formati | `hub/formati/cpo_rw.py` | Selco OSI `.cpo` — čitanje i pisanje bajt-po-bajt (50/50 PW datoteka identično), validacija stabla rezova |
| formati | `hub/formati/nalog_io.py` | standardni nalog ↔ PPNEST TXT/CSV, CIX za bNest (postavke operatera, alat 8D/14), CPW za PanelWizard |
| formati | `hub/formati/parseri.py` | CPW, CPO, PPNEST CSV/TXT, bNest `.mno`, `_lbl.xml` |
| optimizacija | `hub/optimizacija/obracun.py` | kalkulator količina PW-metodom: korisni ostatak, m² za naplatu, metri trake (točno kao PW PDF) |
| optimizacija | `hub/optimizacija/pila_optimizator.py` | giljotinski optimizator (uzdužno / poprečno / trake) + izbor po D-19 + CPO za pilu |
| alati | `hub/alati/benchmark_optimizator.py` | Hub vs PanelWizard na svim testnim nalozima (11. 9.: +4,0 % m², 104 vs 102 ploče) |
| alati | `hub/alati/provjera_exporta.py` | Hubov izvoz (stvarno napisane CPW/CSV datoteke) protiv PPNEST-ovog / PW-ovog na testnim nalozima (CSV 8/8, CPW 5/8 — razlike samo slovo M/A, D-61) |
| alati | `hub/alati/cpo_crtaj.py`, `d09_tri_naloga.py`, `benchmark_nalozi.py` | slike shema iz CPO-a, D-09 dokument, benchmark naloga |

## Pokretanje

```bat
py -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
set HUB_TEST_DATA=C:\Users\Administrator\Desktop\IGOR\CLAUDE_COWORK\Paneli_Production_Hub\05_NALOZI_ZA_TEST
py -m pytest -q
rem uvijek s HUB_TEST_DATA: 5 testova na stvarnim nalozima (CPO/CSV round-trip, šifrarnik, uvoz) bez toga se preskaču — a upravo su oni 15. 9. našli greške
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

rem 4. ispravci ureda koje Pantheon nema (D-51): debljina, "ne koristi se", ručna veza Winstore kod -> ident
py -m hub.sifrarnici.ispravci --db hub.db --popis
py -m hub.sifrarnici.ispravci --db hub.db --debljina IV001032=19 --ne-koristi IV000633 --kod H3303ST10-18=IV000941 --tko IGOR

rem 5. nalazi o šifrarniku za ured (što ispraviti u Pantheonu, D-45) → dokument 13 + CSV za Excel
py -m hub.sifrarnici.nalazi --db hub.db --md ..\20_ANALIZA\13_nalazi_sifrarnika.md --csv ..\20_ANALIZA\13_identi_bez_debljine.csv --obrazac ..\20_ANALIZA\13_compact_i_zidne_debljine.csv --obrazac-kodovi ..\20_ANALIZA\13_winstore_kodovi_bez_identa.csv

rem obrazac popuni ured (stupac 'vrijednost') pa se učita natrag:
py -m hub.sifrarnici.ispravci --db hub.db --csv ..\20_ANALIZA\13_compact_i_zidne_debljine.csv --tko IVANA
py -m hub.sifrarnici.ispravci --db hub.db --csv ..\20_ANALIZA\13_winstore_kodovi_bez_identa.csv --tko OPERATER

rem 6. prijedlozi spajanja malih naloga za nesting (D-54) — samo popis, voditelj odlučuje
py -m hub.nalozi.spajanje --db hub.db --md ..\20_ANALIZA\prijedlozi_spajanja.md

rem 7. izvoz naloga na nesting (CSV + CIX za bNest) — --suho samo pokaze sto bi nastalo
rem    na stroj ide samo nalog u statusu potvrdjeno / skladiste / pila_nesting i bez stavki za potvrdu (D-65); za probu iz 'unos' dodati --forsiraj
py -m hub.nalozi.export_nesting --db hub.db --nalog 9 --mapa C:\PPNESTING --suho
py -m hub.nalozi.export_nesting --db hub.db --nalog 9 --mapa C:\PPNESTING
py -m hub.nalozi.export_nesting --db hub.db --nalog 9 --mapa C:\PPNESTING --forsiraj

rem 8. izvoz naloga za PanelWizard (CPW) i za pilu (CPO)
py -m hub.nalozi.export_pw   --db hub.db --nalog 9 --mapa C:\PPNESTING
py -m hub.nalozi.export_pila --db hub.db --nalog 9 --mapa C:\PILA            (isto pravilo statusa kao nesting; --forsiraj za probu)
py -m hub.nalozi.optimiziraj --db hub.db --nalog 9 [--materijal 40 --nacin poprecno --dubina brzo]   (D-75: prijedlog slaganja; --potvrdi ID potvrđuje;
                                                                               ponuda i pila koriste SAMO potvrđeno slaganje; --potvrdi-sve za probe)
py -m hub.ispis.krojni --db hub.db --nalog 9 [--materijal 40] [--mapa C:\ISPISI]      (D-76: krojni nacrt PDF iz potvrđenog slaganja; bez potvrde = PRIJEDLOG)

rem 9. provjera izvoza: Hub protiv PPNEST-ovih / PW-ovih datoteka na svim testnim nalozima
py -m hub.alati.provjera_exporta --db hub.db --nalozi ..\05_NALOZI_ZA_TEST --md ..\20_ANALIZA\provjera_exporta.md --obrisi

rem 10. API (probno): http://localhost:8765/docs
set HUB_DB=hub.db
py -m uvicorn hub.api.app:app --host 0.0.0.0 --port 8765
```

Baza `hub.db` je jedna SQLite datoteka (u `.gitignore`); shema se primjenjuje automatski pri prvom otvaranju (migracija v8 briše brojač naloga
koji su potrošile probe dok u bazi nema stvarnog naloga — D-47). Winstore XML je cijeli inventar: svaki uvoz zamjenjuje prethodni (D-64/D-65).
Alias-tablica iz skilla krojna-ponuda je kopirana u `hub/sifrarnici/podaci/alias_krojna_ponuda.csv` (izvor ostaje skill).

Stvarni nalozi kupaca (CPO, CSV, PDF) i `ph_identi.csv` **nisu** u repozitoriju — ostaju u `Paneli_Production_Hub\05_NALOZI_ZA_TEST` i `CLAUDE_COWORK\`.

## Pravila rada

- PanelWizard se ne mijenja i ne dekompilira; formati su izvedeni iz izlaznih datoteka (D-07, D-16).
- Svaka odluka ide u `docs/DECISIONS.md` (status ODLUČENO / PREDLOŽENO), ideje u `docs/IDEJE_KASNIJE.md` (D-13).
- Nazivi prema pili i PanelWizardu bez dijakritika; imena CIX datoteka jedinstvena zauvijek (D-23); programi pile `HUB_xxxxx` (D-22).
- Warehouse Huba je izvor istine za količine ploča/restlova/traka, Pantheon je financijska istina (D-02); Hub u Pantheon piše samo eSlog datoteke.
- Prepoznavanje naziva je determinističko (bez LLM-a); što čovjek jednom potvrdi ulazi u alias-tablicu i više se ne pita (D-32).
- Na stroj samo potvrđen nalog bez otvorenih potvrda; elementi se mijenjaju samo u unos / ponuda; brisanje nikad ne oslobađa ime CIX-a (D-65).

## Plan faze 2 (iz `docs/04 §4`)

1. ✅ Šifrarnici: materijali s aliasima (Pantheon ident ↔ Winstore MaterialCode ↔ PW/PPNEST tekst), trake, usluge — D-12, D-24, D-31 (`docs/11`)
2. ✅ Nalog: kupci iz Pantheona, nalog + materijali + elementi, uvoz CPW / PPNEST CSV kroz šifrarnik, statusi i događaji, API (`docs/12`); slijedi: Excel / rukopis kupca, okov (D-32), Corpus paket (D-29)
3. Export: ✅ CSV+CIX (bNest) `docs/15`, ✅ CPW (PW, paralelni rad D-11) i ✅ CPO (pila) `docs/16`; slijedi spajanje naloga (D-54 korak B), čitanje rezultata natrag (.mno, CPO sheme → PNG), Corpusov paket
4. Obračun i eSlog ponuda (skill `krojna-ponuda` kao osnova, pravila D-18/D-19/D-20, D-40)
5. Warehouse: ploče (Winstore XML), restlovi (migracija Excel V3), trake (regal-traka API); nabava (D-42)
6. API + web ekrani (mockup v0.4) + `ai` modul (D-15)
