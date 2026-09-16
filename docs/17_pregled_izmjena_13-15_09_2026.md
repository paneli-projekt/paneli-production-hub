# 17 — Pregled izmjena u Hubu 13.–15. 9. 2026. (rad Opusa) — nalazi

**Datum pregleda:** 15. 9. 2026. · **Popravci:** isti dan popodne, vidi §G i D-65 · **Opseg:** Git `30_NOVI_PROGRAM`, commitovi `554c7df` (12. 9. 14:41, prethodno stanje) → `8fdda8f` (14. 9.) → `ad52930` (15. 9. 10:53, HEAD).
62 datoteka, +10 244 / −53 redaka. **Nespremljenih izmjena nema** (`git status` čist; samo ignorirano: `hub.db`, `__pycache__`, PNG-ovi).
Ništa nije mijenjano — ovo je samo izvještaj.

**Kako je provjeravano:** kod pročitan modul po modul (db, schema, nalozi, uvoz, sva tri izvoza, API, šifrarnik, kupci, spajanje, provjere),
testovi pokrenuti bez i sa stvarnim podacima (`HUB_TEST_DATA = 05_NALOZI_ZA_TEST`), svaka sumnja iz čitanja potvrđena posebnom probom
(kratki pytest koji poziva stvarne funkcije), dnevni uvoz šifrarnika i `provjera_exporta` pokrenuti na **kopiji** stvarnog `hub.db`.
Okruženje: Linux VM, Python 3.10 (Igorov PC: Windows, Python 3.14) — vidi „Što nisam mogao provjeriti“.

## Sažetak

| | Broj |
|---|---|
| Potvrđene greške (reproducirano) | 10 |
| Rizici za podatke / propusti prema planu (potvrđeno kodom ili probom) | 6 |
| Sumnje (nisu dokazane, treba odluka ili dublja provjera) | 5 |
| Dokumentacija zastarjela / netočna | 4 |

Testovi: **bez stvarnih podataka 72 prolaze + 5 preskočenih** (STANJE kaže 63 — brojka je zastarjela, ali smjer je dobar).
**Sa stvarnim podacima 2 od 5 „stvarnih“ testova padaju** (točke 9 i 10) — ti testovi u Opusovim sesijama nisu ni pokretani
(„+5 preskočenih bez stvarnih podataka“), pa tvrdnje „63 testa prolaze“ nikad nisu obuhvatile Corpus uzorak.

Najvažnije za Igora, po redu: **1** (dva API izvoza ne rade), **3** (brisanje elementa nakon izvoza ruši se), **5** (nazivi elemenata gube se u CPW-u),
**11** (Winstore stanje se zbraja iz dana u dan), **13** (prvi stvarni nalog neće biti 2026-00001).

---

## A. Potvrđene greške

### 1. API izvoz za PanelWizard i za pilu ne radi — HTTP 500 (VISOKO)
- **Datoteka:** `hub/api/nalozi_api.py`, redak 265 (`EW.izvezi`) i 283 (`EP.izvezi`); uvoz modula je samo u retku 36 (`export_nesting as EX`).
- **Dokaz:** `EW` i `EP` nigdje nisu definirani → `NameError`. Proba kroz `TestClient`: `POST /api/nalog/{id}/izvoz/pw` → **500**, `POST …/izvoz/pila` → **500**, `…/izvoz/nesting` → 200.
  Dokument 16 i STANJE tvrde „oba i preko API-ja“ — to nije točno; CLI (`py -m hub.nalozi.export_pw / export_pila`) radi.
- **Zašto testovi nisu uhvatili:** `tests/test_api.py` i `test_nalozi.py::test_api_nalozi` ne zovu te dvije rute.
- **Popravak:** u redak 36 dodati `export_pw as EW, export_pila as EP`; dodati test koji zove obje rute sa `suho=true`.

### 2. `provjera_exporta --obrisi` ruši se, probni nalozi ostaju u bazi (SREDNJE)
- **Datoteka:** `hub/alati/provjera_exporta.py`, redak 236: `N.obrisi_nalog(conn, …)` — funkcija **ne postoji** u `hub/nalozi/nalozi.py` (grep: nema `def obrisi_nalog` nigdje u repozitoriju).
- **Dokaz:** pokrenuto na kopiji stvarne baze s `--obrisi`: izvještaj se ispiše, zatim `AttributeError`; nakon dva pokretanja u bazi ostaje **32 probna naloga / 1 756 elemenata**. README (korak 9) preporučuje upravo `--obrisi`.
- **Popravak:** koristiti `provjera.obrisi_provjere(conn)` (postoji u `hub/nalozi/provjera.py`) — ali vidi točku 3, jer ni ona ne pokriva sve ovisnosti.

### 3. Nakon izvoza na nesting element / materijal se više ne može obrisati — `FOREIGN KEY constraint failed` (VISOKO)
- **Datoteke:** `hub/schema.sql` redak 297 (`cix_registar.element_id REFERENCES element (id)` bez `ON DELETE SET NULL`), `hub/nalozi/nalozi.py` redci 277–278 (`obrisi_materijal`) i 402 (`obrisi_element`), `hub/nalozi/provjera.py` redci 149–153 (`obrisi_provjere` briše element / nalog_materijal / dogadjaj / dokument / nalog, ali ne `cix_registar` ni `optimizacija`).
- **Dokaz (proba):** nalog → `export_nesting.izvezi` → `obrisi_element` → `IntegrityError: FOREIGN KEY constraint failed`; isto `obrisi_materijal`; isto `obrisi_provjere` nakon nesting + pila izvoza. Kroz API to je HTTP 500 (`_greska` hvata samo `NalogGreska`).
  Komentar u shemi kaže „NULL kad je element obrisan — ime se NIKAD ne oslobađa“, ali to nitko ne provodi.
- **Posljedica:** čim se nalog jednom izveze (a upravo je izvoz HUMER_OMIS_9 opisan u STANJE-u), ured više ne može ispraviti taj nalog brisanjem stavke; `provjera --obrisi` puca.
- **Popravak:** u `obrisi_element` / `obrisi_materijal` / `obrisi_provjere` prije brisanja `UPDATE cix_registar SET element_id = NULL WHERE element_id IN (…)` (ime ostaje zauzeto — točno po D-23/D-60), obrisati i `optimizacija` retke za `nalog_materijal`; ili u shemi `ON DELETE SET NULL` (za postojeće baze treba REBUILD migracija).

### 4. Potvrda trake bez pamćenja (`zapamti=false`) ne radi ništa (SREDNJE)
- **Datoteka:** `hub/nalozi/nalozi.py`, redci 414–429 (`potvrdi_traku_naloga`); API `POST /api/nalog/materijal/{nm}/potvrdi-traku` s `zapamti=false`.
- **Dokaz (proba):** rub `taverna` nesiguran → `potvrdi_traku_naloga(…, zapamti=False)` → `rub1_traka_id` i dalje `None`, `provjeri` i dalje 1. Sa `zapamti=True` radi.
- **Zašto:** grana `zapamti=False` upiše `traka_id` u elemente, ali ne spusti `provjeri`, a odmah zatim `_prepoznaj_rubove(samo_provjeri=True)` ponovno prepozna te iste elemente i (jer aliasa nema) vrati rubove na `NULL`. Uz to se uspoređuje `UPPER(rub_kod)` s `norm(oznaka)` (norm skida dijakritiku, UPPER ne).
- **Popravak:** u toj grani postaviti `traka_id` i preračunati `provjeri` bez ponovnog prepoznavanja tih rubova (ili ponovno prepoznavanje preskočiti za rubove koji već imaju `traka_id`); usporedbu raditi preko `norm()` s obje strane.

### 5. Naziv elementa iz CPW-a gubi se pri izvozu u CPW; Corpusova cjelina/pozicija i PPNEST GLODANJE ne vraćaju se u CSV (SREDNJE)
- **Datoteke:** `hub/nalozi/uvoz_datoteka.py` redak 80 (2. polje CPW-a sprema se u `element.naziv`), `hub/nalozi/nalozi.py` redak 516 (u export-zapis ide `napomena=el["napomena_etiketa"]`, `naziv` se ne prenosi), `hub/formati/nalog_io.py` redak 214 (`write_cpw` u 2. polje piše `napomena`), redci 137–145 (`write_ppnest_csv`: `NAZIV ELEMENTA`, `IME DASKE`, `PROGRAM1/2` uvijek prazni, `GLODANJE` se ponovno računa iz mjera).
- **Dokaz (proba):** `a_bijeli.CPW` redak `ELEMENT;bok;700;400;2;M;;M;…` → nakon uvoza i `export_pw` Hub piše `ELEMENT;;700;400;2;M;;M;…` — naziv „bok“ nestao (u bazi je: `element.naziv = 'bok'`).
- **Zašto to provjera nije vidjela:** `provjera_exporta` uspoređuje samo debljinu, mjere, komade i masku rubova (namjerno), a PPNEST-ovi CPW-ovi imaju to polje prazno. Kupčev PPW (HUMER, 121 el.) i Corpusov CPW ga imaju popunjeno — i to je ono što ured i PW vide na krojnoj listi. Za Corpus je uz to `D-55 (5)` rekao da ID elementa iz Corpusa mora ostati.
- **Popravak:** u `elementi_za_export` prenijeti i `naziv`, `cjelina`, `pozicija`, `program1/2`; `write_cpw` u 2. polje pisati `naziv` (napomena ide na etiketu, ne u CPW); `write_ppnest_csv` popuniti `NAZIV ELEMENTA` / `IME DASKE` / `PROGRAM1/2` kad postoje; `prolaza` spremiti u element (danas nema stupca) ili barem ne pregaziti vrijednost iz CSV-a.

### 6. Element se može mijenjati i brisati u bilo kojem statusu, i nakon izvoza na stroj (SREDNJE)
- **Datoteka:** `hub/nalozi/nalozi.py` redci 380–404: `uredi_element` i `obrisi_element` nemaju provjeru statusa (za razliku od `dodaj_element`, `dodaj_materijal`, `obrisi_materijal` koji dopuštaju samo `unos` / `ponuda`).
- **Dokaz (proba):** nalog u statusu `pila_nesting` → `uredi_element(L=1234)` prolazi, `obrisi_element` prolazi.
- **Posljedica:** mjere u bazi i u već poslanom CIX/CSV/CPO/CPW-u razilaze se bez traga (D-35 tok, obračun po D-18); u kombinaciji s točkom 8 (izvoz ne provjerava `provjeri`) na stroj može otići rub koji je poslije uvoza promijenjen i nije potvrđen.
- **Popravak:** ista provjera statusa kao u `dodaj_element`; kasnije (praćenje) verzija naloga.

### 7. Neuspjeli izvoz ostavlja otvorenu transakciju na dijeljenoj API vezi — sljedeći tuđi zahtjev je commita (SREDNJE)
- **Datoteke:** `hub/api/app.py` redci 37–45 (jedna dijeljena veza), `hub/api/nalozi_api.py` redci 50–54 (`_greska` nema rollback; `izvoz/*` hvataju samo `ExportGreska`), `hub/nalozi/export_pila.py` redak 72 (`novi_program` troši brojač prije pisanja datoteke), `export_nesting.py` redci 128–133 (dokumenti se upisuju paket po paket).
- **Dokaz (proba):** `export_pila.izvezi` na mapu u koju se ne može pisati → `FileNotFoundError`; veza ostaje `in_transaction=True` s `brojac_pila=1` neupisanim; prvi sljedeći `commit()` (bilo koji zahtjev) ga trajno upiše. Isti obrazac vrijedi za djelomično upisane `dokument` retke kad padne pisanje 2. paketa.
- **Popravak:** u API-ju oko svake radnje `try/except Exception: conn.rollback(); raise`; u izvozima brojač/dokumente upisivati tek nakon uspješnog pisanja svih datoteka (ili sve u jednoj transakciji s commitom na kraju).

### 8. Događaji izvoza upisuju se bez korisnika (NISKO)
- **Datoteke:** `export_nesting.py` 141–143, `export_pw.py` 73–75, `export_pila.py` 101–103: `(SELECT id FROM korisnik WHERE oznaka = ?)` s `tko` kakav je stigao (`web`, `ivana`), dok `nalozi.korisnik_id` uppercasea i ima rezervu `WEB`.
- **Dokaz (proba):** `izvezi(…, tko="ivana")` → događaj „izvoz na nesting“ ima `tko = None`; događaj „nalog otvoren“ istog korisnika ima `IVANA`.
- **Popravak:** koristiti `N.korisnik_id(conn, tko)`.

### 9. Test `test_prihvacanje_cpo_i_ponude` pada na stvarnim podacima (SREDNJE — tvrdnja u dokumentaciji netočna)
- **Datoteka:** `tests/test_sifrarnik.py` redak 455; podatak `05_NALOZI_ZA_TEST/_CORPUS_UZORAK/03_export_pila/S0_06374.cpo`.
- **Dokaz:** nesigurni CPO materijali: 3 × ZO (dopušteno) **+ `S0_06374.cpo` „MDF BIJELI 4 MM“ → `za_potvrdu`**. Test dopušta samo ZO. Dokument 14 §5 kaže „CPO 47/50 nepromijenjeno“ — ali s Corpusom CPO-ova je 53, a Corpusov CPO nema Winstore kod pa D-57 (šifra jača od debljine) tu ne pomaže: „MDF BIJELI 4 MM“ traži ident od 4 mm kojeg nema.
- **Što treba odlučiti:** je li „MDF BIJELI 4 MM“ u CPO-u legitiman `za_potvrdu` (onda test i dokument 14 popraviti) ili alias `MDF BIJELI 4 MM → IV000054` treba upisati (D-57 to zapravo i kaže) — tada prolazi bez potvrde.

### 10. Test `test_cpo_roundtrip_identican` pada na Corpusovim CPO-ima — `cpo_rw` gubi oznaku elementa (SREDNJE)
- **Datoteka:** `tests/test_formati.py` redak 14; `hub/formati/cpo_rw.py` (nije mijenjan u ovom razdoblju — greška je **otkrivena** novim podacima, ne unesena).
- **Dokaz:** sva 3 Corpusova CPO-a (`S0_06372/73/74`) se ne vraćaju bajt po bajt: `ORD2,   5.995,-  …,EL_BU` → Hub piše `,     ` (polje s imenom elementa iz Corpusa — `EL_BU`, `FR1 -` — parser ga ispušta). 50 PW-ovih CPO-a i dalje prolazi.
- **Posljedica:** čitanje rezultata pile natrag (korak 3a) i D-55 (5) „ID elementa iz Corpusa mora ostati“ — za Corpusove programe pile gubi se veza element ↔ komad.
- **Popravak:** `cpo_rw.parse/write` prenijeti to polje ORD2 zapisa; test ostaje kakav jest.

---

## B. Rizici za podatke i propusti prema planu (potvrđeno)

### 11. Winstore stanje se zbraja iz dana u dan — dnevni XML s novim imenom NE zamjenjuje stari (VISOKO za Warehouse, D-64)
- **Datoteka:** `hub/sifrarnici/winstore.py` redak 58: `DELETE FROM winstore_ploca WHERE izvoz = ?` briše samo redove **istog imena datoteke**; `stanje_po_kodu` (137), `nalazi.py` (36–39, 63, 75), `ispravci.neslaganje_debljine` (174) i izvod debljine iz Winstorea (107–109) zbrajaju **sve** izvoze.
- **Dokaz (proba na kopiji stvarne baze):** uvoz `11092026.XML` → `W908ST2-18` = 13 kom; isti XML kopiran kao `12092026.XML` i uvezen → `stanje_po_kodu` = **26 kom**, tablica ima 1 184 retka (2 × 592).
- **Zašto je bitno:** D-64 kaže „pune ploče → Winstore, dnevni XML“; s ovim kodom bi skladište nakon tjedan dana pokazivalo 7× stanje, a „nepovezani kodovi sa stanjem“ i „debljina iz Winstorea“ (COUNT DISTINCT preko svih dana) bi lutali.
- **Popravak:** pri uvozu zamijeniti **cijeli** prethodni inventar (`DELETE FROM winstore_ploca` ili filter „zadnji izvoz“ = `postavke.winstore_izvoz` u svim upitima); test u `test_sifrarnik.py` redak 319 provjerava samo ponovni uvoz *istog* imena.

### 12. D-53 nije proveden za postojeću bazu: 4 „TRAKA ZA R.P.“ ostaju materijali od 38 mm (SREDNJE)
- **Datoteka:** `hub/sifrarnici/pantheon.py` redci 46–49 (`je_materijal` ih više ne uvozi) — ali ne briše i ne deaktivira postojeće retke; `primijeni_zadane_debljine` (91–102) im je pritom dodijelio **38 mm** (pravilo RP radna).
- **Dokaz:** u Igorovom `hub.db` (kopija): `RP000020/23/25/27 TRAKA ZA R.P. …`, `vrsta=RP, aktivan=1, ne_koristi_se=0, debljina=38`. `prepoznaj._materijali` ih i dalje nudi (filtrira samo `ne_koristi_se`). U svježoj bazi ih nema — zato testovi prolaze.
- **Popravak:** u `uvezi_pantheon` na kraju označiti (`ne_koristi_se=1` ili `DELETE`) materijale čiji ident više ne zadovoljava `je_materijal` (ili ga u CSV-u više nema); isto za trake.

### 13. Prvi stvarni nalog neće biti `2026-00001` nego `2026-00035` (SREDNJE, D-47)
- **Dokaz:** Igorov `hub.db` (`30_NOVI_PROGRAM\hub.db`, 14. 9. 08:33, shema v3): `postavke.brojac_naloga_2026 = 34`, naloga u bazi **0** (probni obrisani). Migracija v3 → v7 prolazi uredno (provjereno na kopiji), ali brojač nitko ne resetira; `PROV-` numeracija vrijedi tek za nove probne naloge.
- **Popravak:** prije prvog stvarnog naloga `DELETE FROM postavke WHERE kljuc = 'brojac_naloga_2026'` (ili u migraciju v8 dodati brisanje brojača kad nema nijednog naloga bez `PROV-`).

### 14. Izvoz na nesting ne gleda status naloga ni nepotvrđene rubove (SREDNJE)
- **Datoteke:** `hub/nalozi/export_nesting.py` 86–146 (preskače samo nepotvrđen materijal, `put='pila'`, debljinu); `hub/nalozi/nalozi.py` redak 512: za nesiguran rub u CSV ide **sirovi tekst iz naloga** kao naziv trake, redak 513: `tip_ruba` mu daje `A`.
- **Dokaz:** kod; element s `provjeri=1` izvozi se bez upozorenja u `preskoceno`. U redovnom toku D-46 (3) ne pušta nalog u `ponuda` s otvorenim potvrdama, ali točka 6 (izmjena elementa u bilo kojem statusu) taj štit zaobilazi.
- **Popravak:** izvoz odbiti (ili barem prijaviti u `preskoceno` po elementu) dok `broj_za_potvrdu > 0`; dopustiti samo statuse `skladiste` / `pila_nesting` (D-35). Isto vrijedi za `export_pila` (nepotvrđen materijal ide na pilu s kupčevim tekstom kao imenom).

### 15. `provjera_exporta` ne izvozi ništa — uspoređuje bazu s originalom, ne napisane datoteke (NISKO, ali zavarava)
- **Datoteka:** `hub/alati/provjera_exporta.py` redci 121–140: `mapa_izvoza` (tmp) se nigdje ne koristi, `EN` / `EPW` su uvezeni i nekorišteni; uspoređuje se `N.elementi_za_export` (in-memory zapis).
- **Posljedica:** dokument 16 §4 „iz Huba izveze natrag i usporedi“ nije točan opis; greške u `write_cpw` / `write_ppnest_csv` (točka 5) ova provjera ne može vidjeti. Rezultat CSV 8/8, CPW 5/8 sam reproducirao — vrijedi za zapis u bazi.
- **Popravak:** stvarno pozvati `export_pw.izvezi` / `export_nesting.izvezi` u tmp i čitati napisane datoteke `citaj_cpw` / `citaj_csv`.

### 16. Probne datoteke testa pišu se u mapu stvarnih naloga (NISKO)
- **Datoteka:** `tests/test_formati.py` redci 24–28: `_hub_test.csv` se piše u `05_NALOZI_ZA_TEST\…\04_export_nesting\<NALOG>\` i briše u `finally`.
- **Posljedica:** na mom VM-u brisanje nije dopušteno pa je ostala **`_BLAGO_JASA\04_export_nesting\BLAGO_3166_JASA\_hub_test.csv`** — moj trag, treba je obrisati (mogu uz odobrenje). Sadržajno test prolazi (25/25 CSV isto — provjereno ručno u `$HOME`).
- **Popravak:** pisati u `tmp_path`.

---

## C. Sumnje (nisam dokazao, ali treba pogledati)

### 17. Prijedlozi spajanja (D-54) računaju „ploče“ iz neto m², ne PW-metodom
- `hub/nalozi/spajanje.py` 39–40: `ploca = m2 dijelova / m2 ploče`; bez otpada i kerfa broj ploča je podcijenjen, pa `zasebno` / `spojeno` / `usteda` (69–71) mogu biti krivi za ±1 ploču. Ne isključuje materijale > 26 mm (nesting ih ne reže) ni one s `put='pila'` koje je voditelj već odlučio. Prijedlog je samo popis, pa je rizik nizak — ali brojke idu voditelju.

### 18. D-60: sukob imena CIX-a nema izlaz
- `export_nesting.dodijeli_imena` (63–69) staje s „preimenovati prije izvoza“, ali nigdje ne postoji način da se `cix_ime` elementa promijeni ili obriše (ni CLI ni API; `uredi_element` ne dopušta `cix_ime`). Elementi uvezeni iz PPNEST CSV-a nose PPNEST-ova imena po vremenu, koja se ponavljaju (D-60 to i navodi) → drugi takav nalog neće se moći izvesti.

### 19. `sljedeci_broj` čita-pa-piše bez transakcije
- `hub/nalozi/nalozi.py` 47–54. U API-ju je pod bravom pa je sigurno; iz dva CLI procesa istodobno (npr. uvoz + API) `nalog.broj UNIQUE` uhvatit će sudar kao grešku, ali brojač bi ostao preskočen. Nisko.

### 20. `uredi_nalog(kupac_id=…)` ne osvježava rabat ni kratki naziv kupca
- `hub/nalozi/nalozi.py` 126–135: promjena kupca ostavlja `rabat_materijal/usluge` i `naziv` starog kupca. D-40 kaže rabat je „kopija s kupca u trenutku ponude“ — moguće namjerno, ali ekran će to morati riješiti.

### 21. Ispravak vrste `debljina` ne pobjeđuje `rucno_umjesto_naziva`, ali pobjeđuje `winstore` i `vrsta` — je li to točan D-52 red?
- `hub/sifrarnici/ispravci.py` 89–94 i `winstore.py` 107–109. Redoslijed naziv → ručno → vrsta → Winstore je proveden; jedino mi nije jasno je li `debljina_umjesto_naziva` smjela dobiti i `debljina_rucno` (87–88) — kad se ukloni, `makni` vraća na naziv, što je u redu. Vjerojatno ispravno, samo nije testirano za taj put.

---

## D. Dokumentacija koja više ne stoji

22. `docs/STANJE.md`: „Kod je na disku, **u Gitu još nije**“ — commit `ad52930` je od 15. 9. 10:53; „63 testa“ — sada 72 + 5; napomena „`device_bash` na Igorovom PC-u ne radi“ — radi (ovaj pregled je njime rađen).
23. `hub/schema.sql` redak 1: „verzija 4“ — `SHEMA_VERZIJA = 7`.
24. `docs/16` §1 i STANJE: „oba i preko API-ja“ — ne (točka 1); §4 „izveze natrag“ — ne (točka 15).
25. `docs/14` §5 „CPO 47/50 nepromijenjeno“ — s Corpusom je 53 CPO-a, jedan pada (točka 9).

---

## E. Što nisam mogao provjeriti

- **Windows / Python 3.14**: sve je pokretano na Linuxu s Pythonom 3.10. Kod ne koristi ništa specifično za 3.14, ali putanje s razmakom (`PANEL WIZARD`), `cp1250` konzola i `sys.stdout.reconfigure` nisu provjereni na Igorovom PC-u.
- **Strojevi**: da bNest zaista prihvaća Hubov CSV + CIX (`H0000001`) i da Selco čita `HUB_00001.cpo` — samo format je provjeren (bajt-po-bajt protiv PW-ovih datoteka), ne stroj.
- **Živi API** (uvicorn) — korišten samo `TestClient`; ponašanje pod stvarnim istodobnim zahtjevima (async `nalog_uvoz` drži bravu u event-loopu) nije mjereno.
- **Mockup HTML** (`docs/mockup/skica_elementa.html`, `trake_naloga.html`, `v04/*`) — nisam funkcionalno pregledavao; nije dio kralježnice.
- **Semantika šifrarnika** (`nazivi.py` D-52/D-58, 370 aliasa iz skilla) — oslonio sam se na postojeće testove (prolaze) i na to da se brojke iz dokumenta 13 reproduciraju na kopiji stvarne baze (236 identa bez debljine, svi „ne koristi se“; 2 nepovezana koda sa stanjem).
- **Migracija v1 → v2 (`REBUILD nalog_materijal`)** — nemam bazu v1; v3 → v7 na Igorovoj bazi prolazi (`integrity_check ok`, `foreign_key_check` prazan).

## F. Što je dobro (da se ne pretpostavlja da je sve krivo)

Uvoz šifrarnika je idempotentan (dva uzastopna uvoza daju iste brojeve, Hub-polja kupaca i ispravci ureda preživljavaju), migracije rade na stvarnoj bazi,
`export_nesting` stvarno vraća ista imena pri ponovnom izvozu, `--suho` ne dira bazu, PPNEST CSV round-trip 25/25, CPO round-trip 50/50 na PW datotekama,
CSV 8/8 i CPW 5/8 s razlikama samo u M/A reproducirano, `najnovije_datoteke` rješava BRATEK (108 kom). Sintetički testovi su dobro napisani i pokrivaju tok statusa, D-46, D-48, D-57, D-58.

## G. Što je popravljeno — 15. 9. 2026. popodne (D-65)

Igorove odluke: (1) `MDF BIJELI 4 MM` bez šifre → alias na IV000054; (2) izvoz na stroj samo iz potvrđeno / skladište / pila-nesting, `--forsiraj` za probe, `--suho` uvijek; (3) migracija smije resetirati brojač kad nema stvarnih naloga.

| Točka | Stanje | Gdje |
|---|---|---|
| 1 API izvoz PW / pila | popravljeno | `nalozi_api.py` uvoz `EW`/`EP`; sve izvozne rute kroz `_greska` |
| 2 `provjera_exporta --obrisi` | popravljeno | `nalozi.obrisi_nalog` (novo), `provjera.obrisi_provjere` ga zove |
| 3 brisanje nakon izvoza | popravljeno | `nalozi._odvezi_elemente`, `_obrisi_materijal_bez_provjere`: `cix_registar.element_id → NULL`, briše `optimizacija`, `rezervacija`, … |
| 4 potvrda trake `zapamti=false` | popravljeno | `potvrdi_traku_naloga`: upisuje traku po `norm()`, preračuna `provjeri`, bez ponovnog prepoznavanja |
| 5 naziv elementa u CPW/CSV | popravljeno | `read_cpw` → `naziv`; `write_cpw` piše `naziv`; `write_ppnest_csv` piše cjelinu / poziciju / PROGRAM1/2 / GLODANJE; `element.prolaza` (shema v8) |
| 6 izmjena elementa u bilo kojem statusu | popravljeno | `uredi_element` / `obrisi_element` samo u unos / ponuda; provjera mjera > 0 i pri izmjeni |
| 7 otvorena transakcija nakon greške | popravljeno | `_greska` radi rollback za svaku iznimku; izvozi omotani `uz_rollback` |
| 8 događaj izvoza bez korisnika | popravljeno | `_dogadjaj_izvoza` koristi `korisnik_id` |
| 9 test CPO Corpus | popravljeno | alias (D-65/6); fixture `stvarna_baza` primjenjuje ispravke ureda kao i `uvoz` |
| 10 `cpo_rw` ORD2 oznaka | popravljeno | 3. polje ORD2 čita se i piše (`oznaka`); round-trip 53/53 |
| 11 Winstore zbrajanje | popravljeno | `uvezi_winstore` briše cijeli inventar |
| 12 D-53 za postojeću bazu | popravljeno | `pantheon._izbaci_sto_vise_nije`: obriši ili označi; na Igorovoj bazi 4 izbačena |
| 13 brojač 34 | popravljeno | migracija v8 briše `brojac_naloga_*` dok nema naloga bez `PROV-` |
| 14 izvoz bez provjere statusa / potvrda | popravljeno | `export_nesting.provjeri_spremnost` (nesting i pila); CPW za PW ostaje slobodan |
| 15 `provjera_exporta` ne piše datoteke | popravljeno | `napisi_iz_huba` piše CPW/CSV u tmp i čita ih; rezultat isti (CSV 8/8, CPW 5/8) |
| 16 test piše u mapu naloga | popravljeno | `tmp_path` |
| 17 spajanje neto m² | djelomično | materijali > 26 mm isključeni; PW-metoda ostaje za korak 4 (komentar u kodu) |
| 18 sukob PPNEST imena CIX | popravljeno | PPNEST ime u sukobu → novo Hub ime; Corpusovo i dalje staje |
| 19–21 | bez promjene | nisko / čeka odluku |
| 22–25 dokumentacija | popravljeno | STANJE, DECISIONS (D-65), README, docs 14 i 16, zaglavlje sheme |

Uz to (nađeno tijekom popravaka): kupčev PPW HUMER ima element na punu dužinu ploče (**2800 × 320** u IV JELA TAVERNA) koji ne stane na ploču s obrezom 10 mm — `export_pila` se rušio s `ValueError`. **Igor (15. 9.): reže se bez obreza ruba 10 mm** → Hub takav materijal složi s obrezom 0 (CPO INV1 trim 0, `obrez` u `optimizacija`) uz upozorenje; JELA TAVERNA iz kupčevog PPW-a tako daje 6 ploča kao PW (D-65/10). Element veći od same ploče vraća `ExportGreska` s popisom.

Testovi: `tests/test_popravci_2026_09_15.py` (11 testova, jedan po točki) + dopunjeni `test_nalozi.py`, `test_sifrarnik.py`, `test_formati.py`. **Sa stvarnim podacima 87 prolazi, bez njih 82 + 5 preskočenih.** Provjereno i na kopiji Igorove baze: migracija v3 → v8, uvoz šifrarnika, drugi dan Winstorea (stanje ostaje 13, ne 26), brojač obrisan, `TRAKA ZA R.P.` nestali, `provjera_exporta --obrisi` čisti bazu, CLI izvozi (`--suho`, bez i s `--forsiraj`).
