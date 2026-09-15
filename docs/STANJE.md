# Paneli Production Hub — STANJE (za nastavak u novoj sesiji)

**Ažurirano: 15. 9. 2026.** — zaključno s D-64. 14. 9.: šifrarnik i debljine (D-47 … D-53), Corpus uzorak (D-55/D-56), prijedlozi spajanja (D-54), izvoz na nesting, PanelWizard i pilu (D-60/D-61). 15. 9.: unos traka i veza sa skladištem (D-61 … D-64). Ovo je jedini dokument koji treba pročitati prvi; sve ostalo je referenca.
Redoslijed čitanja u novoj sesiji: **STANJE.md → DECISIONS.md (odluke D-01 … D-64) → dokument koji se tiče zadatka** (12 nalog, 11 šifrarnik, 13 nalazi šifrarnika,
07 mockup, 09 checklista, 10 praćenje i nabava, 08 Corpus, 04 model podataka, 05/06 audit i benchmark).

## Gdje smo

**Kralježnica je gotova do kraja izvoza.** Korak 1 (šifrarnik), korak 2 (kupci, nalog, elementi) i korak 3
(nesting CSV+CIX, CPW za PanelWizard, CPO za pilu) rade i provjereni su na stvarnim nalozima. Shema je na **v7**,
**63 testa prolaze** (+5 preskočenih bez stvarnih podataka). Kod je na disku, **u Gitu još nije** — čeka `GIT_POSALJI.cmd`.

**Što slijedi:** ostatak koraka 3 (čitanje rezultata natrag iz `.mno` i CPO shema, stvarno spajanje naloga D-54/B,
uvoz Corpusovog paketa), pa korak 4 (obračun + eSlog ponuda) i Warehouse po D-64.

**Novo 15. 9.:** D-61 riješen (slovo M/A je mjesto u PW obrascu, ne vrsta trake — naplata nije bila pogrešna),
D-62 (popis traka s oznakama umjesto dva polja, proba objavljena), D-63 (veza s Regal trakom ide po TR identu),
D-64 (Warehouse je pogled nad izvorima, ne drugo brojanje).

- **Faza 1 (audit) zatvorena 11. 9.** (D-28). **Faza 2 = mockup ekrana + kralježnica aplikacije**, u tijeku.
- **Kralježnica korak 3b — CPW ZA PANELWIZARD I CPO ZA PILU GOTOVI 14. 9.** (dokument **16**, D-61). `py -m hub.nalozi.export_pw --db hub.db --nalog 9 --mapa C:\PPNESTING` i `py -m hub.nalozi.export_pila --db hub.db --nalog 9 --mapa C:\PILA`, oba i preko API-ja, oba sa `--suho`. CPW ide u `<NALOG>\PANEL WIZARD\` točno kako ga je pisao PPNEST i obuhvaća SVE materijale naloga (PW računa cijeli nalog, D-11). CPO ide u `<NALOG>\PILA\` s Hubovim brojem programa `HUB_00001` (D-22), kerfom naloga za slaganje i fizičkih 5,00 u datoteci (D-21), način bira Hub po D-19; svaki izvoz upisuje red u `optimizacija` i dokument u nalog. **Mjera uspjeha: CPO za HUMER-ov IV JELA TAVERNA 19 ima isti oblik kao PW-ov `I_01915.cpo`** (6 INV / 35 ORD / 35 PRT / 6 PAT, 19,0 / 95,0, kerf 5,00, god Y), prolazi provjeru stabla rezova, čita se natrag bajt po bajt; PW 6 ploča / 73,5 % / 30,97 m² prema Hub 6 ploča / 73,5 % / 30,89 m². Optimizator nije mijenjan (benchmark +4,0 %, 104 vs 102 ploče — ostaje za korak 4). **Nova ponovljiva provjera** `py -m hub.alati.provjera_exporta`: uveze PPNEST-ov izvoz, izveze natrag iz Huba i usporedi mjere, komade i rubove — **CSV 8/8, CPW 5/8**, a sve tri razlike su samo slovo M/A (D-61). **63 testa prolaze.**
- **Kralježnica korak 3a — IZVOZ NA NESTING GOTOV 14. 9.** (dokument **15**, D-60). `py -m hub.nalozi.export_nesting --db hub.db --nalog 9 --mapa C:\PPNESTING` + `POST /api/nalog/{id}/izvoz/nesting`. Iz naloga po materijalu nastaje CSV (isti 28-stupčani profil koji bNest već čita) i po jedan CIX za svaki element, u `<mapa>\<NALOG>\NESTING\` — mapa i imena kao dosad, bNest ne treba nikakvu izmjenu. **Mjera uspjeha ispunjena: HUMER_OMIS_9 → 2 paketa, 89 CIX, 91 datoteka; oba materijala daju ISTE ELEMENTE kao PPNEST** (54 el / 177 kom i 35 el / 48 kom, mjere, količine i sve četiri oznake trake bez razlike; CIX iznutra `LPX=820 LPY=550 LPZ=18`, `TNM=8D`, `VTR=2`). Dvije razlike od PPNEST-a: ime CIX datoteke je `H0000001` iz brojača i registra (D-23/D-60 — PPNEST-ovo ime po vremenu se ponavlja i bNest pregazi datoteku), a `SIFRA MAT` je pravi Winstore kod (D-24). Ponovni izvoz vraća ISTA imena. `--suho` pokaže što bi nastalo bez pisanja (to će ekran prikazati prije „Pošalji na nesting“). Preskače se, uz ispisan razlog: materijal poslan na pilu, nepotvrđen materijal, nepoznata debljina, deblje od 26 mm. Shema v7 (nova `cix_registar`, migracija sama upiše postojeća imena). **60 testova prolazi** (+5 preskočenih).
- **Prijedlozi spajanja naloga (D-54), 14. 9.** `py -m hub.nalozi.spajanje --db hub.db` + `GET /api/spajanje` — među nalozima koji čekaju rezanje traži isti materijal i predlaže zajedničko rezanje na nestingu (uvjet: zbroj ≥ 1 ploča; naloge na restlu preskače). Na 8 testnih naloga: 5 prijedloga, 5 naloga bi umjesto na pilu otišlo na nesting, razlika 7 ploča. Provjereno da bSolid etiketa već nosi naziv naloga, pa operater na nestingu može razvrstati dijelove. Stvarno spajanje (jedan CSV+CIX paket) je korak 3.
- **D-61 RIJEŠENO (Igor, 15. 9.):** slovo `M`/`A` uz rub u CPW-u nije vrsta trake nego **mjesto u PW obrascu** — PW ima dva polja za naziv trake („ABS" i „MEL"), pa kad nalog treba dvije različite ABS trake druga ide u MEL polje; inače bi se naziv brisao i pretipkavao za svaki element, jer kupci na papiru izmjenjuju trake iz elementa u element. Primjer BOGDANIC: PW statistika pokazuje `ABS: 1/22 OF CHAMPAGNE 65,010 m`, `MEL: 0,000 m`, `MEL: 1/22 AVIVA DEW 33,409 m` — druga ABS traka u praznom MEL slotu. Ivana iz te statistike čita pravi naziv i u Pantheon unosi ABS, pa **naplata nije bila pogrešna**. Mjerodavan je naziv trake; Hub slovo izvodi iz prepoznate trake i time je ispravan. Razilazi se 70 od 474 ruba (15 %) na 8 testnih naloga.
- **D-62 ODLUČENO (Igor, 15. 9.) — unos traka:** materijal naloga nema fiksna dva polja nego **popis koji počinje s `ABS-ISTI` i `MEL-ISTI` (isti dekor kao materijal) i raste na `+ ABS traka` / `+ MEL traka`**; svaka traka ima vrstu, naziv iz šifrarnika, boju i kratku oznaku (`A1`, `A2`, `M1`…) koja se upisuje uz element umjesto cijelog naziva. **Uz svaki rub stoji kućica vidljiva i kad je prazna** — klik stavlja aktivnu traku, ponovni klik je miče; dvoklik u sredinu stavlja je na sva četiri ruba, sljedeći dvoklik briše sve. Ne generalizira se po materijalu; upozorenje za dvije trake istog dekora različite debljine ne treba. Mijenja D-59 (dvoklik više ne vrti ABS → MEL → bez). Proba: `30_NOVI_PROGRAM\docs\mockup\trake_naloga.html` (artefakt „Trake naloga“). Ulazi u mockup v0.5.
- **D-63 PREDLOŽENO (15. 9.) — veza Hub ↔ Regal traka:** ključ je **Pantheon ident trake** (`TR001254`), koji obje strane već koriste — Regal traka se gradi iz istog `ph_identi.csv`, a njezin QR nosi punu adresu s identom (`http://192.168.5.201:8080/t/TR000103`); u Hubovoj tablici `traka` stupac `regal_traka_ident` postoji od prvog dana. Oznaka `A1`/`M1` iz D-62 ne izlazi iz ekrana za unos. Hub Regal traku samo ČITA (`GET /api/stanje`: `lok` ident → pretinac, `q` ident → metri), bez refaktora (D-07). Novo što Hub može dati: pick-lista po nalogu (koja traka, koliko metara, koji pretinac), provjera ima li dovoljno metara prije rezanja, i potreba za nabavu preko svih potvrđenih naloga (D-42/5). **Otvoreno:** ekran ili ispis pick-liste; tko je dugoročno vlasnik metara (D-02 kaže Hub, a fizički se broji kod kanterice); treba li TR ident i na etiketu.
- **D-64 ODLUČENO (Igor, 15. 9.) — Warehouse je POGLED, ne drugo brojanje.** Svaka količina ima jednog vlasnika i Hub je vuče od njega: **pune ploče → Winstore** (dnevni XML, već radi), **restlovi → modul RESTLOVI u Hubu** (vode ga skladištari), **trake → Regal traka** (kasnije možda modul Huba). Hub nigdje ne vodi paralelni fizički broj; dodaje rezervaciju i računicu raspoloživo = fizičko − rezervirano + naručeno (D-42/4) te potrebu preko svih potvrđenih naloga (D-42/5). Provedbeno: svaki izvor ima JEDAN prilagodnik istog sučelja (`hub/skladiste/ploce.py`, `restlovi.py`, `trake.py`), pa kad Regal traka postane modul Huba mijenja se samo ta datoteka. **Otvoreno:** pokriva li Winstore sve pune ploče (o tome ovisi treba li `ploca_stanje`); je li RESTLOVI nov modul ili preseljenje Excela V3; tko otvara restl — Hub ga iz sheme zna predložiti, skladištar potvrđuje.
- **Corpus uzorak stigao i analiziran (D-55, D-56), 14. 9.** — dokument **14**. Tehnička priprema napunila `_CORPUS_UZORAK` projektom TEST BUSENJE (15 komada, 3 materijala, bušenje + utori + krivolinija, cijeli lanac do ponude 26-010-003406) i odgovorila na svih 7 pitanja. Nalazi: Corpusov CSV ima 4 drukčija imena stupaca od PPNEST-ovog (Hubov čitač je pucao — **popravljeno**, sada čita oba i iz Corpusa vadi cjelinu, poziciju i oba CIX programa); CSV ≠ CPW je podjela puta, ne greška (MDF leđa uvijek na pilu); element može imati dva CIX-a (vertikalni + horizontalno bušenje); CIX je standardni bSolid pa Hub iz njega čita obradu bez diranja; nakon dviju Igorovih dopuna (D-57 nut od 4 mm za MDF 3 mm → šifra je jača od deklarirane debljine; D-58 „siva tamna" = „sivi tamni") sva tri Corpusova materijala prolaze sigurno. **D-29 i D-30 potvrđeni → ODLUČENO.** Benchmark: CPO 47/50 i 40/40 nepromijenjeno, **CPW 40/40**, CSV 32/33, trake 44/51.
- **Debljina ploče (D-52) i kriva klasifikacija (D-53), 14. 9.** Radne ploče i ploče stola su 38 mm — Hub upisuje sam (281 ident); compact i zidne obloge Hub NE pogađa (varira 6/8/12/13 i 8/18) nego ured potvrdi jednom po identu kroz obrazac `13_compact_i_zidne_debljine.csv`. Prednost: naziv u Pantheonu → ručni upis → pravilo po vrsti → Winstore (`materijal.debljina_izvor`). Debljina se čita i iz dimenzije (`4100X640X8MM`), 13 mm dodan u popis debljina. 4 identa „TRAKA ZA R.P.“ pod RP prefiksom više nisu materijali. Ured je 14. 9. popunio obrazac (47 identa) i označio `IV000698` kao neupotrebljavan: **popis identa bez debljine 586 → 236, a svi preostali su stari dekori — pitanja o debljini više nema**. Odluke su u `hub/sifrarnici/podaci/ispravci_sifrarnika.csv` (53 retka) i primjenjuju se pri svakom uvozu. Shema v6, 57 testova prolazi.
- **Ispravci ureda žive u Hubu (D-51, 14. 9.).** Ured u Hubu upisuje debljinu koje nema u Pantheonu, oznaku „ident se ne koristi“ i ručnu vezu Winstore kod → ident; sve preživljava svaki uvoz (`py -m hub.sifrarnici.ispravci`, sjeme u `hub/sifrarnici/podaci/ispravci_sifrarnika.csv`, shema v5). Igorovi odgovori na 4 identa iz 13 §1.1 su upisani → **razred „isti ident za više debljina“ je prazan**, ostaje 12 identa za dopisivanje debljine. Prepoznavanje nepromijenjeno: 47/50 CPO, 40/40 vs ponuda, 37/37 CPW, 30/31 CSV, 42/48 trake; nalozi 7/8, 999 elemenata, 2 248 komada.
- **14. 9. — dorada nakon Igorovog pokretanja na PC-u i tri odluke.** Igor odlučio: **D-47** brojač naloga kreće od 1 (probni nalozi ga više ne troše — dobivaju `PROV-nnn`, pa je prvi stvarni uvijek `2026-00001`); **D-49** ambalažne ploče u Winstoreu nisu roba (podloge za slaganje) — ne vode se na stanju, ne povezuju se s identom; **D-50** e-mail kupca upisuje ured u Hub, Pantheon ga nema i izvoz se ne proširuje. Uz to: debljina se preuzima iz Winstorea kad je jednoznačna, prijedlozi povezivanja su sada isti u svakom uvozu (ne ovise o redoslijedu), `_PREDLOZAK_NALOGA` se preskače, dnevni ispis uvoza je kratak (`--detaljno` za sve). **Novi alat `py -m hub.sifrarnici.nalazi`** → dokument **13** + `13_identi_bez_debljine.csv`: popis za ured je pao s „586 identa bez debljine“ na **16 identa + 12 Winstore kodova**. Shema v4 (automatska migracija). 54 testa prolaze (+5 preskočenih bez stvarnih podataka).
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

1. **`GIT_POSALJI.cmd`** — u repo ulaze koraci 1, 2 i 3 (nesting, PanelWizard, pila) + dorada od 14./15. 9. (Igor je 13. 9. sve pokrenuo na PC-u, brojke potvrđene). Novo od zadnjeg commita:
   `hub\schema.sql` (v7), `hub\db.py`, `hub\nalozi\export_nesting.py`, `export_pw.py`, `export_pila.py` (sve novo), `hub\nalozi\nalozi.py` (`tip_ruba`), `hub\api\nalozi_api.py` (3 nova izvoza), `hub\alati\provjera_exporta.py` (novo), `hub\formati\cix_bsolid_template.cix`, `tests\test_nalozi.py`, `README.md`, `docs\15_*`, `docs\16_*`, `docs\DECISIONS.md`, `docs\STANJE.md`, `docs\mockup\trake_naloga.html`.
2. **Ured / operater: ostatak po dokumentu 13** — (a) `U125ST9-18 IVERAL PJESCANO ZUTI 18MM` (2 ploče na stanju): ponuđeni `IV001312` ne postoji, treba pravi ident ili otvoriti novi; (b) `1111PO-18 POVRAT OSTECENO` (1 ploča): dogovoriti kako se vodi oštećena vraćena roba; (c) dvije izmjene šifre u Winstoreu koje je Igor potvrdio: `U999TM28-18` → 19,6 mm i `IV001027` (hrast furnir 26 mm) dobiva novi kod; `MOSAICOFB35` se ispravlja u Pantheonu na 19 mm (Hub je u međuvremenu točan preko ispravka `debljina_umjesto_naziva`).
   Ne blokira Hub (odluke se mogu upisati i u Hub, D-51); kad se napravi, ponovni `py -m hub.sifrarnici.nalazi` pokaže prazne popise.
   Novo: **`IV000065-25`** (IVERAL FURNIR HRAST 25 mm, 1 ploča na stanju) nema ident u Pantheonu — otvoriti ga ili operater preimenuje kod.
3. **D-63 / D-64** — pick-lista traka: ekran ili ispis? Treba li TR ident na etiketi uz današnju oznaku trake? Pokriva li Winstore sve pune ploče (radne ploče 4100, compact) ili ih ima izvan njegova regala? Je li modul RESTLOVI nov ili preseljenje Excela V3? Tko otvara restl — Hub predlaže iz sheme, skladištar potvrđuje?
4. **D-44** — zidne obloge bez identa (ZO HR EVOKE SUNSET, ZO HR CREMONA CANNOLO): kako se naplaćuju / otvoriti ident? (11 §5.1)
5. **D-45 (c)** — trake koje nedostaju za dekore koji se kantiraju: CRNA NK u širini 22, CHAMPAGNE UM, PVC CRNI MAT VSM-02 → otvoriti u Pantheonu.
6. Korak 4 (eSlog): provjeriti na probnoj ponudi da Pantheon uzme kupca iz uloge BY („Krajnji kupac“ / subjekt tvrtke) i napomenu s imenom osobe (D-48).
7. Pružatelj e-pošte za `paneliprojekt.hr` (Microsoft 365 / Google / hosting) → potvrda D-41.
8. Prezentacija mockupa v0.4 Ivani, Goranu, Saneli i voditelju (pitanja za njih u 07 §4c) → povratne informacije → v0.5.
9. ~~Corpus uzorak~~ — **stigao 14. 9., analiziran (dokument 14)**. Staro: **mapa je pripremljena**: `05_NALOZI_ZA_TEST\_CORPUS_UZORAK\` (STO_OVDJE, UPUTA, PITANJA, NALOG + 6 podmapa).
   Tehnička priprema puni jedan projekt s bušenjem, utorom i krivolinijom + odgovara na 7 pitanja iz 08 §6.
   Minimum da se može krenuti: CSV za nesting + 3 CIX + 1 CPW iz iste mape izvoza.
10. Popis dekora „samo cijela ploča“ (D-37b) — kasnije, nije bitan.

## Sljedeći koraci (redom)

1. **Kralježnica korak 3 — ostatak** (04 §4). ~~CSV + CIX za bNest~~ (dokument 15), ~~CPW za PanelWizard~~, ~~CPO za pilu~~ (dokument 16) — **gotovo 14. 9.** Ostaje:
   (a) **čitanje rezultata natrag** — CPO sheme → PNG za operatera, stvarna potrošnja iz `.mno` i razdioba po nalozima (D-38);
   (b) **stvarno spajanje malih naloga (D-54, korak B)** — prijedlozi već rade (`py -m hub.nalozi.spajanje`), sada dolazi jedan zajednički
   CSV+CIX paket uz oznaku NJEGOVOG naloga na svakom elementu (etiketa je već nosi) i razdioba potrošnje natrag;
   (c) **uvoz Corpusovog paketa** (D-55 točka 3 — element s dva CIX-a, vertikalni + horizontalno bušenje).
2. **Korak 4 — obračun + ponuda iz Huba** (D-18/D-19/D-20/D-40): kalkulator iz `hub/optimizacija/obracun.py` + cjenik iz `pantheon_ident`, rabat s naloga,
   eSlog XML (skill krojna-ponuda), verzije ponude; usporedba s 40 ponuda iz benchmarka.
3. Paralelno kad stignu podaci: Corpus paket (D-29), uvoz Excel / rukopis kupca (skill krojna-ponuda), okov (D-32).
4. **Mockup v0.5** — ugraditi skicu elementa koja prati mjere i dvoklik za sve rubove (D-59; proba: `docs/mockup/skica_elementa.html`) te popis traka s oznakama (D-62; proba: `docs/mockup/trake_naloga.html`), pa ostalo nakon povratnih informacija kolega (+ „mirna“ varijanta ekrana 2/3 ako Igor želi); zatim web ekrani na ovom API-ju.
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
| Odluke (sve, s obrazloženjem) | `DECISIONS.md` (D-01 … D-64), stanje na dnu |
| Ideje za kasnije | `IDEJE_KASNIJE.md` (I-01 … I-16) |
| Izvoz na nesting (CSV + CIX za bNest) — korak 3a | **`15_izvoz_nesting_korak3a_2026-09-14.md`** |
| Izvoz za PanelWizard (CPW) i pilu (CPO), provjera izvoza — korak 3b | **`16_izvoz_pw_i_pila_korak3b_2026-09-14.md`** (+ `provjera_exporta.md`) |
| Nalog i elementi, kupci, uvoz CPW/CSV, API — korak 2 | `12_nalog_i_elementi_korak2_2026-09-13.md` (+ `12a_provjera_naloga_2026-09-13.md`) |
| Šifrarnik materijala i traka — što radi, provjera, pitanja za Igora | `11_sifrarnik_korak1_2026-09-12.md` (+ `11a_provjera_sifrarnika_2026-09-12.md`) |
| Nalazi o šifrarniku — što ured ispravlja (generira se) | `13_nalazi_sifrarnika_2026-09-14.md` (+ `13_identi_bez_debljine.csv`, obrazac `13_compact_i_zidne_debljine.csv`) |
| Mockup ekrana (v0.1 → v0.4), što je ugrađeno, pitanja za kolege | `07_mockup_ekrana_2026-09-11.md` |
| Checklista 23 pitanja s odgovorima | `09_checklista_odgovori_2026-09-12.md` |
| Praćenje proizvodnje i nabava — temelji u Hubu | `10_temelji_za_pracenje_i_nabavu_2026-09-12.md` |
| Corpus put naloga (vlastita proizvodnja) | `08_corpus_put_naloga_2026-09-12.md` + **`14_corpus_uzorak_nalazi_2026-09-14.md`** (uzorak, odgovori, nalazi) |
| Model podataka, arhitektura, plan faze 1 | `04_model_podataka_arhitektura_plan_2026-09-10.md` |
| Formati strojeva, test D-10, benchmark 3 naloga | `02`, `05`, `06` |
| Audit (početak) | `00_audit_sazetka_2026-09-10.md`, `01`, `03` |
