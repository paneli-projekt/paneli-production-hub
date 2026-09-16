# Paneli Production Hub — 21: Obračun i ponuda iz Huba (kralježnica korak 4)

Stanje 15. 9. 2026. kasno navečer. Hub sada iz naloga radi ono zbog čega je cijeli lanac i građen: **stavke ponude** s cijenama iz Pantheona
i rabatom kupca, **verzije ponude**, **eSlog XML** za uvoz potvrđene ponude u Pantheon, i **korekciju po stvarnom stanju** za vlastitu
proizvodnju. Pravila su ona koja ured već koristi (skill krojna-ponuda, D-18/D-19/D-20/D-40), provjerena na 8 stvarnih ponuda.

## 1. Obračun (`hub/nalozi/obracun.py`)

    py -m hub.nalozi.obracun --db hub.db --nalog 12 [--bez-pravila] [--suho]
    GET /api/nalog/{id}/obracun        POST /api/nalog/{id}/obracun {pravila, tko}

Po materijalu naloga, redoslijedom kojim ured piše ponude (D-32: ploča → rezanje → usluge → trake → kantiranje; okov na kraju):

| Stavka | Pravilo | Ident |
|---|---|---|
| ploča | PW-metoda (isti optimizator kao pila, D-19 najmanja naplata; element na punu mjeru → bez obreza, D-65/10) → m² za naplatu s odbijenim korisnim ostatkom; **pravilo načete ploče** (krojna-ponuda §1): >2/3 cijela ploča, 1/3–2/3 +0,25 m², <1/3 minimum 1/3, 28–33 % +0,25 i PROVJERI — svaki dodatak piše u `pravilo` stavke, `--bez-pravila` daje čisti PW m² | ident materijala |
| restl | nalog vezan na vlastitu ploču (`ploca_L/W`) → cijela površina × broj ploča | ident |
| radna / zidna ploča | Σ dulja stranica × kom po dužnom metru + 2 reza × kom | RP/ZO + US000303 |
| rezanje | m² ploče; MDF do 8 mm | US000002 / US000013 |
| CNC iz napomene ili CIX-a | `CNC 2xFI35` → kom; `NUT`/`FALC` → m po duljini; `UREZ GOLA` → m; obrada iz CIX-a (Corpus) i „po skici“ → **upozorenje**, ured dodaje ručno | US000149 / US000016 / US002075 |
| trake | Σ stranica × kom × 1,10 (10 % otpada je unutra) po TR identu, **naviše na cijeli metar**, uz svoj materijal | TR ident iz prepoznatog ruba |
| kantiranje | **točni** PW metri po klasi trake (D-20) | US000003 (0,5) / US000011 (1 i 2 mm /22) / US000012 (/44) |
| okov | samo potvrđene stavke `okov_stavka` (D-32); nepotvrđeno → upozorenje | OK ident |

Cijena = `pantheon_ident.cijena_neto` (zaokružena na 2 dec., kao na ponudi); rabat s naloga: `rabat_materijal` za ploče, trake i okov,
`rabat_usluge` za rezanje, kantiranje i CNC (D-40). Nepotvrđen materijal ili rub bez trake → upozorenje, stavka se ne izmišlja.
Radne stavke se upisuju u `obracun_stavka` (bez verzije); svaki novi upis ih zamijeni.

## 2. Ponuda (`hub/nalozi/ponuda.py`)

    py -m hub.nalozi.ponuda --db hub.db --nalog 12 --nova | --eslog VID | --potvrdi VID --pantheon 26-010-003406 | --izdatnica
    POST /api/nalog/{id}/ponude   GET /api/ponuda/{vid}   POST /api/ponuda/{vid}/eslog | /poslana | /potvrdi   POST /api/nalog/{id}/izdatnica

- **Verzija** = snimka stavki (cijena, rabat) + neto i PDV 25 %; nova verzija zamjenjuje nacrt / poslanu (`zamijenjena`), potvrđena se ne dira;
  prva verzija prebacuje nalog iz `unos` u `ponuda` (D-35). Iz `unos` s otvorenim potvrdama nema verzije.
- **Poslana** — `posalji`: PDF ponude (`ponuda_pdf.py`, reportlab; bez njega HTML) + HTML tijelo maila preko SMTP-a hostinga (`mail.py`: `mail.paneliprojekt.hr`:465 SSL, `prodaja@paneliprojekt.hr` — Igor, 15. 9., D-41 riješen); adresa je e-mail kupca iz Huba (D-50). Lozinka u `smtp_lozinka.txt` uz bazu ili `HUB_SMTP_LOZINKA`, nikad u bazi/Gitu; bez nje ured šalje ručno i označi `poslana`.
- **Potvrda kupca** (dijalog 3b): verzija `potvrdjena`, nalog `potvrdjeno` s datumom / načinom / rokom / prioritetom, Pantheon broj ponude u
  nalog (može i kasnije, `upisi_pantheon_broj`), i odmah **eSlog XML**.
- **eSlog 220** — isti kalup kao `skripte\12_ponuda_eslog.py` (klon Pantheon izvoza, uvoz potvrđen 29. 8.): glava 220, datum, PUR napomena
  (nalog + ime osobe krajnjeg kupca), BY / DP / SU / OB (SU = Pantheon subjekt za račun, D-48), stavka po stavci s identom, MJ (M2→MTK, M→MTR,
  KOM→H87), cijenom AAA/AAB i **rabatom po stavci** u `OdstotkiPostavk` (postotak + iznos). XML ide u postavku `mapa_eslog_ponude` (zadano
  `eslog_uvoz_ponude` uz bazu) i bilježi se kao dokument naloga. **Rabat u XML-u treba probni uvoz u Pantheon** — do sada su se rabati upisivali
  ručno nakon uvoza (skill), pa je ovo prvi put da putuju u datoteci (STANJE, otvoreno 6).
- **Vlastita proizvodnja (D-56)**: `korekcija_po_stvarnom` uzme za svaki materijal bNestov rezultat (`.mno`, dokument 19 — stvarno potrošene ploče)
  umjesto PW-metode, ostalo ostaje, i napravi verziju `izdatnica` + eSlog `IZD-<broj>`; nalog dobiva novi status **`izdatnica`** (samo za
  vlastitu proizvodnju; proizvodnja → izdatnica → zatvoren). Materijal bez bNest rezultata ostaje po obračunu uz upozorenje. Koji Pantheon
  dokument prima izdatnicu (vrsta dokumenta u eSlog-u) — pitanje za Igora; sada ide kao 220.

## 3. Benchmark — Hub vs 8 Pantheon ponuda (`py -m hub.alati.benchmark_ponuda`, izvještaj `21a_benchmark_ponuda_2026-09-15.md`)

Za svaki testni nalog Hub uveze PPNEST-ov izvoz (HUMER: kupčev PPW), napravi obračun s rabatima iz same ponude, a stavke ponude čitaju se iz PDF-a.

| | |
|---|---|
| Nalozi s ponudom | 8 (BLAGO ×2, BOGDANIC, BRATEK, HUMER, MAZUR, TURALIJA, VARGA) |
| Zajednički identi (Hub i ponuda) | 76 |
| **Cijena ista** | **73 / 76** (3 razlike su promjene cijena u Pantheonu od datuma ponude — BLAGO_ADRIJANA) |
| Količina unutar ±5 % | 41 / 76 |
| Neto zajedničkih stavki | Hub 10 609,64 € vs ponuda 10 330,05 € (**+2,7 %**) |
| Materijal koji Hub nema, a ponuda ima | samo materijali kojih nema u PPNEST izvozu (na pilu išli izravno kroz PW: IV000002, IV000054, RP…) |
| Što Hub nikad ne računa | okov (ured), ručne usluge (CNC rezanje, bušenja 5/8, LED urez, plastificiranje, spoj radne ploče…) — na ponudama 10–40 takvih stavki |

Primjeri: HUMER JELA TAVERNA **30,97 m² = ponuda** (PW-metoda + pravilo načete ploče), BIJELI NK 16 5,80 = 5,80; BIJELI NK 18 59,89 vs 57,96 (+3,3 %,
Hubov optimizator 11 ploča vs PW 10 — poznatih +4 %); MDF 21,12 vs 18,49 (isto); trake −5 do −12 % (ured zaokružuje ručno; HUMER-ova ponuda je i
kantiranje pisala zaokruženo, D-20 kaže točno). BRATEK: kantiranje 2/22 Hub 20 m vs 115 m — jer traka CHAMPAGNE nije potvrđena u probi (u radu se
potvrdi prije ponude). Ukupno: gdje su ulazi isti, Hub je u granicama ručnog zaokruživanja; sustavna razlika je optimizator (+4 %, korak 5).

## 4. Testovi

`tests/test_obracun_ponuda.py` — pravilo načete ploče (Blago basanit 7,54 → 7,79 PROVJERI), stavke (redoslijed, D-20 traka 3 m / kantiranje 2,20 m,
NUT, okov potvrđen / nepotvrđen, cijene i rabati, upis), verzije ponude (zamjena, snimka), eSlog XML (struktura, MJ, rabat, partneri), poslana / potvrda /
Pantheon broj / dokument, greške, izdatnica (bNest ploče, status `izdatnica`, usluga ne može), API, stvarni HUMER vs ponuda (cijene 12/12, JELA 30,97 = 30,97,
neto zajedničkih unutar 3 %). **109 testova prolazi** (s `tests/test_mail_ponuda.py`: SMTP postavke i lozinka, PDF/HTML, slanje s lažnim SMTP-om, greška prijave, API).

## 5. Što ostaje za korak 4 → 5

- probni uvoz eSlog-a s rabatom u Pantheon (i izdatnice — koja vrsta dokumenta);
- okov: uvoz iz kupčevog Excela / Corpusa s prijedlogom identa (D-32, skill `13_okov_mapiraj`) — sada se okov upisuje ručno u `okov_stavka`;
- ručne usluge (CNC, bušenja, LED…) kao popis za brzi unos na ekranu 3;
- optimizator +4 % (D-17 korak 3) — jedina sustavna razlika u m².
