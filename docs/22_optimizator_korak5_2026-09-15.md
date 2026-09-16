# Paneli Production Hub — 22: Optimizator pile — korak 5 (D-17/3)

> **Druga runda (isti dan, na Igorov zahtjev „bar jednak učinak na ostalima“): Hub je sada na 45 materijala −3,6 % prema PW-u (422,76 vs 438,36 m², 103 vs 105 ploča), bolji na 30, isti na 14, slabiji na 1 (I_01970, +0,04 m²). Vidi §4.**

Stanje 15. 9. 2026. navečer. Jedina sustavna razlika Hubova obračuna prema PanelWizardu bila je optimizator: +3,9 % površine za naplatu
na 45 materijala testnih naloga (455,45 vs 438,36 m², 107 vs 105 ploča). Sada je **+0,9 %** (442,10 m², 106 ploča), a Hub je na 13 materijala
bolji od PW-a, na 18 isti i na 14 slabiji. Pravila obračuna (D-18/D-19) i CPO zapis nisu mijenjani — samo slaganje.

## 1. Što je dodano (`hub/optimizacija/pila_optimizator.py`)

Izbor po D-19 ostaje (svi dopušteni načini, vrijedi najmanja površina za naplatu); u „natjecanje“ su ušla tri nova kandidata:

1. **Kolone** (`slozi_kolone`) — traka je kolona čija se širina bira kao najbolja kombinacija do tri širine komada, a **orijentacija se bira po
   komadu** (bez goda), ne za cijeli nalog; traka se bira po popunjenosti (`fill`) ili po površini (`area`), uz do 3 nasumična starta kad
   komada nije puno. Ovo je najviše pomoglo kod MDF-a i mješovitih fronti (I_01842 7,54 → 7,08 — bolje od PW-a; I_02025 30,89 → 29,68).
2. **Best-fit** (`slozi_bf`) — kao dosadašnje slaganje, ali komad ide na **mjesto s najmanjim otpadom**, ne na prvo koje stane, i bira
   orijentaciju po komadu; tri redoslijeda × 4 starta. HUMER BIJELI NK 18 (177 komada): 58,98 / 11 ploča → **57,96 / 10 = PW**.
3. **Dotjerivanje zadnje ploče** (`dotjeraj_zadnju`) — načeta ploča odlučuje o korisnom ostatku, pa se njeni komadi presložе svim načinima i
   zadrži slaganje s najvećim ostatkom (I_01843 5,41 → 5,27, I_02090 → 9,74 = PW).

Vrijeme: većina materijala < 1 s; najveći (177 komada) 17 s, 93 komada 10 s. Za ekran obračuna to je granica — ako zasmeta, obračun može
dobiti „brzi“ način (stari kandidati) uz puni pri izvozu.

## 2. Brojke (`22a_benchmark_optimizator_2026-09-15.md`, `py -m hub.alati.benchmark_optimizator`)

| | PW | Hub prije | Hub poslije |
|---|---|---|---|
| Površina za naplatu, 45 materijala | 438,36 m² | 455,45 (+3,9 %) | **442,10 (+0,9 %)** |
| Ploče | 105 | 107 | **106** |
| Hub bolje / isto / slabije od PW-a | — | 5 / 17 / 23 | **13 / 18 / 14** |

Preostale veće razlike: I_01840 (28,98 vs 27,30 — PW zadnju ploču puni tanjim komadima i ostavlja 590 mm ostatka), SA_016447 (6 vs 5 ploča, 88 %
popunjenost — PW ima bolje mješanje 600-širokih komada), I_01914 MDF (19,13 vs 18,49). Obračun ponude (dokument 21) sada daje HUMER JELA TAVERNA
30,95 m² prema ponudi 30,97 (Hub našao malo veći ostatak).

## 3. Testovi

Postojeći testovi optimizatora i izvoza (CPO stablo rezova, `cpo_rw.validate`, provjera_exporta) prolaze nepromijenjeni; test obračuna vs ponuda
dopušta ±0,05 m² na JELA TAVERNA. Test šifrarnika: novi testni nalog `_ROMIC_Kuhinja` (Corpus) nosi materijal `AMBALAZA-19` — ispravno „za potvrdu“
(ambalaža nije roba, D-49). 109 testova prolazi.

## 4. Druga runda — što je otkriveno i promijenjeno (D-72)

Analiza 14 materijala na kojima je Hub bio slabiji pokazala je dvije stvari koje nisu bile u pravilima, nego u PW-ovim datotekama:

1. **PW slaže s fizičkim kerfom pile (5 mm), a ne s 16.** Na svih 45 CPO-a zbrojevi blokova u traci dodiruju granicu ploče točno s kerfom 5
   (višak 0,0 mm), a s 16 bi je premašili (do +28 mm). Korisni ostatak i naplata i dalje se računaju s 16 („Podesi alat“) — to je bilo
   ispravno reverzno izvedeno (05 §5.3) i ostaje. Hub je dosad slagao s 16 → gubio 11 mm po rezu. Sada: **slaganje s 5 mm, ocjena s 16**
   (`export_pila`, `obracun`, benchmark). To je najveći pojedinačni dobitak (HUMER BIJELI NK 18: 57,96 → 54,72 m²).
2. **PW koristi poprečnu shemu i za materijal s godom** (I_01843, PVC CRNI MAT, grain Y, obje sheme S): orijentacija komada ostaje uz god
   (duljina dijela uz duljinu ploče), pa god nije narušen. D-19 („s godom samo uzdužni načini“) opisuje što operater klikne, ne što je fizički
   dopušteno — Hub sada i s godom proba `poprecno`, a uzima ga samo ako je bolji.

Uz to: kolone biraju „širi“ ili „dulji“ prvi komad u traci (obje varijante u natjecanju — I_01841 = PW), pretraga po širinama traka za
zadnju ploču (DFS s budžetom 1–2 s, do 60 komada), premještanje komada zadnje ploče u rupe prethodnih, više startova za male naloge
(≤ 40 / ≤ 60 komada). Za velike naloge (> 120 komada) skup varijanti je ograničen — najdulji materijal 19 s, svih 45 ukupno 106 s.

| | PW | Hub prije koraka 5 | Hub prva runda | **Hub druga runda** |
|---|---|---|---|---|
| Površina za naplatu, 45 materijala | 438,36 m² | 455,45 (+3,9 %) | 442,10 (+0,9 %) | **422,76 (−3,6 %)** |
| Ploče | 105 | 107 | 106 | **103** |
| Hub bolje / isto / slabije | — | 5 / 17 / 23 | 13 / 18 / 14 | **30 / 14 / 1** |

Jedini preostali: I_01970 (4,40 vs 4,36 — PW-ov uzorak ima rez razine 5, koji CPO writer Huba ne piše). Obračun ponude na HUMER-u sada daje
manje m² od ponude (JELA TAVERNA 30,91 vs 30,97; BIJELI NK 18 −6 %) — Hub je u tim slučajevima štedljiviji od PW-a, što u ponudi znači manje
naplaćenog materijala; ako ured želi zadržati stare količine, obračun ima pravilo načete ploče i ručnu korekciju, a razlika je vidljiva u benchmarku 21a.

## 5. Treća runda (16. 9. 2026.) — smjer po ploči, seljenje u novu traku, granica pretrage

Igor: „ako misliš da možeš još izbrusiti optimizator, pokreni još jednu rundu“. Tri promjene u `pila_optimizator.py`, sve unutar D-19 izbora:

1. **Smjer po ploči (`slozi_kolone_mix`)** — PW unutar jednog posla miješa uzdužnu i poprečnu shemu (I_02024: L, L, S, L). Hub je dosad
   birao smjer za cijeli nalog; sada za svaku novu ploču složi prvu ploču obje sheme na preostalim komadima i zadrži onu koja na tu ploču
   stavi više površine. Računa se samo prva ploča (ne cijeli ostatak), pa je kandidat ~40 % jeftiniji nego u prvoj probi uz isti rezultat.
2. **Nova traka u ranijoj ploči** — pri dotjerivanju zadnje ploče komad se dosad selio samo u postojeću rupu prethodnih ploča; sada može
   otvoriti i novu traku u ranijoj ploči ako tamo ima mjesta po širini.
3. **Granica pretrage širina** — kombinacije širina traka (do tri komada) su bez ograničenja do 120 komada u nalogu; iznad toga 30 najčešćih
   širina / 200 kandidata po traci. Prijašnja granica (14 / 48, brojana po orijentacijama pa je hvatala i naloge od 130 komada) na HUMER-u
   je koštala 0,8 m²; nova daje na I_01913 (174 komada) 54,69 m² u 5–13 s umjesto 54,72 u 19 s.

**Brojke (22a, svih 45 materijala):** PW 438,36 m² / 105 ploča — Hub **421,76 m² / 103 ploče (−3,8 %)**, bolje 30 / isto 14 / slabije 1
(i dalje samo I_01970, +0,04 m²). Prema drugoj rundi **−1,00 m² (−0,24 %)** na četiri materijala: I_01840 26,38 → **26,03**, I_02094 24,56 → **24,07**,
I_01915 29,49 → **29,36** (sva tri `mix`), I_01913 54,72 → **54,69**. Na materijalima na kojima miješani smjer pomaže dobitak je 0,5–2 %, na ukupnom
zbroju četvrt postotka — ispod praga od pola posto koji sam si postavio, pa ostaje po odluci, ne po brojci: **zadržan je**, jer nakon ubrzanja
košta 25–40 % vremena samo na velikim nalozima (I_01840 93 komada ≈ 22 s, I_02025 77 komada ≈ 27 s na VM-u s 2 jezgre; mali nalozi nepromijenjeno
< 1 s) i jer je to točno PW-ovo ponašanje koje je dosad nedostajalo.

**Gdje odlazi vrijeme:** po traci se ocjenjuje 350–630 kandidat-širina po 0,2 ms — ne pojedini algoritam nego širina pretrage; svako grubo rezanje
te pretrage (probano 30 / 200 na svima) vraća 0,5–0,7 m² na I_01840 i I_02094. Jeftin izlaz kad zatreba: kandidati paralelno po jezgrama (I-17).

**Zaključak:** optimizator je time za sada zaključen (D-74). Sljedeći dobitak nije u slaganju nego u onome što CPO writer ne zna: rez razine 5
(I_01970) i nizovi goda (D-70). Regresija = 22a; u paralelnom razdoblju (D-73) mjerilo su stvarni nalozi. 109 testova prolazi.
