# 12 — Nalog i elementi (kralježnica, korak 2) — 13. 9. 2026.

Korak 2 plana iz 04 §4: **kupci iz Pantheona, nalog (KUPAC_NAZIV_BROJ), materijali sa zadanim trakama, elementi s rubovima, tok statusa
s događajima, uvoz postojećih datoteka (CPW, PPNEST CSV) u nalog kroz šifrarnik iz koraka 1, API za ekrane 1 i 2 mockupa.**
Rezultat provjere na svih 9 testnih naloga: **CPW i CSV uvoz istog naloga daju iste materijale, elemente, komade i m² (7 / 8 usporedivih;
8. je razlika samo zato što CSV nosi tipfeler operatera `K2739DC-19`)**, 56 od 57 materijala prepoznato bez ruke, 999 elemenata / 2 248 komada;
HUMER-ov kupčev PPW paket (5 CPW-a): 121 elemenata, 278 komada, 0 stavki za potvrdu. Stavki za potvrdu ukupno 9 — sve su rupe u
Pantheon šifrarniku traka koje su već popisane u 11 §5.3 (jednom se potvrde i više se ne pitaju).

Kod: `30_NOVI_PROGRAM\hub\nalozi\{kupci,nalozi,uvoz_datoteka,provjera}.py`, `hub\api\nalozi_api.py`, shema v2 (`hub\schema.sql`, migracija u
`hub\db.py`), testovi `tests\test_nalozi.py` (8 + 1 na stvarnim podacima); ukupno 57 testova prolazi.

## 1. Što je napravljeno

| Dio | Datoteka | Sadržaj |
|---|---|---|
| Kupci | `hub/nalozi/kupci.py` | `ph_subjekti.csv` (= tHE_SetSubj, 4 750 subjekata) → 3 619 kupaca (acBuyer = T): naziv, puni naziv, adresa, pošta + mjesto (iz `ph_poste.csv`), OIB, fizička osoba. Pretraga bez dijakritike (ROMIĆ = romic, „31000 varga“, OIB). **Hub-polja koja Pantheon ne održava**: e-mail, telefon, rabat materijal / usluge (D-40), dani plaćanja — ponovni uvoz ih ne dira. Prijedlog kratkog naziva za nalog: `NAMJEŠTAJ MARIO vl.Mario Humer` → HUMER, `KL - MONT, vl. Ivan Bogdanić` → BOGDANIC, `BOJAN ROMIĆ` → ROMIC, `ADRIA GRUPA d.o.o.` → ADRIA_GRUPA (ured može promijeniti). |
| Krajnji kupci (D-48) | `hub/nalozi/kupci.py` | Svaki kupac ima **vrstu** (tvrtka / obrt / krajnji = fizička osoba; nosi zadani rabat: krajnji 0 %) i **subjekt za Pantheon** (kome ide ponuda / račun u eSlogu): tvrtke i obrti svoj, fizičke osobe bez OIB-a → zajednički „Krajnji kupac“, s OIB-om svoj. Uvoz razvrstava: 1 399 tvrtki, 336 obrta, 1 883 fizičkih (1 098 → Krajnji kupac), 63 probna subjekta neaktivna. Nova fizička osoba otvara se u Hubu (`POST /api/kupci`, bez Pantheona) uz provjeru **ponavljača**: isti telefon (+385 / 00385 / 0 izjednačeno) ili e-mail = isti kupac, isto ime = vjerojatno — API vraća 409 sa sličnima, ured izabere postojećeg ili potvrdi novog. Prijelaz krajnji ↔ obrt = promjena vrste i subjekta na kartici kupca. |
| Nalog | `hub/nalozi/nalozi.py` | `novi_nalog`: Hub broj `2026-00001` (brojač po godini u postavkama; početak podesiv, npr. 3300), naziv `KUPAC_NAZIV_BROJ` bez dijakritike i razmaka (D-33), vrsta usluga / vlastita_proizvodnja (D-30), rabat kopiran s kupca ili zadani 15 / 20 % (D-40), kerf 16 (D-21), događaj „nalog otvoren“. Statusi po D-35 (`unos → ponuda → potvrdjeno → skladiste → pila_nesting → proizvodnja → zatvoren`, natrag samo dok kupac nije potvrdio / na prethodni korak); svaki prijelaz = red u `dogadjaj` (tko, kada, razlog) + dnevnik; „Kupac potvrdio“ (dijalog 3b) upisuje datum, način, rok obećan, prioritet, tko. Nalog ne može u `ponuda` dok ima stavki za potvrdu. |
| Materijali naloga | isto | `nalog_materijal`: materijal po identu (ručno) ili po tekstu iz datoteke (prepoznavanje iz koraka 1); nesiguran ostaje bez identa s `provjeri = 1`; zadana traka materijala (izbornik MEL-ISTI / ABS-ISTI / ABS-ISTI 2mm, D-31/D-36), god iz šifrarnika (Winstore Grain), put pila / nesting (voditelj, D-34). |
| Elementi | isto | `element`: L × W × kom, naziv, god H/V, rubovi lijevo / dolje / desno / gore (isti redoslijed kao CPW: duža1, kraća1, duža2, kraća2) — u svakom rubu tekst iz naloga (`ABS-ISTI`, `taverna`, `1/22 CHAMPAGNE UM`) i prepoznata traka; napomena cijela + prvih 14 znakova za etiketu (D-38); CIX ime ako dolazi iz PPNEST-a. Rub koji šifrarnik nije siguran ostaje **prazan** s `provjeri = 1` — ništa nepotvrđeno ne ide u ponudu ni na stroj. |
| Za potvrdu i potvrde | isto | `za_potvrdu(nalog)`: popis materijala i oznaka rubova koje čovjek mora potvrditi, s kandidatima (desni stupac „Provjere“ na ekranu 2). Potvrda materijala → alias teksta (D-32) + rubovi tog materijala se ponovno prepoznaju; potvrda trake → ISTI-oznake se pamte uz materijal (i kao zadana traka te klase), oznake s vlastitim dekorom (`1/22 CHAMPAGNE UM`, `MEL CRNA NK`) općenito — jednom potvrđeno vrijedi za sve naloge. |
| Uvoz datoteka | `hub/nalozi/uvoz_datoteka.py` | CPW (kupčev PPW, PanelWizard / PPNEST export, Corpus `FORMAT;CORPUS->PW`) i PPNEST CSV (SIFRA MAT = Winstore kod → razina „Winstore“, GOD, CIX ime, napomena) → materijali + elementi kroz šifrarnik. Isti materijal iz više datoteka spaja se u jedan; ista datoteka (hash) ne uvozi se dvaput; **stariji PPNEST izvoz istog materijala** (`…_110205.CPW` uz `…_121006.CPW`) se preskače i prijavi — PPNEST pri ponovnom izvozu ostavlja staru datoteku u mapi (BRATEK, BLAGO_ADRIJANA, HUMER, MAZUR, BOGDANIĆ). CPW `M` / `A` bez naziva trake → `MEL-ISTI` / zadana ABS oznaka materijala. |
| Export-zapis | `nalozi.elementi_za_export` | nalog → element-zapis kakav čita `hub.formati.nalog_io` (rb, nalog, L, W, kom, SIFRA MAT = Winstore kod, deb, mat, god, traka L/D/G/O = Pantheon naziv trake, tip M/A po klasi, cix, napomena 14 zn., prolaza, glodalo) — ulaz za korak 3 (CSV + CIX, CPW, CPO). |
| API | `hub/api/nalozi_api.py` | `/api/kupci`, `/api/nalozi`, `/api/nalog/{id}` (cijeli nalog za ekran 2), statusi, materijali, elementi, potvrde, `POST /api/nalog/{id}/uvoz` (upload CPW / CSV), `ponovi-prepoznavanje`, `elementi-export`; `/docs` za isprobavanje. |
| Baza | `hub/schema.sql` v2, `hub/db.py` | kupac + adresa / OIB / mjesto / pretraga; `nalog_materijal` s ulaznim nazivom, Winstore kodom i „za potvrdu“; `materijal` / `traka` / `kupac` dobivaju stupac `trazi` (oba pisanja: BIJELI i BJELI, KAŠMIR i KASMIR); početni korisnici (IVANA, GORAN, SANELA, VP, IGOR) i postavke (kerf, zadani rabati, početak brojača). Stara baza (v1) se migrira sama pri prvom otvaranju. |

## 2. Provjera na testnim nalozima (`py -m hub.nalozi.provjera`)

| Nalog | CPW: mat / el / kom / m² | CSV: mat / el / kom / m² | Slaže se | Za potvrdu |
|---|---|---|---|---|
| BLAGO_ADRIJANA | 6 / 72 / 156 / 49,92 | 6 / 72 / 156 / 49,92 | da (stariji izvoz PVC preskočen) | `MEL CRNA NK` (nema 0,5/22), `ABS-ISTI` za PVC CRNI MAT (dva identična `ABS 1/22 CRNA MAT`) |
| BLAGO_JASA | 2 / 18 / 32 / 5,97 | isto | da | — |
| BOGDANIC_IVA | 5 / 86 / 158 / 56,67 | isto | da | — |
| BRATEK_KUPAC1 | 3 / 40 / 108 / 42,04 | isto | da (stariji izvoz BIJELI NK preskočen: 65 kom kao u CPO-u pile) | `1/22 CHAMPAGNE UM`, `ABS-ISTI` za CHAMPAGNE UM (nema trake UM) |
| HUMER_OMIS | 2 / 89 / 225 / 76,55 | isto | da | — |
| HUMER_OMIS — kupčev PPW (5 CPW) | 5 / 121 / 278 / 98,53 | — | — | — (i `taverna` prepoznat) |
| MAZUR_16 | 4 / 64 / 171 / 50,76 | 4 / 64 / 171 / 50,76 | brojevi da; materijal `IV_HR_CREMONA_CANNOLO_19` u CSV-u za potvrdu (SIFRA MAT `K2739DC-19` ne postoji) | tipfeler operatera |
| ROMIC_NALOG | — (samo pila) | — | — | — |
| TURALIJA_TUKA | 2 / 16 / 32 / 8,54 | isto | da | — |
| VARGA_POTNJANI | 2 / 54 / 103 / 23,57 | isto | da | — |

Sve razlike koje su se pojavile bile su u podacima, ne u Hubu: (1) PPNEST ostavlja stare izvoze u mapi (rješeno pravilom „najnovija datoteka
po materijalu“ + izvještaj što je preskočeno); (2) tipfeler u SIFRA MAT; (3) trake koje u Pantheonu ne postoje (11 §5.3).

## 3. Što ovo znači za ekrane (mockup v0.4)

Ekran 1 (popis) dobiva podatke iz `GET /api/nalozi` (status, kupac, materijala / elemenata / komada, broj stavki za potvrdu, rokovi).
Ekran 2 (unos) iz `GET /api/nalog/{id}`: zaglavlje (kupac, rabat, kerf), lijevo materijali sa zadanom trakom i identom, sredina elementi
s rubovima (tekst + prepoznata traka), desno „Provjere“ = `za_potvrdu` s kandidatima; klik na kandidata = `POST …/potvrdi` ili
`…/potvrdi-traku`, i stavka nestaje za sve naloge. Uvoz kupčeve datoteke = `POST /api/nalog/{id}/uvoz` (datoteka se sprema u `ulaz\<NALOG>\`
uz bazu). Dijalog „Kupac potvrdio“ (3b) = `POST /api/nalog/{id}/status` sa `status = potvrdjeno`, datum, način, rok obećan, prioritet.

## 4. Što treba Igor

1. **Pokrenuti na svom PC-u** (u `30_NOVI_PROGRAM`; ako `hub.db` već postoji iz koraka 1, sama se nadogradi na shemu v2):
```bat
cd C:\Users\Administrator\Desktop\IGOR\CLAUDE_COWORK\Paneli_Production_Hub\30_NOVI_PROGRAM
pip install -r requirements.txt
py -m hub.sifrarnici.uvoz --db hub.db --pantheon ..\..\ph_identi.csv --winstore ..\04_STROJEVI\NESTING\11092026.XML --kupci ..\..\ph_subjekti.csv --poste ..\..\ph_poste.csv
py -m hub.nalozi.provjera --db hub.db --nalozi ..\05_NALOZI_ZA_TEST --md ..\20_ANALIZA\12a_provjera_naloga.md --obrisi
set HUB_TEST_DATA=C:\Users\Administrator\Desktop\IGOR\CLAUDE_COWORK\Paneli_Production_Hub\05_NALOZI_ZA_TEST
py -m pytest -q
```
Očekivano: `Kupci: 3619 kupaca`, `Sažetak: 9 naloga; CPW ↔ CSV slaže se 7 / 8; materijala 57 (sigurno 56)`, testovi prolaze
(`test_formati::test_ppnest_csv_iz_txt_identican` treba PPNEST TXT datoteke — na tvom disku ih ima). Zatim `GIT_POSALJI.cmd`.
2. **Početni broj naloga** (postavka `brojac_naloga_pocetak`, sada 1): želiš li nastaviti niz Pantheon ponuda (npr. 3300) ili krenuti od 1 u novom nizu? Naziv naloga koristi taj broj (`HUMER_OMIS_3301`).
3. **E-mail kupaca**: u `tHE_SetSubj` ga nema (kontakti su u zasebnoj tablici) — do proširenja izvoza (`IzvozPantheon_v2.ps1`, tablica kontakata) ured upisuje e-mail u Hub na kartici kupca. Rabati i dani plaćanja ionako žive u Hubu (D-40).
4. **Kratki naziv kupca** u nazivu naloga — prijedlog iz Pantheon naziva (HUMER, BOGDANIC, ROMIC) se može promijeniti pri otvaranju naloga; ako želiš drukčije pravilo (npr. uvijek naziv obrta), reci.
5. **Krajnji kupci (D-48, odlučeno 13. 9.)**: zajednički subjekt „Krajnji kupac“ postoji u Pantheonu i Hub ga koristi kao zadani (postavka `krajnji_kupac_subjekt`). U koraku 4 (eSlog) ime osobe i naziv naloga idu u napomenu dokumenta — provjeriti na jednoj probnoj ponudi da uvoz uzme kupca iz uloge BY.

## 5. Sljedeće (korak 3)

Exporti iz naloga: CSV + CIX za bNest (imena CIX iz Hub brojača, D-23), CPW za PanelWizard (paralelni rad D-11), CPO za pilu (optimizator iz
`hub/optimizacija`), sve iz `elementi_za_export`; uz to čitanje rezultata (CPO sheme, MNO) natrag u nalog. Paralelno: uvoz Excel / rukopis
kupca (skill krojna-ponuda), okov (D-32), Corpus paket (D-29) čim stigne uzorak.
