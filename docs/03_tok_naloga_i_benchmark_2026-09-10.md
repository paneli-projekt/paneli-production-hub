# Paneli Production Hub — audit 3/4: tok naloga danas i benchmark 9 testnih naloga

Stanje 10. 9. 2026. Brojke su iz `20_ANALIZA\benchmark_nalozi.csv` (generira `skripte\benchmark_nalozi.py` iz CPO / PPNEST CSV / bNest MNO / Pantheon PDF).

## 1. Tko što radi danas (rekonstruirano iz datoteka; Igor potvrđuje)

1. **Ulaz** — kupac šalje CPW (PPW), Excel, fotografiju rukopisa ili skenirani PDF; okov na istom papiru ili u Excelu.
2. **Unos** — administrator (IVANA / GORAN po ponudama; "IVANA" je i operater u PW-u) prekucava u **PPNEST** (kupac, nalog `PREZIME_BROJ`, materijal, šifra ploče, elementi s 4 ruba, napomene). PPNEST sprema TXT i izvozi **CSV+CIX** (nesting) i **CPW** (PanelWizard). Kod CPW ulaza iz PPW-a nije jasno prekucava li se ili se CPW učitava u PW izravno (pitanje).
3. **Pila** — PW učitava CPW, optimira, tiska krojnu PDF (po materijalu) i šalje `.cpo` u OSI; program dobiva broj `I_0xxxx`/`SA_0xxxxx`. Etikete printa pila.
4. **Nesting** — CSV+CIX se učita u bNest, rezultat `.mno` + `.bSolid` po ploči; etikete Zebra ZT411 iz bSolida.
5. **Ponuda** — iz krojnih PDF-ova ("Površina za naplatu", metri kantiranja po dekoru) i popisa okova ručno (ili skill krojna-ponuda) u Pantheon; broj ponude `26-010-00xxxx` (od 2423 u lipnju do 3258 početkom rujna ≈ 12 ponuda radno-dnevno — poklapa se s 10–15 naloga/dan).
6. **Odluka pila/nesting** — voditelj proizvodnje, nakon što su oba exporta napravljena (isti nalog prolazi obje pripreme).

Posljedica: isti nalog se **priprema dvaput** (PPNEST + PW), broj ploča za naplatu dolazi iz PW-a čak i kad se reže na nestingu, a nesting rezultat (.mno) se nigdje ne knjiži.

## 2. Testni nalozi — pregled

| Nalog | Ponuda | Materijala (CPO) | Elemenata | m² dijelova | Ploča (pila) | Tip ulaza | Napomena |
|---|---|---|---|---|---|---|---|
| HUMER_OMIS | 26-010-002823 (76 st.) | 6 | 280 | 103,1 | 24 | CPW (PPW) + skice + Excel okova | jedini s bNest rezultatom (2 materijala) |
| BLAGO_ADRIJANA | 26-010-002929 (63 st.) | 8 | 159 | 53,6 | 18 | foto rukopisa | ponuda počinje od rb 3 — vidi §4 |
| BOGDANIC_IVA | 26-010-003217 (52 st.) | 5 | 158 | 56,7 | 15 | foto rukopisa (3 str.) | |
| MAZUR_16 | 26-010-003258 (28 st.) | 7 | 186 | 57,9 | 18 | foto rukopisa | PW nalog dva puta izvezen (04.09 i 10.09) |
| VARGA_POTNJANI | 26-010-003213 (35 st.) | 7 | 129 | 33,9 | 11 | foto rukopisa | |
| BRATEK_KUPAC1 | 26-010-003231 (27 st.) | 4 | 118 | 49,3 | 11 | Excel kupca (NARUDŽBA + OKOV) | ponuda: G. Spajić |
| TURALIJA_TUKA | 26-010-002924 (28 st.) | 5 | 43 | 12,7 | 7 | sken rukopisa PDF | 5 materijala, sve ≤ 2 ploče |
| ROMIC_NALOG | 26-010-002423 (35 st.) | 6 | 10 | 6,7 | 7 | sken rukopisa PDF | "problematičan" tip: 6 materijala, 1–2 dijela svaki |
| BLAGO_JASA | 26-010-003166 (18 st.) | 2 | 32 | 6,0 | 2 | foto rukopisa | najmanji |

Ukupno: 50 CPO datoteka, 1.115 elemenata, 379,7 m² dijelova, 113 ploča (587,9 m² bruto) → **bruto iskorištenje 64,6 %**, 1.839 rezova.

## 3. Benchmark pila vs. nesting vs. ponuda

### 3.1 Iskorištenje ploča po veličini serije (pila, iz CPO)
- 11 materijala s ≥ 4 ploče: prosjek **75,6 %** (najbolje BRATEK 18 mm 88,3 %, HUMER 18 mm 86,9 %).
- 25 materijala ide na **jednu ploču**, od toga 16 s iskorištenjem **< 50 %** (ROMIC 6–24 %, TURALIJA 12–31 %). Na tih 16 ploča ostaje ≈ **70 m² ostatka** (12 cijelih ploča) — to je materijal koji danas živi samo u Excelu restlova.
- PW "Iskorištenje" po listu (npr. 99,26 %) računa se **bez korisnog ostatka** — nije usporedivo s bNestom (88,2 % stvarno). Za benchmark koristiti CPO (dijelovi / bruto ploče) i .mno (PartUsedArea / ploča).

### 3.2 Pila vs. nesting na istom nalogu (HUMER, jedini s .mno)
| Materijal | Elemenata | Pila (PW → CPO) | Nesting (PPNEST → bNest .mno) |
|---|---|---|---|
| IV BIJELI NK 18 (W908ST2-18) | 174 (nest 177) | **10 ploča**, 86,9 % | **9 ploča**, 49,8 m² iskorišteno = 95,4 % |
| IV JELA TAVERNA 19 (K2665AI-19) | 48 | **6 ploča**, 73,5 % | **5 ploča**, 88,2 % (po ploči 94,9 / 93,8 / 93,2 / 92,1 / 67,2 %) |

Nesting je na oba materijala uštedio **1 ploču** (10 %, resp. 17 %). Razlika u broju elemenata (174 vs 177) i CNC napomene ("CNC SKICA NUT ZA GOLU") upućuju da se dio elemenata dodaje/mijenja u PPNEST-u nakon PW-a — provjeriti.

### 3.3 Naplaćeno vs. izrezano
Za 40 uparenih stavki: naplaćeno m² / m² dijelova = **1,13 – 2,07, medijan 1,26**; naplaćeno / bruto ploče = 0,12 – 1,00.
Pravilo je PW-ovo "Površina za naplatu" (bruto ploče minus korisni ostatci > 400 mm × > 400 mm i > 1 m²) ± ručno zaokruživanje:
HUMER 18 mm 57,96 = 10 × 5,796 (cijele ploče), JELA TAVERNA 30,97 vs PW 30,16, ROMIC 25 mm 1,24 m² za 0,60 m² dijelova (jedna ploča 5,8 m²).
Trake: PW daje metre po dekoru (JELA TAVERNA: 151,3 m ABS-ISTI, 6,8 m 1/44), ponuda 180 m + 8 m (≈ +19 %).
→ Hub mora reproducirati upravo ove brojke (obračun iz skilla `krojna-ponuda`, `references/pravila.md`), a ne "točnije" — inače se ponude mijenjaju.

## 4. Nalazi koje treba provjeriti (potencijalne greške u današnjem procesu)
1. **Ponuda 26-010-002929 (BLAGO ADRIJANA) počinje od rb 3** — stavke 1 i 2 su obrisane; u nalogu su izrezane **5 ploča IV BIJELI NK 18 mm (24,1 m² dijelova)** koje se u ponudi ne pojavljuju (ni ident IV000090 ni USLUGA REZANJA za njih). Ili je naplaćeno drugom ponudom / kupac donio ploče, ili nije naplaćeno. Ovo je točno tip pogreške koju Hub uklanja (obračun iz naloga, ne iz PDF-a).
2. PanelWizard PDF: "Debljina reza: 16 mm" (kerf u CPO je 5 mm) — kriva postavka ispisa ili optimizacije.
3. Dva različita niza programa za pilu (`I_` i `SA_`) i dva PW naloga za isti materijal (MAZUR 18 mm: 04.09. i 10.09., identični) — nema jedinstvenog ID-a naloga koji veže PPNEST nalog, PW program, bNest projekt i ponudu; danas ih veže samo ime `PREZIME_BROJ`.
4. Nazivi materijala nisu normirani: `IV BIJELI NK 18MM`, `IV_BIJELI_NK_18_MM`, `IV BIJELI NK 18mm`, `IVERAL BIJELI NK W908 ST2 18 MM` (Pantheon), `W908ST2-18` (šifra ploče) — svaki sustav svoj tekst; u `hub_ploce.csv` (Pantheon) 1.612 identa ploča. Hub treba jednu tablicu materijala s aliasima (Pantheon ident ↔ šifra proizvođača ↔ PW/PPNEST tekst).
5. PW baza materijala i traka je prazna → sve se piše rukom po nalogu (izvor tipfelera "CHAMPANGE", "KAMIR").
6. Kod HUMER-a su za isti materijal dva PPNEST exporta (082944 i 083204) i "New" PW datoteke u nesting mapi — ostaci ponavljanja; Hub treba verzionirati nalog, ne datoteke.

## 5. Što od ovoga Hub preuzima kao "ground truth" za fazu 1
- Element i nalog: model iz PPNEST CSV-a (28 stupaca) proširen Pantheon identom, jedinstvenim ID-om i fazom.
- Rezultat pile: parsiranje CPO-a (broj ploča, sheme, rezovi) — dok Hub nema svoj optimizator, PW ostaje "engine", a Hub ga čita.
- Rezultat nestinga: parsiranje .mno (ploče, iskorištenje, pozicije) → restlovi s nestinga.
- Obračun: pravila iz `krojna-ponuda`, kontrola "svaki materijal u nalogu ima stavku u ponudi" (spriječilo bi nalaz 4.1).

## 6. Dopuna 11. 9. 2026. (Igor) — što pila stvarno reže i čemu služi PW

Pila Sektor 450 danas reže uglavnom **MDF 3 mm, radne ploče, zidne obloge, compact ploče, restlove i male naloge (ispod jedne pune ploče)**; sve ostalo ide na nesting.
Svaki nalog ipak prolazi kroz PanelWizard — ne radi rezanja, nego da se dobiju **količine za obračun**: m² materijala + usluga rezanja, metri trake + usluga kantiranja, koje se unose u Pantheon.
Posljedice za nalaze iznad: (1) PW je u praksi **kalkulator količina za ponudu**, optimizator pile samo za mali dio naloga; (2) benchmark "pila vs nesting" (HUMER 10→9, 6→5 ploča) nije
usporedba dva stroja nego usporedba *naplaćene* količine (PW) i *stvarne* potrošnje (bNest) — razlika je marža koju danas nitko ne vidi; (3) pitanje 8 iz 04 je odgovoreno pravilom po
materijalu/veličini, što Hub može automatizirati odmah.
