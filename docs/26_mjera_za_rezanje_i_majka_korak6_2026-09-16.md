# Paneli Production Hub — 26: Mjera za rezanje i majka (korak 6 — D-70 niz goda, D-79 lijepljenje, D-80 mali komadi)

Stanje 16. 9. 2026. navečer. Jedan mehanizam za tri Igorove odluke od 15./16. 9.: element sada ima **konačnu mjeru** (po njoj idu trake,
kantiranje i etiketa) i **mjeru za rezanje** (po njoj se slaže ploča, pišu CPO / CSV / CIX i naplaćuje materijal), a Hub sam radi
**majku** — veći komad koji ide na stroj umjesto svojih članova — za fronte koje prate god i za male komade koje kanterica ne prima.
Shema **v11**, novi modul `hub/nalozi/grupe.py`, **127 testova prolazi** sa stvarnim podacima (10 novih u `tests/test_grupe.py`).

## 1. Model (shema v11)

| Gdje | Što | Čemu služi |
|---|---|---|
| `element.L`, `element.W` | **konačna mjera** (kako je i bilo) | trake, kantiranje, CNC, etiketa člana, statistika |
| `element.rez_L`, `rez_W`, `rez_razlog` | **mjera za rezanje**; `NULL` = ista kao konačna; razlog `suziti` (D-80) ili `sloj` (D-79) | pila, nesting, PW, optimizacija, m² materijala, krojni nacrt |
| `element.vrsta` | `element` (pravi) ili `majka` (veći komad koji je Hub sam napravio) | na stroj idu pravi elementi bez majke + element-majke |
| `element.majka_id`, `majka_poz` | član majke / sklopa i položaj u njoj (`A2`, `C1-2`, sloj `1` / `2`, `clan`) | skica, etiketa, obračun |
| `element.niz` | oznaka niza goda `A1` / `E1H` / `C1-2` (iz sufiksa naziva ili s ekrana) | izvor za majku niza |
| `element.ljepljenje` | sloj sklopa `A1` / `A2` (iz sufiksa `_LA1` ili Corpusovog stupca `LJEPLJENJE`) | izvor za sklop |
| `element.napomena_rez` | što Hub dodaje na etiketu: `SUZITI NA 120`, `LA1/2>930x340`, `A2/3`, `M1 15x600x120`, `IZ M1` | etiketa (14 znakova, D-38 / D-78) — ima prednost pred napomenom |
| tablica `majka` | vrsta `niz` / `mali` / `lijepljenje`, oznaka, smjer, mjera, debljina sklopa, kerf, članovi, `skica_json`, `provjeri` | grupa; `element_id` = element-majka (niz, mali); sklop nema element-majku |

Sve je izvedeno iz podataka elemenata (naziv, `niz`, `ljepljenje`, rubovi, mjere), pa je `grupe.primijeni(conn, nalog_id)` **idempotentno**:
obriše automatske majke i složi ih iznova. Poziva se sam pri svakom uvozu (CPW / CSV / Corpus paket — jednom na kraju), pri ručnom dodavanju,
uređivanju i brisanju elementa, i na zahtjev (`POST /api/nalog/{id}/grupe`, `py -m hub.nalozi.grupe --db hub.db --nalog N`). Radi samo u
statusima unos / ponuda (D-65/2) — nakon potvrde kupca mjere su ono što je otišlo na ponudu.

**Jedno mjesto za „što ide na stroj“:** `nalozi.elementi_za_export()` sada vraća mjeru za rezanje kao `L` / `W` (konačna je u `L_kon` / `W_kon`),
element-majke umjesto članova i slojeve lijepljenja na sirovu mjeru — pa izvoz na pilu, nesting i PW, optimizacija s potvrdom, hash elemenata
i krojni nacrt rade ispravno **bez ijedne izmjene u njima**. Za trake, kantiranje i CNC postoji `nalozi.elementi_konacni(nm_id)` — svi pravi
elementi (i članovi) s konačnom mjerom; obračun i krojni nacrt koriste njega.

## 2. D-80 — mali komadi (kanterica: rub ≥ 150 mm, širina ≥ 60 mm)

Pravilo `grupe.pravilo_malih(L, W, kant_L, kant_W)`: rub koji se kantira mora biti dug barem 150 mm, a druga mjera (širina kroz kantericu)
barem 60 mm. Sve što ne prolazi dobiva mjeru za rezanje **150** odnosno **60** i etiketu `SUZITI NA <konačna>` (`SUZITI 100x40` kad obje).
Vrijedi za ručni unos, kupčev PPW, PPNEST CSV i Corpus (Corpus daje točnu mjeru, nadmjeru dodaje Hub — Igor, 2. krug).

**Majka:** 4 i više ISTIH komada (mjere, sve četiri trake, god) kantiranih po kraćoj strani < 150 mm grupiraju se u majku
`l × (n·s + (n−1)·kerf pile)`: dugi rubovi majke su zbroj kratkih rubova komada i **kantiraju se na majci** (element-majka nosi te dvije trake),
pa se majka reže na komade, a komadi se po svojim dugim rubovima kantiraju kao dosad. Jedna majka dok stane u ploču minus obrez (s godom:
poprijeko goda uz širinu ploče 2050 mm, uz god 2780), inače više majki s podjednakim brojem komada (7 → 4 + 3, 30 → 15 + 15; na ploči 1220
30 × 120 → 8 + 8 + 7 + 7). Komad uži od 60 mm koji se kantira i po dugoj strani ne ide u majku (majka mu ne pomaže) nego pojedinačno na 60.
Članovi s CNC programom → majka `provjeri` s napomenom (obrada na komadu nakon rezanja iz majke).
Etiketa majke `M1 15x600x120`, člana `IZ M1`; skica majke (PNG uz CPO / CSV + stranica „Majke i sklopovi“ u krojnom nacrtu).

**Corpusov CIX (D-80, 2. krug):** element s programom čija je mjera za rezanje veća od konačne dobiva pri izvozu **kopiju CIX-a s povećanim
`LPX` / `LPY`** (`grupe.kopiraj_cix_prosiren`) — ishodište ostaje, obrade ostaju na mjestu, višak je na strani suprotnoj od ishodišta; ako element
ima i drugi CIX (bušenje u kant) izvoz javi „PROVJERITI program na produženom rubu“. CIX-ovi članova majki (fronte, komadi) ne idu u CSV
(režu se iz majke) nego u podmapu `NESTING\NIZ\` odnosno `NESTING\MAJKA\` — program se pokreće na Roveru na izrezanom komadu.

**Na stvarnim nalozima (9 testnih):** BLAGO 3, BOGDANIC 3, BRATEK 3, HUMER 11–14, MAZUR 5, VARGA 6 komada dobiva `SUZITI NA`; HUMER dobiva
jednu majku (5 × 817 × 140 → 817 × 720). **Nalaz:** kupčevi PPW-ovi već sadrže RUČNU nadmjeru — element nazvan `114X560` upisan je kao
140 × 560, `90X600` kao 140 × 600, `2630X100` kao 2630 × 140 — priprema je dosad povećavala u glavi, pa Hub sada za takve elemente javi
„naziv izgleda kao konačna mjera — nadmjera je već dodana ručno? upisati konačnu mjeru“. Kad ured upiše konačnu (114 × 560), Hub sam reže 150
i etiketira `SUZITI NA 114`.

## 3. D-79 — sklop lijepljenja

Sloj se prepoznaje iz sufiksa naziva `_LA1` / `_LA2` (kupčev PPW, ručni unos — upisana mjera je SIROVA, konačna = − 10 mm; `=930x340` u nazivu
se samo provjeri) ili iz Corpusovog paketa (CSV stupac `LJEPLJENJE` 1 / 2 + isti `NAZIV ELEMENTA` + ista `KONACNADIMENZIJA`; sloj bez CSV retka
iz CPW naziva `,(I) (37)#: 1465.00 x 600.00` i `top_12`). Hub tada:

* slojeve reže na sirovu mjeru (`rez_razlog = sloj`), konačna mjera ostaje u `L` / `W`;
* **kant skida sa slojeva 2+** (Corpus ga stavlja na oba — to je bila ručna korekcija u PW-u) i ostavlja ga na sloju 1 = sklopu, s klasom trake po
  Σ debljina slojeva (`prepoznaj_traku(…, debljina=37)` → širina 44: ≤ 20 → /22, 25 → /29, > 30 → /44; `sirina_za_materijal` sada ima granicu 20,5 mm);
* obračun: ploče po sirovoj mjeri svakog sloja na svom materijalu, trake po konačnoj mjeri sklopa, kantiranje po klasi (/44 → US000012),
  **`US000007 USLUGA LJEPLJENJA PLOČA` × m² sirove mjere jednog sloja × kom**, rez na konačnu mjeru se ne naplaćuje;
* etiketa sloja `LA1/2>1465x600` (14 znakova, sadržaj kao na dosadašnjoj bSolid etiketi).

**Stvarni uzorak `_CORPUS_UZORAK\LIJEPLJENJE\NESTING\TEST LJEPLJENJE NK`** (test `test_stvarni_corpus_lijepljenje`): sloj 1 CHAMPAGNE 19
(`27045BS-19` → IV000017) + sloj 2 BIJELI NK 18 (`W908ST2-18` → IV000090) → sklop 37 mm, konačna 1465 × 600, sirova 1475 × 610, sloj 1 traka
`TR000850 ABS 1/44 CHAMPAGNE` (klasa 1/44, bez potvrde), sloj 2 bez kanta; ponuda: US000007 0,90 m², TR000850 5 m (4,54), oba sloja na nesting
1475 × 610. Uvoz Corpusa sada nalazi CPW-ove i u `…\PW\<PROJEKT>` uz `…\NESTING\<PROJEKT>` (raspored uzorka).

## 4. D-70 — niz goda

Sufiks naziva po 23 §5 (`FR1_A1`, `FR11_E1H`, `FR20_C1-2`; regex `_[A-Z][0-9]+(H|-[0-9]+)?$`) puni `element.niz`; ista oznaka može se upisati
i na ekranu (`PUT /api/nalog/element/{id} {niz}`). Majka niza: okomiti niz L = Σ visina + kerf pile × (n − 1), W = najšira fronta; vodoravni
(`H`) W = Σ širina + kerf; mreža (`red-stupac`) po redovima i stupcima. HUMER skica 2: 406 + 406 + 5 = **817** ✓. Element-majka `NIZ A (2 fronte)`
ide na pilu / nesting bez kanta, fronte ostaju s trakama i CNC-om, etiketa fronte `A1/2`, majka `NIZ A (2)`. Provjere: brojevi 1..n bez rupa,
ista količina, majka stane u ploču — inače `provjeri` s napomenom. Skica niza (PNG + stranica krojnog nacrta) pokazuje položaj svake fronte.

**Kupčev PPW (`skica 2` = već veći komad):** uvoz javi „kupčev veći komad s frontama na skici“; ured upiše fronte kroz
`POST /api/nalog/element/{id}/niz {fronte:[{L, W, rubovi}], smjer}` (`grupe.niz_iz_kupceve_majke`) — Hub otvori fronte kao članove niza, kupčev
element zamijeni svojom majkom i **usporedi mjeru**: 817 = 406 + 406 + 5 prolazi, skica 5 (2050 prema 1227 + 406 + 406 + 10 = 2049) daje
upozorenje „provjeriti skicu“. Elemente `SKICA NUT …` (CNC napomena, HUMER) Hub ne dira.

**Prijedlozi za tri otvorena pitanja D-70 (D-81, PREDLOŽENO):** (a) bez rezerve uz kerf — majka = Σ + 5 mm po rezu; kupčeva veća mjera se
javi, ne preuzima; (b) fronte s CIX-om: majka na pilu / nesting kao pravokutnik, CIX fronti u `NESTING\NIZ\` za Rover; (c) etiketa `A2/3` +
skica u krojnom nacrtu.

## 5. Što se promijenilo u postojećim modulima

| Modul | Izmjena |
|---|---|
| `nalozi.py` | `dodaj_element(niz, ljepljenje, konacna, grupe)`, `uredi_element(niz, ljepljenje)` (sloj vraća sirovu mjeru kad se oznaka makne), element-majka se ne uređuje ni ne briše ručno, `element()` daje `rez_L/rez_W`, `m2_rez`, etiketa s prednošću `napomena_rez`; `elementi_za_export` = stroj, `elementi_konacni` = trake; `pregled()` ima `grupe` i `majke` po materijalu |
| `prepoznaj_traku(…, debljina=)`, `nazivi.sirina_za_materijal` | klasa trake po debljini sklopa; granica /22 pomaknuta s 19,5 na 20,5 mm (D-79) |
| `nalog_io.read_ppnest_csv` | čita `LJEPLJENJE` i `KONACNA DIMENZIJA` |
| `uvoz_datoteka`, `uvoz_corpus` | prosljeđuju sloj i konačnu, primijene pravila jednom na kraju; Corpus slova sklopa A, B… po (naziv elementa, konačna) |
| `obracun.py` | trake / kantiranje / CNC po `elementi_konacni`, `US000007` po sklopu |
| `export_nesting.py` | kopija CIX-a s povećanom mjerom, CIX-ovi članova u `NIZ\` / `MAJKA\`, skice majki uz CSV, ispis majki i suženih |
| `export_pila.py` | skice majki uz CPO (`HUB_00001_MAJKA_M1.png`), ispis majki i suženih |
| `ispis/krojni.py` | trake po konačnim elementima, napomena „SUZITI NA 120 · konačna 600 × 120“, stranica **„Majke i sklopovi“** (skica + članovi) |
| API | `GET/POST /api/nalog/{id}/grupe`, `POST /api/nalog/element/{id}/niz`, `GET /api/majka/{id}/skica.png`, `PUT element {niz, ljepljenje}` |
| `db.py` | migracija v11 (stupci elementa; tablica `majka` iz schema.sql) |

Probe za pregled: `docs/sheme_proba/krojni_proba_majke.pdf` (4 stranice: list, statistika, majke), `majka_proba_M1.png`, `majka_proba_LA.png`,
`majka_proba_A.png`. Uz to je popravljen test `test_mail_ponuda::test_postavke_i_lozinka` (tražio je lozinku u radnoj mapi umjesto uz bazu).

## 6. Otvoreno / za Igora

1. D-81 (a)–(c) gore — potvrditi ili ispraviti.
2. Kupčevi PPW-ovi s ručnom nadmjerom (`114X560` → 140 × 560): dogovoriti s kupcima / uredom da se upisuje konačna mjera; Hub javi sumnju.
3. Majka malih komada radi samo za ISTE komade (iste trake); komadi iste mjere s različitim trakama idu pojedinačno — namjerno (kant na majci mora biti jedan).
4. Ekrani: kućica „niz“ / „sloj“ uz element i dijalog „fronte za skicu N“ ulaze u web ekran 2 (API postoji).
