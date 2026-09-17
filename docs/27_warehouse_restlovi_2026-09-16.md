# Paneli Production Hub — 27: Warehouse, prvi zadatak — uvoz evidencije restlova (D-64)

Stanje 16. 9. 2026. navečer. Prvi zadatak Warehousea po STANJE.md: uvesti `20_ANALIZA\RESTLOVI_V7.xlsm` i izmjeriti koliko se dekora iz
evidencije skladišta veže na Pantheon idente kroz šifrarnik — jedino mjesto gdje stvarni podaci mogu iznenaditi. Shema **v12**, novi modul
`hub/skladiste/restlovi.py`, **133 testa prolaze** sa stvarnim podacima (6 novih u `tests/test_restlovi.py`). Puni izvještaj uvoza: `27a_uvoz_restlova_izvjestaj_2026-09-16.md`.

## 1. Što je u evidenciji (RESTLOVI_V7.xlsm, 28. 8. 2026.)

| | |
|---|---|
| Restlova (list RESTLOVI) | **1 363** — 1 226 NA SKLADIŠTU, 137 PROVJERI (izgrebano, više mjera…); ≈ 1 540 m² |
| Različitih dekora (stupac STARI OPIS = naziv kao u PW-u) | **429** |
| Grupe | DRVNI DEKOR 341, UNI DEKOR 251, AKRIL PVC 220, COMPACT 181, EGGER DEKORI 116, LESONIT/ŠPER/SIROVI/OSB 108, DEKORI RAZNI 102, IV BIJELI 44 |
| Lokacije | A001…A010, B001…B010, C003…C009 i SATOR B/C x.y (31 restla bez lokacije) |
| Kom | 1 290 × 1 kom; 73 redaka s 2–13 istih komada („VISE MJERA“) |
| **Debljina** | **u tablici je NEMA** — zna se samo preko identa |
| List MAPIRANJE DEKORA | ručno provjereno mapiranje dekor → ident: 366 TOČNO, 44 PROVJERI, 19 NEMA U CJENIKU |
| Stupci Nalog (izlaz), Datum | prazni kroz cijelu tablicu |

## 2. Mjera: koliko se dekora veže na idente kroz šifrarnik

Vezanje ide kroz `prepoznaj_materijal` (alias → Winstore kod → naziv), Excelov ident služi samo kao usporedba i kao potvrđena rezerva (TOČNO).

| | dekora | restlova |
|---|---|---|
| **vezano sigurno** | **372 (87 %)** — 366 alias + 6 naziv | **1 223 (90 %)** |
| za potvrdu (Hub daje kandidate) | 49 (11 %) | 119 (9 %) |
| nema kandidata | 8 (2 %) | 21 (2 %) |

* **Svih 366 dekora koje Excel ima kao TOČNO Hub veže na ISTI ident (0 razlika).** To nije slučajno: alias-tablica skilla krojna-ponuda
  (369 parova, u Hubu od koraka 1) nastala je iz istog popisa restlova, pa je to mapiranje već bilo u Hubu — uvoz ga je samo potvrdio.
* **Bez alias-tablice** šifrarnik po samom nazivu veže 244 dekora (57 %), od čega se 218 slaže s Excelom, a **13 ne** (`BIJELA BIJELA ISPUNA`,
  `PRADO AGATE GREY`, `CROMIX WHITE`, `H1277 25 MM`…) — jer nazivi u evidenciji nemaju debljinu ni kod dekora. Zato aliasi ostaju
  obvezni, a svaka nova potvrda ide u alias-tablicu (D-32).
* **6 dekora Hub veže sam po nazivu, a Excel ih nije imao** (10 restlova): `IV QUARTZ` → IV000270 IVERAL HRAST QUARTZ AW 19, `IV PJESAK` → IV000016
  IVERAL PIJESAK 19, `IV RIGOLETO BRONZA` → IV000187, `IV SLJIVA 8MM` → IV000083, `W1200 PORCULAN BIJELA` → IV000858 PORCULANSKA PLOČA 12MM BOOST WHITE,
  `AK MAROON SJAJ VA 105` → IV000566. Sigurni su po pravilu D-43 (jedini ident tog dekora), ali su bez debljine — **Igor: pogledati ovih 6**.
* **7 dekora Hub veže po nazivu, a Excel je nagađao DRUGI ident** (`HR FURNIR 25MM`, `MDF FURNIR 0227`, `IV AMOUK`, `IV EVOKE LIGHT`, `IV HR NATUR GRUBI`,
  `AK ANTRACIT SJAJ`, `PANEL PLOCE BREZA 18MM`) — namjerno idu na potvrdu s oba kandidata, Hubov prvi.
* **Za potvrdu (57 dekora / 140 restlova)** su tri vrste: (a) dekor bez debljine s više identa (`IV BIJELI GLATKI` 10/18/25, `IV HR SONOMA GOMOLJASTI`
  18/25, `IV SIVA SVJETLA`, `PVC GALAXY`…) — jedan klik ureda; (b) opisni nazivi (`JEDNOSTRANI`, `FANGO`, `13MM`, `SIROVA (VLAGO OTPORNA)`,
  `SIVA SA CRNOM ISPUNOM`) — treba pogledati restl; (c) **8 dekora bez kandidata** (`(FRANJIC)` 6, `IV FRANJIC CUDAN DEKOR` 5, `IV U775` 3,
  `JEDNA OD NIJANSI` 2, `SKUPIII` 2, `IV VANILA`, `H 1398`, `H 1345`) — u Pantheonu ih nema, kao i u Excelu (NEMA U CJENIKU).
* M² iz mjera = Excelov M2 na svih 1 363 redaka (0 razlika).

**Zaključak za Igora:** posao oko potvrda je mali — 57 dekora (140 restlova, 10 % stanja), od toga polovica jednim klikom; 8 dekora nema
u Pantheonu i treba odlučiti otvaraju li se identi ili se ti restlovi vode „bez identa“ (ne ulaze u obračun ni rezervaciju dok nemaju ident).

## 3. Što je napravljeno

**Shema v12** (`hub/schema.sql`, migracija sama pri prvom otvaranju): `ploca_stanje` izbačena (Winstore pokriva sve pune ploče, D-64/1);
`restl` proširen — `oznaka` (R0001…, ide na QR), `dekor_ulaz`, `ident_ulaz` (Excel), `grupa`, `provjeri` + `razina` + `kandidati_json`
(isti obrazac „za potvrdu“ kao materijal naloga, D-46/4), `izvor` (excel_v7 | prijedlog | rucno), `nalog_materijal_id` (iz koje sheme je predložen),
`nalog_izlaz`, `potvrdio` / `potvrdjeno` (skladištar zalijepio QR); `rezervacija` bez `ploca_stanje_id`.
Statusi: `slobodan | rezerviran | provjeri | prijedlog | potrosen | otpisan` (Excel: NA SKLADIŠTU / REZERVIRAN / PROVJERI / PRODAN / OTPISAN).

**`hub/skladiste/restlovi.py`** — prilagodnik restlova s istim sučeljem kao ploče i trake (D-64): `ucitaj_xlsm`, `prepoznaj_dekor`, `uvezi_excel`
(idempotentno po oznaci; ne dira restlove koje je skladištar u Hubu potvrdio ni Hubove prijedloge), `potvrdi_dekor` (svi restlovi tog dekora +
alias), `stanje(materijal_id | ident, samo_slobodni)`, `lokacija(oznaka)`, `sazetak`. CLI:

```
py -m hub.skladiste.restlovi --db hub.db --uvoz ..\20_ANALIZA\RESTLOVI_V7.xlsm --md ..\20_ANALIZA\27a_uvoz_restlova_izvjestaj.md
py -m hub.skladiste.restlovi --db hub.db --stanje --ident IV000090
py -m hub.skladiste.restlovi --db hub.db --potvrdi "IV JAVOR (KRONO)" IV000013 --tko IVANA
```

Pravila vezanja (provedba D-64/2): šifrarnik siguran → ident; šifrarnik siguran ali Excel TOČNO drugi ident → potvrda (sukob); šifrarnik po nazivu a
Excel PROVJERI drugi → potvrda (oba kandidata); šifrarnik nesiguran a Excel TOČNO → Excelov ident (razina `excel`); inače potvrda / nema.
Potvrđeni par postaje alias (izvor `restlovi`) i vrijedi za nalog, CPW i sve buduće restlove istog dekora.

**Na stanju** su restlovi `slobodan / rezerviran / provjeri` s vezanim identom; `prijedlog` (D-64/3) i nevezani dekori se ne broje.

## 4. Sljedeće (ostatak Warehousea, D-64) — nakon Igorove potvrde brojki

1. `hub/skladiste/ploce.py` — pogled nad `winstore_ploca` (stanje, lokacija) istim sučeljem; `trake.py` proširiti na `lok` / `q` (već čita).
2. **Rezervacija po nalogu** (D-42/4): `rezerviraj` / `oslobodi` na sva tri izvora, raspoloživo = fizičko − rezervirano + naručeno; status
   naloga „skladište“ (D-35) dobiva upozorenje i popis za nabavu.
3. **Restl kao PRIJEDLOG iz potvrđene sheme** (D-64/3): iz `optimizacija.slaganje_json` korisni ostatak ≥ 400 × 400 i ≥ 1 m² (D-19) → `restl`
   sa statusom `prijedlog`, `izvor = prijedlog`, `nalog_materijal_id`; skladištar potvrdi (`potvrdio`, QR) → `slobodan`.
4. Potreba preko svih potvrđenih naloga (D-42/5) za Nabavu; `GET /api/skladiste/…` za ekran 4.
5. QR naljepnica restla (oznaka + ident + mjere), ispis kroz `hub/ispis/` (D-76).
