# Paneli Production Hub — 30: Nabava (narudžbenica, D-42/5) i QR naljepnice restlova (D-64/3)

Stanje 16. 9. 2026. kasno navečer — nastavak Warehousea (dokumenti 27, 28). Shema **v13**, **141 test** prolazi sa stvarnim podacima
(3 nova u `tests/test_nabava.py`). Igor je između toga dao ideju D-84 (CNC obrade, dokument 29) — čeka njegove podatke, ne blokira.

## 1. Narudžbenica (`hub/nabava/narudzbenica.py`, PDF `hub/ispis/narudzbenica.py`)

Tok kako ga je D-42/5 zamislio, sada radi od kraja do kraja:

1. **Iz potreba** (`iz_potreba`): iz `potrebe_ukupno` (manjak preko svih naloga u potvrđeno / skladište / pila-nesting) nastaje **jedan nacrt po dobavljaču**
   — dobavljač identa je iz Pantheona (`pantheon_ident.dobavljac`: IVERPAN 515 identa, Frischeis 201, Stoliv 124…); ident bez dobavljača ide u nacrt
   „NEPOZNAT DOBAVLJAČ" koji Sanela preraspodijeli. Ploče u **KOM cijelih ploča** s dimenzijom iz šifrarnika (2800×2070), trake u **M** naviše.
   Ono što je već na otvorenoj narudžbenici ne naručuje se dvaput (manjak to već računa: Σ potrebno − fizičko − naručeno).
2. **Dorada** (samo u nacrtu): dodaj / promijeni / ukloni stavku, zaliha unaprijed bez naloga, očekivani datum, napomena.
3. **Slanje** (`posalji`): PDF (zaglavlje tvrtke, dobavljač, stavke bez cijena, „navesti broj narudžbe na otpremnici") + mail istim SMTP-om kao ponuda (D-41),
   status → **poslana**; adresa iz `dobavljac.email` (nova tablica, v13) ili zadana; `--suho` sastavi bez slanja. Poslana se više ne mijenja.
4. **Naručeno** odmah ulazi u raspoloživo (D-42/4): raspoloživo = fizičko − rezervirano + naručeno — samo poslane / djelomično zaprimljene.
5. **Primka**: (a) **eSlog primka** (`uvezi_primku_eslog`) — isti XML koji Knjiga radi za Pantheon (skill primke-pantheon: `StevilkaArtiklaDodatna` SA = naš ident,
   `Kolicina` + `EnotaMere`, dobavljač SE, `ReferencniDokumenti ON` = naš broj narudžbe ako ga dobavljač vrati): spaja **po broju narudžbe** kad ga ima,
   inače **po dobavljaču i identu FIFO** (najstarija poslana prva); **m² s računa → ploče** preko dimenzije ploče iz šifrarnika (11,592 m² = 2 × 2800×2070);
   nespojeno (ident ni na jednoj otvorenoj) se javi, ne izmišlja; dobavljač se prepoznaje bez „d.o.o." i dijakritike. (b) **Ručna primka** (`zaprimi`) za
   robu bez eSlog-a. Status: poslana → djelomično → zaprimljena; višak iznad naručenog se javi, ne odbija.
6. **Poništenje** nacrta / poslane (ne zaprimljene).

Broj narudžbenice `N-2026-001` (brojač po godini u postavkama). CLI: `py -m hub.nabava.narudzbenica --db hub.db --iz-potreba --tko SANELA`,
`--popis`, `--posalji N-2026-001 [--na …] [--suho]`, `--primka ..\..\eslog_uvoz\x.xml`, `--dobavljaci`.

## 2. QR naljepnice restlova (`hub/ispis/naljepnica_restl.py`)

Skladištar ih zalijepi pri potvrdi restla (D-64/3). Sadržaj: **oznaka** (R1364, veliko), QR s adresom Huba `http://192.168.5.201:8766/r/R1364` (isti
princip kao Regal traka `/t/TR000103`; postavka `naljepnica_restl_url`), ident + naziv, L × W (× kom), debljina, lokacija (prazna crta ako još nema),
datum / status. Dva formata (postavka `naljepnica_restl_format`): **A4 mreža 2 × 5** (99 × 57 mm, Avery 3652 / L7173 — zadano) i **rola 62 × 40 mm**
(Brother / Zebra) — kad Igor javi koji printer je kod skladištara (07_ETIKETE\printeri), zadano se prebaci. Probe:
`docs/sheme_proba/naljepnice_restl_proba.pdf` (+ PNG). `GET /r/{oznaka}` = stranica koju skener otvori (materijal, mjere, lokacija, status, tko potvrdio).
Bez dodatnih paketa (QR iz reportlaba).

## 3. API

`/api/nabava/dobavljaci` (GET, POST e-mail), `/api/nabava/narudzbenice` (GET; POST `iz_potreba: true` ili ručna), `/api/nabava/narudzbenica/{id|broj}`,
`…/stavke` (POST), `/api/nabava/stavka/{sid}` (PUT kom, DELETE), `…/posalji`, `…/zaprimi`, `…/ponisti`, `/api/nabava/primka {putanja}`;
`/api/skladiste/restlovi/naljepnice.pdf?oznake=|nalog=|status=&format=`, `/r/{oznaka}`.

## 4. Provjereno (sintetički, `tests/test_nabava.py`)

Nalog 1 ploča + 3 m trake, Winstore 0 → za nabavu IV000090 1 PLOČA + TR000168 1 M → dva nacrta (IVERPAN / NEPOZNAT); dorada (zbroj iste stavke, uklanjanje);
bez e-maila greška → e-mail dobavljača → PDF + mail → poslana; naručeno 3 → manjak 0; ručna primka 1 → djelomično; eSlog 11,592 m² → 2 ploče → zaprimljena,
nepoznat ident nespojen; primka s našim brojem ide točno na tu narudžbenicu, bez broja FIFO preko dvije (2 + 1). Naljepnice A4 i rola, `/r/R0001`.

## 5. Otvoreno (Igor) — D-85 PREDLOŽENO

1. **E-mail dobavljača i tekst narudžbe** — tko upisuje (Sanela u Hubu, jednom po dobavljaču); treba li kopija narudžbe na `prodaja@` / Saneli.
2. **Kada se Knjiga veže**: Knjiga danas radi eSlog primke za Pantheon — dodati joj jedan poziv `POST /api/nabava/primka {putanja}` nakon svakog XML-a
   (integracija „kao s Regal trakom", bez refaktora) ili Hub sam gleda mapu `eslog_uvoz`? Prijedlog: Hub gleda mapu (dnevno, kao Winstore XML).
3. **Printer za naljepnice restlova** (model, veličina) → koji je zadani format.
4. Naručeno bez naloga (zaliha unaprijed) ulazi u raspoloživo isto kao naručeno za nalog — je li to u redu za Sanelu (danas: da, D-42/5 „može naručiti i unaprijed").
