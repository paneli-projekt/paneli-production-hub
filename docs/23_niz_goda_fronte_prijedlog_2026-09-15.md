# Paneli Production Hub — 23: Fronte koje prate god (niz) — prijedlog označavanja i automatizacije

Igorova napomena 15. 9. 2026.: kod kupčevih krojnih lista i u vlastitoj proizvodnji nekoliko fronti u nizu često mora **pratiti sliku goda** —
god se nastavlja s jedne fronte na drugu, spoj na rubu. Dosad se reže **veći komad**, a operater na pili iz njega ručno reže fronte po skici.
Primjeri: `_HUMER_OMIS` (kupac) i `_ROMIC_Kuhinja` (Corpus).

## 1. Što primjeri pokazuju

**HUMER (kupčev PPW)** — kupac je u CPW poslao *veće komade* nazvane `skica 2` … `skica 6`, a fronte su na skici (`Ivana omis skica fronti.pdf`):

| Element u CPW-u | Mjere | Skica | Fronte u nizu (uz god) | Račun |
|---|---|---|---|---|
| skica 2 (×3) | 817 × 497 | sk 2 | 406 + 406 | 406 + 406 + **5** = 817 |
| skica 4 | 817 × 597 | sk 4 | 406 + 406 | isto |
| skica 5 | 2050 × 597 | sk 5 | 1227 + 406 + 406 | 1227 + 406 + 406 + 5 + 5 = 2049 → **2050** |
| skica 6 | 2650 × 1190 | sk 6 | 1050 / 675 / 100 / 820 … dva stupca (640 + 547) | zbrojevi + rez po rezu, zaokruženo |

Dakle veći komad = **zbroj fronti uz god + 5 mm po rezu (kerf pile), zaokruženo na cijeli mm naviše**. Naziv `skica N` je jedini trag u
datoteci; fronte, trake i CNC obrada tih fronti danas žive samo na papiru.

**ROMIC (Corpus, vlastita proizvodnja)** — fronte su u CSV-u i CIX-u **pojedinačno** (`FR3`, `FR4`, `FR5`, svaka sa svojim programom
`PROG 60e / 5ef / 5db`, `NAKOSITI 30ST`), a niz je na zasebnoj skici `pratiti god skica.pdf` (SKICA A: FR1 + FR2, 370 + 370 × 746; SKICA B:
FR3 + FR4 + FR5 = 183 + 183 + 370; SKICA C; SKICA D; SKICA E: FR11 + FR12 vodoravno). U datotekama niz **nije označen** — bNest bi te fronte
rasporedio po ploči kako mu odgovara i god bi se izgubio.

## 2. Prijedlog označavanja (D-70 PREDLOŽENO)

Jedna oznaka na elementu: **niz** = slovo grupe + redni broj u nizu, npr. `A1`, `A2`, `A3`; za dvodimenzionalne nizove (skica 6) redak/stupac:
`A1.1`, `A2.1` (drugi broj = stupac). Smjer niza je smjer goda (fronte jedna iznad druge; kod vodoravnog niza kao SKICA E: `E1`, `E2` s oznakom
smjera `→`). U Hubu su to dva polja elementa: `niz` (`A`) i `niz_rb` (`1`, `2` … ili `1.1`).

Kako oznaka ulazi u Hub, tri puta:

| Ulaz | Tko označava | Kako |
|---|---|---|
| Kupčev PPW (HUMER) | ured pri unosu | element `skica N` Hub prepozna po nazivu (`skica`, `sk`, `SKICA`) i otvori ga kao **niz**: ured upiše fronte (mjere sa skice) i njihove trake; veći komad Hub izračuna sam i **uspoređuje s kupčevim** (817 = 406 + 406 + 5 ✓; razlika → upozorenje) |
| Corpus (ROMIC) | tehnička priprema u Corpusu | **naziv elementa** dobiva sufiks, npr. `FR3 #B1`, `FR4 #B2`, `FR5 #B3` — Corpus ga prenosi u CPW (2. polje) i CSV (`IME DASKE`), Hub ga pročita i sam složi niz; nema više zasebne skice |
| Ručni unos | ured na ekranu 2 | označi 2–6 fronti → gumb „Prati god“ → Hub dodijeli slovo i redoslijed po redoslijedu klika; skica elementa pokaže niz kao stupac |

## 3. Što Hub tada radi sam (automatizacija)

1. **Veći komad („majka“)** za pilu: L = Σ visina fronti + kerf pile × (n − 1), zaokruženo naviše na mm (+ rezerva ako se dogovori, npr. 1 mm);
   W = širina fronti (ili Σ širina + kerf kod vodoravnog niza / stupaca). God majke = god fronti. Majka ide u CPO i na shemu kao jedan komad
   s napomenom `NIZ A (3 fronte)`; fronte se **ne** šalju na pilu ni u CSV za bNest.
2. **Skica niza za operatera** (PNG/PDF uz CPO, kao sheme iz dokumenta 19): majka s položajem svakog reza, mjerama fronti, oznakom `A1…A3`
   i programom (`PROG 5ef`) — zamjena za ručno crtanu skicu; ista slika ide na ekran uz materijal.
3. **Etiketa fronte**: `A2/3` uz naziv, da se nakon rezanja zna redoslijed (danas se to pamti napamet ili piše flomasterom).
4. **CNC obrada fronti** (Corpus): fronte zadrže svoje CIX-ove; Hub ih kopira u podmapu `NESTING\NIZ\` (nisu u CSV-u za nesting jer se ne nestaju,
   nego se program pokreće na Roveru na već izrezanom komadu — kako se, koliko razumijem, radi i danas s `PROG …`). Ako je praksa drukčija
   (fronte se ipak nestaju iz majke kao jednog „lista“ = restl), Hub može majku izvesti kao **restl-ploču** za bNest s frontama unutra —
   to je pitanje 3 dolje.
5. **Obračun**: materijal po majci (to se stvarno potroši), trake i kantiranje po frontama, CNC po frontama — ništa se ne gubi kao danas kad su
   fronte samo na skici.
6. **Nesting**: ako materijal niza ide na nesting, majka ide u CSV kao jedan komad (bNest je složi kao pravokutnik), fronte se poslije režu na
   pili iz majke po skici — isti postupak kao danas, samo s Hubovom skicom i etiketom.

## 4. Pitanja za Igora prije ugradnje

1. Kerf i rezerva: potvrđeno **5 mm po rezu** (HUMER: 817 = 406 + 406 + 5)? Dodaje li se još koji mm rezerve (2050 umjesto 2049 — zaokruživanje ili rezerva)?
2. Corpus: može li tehnička priprema pisati sufiks u nazivu elementa (`FR3 #B1`)? Ako ne, ostaje označavanje u Hubu na ekranu (jedan klik po nizu).
3. Fronte s CNC programom iz niza — danas se program pokreće na Roveru na izrezanoj fronti (pojedinačno), ili se majka nesta kao cjelina? Od toga ovisi točka 3.4.
4. Smjer goda: uvijek okomit na fronti (niz = fronte jedna iznad druge), a vodoravni niz (SKICA E) je iznimka koju treba označiti?
5. Etiketa: dovoljno `A2/3` uz naziv, ili operater želi i skicu niza otisnutu (A6 uz CPO)?

Ugradnja nakon odgovora: polja `niz` / `niz_rb` na elementu (shema v10), prepoznavanje `skica N` i sufiksa `#A1`, majka pri izvozu na pilu + skica niza,
etikete, obračun — otprilike jedan korak kralježnice (kao 3c).
