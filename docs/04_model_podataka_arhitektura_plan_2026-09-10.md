# Paneli Production Hub — audit 4/4: model podataka, arhitektura, plan faze 1, otvorena pitanja

Stanje 10. 9. 2026. Temelji se na 02 (formati) i 03 (tok i benchmark). **Ovo je prijedlog za Igorovo odobrenje — kod se ne piše dok nije odobreno.**

## 1. Što audit mijenja u odnosu na sažetak od jutros (00_audit_sazetka)

| Jutros smo mislili | Sada znamo |
|---|---|
| Nesting driver je rizik br. 1 (format nepoznat) | Rizik je **mali**: bNest jede CSV (28 stupaca) + CIX po elementu, oboje već generira PPNEST; rezultat .mno je XML koji se lako čita. |
| PanelWizard je središte procesa | Središte unosa je **PPNEST** (vlastita .NET 6 aplikacija); PW je optimizator pile + generator CPO. Hub zamjenjuje PPNEST + ručni dio PW-a, a PW ostaje "engine" pile dok Hub nema optimizator. |
| Saw optimizer = istraživački POC | I dalje POC, ali imamo **ground truth**: CPO sadrži PW-ove sheme i rezove za svih 50 materijala → benchmark se može automatizirati odmah. |
| Čitanje Pantheona otvoreno | Riješeno (ph_*.csv, `hub_*.csv`); fali samo stanje (tHE_Stock — dodano u skriptu izvoza). |
| Stablo direktorija 00–13 | Testni nalozi u 05 po predlošku (9 naloga, 338 datoteka) — dovoljno za fazu 1; mape 06/07 (skladište, etikete) još prazne, ali etikete su riješene snimkama (ZT411 ZPL, LBL_PP1). |

## 2. Model podataka (jezgra — "standardni nalog")

Načelo: jedan zapis naloga iz kojeg se **generiraju** svi današnji formati (CPW, CSV+CIX, CPO kasnije, eSlog) i u koji se **učitavaju** svi rezultati (CPO, MNO). Sve što je danas u PPNEST CSV-u ostaje 1:1 (da export bude istovjetan), dodaje se ono što nedostaje.

```
kupac            id, naziv, šifra_pantheon (acSubject), kontakt, napomena
nalog            id (npr. 2026-03258), kupac_id, naziv_pw ("MAZUR_3258_16"), datum, status (unos→provjera→optimirano→ponuda→proizvodnja→zatvoren),
                 put_default (pila|nesting|oboje), ponuda_pantheon (26-010-003258), izradio, verzija, napomena
materijal        id, pantheon_ident (IV000090), naziv_pantheon, sifra_proizvodjaca (W908ST2-18), naziv_kratki ("IV BIJELI NK 18"), debljina, ploca_L, ploca_W,
                 obrez, god (da/ne), vrsta (IV/MDF/PVC/AK/RP/ZO/PS…), aktivan            + materijal_alias (tekst kako ga pišu PW/PPNEST/kupci → materijal_id)
traka            id, pantheon_ident (TR001254), naziv ("ABS 1/22 JELA CLAY"), debljina (0,5/1/2), širina (22/44), vrsta (ABS/MEL/PVC), dekor, regal_traka_ident
nalog_materijal  id, nalog_id, materijal_id, put (pila|nesting), god, napomena, ploca_L/W override (restl!), status_optimizacije
element          id, nalog_materijal_id, rb, naziv ("1_ELEMENT" / "L_BOK"), L, W, kom, god (H/V/ne), gotova_mjera ("777x135"),
                 rub1..rub4 (traka_id ili null), rub_kod1..4 (A/M), obrada (CNC/NUT/UREZ/GLODANJE 1|2), program1/2, ljepljenje, napomena,
                 cix_ime, faza, cjelina, pozicija_u_korpusu, izvor (cpw|excel|rukopis|ručno), provjeri (bool — iz AI čitanja)
okov_stavka      id, nalog_id, pantheon_ident (OK…), naziv, kom, izvor_tekst (kako je kupac napisao), provjeri
optimizacija     id, nalog_materijal_id, engine (PW|bNest|Hub), datum, broj_ploca, iskoristenje, m2_dijelova, m2_ploca, m2_za_naplatu,
                 rezova, sheme_json (iz CPO PAT/CUT ili .mno FOGLIO/POS), datoteka_id
ploca_stanje     id, materijal_id, lokacija, kom (izvor istine = Hub), zadnja_inventura                      (Warehouse)
restl            id, materijal_id, L, W, kom=1, lokacija, qr, izvor (nalog_materijal_id / ručno), status (slobodan|rezerviran|potrošen)
rezervacija      id, restl_id | ploca_stanje_id, nalog_materijal_id, kom, datum, korisnik
obracun_stavka   id, nalog_id, pantheon_ident, naziv, kolicina, mj, cijena, rabat, izvor (materijal|rezanje|traka|kantiranje|okov|usluga), pravilo
dokument         id, nalog_id, vrsta (cpw_ulaz|cpw_pw|csv|cix|cpo|pnl|pdf_krojna|mno|lbl|ponuda_pdf|eslog|foto), putanja, hash, datum
dnevnik          id, tko, kada, entitet, id_entiteta, što (audit trail)
```
Trake i njihovi metri: Hub računa metre kantiranja po traci iz elemenata (kao PW), a **stanje traka ostaje u regal-traci** (API); Hub samo šalje "potrošnja po nalogu".

## 3. Arhitektura (prijedlog)

- **Jedan Python servis** (FastAPI + SQLite, kasnije PostgreSQL) na VM-u 192.168.5.201, uz Knjigu (:8765) i regal-traku (:8080); web sučelje bez frameworka (kao regal-traka), radi u LAN-u, bez interneta.
- **Moduli** (svaki = paket, vlastite provjere):
  1. `sifrarnici` — materijali/trake/okov iz `hub_*.csv` + aliasi; osvježavanje iz ph_*.csv izvoza.
  2. `nalog` — unos/uređivanje, verzije, statusi, kontrola (svaki materijal ima ploču, svaki rub traku).
  3. `import` — CPW (PPW), Excel (BRATEK stil, PW predložak), AI rukopis (iz skilla krojna-ponuda → ekran "original + prepoznato + potvrdi").
  4. `export` — `CSV + CIX` za bNest, `CPW` za PanelWizard, kasnije `CPO` za OSI; etikete ZPL.
  5. `rezultati` — watcher na mape: `.cpo` (OSI ulazna mapa / PW export) i `.mno` (bNest projekt) → optimizacija + prijedlog restlova.
  6. `warehouse` — ploče, restlovi (QR), rezervacije, inventura; ulaz robe iz istog eSlog XML-a kao primke; mjesečno usklađenje s Pantheonom (ph_stock.csv).
  7. `obracun` — pravila iz `krojna-ponuda/references/pravila.md` + `cjenik.csv`, stavke → provjera → eSlog XML ponude (postojeći generator).
  8. `api` — `/api/nalog`, `/api/restl`, `/api/traka/potrosnja` (regal-traka), `/api/pantheon/stavke`.
  9. `ai` — (dodano 11.9., D-15) jedini ulaz za sve LLM pozive: `ai.run(zadatak, ulaz) -> strukturirani rezultat + provjeri=True`.
     Zadaci su imenovani (`rukopis_krojna`, `rukopis_okov`, `normalizacija_materijala`, `sazetak_napomene`…), a koji model/pružatelj ih izvršava
     je konfiguracija (tablica ili `ai.toml`), ne kod. U fazi 1 postoji samo pružatelj `claude` (već u skillu krojna-ponuda) i `none`
     (deterministički, npr. alias-tablica). Sve što iz `ai` izađe ulazi u polja s `izvor='ai'`/`provjeri=True`, nikad izravno u obračun,
     export za strojeve ili skladište; svaki poziv se upiše u `dnevnik` (zadatak, pružatelj, model, verzija prompta, trajanje, ulazni hash).
- **Ne gradi se u fazi 1**: vlastiti optimizator pile (POC paralelno na CPO ground truthu), praćenje proizvodnje, korisnička prava (samo ime korisnika + dnevnik).

## 4. Plan faze 1 — "kralježnica" (Igorovim tempom ≈ 4–6 tjedana)

| Korak | Isporuka | Kriterij prihvaćanja (na 9 testnih naloga) |
|---|---|---|
| 1 | Šifrarnik materijala/traka s aliasima | svih 50 CPO materijala i 76 ponudbenih identa iz testova mapirani bez ručnog rada |
| 2 | Nalog + elementi (web unos, kopiranje, verzije) | HUMER (280 el., 6 mat.) unesen za < 15 min iz CPW-a |
| 3 | Import CPW / Excel | 5 HUMER CPW-ova i BRATEK xlsx → identični elementi kao u PPNEST CSV |
| 4 | Export CSV+CIX i CPW | bNest učita Hubov CSV+CIX bez greške (isti rezultat kao PPNEST); PW učita Hubov CPW |
| 5 | Čitanje CPO i MNO | za svih 9 naloga broj ploča, m² i iskorištenje kao u benchmark_nalozi.csv; restlovi predloženi iz zadnje ploče |
| 6 | Obračun + eSlog | količine m² / m traka / usluge = Pantheon ponuda (tolerancija zaokruživanja); kontrola "materijal bez stavke" javlja BLAGO 2929 |
| 7 | Restlovi s QR + rezervacija | RESTLOVI Excel uvezen; nalog može rezervirati restl → override dimenzije ploče u exportu |

Nakon toga (faza 2): AI import rukopisa s ekranom za potvrdu, integracija regal-trake, etikete iz Huba, izvještaj Hub↔Pantheon, POC optimizatora.

## 5. Otvorena pitanja za Igora (odgovori idu u ovaj dokument ili STO_OVDJE.txt)

1. ~~CPW rubovi~~ **ODGOVORENO 11.9.**: redoslijed je naizmjenično **duža1, kraća1, duža2, kraća2** — potvrđeno testnim uvozom u PW 27.8.2026. (skill krojna-ponuda, `scripts/upit2cpw.py`, DUZA=(0,2), KRACA=(1,3)). Isto vrijedi za RUB1–RUB4 u PPNEST CSV-u.
2. ~~PPW → PW~~ **ODGOVORENO 11.9.**: kupčev CPW se učita u PanelWizard samo radi količina (materijal, trake, usluge), a zatim se **ručno prekucava u PPNEST** da nalog ode u proizvodnju. Dvostruki unos — Hub ga uklanja.
3. ~~Source code~~ **ODGOVORENO 11.9.**: obje aplikacije pisane **interno**; izvorni kod je kopiran u `03_NESTING_APLIKACIJA\source_code` (NESTING_1.1.sln, KROJNA.vb 45 kB) i `02_KLIJENTSKA_APLIKACIJA\source_code` (PPWizard_5.2.sln, forme MATERIJALI/OKOV/VODILICE/AVENTOS/BUSENJE…). Nema gita. → Hub preuzima točnu logiku exporta CSV/CIX/CPW iz KROJNA.vb umjesto pogađanja iz datoteka.
4. Značenje stupaca PPNEST CSV-a: `GLODANJE` 1/2, `OBRADA`, `PROGRAM1/2`, `LJEPLJENJE`, `GOD`=0; odakle `SIFRA MAT` (upisuje se ručno ili bira iz liste u PPNEST-u?).
5. **Pila**: što znače prefiksi `I_` i `SA_` (dva računala / dva operatera / dvije pile?); prima li OSI `.cpo` iz bilo koje mape (može li Hub pisati izravno u OSI-jevu mapu narudžbi?).
6. **Ponuda 26-010-002929**: gdje su stavke 1–2 (5 ploča IV BIJELI NK 18)?
7. PW "Debljina reza 16 mm" — postavka?
8. ~~Pravilo pila vs. nesting~~ **ODGOVORENO 11.9.**: pila = MDF 3 mm, radne ploče, zidne obloge, compact, restlovi, nalozi < 1 pune ploče; sve ostalo nesting. Hub predlaže put po materijalu + m² dijelova, čovjek potvrđuje.
9. bNest baza materijala/ploča (`K2665AI-19-2800X2070.xml`) — može li se izvesti popis definiranih ploča (dimenzije, god) da Hub koristi iste šifre?
10. Restlovi: koja je verzija Excela u upotrebi (V7?) i koliko restlova trenutno; ima li nesting svoj ostatak koji se vraća u skladište?
11. Etikete na pili: koje podatke PW šalje printeru (format/predložak) — treba snimka ili primjer.
12. Tko su korisnici Huba u fazi 1 (Ivana, Goran, voditelj proizvodnje, Igor) i na kojim računalima (PW računalo, PPNEST računalo, VM)?

## 6. Dopuna 11. 9. 2026. — PW kao kalkulator obračuna, ne optimizator proizvodnje

Iz Igorove napomene (03 §6) slijedi da modul `optimizacija` u Hubu ima **dvije odvojene uloge**, koje danas obje radi PanelWizard:
1. **Kalkulator količina za obračun** — za svaki materijal u nalogu, bez obzira ide li na pilu ili nesting, izračun broja ploča, "površine za naplatu" (pravilo korisnog ostatka) i metara traka po dekoru. Mora davati brojke usporedive s PW-om jer o njima ovise cijene kupcima. **Ovo je prvi cilj vlastitog optimizatora (D-16) i mjeri se na svih 50 CPO-a.**
2. **Program za pilu** — samo za ono što Sektor 450 stvarno reže (MDF 3 mm, radne/zidne/compact ploče, restlovi, mali nalozi): jednostavniji slučajevi, često jedna ploča ili trake, gdje osnovna giljotinska heuristika + CPO writer pokrivaju posao. Velike serije ivera idu na nesting i tamo bNest već optimira.
Time "optimizator kao PW" prestaje biti rizik: za obračun treba reproducirati PW-ove brojke (ne nadmašiti ih), a za proizvodnju treba pokriti mali i jednostavni dio posla.
Dodatno: Hub prvi put može pokazati **razliku između naplaćene (PW) i stvarno potrošene (bNest .mno) količine** po nalogu.

## 7. Dopuna 11. 9. 2026. — što skill krojna-ponuda već ima za D-17

- `scripts/upit2cpw.py` — **CPW writer** (format CORPUS->PW, cp1250, rubovi D1/K1/D2/K2), potvrđen uvozom u PanelWizard.
- `scripts/optimizator.py` — **giljotinski kalkulator ploča** kalibriran prema PW-u (trim 10, kerf 4,4, god, shelf/best-short-side-fit, pravilo korisnog ostatka > 400 mm i > 1 m²), "validiran 20/20 vs PW" na ponudama; vraća broj ploča, m² za naplatu, iskorištenje, ostatke.
- `scripts/brza_ponuda.py` + `krojna2ponuda.py` — stavke ponude iz upita / iz PW krojne PDF.
→ D-17 korak 1 (kalkulator obračuna) **ne kreće od nule**: postojeći `optimizator.py` se preseljava u Hub i mjeri na 50 CPO-a iz benchmarka (do sada mjeren samo na broju ploča iz ponuda). Ono što fali: CPO writer (sheme za pilu), metri traka po dekoru u istom modulu, usporedba po materijalu s CUT1 shemama.

## 8. Odgovori Igora 11. 9. 2026. na preostala pitanja iz §5

- **4 (PPNEST CSV stupci)** — nije pitano posebno; odgovor se čita iz `KROJNA.vb` (source code sada dostupan). Ostaje: provjeriti GLODANJE 1/2, OBRADA, PROGRAM1/2, LJEPLJENJE u kodu.
- **5 (pila, prefiksi)** — `I_` i `SA_` = **dva računala / dva operatera** (Ivana, Sanela), svaki PanelWizard ima svoj brojač programa.
- **6 (CPO → OSI)** — PW sprema `.cpo` u **mrežnu mapu koju OSI čita**. Hub može pisati u istu mapu — najjednostavniji put do pile. (Putanju mape upisati u `04_STROJEVI\PILA\STO_OVDJE.txt`.)
- **7 (ponuda 2929 bez rb 1–2)** — 5 ploča IV 18 mm **naplaćeno na drugom računu**. Nije greška; ostaje argument da Hub veže nalog ↔ sve dokumente naplate.
- **8 (kerf 16 mm u PW-u)** — **namjerno**: PW računa obračun s 16 mm reza „zbog sigurnosti obračuna na nestingu“ (nesting reže glodalom 12 ili 16 mm; Sektor 450 pilom 5 mm). → Kalkulator obračuna (D-17/1): **kerf je varijabilan, bira ga korisnik koji radi nalog** (zadano 16 mm za nesting-obračun, 5 mm za pilu) + pravilo korisnog ostatka. Polje `kerf_mm` na `nalog_materijal`. **Za provjeru:** `krojna-ponuda/scripts/optimizator.py` ima DEFAULT_KERF = 4,4 mm — treba uskladiti.
- **9 (bNest baza ploča)** — održava operater nestinga, **može se izvesti/kopirati** → kopirati XML-ove ploča u `04_STROJEVI\NESTING\baza_ploca\`; Hub koristi iste šifre kao `SIFRA MAT`.
- **10 (restlovi)** — RESTLOVI **V7 još nije u funkciji**; vodi se stari popis iz kojeg je V7 nastao. → Hub uvozi stari popis (kolone provjeriti), V7 služi kao specifikacija što se htjelo. Ostatak s nestinga: **vraća se u skladište restlova (regal za restlove) i bilježi u Excel restlova** — Hub ga predlaže iz .mno i upisuje u `restl` s izvorom nalog/nesting.
- **11 (etikete na pili)** — nije odgovoreno; ostaje.
- **12 (korisnici faze 1)** — Ivana i Goran (unos naloga i ponude, uredsko računalo s PW-om), Sanela (restlovi i skladište ploča), voditelj proizvodnje (odluka pila/nesting, operater nestinga), Igor (administracija, šifrarnici, odobrenja).
