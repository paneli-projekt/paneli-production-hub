# Paneli Production Hub — sažetak audita specifikacije (10. 9. 2026.)

> **Napomena za nove sesije (12. 9. 2026.):** ovo je početni audit. Aktualno stanje projekta, otvorene stvari i sljedeći koraci su u
> **`STANJE.md`** (čitati prvo), odluke u `DECISIONS.md` (D-01 … D-42). Audit je zatvoren 11. 9. (D-28); u tijeku je faza 2 (mockup + odluke o toku).

Spremiti u: `CLAUDE_COWORK\Paneli_Production_Hub\20_ANALIZA\`
Izvor: audit ChatGPT sažetka specifikacije, razgovor s Igorom u Claude chatu.

## Odluke Igora (10. 9. 2026.)

1. Praćenje proizvodnje ostaje ZASEBAN sustav (stari APEX program, novi u kasnijoj fazi).
   Hub ipak mora imati stabilan ID naloga i izračunate količine operacija
   (dm rezanja, dm kantiranja, rupe, m² kantiranja) kao izlaz koji čeka.
2. Warehouse modul Huba je IZVOR ISTINE za količine ploča, restlova i traka (ne Pantheon).
   Posljedica: ulaz robe u Hub iz istog eSlog XML-a koji ide u Pantheon (primke),
   mjesečno usklađenje Hub ↔ Pantheon s izvještajem razlika. Pantheon = financijska istina.
3. Kroz PanelWizard dnevno prolazi 10–15 naloga (~3.000/god) → SQLite za start je dovoljan.
4. Testni nalozi: postojeći iz `CLAUDE_COWORK\Obrada kupaca` (ne kopirati), dopuniti
   3 naloga datotekom za pilu + snimkom PW optimizacije. Novi primjeri samo za tipove
   koji fale (restl, veliki, problematičan). Nalog s NESTINGA najvažniji — još nijedan primjer.
5. Podaci za audit skupljaju se u `CLAUDE_COWORK\Paneli_Production_Hub\` (mape 00–08);
   Igorove napomene idu u postojeći `STO_OVDJE.txt` u svakoj mapi; prazno = "nema"/"ne znam".

## Što već postoji (dokument to nije znao)

- **krojna-ponuda skill** = POC C (Pantheon ponuda) + veći dio §13 obračuna:
  PW krojna PDF → stavke (materijal, rezanje, kantiranje, restl upozorenja, prijedlog okova
  preko cjenik.csv/alias.csv) → eSlog XML → Pantheon. Pravila obračuna u `references/pravila.md`.
  Hub ih PRESELJAVA, ne specificira iznova.
- **AI čitanje rukopisa** (isti skill) = pola POC-a B: konvencije (podvlake = kantovi,
  "ISTI" = traka u dekoru ploče, NUT, UREZ GOLA, CNC po skici), stupac PROVJERI.
  Fali samo web ekran "original + prepoznato + potvrdi".
- **Pantheon integracija** = eSlog uvoz, dokazan za primke (Knjiga na VM 192.168.5.201) i ponude.
  Otvoreno samo ČITANJE iz Pantheona (read-only SQL ili izvoz) — pitanje u 08_PANTHEON/pristup_bazi.
- **regal-traka** (v1.9.x, VM 192.168.5.201:8080): stanje po IDENTU ne po roli (poznata slabost),
  lokacije R3-05-B, QR, evidencija promjena `ev`, bez korisničkih prava, JSON baza,
  Python server bez ovisnosti, 137 automatskih provjera. Preporuka: opcija B — integracija
  preko API-ja, bez refaktora; postaje dio Warehouse sloja za trake (njeni metri su stanje).
- Baza okova i cjenici = Pantheon izvozi (ph_identi.csv, cjenik.csv) + interne kolone. Ne graditi novo.
- Restlovi danas: Excel na `Z:\TESTMAP\SANELA\RESTLOVI U SKLADIŠTU` — stvarna rupa, Hub tu donosi najviše.

## Prijedlozi izmjene plana

- Redoslijed faza: prvo "kralježnica" (standardni nalog + importer CPW/klijentski export +
  obračun iz skilla + eSlog ponuda + restlovi s QR), zatim AI import ekran, integracija
  regal-trake; saw optimizer PARALELNO kao istraživački POC, ne kao faza 3.
- Optimizer benchmark = 3 metrike: iskorištenje, broj rezova/uzoraka, prihvaćanje operatera.
  Treba stvarna ograničenja pile (glavni rezovi, max duljina, obrez).
- Nesting driver ovisi 100 % o formatu nesting softvera — rizik br. 1 dok se ne vidi.
- Model elementa (§6) dodati: faza, cjelina, podaci za etiketu (pozicija u korpusu), veza na nalog proizvodnje.
- Stablo direktorija skraćeno (bez 09–13 i bez praznih podmapa u 30_NOVI_PROGRAM).
- Stack: Python + SQL (SQLite → PostgreSQL) + web; dugoročno jedan proces i jedna prijava
  na VM-u (danas Knjiga :8765 + regal-traka :8080).
- "Pouzdanost 63 %" = kozmetika; stvarno radi lista označenih polja za provjeru.

## Procjena izvedivosti (Claude)

| Modul | Sigurnost |
|---|---|
| Standardni nalog, importeri, obračun, eSlog ponuda, restlovi+QR, etikete, uloge, audit | visoka |
| AI import s ekranom za potvrdu | visoka |
| Integracija regal-traka | visoka |
| Čitanje stanja iz Pantheona | srednja (ovisi o pristupu) |
| Nesting driver | nepoznato do uvida u format |
| Saw optimizer na razini PanelWizarda u praksi | srednja–niska u prvom pokušaju, puno iteracija |

Kralježnica: ~mjesec dana; cijeli opseg: 6–12 mjeseci Igorovim tempom.

## Otvorena pitanja (čekaju podatke u mapama)

1. Pila: proizvođač/model + datoteka koju uvozi (`04_STROJEVI/PILA`, `01_PANELWIZARD/export_na_pilu`)
2. Nesting softver + primjer ulaza (`04_STROJEVI/NESTING`, `03_NESTING_APLIKACIJA/export_za_nesting`)
3. Read-only pristup Pantheon SQL bazi da/ne (`08_PANTHEON/pristup_bazi/PRISTUP.txt`)
4. Source code klijentske i nesting aplikacije (jezik, git)
5. Nalog koji je išao na nesting (`05_NALOZI_ZA_TEST/novi_nalog_nesting`)

## Sljedeći korak

Kad su popunjene mape PRIORITET 1 → pravi audit u 20_ANALIZA/ (model podataka, arhitektura, plan faze 1).
Punu aplikaciju ne graditi dok Igor ne odobri rezultate audita.

## Dopuna 10. 9. 2026. popodne — audit napravljen

Igor je napunio mape (9 testnih naloga u `05_NALOZI_ZA_TEST`, strojevi, PPW/PPNEST buildovi, PW instalacija). Nalazi su u:

- `02_formati_i_strojevi_2026-09-10.md` — pila Biesse Selco Sektor 450 / OSI (.cpo), nesting Biesse Rover B 2231 / bSolid+bNest (CSV+CIX → .mno),
  PPNEST 1.2 (.NET 6) kao stvarni "standardni nalog", specifikacija svih formata; parseri u `skripte/parseri.py`.
- `03_tok_naloga_i_benchmark_2026-09-10.md` — tok danas, benchmark 50 materijala (113 ploča, 64,6 % bruto), pila vs nesting (HUMER: 10→9 i 6→5 ploča),
  naplaćeno vs izrezano (medijan 1,26× m² dijelova), 6 nalaza za provjeru (ponuda 2929 bez stavki 1–2!). Tablica: `benchmark_nalozi.csv`.
- `04_model_podataka_arhitektura_plan_2026-09-10.md` — model podataka, arhitektura (jedan Python servis na VM-u, 8 modula), plan faze 1 u 7 koraka
  s kriterijima prihvaćanja, 12 otvorenih pitanja za Igora.

Otvorena pitanja 1–5 od jutros: (1) pila = Sektor 450 / OSI, format .cpo — RIJEŠENO; (2) nesting = bNest, CSV+CIX — RIJEŠENO;
(3) Pantheon read-only — RIJEŠENO (PRISTUP.txt); (4) source code PPW/PPNEST — I DALJE OTVORENO (mape prazne, PPNEST je .NET 6 s .pdb);
(5) nesting nalog — RIJEŠENO (HUMER, 2 materijala s .mno).
