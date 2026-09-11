# Paneli Production Hub — audit 2/4: formati datoteka, strojevi i softver

Stanje 10. 9. 2026. (popodne). Izvor: mape 01–08 u `Paneli_Production_Hub\` i 9 testnih naloga u `05_NALOZI_ZA_TEST\`.
Parseri za sve formate ispod su u `20_ANALIZA\skripte\parseri.py` i provjereni na svim datotekama iz testnih naloga.

## 1. Strojevi i softver (iz PROIZVODJAC_MODEL.txt i snimki ekrana)

| | Pila (raskrajač) | Nesting (CNC) |
|---|---|---|
| Stroj | **Biesse Selco Sektor 450** (2012) | **Biesse Rover B 2231** (2023) |
| Softver na stroju | **OSI 1.20.04.00** (Biesse OSI, hrvatska lokalizacija) | **B_SOLID 4.0.0.262** + **bNest** |
| Što učitava | `.cpo` datoteke (jedna po materijalu/nalogu), stablo Narudžbe → kupac → program | `CSV` popis elemenata + jedan `.cix` po elementu |
| Tko generira ulaz | PanelWizard (PW920.26, instalacija u `01_PANELWIZARD\installed_directory`) | **PPNEST 1.2** (vlastita aplikacija, .NET 6 / VB.NET WinForms, prosinac 2023) |
| Etikete | PW šalje podatke, printa printer na raskrajaču | bSolid Labels: predložak `LBL_PP1` 102×64 mm, Zebra **ZDesigner ZT411 203 dpi ZPL**, IP 10.100.100.70 |
| Prefiksi programa | `I_0xxxx` i `SA_0xxxxx` (dva računala/operatera), `TP4_` | naziv projekta = `KUPAC_BROJ_..._ŠIFRA-DEB` |

Ploča: standard **2800 × 2070 mm**, obrez 10 mm sa svih strana (radna 2780 × 2050), kerf pile 5,0 mm (CTL2), visina paketa 80–95 mm (THK1 = 5 ploča).
PanelWizard u PDF-u ispisuje "Debljina reza: 16 mm" — sumnjivo, provjeriti postavku (u CPO ide 5,00).

## 2. Tok datoteka (kako je danas)

```
kupac ──(PPW 5.2 → .CPW)──┐
kupac ──(Excel / rukopis / PDF)──┤ ručni unos
                                 ▼
                    ┌── PanelWizard (PW920) ──► .cpo → pila (OSI)     + krojna PDF + .pnl (spremljeno)
   PPNEST 1.2 ──────┤          ▲
   (unos naloga)    │          └── .CPW (PPNEST ga sam izvozi u "PANEL WIZARD\")
                    └── CSV + .cix (mapa "NESTING\") ──► bNest ──► .mno (rezultat) + .bSolid (po ploči) + _lbl.xml (etikete) + .xml (izvještaj)
                                 │
                    Pantheon ponuda (ručno iz krojne PDF / skill krojna-ponuda) ──► PDF
```

Ključni nalaz: **PPNEST je već "standardni nalog"** — iz jednog unosa proizvodi i CSV/CIX za nesting i CPW za PanelWizard, a njegov TXT je jedini
zapis koji sadrži sve podatke elementa (materijal, šifra ploče, 4 ruba, CIX, glodanje). PanelWizard je u tom lancu samo optimizator pile i generator CPO/etiketa.
Svi nalozi u testnoj mapi idu i na pilu i na nesting (POPIS_NALOGA: o podjeli odlučuje voditelj proizvodnje; želja je da to radi administrator pri otvaranju naloga).

## 3. Formati — specifikacija

### 3.1 CPW (klijentska aplikacija PPW 5.2 → PanelWizard; PPNEST → PanelWizard)
Tekst, `;` separator, cp1250, jedan element = 3 retka, blok se ponavlja za svaki element:
```
FORMAT;CORPUS->PW;002600;
MATERIJAL;<naziv materijala>;<debljina>;
ELEMENT;<naziv/oznaka>;<duljina>;<širina>;<kom>;<r1>;<r2>;<r3>;<r4>;<traka1>;<traka2>;<traka3>;<traka4>;
```
`r1–r4`: `A` = ABS, `M` = melamin (tanka traka), prazno = bez ruba. `traka1–4`: naziv trake (`ABS-ISTI`, `MEL-ISTI`, `taverna`, `1/22 VSM06 KASMIR`…).
Naziv elementa kupci koriste i za "gotovu mjeru" (`777x135` uz element 777×140 = element se reže veći, PW to ispisuje uz dio).
Redoslijed r1–r4 u CPW-u = redoslijed RUB1–RUB4 u PPNEST CSV-u (provjereno na MAZUR 18 mm: `A;M;;M` ↔ `KASMIR;MEL-ISTI;;MEL-ISTI`); u CSV-u su stupci `RUBx` prazni, a naziv trake je u `TRxSIFRA`. **Otvoreno:** koja je strana 1–4 (duža1/kraća1/duža2/kraća2 ili L/D/G/D) — potvrditi s Igorom.
Materijal u CPW-u je slobodan tekst (`IV BIJELI NK 18MM`, `IV_BIJELI_NK_18_MM`) — nema šifre; mapiranje na Pantheon ident radi čovjek.

### 3.2 CPO (PanelWizard → Biesse OSI, pila)
Tekstualni Selco format, zapisi po 4-slovnom tagu, cp1250. Sadrži **cijeli nalog za pilu I optimirane sheme**:
```
HDR1,<br. programa>,<materijal>          HDR2,<datum>,<vrijeme>      HDR3,...
CTL1..3   parametri (CTL2: kerf 5.00, 5.00 ...)
THK1,<debljina>,<visina paketa>
INV1,999,<kom>,<cijena>,<W 2070>,<L 2800>,<obrez ×4>   INV2,<naziv materijala>   INV3
ORD1,<kom>,<kom>,<W>,<L>,<god H/V>,<Y>   ORD2,<cijena>,<oznaka gotove mjere>   ORD3,1,<rb>      (po elementu)
PRT1,<kom>,<n>,<W>,<L>,1,...,"Element n"  PRT2  PRT3,<maska 1111>,<rub1 kod,naziv,kratki> ×4   PRT4,<kupac>  PRT5
PAT1,<br. sheme>,L,<kom ploča>,1   PAT2..PAT5                                                     (po shemi/ploči)
BCUT  CUT1,<razina 1–5>,<pozicija mm>,<1 = dobiven dio>,<rb dijela>  ...  END
```
Iz CPO-a se bez PanelWizarda dobiva: broj ploča, sve dimenzije, rubovi po strani, kupac, **sheme rezanja i redoslijed rezova** (→ dm rezanja, broj rezova),
iskorištenje. To je format koji Hub mora **pisati** za pilu (i najbolji dostupni "ground truth" za benchmark optimizatora).

### 3.3 PPNEST — TXT (interni zapis), CSV (→ bNest), CIX (→ bNest/Rover)
CSV, `;`, UTF-8 BOM, zaglavlje s 28 stupaca:
`RB;RN;NAZIV ELEMENTA;BROJ ELE;IME DASKE;KONACNA DIMENZIJA;SIRINA;DUZINA;KOLICINA;SIFRA MAT;MAT DEB;MAT NAZIV;GOD;PROGRAM1;PROGRAM2;OBRADA;RUB1;TR1SIFRA;RUB2;TRS2IFRA;RUB3;TR3SIFRA;RUB4;TR4SIFRA;LJEPLJENJE;CIX;NAPOMENA;GLODANJE`
— `SIFRA MAT` = šifra ploče proizvođača (`W908ST2-18`, `K2665AI-19`, ili Pantheon ident `IV000160-18`), `IME DASKE` = `<rb>_ELEMENT`, `CIX` = ime CIX datoteke (`ddmmyy_hhmmss`),
`GLODANJE` 1/2 (broj prolaza?). U bNest se mapira na Description 1–24 (etikete: Description2 = kupac, 5 = šifra, 21 = napomena, 22 = kom, 23 = materijal).
TXT = isti podaci, "ključ u jednom retku, vrijednost u sljedećem", blok `ELEMENT` po elementu (+ `ELEMENTSVI` redni broj).
CIX = Biesse CIX v5 (`BEGIN MAINDATA LPX/LPY/LPZ … MACRO GEO/START_POINT/LINE_EP/ROUTG`): pravokutna kontura + glodanje glodalom Ø12 do dubine LPZ+0,15 — **PPNEST ga generira sam**, po jedan CIX po elementu (istog sadržaja osim dimenzija).
→ Hub mora pisati CSV + CIX u ovom obliku; ništa drugo bNestu ne treba (potvrđeno snimkom "CSV UCITANI").

### 3.4 bNest izlaz — MNO, bSolid, _lbl.xml, XML
- `.mno` = **XML** (`NESTING_RESULT` → `FOGLIO` po ploči: `NAME="K2665AI-19-2800X2070.xml"`, `StatisticInfo PartUsedArea`, `Production/POS` pozicije dijelova, `LABEL`).
  Iz njega se čita broj ploča, iskorištenje po ploči i točan položaj svakog dijela — **izvor istine za nesting rezultat i za restlove s nestinga**.
- `.bSolid` = ZIP (program po ploči za Rover) — Hub ga ne dira.
- `_lbl.xml` = `<CutList><Part id L W qMin Material MatEdgeUp/Lo/L/R Description11..24/>` — sadržaj etiketa, dobar za Hubove etikete.
- `.xml` = kopija projekta/parametara nestinga (Clearance 0.08, NestDirection X, …) — informativno.

### 3.5 PanelWizard — PNL, pnl.ini, krojna PDF, baza materijala
- `.pnl` (spremljeni nalog) i `pnl.ini` (radni podaci, 411 kB) su **binarni VB6 zapisi fiksne širine** (30-znakovna polja). Čitljivi su stringovi (kupac, datum, materijal, rubovi, imena elemenata, `.CIX` reference), ali format nije za oslanjanje — **ne parsirati**, koristiti CPW/CPO/PDF.
- Krojna PDF (Microsoft Print to PDF): po listu raspored + "Iskorištenje %" (bez korisnog ostatka!), na kraju **Statistika**: popis elemenata s oznakama kantiranja (2DA 2KA…), "Površina svih ploča", **"Površina za naplatu"** (kriterij korisnog ostatka: obje mjere > 400 mm i > 1 m²), "Broj potrošenih ploča", "Ukupno iskorištenje", **kantiranje po dekoru u metrima**. Skill `krojna-ponuda` ovo već čita.
- `MaterijalPW900.mdb` (Access): 3 materijala, 4 ploče — **prazna, ne koristi se** (potvrđuje Igorovu napomenu); materijal se upisuje kao tekst po nalogu.
- `kantovi.txt`: šifrarnik traka PW-a — 6 zapisa (`ABS-ISTI 200`, `ABS-1 1227`, `mel-ISTI 100`, `OBRADA-RUBA`…) = **nema prave baze traka**.
- `PWExcel_03_konfig.xls`: predložak uvoza krojne iz Excela (stupci A–P, zaglavlje redovi 2–5) — kupci ga (uglavnom) ne koriste; Excel narudžbe su proizvoljne (BRATEK: 26 stupaca, vlastiti predložak s NARUDŽBA + OKOV listom).
- `KrojneListe\AutoSave` (432 .pnl) i `pwlg` (775 dnevnih .pwa logova od 8/2020) — arhiva, nije za migraciju.

### 3.6 Pantheon ponuda (PDF)
Obrazac A0F: `Rb | Ident | Naziv | Količina | MJ | Cijena | R.% | PDV% | Vrijednost`; identi IV/RP (materijal, m² ili m), US (usluge), TR (trake), OK (okov).
Stavke su u paru materijal + USLUGA REZANJA (ista količina m²), traka + USLUGA KANTIRANJA (m). `pdftotext -layout` izgubi stavke koje preklapaju zaglavlje
(BLAGO ADRIJANA: rb 1–2 nedostaju i u PDF-u — vidi audit 3).

## 4. Ulazi kupaca (01_ulaz_kupca) — što Hub mora primiti
- CPW iz PPW 5.2 (HUMER) — strojno; PPW ne zna trake po šifri, samo tekst.
- Excel vlastitog formata (BRATEK: materijal, deb, 1. mjera (smjer goda), 2. mjera, kom, kantiranje 1./2. mjera, napomena ABS 1/2 mm, + list OKOV).
- Fotografija rukopisa (BLAGO JASA, BOGDANIC, MAZUR, VARGA) — tablica po materijalu, `ABS 1mm 4x / 2D`, popis okova ispod.
- Skenirani PDF rukopisa (ROMIC, TURALIJA) — isti stil, po materijalu kvadranti, "0,8 ISTI", podcrtane mjere = kantirano.
- Skica/nacrt PDF + Excel okova (HUMER: radne ploče, fronte, OKOV (48).xlsx s 130 stavki šifrarnika okova kupca).
