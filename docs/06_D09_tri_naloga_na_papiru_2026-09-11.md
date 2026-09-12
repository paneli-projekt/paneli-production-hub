# Paneli Production Hub — D-09: tri naloga kroz cijeli lanac "na papiru"

Generirano skriptom `skripte/d09_tri_naloga.py` (11. 9. 2026.) iz datoteka u `05_NALOZI_ZA_TEST`. Izvor istine za elemente i sheme je PW CPO
(imaju ga sva tri naloga); obračun je PW-metodom po pravilima iz 05 §5.3 (kerf 16, obrub 10, korisni ostatak ≥ 400×400 mm i ≥ 1 m²,
naplata = Σ ploča − Σ korisnih ostataka; trake = Σ stranica × 1,10). Ponuda = stavke iz Pantheon PDF-a.

## HUMER_2823_OMIS — ponuda 26-010-002823

**1. Ulaz kupca** (CPW iz klijentske aplikacije (PPW) + skice + Excel okova): `Ivana Omis radne ploce.pdf`, `Ivana omis skica fronti.pdf`, `OKOV (48).xlsx`

**2. Unos i exporti:** PPNEST zapisa (TXT) 3, nesting CSV 0 + CIX 0, CPW za PW 0, PW programa za pilu (CPO) 6, bNest rezultata nema

**3. Materijali kroz lanac** (nalog = PW program; obračun PW-metodom iz stabla rezova; Hub = vlastiti optimizator, D-19):

| PW program | Materijal | Elem. | Kom | m² dijelova | God | PW ploča | PW m² naplata | Hub ploča | Hub m² (način) | Ponuda ident | Ponuda kol. | Razlika ponuda−PW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I_01911 | IV HRAST RELIEF CARD | 1 | 1 | 1.95 | da | 1 | 2.73 | 1 | 2.73 (uzduzno) | IV001219 | 2.98 M2 | +0.25 |
| I_01912 | IV BIJELI NK 16MM | 10 | 28 | 4.60 | ne | 1 | 5.80 | 1 | 5.80 (poprecno) | IV000002 | 5.8 M2 | +0.00 |
| I_01913 | IV BIJELI NK 18MM | 53 | 174 | 50.37 | ne | 10 | 57.96 | 11 | 58.98 (uzduzno) | IV000090 | 57.96 M2 | +0.00 |
| I_01914 | MDF BIJELI 3MM | 22 | 27 | 16.09 | ne | 4 | 18.49 | 4 | 20.87 (poprecno) | IV000054 | 18.49 M2 | +0.00 |
| I_01915 | IV JELA TAVERNA 19MM | 35 | 48 | 25.57 | da | 6 | 30.16 | 6 | 30.89 (uzduzno) | IV001210 | 30.97 M2 | +0.81 |
| I_01916 | RP BASANIT SAND | 2 | 2 | 4.49 | da | 2 | 7.38 | 2 | 7.38 (uzduzno) | RP000136 PLOČA STOLA CIJELA | 2 KOM | = D-37b (900 mm → 2 × cijela); *ispravak 12.9.*: 2,4 M RP000259 je zasebna stavka izvan CPO-a |

Ukupno ploče (bez RP/ZO): **PW 115.14 m² · Hub 119.27 m² · ponuda 116.20 m²**

**4. Trake** (PW "Kantiranje sortirano po dekorima" = Σ stranica × 1,10; rekonstruirano iz CPO PRT3):

| PW program | Materijal | Traka (naziv u nalogu) | PW metri | Ponuda (TR ident, m) |
|---|---|---|---|---|
| I_01911 | IV HRAST RELIEF CARD | ABS-ISTI | 6.6 |  |
| I_01912 | IV BIJELI NK 16MM | MEL-ISTI | 50.9 |  |
| I_01913 | IV BIJELI NK 18MM | taverna | 208.2 |  |
| I_01913 | IV BIJELI NK 18MM | MEL-ISTI | 21.8 |  |
| I_01915 | IV JELA TAVERNA 19MM | ABS-ISTI | 151.3 |  |
| I_01915 | IV JELA TAVERNA 19MM | 1-44 ISTI | 6.8 |  |
| I_01916 | RP BASANIT SAND | 1-44 ISTI | 2.0 |  |

Stavke traka u ponudi: TR001254 ABS 1/22 JELA CLAY 210 m; TR000017 ABS 0,5/22 BIJELI NK 23 m; TR001254 ABS 1/22 JELA CLAY 180 m; TR001258 ABS 1/44 JELA CLAY 8 m; TR001213 ABS 1/22 HRAST RELIEF PIMENTO 8 m; TR000017 ABS 0,5/22 BIJELI NK 55 m

**5. Usluge u ponudi:** US000002 USLUGA REZANJA 57.96 M2; US000005 USLUGA REZANJA CNC 1.98 M; US000148 USLUGA P-BUŠENJA 5/8 MM 569 KOM; US000011 USLUGA KANTIRANJA 2/22 210 M; US000003 USLUGA KANTIRANJA 0,5/22 23 M; US000002 USLUGA REZANJA 30.97 M2; US000011 USLUGA KANTIRANJA 2/22 180 M; US000012 USLUGA KANTIRANJA 2/44 6.5 M; US002089 USLUGA UREZIVANJA ZA LED PROFIL 1.04 M; US000087 USLUGA NUT KANT 5.38 M; US000007 USLUGA LJEPLJENJA PLOČA 1.1 M2; US000245 USLUGA GLODANJA ZA RUČKICU 25 KOM; US000002 USLUGA REZANJA 2.98 M2; US000011 USLUGA KANTIRANJA 2/22 6.2 M; US000002 USLUGA REZANJA 5.8 M2; US000003 USLUGA KANTIRANJA 0,5/22 55 M; US000013 USLUGA REZANJA MDF 18.49 M2; US000303 USLUGA REZANJA RADNE PLOČE 2 KOM; US000015 USLUGA SPOJ RADNE PLOČE 2 KOM; US000686 USLUGA PLASTIFICIRANJA 8.2 M; US000055 ALU. VRATA PO SPECIFIKACIJI 1 KPT

**6. Okov u ponudi:** 42 stavki (ručni unos iz upita kupca — Hub ne računa, D-07/pravila §6)

## BRATEK_3231 — ponuda 26-010-003231

**1. Ulaz kupca** (Excel kupca (NARUDŽBA + OKOV)): `panel projekt BRATEK_rev2.xlsx`

**2. Unos i exporti:** PPNEST zapisa (TXT) 4, nesting CSV 0 + CIX 0, CPW za PW 0, PW programa za pilu (CPO) 4, bNest rezultata nema

**3. Materijali kroz lanac** (nalog = PW program; obračun PW-metodom iz stabla rezova; Hub = vlastiti optimizator, D-19):

| PW program | Materijal | Elem. | Kom | m² dijelova | God | PW ploča | PW m² naplata | Hub ploča | Hub m² (način) | Ponuda ident | Ponuda kol. | Razlika ponuda−PW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SA_016447 | IV BIJELI NK 18mm | 20 | 65 | 25.60 | ne | 5 | 28.98 | 6 | 30.96 (poprecno) | IV000090 | 28.98 M2 | +0.00 |
| SA_016449 | IV BIJELI NK 16 mm | 7 | 22 | 3.75 | ne | 1 | 4.40 | 1 | 4.50 (poprecno) | IV000002 | 4.4 M2 | +0.00 |
| SA_016451 | IV CHAMPANGE UM 19 m | 13 | 21 | 12.69 | ne | 3 | 14.87 | 3 | 15.71 (uzduzno) | IV001157 | 15.12 M2 | +0.25 |
| SA_016452 | MDF BIJELI 3mm | 6 | 10 | 7.23 | ne | 2 | 8.76 | 2 | 8.68 (poprecno) | IV000054 | 8.76 M2 | +0.00 |

Ukupno ploče (bez RP/ZO): **PW 57.01 m² · Hub 59.85 m² · ponuda 57.26 m²**

**4. Trake** (PW "Kantiranje sortirano po dekorima" = Σ stranica × 1,10; rekonstruirano iz CPO PRT3):

| PW program | Materijal | Traka (naziv u nalogu) | PW metri | Ponuda (TR ident, m) |
|---|---|---|---|---|
| SA_016447 | IV BIJELI NK 18mm | 1-22 CHAMPAGNE UM | 37.2 |  |
| SA_016447 | IV BIJELI NK 18mm | 1-22 BIJELI NK | 10.3 |  |
| SA_016447 | IV BIJELI NK 18mm | MEL 0.5-22 BIJELI NK | 4.0 |  |
| SA_016447 | IV BIJELI NK 18mm | 2-22 BIJELI NK | 9.9 |  |
| SA_016449 | IV BIJELI NK 16 mm | MEL-ISTI | 12.7 |  |
| SA_016451 | IV CHAMPANGE UM 19 m | ABS-ISTI | 57.8 |  |

Stavke traka u ponudi: TR000168 ABS 1/22 BIJELI NK 11 m; TR001163 ABS 1/22 CHAMPAGNE OM/OF 19MM 38 m; TR000017 ABS 0,5/22 BIJELI NK 4 m; TR000016 ABS 2/22 BIJELI NK 10 m; TR000017 ABS 0,5/22 BIJELI NK 13 m; TR001163 ABS 1/22 CHAMPAGNE OM/OF 19MM 58 m

**5. Usluge u ponudi:** US000002 USLUGA REZANJA 28.98 M2; US000011 USLUGA KANTIRANJA 2/22 10.3 M; US000011 USLUGA KANTIRANJA 2/22 37.2 M; US000003 USLUGA KANTIRANJA 0,5/22 4 M; US000011 USLUGA KANTIRANJA 2/22 9.9 M; US000002 USLUGA REZANJA 4.4 M2; US000003 USLUGA KANTIRANJA 0,5/22 12.7 M; US000002 USLUGA REZANJA 15.12 M2; US000011 USLUGA KANTIRANJA 2/22 57.8 M; US000149 USLUGA P-BUŠENJA 35 MM 27 KOM; US000013 USLUGA REZANJA MDF 8.76 M2

**6. Okov u ponudi:** 6 stavki (ručni unos iz upita kupca — Hub ne računa, D-07/pravila §6)

## ROMIC_2423 — ponuda 26-010-002423

**1. Ulaz kupca** (sken rukom pisanog upita (PDF)): `20260910155417.pdf`

**2. Unos i exporti:** PPNEST zapisa (TXT) 0, nesting CSV 0 + CIX 0, CPW za PW 0, PW programa za pilu (CPO) 6, bNest rezultata nema

**3. Materijali kroz lanac** (nalog = PW program; obračun PW-metodom iz stabla rezova; Hub = vlastiti optimizator, D-19):

| PW program | Materijal | Elem. | Kom | m² dijelova | God | PW ploča | PW m² naplata | Hub ploča | Hub m² (način) | Ponuda ident | Ponuda kol. | Razlika ponuda−PW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SA_015891 | IV HR SONOMA 18mm | 1 | 1 | 1.34 | da | 1 | 2.08 | 1 | 2.08 (uzduzno) | IV000171 | 2.08 M2 | +0.00 |
| SA_015892 | IV BIJELI GL 10 mm | 1 | 1 | 1.38 | ne | 1 | 1.59 | 1 | 1.59 (poprecno) | IV000091 | 1.59 M2 | +0.00 |
| SA_015893 | IV HR SONOMA 25mm | 2 | 2 | 0.60 | da | 1 | 1.24 | 1 | 1.24 (uzduzno) | IV000351 | 1.24 M2 | +0.00 |
| SA_015894 | IV BIJELI NK 18mm | 1 | 2 | 0.40 | ne | 1 | 0.74 | 1 | 0.74 (poprecno) | IV000090 | 0.74 M2 | +0.00 |
| SA_015895 | MDF BIJELI 3mm | 1 | 2 | 0.36 | ne | 1 | 0.72 | 1 | 0.72 (poprecno) | IV000054 | 0.72 M2 | +0.00 |
| SA_015896 | RP HR SONOMA | 2 | 2 | 2.59 | da | 2 | 2.61 | 2 | 4.92 (uzduzno) | RP000068 | 4.41 M | D-37a (600 mm, po metru): elementi 2,01 + 2,30 = 4,31 m; +0,10 m u ponudi — provjeriti |

Ukupno ploče (bez RP/ZO): **PW 6.37 m² · Hub 6.37 m² · ponuda 6.37 m²**

**4. Trake** (PW "Kantiranje sortirano po dekorima" = Σ stranica × 1,10; rekonstruirano iz CPO PRT3):

| PW program | Materijal | Traka (naziv u nalogu) | PW metri | Ponuda (TR ident, m) |
|---|---|---|---|---|
| SA_015891 | IV HR SONOMA 18mm | 1-22 ISTI | 5.7 |  |
| SA_015892 | IV BIJELI GL 10 mm | 1-22 ISTI | 5.7 |  |
| SA_015893 | IV HR SONOMA 25mm | 1-22 ISTI | 4.2 |  |
| SA_015894 | IV BIJELI NK 18mm | mel-ISTI 22 | 2.8 |  |
| SA_015896 | RP HR SONOMA | 1-22 ISTI | 1.3 |  |

Stavke traka u ponudi: TR000358 ABS 1/22 HRAST SONOMA 48.6 m; TR000456 ABS 1/22 BIJELA GLATKA 5.4 m; TR000552 ABS 1/29 HRAST SONOMA 5 m; TR000017 ABS 0,5/22 BIJELI NK 2.8 m; TR000891 ABS 1/44 HRAST SONOMA 2 m

**5. Usluge u ponudi:** US000002 USLUGA REZANJA 2.08 M2; US000011 USLUGA KANTIRANJA 2/22 44.6 M; US000009 USLUGA - REZ 21 KOM; US000002 USLUGA REZANJA 1.59 M2; US000011 USLUGA KANTIRANJA 2/22 5.4 M; US000002 USLUGA REZANJA 1.24 M2; US000004 USLUGA KANTIRANJA 2/29 4.1 M; US000002 USLUGA REZANJA 0.74 M2; US000003 USLUGA KANTIRANJA 0,5/22 2.8 M; US000013 USLUGA REZANJA MDF 0.72 M2; US000303 USLUGA REZANJA RADNE PLOČE 4 KOM; US000012 USLUGA KANTIRANJA 2/44 1.3 M; US000005 USLUGA REZANJA CNC 0.17 M; US000006 USLUGA KANTIRANJA CNC 0.17 M

**6. Okov u ponudi:** 10 stavki (ručni unos iz upita kupca — Hub ne računa, D-07/pravila §6)


---

## Zaključak D-09 (ručna analiza, 11. 9. 2026.)

**Lanac prolazi za sva tri naloga.** Ulaz → nalog → export → rezultat → obračun je rekonstruiran iz datoteka bez ijedne rupe: elementi i sheme iz
PW CPO-a, ponuda iz Pantheon PDF-a, nesting rezultat iz bNest .mno (HUMER: `03_NESTING_APLIKACIJA\export_za_nesting\…\OUT\*.mno` —
IV BIJELI NK 18: **9 ploča** (PW 10), JELA TAVERNA: **5 ploča** (PW 6), iskorištenje 95,4 % / 88,2 %).

**Ploče (m² za naplatu):** Hubov kalkulator PW-metodom reproducira PW točno na svih 16 materijala (potvrđeno i na 4 PW PDF-a i na 40 stavki
ponuda svih 9 naloga: 23/40 identično, ostalo je +0,25 m² pravilo za načetu ploču ili ručna korekcija). Razlike ponuda − PW u ova tri naloga:
HRAST RELIEF +0,25 i CHAMPAGNE +0,25 (pravilo 1/3–2/3 iz `krojna-ponuda/pravila.md`), JELA TAVERNA +0,81 (zadnja ploča iskorištena 20 % →
pravilo "min 1/3 ploče" daje +0,75; ostatak 0,06 = ručno zaokruživanje). Hub će ta pravila primijeniti dosljedno i svaki dodatak označiti.

**Trake (metri):** PW metri = Σ stranica × 1,10 (točno rekonstruirano). Ponude **nemaju jedno pravilo**:
- BRATEK (Sanela, 2. 9.): traka = PW metri zaokruženi **na cijeli metar naviše** (37,2→38, 10,3→11, 9,9→10, 12,7→13, 57,8→58), usluga kantiranja = točno PW metri.
- HUMER (Ivana, 8.): traka 208,2→210, 21,8→23, 151,3→**180** (+19 %), 6,8→8, 6,6→8, 50,9→55; usluga = isto zaokruženo.
- Skill `krojna-ponuda` (pravilo iz kolovoza) kaže PW × 1,10 pa naviše — što je **drugi** 10 % na PW-ovih 10 % (HUMER 208→229 umjesto 210).
→ **Treba odluka (prijedlog D-20):** traka = PW metri (koji već sadrže 10 %) zaokruženo na cijeli metar naviše; usluga kantiranja = PW metri.
Time bi BRATEK bio identičan, a HUMER-ova ručna rezerva (180 vs 151) nestala — Igor da potvrdi ili zadrži drugačiju rezervu za pojedine trake.

**Vlastiti optimizator (Hub, D-19 izbor):** ROMIC identičan PW-u (6/6 materijala), BRATEK +2,84 m² (+5 %), HUMER +4,13 m² (+3,6 %, od toga
1 ploča više na bijelom 18 mm i 2,4 m² na MDF-u). Na svih 42 materijala testnih naloga (bez RP/ZO): PW 429,16 m² / 102 ploče, Hub 446,25 m² / 104
ploče (**+4,0 %**), 14 identičnih. To je stanje "jednostavnog" optimizatora (D-17 korak 2); PW-kvaliteta (D-16) je zaseban posao —
benchmark `skripte\benchmark_optimizator.py` ga mjeri automatski.

**Što u lancu radi ručno i Hub preuzima:** unos elemenata (danas PPNEST + PW dvaput), izbor načina optimizacije (D-19 automatski), mapiranje
naziva materijala/traka na Pantheon ident (aliasi: "taverna" = TR001254 ABS 1/22 JELA CLAY, "MEL-ISTI" na bijelom = TR000017 0,5/22…),
pravila +0,25 / min 1/3, zaokruživanje traka, usluge (rezanje = m² naplate, kantiranje = m po klasi trake, P-bušenje iz napomena).
Okov ostaje ručni unos (42 / 6 / 10 stavki).
