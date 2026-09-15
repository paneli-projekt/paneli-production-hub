# Paneli Production Hub — 14: Corpus uzorak — što smo saznali i što je već popravljeno

Stanje 14. 9. 2026. Tehnička priprema je napunila `05_NALOZI_ZA_TEST\_CORPUS_UZORAK` projektom **TEST BUSENJE**
(niski ormarići, Siniša, Corpus 6.2.100.261 / modul V55) i odgovorila na svih 7 pitanja iz dokumenta 08 §6.
Ovo je analiza tog paketa na stvarnim datotekama — prva provjera trećeg puta naloga (D-29, D-30) na nečemu što
je doista prošlo cijeli lanac: Corpus → PanelWizard → pila i nesting → ponuda u Pantheonu (26-010-003406).

## 1. Odgovori tehničke pripreme

| # | Pitanje | Odgovor |
|---|---|---|
| 1 | Verzija i CNC modul; nosi li CSV Winstore kod? | Corpus **6.2.100.261**, modul **V55**; CSV **nosi Winstore šifru** (`W908ST2-18`) |
| 2 | Jedan bNest uvozni profil ili dva? | **Isti profil** za PPNEST i Corpus |
| 3 | Tko, kamo, kako do operatera | Siniša; izvoz u `C:\Users\bolko\Desktop\CNC PROGRAMI\NESTING\<projekt>`; **mrežni disk** |
| 4 | Kamo idu brojke iz PW-a | U **ponudu**, koju radi **ured**; ponuda je radni dokument, nakon posla se **korigira po stvarnom stanju i ide u internu izdatnicu** |
| 5 | Pila pa Rover? | **Oboje** — pila uvijek reže leđa MDF 3 mm |
| 6 | Etikete | Corpusove se **ne** koriste (koriste se OSI i bSolid), ali **ID elementa iz Corpusa mora ostati na etiketi** |
| 7 | Uslužni nalozi u Corpusu? | **Isključivo vlastita proizvodnja** |
| 8 | Sudar imena CIX-a | Isto ime u dva projekta se ne događa, ali **novi CIX je znao pregaziti stari** — zato PPNEST imenuje po datumu i vremenu |
| 9 | Što se ručno popravlja | **Ime CSV-a** se mijenja u ime posla |

Odgovor 4 mijenja pretpostavku iz dokumenta 08 (§6 pitanje 4): nije ni „ponuda kupcu" ni „interni radni nalog",
nego **ponuda kao radni dokument → korekcija po stvarnom stanju → interna izdatnica**. To je jedan korak više nego
što D-40 danas opisuje i treba ga ugraditi u tok za `vrsta = vlastita_proizvodnja`.

Odgovor 8 je izravna potvrda da registar imena CIX datoteka (D-23) nije teorijski oprez — pregaženi program se već dogodio.

## 2. Što je paket sadržavao

`TEST BUSENJE`: 2 korpusa, **15 komada** u 3 materijala, s bušenjem (2 elementa), utorima (2) i krivolinijom (1).

- **3 CPW-a** (po materijalu): `IV BIJELI NK_18` (10 el.), `IV SIVI TAMNI_19` (3), `MDF BIJELI 4 MM_4` (2)
- **1 CSV** za nesting: `TEST_BUSENJE.CSV`, **13 elemenata**
- **15 CIX-ova** + 4 dodatna u podmapi `HORIZONTALNO_BUSENJE`, te `LJEPLJENE_DASKE`
- PW izlaz: 3 krojne PDF + 3 CPO (`S0_06372/73/74`) + `.pnl` radne datoteke
- bNest: dva projekta (`TEST_BUSENJE_W908ST2-18_18`, `TEST_BUSENJE_2162PE-19_19`) s `.mno`, `.bSolid` i `xMno`
- Pantheon: `PONUDA PANELI_26-010-003406.pdf`

## 3. Nalazi na datotekama

### 3.1 CSV profil NIJE isti kao PPNEST-ov — Hub je popravljen

bNest oba čita istim uvoznim profilom (odgovor 2), ali imena stupaca se razlikuju na četiri mjesta, a Corpus ima
i jedan stupac više (29 : 28):

| Stupac | PPNEST | Corpus |
|---|---|---|
| 6 | `KONACNA DIMENZIJA` | `KONACNADIMENZIJA` (bez razmaka) |
| 20 | `TRS2IFRA` (tipfeler) | `TR2SIFRA` |
| 27 | `NAPOMENA` | `bSolid` |
| 29 | — | `Primjedba` (`True` / `False`) |

Hubov čitač je pucao na `TRS2IFRA`. **Popravljeno**: `nalog_io.read_ppnest_csv` sada prihvaća oba pisanja
istog stupca, preskače prazan zadnji redak (Corpus izvoz završava s `;`) i ne upisuje `True`/`False` kao napomenu.
Isti čitač čita oba izvora, kao i bNest. PPNEST datoteke čitaju se nepromijenjeno.

**Usput dobiveno**: iz Corpusovog CSV-a Hub sada čita i `NAZIV ELEMENTA` (cjelina, npr. `EL_BUSENJE`),
`IME DASKE` (pozicija: `L_BOK`, `POD`, `STROP`, `Polica`, `FR`), `PROGRAM1` i `PROGRAM2`. To je točno ono što
traži odgovor 6 — ID elementa iz Corpusa koji mora ostati na etiketi.

### 3.2 CSV i CPW se NE poklapaju — i to je ispravno

CSV ima 13 elemenata, CPW-ovi 15. Razlika su dva leđa od MDF-a, koja po odgovoru 5 uvijek idu na pilu, pa ih
Corpus ni ne stavlja u nesting listu. Za PPNEST naloge Hub razliku CPW ↔ CSV prijavljuje kao grešku (D-46 (6));
**za Corpus pakete to ne smije biti greška**, nego podjela puta: CSV = nesting, CPW = svi elementi po materijalu.

### 3.3 Dva CIX-a po elementu

Elementi `POD` i `STROP` imaju `PROGRAM1` = `1446A088F7C` (vertikalno, nesting) i `PROGRAM2` = `2446A088F7C`
(horizontalno bušenje, u podmapi `HORIZONTALNO_BUSENJE`, uz `.wmf` sliku). Hub mora prenijeti **oba**; prijenos
samo prvog izgubio bi bušenje u kant.

### 3.4 CIX je standardni bSolid — Hub ga može pročitati bez diranja

Zaglavlje `BEGIN ID CID3` + `MAINDATA` s `LPX/LPY/LPZ`, makroi s `PARAM`. Iz uzorka:

| Datoteka | Dimenzija | Što sadrži |
|---|---|---|
| `1446A6B3FCB` | 796×888×4 | samo kontura (5 × `LINE_EP`) — leđa, bez obrade |
| `1446A088F7C` | 864×556×18 | kontura + 8 `TTP` — utor |
| `1446A088F7A` | 800×560×18 | **25 bušenja** (`DP`/`DIA`), 36 `TTP` |
| `2446A088F7C` | 864×556×18 | 12 horizontalnih bušenja |

Znači Hub može deterministički izvući `ima_obradu`, broj bušenja i konturu (08 §3.1) bez ijedne izmjene CIX-a —
što je i bio uvjet iz D-29: Corpus ostaje CAM autoritet, Hub provjeri, registrira i proslijedi.

### 3.5 Šifrarnik: 2 od 3 materijala sigurno, jedan pravi nalaz

| Iz Corpusa | Debljina | Hub | Rezultat |
|---|---|---|---|
| `W908ST2-18` / IV BIJELI NK | 18 | IV000090 | sigurno (Winstore kod) |
| `2162PE-19` / IV SIVI TAMNI | 19 | IV000027 | sigurno (Winstore kod) |
| `IV000054-3` / MDF BIJELI 4 MM | 4 (nut) | IV000054 | sigurno nakon ispravka — vidi dolje |

Treći nije greška ni u Corpusu ni u Pantheonu — **Igor je objasnio 14.9.2026.**: MDF od 3 mm je u stvarnosti
3,2–3,6 mm, pa se nut u bočnim stranicama radi **4 mm** da ploča lakše klizne. Corpus zato materijal vodi kao
„MDF BIJELI 4 MM" (po nutu), a šalje šifru `IV000054-3` — ident `IV000054 MDF BIJELI 3 MM`, što je ispravna ploča.
Hub je odbio povezati jer je uspoređivao deklariranu debljinu (4) s debljinom identa (3).

**Riješeno na dva načina:** (a) veza `IV000054-3 → IV000054` upisana je kao ispravak ureda (D-51) s tim
obrazloženjem; (b) prepoznavanje sada Winstore kod traži i u **samom nazivu materijala** — Corpusov CPW u polje
`MATERIJAL` piše upravo kod (`W908ST2-18`, `IV000054-3`), a ne tekstualni naziv kao PPW-ov CPW. Time sva tri
Corpusova materijala prolaze sigurno, i to preko koda, što je jača razina od pogađanja po nazivu.

Trake: `BIJELA_NK-1/22` → TR000168 i `BIJELA_NK-MEL` → TR000017 sigurno. `SIVA_TAMNA-1/22` je isprva promašila
(nudila je PLATINASTO SIVI) jer Corpus piše ženski rod, a Pantheon muški. Igor je potvrdio da je **„sivi tamni" i
„siva tamna" ista stvar**, pa je `TAMNA → TAMNI` dodan u tablicu sinonima — uz `BIJELA → BIJELI`, `CRNA → CRNI`,
`SIVA → SIVI` koje su već bile tamo. Sada Hub nudi prave kandidate, ali i dalje traži potvrdu jer ih ima dva:
`ABS 1/22 SIVI TAMNI 2162 OM` (TR000693) i `ABS 1/22 SIVI TAMNI` (TR000875), a materijal je 2162 **PE**. To je
stvarna dvojba, ne promašaj — jedna potvrda ureda pretvara je u alias zauvijek (D-32).

## 4. Što ovo mijenja u planu

1. **D-29 i D-30 su potvrđeni na stvarnom paketu** — mogu iz PREDLOŽENO u ODLUČENO.
2. **Hubov CPW čitač treba proširiti za Corpus**: danas čita mjere, rubove i materijal, ali **gubi naziv elementa
   (`EL_BUSENJE - L_BOK`) i imena CIX datoteka** iz zadnja tri stupca. To su upravo Corpusovi podaci. Ide u korak 3.
3. **Uvoz Corpus paketa** (modul `import.corpus`, 08 §4.3) radi se u koraku 3 zajedno s exportima: pročitaj mapu,
   spoji CPW + CSV + CIX, provjeri da svaki element s programom ima CIX, razdvoji put (CSV → nesting, ostatak → pila),
   registriraj imena (D-23) i proslijedi.
4. **Obračun za vlastitu proizvodnju** (D-40 dopuna): ponuda kao radni dokument → korekcija po stvarnom stanju →
   interna izdatnica. Treba mu vlastiti status u toku naloga.
5. **Mjereno nakon popravaka** (uzorak je ušao u redovnu provjeru): CPO 47 / 50 i 40 / 40 prema ponudi nepromijenjeno;
   **CPW 40 / 40 sigurno** (bila 37 / 37 — sva tri Corpusova materijala prolaze); PPNEST CSV 32 / 33; trake 44 / 51.
   58 testova prolazi.

## 5. Sitno

- U mapi je i `New folder\_CORPUS_UZORAK` — slučajna kopija praznog predloška, može se obrisati.
- `NALOG.txt` polje „Broj elemenata: 2" znači 2 korpusa; komada je 15.
- Mapa `LJEPLJENE_DASKE` sadrži samo `_PREDLOZAKPP.PDF` — nije bilo lijepljenih dasaka u ovom projektu.
- Uzorak sada ulazi u `hub.sifrarnici.provjera` (mapa je u `05_NALOZI_ZA_TEST`), pa se brojke benchmarka odnose na
  9 naloga umjesto 8. Uvoz cijelog Corpus paketa u nalog (`hub.nalozi.provjera`) još ne radi jer paket ima drugu
  strukturu mapa — to je korak 3 (točka 3 gore).
