# Paneli Production Hub — STANJE (za nastavak u novoj sesiji)

**Ažurirano: 13. 9. 2026. (kralježnica korak 2: kupci, nalog, elementi, uvoz CPW/CSV).** Ovo je jedini dokument koji treba pročitati prvi; sve ostalo je referenca.
Redoslijed čitanja u novoj sesiji: **STANJE.md → DECISIONS.md (odluke D-01 … D-48) → dokument koji se tiče zadatka** (12 nalog, 11 šifrarnik, 07 mockup, 09 checklista,
10 praćenje i nabava, 08 Corpus, 04 model podataka, 05/06 audit i benchmark).

## Gdje smo

- **Faza 1 (audit) zatvorena 11. 9.** (D-28). **Faza 2 = mockup ekrana + kralježnica aplikacije**, u tijeku.
- **Kralježnica korak 2 — kupci, nalog, elementi — GOTOV 13. 9.** (D-46, dokument 12): kupci iz `ph_subjekti.csv` (3 619), nalog
  `KUPAC_NAZIV_BROJ` s Hub brojačem, materijali sa zadanim trakama, elementi s rubovima (tekst + prepoznata traka), tok statusa D-35 s događajima,
  popis „za potvrdu“ + potvrde koje postaju aliasi, uvoz CPW / PPNEST CSV kroz šifrarnik, API za ekrane 1 i 2 (`hub/api/nalozi_api.py`), shema v2
  s automatskom migracijom (v3). **Krajnji kupci (D-48, Igor odlučio 13. 9.)**: fizičke osobe Hub vodi sam (ime, telefon, e-mail, rabat 0 %), u Pantheon
  idu na zajednički „Krajnji kupac“ (bez OIB-a) ili svoj subjekt (s OIB-om); ponavljači po telefonu / e-mailu / imenu. **Provjera: 9 testnih naloga,
  CPW ↔ CSV isti elementi 7 / 8 (8. = tipfeler operatera), 56 / 57 materijala, HUMER kupčev PPW 121 el / 278 kom bez stavki za potvrdu.** 57 testova prolazi. Kod na disku u `30_NOVI_PROGRAM\hub\nalozi\`, `hub\api\nalozi_api.py` — **još nije u Gitu**.
- **Kralježnica korak 1 — šifrarnik — GOTOV 12. 9.** (D-43, dokument 11): baza, uvoz Pantheona i Winstorea, prepoznavanje naziva → ident
  (47 / 50 CPO, 40 / 40 vs ponuda, 37 / 37 CPW, 30 / 31 CSV, trake 42 / 48), zadane trake, API kostur.
- **Mockup v0.4** (12. 9., 07 §4c): 9 artboarda u dizajnu D (D-39) — 1 popis, 2 unos, 2b okov, 3 obračun → ponuda iz Huba (D-40), 3b dijalog „Kupac potvrdio“,
  3c događaji naloga, 4 skladište, 5 pila / nesting, 6 Nabava (D-42). Platno = artefakt „Production Hub — mockup ekrana“ (verzija 17); slike
  `20_ANALIZA\mockup\v04_*.png`; izvor `30_NOVI_PROGRAM\docs\mockup\v04\`. Igor: „mockup izgleda odlično“, strah od količine informacija → v0.5 može dobiti
  „mirnu“ varijantu ekrana 2 i 3 (manje na prvi pogled, više na klik).
- **Checklista 09 zatvorena** (D-33 … D-38); tok naloga D-35; ponuda iz Huba D-40 (rabat 15 % / 20 %); slanje maila D-41 PREDLOŽENO (čeka pružatelja e-pošte);
  temelji za praćenje i nabavu D-42 (dokument 10).

## Otvoreno / čeka Igora

1. **Pokrenuti korak 1 + 2 na svom PC-u** (naredbe u 12 §4): `pip install -r requirements.txt`, `py -m hub.sifrarnici.uvoz … --kupci … --poste …`,
   `py -m hub.nalozi.provjera … --obrisi`, `py -m pytest -q` — očekivano 47 / 50, 7 / 8, 3619 kupaca. Zatim `GIT_POSALJI.cmd` (u repo ulaze koraci 1 i 2).
2. **D-47** — početni broj naloga (nastaviti niz Pantheon ponuda, npr. 3300, ili od 1)? Postavka `brojac_naloga_pocetak`.
3. **D-44** — zidne obloge bez identa (ZO HR EVOKE SUNSET, ZO HR CREMONA CANNOLO): kako se naplaćuju / otvoriti ident? (11 §5.1)
4. **D-45** — higijena šifrarnika: ambalažne ploče u Winstoreu, identi bez debljine, trake koje nedostaju (CRNA NK /22, CHAMPAGNE UM, PVC CRNI MAT),
   12 Winstore kodova bez identa (11 §5.2–5.3). Ne blokira — do odluke sve ide „za potvrdu“.
5. E-mail kupaca nije u izvozu Pantheona (tHE_SetSubj nema kontakte) — proširiti `IzvozPantheon_v2.ps1` tablicom kontakata ili ured upisuje u Hub (12 §4.3).
   Korak 4 (eSlog): provjeriti na probnoj ponudi da Pantheon uzme kupca iz uloge BY („Krajnji kupac“ / subjekt tvrtke) i napomenu s imenom osobe (D-48).
6. Pružatelj e-pošte za `paneliprojekt.hr` (Microsoft 365 / Google / hosting) → potvrda D-41.
7. Prezentacija mockupa v0.4 Ivani, Goranu, Saneli i voditelju (pitanja za njih u 07 §4c) → povratne informacije → v0.5.
8. Corpus uzorak (08 §6): jedan paket CPW + CSV + CIX iz tehničke pripreme + odgovori na 7 pitanja.
9. Popis dekora „samo cijela ploča“ (D-37b) — kasnije, nije bitan.

## Sljedeći koraci (redom)

1. **Kralježnica korak 3 — exporti iz naloga** (04 §4): CSV + CIX za bNest (CIX imena iz Hub brojača, D-23; postavke operatera iz `nalog_io`),
   CPW za PanelWizard (paralelni rad D-11), CPO za pilu (optimizator iz `hub/optimizacija`, programi `HUB_xxxxx` D-22) — sve iz
   `nalozi.elementi_za_export`; čitanje rezultata natrag (CPO sheme → PNG, MNO potrošnja). Provjera: Hubov CSV/CIX/CPW/CPO za HUMER identičan
   PPNEST-ovom / PW-ovom (D-10 test već dokazan na formatima).
2. **Korak 4 — obračun + ponuda iz Huba** (D-18/D-19/D-20/D-40): kalkulator iz `hub/optimizacija/obracun.py` + cjenik iz `pantheon_ident`, rabat s naloga,
   eSlog XML (skill krojna-ponuda), verzije ponude; usporedba s 40 ponuda iz benchmarka.
3. Paralelno kad stignu podaci: Corpus paket (D-29), uvoz Excel / rukopis kupca (skill krojna-ponuda), okov (D-32).
4. **Mockup v0.5** nakon povratnih informacija kolega (+ „mirna“ varijanta ekrana 2/3 ako Igor želi); zatim web ekrani na ovom API-ju.
5. Igor sprema prijedlog skilla krojna-ponuda (D-20) i učitava `Obrada kupaca\krojna-ponuda_v2_D20.skill` — ako još nije.

## Pravila rada koja vrijede (kratko)

Hrvatski. Nalazi u `20_ANALIZA\`, kod u `30_NOVI_PROGRAM\` (= repo, Igor pusha sam), mape 01–13 i 99_BACKUP se ne diraju. PanelWizard je
referenca i benchmark — bez mijenjanja i kopiranja koda. Pantheon samo eSlog (D-06). Na ekranima nikad riječ „AI“ ni oznake odluka (D-xx);
na radnom ekranu samo ono što korisnik u tom koraku treba, ostalo na klik (D-14). Kad Igor treba nešto izvršiti: objašnjenje + gotova cmd naredba,
bez sitnih kontrolnih koraka. Svaka nova odluka → DECISIONS (ODLUČENO / PREDLOŽENO, sa „Zašto“); ideje → IDEJE_KASNIJE; kopije na disk
(`20_ANALIZA\` + `30_NOVI_PROGRAM\docs\`) i u projekt (`claude/…`). Prije rada na kodu: prvo objasniti Igoru na čemu se radi, pa raditi.
Napomena o alatu: `device_bash` na Igorovom PC-u ne radi (Windows update 8. 9.) — datoteke se prenose stage / commit alatima.

## Datoteke po temi

| Tema | Dokument |
|---|---|
| Odluke (sve, s obrazloženjem) | `DECISIONS.md` (D-01 … D-48), stanje na dnu |
| Ideje za kasnije | `IDEJE_KASNIJE.md` (I-01 … I-16) |
| Nalog i elementi, kupci, uvoz CPW/CSV, API — korak 2 | `12_nalog_i_elementi_korak2_2026-09-13.md` (+ `12a_provjera_naloga_2026-09-13.md`) |
| Šifrarnik materijala i traka — što radi, provjera, pitanja za Igora | `11_sifrarnik_korak1_2026-09-12.md` (+ `11a_provjera_sifrarnika_2026-09-12.md`) |
| Mockup ekrana (v0.1 → v0.4), što je ugrađeno, pitanja za kolege | `07_mockup_ekrana_2026-09-11.md` |
| Checklista 23 pitanja s odgovorima | `09_checklista_odgovori_2026-09-12.md` |
| Praćenje proizvodnje i nabava — temelji u Hubu | `10_temelji_za_pracenje_i_nabavu_2026-09-12.md` |
| Corpus put naloga (vlastita proizvodnja) | `08_corpus_put_naloga_2026-09-12.md` |
| Model podataka, arhitektura, plan faze 1 | `04_model_podataka_arhitektura_plan_2026-09-10.md` |
| Formati strojeva, test D-10, benchmark 3 naloga | `02`, `05`, `06` |
| Audit (početak) | `00_audit_sazetka_2026-09-10.md`, `01`, `03` |
