# Paneli Production Hub — audit 5: novi podaci (Winstore, restlovi, OSI), KROJNA.vb i priprema testova D-10

Stanje 11. 9. 2026. Nastavak na 02 (formati), 03 (tok/benchmark) i 04 (model/plan). Skripte: `20_ANALIZA\skripte\`, testne datoteke: `20_ANALIZA\test_D10\`.

## 1. Što je Igor dodao 11. 9. i što iz toga slijedi

### 1.1 Putanja pile (04_STROJEVI\PILA\STO_OVDJE.txt)
OSI čita `.cpo` iz **`Z:\Krojne_liste`** (server `\\Paneli-Pc`). PW piše tamo; Hub će pisati u istu mapu (test 3 dolje). Broj programa
(`I_0xxxx` / `SA_0xxxxx`) daje PW/operater — Hub treba vlastiti brojač koji ne sudara s postojećim nizom (otvoreno: nastaviti I_/SA_ ili
jedinstveni `HUB_xxxxx`; za test koristim HUB_00901–903).

### 1.2 Winstore — nesting ima AUTOMATSKO SKLADIŠTE PLOČA (04_STROJEVI\NESTING\Winstore.png + 11092026.XML)
Slika ekrana je **WINSTORE store manager 1.2.1.0** (Biesse): automatsko skladište ploča koje hrani Rover B — mjesta A00–A15, B01, B02,
ulaz IN1, viličar ("fork-lift 1"), kontrola težine po ploči, dnevnik ("Board: Code 27045MN-19-2800X2070 … Picking end / Placing end").
To do sada nije bilo u audit dokumentima i mijenja model Warehouse modula:

- **11092026.XML = izvoz Winstore inventara** (`<Inventory><Item>…`): 592 stavki, 524 različita koda, **374 ploče** u 184 stavki s količinom > 0
  (ostale stavke su šifrarnik s količinom 0). Polja: `Code` (= `<šifra dekora>-<deb>-<L>X<W>`, npr. `27049MN-19-2800X2070`), `Length`, `Width`,
  `Thickness`, `Grain` (1 = ima god: 443, 0: 148), `MaterialCode` (`27049MN-19`, `IV000065B-19`, …), `MaterialDescription`
  (`IVERAL KASMIR MN 27049MN 19MM`), `Drop` (**svugdje 0 → u Winstoreu nema restlova, samo cijele ploče**), `TotalQty / InternalQty / ExternalQty`
  (External svugdje 0). Isti kod se ponavlja više puta (39 kodova) = više stogova/lokacija iste ploče; lokacija (A09 …) nije u XML-u.
- Dimenzije: 483 × 2800×2070, 40 × 2800×1220 (PVC/MDF/akril), 35 × 2800×1300 (akril), ostalo 2840×1830, 2800×2050 … Debljine: 19 (301), 18 (226),
  25 (39), 16, 10, 22, 28, 38, 8, 12. Ima i "AMBALAZA <kupac>" ploča (ploče kupaca: ZLAJA, IVAN, PERO, SOKAC, HAVRO) i `1111PO-18 POVRAT OSTECENO`.
- **Posljedica za D-05/model:** `ploca_stanje` mora imati tri fizička izvora: (a) Winstore (cijele ploče uz nesting — izvor istine za nesting,
  strojno vođen), (b) regal/pila (ploče i ploče kupaca izvan Winstorea), (c) restlovi (Excel → Hub). Pantheon ostaje financijska istina.
  Hub u fazi 1 **čita** Winstore XML (dnevni izvoz, `11092026.XML` uzorak) i uspoređuje s Pantheonom; piše li se u Winstore (rezervacija, ulaz robe)
  — treba provjeriti u Winstore dokumentaciji (ima li import). Šifra `MaterialCode` (27049MN-19) je **četvrti** naziv istog materijala
  (uz Pantheon ident IV000090, PW/PPNEST tekst, PPNEST šifru K2751AE-19) → tablica aliasa iz 04 dobiva stupac `winstore_code`.
- Winstore kod ima točan format za `sifra_ploce` u Hubu: `<dekor>-<deb>-<L>X<W>`; predlažem da Hub preuzme taj oblik (jedan ključ za ploču).

### 1.3 RESTLOVI SKLADIŠTU V3.xlsx (06_SKLADISTE_I_RESTLOVI)
8 listova po vrsti (DRVNI DEKOR, UNI DEKOR, IV BIJELI, EGGER DEKORI, DEKORI RAZNI, AKRIL/PVC, LESONIT/ŠPER/SIROVI/OSB/GRUND, COMPACT).
Stupci: NAZIV DEKORA | DUZINA | SIRINA | KOL. | POZICIJA | NAPOMENA | M2 | UKUPNO (zbroj po dekoru u prvom retku dekora).
- **1.415 redaka restlova, 1.589 komada, ≈ 1.668 m²** (izvučeno u `20_ANALIZA\restlovi_v3.csv`, stupci list;dekor;L;W;kol;poz;nap;m2).
- Pozicije: `SATOR B/C x.y` (288 — regal "šator", polica), `A001…A010`, `B001…B010`, `C003…C007`, "NASLONJENO NA HALU", "NA PALETI KOD STAROG KOTLA";
  29 redaka bez pozicije.
- Napomene = stanje: "IZGREBANO PROVJERITI" (≈ 65 varijanti), "NESTING KOMAD" (28 — ostatak s nestinga, nepravilan), "VISE MJERA" (22 — komad
  nepravilna oblika, upisana samo najveća mjera, M2 = 0), "PROVJERITI PRIJE DEKOR", "18MM PAZI!!!!!" (debljina odstupa od liste).
- 388 redaka ima jednu mjeru < 400 mm (po PW pravilu to nije "korisni ostatak", ali se čuva); medijan 0,89 m².
- Nazivi dekora su slobodan tekst (`IV KASMIR BS 19MM (27049 BS)`, `IV CHAMPAGNE (27045 BS)`, `H1277 ST 9 18MM`, `U999 TM28-18MM`) — isti alias problem;
  ponegdje je šifra u zagradi, što je dovoljno za poluautomatsko mapiranje na Winstore/Pantheon kod.
- **Model `restl` (dopuna 04):** id, materijal_id (preko aliasa), L, W, kom, pozicija (regal/polica), stanje (OK / izgreban / provjeriti / nepravilan),
  izvor (pila / nesting / povrat), nalog_izvor, datum_ulaza, rezerviran_za_nalog, datum_izlaza. Uvoz V3 = jednokratna migracija (skripta),
  a "VISE MJERA" komadi dobivaju polje `nepravilan=1` i po potrebi skicu/fotografiju.

## 2. KROJNA.vb (PPNEST 1.2) — što je potvrđeno iz našeg koda
Datoteka: `03_NESTING_APLIKACIJA\source_code\KROJNA.vb` (45 KB, WinForms). Sve pretpostavke iz 02 potvrđene, plus:
- ListView ima 33 stupca (SubItems 0–32): 0 RB, 1 nalog, 4 "ELEMENT", 6 MJERA1 (= **duljina**, CIX LPX, CSV DUZINA, CPW L), 7 MJERA2 (= širina,
  LPY, CSV SIRINA, CPW W), 8 kom, 9 šifra materijala, 10 debljina, 11 materijal, 12 GOD, 17/19/21/23 trake lijevo/desno/gore/dolje (naziv),
  25 CIX id (= `ddMMyy_HHmmss` trenutka unosa elementa), 26 napomena (u CPW ide kao naziv elementa), 27 BROJPROLAZA, 28 GLODALO, 29–32 tip trake M/A.
- **GLODANJE** (CSV) = broj prolaza glodala: **2 ako je bilo koja mjera < 200 mm**, inače 1 (`VTR` u CIX-u). **GLODALO** = Ø12, a **Ø14 za deb > 20 mm**
  (`DIA`/`TNM`). Dubina `DP = deb + 0,15`. PROGRAM1/2, OBRADA, LJEPLJENJE, RUBx u CSV-u **uvijek prazni** (rezervirani stupci — nikad korišteni).
- CIX = pravokutna kontura: start (L/2, 0) → (L,0) → (L,W) → (0,W) → (0,0) → (L/2,0), ROUTG uz konturu (TIN/TOU 8 mm, 45°), sve u 1 datoteku po elementu.
- **Redoslijed rubova** u CPW koji PPNEST piše: `tipL;tipDolje;tipD;tipGore;trakaL;trakaDolje;trakaD;trakaGore` — u PPNEST ekranu lijevo/desno su duže
  stranice (MJERA1 okomito), pa to odgovara Igorovom "duža1, kraća1, duža2, kraća2". U CPO (PW) maska rubova PRT3 = `[dolje, desno, gore, lijevo]`
  (potvrđeno na 240 elemenata s djelomičnim kantiranjem).
- Izlaz: `C:\PPNESTING\<kupac>\NESTING\*.CSV + *.cix`, `…\PANEL WIZARD\*.CPW`, `…\<nalog>_<mat>_<stamp>.txt`. CSV/TXT UTF-8 bez BOM-a, CRLF.
- Sitnice: PPNEST u CPW ponavlja `FORMAT`/`MATERIJAL` ispred **svakog** elementa (bug u petlji; PW to tolerira); popis materijala je **hard-kodiran**
  u `CBMATERIJAL_SelectedIndexChanged` (u ovoj verziji izvora 4 materijala) — sve ostalo se upisuje ručno; "Zelena polja" validacija; nema šifrarnika.
  Datum izvora 3. 12. 2023. — pokrenuta verzija možda ima više materijala (nebitno za Hub: šifrarnik dolazi iz Huba, D-12).

## 3. CPO (Selco OSI) — format potpuno dekodiran, čitanje/pisanje bajt-po-bajt
`skripte\cpo_rw.py`: `parse()` + `write()` daju **identične bajtove za svih 50 PW datoteka**; `validate()` provjerava stablo rezova.
Pravila (potvrđena na 1.115 dijelova, 113 ploča, 1.839 rezova):
- Jedan `INV1/2/3` blok **po shemi** (n ploča ponovljeno n puta, qty = n), `ORD` blok po naručenom elementu, `PRT` blok po elementu
  (`PRT1` W, L, napomena, "Element N"; `PRT3` maska + 4 × (šifra 8 / naziv 20 / kratki 10 znakova, zadnji 6); `PRT4` nalog 16 zn.), `PAT` po ploči, `CUT1` po rezu.
- `CUT1,<razina>,<pozicija>,<1 = dio>,<rb dijela>`: **dio na razini n ima točno dimenzije (pozicija reza razine n-1, pozicija reza razine n)** — bez iznimke.
  Shema `L`: rez razine 1 paralelan s dužom stranicom (trake širine *pos* × 2780), `S`: okomit. PW koristi do 8 razina (tipično 2–4).
- `CTL1,M,M,Y|N` = materijal s godom: kod `Y` duljina dijela uvijek uz duljinu ploče (124 : 1). `CTL2` kerf 5,00 (varijabilan po nalogu — D odluka, Hub
  ga upisuje). `THK1` = debljina i visina paketa (5 × deb). Obrub 10 mm (0 kod radnih ploča 4100×600/640/900, 5 kod nekih). Cijene 49,000 / 5,995 konstante.
- PW u CPO zamjenjuje `,` i `/` u nazivima traka s `-` (`0,5/22 CHAMPAGNE` → `0-5-22 CHAMPAGNE`). `PAT2` iskorištenje uvijek 100,000 (ne koristiti).
- Kuriozitet: kad dio zauzima punu širinu radne ploče (900×2880 na 900×4100, trim 0) PW upiše rez razine 1 dvaput (`01,900` `01,900`) — nešto što
  OSI očito prihvaća; Hub to ne mora ponavljati, ali validator ga ne smije odbaciti.

## 4. Hub piše: PPNEST CSV/TXT/CIX, CPW, CPO — sve provjereno protiv stvarnih datoteka
| Što | Skripta | Provjera |
|---|---|---|
| PPNEST CSV | `nalog_io.write_ppnest_csv` | 8 CSV-ova testnih naloga regenerirano iz TXT-a — **identično** |
| PPNEST TXT | `nalog_io.write_ppnest_txt` | round-trip identičan |
| CIX | `nalog_io.cix_text` | 100926_080618.cix — identičan |
| CPW | `nalog_io.write_cpw` | MAZUR_3258_16 …CPW (PPNEST stil) — identičan; PPW stil (zaglavlje jednom) = kao datoteke iz 02_KLIJENTSKA |
| CPO | `cpo_rw.write` + `pila_optimizator.napravi_cpo` | 50/50 round-trip identično; Hub-ove sheme prolaze `validate()` |
| Slika sheme | `cpo_crtaj.py` | crta bilo koji CPO (PW ili Hub) u PNG — koristi se i za usporedbu PW shema |

### 4.1 Jednostavni optimizator pile (D-17 korak 2) — prvi rezultat
`pila_optimizator.py`: trake → blokovi → pod-trake → komadi (razine 1–4), god poštovan, kerf i obrub kao PW. Namjerno bez heuristika kvalitete.
Na 23 usporediva PPNEST izvoza (isti elementi kao PW): **Hub 72 ploče vs PW 73** — 19 izvoza isti broj ploča, BRATEK 18 mm (oba izvoza) Hub 6 vs PW 5 (lošije),
PVC KAŠMIR i PVC BIJELA "bolje" samo zato što je Hub računao na 2800×2070 umjesto 2800×1220 (dimenzija ploče mora doći iz šifrarnika — Winstore kod
to rješava), TURALIJA PVC isto. Zaključak: format i pravila su točni; kvaliteta slaganja (PW-like, D-16) je odvojen posao i ide kasnije.

## 5. Testne datoteke D-10 (`20_ANALIZA\test_D10\`, upute u `UPUTE_ZA_TEST.txt`)
Nalog BLAGO_3166_JASA (2 materijala) + HUMER JELA TAVERNA (za usporedbu s postojećim bNest rezultatom):
1. **bNest**: `01_za_bNest\NESTING\` CSV + CIX (uzorak imena kao PPNEST) → uvoz u bNest, očekujem 5 ploča za HUMER JELA TAVERNA.
2. **PanelWizard**: `02_za_PanelWizard\` CPW u dva oblika (zaglavlje jednom / ponovljeno) → uvoz, očekujem 1 + 1 ploču kao 28. 8.
3. **OSI**: `03_za_OSI\HUB_00901–903.cpo` → kopirati u `Z:\Krojne_liste`, otvoriti na pili, **simulacija F11**, ne rezati. Uz svaki CPO je PNG sheme.
Rezultat testova Igor upisuje na dno `UPUTE_ZA_TEST.txt`. Dok testovi ne prođu, ne pišemo kod modula `export` (D-10).

### 5.1 Rezultat testa 1 (bNest) — PROŠAO, 11. 9. 2026.
bNest je učitao sve elemente, simulacija prolazi. Operater nestinga je tražio da CIX ima postavke koje on inače ručno postavlja
u bSolidu (do sada je svaki PPNEST CIX popravljao rukom) i dostavio uzorak `04_STROJEVI\NESTING\korekcija\Korekcija.cix` (800×500×18).
Razlike prema PPNEST obliku: ORLST=5, kontura počinje u (0,W) i ide (0,0)→(L,0)→(L,W)→(0,W) (CRN=2), ROUTG kroz ploču
(THR=1, DP=0,1) alatom po imenu **TNM="8D"** (DIA=0), kompenzacija CRC=2, **VTR=2 (dva prolaza uvijek)**, ulaz/izlaz TIN/TOU 8 mm pod 45°,
DIN = mjesto ulaza glodala po konturi (u uzorku ≈ sredina donje stranice; Hub računa točno W + L/2), plus puni bSolid skup parametara
(CKA, OPT, PRP, SDS, SDSF…) koje Hub prepisuje nepromijenjene iz predloška `skripte\cix_bsolid_template.cix`.
`nalog_io.write_cix(stil='bsolid')` je sada zadano; `stil='ppnest'` ostaje za usporedbu. Predložak s DIN iz uzorka reproducira
Korekcija.cix bajt-po-bajt. Svih 53 CIX-a u test_D10 regenerirano.
**Pravilo alata (Igor, 11. 9.):** ulaz glodala uvijek na L/2 donje stranice; **do 19 mm glodalo "8D"**, **deblje (najviše 26 mm) glodalo "14"**,
u oba slučaja 2 prolaza, položaj i ulaz isti. Ugrađeno u `nalog_io.alat_za_debljinu()`; debljina > 26 mm = greška (nesting to ne reže).
**Imena CIX datoteka (operater, 11. 9.):** ime svakog CIX-a mora biti jedinstveno *zauvijek* — bNest ima jednu bazu programa i datoteku
s istim imenom **pregazi** (stari nalog bi dobio geometriju novog). PPNEST to rješava vremenskim žigom ddMMyy_HHmmss po elementu.
Za Hub: ime iz globalnog brojača u bazi Huba (npr. `H0001234`, nikad se ne ponavlja ni kod ponovnog izvoza istog naloga), a čitljivost daje
CSV (NAZIV ELEMENTA / NAPOMENA / RN); varijanta s prefiksom `NALOG_RB_H0001234` samo ako bNest nema ograničenje duljine imena — provjeriti.
`NALOG_RB` bez brojača se **ne koristi** (ponovni izvoz istog naloga pregazio bi stare programe).
→ TEST 1 zatvoren.

### 5.2 Rezultat testa 2 (PanelWizard) — PROŠAO, 11. 9. 2026.
PW je učitao sve CPW datoteke (obje varijante zaglavlja) bez greške. Hub će pisati varijantu sa zaglavljem jednom (PPW oblik).
Što CPW *ne nosi*, pa operater i dalje postavlja u PW-u: god (CTL1 Y/N), dimenziju ploče (2800×2070 / 2800×1220 / radne ploče), kerf i obrub —
Hub to zna iz šifrarnika, ali PW-u ne može poslati; za paralelni rad (D-11) to je prihvatljivo, jer PW ostaje samo kalkulator količina (D-18).
Dijakritici: **PW ne prikazuje Š/Ć/Č** (Igor, 11. 9.) → Hub u CPW i CPO piše nazive bez dijakritika (Š→S, Č/Ć→C, Ž→Z, Đ→D;
`nalog_io.bez_dijakritika`), a puni naziv ostaje u Hubu/CSV-u za nesting. Ostaje kontrola da količine za naplatu iz Hub-CPW-a budu iste kao iz PPNEST-CPW-a (isti elementi → mora biti).

**Površine za naplatu iste** (BLAGO_JASA, Hub-CPW vs PPNEST-CPW) — ali Igorova napomena (11. 9.): površinu za naplatu određuju **postavke
PW optimizacije** (uzdužno / poprečno rezanje ploče, kerf, obrub, pravilo ostatka…), ne samo elementi. To znači: (1) PW postavke su *skriveni ulaz
obračuna* — u 50 CPO datoteka 31 je samo s uzdužnim (L), 16 samo s poprečnim (S), 3 miješano, dakle smjer se očito bira po nalogu/materijalu;
(2) Hubov kalkulator količina (D-17 korak 1, metoda PW po D-18) mora te postavke imati kao **izričite parametre naloga** (smjer prvog reza, kerf,
obrub, dimenzija ploče, kriterij korisnog ostatka) sa zadanim vrijednostima kakve PW koristi danas; (3) usporedba PW ↔ Hub u paralelnom radu (D-11)
vrijedi samo uz iste postavke. Postavke nisu u datotekama u 01_PANELWIZARD (`pnl.ini` je binarni zapis zadnjeg naloga, ne postavke) — treba
**screenshot PW dijaloga postavki optimizacije** i odgovor bira li operater smjer rezanja po nalogu ili je fiksan.

### 5.3 Postavke PanelWizarda — pregledano uživo na Ivaninom računalu (AnyDesk, 11. 9. 2026., uz Igorovo odobrenje)
Verzija 920.26.P Profesional (autor Ivica Ergović). Ništa nije mijenjano; pokrenute su 3 optimizacije na otvorenom nalogu HUMER_MARTINA_3386
(I_02201), zadnja u istom načinu koji je Ivana imala, pa je rezultat vraćen na isto (PW automatski sprema svako optimiranje s vremenskom oznakom).

**Načini optimizacije = desni klik na žarulju (po nalogu/materijalu bira operater):** Trake brzo / Trake standardno / **Uzdužno brzo /
Uzdužno standardno / Poprečno brzo / Poprečno standardno** / Uzdužno na veliko / Poprečno na veliko. Nema zadanog — operater klikne što želi.
Isti nalog (SILK 27068 MN 19 mm, 3 ploče): **Uzdužno standardno → naplata 13,26 m², rez 17,8 m, ostatak 2800×1474**;
**Poprečno standardno → naplata 12,66 m², rez 18,2 m, ostatak 2800×1688**. Razlika 0,6 m² (4,5 %) na istom nalogu — potvrda da je smjer rezanja
parametar obračuna. Formula naplate potvrđena na ekranu: *Površina za naplatu = Σ ploča − Σ korisnih ostataka* (17,39 − 4,73 = 12,66).

**Globalne postavke (Opcije → Konfiguracija):**
- Generalno: korisni ostatak = dužina **i** širina ≥ 400 mm **i** površina ≥ 1 m²; klizač "kriterij za ostatke isti kao za cijele panele ↔ prednost
  korištenju ostataka" na sredini; "Ignoriraj 0 mm trimanje panela" uključeno.
- Opcije pile: "Ispis pojedinačnih rezova za SCM, Giben i CPOUT" ✓ (to je CUT1 popis u CPO-u); "Ograniči broj okretanja ploče = 0 (bez ograničenja)";
  "Povuci zadnji rez na točnoj mjeri" ✓; "Kod generiranja za pilu spremi .pnl u Naloge" ✗; minimalni ostatak za trimanje 100 mm; SCM AltPacco 85,
  VelRotaz 3000, VelAvanz 32; "Ime pxt naloga 6 znamenki" ✓; filter naloga 10 znakova.
- Kantiranje: "Izračunaj cijenu kantiranja" ✓; "Naljepnica: Kant – duga uz dugu, kraća uz kraću" (redoslijed rubova potvrđen); naziv kanta kod
  importa Mel = "melamin", ABS = "ABS" (isključeno).
- Novi posao: bez potvrde prije automatskog spremanja; "Dodatno spremi nalog pod imenom kupca" ✓; "Spremi s vremenskom oznakom – spremi sva
  optimiranja" ✓ (→ više .pnl verzija istog naloga); "Zabrana tiskanja ako nije zadan RN, kupac ili materijal" ✓; "Provjeri god prije optimiranja" ✓
  (upozorenje "Godovi elemenata i panela se razlikuju" iskače kod svakog optimiranja ovog naloga).
- Statistika (ispis): lista elemenata ✓, dužina kantiranja po materijalima ✓, barcode ✓, skica uz statistiku ✓; cijena kantiranja/materijala ✗.
- Postavke: "Automatski numeriraj RN" ✓. Okolina: mm, jezik hrvatski, "Pokaži status optimiranja" ✓, Opcije pile → "Head cut" ✗.

**Po nalogu:** Posao → Podesi alat: **"Max. debljina lista pile – Debljina reza 16 mm"** (globalno; CPO ipak nosi 5,00 → export za pilu ima svoj kerf).
Posao → Zadaj panel: ploča 2800×2070, kom 0 (= neograničeno), **rub 10 mm**, "Ostatak" ✗, materijal + god + debljina se upisuju ručno,
"Vrsta optimiranja: materijal zadan u poljima" (ne iz baze), "Optimiraj zadnji panel na ostacima" ✗. Nacrt nudi **"Uredi rezove"** (ručno
uređivanje sheme) i "Prihvati rješenje – uzmi iz baze".
**Export:** Opcije → Folderi → "Generiranje naloga za pilu" = **`S:\Krojne_liste`** (na Ivaninom PC-u server je S:, kod Igora Z: — ista mapa).

**Pravilo izbora načina (Igor, 11. 9. → D-19):** materijal **s godom** → samo uzdužni načini (Trake brzo, Trake standardno, Uzdužno brzo/standardno,
Uzdužno na veliko); materijal **bez goda** (npr. bijela iverica za korpuse) → uz njih i Poprečno brzo / standardno / na veliko. **Valjan je rezultat
s najmanjom površinom za naplatu.** Za Hub to znači da izbor nije ručan: kalkulator pokrene sve dopuštene načine, uzme minimum m² i zapiše pobjednika.
Parametri obračuna uz to: kerf 16, rub 10, ploča, god, kriterij ostatka 400/400/1 m².

### 5.4 Rezultat testa 3 (OSI, simulacija F11) — PROŠAO, 11. 9. 2026.
OSI je učitao `HUB_00903.cpo` (HUMER IV JELA TAVERNA, 6 ploča, Hubov optimizator), simulacija prolazi, sheme na pili identične `HUB_00903.png`.
→ Sva tri testa D-10 prošla: Hub piše CSV+CIX (bNest), CPW (PanelWizard) i CPO (OSI) koje strojevi/programi prihvaćaju bez izmjena.
Preduvjet za kod modula `export` (D-10) je ispunjen; za početak koda Huba ostaje još D-09 (3 naloga "na papiru") i Igorovo odobrenje audita (D-01).

### 5.5 Kalkulator količina PW-metodom (D-17 korak 1) — napravljen i provjeren, 11. 9. 2026.
`skripte\obracun.py`. Pravila izvedena iz PW PDF-ova + CPO-a + ekrana (§5.3) i **potvrđena brojkama**:
- **Korisni ostatak** = jedna traka po ploči, okomita na trake razine 1: `ostatak = dim − 10 − Σ(širine traka) − 16·n_traka`, zadržava daleki obrub
  i puni nominalni drugi dim (PDF "Ostatak 2800 × 1016"); vrijedi samo ako obje mjere ≥ 400 i površina ≥ 1 m². **Kerf u obračunu je 16** (CPO nosi 5).
- **Površina za naplatu** = n·2,8·2,07 − Σ ostataka → I_01970 4,36, I_01971 2,95, I_01913 57,96, I_01915 30,16 (sva 4 PDF-a točno);
  protiv Pantheon ponuda svih 9 naloga: **23/40 stavki identično**, 14 stavki +0,23…0,25 (pravilo načete ploče iz skilla), 3 negativne (−0,03…−0,10:
  jobovi koje je PW optimirao s kerfom 5/10 — I_02021, I_02022, I_02090), ostalo ručne korekcije (+0,36…+1,88).
- **Metri trake** (PW "Kantiranje sortirano po dekorima") = Σ stranica × kom × **1,10** — omjer točno 1,1000 na sva 4 PDF-a; iz CPO PRT3 identično.
  Posljedica: skill `krojna-ponuda` množi PW metre s još 1,10 (dvostruko) — ponude to ne rade dosljedno (vidi 06, prijedlog D-20).
- Uočeno: PW-ovi rasporedi kod ~15 % jobova stanu samo ako se računa **jedan** obrub (zadnja traka smije "u daleki obrub") — Hub zasad računa
  oba obruba (konzervativno, može dati ploču više); 3 joba (BOGDANIC 16 mm, dva MDF 3 mm) optimirana su s kerfom 5/10, ne 16 → "Podesi alat" se mijenja po nalogu.

### 5.6 Vlastiti optimizator — načini + D-19 + benchmark
`pila_optimizator.py`: načini `uzduzno` (shema L), `poprecno` (S), `trake` (u traci samo ista širina), svaki u 4 varijante slaganja
(3 redoslijeda + "pametne trake": širina trake = kombinacija do 3 širine komada, kao PW kod EGGER H1180: 376+16+376); bez goda i obrnuta orijentacija.
`najbolje()` = D-19 (min m² naplate, pa ploče, pa rezovi). `benchmark_optimizator.py` na 42 materijala (50 CPO-a bez RP/ZO): **PW 429,16 m² / 102 ploče,
Hub 446,25 m² / 104 ploče (+4,0 %)**, 14 identično, 5 Hub manje, 23 Hub više; najveće razlike HUMER MDF 3 mm +2,4 m², BRATEK 18 mm +2,0 (6 vs 5 ploča),
MAZUR MDF +1,9, BLAGO 18 mm +1,7, HUMER 18 mm +1,0 (11 vs 10 ploča). Rezultati u `benchmark_optimizator.csv`. Ovo je "jednostavni" optimizator
(D-17 korak 2, dovoljan za pilu); PW-kvaliteta (D-16) = sljedeći korak, mjeri se istim benchmarkom.

### 5.7 D-09 — tri naloga na papiru
Napravljeno: `06_D09_tri_naloga_na_papiru_2026-09-11.md` (generira `skripte\d09_tri_naloga.py` + ručni zaključak). Lanac prolazi za HUMER, BRATEK i ROMIC;
ploče se slažu s ponudama (uz +0,25 / min 1/3 pravila), trake pokazuju da ponude nemaju jedno pravilo zaokruživanja → prijedlog D-20.

### 5.8 Igorovi odgovori 11. 9. (večer) → DECISIONS D-20 … D-28
Trake = PW metri naviše na metar (D-20); jedan kerf po nalogu, zadano 16, CPO nosi 5,00, ista shema na pilu (D-21); programi `HUB_xxxxx` (D-22);
CIX imena `H0001234` (D-23); djelatnici rade s Pantheon identom, Hub u pozadini upisuje Winstore MaterialCode u SIFRA MAT — **potvrđeno: PPNEST
SIFRA MAT = Winstore MaterialCode** (9/12 šifri iz testnih naloga postoji u Winstore XML-u; `XXX` = MDF 3 mm koji ne ide u Winstore; `K5574IR_19`
i `K2739DC-19` su tipfeleri/nepostojeći) (D-24); etikete na pili ostaju u OSI-ju (D-25); optimizator dovoljan za fazu 1 (D-26); GitHub organizacija
tvrtke + VM 192.168.5.201 (D-27); **audit odobren, faza 1 zatvorena** (D-28). Winstore XML = ručni izvoz operatera.

## 6. Otvoreno nakon ovoga
- Winstore: postoji li uvoz/API (rezervacija, ulaz robe), ili Hub samo čita dnevni XML? Gdje je XML izvezen (ručno iz Winstorea?) — treba automatski izvoz.
- Brojač programa za pilu (nastaviti I_/SA_ nizove ili HUB_?), i tko "šalje" na pilu u Hubu (voditelj ili administrator).
- Etiketa na pili (još neodgovoreno iz 04).
- Dimenzije ploča po materijalu (2800×2070 / 2800×1220 / 2800×1300 / 4100×600…) — u šifrarnik `hub_ploce.csv` dodati stupac iz Winstore koda.
- Skill `krojna-ponuda/optimizator.py` (kerf 4,4, shelf heuristika) ostaje samo za brzu ponudu; za pilu se koristi `pila_optimizator.py` s pravim stablom rezova.
