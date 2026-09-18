# 34 — Stil ekrana 1A + 2A + 3A i nova stranica Postavke

**Datum:** 17. 9. 2026. · **Odluka:** D-94 · **Kod:** `hub/web/app.css`, `hub/web/ekrani.js`, `hub/api/nalozi_api.py` · **Testovi:** 166 (novi `tests/test_postavke_ekran_2026_09_17.py`)
**Slike:** `30_NOVI_PROGRAM\docs\ekrani_proba\stil_1A_*.png`

Igor je poslao skice u tri varijante i odabrao kombinaciju **1A (boje) + 2A (upozorenja) + 3A (kartice)**, a zatim skicu stranice Postavke u istom stilu. Skice su smjernica za izgled — podaci, sheme, navigacija, pravila pristupa i poslovna logika ostaju isti.

## 1. Boje (1A „Svježa trava“)

| Uloga | Boja |
|---|---|
| Glavna akcija (gumb) | `#78B84A`, tekst `#173510` (hover `#6BAA3E`) |
| Odabrani tab, odabrani red, aktivni izbornik | `#EFF6E7` |
| Pozadina stranice | `#F6F5F1` |
| Kartice | bijele `#FFFFFF`, diskretan obrub `#ECE9E2` |

- Velike zelene površine (odabrani materijal, aktivni čip, sažetak ponude, zbroj „ZA PLATITI“) su sada bijele ili blago zelene; stanje nose male oznake.
- **Ne mijenja se:** boje u krojnim shemama (iskorišteno / naš restl / kupčev restl), boje kantiranja (ABS, MEL, oznake traka A1, M1 …) i oznake puta (nesting / pila).
- Zamjenjuje boju gumba `#4F8F32` iz D-93.

## 2. Upozorenja (2A)

- Oznaka stanja: **zeleno** potvrđeno / dostupno, **žuto** čeka ili upozorenje, **crveno** greška ili blokada (manjak, nema restla), **sivo** informacija.
- Ponavljajuća upozorenja se skupljaju u **jednu sažetu poruku iznad tablice**, detalji su na klik i uz pripadajući materijal:
  - **Ponuda:** jedan sažetak upozorenja obračuna; uz prvi red materijala oznaka ⚠ s detaljem.
  - **Skladište naloga:** „N materijala imaju manjak · ukupno X ploča“ + gumb **Otvori nabavu**; u tablici stupac **Status** („✓ Dostupno“, „! Manjak 3“, „Nema restla“); za radne ploče i zidne obloge sivi red „Ne vodi se u Winstoreu“.
  - **Optimizacija:** žuta traka „N materijal(a) čeka potvrdu optimizacije“ s gumbom za potvrdu svih zadanih.
- Skladište naloga se sada lista kao cijela stranica (bez skrolanja unutar malih panela), tablica se na užem ekranu ne širi izvan prozora.

## 3. Kartice (3A)

Optimizacija (korak 2) i Proizvodnja (korak 5) imaju isti raspored kartice:

1. naziv materijala i ident, desno oznaka stanja (**✓ Potvrđeno** / **◷ Čeka potvrdu** / **Nema prijedloga**)
2. shema u okviru iste visine na svim karticama
3. tri ključne brojke: **Količina** (N ploča) · **Iskorištenje** · **Za naplatu** (m² ili m za radne ploče)
4. pomoćni red (način, broj rezova, pravilo naplate radne ploče)
5. akcije u jednom redu: glavna zelena (**Potvrdi optimizaciju** / **Izračunaj optimizaciju**), neutralni **Pregled shema** i **Krojni nacrt PDF**
6. traka na dnu: **Ostale varijante (n) ▾** (popis s „Sheme“ i „Potvrdi“) i **Druga varijanta… / Alternativa…** — na svim karticama ista, pa su gumbi poravnati.

## 4. Postavke

Jedna stranica, bijele kartice, naziv i pomoćni tekst lijevo, kratko polje s jedinicom desno.

| Cjelina | Polje na ekranu | Ključ | Unos |
|---|---|---|---|
| **Obračun** | Kerf za naplatu | `kerf` | broj, mm |
| | Nadmjera trake | `nadmjera_trake` | broj, % |
| | Obračun rezanja | `obracun_rezanja` | izbornik: Po m² ploče (`m2`) / Po broju rezova (`rezova`) / Po dužnom metru reza (`m_reza`) |
| | Usluga po rezu | `ident_rezanje_rez` | Pantheon ident |
| | Usluga po dužnom metru | `ident_rezanje_m` | Pantheon ident (prazno dok se ne otvori) |
| **Pravila pile** | Fizički kerf pile | `kerf_pile` | broj, mm |
| | Najviše razina rezanja | `pila_max_razina` | izbornik 2 / 3 / 4 razine |
| | Najviše različitih širina u traci | `pila_max_sirina_u_traci` | cijeli broj, 0 = bez ograničenja |
| | Najmanji komad 4. razine | `pila_min_komad_4` | broj, mm, 0 = bez ograničenja |
| | Miješana orijentacija | `pila_mijesana_orijentacija` | **prekidač** (0 / 1) |
| **Mape izvoza** | Nesting (bNest) | `mapa_nesting` | putanja |
| | Pila (OSI) | `mapa_pila` | putanja |
| **E-pošta** | Poslužitelj, Port, Pošiljatelj, Naziv pošiljatelja; **Napredni podaci** (sklopivo): korisničko ime, kopija svake poruke, datoteka s lozinkom, lozinka postavljena | SMTP postavke | samo pregled; oznaka **Konfigurirano** ili „Lozinka nije postavljena“ |
| **Podaci tvrtke** *(dodatak)* | Naziv, Adresa, OIB, IBAN, Telefon, E-mail, Web | `tvrtka_*` | tekst; OIB 11 znamenki, IBAN bez razmaka velikim slovima |
| **Korisnici i prijava** | Oznaka, Korisnik (ime, funkcija), Uloga, E-mail / telefon, Lozinka, Akcije | korisnici | vidi dolje |

**Spremanje:** gumbi **Odustani** i **Spremi postavke** stoje odmah ispod polja. Rade tek kad postoji promjena; izmijenjeno polje ima žutu točku, neispravno crveni obrub i poruku („upiši broj“, „OIB ima 11 znamenki“). Šalju se samo promijenjene vrijednosti, s oznakom korisnika u dnevniku; nakon spremanja „✓ Postavke su spremljene“. Značenje svih vrijednosti i provjera na poslužitelju su isti kao prije.

**Korisnici i prijava:** žuta poruka „Prijava nije obavezna. Aktivira se postavljanjem prve lozinke.“ (ili siva „Prijava s lozinkom je obavezna“ kad je uključena); uloge razumljivim nazivima (Ured, Nabava, Voditelj, Administrator); lozinka **Postavljena** / **Nije postavljena**; neutralni gumbi **Uredi** i **Postavi lozinku** / **Promijeni lozinku**; dno: „Prijavljeni korisnik: IVANA“ + Promijeni korisnika / Odjava. Pravila pristupa ista: popis svih korisnika i „+ Novi korisnik“ samo administrator (ili dok prijava nije obavezna), ostali vide i uređuju samo sebe.

**Podaci tvrtke — dodatak izvan skice:** OIB, IBAN i telefon tvrtke već se ispisuju na ponudi i narudžbenici, ali ih nije bilo moguće upisati s ekrana (STANJE A2). Dodana je kartica i API `GET/POST /api/postavke/tvrtka` (samo ti ključevi, promjena ide u dnevnik).

## 5. Otvoreno

1. Na ekranu Proizvodnja oba gumba „Nesting — pošalji“ i „Pila — pošalji“ su zelena, a u skladištu naloga „Potvrdi (QR)“ u svakom redu restla. Ako Igor želi strože „jedna zelena akcija po ekranu“ — neutralni gumbi u redovima.
2. E-poštu (SMTP) i dalje mijenja administrator na poslužitelju; uređivanje s ekrana se nije dodavalo.
