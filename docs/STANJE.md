# Paneli Production Hub — STANJE

**Ažurirano: 17. 9. 2026.** · Odluke: `DECISIONS.md` (D-01 … D-91) · Ideje: `IDEJE_KASNIJE.md` (I-01 … I-20) · Povijest do 17. 9.: `STANJE_POVIJEST.md`

Prvi dokument u novoj sesiji. **Drži se kratkim:** na kraju sesije zamijeniti odlomke „Brojke“, „Čeka Igora“ i „Sljedeće“ — ne dopisivati dnevnik. Što je i zašto napravljeno ide u `DECISIONS.md` i u dokument teme.

## Ukratko

Hub pokriva cijeli tok **unos → slaganje → ponuda → skladište → proizvodnja (pila / nesting) → nabava**, s web ekranima. Radi na VM-u; Igor prolazi prave naloge kroz ekrane i javlja napomene.

## Brojke

| | |
|---|---|
| Kod | `30_NOVI_PROGRAM\` (Git repo). Zadnji commit `26a4a88` (17. 9.) sadrži sve do D-91 i skraćeni STANJE; **dopuna 8 (uvoz više datoteka, promjene verzija, Proizvodnja) čeka `GIT_POSALJI.cmd`** |
| Shema | **v16** — migracija ide sama pri pokretanju |
| Testovi | **159** (izbrojano 17. 9. popodne), uvijek s `HUB_TEST_DATA` (README; bez toga se testovi na stvarnim nalozima preskaču) |
| Hub na VM-u | `C:\Paneli\Hub` → `http://192.168.5.201:8766/` (8765 = Knjiga, 8080 = Regal traka); upute `deploy\README_DEPLOY_HUB.md` |
| Zadnji dokument | **32** — Igorove napomene na ekrane, dopune 1–8 |

## Što je gotovo

| Dio | Kod (`hub/`) | Dokument |
|---|---|---|
| Šifrarnik: Pantheon, Winstore, prepoznavanje naziva, ispravci ureda | `sifrarnici/` | 11, 13 |
| Kupci, nalog, elementi; uvoz CPW, PPNEST CSV, PW `.pnl` | `nalozi/` | 12, 32 |
| Izvoz nesting (CSV + CIX), PanelWizard (CPW), pila (CPO); uvoz Corpus paketa; `.mno` natrag; spajanje naloga | `nalozi/export_*`, `uvoz_corpus`, `rezultat_nesting`, `spajanje` | 15, 16, 18, 19, 20 |
| Optimizator pile; slaganje s potvrdom; zadano „Realno za pilu“ uz ograničenja iz postavki, „Hub rezerva“ kao alternativa (D-91) | `optimizacija/`, `nalozi/optimiziraj.py` | 22, 22a, 25, 32 |
| Mjera za rezanje, majke malih komada, sklop lijepljenja, niz goda | `nalozi/grupe.py` | 26 |
| Obračun i ponuda: verzije, ručne stavke, korekcije, PDF, mail s potpisom osobe, eSlog 220, izdatnica | `nalozi/obracun.py`, `ponuda*.py`, `mail.py` | 21, 21a, 32 |
| Warehouse: ploče (Winstore), restlovi (Hub), trake (Regal traka), rezervacije, provjera naloga, restl iz sheme, QR naljepnice | `skladiste/`, `ispis/naljepnica_restl.py` | 27, 27a, 28, 30 |
| Nabava: potrebe, narudžbenica (PDF + mail), primka iz eSlog-a | `nabava/` | 30 |
| Krojni nacrt PDF (statistika s identima i pretincima) | `ispis/krojni.py` | 25 |
| Web ekrani: popis naloga, 1 Unos → 2 Slaganje → 3 Ponuda → 4 Skladište → 5 Proizvodnja, nabava, šifrarnik, postavke; prijava s lozinkom; uvoz više datoteka; promjene između verzija ponude | `web/`, `api/`, `korisnici.py` | 31, 32 |

## Čeka Igora

**Na VM-u (prvo):**
1. Prvi prolaz na VM-u 17. 9. — „sve je ok“, napomene provedene (32 dopuna 8). Kopirati Hub na VM (`deploy\1_KOPIRAJ_HUB_NA_VM.bat`, na VM-u `2_VM_HUB_POSTAVI.bat`) i nastaviti prolaz; javiti što još smeta.
2. Postavke: upisati `tvrtka_oib`, `tvrtka_iban`, `tvrtka_tel`; postaviti prvu lozinku (IGOR, admin) — od tada je prijava obavezna za sve (D-88).
3. Prije stvarnog rada obrisati probne naloge iz baze na VM-u.

**Prijedlozi koji čekaju „da“ ili ispravak:**
- **D-82** pravila restlova (27) · **D-83** rezervacije i tok skladišta (28) · **D-85** pravila nabave (30)
- **D-84** CNC obrade iz Huba — Igor šalje popis obrada i zadane parametre (29 §4)
- 57 dekora restlova za potvrdu (27a) — Igor: „naknadno“
- Iz 32 §Otvoreno: prazan rabat ručne stavke = rabat naloga po grupi?; treba li HTML tijelo maila izgledati kao PDF?; prava po ulogama (zasad samo admin uređuje korisnike)

**Ured / Pantheon (ne blokira Hub):**
- Probni uvoz eSlog ponude iz Huba u Pantheon (kupac u SU, rabat po stavci u `OdstotkiPostavk`) i koja vrsta dokumenta prima izdatnicu (D-56)
- D-44 zidne obloge bez identa; D-45 (c) trake koje nedostaju: CRNA NK 22, CHAMPAGNE UM, PVC CRNI MAT VSM-02
- Dokument 13: `U125ST9-18` (pravi ident), `1111PO-18` (oštećeni povrat), `IV000065-25` (otvoriti ident), Winstore `U999TM28-18` → 19,6 mm i novi kod za `IV001027`; `MOSAICOFB35` ispraviti u Pantheonu na 19 mm (Hub je već točan preko ispravka)
- D-37b popis dekora „samo cijela ploča“ — kasnije
- Ako još nije: učitati `Obrada kupaca\krojna-ponuda_v2_D20.skill`

## Sljedeće (redom)

1. Nastaviti s Igorovim napomenama s prolaza na VM-u (sljedeće u dokument 33).
2. Na VM-u: Task Scheduler „Paneli - Hub Server“ (`deploy\HUB_SERVER.bat`, at startup, restart on failure) i **noćna kopija `hub.db`** na drugi disk (dokument 24).
3. Ispisi na `hub/ispis/`: radni nalog, pick-lista traka uz krojni nacrt (D-63), izdatnica.
4. Okov: uvoz s prijedlogom identa (D-32); do tada ide kroz ručne stavke ponude (D-87).
5. Kad Igor potvrdi D-84: blok „Obrada“ na elementu (CIX + usluga + bar kod na naljepnici).
6. Manje: dijalog fronti za kupčev `skica N` na ekranu unosa; uvoz Excela / rukopisa kupca (skill krojna-ponuda).

## Pravila rada

- Hrvatski. Nalazi u `20_ANALIZA\`, kod u `30_NOVI_PROGRAM\` (Igor pusha sam, `GIT_POSALJI.cmd`); mape 01–13 i `99_BACKUP_NE_DIRATI` se ne diraju.
- PanelWizard je referenca i benchmark — ne mijenjati, ne kopirati kod. U paralelnom razdoblju PW je sigurnosna mreža, benchmark 22a je regresija (D-73).
- Pantheon samo eSlog (D-06). Warehouse je pogled nad izvorima — Hub ne vodi paralelni fizički broj (D-64). Ponuda, narudžba i stroj uvijek prate **potvrđeno** slaganje (D-75).
- Na ekranima nikad riječ „AI“ ni oznake D-xx; na radnom ekranu samo ono što korisnik u tom koraku treba, ostalo na klik (D-14).
- Prije rada na kodu Igoru prvo objasniti na čemu se radi. Kad Igor treba nešto izvršiti: objašnjenje + gotova cmd naredba, bez sitnih kontrolnih koraka.
- Nova odluka → `DECISIONS.md` (ODLUČENO / PREDLOŽENO + „Zašto“); ideja → `IDEJE_KASNIJE.md`. Kopije: `20_ANALIZA\` + `30_NOVI_PROGRAM\docs\` + projekt `claude/…`.
- Push u Git nakon svakog dana rada; Corpus uzorak (`05_NALOZI_ZA_TEST\_CORPUS_UZORAK`) kao dimni test prije svake nadogradnje bNesta / bSolida / Corpusa (dokument 24).
- Datoteke na Igorovom PC-u: `device_bash` (radi); ako stane, stage / commit alati. **Git iz `device_bash` samo čitati i uvijek s `GIT_OPTIONAL_LOCKS=0`** — inače ostaje `.git\index.lock` (ne da se obrisati iz VM-a) i Igorov `GIT_POSALJI.cmd` pada.

## Karta dokumenata (čitati samo kad zadatak traži)

Audit i temelji 00–06 · mockup 07 · Corpus put 08, 14 · checklista 09 · temelji praćenja i nabave 10 · šifrarnik 11, 13 · nalog 12 · izvozi 15, 16 · pregled koda 17 · uvoz Corpusa 18 · rezultati natrag 19 · spajanje naloga 20 · obračun i ponuda 21, 21a · optimizator 22, 22a · niz goda 23 · rizici „što ako“ 24 · slaganje s potvrdom i krojni nacrt 25 · mjera za rezanje 26 · restlovi 27, 27a · Warehouse pogled 28 · CNC obrade 29 · nabava i QR 30 · web ekrani 31 · napomene na ekrane 32

Zasebno: `20_web_katalog_korpusa_2026-09-15.md` — prijedlog javnog web kataloga korpusa (15. 9.), nije ušao u DECISIONS; nije dio trenutnog posla.
