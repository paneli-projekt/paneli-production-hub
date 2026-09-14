# 11 — Šifrarnik materijala i traka (kralježnica, korak 1) — 12. 9. 2026.

Korak 1 plana iz 04 §4: **šifrarnik materijala i traka s aliasima** (Pantheon ident ↔ Winstore MaterialCode ↔ tekst iz PW / PPNEST / naloga),
baza Huba i prvi API. Kriterij prihvaćanja iz 04: *svih 50 CPO materijala i ponudbeni identi iz testnih naloga mapirani bez ručnog rada.*
**Rezultat: 47 / 50 sigurno (3 preostala su zidne obloge koje u Pantheonu nemaju ident), 40 / 40 točno prema identu u ponudi, CPW 37 / 37,
PPNEST CSV 30 / 31 (31. je tipfeler operatera — ispravno „za potvrdu“), trake 42 / 48 (6 „za potvrdu“ su stvarne rupe u šifrarniku traka).**

Kod: `30_NOVI_PROGRAM\hub\schema.sql`, `hub\db.py`, `hub\sifrarnici\*.py`, `hub\api\app.py`, testovi `tests\test_sifrarnik.py`, `tests\test_api.py`
(46 testova + 2 na stvarnim podacima). Ovaj dokument: što je napravljeno, kako radi, što je provjera pokazala i **što treba Igor** (§5).

## 1. Što je napravljeno

| Dio | Datoteka | Sadržaj |
|---|---|---|
| Baza | `hub/schema.sql`, `hub/db.py` | SQLite (jedna datoteka `hub.db`), shema v1 po 04 §2 + 10 §4: `pantheon_ident` (kopija identa s cijenama), `kupac`, `materijal`, `materijal_alias`, `winstore_ploca`, `traka`, `traka_alias`, `materijal_traka` (zadane trake, D-31), `nalog`, `ponuda_verzija`, `nalog_materijal`, `element`, `okov_stavka`, `obracun_stavka`, `optimizacija`, `dokument`, `dogadjaj`, `ploca_stanje`, `restl`, `rezervacija`, `narudzbenica(_st)`, `operacija`, `dnevnik`, `postavke`, `korisnik`. Shema se primjenjuje sama pri prvom otvaranju. |
| Uvoz Pantheona | `hub/sifrarnici/pantheon.py` | `ph_identi.csv` (12 643 identa, NUL bajtovi očišćeni) → 1 609 materijala (identi `IV*` i `RP*`) i 1 388 traka (`TR*` + četiri „ABS …“ pod `OK`/`US`; tri ploče otvorene pod `TR` isključene). Iz naziva se izvode vrsta (IV / MDF / PVC / AK / HPL / CP / SP / RP / ZO), debljina, riječi dekora, kod dekora (W908 ST2, K2665 AI, 27045 OF, VSM-06…), za RP obitelj radna / stola / zidna sa širinom 600 / 900 / 640 (D-37). Idempotentno: ponovni uvoz osvježava nazive, cijene i aktivnost, ne dira aliase i veze. |
| Uvoz Winstorea | `hub/sifrarnici/winstore.py` | Winstore XML (ručni izvoz operatera) → `winstore_ploca` (592 stavki, 523 MaterialCode) + povezivanje koda s materijalom (D-24): (1) kod već zapamćen, (2) kod je Pantheon ident (`IV000065-19`, `IV000160A-18` — operater tako piše dio kodova), (3) prepoznavanje po opisu. Materijal pamti prvi kod, ostale kodove istog materijala (varijante A/B/C, druga dimenzija) veže na razini ploče. |
| Normalizacija | `hub/sifrarnici/nazivi.py` | Čiste funkcije: `norm` (velika slova, bez dijakritike, `_` → razmak, IJE = JE), sinonimi i tipfeleri koji se ponavljaju (HR = HRAST, BIJELA = BIJELI, CASHMIR = KAŠMIR, CHAMPANGE = CHAMPAGNE, HALIFAKS = HALIFAX, LIGHT = SVIJETLI…), kodovi dekora u svim zapisima (`W908 ST2` = `W908ST2`), debljina iz naziva, oznake traka (`ABS-ISTI`, `MEL-ISTI`, `1/22 ISTI`, `MEL CRNA NK`, `MET 0.5/22 BIJELI NK`…). |
| Prepoznavanje | `hub/sifrarnici/prepoznaj.py` | Tekst iz naloga → ident, deterministički (bez LLM-a, D-15), redoslijed: **alias** (točan normalizirani tekst) → **Winstore kod** (SIFRA MAT iz CSV-a) → **naziv** (vrsta + debljina + riječi dekora + kod dekora, bodovanje). Jedinstven i potpun pogodak = *sigurno*; više kandidata, promašena riječ ili drugi kod dekora = *za potvrdu* s popisom kandidata; ništa = *nema*. Trake: alias uz materijal → zadana traka materijala za tu klasu (D-31) → po nazivu (dekor materijala za ISTI, inače dekor iz oznake); klasa (0,5/22, 1/22, 2/22, 1/44) daje uslugu kantiranja (D-20). Potvrda čovjeka upisuje alias — idući put bez pitanja (D-32). |
| Aliasi i zadane trake | `hub/sifrarnici/aliasi.py` | 369 parova iz skilla krojna-ponuda (kopija u `hub/sifrarnici/podaci/alias_krojna_ponuda.csv`), parovi potvrđeni u ponudama testnih naloga (06 §5), zadane trake iz ponude 2823 (JELA TAVERNA → JELA CLAY, RELIEF CARDAMOM → RELIEF PIMENTO, BIJELI NK → 0,5/22, 1/22, 2/22), te **automatski izvedene zadane trake** po nazivu (1 054 parova za 606 od 959 aktivnih ploča) — strogo: traka mora imati iste riječi dekora i ne smije imati riječ viška (MASLINA ≠ MASLINA SJAJ) osim ako se kod dekora poklapa. |
| Naredbe | `hub/sifrarnici/uvoz.py`, `provjera.py` | Dnevni uvoz (≈ 5 s) i provjera na testnim nalozima s Markdown izvještajem (prilog §6). |
| API | `hub/api/app.py` | FastAPI kostur: `/api/zdravlje`, pretraga `/api/sifrarnik/materijali?q=`, `/materijali/{ident}` (aliasi, zadane trake, Winstore stanje), `/trake?q=&klasa=`, `/prepoznaj?naziv=&debljina=&kod=`, `/prepoznaj-traku?oznaka=&materijal=`, `POST /alias`, `POST /alias-traka`. Dokumentacija i isprobavanje na `/docs`. |

## 2. Kako to izgleda korisniku (ekran 2 iz mockupa)

Pri uvozu CPW-a / CSV-a / Excela ili pri tipkanju naziva, Hub uz svaki materijal i rub pokaže **ident i naziv iz Pantheona** ili oznaku
**„za potvrdu“** s 2–3 kandidata. Ono što Ivana ili Goran jednom potvrde ulazi u alias-tablicu i više se ne pita — ni za taj tekst ni za
istu oznaku trake uz isti materijal. Sigurne razine: *alias* (tekst već viđen), *Winstore* (kod iz nesting CSV-a), *zadana* (traka
materijala za tu klasu), *naziv* (jedinstven pogodak). Na ekranu se razine ne prikazuju kao kod — samo ident/naziv ili „za potvrdu“.

## 3. Što je provjera pokazala (stvarni testni nalozi, 9 kupaca)

| Skup | Ukupno | Sigurno | Po razini | Napomena |
|---|---|---|---|---|
| CPO materijali (PW, pila) | 50 | **47** | naziv 43, alias 4, nema 3 | 3 „nema“ = `ZO HR EVOKE SUNSET` (2×), `ZO HR CREMONA CANNOLO` — zidne obloge bez identa u Pantheonu (§5.1) |
| CPO vs ident u ponudi (`benchmark_nalozi.csv`) | 40 | **40** | — | ni jedan krivi ident |
| CPW materijali (Corpus / PW) | 37 | **37** | naziv 33, alias 4 | |
| PPNEST CSV (SIFRA MAT) | 31 | **30** | Winstore 23, naziv 4, alias 3, za potvrdu 1 | `K2739DC-19` ne postoji (ispravno `K2739OC-19`) — tipfeler operatera koji danas prolazi bez kontrole (D-24), Hub ga hvata |
| Trake iz CPW oznaka | 48 | **42** | zadana 26, naziv 14, alias 2, za potvrdu 6 | §5.3: nema trake CRNA NK u širini 22 (samo /29 i /44), nema CHAMPAGNE UM (samo GOD, SATIN SU i OM/OF), PVC CRNI MAT VSM-02 bez „svoje“ trake |
| Winstore kodovi | 523 | **424** | ident 19, naziv 405 | 99 nepovezano: 17 ambalaža, 70 s stanjem 0 (stari kodovi), 12 stvarnih (§5.2) |

Ono što je alias-tablica iz skilla krojna-ponuda znala (369 parova) sad zna i Hub; uz to su prepoznavanjem po nazivu pokriveni i nazivi
koje skill nije imao (43 od 50 CPO naziva riješeno bez aliasa). Brzina: prepoznavanje < 1 ms po nazivu, uvoz cijelog šifrarnika ≈ 5 s.

## 4. Pravila koja su se pokazala nužnima (ugrađena, vrijede dalje)

1. **Kod dekora je jači od riječi**: `IV EGGER H1180 ST37` = `IVERAL H1180 HRAST HALIFAX 18MM` (kod isti, riječi različite); `IV SIVI TAMNI 2162 MN` ≠ `… 2162 PE` (isti kod, drugi sufiks → za potvrdu); `IVERAL W960 ST7` ≠ `IVERAL U999 ST7` (oba imaju kod, a različit je → za potvrdu).
2. **Dvoslovni sufiksi (PE, MN, AE, UM, OF) nisu riječi dekora**: `IV_CHAMPAGNE_UM` pogađa `IVERAL CHAMPAGNE 27045 UM`, a `MDF CHAMPAGNE UM` uz postojeći samo `27045 OF` ide na potvrdu.
3. **Debljina iz datoteke** (CPO THK, CPW MATERIJAL, CSV MAT DEB) nadomješta debljinu koje u nazivu nema (`IV_HR_EVOKE_SUNSET_1` — PPNEST reže na 20 znakova).
4. **Širina ploče odlučuje obitelj radne ploče** (D-37): 600 radna, 900 stola, 640 zidna — `RP BASANIT SAND` iz CPO-a 4100×900 → `PLOČA STOLA BASANIT SAND K2875CN`.
5. **Winstore opis bez vrste** (`HAMILTON HRAST NATUR`) uz ploču širu od 1 m nije radna/zidna ploča.
6. **Neaktivni identi** gube pri izjednačenju; materijal koji postoji u Winstoreu ima blagu prednost (stvarno se koristi).
7. **Zadane trake izvedene po nazivu** primjenjuju se bez pitanja, pa su stroge (iste riječi, bez viška, ili isti kod); potvrđene iz ponuda imaju prednost i uvoz ih ne prepisuje.

## 5. Što treba Igor (pitanja i nalazi o podacima)

### 5.1 Zidne obloge bez identa
U tri CPO-a (ROMIC `I_01847`, `SA_016436`; BRATEK `I_02096`) materijal je `ZO HR EVOKE SUNSET` / `ZO HR CREMONA CANNOLO` (ploča 4100×640).
U Pantheonu postoji 20 identa `ZIDNA PLOČA …` / `ZIDNA OBLOGA …` (Egger kodovi: F204 ST9, H1180 ST37, U702 ST89…), ali **ni jedan za
EVOKE SUNSET ni CREMONA CANNOLO**, a u ponudama tih naloga nema stavke za njih (benchmark „—“). **Pitanje:** kako se zidna obloga tih
dekora naplaćuje — pod identom radne ploče (`RP000149 RADNA PLOČA HRAST EVOKE SUNSET K5574 AW`, u 640 mm), kao zasebna stavka, ili
se otvara ident? Hub bi za ZO bez identa mogao ponuditi RP ident istog dekora „za potvrdu“ — treba pravilo.

### 5.2 Winstore kodovi koji se ne mogu povezati, a imaju stanje
| Kod | Opis u Winstoreu | kom | Zašto |
|---|---|---|---|
| 2800AB-19 | IVERICA FURNIR.E.HRAST 2800AB 19MM | 8 | u Pantheonu nema furnirane iverice s tim kodom (`IV000065 IVERAL FURNIR HRAST` je već vezan na `IV000065-19`) |
| MOSAICOFB35-19 | IVERAL MOSAICO CLEAF FB35 19MM | 2 | nema identa s FB35 |
| U125ST9-18 | IVERAL PJESCANO ZUTI 18MM | 2 | nema identa „pješčano žuti“ ni U125 |
| 0162PE-25 | GRAFIT SIVA | 1 | opis bez vrste i debljine; više kandidata |
| 0227-19 | FURNIRANI MDF HRAST 0227 19MM | 1 | nema identa |
| 0514AM-18 | AKRIL IVORY 0154AM 18MM | 1 | kod u opisu (0154) ≠ kod (0514) — tipfeler |
| 37737ND-19 | IVERAL BREZA TAIGA 37737 ND 19MM | 1 | nema identa |
| H1277ST9-18 | IVERAL LAKELAND BAGREM SVIJETLI H1277ST9 18MM | 1 | nema identa |
| IV000115-19 | AKRIL LJUBICASTA IV000115 19MM | 1 | ident postoji, ali s debljinom 18,6 mm (Winstore 19) |
| K4892DP-19 | IVERAL PIETRA GREY K4892DP 19MM | 1 | nema identa |
| U999TM28-18 | IVERAL U999 TM28 18MM CRNI GOD | 1 | Pantheon ima `U999 ST7 CRNI NK` (drugi kod) |
| 1111PO-18 | POVRAT OSTECENO | 1 | nije materijal |

Ambalažne ploče: 17 kodova (44 ploča) s opisom `AMBALAZA …` — Pantheon ima `IV000931/932/933 AMBALAŽA 18/19/25MM` i `IV000322 AMBALAŽA`,
a Winstore kodove piše po osobi (`111IVAN-18`, `222ZLAJA-19`, `555SOKAC-19`…). **Pitanje:** treba li ih Hub uopće voditi (za nesting
jesu ploče na stanju) — prijedlog: sve `AMBALAZA` kodove vezati na ident po debljini (18 → IV000931 …), bez obračuna.
Ostalih 70 nepovezanih kodova ima stanje 0 (stari dekori) — nije hitno; kad se pojave, idu „za potvrdu“.

### 5.3 Rupe i nedosljednosti u Pantheon šifrarniku (ne blokiraju, ali ih čovjek mora znati)
- **Isti ident za više debljina** jer naziv nema debljinu: `IV000994 IVERAL U999 ST7 CRNI NK` (Winstore 10 i 18 mm), `IV001032 MDF U665 PM/ST9 MAT` (18 i 19), `IV000633 IVERAL NATURAL HAMILTON OAK` (18 i 25), `IV001274 IVERAL FURNIR HRAST 1 KLASA` (25). Hub veže obje debljine na isti ident; ako se naplaćuju različito, treba ih razdvojiti u Pantheonu.
- **Jedan ident, dva dekora u Winstoreu**: `IV000719 IVERAL HRAST CHALET 25MM` (bez koda) ↔ Winstore `35252AT-25` i `35252PR-25`.
- **Dva identa za „HRAST SONOMA 18“** (`IV000171` 3025 SN i `IV000954` 517 2840×1830) — riješeno aliasom iz ponude, ali `IV HR SONOMA 25mm` ide na `IV000351` samo zbog aliasa.
- **Trake koje nedostaju** za dekore koji se stvarno kantiraju: `ABS 0,5/22 CRNA NK` i `ABS 1/22 CRNA NK` (CRNA NK postoji samo kao 0,5/29, 0,5/44, 1/44 i 2/29), `ABS 1/22 CHAMPAGNE UM` (postoji `CHAMPAGNE GOD`, `CHAMPAGNE/SATIN SU` i `CHAMPAGNE OM/OF`), traka za `PVC CRNI MAT VSM-02` (dva kandidata `ABS 1/22 CRNA MAT`, TR000534 i TR000733 — duplikat u Pantheonu). Prvi put se potvrde na ekranu, ali ako se ti dekori kantiraju redovito, bolje je otvoriti trake u Pantheonu.
- Tipfeleri u nazivima (`CHINCHILLLA`, `SHELLL`, `CAPUCCINO` / `CAPPUCINO`, `MOČVARNI 25MM 37717AT` s kodom iza debljine) i nazivi bez debljine (`PVC TREND GREY VHG-19 SJAJ`, `PVC KAMEN SIVI VHG-22`) — prepoznavanje ih podnosi, ali ih vrijedi ispraviti u Pantheonu.
- 191 `IV*` identa nema prepoznatljivu vrstu u nazivu (`LAMINAT …`, `KAMENA PLOČA …`, `FOLIJA …`) — vode se kao „ostalo“ i ne sudjeluju u prepoznavanju ploča.

### 5.4 Što Igor pokreće (na svom PC-u, u `30_NOVI_PROGRAM`)
```bat
cd C:\Users\Administrator\Desktop\IGOR\CLAUDE_COWORK\Paneli_Production_Hub\30_NOVI_PROGRAM
pip install -r requirements.txt
py -m hub.sifrarnici.uvoz --db hub.db --pantheon ..\..\ph_identi.csv --winstore ..\04_STROJEVI\NESTING\11092026.XML
py -m hub.sifrarnici.provjera --db hub.db --nalozi ..\05_NALOZI_ZA_TEST --benchmark ..\20_ANALIZA\benchmark_nalozi.csv --md ..\20_ANALIZA\11a_provjera_sifrarnika.md
set HUB_TEST_DATA=C:\Users\Administrator\Desktop\IGOR\CLAUDE_COWORK\Paneli_Production_Hub\05_NALOZI_ZA_TEST
py -m pytest -q
```
Očekivano: `CPO materijali (50) — sigurno 47 … točno vs ponuda 40 / 40`, `CPW 37`, `CSV 30`, `Trake 42`, testovi prolaze. Probni API:
`set HUB_DB=hub.db` pa `py -m uvicorn hub.api.app:app --port 8765` i otvoriti `http://localhost:8765/docs`.

## 6. Prilog — izvještaj provjere (generiran naredbom `provjera --md`)

| Skup | Ukupno | Sigurno | Razine |
|---|---|---|---|
| CPO materijali (pila, PW) | 50 | 47 | alias 4, naziv 43, nema 3 |
| CPW materijali | 37 | 37 | alias 4, naziv 33 |
| PPNEST CSV materijali (SIFRA MAT) | 31 | 30 | alias 3, naziv 4, winstore 23, za_potvrdu 1 |
| Trake iz CPW oznaka | 48 | 42 | alias 2, naziv 14, za_potvrdu 6, zadana 26 |

CPO vs ident u ponudi (benchmark_nalozi.csv): točno 40 / 40

| Datoteka | Naziv u CPO | Razina | Hub ident | Pantheon naziv | Ponuda |
|---|---|---|---|---|---|
| I_01840.cpo | IV_BIJELI_NK_18_MM | naziv | IV000090 | IVERAL BIJELI NK W908 ST2 18 MM | — |
| I_01841.cpo | IV_BIJELI_NK_16_MM | naziv | IV000002 | IVERAL BIJELI NK W908 ST2 16MM | IV000002 |
| I_01842.cpo | MDF_BIJELI_3MM | naziv | IV000054 | MDF BIJELI 3 MM IV000054 | IV000054 |
| I_01843.cpo | PVC_CRNI_MAT_18 | alias | IV000671 | PVC CRNI MAT VSM-02 18MM | IV000671 |
| I_01844.cpo | AK_CREAM_SJAJ_VA103_18 | naziv | IV000562 | AKRIL CREAM SJAJ VA-103 18MM | IV000562 |
| I_01846.cpo | RP SLATE VULCANO K2877 | naziv | RP000286 | RADNA PLOČA SLATE VULCANO K2877CN | — |
| I_01847.cpo | ZO HR EVOKE SUNSET | nema | — |  | — |
| I_01848.cpo | IV_HR_EVOKE_SUNSET_19 | naziv | IV000592 | IVERAL HRAST EVOKE SUNSET K5574 IR 19MM | IV000592 |
| I_01970.cpo | IV_BIJELI_NK_18_MM | naziv | IV000090 | IVERAL BIJELI NK W908 ST2 18 MM | IV000090 |
| I_01971.cpo | IV_HR_AVIVA_DEW_19 | naziv | IV001104 | IVERAL HRAST AVIVA DEW K2751 AE 19MM | IV001104 |
| I_02021.cpo | IV_BIJELI_NK_16_MM | naziv | IV000002 | IVERAL BIJELI NK W908 ST2 16MM | IV000002 |
| I_02022.cpo | MDF_BIJELI_3MM | naziv | IV000054 | MDF BIJELI 3 MM IV000054 | IV000054 |
| I_02023.cpo | MDF_CHAMPAGNE_OF_27045-1 | naziv | IV001038 | MDF CHAMPAGNE 27045 OF 19MM | IV001038 |
| I_02024.cpo | IV_HR_AVIVA_DEW_K2751AE- | naziv | IV001104 | IVERAL HRAST AVIVA DEW K2751 AE 19MM | IV001104 |
| I_02025.cpo | IV_BIJELI_NK_18_MM | naziv | IV000090 | IVERAL BIJELI NK W908 ST2 18 MM | IV000090 |
| SA_016447.cpo | IV BIJELI NK 18mm | naziv | IV000090 | IVERAL BIJELI NK W908 ST2 18 MM | IV000090 |
| SA_016449.cpo | IV BIJELI NK 16 mm | naziv | IV000002 | IVERAL BIJELI NK W908 ST2 16MM | IV000002 |
| SA_016451.cpo | IV CHAMPANGE UM 19 mm | naziv | IV001157 | IVERAL CHAMPAGNE 27045 UM 19MM | — |
| SA_016452.cpo | MDF BIJELI 3mm | naziv | IV000054 | MDF BIJELI 3 MM IV000054 | IV000054 |
| I_01911.cpo | IV HRAST RELIEF CARDAMOM | naziv | IV001219 | IVERAL HRAST RELIEF CARDAMOM K2776 GR 19MM | IV001219 |
| I_01912.cpo | IV BIJELI NK 16MM | naziv | IV000002 | IVERAL BIJELI NK W908 ST2 16MM | IV000002 |
| I_01913.cpo | IV BIJELI NK 18MM | naziv | IV000090 | IVERAL BIJELI NK W908 ST2 18 MM | IV000090 |
| I_01914.cpo | MDF BIJELI 3MM | naziv | IV000054 | MDF BIJELI 3 MM IV000054 | IV000054 |
| I_01915.cpo | IV JELA TAVERNA 19MM | naziv | IV001210 | IVERAL JELA TAVERNA K2665 AI 19MM | IV001210 |
| I_01916.cpo | RP BASANIT SAND | naziv | RP000243 | PLOČA STOLA BASANIT SAND K2875CN | — |
| I_02089.cpo | IV BIJELI NK 16MM | naziv | IV000002 | IVERAL BIJELI NK W908 ST2 16MM | IV000002 |
| I_02090.cpo | MDF_BIJELI_3MM | naziv | IV000054 | MDF BIJELI 3 MM IV000054 | IV000054 |
| I_02091.cpo | IV_HR_CREMONA_CANNOLO_19 | naziv | IV001206 | IVERAL HRAST CREMONA CANNOLO K2739 OC 19MM | IV001206 |
| I_02093.cpo | PVC_KAMIR_VSM06_18 | naziv | IV000580 | PVC KAŠMIR VSM-06 18MM | IV000580 |
| I_02094.cpo | IV_BIJELI_NK_18_MM | naziv | IV000090 | IVERAL BIJELI NK W908 ST2 18 MM | IV000090 |
| I_02095.cpo | RP HR CREMONA CANNOLO | naziv | RP000293 | RADNA PLOČA HRAST CREMONA CANNOLO K2739AX | — |
| I_02096.cpo | ZO HR CREMONA CANNOLO | nema | — |  | — |
| SA_015891.cpo | IV HR SONOMA 18mm | alias | IV000171 | IVERAL HRAST SONOMA 3025 SN 18MM | IV000171 |
| SA_015892.cpo | IV BIJELI GL 10 mm | naziv | IV000091 | IVERAL BIJELI GLATKI 1615FH 10MM | IV000091 |
| SA_015893.cpo | IV HR SONOMA 25mm | alias | IV000351 | IVERAL HRAST SONOMA 3025 SN 25MM | IV000351 |
| SA_015894.cpo | IV BIJELI NK 18mm | naziv | IV000090 | IVERAL BIJELI NK W908 ST2 18 MM | IV000090 |
| SA_015895.cpo | MDF BIJELI 3mm | naziv | IV000054 | MDF BIJELI 3 MM IV000054 | IV000054 |
| SA_015896.cpo | RP HR SONOMA | naziv | RP000068 | RADNA PLOČA HRAST SONOMA SVIJETLI 34038 AT | — |
| SA_016178.cpo | IV BIJELI NK 16 mm | naziv | IV000002 | IVERAL BIJELI NK W908 ST2 16MM | IV000002 |
| SA_016180.cpo | PVC BIJELI MAT VSM 01 18 | naziv | IV000577 | PVC BIJELI MAT VSM-01 18MM | IV000577 |
| SA_016181.cpo | IV SIVI TAMNI 2162MN 19m | naziv | IV001168 | IVERAL SIVI TAMNI 2162 MN 19MM | IV001168 |
| SA_016182.cpo | IV EGGER H1180 ST37 | alias | IV000315 | IVERAL H1180 HRAST HALIFAX 18MM | IV000315 |
| SA_016183.cpo | MDF BIJELI 3mm | naziv | IV000054 | MDF BIJELI 3 MM IV000054 | IV000054 |
| SA_016431.cpo | IV BIJELI NK 18mm | naziv | IV000090 | IVERAL BIJELI NK W908 ST2 18 MM | IV000090 |
| SA_016432.cpo | MDF CHAMPAGNE OF | naziv | IV001038 | MDF CHAMPAGNE 27045 OF 19MM | IV001038 |
| SA_016433.cpo | IV HR EVOKE SUNSET 19mm | naziv | IV000592 | IVERAL HRAST EVOKE SUNSET K5574 IR 19MM | IV000592 |
| SA_016434.cpo | IV BIJELI NK 16 mm | naziv | IV000002 | IVERAL BIJELI NK W908 ST2 16MM | IV000002 |
| SA_016435.cpo | RP HR EVOKE SUNSET | naziv | RP000149 | RADNA PLOČA HRAST EVOKE SUNSET K5574 AW | — |
| SA_016436.cpo | ZO HR EVOKE SUNSET | nema | — |  | — |
| SA_016437.cpo | MDF BIJELI 3mm | naziv | IV000054 | MDF BIJELI 3 MM IV000054 | IV000054 |

## Trake (oznaka u CPW → traka)

| Materijal | Oznaka | Razina | Traka | Naziv | Klasa |
|---|---|---|---|---|---|
| IV000562 | ABS-ISTI | zadana | TR000650 | ABS 1/22 CREAM SJAJ VA-103 | 1/22 |
| IV000002 | MEL-ISTI | zadana | TR000017 | ABS 0,5/22 BIJELI NK | 0,5/22 |
| IV000090 | 1/22 ISTI | zadana | TR000168 | ABS 1/22 BIJELI NK | 1/22 |
| IV000090 | MEL CRNA NK | za_potvrdu | TR000739 | ABS 0,5/29 CRNA NK | 0,5/22 |
| IV000090 | MEL_ISTI | zadana | TR000017 | ABS 0,5/22 BIJELI NK | 0,5/22 |
| IV000592 | ABS-ISTI | zadana | TR000659 | ABS 1/22 HRAST EVOKE SUNSET K5574IR | 1/22 |
| IV000671 | ABS-ISTI | za_potvrdu | TR000534 | ABS 1/22 CRNA MAT | 1/22 |
| IV001104 | ABS-ISTI | zadana | TR001243 | ABS 1/22 HRAST AVIVA DEW | 1/22 |
| IV000090 | 1/22 AVIVA DEW | naziv | TR001243 | ABS 1/22 HRAST AVIVA DEW | 1/22 |
| IV000090 | 1/22 OF CHAMPAGNE | naziv | TR001163 | ABS 1/22 CHAMPAGNE OM/OF 19MM | 1/22 |
| IV001038 | ABS-ISTI | naziv | TR001163 | ABS 1/22 CHAMPAGNE OM/OF 19MM | 1/22 |
| IV000090 | 1/22 BIJELI NK | naziv | TR000168 | ABS 1/22 BIJELI NK | 1/22 |
| IV000090 | 1/22 CHAMPAGNE UM | za_potvrdu | TR000262 | ABS 1/22 CHAMPAGNE GOD | 1/22 |
| IV000090 | 2/22 BIJELI NK | naziv | TR000016 | ABS 2/22 BIJELI NK | 2/22 |
| IV000090 | MEL 0.5/22 BIJELI NK | naziv | TR000017 | ABS 0,5/22 BIJELI NK | 0,5/22 |
| IV000090 | MET 0.5/22 BIJELI NK | naziv | TR000017 | ABS 0,5/22 BIJELI NK | 0,5/22 |
| IV001157 | ABS-ISTI | za_potvrdu | TR000262 | ABS 1/22 CHAMPAGNE GOD | 1/22 |
| IV000090 | MEL-ISTI | zadana | TR000017 | ABS 0,5/22 BIJELI NK | 0,5/22 |
| IV000090 | taverna | alias | TR001254 | ABS 1/22 JELA CLAY | 1/22 |
| IV001219 | ABS-ISTI | zadana | TR001213 | ABS 1/22 HRAST RELIEF PIMENTO | 1/22 |
| IV001210 | ABS-ISTI | zadana | TR001254 | ABS 1/22 JELA CLAY | 1/22 |
| IV000090 | 1/22 JELA TAVERNA | alias | TR001254 | ABS 1/22 JELA CLAY | 1/22 |
| IV001210 | 1/44 ISTI | zadana | TR001258 | ABS 1/44 JELA CLAY | 1/44 |
| IV000090 | 1/22 VSM06 KASMIR | naziv | TR000748 | ABS 1/22 CASHMIR VSM-06 | 1/22 |
| IV001206 | ABS-ISTI | zadana | TR001352 | ABS 1/22 HRAST CREMONA CANNOLO | 1/22 |
| IV000580 | ABS-ISTI | zadana | TR000748 | ABS 1/22 CASHMIR VSM-06 | 1/22 |
| IV001168 | ABS-ISTI | zadana | TR000875 | ABS 1/22 SIVI TAMNI | 1/22 |
| IV000577 | ABS-ISTI | zadana | TR000540 | ABS 1/22 BIJELA MAT | 1/22 |
| IV000090 | 0,5/22 CHAMPAGNE | naziv | TR000045 | ABS 0,5/22 CHAMPAGNE | 0,5/22 |
