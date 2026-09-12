# Paneli Production Hub — STANJE (za nastavak u novoj sesiji)

**Ažurirano: 12. 9. 2026. navečer.** Ovo je jedini dokument koji treba pročitati prvi; sve ostalo je referenca.
Redoslijed čitanja u novoj sesiji: **STANJE.md → DECISIONS.md (odluke D-01 … D-42) → dokument koji se tiče zadatka** (07 mockup, 09 checklista,
10 praćenje i nabava, 08 Corpus, 04 model podataka, 05/06 audit i benchmark).

## Gdje smo

- **Faza 1 (audit) zatvorena 11. 9.** (D-28). **Faza 2 = mockup ekrana + odluke o toku**, u tijeku. Kod Huba (kralježnica po 04 §4) još NIJE počeo —
  kreće kad Igor odobri mockup v0.3 s Ivanom, Goranom i voditeljem proizvodnje.
- **Mockup v0.3.1** (12. 9.): 6 ekrana u dizajnu D (D-39) — popis naloga, unos, okov i obrade, obračun → ponuda (čeka kupca), skladište nakon
  potvrde (novi), pila / nesting. Platno = artefakt „Production Hub — mockup ekrana“ (verzija 16); slike `20_ANALIZA\mockup\v03_*.png`; izvor
  `30_NOVI_PROGRAM\docs\mockup\v03\` (`build_v03.py` + `v03_base.py`, Python → `.dc.html`, platno se sastavlja skriptom `seed-canvas` iz skilla design).
  Stare varijante: `20_ANALIZA\mockup\ARHIVIRAJ_STARE.cmd` ih seli u `arhiva\` (Igor pokreće; nisam mogao premještati).
- **Checklista 09 zatvorena**: svih 23 pitanja odgovoreno → D-33 … D-38. Tok naloga (D-35): Unos → Ponuda (čeka kupca) → Potvrđeno →
  Skladište (upozorenje + popis za nabavu) → Pila / nesting → Proizvodnja → Zatvoren.
- **Ponuda ide iz Huba** (D-40): cijene iz dnevne sinkronizacije Pantheona (nepromjenjive u Hubu), rabat po kupcu u Hubu s DVIJE stope
  (materijal + okov + ostalo / usluge rezanja i kantiranja — u 2823: 15 % / 20 %), PDF + mail kupcu iz Huba, ured ručno upisuje potvrdu, eSlog u
  Pantheon tek nakon potvrde. Slanje maila: D-41 PREDLOŽENO (sandučić `ponuda@paneliprojekt.hr` kod postojećeg pružatelja, SMTP) — **čeka odgovor
  tko vodi e-poštu za paneliprojekt.hr**.
- **Temelji za praćenje proizvodnje i nabavu** (D-42, dokument 10): jedinica praćenja nalog × materijal × stroj; dnevnik događaja, rokovi
  (`rok_obecan` = službeni), osobe po koraku, rezervacije; narudžbenice u Hubu (modul `nabava`, zamjena za stari sustav narudžbi koji koristi
  Sanela; pregled potreba preko svih naloga + narudžba unaprijed), zatvaranje automatski iz eSlog primke; Knjiga se ne mijenja.

## Otvoreno / čeka Igora

1. Pružatelj e-pošte za `paneliprojekt.hr` (Microsoft 365 / Google / hosting) → potvrda D-41.
2. Popis dobavljača / dekora „samo cijela ploča“ (D-37b) — Igor dopunjuje kasnije, sada nije bitan.
3. Igor pokreće `ARHIVIRAJ_STARE.cmd` i šalje repozitorij (`30_NOVI_PROGRAM\GIT_POSALJI.cmd`) — u repo su ušli 09, 10, DECISIONS, IDEJE, 07, mockup v03.
4. Prezentacija mockupa v0.3 Ivani, Goranu i voditelju (najviše se tiču ekrani 4 i 5); povratne informacije → v0.4.

## Sljedeći koraci (redom)

1. **Mockup v0.4** nakon povratnih informacija: ekran 3 s glavnom akcijom „Pošalji kupcu“ i eSlog-om uz „Kupac potvrdio“ (D-40), rabat kupca u
   zaglavlju, **novi ekran „Nabava“** za Sanelu (pregled potreba + narudžbenice, D-42), po potrebi ekran događaja naloga (vremenska crta).
2. **Corpus uzorak** (08 §6): tehnička priprema daje jedan paket (CPW + CSV + CIX) i odgovara na 7 pitanja → provjera D-29/D-30 na stvarnom nalogu.
3. **Kralježnica Huba** (04 §4, koraci 1–7) — tek kad Igor odobri mockup; prvo šifrarnik materijala/traka s aliasima, pa nalog + elementi, uvoz
   CPW/Excel, exporti (D-10 već dokazano), čitanje CPO/MNO, obračun + eSlog, restlovi. Uz to od početka: polja i tablice iz 10 §4 (događaji,
   rokovi, rezervacije, narudžbenice, operacije) i API.
4. Igor sprema prijedlog skilla krojna-ponuda (D-20) i učitava `Obrada kupaca\krojna-ponuda_v2_D20.skill` — ako još nije.

## Pravila rada koja vrijede (kratko)

Hrvatski. Nalazi u `20_ANALIZA\`, kod u `30_NOVI_PROGRAM\` (= repo, Igor pusha sam), mape 01–13 i 99_BACKUP se ne diraju. PanelWizard je
referenca i benchmark — bez mijenjanja i kopiranja koda. Pantheon samo eSlog (D-06). Na ekranima nikad riječ „AI“ ni oznake odluka (D-xx);
na radnom ekranu samo ono što korisnik u tom koraku treba, ostalo na klik (D-14). Kad Igor treba nešto izvršiti: objašnjenje + gotova cmd naredba,
bez sitnih kontrolnih koraka. Svaka nova odluka → DECISIONS (ODLUČENO / PREDLOŽENO, sa „Zašto“); ideje → IDEJE_KASNIJE; kopije na disk
(`20_ANALIZA\` + `30_NOVI_PROGRAM\docs\`) i u projekt (`claude/…`).

## Datoteke po temi

| Tema | Dokument |
|---|---|
| Odluke (sve, s obrazloženjem) | `DECISIONS.md` (D-01 … D-42), stanje na dnu |
| Ideje za kasnije | `IDEJE_KASNIJE.md` (I-01 … I-16) |
| Mockup ekrana (v0.1 → v0.3.1), što je ugrađeno | `07_mockup_ekrana_2026-09-11.md` |
| Checklista 23 pitanja s odgovorima | `09_checklista_odgovori_2026-09-12.md` |
| Praćenje proizvodnje i nabava — temelji u Hubu | `10_temelji_za_pracenje_i_nabavu_2026-09-12.md` |
| Corpus put naloga (vlastita proizvodnja) | `08_corpus_put_naloga_2026-09-12.md` |
| Model podataka, arhitektura, plan faze 1 | `04_model_podataka_arhitektura_plan_2026-09-10.md` |
| Formati strojeva, test D-10, benchmark 3 naloga | `02`, `05`, `06` |
| Audit (početak) | `00_audit_sazetka_2026-09-10.md`, `01`, `03` |
