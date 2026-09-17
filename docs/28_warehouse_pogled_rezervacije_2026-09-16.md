# Paneli Production Hub — 28: Warehouse, 2. dio — pogled nad izvorima, rezervacije, provjera naloga, restl iz sheme, potrebe za nabavu (D-64, D-42/4, D-42/5, D-35)

Stanje 16. 9. 2026. kasno navečer. Nastavak dokumenta 27 („može dalje", Igor). Warehouse je sada cijeli POGLED s tri prilagodnika istog sučelja
i računicom iznad njih; **138 testova prolazi** sa stvarnim podacima (5 novih u `tests/test_skladiste.py`, uklj. stvarni HUMER + Winstore XML + evidencija restlova).
Nema promjene sheme (v12 iz dokumenta 27 već ima sve stupce).

## 1. Prilagodnici (`hub/skladiste/`, isto sučelje: stanje · lokacija · rezerviraj · oslobodi)

| Izvor | Modul | Stanje | Lokacija | Rezervacija |
|---|---|---|---|---|
| pune ploče = **Winstore** | `ploce.py` | `stanje(materijal_id)`: kom (bez Drop i ambalaže), interno / eksterno, Drop zasebno, kodovi; `kom(mid)` | Winstore kod materijala (regal nestinga nema pretinac) | `rezervacija(winstore_kod, kom)` po materijalu naloga; Winstore se ne dira |
| restlovi = **Hub** | `restlovi.py` | `stanje(mid)`: slobodan / rezerviran / provjeri s vezanim identom | `lokacija(oznaka)` (A001, SATOR B 2.1) | `rezerviraj(nm, restl)` → restl `rezerviran`; `izdaj` → `potrosen` + nalog izlaza |
| trake = **Regal traka** | `trake.py` | `stanje(ident)`: metri na roli, pretinac, dostupno | pretinac iz `GET /api/stanje` | **nema** — Hub ne oduzima metre (D-63), samo uspoređuje |

## 2. Iznad izvora (`hub/skladiste/pogled.py`)

* **`potrebe_naloga(nalog_id)`** — po materijalu: broj ploča iz **potvrđenog** slaganja (D-75; bez potvrde = nepoznato + upozorenje), je li na restlu
  (`nalog_materijal.ploca_L/W`), najveći komad (za restl kandidate), RP/ZO po dužnom metru (Winstore ih ne vodi), **trake po TR identu**:
  Σ konačna stranica × kom × nadmjera (postavka `nadmjera_trake`, D-77) naviše na metar — ista brojka kao u ponudi (D-20).
* **`stanje_materijala(mid)`** — fizičko (Winstore) + rezervirano (aktivne rezervacije drugih naloga) + naručeno (otvorene narudžbenice
  `poslana` / `djelomicno`, kom − zaprimljeno) → **raspoloživo = fizičko − rezervirano + naručeno** (D-42/4); uz to restlovi (kom, m², popis).
* **`provjera_naloga(nalog_id)`** — ekran 4 / status Skladište (D-35): po materijalu potrebno, raspoloživo, **manjak**, restlovi koji mogu poslužiti
  (u koje stane najveći komad, u obje orijentacije), trake s metrima na roli i pretincem; **upozorenja** i **popis za nabavu** (ploče u KOM, trake u M).
* **`rezerviraj_nalog(nalog_id, restlovi={nm: restl})`** — rezervira pune ploče iz potvrđenog slaganja (Winstore kod) i restl za materijal na restlu
  (ako je zadan), te **predloži restlove iz potvrđenih shema** (§4); `oslobodi_nalog`, `izdaj_nalog`, `zatvori_nalog`.
* **`potrebe_ukupno()`** — ekran 6 Nabava (D-42/5): preko svih naloga u `potvrdjeno / skladiste / pila_nesting` Σ ploča po materijalu i Σ metara po traci;
  **manjak = Σ potrebno − fizičko − naručeno** (rezervacije su rezervacije upravo tih naloga, pa se ne oduzimaju dvaput); nalozi bez potvrđenog
  slaganja idu u `nepoznato`; `za_nabavu` = popis identa s manjkom.

## 3. Tok naloga (D-35) — što Hub sam radi pri promjeni statusa (`nalozi.postavi_status`)

| Prijelaz | Skladište |
|---|---|
| → **skladiste** | `rezerviraj_nalog`: rezervacija ploča po materijalu, prijedlozi restlova iz shema; rezultat provjere vraća se uz nalog (`nalog["skladiste"]`: upozorenja + za nabavu) |
| skladiste → **pila_nesting** | rezervacije → `izdano`; rezervirani restl → `potrosen` s nazivom naloga (materijal je otišao na stroj) |
| skladiste → potvrdjeno | rezervacije → `oslobodjeno`, restl natrag `slobodan` |
| → **zatvoren** | `izdano` → `potroseno`, ostalo oslobođeno |

Ponovni ulazak u „skladište" s istim slaganjem ne duplicira ništa (isti prijedlozi restlova ostaju); novo slaganje zamjenjuje stare prijedloge (otpisani, s napomenom).
Brisanje probnog naloga briše njegove prijedloge i vraća rezervirani restl.

## 4. Restl kao PRIJEDLOG iz potvrđene sheme (D-64/3)

Iz `optimizacija.slaganje_json.ostaci` potvrđenog slaganja — **korisni ostaci ≥ 400 × 400 mm i ≥ 1 m² (D-19), isti koje obračun ne naplaćuje kupcu** —
Hub otvori restlove sa statusom `prijedlog`, oznakom `R…` (niz nastavlja Excelov: prvi Hubov je **R1364**), izvorom `prijedlog`, vezom na materijal
naloga i napomenom `ostatak 1/2 iz sheme HUMER_OMIS_1 (opt. 17)`. Samo za materijal koji ide na **pilu** (nesting ostatke vodi Winstore kao Drop).
Skladištar ih nakon rezanja **potvrdi** (`potvrdi_restl`: lokacija, po potrebi ispravljena mjera; zalijepi QR) → `slobodan` i tek tada je restl na stanju;
ili **odbaci** → `otpisan`. Na stvarnom HUMER-u (5 materijala, kupčev PPW): svi prijedlozi ≥ 1 m² i ≥ 400 mm, kako pravilo traži.

## 5. API (`hub/api/skladiste_api.py`)

`GET /api/skladiste/stanje?ident=&q=` · `GET /api/skladiste/materijal/{mid}` · `GET /api/skladiste/restlovi?ident=&status=&za_potvrdu=&q=` ·
`GET /api/skladiste/restlovi/sazetak` · `POST /api/skladiste/restlovi/uvoz {putanja}` · `POST /api/skladiste/restlovi {ident, L, W, kom, lokacija}` ·
`POST /api/skladiste/restlovi/{id|oznaka}/potvrdi {lokacija, L, W}` · `…/odbaci {razlog}` · `POST /api/skladiste/restlovi/potvrdi-dekor {dekor, ident}` ·
`GET /api/skladiste/prijedlozi?nalog=` · `GET /api/skladiste/trake?ident=` · `GET /api/nalog/{id}/skladiste` · `POST …/skladiste/rezerviraj {restlovi}` ·
`POST …/skladiste/oslobodi` · `GET /api/skladiste/potrebe`. CLI: `py -m hub.skladiste.restlovi --prijedlozi [--nalog N]`, `--potvrdi-restl R1364 --lokacija B004`.

## 6. Provjereno

* Sintetički: Winstore 3 ploče + Drop 2, nalog 1 ploča → raspoloživo 3 / manjak 0; drugi nalog vidi rezervaciju (raspoloživo 2); Winstore 1 → manjak 1;
  otvorena narudžbenica 5 → manjak 0; zaprimljena → opet 1; traka TR000168 treba 3 m, na roli 2 → manjak 1 m i stavka za nabavu; prijedlog restla R0001 →
  potvrda → na stanju; izdano / potrošeno / oslobođeno po toku; materijal na restlu 1500 × 900: kandidat samo restl u koji stane, rezervacija → potrošen na stroju.
* Stvarno: HUMER kupčev PPW (5 materijala) + Winstore XML 11. 9. + evidencija restlova: IV BIJELI NK 18 → ploče iz potvrđenog slaganja, Winstore `W908ST2-18`
  na stanju, restlovi iz evidencije vidljivi kao kandidati; potrebe_ukupno = Σ ploča naloga.

## 7. Otvoreno (za Igora) — D-83 PREDLOŽENO

1. **Kada je materijal „izdan"**: sada pri prelasku u pila / nesting (rezervacija → izdano, restl → potrošen). Alternativa: tek kad se `.mno` / CPO vrati.
2. **Restl u koji nalog može stati** Hub samo pokazuje (kandidati); prebacivanje naloga na restl mijenja obračun (cijela površina restla, D-69) pa ostaje odluka ureda u ponudi.
3. **Nesting ostaci** ostaju u Winstoreu (Drop); Hub ih pokazuje uz materijal, ne vodi ih kao restlove.
4. **QR naljepnica restla** (oznaka, ident, mjere, lokacija) kroz `hub/ispis/` — sljedeći korak, uz narudžbenicu (modul nabava, D-42/5).
