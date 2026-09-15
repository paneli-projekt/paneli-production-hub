# 15 — Izvoz na nesting: CSV + CIX za bNest (kralježnica, korak 3a)

**Datum:** 14.9.2026. · **Radi se o:** `hub/nalozi/export_nesting.py`, `POST /api/nalog/{id}/izvoz/nesting`
**Odluke:** D-23 (imena CIX datoteka), D-24 (Winstore kod u `SIFRA MAT`), D-60 (novo — kako izgledaju imena)
**Prethodi:** dokument 12 (nalog i elementi), dokument 14 (Corpus put)

---

## 1. Što ovo zamjenjuje

Danas PPNEST iz naloga složi listu elemenata i pošalje je bNestu: jedna CSV lista po materijalu i jedna
CIX datoteka po elementu, u mapu `<NALOG>\NESTING\`. To je jedini put kojim posao dođe do nesting stroja.

Hub sada radi isto, iz podataka koje nalog već ima — bez PPNEST-a. Mapa, imena datoteka i profil CSV-a
ostali su isti da bNest ne treba nikakvu izmjenu: uvozni profil koji operater već ima nastavlja raditi.

```
C:\PPNESTING\HUMER_OMIS_9\NESTING\
    HUMER_OMIS_9_IV_BIJELI_NK_18_140926_171152.CSV     <- lista elemenata za taj materijal
    H0000001.cix … H0000054.cix                        <- po jedna datoteka za svaki element
    HUMER_OMIS_9_IV_JELA_TAVERNA_AI_19_140926_171152.CSV
    H0000055.cix … H0000089.cix
```

Jedan materijal = jedan paket (CSV + pripadni CIX-evi). Tako je i u PPNEST-u, jer nesting reže jednu ploču
jednog dekora odjednom.

## 2. Provjera na stvarnom nalogu

Izvezen je **HUMER_OMIS_9** i uspoređen s onim što je za isti nalog izašlo iz PPNEST-a:

| Materijal | Winstore | Deb. | Elemenata | Komada | m² | Usporedba s PPNEST-om |
|---|---|---|---|---|---|---|
| IV BIJELI NK 18 | `W908ST2-18` | 18 | 54 | 177 | 50,97 | **ISTI ELEMENTI** |
| IV JELA TAVERNA AI 19 | `K2665AI-19` | 19 | 35 | 48 | 25,57 | **ISTI ELEMENTI** |

Uspoređene su mjere, količine i sve četiri oznake trake po elementu — nema nijedne razlike. Ukupno je
nastalo **2 CSV-a i 89 CIX datoteka** (91 datoteka).

CIX je provjeren i iznutra: `H0000001` ima `LPX=820 LPY=550 LPZ=18`, alat `TNM=8D` za 18 mm, `VTR=2`,
smjer `DIN=(0)+(-960)` — isto što piše u PPNEST-ovoj datoteci za taj element.

**Ponovni izvoz ne mijenja imena.** Drugi izvoz istog naloga ponovno je napisao `H0000001…H0000089`,
registar je ostao na 89 imena, brojač na 89. Operater može izvesti isti nalog koliko god puta bez straha
da će mu se brojevi razbježati.

## 3. Dvije stvari koje Hub radi drukčije nego PPNEST

### 3.1 Ime CIX datoteke je jedinstveno zauvijek (D-23, D-60)

PPNEST datoteku zove po vremenu (`ddmmyy_HHmmss`). Ako dva izvoza padnu u istu sekundu — ili se isti
nalog izveze dvaput — bNest stariju datoteku **pregazi bez pitanja**. To se već dogodilo.

Hub imena dijeli iz brojača: `H0000001`, `H0000002`, … Svako dodijeljeno ime upisuje se u tablicu
`cix_registar` i **nikad se više ne dodjeljuje drugom elementu**, ni kad se element obriše. Element koji
već ima svoje ime (Corpus ga daje, 14 heksadekadskih znamenki, D-55) zadržava svoje — Hub ga samo upiše
u registar i proslijedi. Ako bi dva elementa htjela isto ime, izvoz stane s jasnom porukom umjesto da
tiho pregazi datoteku.

Prefiks `H` postoji da se na prvi pogled vidi odakle je datoteka: `H…` = Hub, `140926_171152` = PPNEST,
dugi hex = Corpus. U istoj mapi mogu stajati sva tri i ne sudaraju se.

### 3.2 `SIFRA MAT` je Winstore kod (D-24)

PPNEST u to polje prepisuje tekst iz naloga, pa operater ploču traži ručno. Hub upisuje pravi Winstore
kod iz šifrarnika (`W908ST2-18`), pa bNest ploču nađe sam. Ako materijal nema kod, izvoz se **ne**
zaustavlja nego uz paket ispiše `PAZI: nema Winstore koda` — nalog mora moći van i dok ured dopunjuje
šifrarnik.

## 4. Što izvoz preskače i zašto

| Preskače | Razlog |
|---|---|
| materijal koji je voditelj poslao na pilu (`put = 'pila'`) | nesting ga ne reže (`--sve` ga ipak izveze) |
| materijal koji nije potvrđen | ne zna se koja je ploča, pa ni kod ni debljina |
| nepoznata debljina | CIX bez `LPZ` bNest ne može izrezati |
| deblje od 26 mm | nesting alat ne ide dublje (D-19) |

Preskočeno se ispiše uz razlog, ne nestane tiho. Ako ne ostane nijedan materijal, izvoz javi grešku s
popisom razloga.

## 5. Kako se pokreće

```cmd
py -m hub.nalozi.export_nesting --db hub.db --nalog 9 --mapa C:\PPNESTING
py -m hub.nalozi.export_nesting --db hub.db --nalog 9 --mapa C:\PPNESTING --suho
```

`--suho` samo pokaže što bi nastalo — ne dira ni disk ni bazu. To je ujedno ono što će ekran pokazati
prije nego voditelj pritisne „Pošalji na nesting“.

Iz aplikacije: `POST /api/nalog/9/izvoz/nesting` s `{"mapa": "C:\\PPNESTING", "suho": true}`.

Svaki izvoz se upiše u nalog: dokumenti (CSV i svaki CIX) u tablicu `dokument`, i jedan događaj u povijest
naloga — tko je izvezao, kad, koliko paketa i CIX-eva, u koju mapu.

## 6. Baza

Shema je na **v7**. Novo je samo `cix_registar` (ime, element, nalog, izvor, kad). Migracija je
automatska i pri podizanju upiše u registar sva imena koja elementi već imaju, pa registar od prvog dana
zna i za Corpusova imena.

## 7. Što slijedi u koraku 3

1. **CPW za PanelWizard** — da Hub i PW mogu raditi paralelno dok se ne prijeđe u potpunosti.
2. **CPO za pilu** — druga polovica izlaza; nesting i pila dijele isti nalog.
3. **Spajanje (D-54, korak B)** — spojeni posao je jedan CSV + CIX paket od više naloga; elementu mora
   ostati oznaka NJEGOVOG naloga (etiketa to već nosi).
4. **Čitanje rezultata natrag** — sheme iz CPO-a u PNG, stvarna potrošnja iz `.mno` i razdioba po
   nalozima (D-38).
