# 36 — Katalozi dobavljača (slike dekora i ABS trake): što imamo i što s tim možemo

**Datum:** 18. 9. 2026. · **Izvor:** `CLAUDE_COWORK\dekori\` (Igor, 18. 9.) · **Veza:** D-95 §8 (slike dekora), D-32 (trake), D-85 (nabava)
Ovo je analiza mape i prijedlog ugradnje. Kod se ne dira dok ne potvrdiš redoslijed.

## 1. Što je u mapi

| | |
|---|---|
| Zapisa dekora | **1 479** — Frischeis 556, Iverpan 499, Elgrad 424 |
| Slika | **2 002** (377 MB); medijan 110 KB, najveća 3,4 MB; preuzeto 1 474 od 1 479 |
| Kategorije | oplemenjena iverica / ploča, radne ploče i obloge, compact, MAT, akril i visoki sjaj, zidni paneli, furnirana, MDF / HDF |
| Blažić rubne trake | za **930 dekora (63 %)** predložena ABS traka: šifra, naziv, debljine, linija, cjenovna skupina, slika trake (528) i slika površine (85) |
| Ocjena podudaranja trake | odlično 560 · vrlo dobro 263 · dobro 47 · približno 60 |
| Proizvođači ploča (iz Blažićeve tražilice) | KAINDL 365, EGGER 266, KRONOSPAN 166, FUNDERMAX 118, ARPA 7, UNILIN 6, CLEAF 1 |
| Uz svaki zapis | poveznica na proizvod kod dobavljača, poveznica na sliku, kategorija, gdje postoji: šifra, proizvođač, debljina, dimenzije |
| Osvježavanje | `.bat` i `.py` skripte po dobavljaču — katalog se može ponovno preuzeti |

## 2. Koliko se toga veže na naše identе (izmjereno)

Vezanje po **kodu dekora** (`25727`, `K2737`, `U504 ST9`…):

| Naši materijali | Koliko ih dobije sliku |
|---|---|
| svi u šifrarniku (1 605) | 455 (28 %) |
| **u zadnjem Winstore izvozu (411)** | **197 (48 %)** |
| **na restlovima (340)** | **143 (42 %)** |
| oni koji uopće imaju kod dekora (1 114) | 455 (41 %) |

Vezanje po **nazivu** (Hubov prepoznavač, uzorak 300 zapisa): 28 % sigurno, 44 % s kandidatima za potvrdu, 28 % ništa.

**Zaključak:** otprilike polovica materijala koje stvarno koristimo dobiva sliku sama. Za dobar dio ostatka Hub može ponuditi kandidate, a potvrda je uz sliku brza (vidiš dekor, klikneš). Nešto jednostavno nije u ovim katalozima — npr. Eggerov `W908 ST2` i stariji Kronospanovi kodovi (`39345 BS`, `37710 BS`) nemaju zapis ni kod jednog od tri dobavljača; za njih ostaje slikanje uzorka.

## 3. Što s tim možemo — po korisnosti

### 3.1 Slika dekora u Hubu (najveća korist, najmanji rizik)
Slika uz materijal i uz restl: skladištar i ured dekor prepoznaju okom.
- **Gdje se vidi:** šifrarnik (sličica u popisu), dijalog materijala na unosu naloga, popis restlova, **skladištarev ekran i stranica restla** (tu je korist najveća), skladište i nabava.
- **Kako:** nova tablica `dekor_slika` (ident → datoteka, izvor, tko je potvrdio) i uvoz iz CSV-a: siguran pogodak po kodu upisuje se sam, ostalo ide na ekran „Dekori bez slike“ gdje ured bira između ponuđenih slika ili odbija.
- **Slike žive izvan koda i izvan Gita** (`C:\Paneli\Hub\dekori\`), Hub ih poslužuje umanjene (96 px u popisu, 480 px na klik).
- Posao: oko jednog dana za uvoz i prikaz, plus jedan prolaz ureda kroz potvrde.

### 3.2 Prijedlog ABS trake uz dekor (Blažić)
Za 930 dekora znamo koju traku proizvođač predlaže, s ocjenom podudaranja i slikom trake.
- Uz „zadanu traku“ materijala Hub pokaže **preporuku proizvođača** i sliku; ako se naša zadana traka razlikuje, to se vidi kao napomena, ne kao greška.
- Korist je najveća kad se otvara **novi dekor** (danas se traka bira ručno) i kao provjera postojećih 1 067 parova materijal–traka.
- Blažićeva šifra (npr. `A616C`) nije naš TR ident, pa Hub predlaže naš ident po dekoru — potvrđuje čovjek.

### 3.3 Dopuna šifrarnika
Iz kataloga dolaze podaci kojih u Pantheonu nema: **proizvođač ploče** (KAINDL, EGGER, KRONOSPAN, FUNDERMAX), **dostupne debljine**, dimenzije ploče i **poveznica na proizvod**. To ide u šifrarnik kao dodatni podatak (ne mijenja Pantheon) i odmah koristi uredu kad kupac pita „ima li to u 25 mm“.

### 3.4 Nabava
Katalog kaže **koji dobavljač uopće drži taj dekor** (Iverpan, Elgrad, Frischeis). Kad ident u Pantheonu nema dobavljača (D-85), Hub može predložiti dobavljača iz kataloga umjesto da stavka padne u „NEPOZNAT DOBAVLJAČ“.

### 3.5 Kasnije: ponuda i web katalog
Slike na ponudi kupcu ostaju isključene (D-95 §8) dok ne dobijemo dopuštenje dobavljača; isto vrijedi za javni web katalog (dokument 20).

## 4. Kako održavati

- Mapa ostaje izvor: skripte za osvježavanje već postoje, pa se katalog ponovno preuzme kad dobavljač doda dekore.
- Uvoz je idempotentan: isti zapis ne radi ništa, novi dekor otvara prijedlog slike, nestali dekor ostaje (slika se ne briše).
- Potvrde ureda se pamte — ponovni uvoz ih ne dira, kao kod restlova i aliasa.

## 5. Napravljeno 18. 9. (D-96)

* **Uvoz kataloga** `py -m hub.sifrarnici.dekori --uvoz <mapa>` (na VM-u `deploy\3_UVEZI_DEKORE.bat`): CSV → `dekor_katalog`, slike umanjene na 640 px u mapu izvan Gita (postavka `mapa_dekori`, zadano `C:\Paneli\Hub\dekori`). Ponavljanje je bezopasno — osvježava podatke, ne dira potvrde.
* **Vezanje:** isti kod i ista obrada → slika se upisuje sama; isti dekor s drugom obradom i poklapanje po nazivu (najmanje dvije zajedničke riječi) → uredu na potvrdu. Na stvarnim podacima: **432 materijala dobiva sliku odmah, 242 čeka potvrdu**; od onih u Winstoreu 48 % + 15 %.
* **Ekran ureda:** Šifrarnik → **Slike dekora** — kartica po materijalu s ponuđenim slikama, klik upisuje, „Nijedna ne odgovara“ miče iz ponude.
* **Gdje se slika vidi:** šifrarnik (sličica), popis restlova, stranica restla i skladištarev ekran. Na ponudi kupcu ne.
* **API:** `GET /api/dekor/slika/{ident}` · `GET /api/dekor/{ident}` (slika + kandidati + podaci kataloga) · `GET /api/dekori/za-potvrdu` · `POST /api/dekor/potvrdi` / `odbij` · `GET /api/dekori/katalog` · `POST /api/dekori/uvoz`. Shema v18, 180 testova.

Preostaje iz ovog dokumenta: prijedlog ABS trake uz dekor (3.2), dopuna šifrarnika (3.3) i dobavljač za nabavu (3.4) — podaci su već u `dekor_katalog`.

## 6. Što trebam od tebe

1. **Redoslijed:** prvo slike dekora (3.1), pa prijedlog trake (3.2), pa šifrarnik i nabava (3.3, 3.4)?
2. **Gdje slike žive na VM-u** — predlažem `C:\Paneli\Hub\dekori\` (izvan Gita, u noćnoj kopiji).
3. **Potvrde:** prolazi ured (Igor, 18. 9.).
