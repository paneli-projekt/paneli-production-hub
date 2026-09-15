# 16 — Izvoz za PanelWizard (CPW) i za pilu (CPO) — kralježnica, korak 3b

**Datum:** 14.9.2026. · **Radi se o:** `hub/nalozi/export_pw.py`, `hub/nalozi/export_pila.py`, `hub/alati/provjera_exporta.py`
**Odluke:** D-11 (paralelni rad s PW-om), D-19 (izbor načina), D-21 (kerf), D-22 (brojevi programa), D-61 (slovo M/A — riješeno 15.9.), D-62 (popis traka — odlučeno 15.9.)
**Prethodi:** dokument 15 (izvoz na nesting)

---

## 1. Čime je nalog sada zatvoren prema strojevima

Dokument 15 je napravio nesting. Ovaj dodaje druga dva izlaza, pa nalog iz Huba sada ide na sve tri strane:

| Izlaz | Modul | Mapa | Čemu služi |
|---|---|---|---|
| CSV + CIX | `export_nesting` | `<NALOG>\NESTING\` | bNest — nesting stroj |
| **CPW** | **`export_pw`** | `<NALOG>\PANEL WIZARD\` | PanelWizard — obračun i paralelni rad (D-11) |
| **CPO** | **`export_pila`** | `<NALOG>\PILA\` | Selco OSI — pila |

```cmd
py -m hub.nalozi.export_pw   --db hub.db --nalog 9 --mapa C:\PPNESTING
py -m hub.nalozi.export_pila --db hub.db --nalog 9 --mapa C:\PILA
```

Oba imaju `--suho`: složi i izračunaj, ne piši ništa. To je ujedno ono što će ekran pokazati prije nego voditelj
pritisne „Pošalji".

## 2. CPW — da Hub i PanelWizard mogu voziti jedan uz drugoga

PW ostaje motor pile i radi obračun dok Hub ne preuzme oboje. Zato Hub piše **istu CPW datoteku koju je dosad pisao
PPNEST**, u istu mapu i s istim zaglavljem (`FORMAT;CORPUS->PW;002600;` ispred svakog elementa — PPNEST je to radio
tako, PW prihvaća i uredniju varijantu, `--zaglavlje-jednom`).

Za razliku od nestinga, CPW dobiva **sve materijale naloga**, i one koji idu na nesting — PW računa cijeli nalog.

## 3. CPO — pila iz Huba, bez PanelWizarda

Iz naloga se po materijalu složi shema (D-18/D-19) i napiše `.cpo` koju pila učita.

- **Način optimizacije bira Hub** (D-19): materijal s godom samo uzdužno, bez goda i poprečno; pobjeđuje najmanja
  površina za naplatu. Koji je pobijedio zapisuje se uz rezultat.
- **Kerf** (D-21): slaganje i obračun po kerfu naloga (zadano 16 mm, kao PW „Podesi alat"), a u datoteku ide fizički
  kerf pile 5,00 — na pilu ide ISTA shema po kojoj je obračunato.
- **Broj programa** (D-22): `HUB_00001`, `HUB_00002`… iz Hubovog brojača — vlastiti niz koji se ne sudara s PW-ovim
  `I_` / `SA_` dok se radi paralelno.
- Svaki izvoz upisuje red u `optimizacija` (broj ploča, iskorištenje, m² za naplatu, rezovi, način) i dokument u nalog,
  pa se kasnije zna po čemu je nalog rezan i naplaćen.

**Datoteka je valjana i istog oblika kao PW-ova.** Na HUMER-u, materijal IV JELA TAVERNA 19:

| | Program | INV | ORD | PRT | PAT | Debljina / paket | Kerf | God |
|---|---|---|---|---|---|---|---|---|
| PanelWizard `I_01915.cpo` | 285 | 6 | 35 | 35 | 6 | 19,0 / 95,0 | 5,00 | Y |
| **Hub `HUB_00002.cpo`** | HUB_00002 | 6 | 35 | 35 | 6 | 19,0 / 95,0 | 5,00 | Y |

Provjera stabla rezova (`cpo_rw.validate`) prolazi bez greške, a datoteka se čita i vraća **bajt po bajt ista**.
Brojke: PW 6 ploča / 73,5 % / 30,97 m², Hub 6 ploča / 73,5 % / **30,89 m²**, 86 rezova prema 85.

Optimizator kao takav nije mijenjan — benchmark protiv PW-a na svih 42 materijala je nepromijenjen: **PW 429,16 m² /
102 ploče, Hub 446,25 m² / 104 ploče (+4,0 %)**; isto 14, Hub bolji 5, Hub lošiji 23. To je i dalje otvorena stavka
koja se rješava u koraku 4.

## 4. Nova provjera: je li Hubov izlaz isti posao kao PPNEST-ov

```cmd
py -m hub.alati.provjera_exporta --db hub.db --nalozi ..\05_NALOZI_ZA_TEST --md ..\20_ANALIZA\provjera_exporta.md --obrisi
```

Za svaki testni nalog uveze se PPNEST-ov izvoz, pa se iz Huba izveze natrag i usporedi. Uspoređuje se ono što stroj i
obračun stvarno troše — **debljina, mjere, komadi i maska rubova po elementu** — a ne tekst naziva (Hub namjerno piše
svoj kratki naziv materijala i pravi naziv trake iz Pantheona).

**Rezultat: CSV 8 / 8 naloga isto, CPW 5 / 8.** Preostale tri razlike su sve iste vrste i objašnjene su u §5; ni u
jednom nalogu se ne razlikuje nijedna mjera, nijedan komad ni broj elemenata.

## 5. Zašto se CPW razlikuje: slovo M/A nije vrsta trake nego mjesto u obrascu

U CPW-u uz svaki rub stoje dvije stvari: slovo (`M` / `A`) i naziv trake. Na testnim nalozima se to dvoje
**razilazi 70 puta od 474 provjerena ruba (15 %)**:

| Nalog | Što piše | Trake |
|---|---|---|
| _BOGDANIC_IVA | slovo `M`, traka je ABS (21 ruba) | `1/22 AVIVA DEW` |
| _BRATEK_KUPAC1 | slovo `M`, traka je ABS (26) | `1/22 BIJELI NK`, `2/22 BIJELI NK` |
| _BRATEK_KUPAC1 | slovo `A`, traka je melamin (7) | `MEL 0.5/22 BIJELI NK` |
| _HUMER_OMIS | slovo `M`, traka je ABS (16) | `1/44 ISTI` |

**Objašnjenje (Igor, 15.9.2026.):** PanelWizard za materijal ima **dva polja** za naziv trake — jedno pod „ABS",
jedno pod „MEL". Kad nalog treba dvije različite ABS trake, druga se upisuje u MEL polje. Nije riječ o grešci nego o
zaobilaznici: kupci na papir pišu elemente redom kako im padnu na pamet, pa se dvije trake izmjenjuju iz elementa u
element, a s dva polja bi to značilo brisanje i ponovno tipkanje naziva za svaki element.

Primjer je upravo BOGDANIC — PW-ova statistika „Kantiranje sortirano po dekorima" za taj nalog pokazuje:

```
1   ABS: 1/22 OF CHAMPAGNE      65.010 m
2   MEL:                         0.000 m
3   MEL: 1/22 AVIVA DEW         33.409 m
```

Prava melaminska traka (red 2) je prazna; red 3 je druga ABS traka u MEL slotu. Ivana iz te statistike čita pravi
naziv i u Pantheon unosi ABS 1/22 — **naplata dakle nije bila pogrešna**, samo je zapis u datoteci nosio slovo koje
znači mjesto, a ne vrstu.

**Mjerodavan je naziv trake.** Hub zato slovo izvodi iz prepoznate trake (klasa 0,5 mm → `M`, deblja → `A`), a kad
traka nije prepoznata, iz teksta oznake (`MEL-ISTI` → `M`). Time PW-ova statistika iz Hubovog CPW-a obje ABS trake
grupira pod „ABS", kako i jesu — to je ispravak, a ne odstupanje.

Usput je popravljena i jedna Hubova greška iste obitelji: rub naručen kao `MEL-ISTI` kojemu šifrarnik nije našao traku
išao je u PW kao `A`. Sada vrijedi tekst oznake.

**Što iz toga slijedi za Hub (D-62):** zaobilaznica postoji samo zato što obrazac ima dva polja. U Hubu svaki rub već
pamti svoju traku, pa ograničenja nema — ostaje riješiti **unos**. Igor je 15.9. odlučio oblik: materijal naloga nema
fiksna dva polja nego **popis koji počinje s `ABS-ISTI` i `MEL-ISTI`, a dopunjuje se gumbom `+ ABS traka` /
`+ MEL traka`**; svaka traka dobiva vrstu, naziv iz šifrarnika, boju i kratku **oznaku** (`A1`, `A2`, `M1`…) koja se upisuje uz element umjesto cijelog naziva. Ne
generalizira se po materijalu — svaki materijal može biti kantiran bilo kojom bojom trake ako kupac tako traži.
Uz svaki rub elementa stoji **kućica vidljiva i kad je prazna**: klik stavlja aktivnu traku na taj rub, ponovni klik
je miče; dvoklik u sredinu stavlja je na sva četiri ruba, sljedeći dvoklik briše sve. Klikabilna proba:
`docs/mockup/trake_naloga.html` (artefakt „Trake naloga").

## 6. Dvije male, namjerne razlike od PPNEST-a

1. **Naziv materijala.** Hub piše svoj kratki naziv (`IV_BIJELI_NK_18`), PPNEST je pisao tekst kakav je stigao od
   kupca (`IV_BIJELI_NK_18_MM`). Materijal je u CPW-u i u CSV-u slobodan tekst — bNest ploču nalazi po Winstore kodu,
   PW po vlastitom izboru — pa je ista ploča sada uvijek isto ime datoteke, bez obzira kako ju je kupac napisao.
2. **Naziv trake.** Hub piše naziv iz Pantheona (`ABS 1/22 JELA CLAY`), PPNEST kupčevu riječ (`1/22 JELA TAVERNA`).
   Veza je potvrđena na stvarnoj ponudi 26-010-002823, dakle to je traka koja je i naplaćena.

Obje razlike mijenjaju samo ono što piše, ne i što se reže.

## 7. Što ostaje u koraku 3

0. **Popis traka pri ručnom unosu (D-62)** — odlučeno 15.9., ide u mockup v0.5 zajedno sa skicom elementa (D-59).
1. **Stvarno spajanje malih naloga (D-54, korak B)** — jedan zajednički CSV + CIX paket, uz oznaku NJEGOVOG naloga na
   svakom elementu (etiketa je već nosi) i razdiobu potrošnje natrag.
2. **Čitanje rezultata natrag** — sheme iz CPO-a u PNG za operatera, stvarna potrošnja iz `.mno` i razdioba po
   nalozima (D-38).
3. **Uvoz Corpusovog paketa** (D-55 točka 3) — element s dva CIX-a.
