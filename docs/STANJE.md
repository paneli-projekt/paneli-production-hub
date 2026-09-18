# Paneli Production Hub — STANJE

**Ažurirano: 17. 9. 2026.** · Odluke: `DECISIONS.md` (D-01 … D-94) · Ideje: `IDEJE_KASNIJE.md` (I-01 … I-20) · Povijest do 17. 9.: `STANJE_POVIJEST.md`

Prvi dokument u novoj sesiji. **Drži se kratkim:** na kraju sesije zamijeniti odlomke „Brojke“, „Čeka Igora“ i „Sljedeće“ — ne dopisivati dnevnik. Što je i zašto napravljeno ide u `DECISIONS.md` i u dokument teme.

## Ukratko

Hub pokriva cijeli tok **unos → optimizacija → ponuda → skladište → proizvodnja (pila / nesting) → nabava**, s web ekranima. Radi na VM-u; Igor prolazi prave naloge kroz ekrane i javlja napomene.

## Brojke

| | |
|---|---|
| Kod | `30_NOVI_PROGRAM\` (Git repo). Zadnji commit `2163d03` (17. 9. 15:59): D-92 radne ploče na pili s ispravkom orijentacije, D-93 obrub / Optimizacija / boja gumba. **Nije još u Gitu:** D-94 izgled ekrana 1A + 2A + 3A i Postavke (17. 9. navečer) — Igor pusha `GIT_POSALJI.cmd` |
| Shema | **v17** — migracija ide sama pri pokretanju |
| Testovi | **166** (izbrojano 17. 9. navečer), uvijek s `HUB_TEST_DATA` (README; bez toga se testovi na stvarnim nalozima preskaču) |
| Hub na VM-u | `C:\Paneli\Hub` → `http://192.168.5.201:8766/` (8765 = Knjiga, 8080 = Regal traka); upute `deploy\README_DEPLOY_HUB.md` |
| Zadnji dokument | **34** — izgled ekrana 1A + 2A + 3A i nova stranica Postavke (D-94); prije toga 33 (radne ploče na pili, obrub) |

## Što je gotovo

| Dio | Kod (`hub/`) | Dokument |
|---|---|---|
| Šifrarnik: Pantheon, Winstore, prepoznavanje naziva, ispravci ureda | `sifrarnici/` | 11, 13 |
| Kupci, nalog, elementi; uvoz CPW, PPNEST CSV, PW `.pnl` | `nalozi/` | 12, 32 |
| Izvoz nesting (CSV + CIX), PanelWizard (CPW), pila (CPO); uvoz Corpus paketa; `.mno` natrag; spajanje naloga | `nalozi/export_*`, `uvoz_corpus`, `rezultat_nesting`, `spajanje` | 15, 16, 18, 19, 20 |
| Optimizator pile; optimizacija s potvrdom; zadano „Realno za pilu“ uz ograničenja iz postavki, „Hub rezerva“ kao alternativa (D-91) | `optimizacija/`, `nalozi/optimiziraj.py` | 22, 22a, 25, 32 |
| Radne ploče, ploče stola, zidne obloge: optimizacija na pili i naplata po ploči (D-37 / D-92) | `optimizacija/radne_ploce.py` | 33 |
| Mjera za rezanje, majke malih komada, sklop lijepljenja, niz goda | `nalozi/grupe.py` | 26 |
| Obračun i ponuda: verzije, ručne stavke, korekcije, PDF, mail s potpisom osobe, eSlog 220, izdatnica | `nalozi/obracun.py`, `ponuda*.py`, `mail.py` | 21, 21a, 32 |
| Warehouse: ploče (Winstore), restlovi (Hub), trake (Regal traka), rezervacije, provjera naloga, restl iz sheme, QR naljepnice | `skladiste/`, `ispis/naljepnica_restl.py` | 27, 27a, 28, 30 |
| Nabava: potrebe, narudžbenica (PDF + mail), primka iz eSlog-a | `nabava/` | 30 |
| Krojni nacrt PDF (statistika s identima i pretincima) | `ispis/krojni.py` | 25 |
| Web ekrani: popis naloga, 1 Unos → 2 Optimizacija → 3 Ponuda → 4 Skladište → 5 Proizvodnja, nabava, šifrarnik, postavke; prijava s lozinkom; uvoz više datoteka; promjene između verzija ponude; izgled 1A + 2A + 3A, Postavke po cjelinama | `web/`, `api/`, `korisnici.py` | 31, 32, 34 |

## Čeka Igora

**Na VM-u (prvo):**
1. Kopirati na VM i proći **novi izgled ekrana i Postavke (D-94, dokument 34)**. Prolaz 17. 9. (uvoz više datoteka, radne ploče na pili, obrub, Optimizacija) — „sada je ok“. Nakon svakog kopiranja na VM nastaviti prolaz s pravim nalozima.
2. Postavke → **Podaci tvrtke**: upisati OIB, IBAN, telefon (sada na ekranu); postaviti prvu lozinku (IGOR, admin) — od tada je prijava obavezna za sve (D-88).
3. Prije stvarnog rada obrisati probne naloge iz baze na VM-u.

**Prijedlozi koji čekaju „da“ ili ispravak:**
- **D-82** pravila restlova (27) · **D-83** rezervacije i tok skladišta (28) · **D-85** pravila nabave (30)
- **D-84** CNC obrade iz Huba — Igor šalje popis obrada i zadane parametre (29 §4)
- 57 dekora restlova za potvrdu (27a) — Igor: „naknadno“
- Iz 33 §Otvoreno: radna ili stol iz PW naziva „RP …“ (prijedlog: komad širi od 600 → stol); identi radnih ploča s jedinicom KOM
- Iz 34 §Otvoreno: dva zelena gumba „pošalji“ na Proizvodnji i „Potvrdi (QR)“ u svakom redu restla — ostaviti ili neutralno?
- Iz 32 §Otvoreno: prazan rabat ručne stavke = rabat naloga po grupi?; treba li HTML tijelo maila izgledati kao PDF?; prava po ulogama (zasad samo admin uređuje korisnike)

**Ured / Pantheon (ne blokira Hub):**
- Probni uvoz eSlog ponude iz Huba u Pantheon (kupac u SU, rabat po stavci u `OdstotkiPostavk`) i koja vrsta dokumenta prima izdatnicu (D-56)
- D-44 zidne obloge bez identa; D-45 (c) trake koje nedostaju: CRNA NK 22, CHAMPAGNE UM, PVC CRNI MAT VSM-02
- Dokument 13: `U125ST9-18` (pravi ident), `1111PO-18` (oštećeni povrat), `IV000065-25` (otvoriti ident), Winstore `U999TM28-18` → 19,6 mm i novi kod za `IV001027`; `MOSAICOFB35` ispraviti u Pantheonu na 19 mm (Hub je već točan preko ispravka)
- D-37b popis dekora „samo cijela ploča“ — kasnije
- Ako još nije: učitati `Obrada kupaca\krojna-ponuda_v2_D20.skill`

## Sljedeće (plan od 17. 9. navečer)

**A. Spremno za stvarni rad (prvo, ovaj tjedan)**
1. Sigurnost podataka na VM-u: Task Scheduler „Paneli - Hub Server“ (Hub se sam diže nakon restarta) + **noćna kopija `hub.db`** na drugi disk s čuvanjem zadnjih 14 dana (dokument 24). Claude pripremi `.bat`, Igor pokrene jednom na VM-u.
2. Igor na VM-u: OIB / IBAN / telefon u Postavke → Podaci tvrtke, prve lozinke (IGOR admin), obrisati probne naloge.
3. Ured: **probni uvoz eSlog ponude iz Huba u Pantheon** (kupac, rabat po stavci) — bez toga ponuda iz Huba ne ide dalje od PDF-a.
4. Paralelno razdoblje (D-73): pravi nalozi idu kroz Hub, PW ostaje sigurnosna mreža; razlike se javljaju i ispravljaju (dokument 35).

**B. Što fali za svakodnevni tok (sljedeća 1–2 tjedna)**
5. Ispisi za pogon: **radni nalog**, **pick-lista traka** uz krojni nacrt (D-63), izdatnica.
6. **Okov**: uvoz s prijedlogom identa (D-32); do tada ručne stavke ponude.
7. Radna ploča ili ploča stola iz PW naziva „RP …“ (33 §Otvoreno 1) i identi s jedinicom KOM (33 §2) — kad Igor odluči.
8. Igor potvrdi ili ispravi **D-82 / D-83 / D-85** → skladište (rezervacije, restlovi) i nabava (narudžbenice, primka) u stvarnom radu; 57 dekora restlova.

**C. Kasnije**
9. CNC obrade iz Huba (D-84) — kad Igor pošalje katalog obrada i parametre.
10. Uvoz Excela / rukopisa kupca (skill krojna-ponuda); dijalog fronti za kupčev `skica N`.
11. Nabava radnih ploča po pločama (Winstore ih ne vodi); web katalog korpusa (dokument 20) — zasebna tema; praćenje proizvodnje — zaseban sustav.

## Pravila rada

- Hrvatski. Nalazi u `20_ANALIZA\`, kod u `30_NOVI_PROGRAM\` (Igor pusha sam, `GIT_POSALJI.cmd`); mape 01–13 i `99_BACKUP_NE_DIRATI` se ne diraju.
- PanelWizard je referenca i benchmark — ne mijenjati, ne kopirati kod. U paralelnom razdoblju PW je sigurnosna mreža, benchmark 22a je regresija (D-73).
- Pantheon samo eSlog (D-06). Warehouse je pogled nad izvorima — Hub ne vodi paralelni fizički broj (D-64). Ponuda, narudžba i stroj uvijek prate **potvrđenu** optimizaciju (D-75).
- Na ekranima nikad riječ „AI“ ni oznake D-xx; na radnom ekranu samo ono što korisnik u tom koraku treba, ostalo na klik (D-14).
- Prije rada na kodu Igoru prvo objasniti na čemu se radi. Kad Igor treba nešto izvršiti: objašnjenje + gotova cmd naredba, bez sitnih kontrolnih koraka.
- Nova odluka → `DECISIONS.md` (ODLUČENO / PREDLOŽENO + „Zašto“); ideja → `IDEJE_KASNIJE.md`. Kopije: `20_ANALIZA\` + `30_NOVI_PROGRAM\docs\` + projekt `claude/…`.
- Push u Git nakon svakog dana rada; Corpus uzorak (`05_NALOZI_ZA_TEST\_CORPUS_UZORAK`) kao dimni test prije svake nadogradnje bNesta / bSolida / Corpusa (dokument 24).
- Datoteke na Igorovom PC-u: `device_bash` (radi); ako stane, stage / commit alati. **Git iz `device_bash` samo čitati i uvijek s `GIT_OPTIONAL_LOCKS=0`** — inače ostaje `.git\index.lock` (ne da se obrisati iz VM-a) i Igorov `GIT_POSALJI.cmd` pada.

## Karta dokumenata (čitati samo kad zadatak traži)

Audit i temelji 00–06 · mockup 07 · Corpus put 08, 14 · checklista 09 · temelji praćenja i nabave 10 · šifrarnik 11, 13 · nalog 12 · izvozi 15, 16 · pregled koda 17 · uvoz Corpusa 18 · rezultati natrag 19 · spajanje naloga 20 · obračun i ponuda 21, 21a · optimizator 22, 22a · niz goda 23 · rizici „što ako“ 24 · optimizacija s potvrdom i krojni nacrt 25 · mjera za rezanje 26 · restlovi 27, 27a · Warehouse pogled 28 · CNC obrade 29 · nabava i QR 30 · web ekrani 31 · napomene na ekrane 32 · radne ploče na pili, obrub 33 · izgled ekrana 1A + 2A + 3A i Postavke 34

Zasebno: `20_web_katalog_korpusa_2026-09-15.md` — prijedlog javnog web kataloga korpusa (15. 9.), nije ušao u DECISIONS; nije dio trenutnog posla.
