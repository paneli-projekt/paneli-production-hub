# 32 — Igorove napomene na prve ekrane (17. 9. 2026.) i što je napravljeno

Hub je 17. 9. ujutro prvi put pokrenut na VM-u (`http://192.168.5.201:8766/`, `C:\Paneli\Hub`, kopiranje `deploy\1_KOPIRAJ_HUB_NA_VM.bat`
računom `PANELI-PC\Igor`, postavljanje `2_VM_HUB_POSTAVI.bat`). Igor je prošao ekran ponude i poslao sedam napomena — sve su ugrađene
isti dan. **148 testova** prolazi (`HUB_TEST_DATA`), shema **v14**.

| # | Igorova napomena | Što je napravljeno | Gdje |
|---|---|---|---|
| 1 | „Ekran se mora skrolati da bi došli do shema i potvrde. To treba biti odmah vidljivo i vrlo uočljivo.“ | **Slaganje ploča je na vrhu ekrana ponude** (i ekrana pile), preko cijele širine, po jedna kartica za svaki materijal: **sličica svih ploča** (PNG iz istog slaganja kao krojni nacrt), velike brojke (ploča, iskorištenje, m² za naplatu) i veliki gumb **„Potvrdi slaganje“**. Iznad kartica **crveni pojas** dok nešto čeka potvrdu, s gumbom **„Potvrdi sve Hub prijedloge (N)“**; zeleni pojas kad je sve potvrđeno. Nema više uske tablice s vodoravnim skrolanjem. Ostale varijante (alternativna slaganja) su ispod, u redcima. Na uskom prozoru kartice idu jedna ispod druge, ekran se cijeli skrola (slaganje je prvo). | `hub/web/ekrani.js` (`optBlok`, `optBanner`, `veziOpt`), `hub/ispis/sheme_png.py`, `GET /api/optimizacija/{oid}/sheme.png?h=` |
| 2 | „U ekranu ponude bih maknuo nazive Materijal, Rezanje, Trake, Kantiranje — da budu sakriveni, na gumb da se pojave.“ | Redci s nazivom grupe su **skriveni**; gumb **„Grupe“** u zaglavlju tablice ih uključi (pamti se u pregledniku). | `ekrani.js` (`E.nalog_obracun`, `hub_ponuda_grupe`) |
| 3 | „Nema opcije da se vlastoručno upiše dodatni artikl.“ | Gumb **„+ Dodaj artikl“** → pretraga Pantheon identa po identu ili nazivu, količina, JM, naziv (smije se prilagoditi), po želji **ručna cijena** i rabat, grupa (usluga / okov / materijal / ostalo), napomena. Stavka ide u obračun kao „ručno“ i ima gumb × za uklanjanje. **Ident mora biti iz šifrarnika** — ponuda ide u Pantheon eSlogom samo s pravim identom; novi artikl se prvo otvori u Pantheonu pa osvježi šifrarnik. Tablica `rucna_stavka` (shema v14), **D-87**. | `hub/nalozi/obracun.py` (`dodaj_rucnu`, `rucne`, `obrisi_rucnu`, ručne u `izracunaj`), `GET/POST /api/nalog/{id}/rucne`, `DELETE /api/rucne/{id}`, `GET /api/sifrarnik/identi?q=` |
| 4 | „Slanje maila u potpisu treba imati osobu koja je poslala, a ne Paneli projekt d.o.o. Useri trebaju imati šifru za logiranje.“ | **Prijava s lozinkom (D-88):** ekran prijave (oznaka + lozinka), lozinke kao PBKDF2 hash, sesija u kolačiću 30 dana. Prva lozinka u Hubu **uključi obaveznu prijavu** za sve; korisnik bez lozinke prijavi se praznom lozinkom i odmah je postavi. **Postavke → Korisnici i prijava:** admin dodaje korisnike, ulogu, e-mail, telefon, funkciju, vlastiti potpis, lozinku; svatko mijenja svoju. **Potpis u mailu** = ime / funkcija / tvrtka / telefon · e-mail prijavljene osobe (ili njezin vlastiti tekst), i u ponudi i u narudžbi; **Reply-To** = e-mail te osobe (From ostaje `prodaja@paneliprojekt.hr`). Klik na kružić korisnika: promjena lozinke / odjava. Zaboravljene sve lozinke: `py -m hub.korisnici --lozinka IGOR` ili `--iskljuci-prijavu` na VM-u. | `hub/korisnici.py`, `hub/api/korisnici_api.py` (middleware: 401 → ekran prijave), `hub/nalozi/mail.py` (Reply-To), `ponuda.py`, `nabava/narudzbenica.py`, `app.js` (`ekranPrijava`, `postaviLozinku`) |
| 5 | „Ponuda treba biti ljepše oblikovana, logo u zaglavlju, malo poradi na dizajnu.“ | Novi PDF ponude: **logo + naziv tvrtke** i kontakt lijevo, **PONUDA + broj** desno u zelenoj, zelena crta; blok **Kupac** (naziv, adresa, OIB, kontakt) i blok **Podaci o ponudi** (nalog, verzija, **Vaš kontakt** = tko šalje); tablica s tamnim zaglavljem i zebrom; zbroj s istaknutim **UKUPNO ZA PLATITI**; uvjeti; potpis pošiljatelja; podnožje na svakoj stranici (tvrtka, OIB, IBAN, broj stranice). Podaci tvrtke iz postavki `tvrtka_naziv / adresa / mail / web / tel / oib / iban` (OIB i IBAN Igor upiše u Postavke ili `postavke` tablicu). | `hub/nalozi/ponuda_pdf.py` (`pdf`, `_fontovi`, `LOGO`), `GET /api/ponuda/{vid}/pdf?svjeze=1` |
| 6 | „Logika označavanja gumba u zaglavlju je nejasna — stisnuo sam Skladište, zeleno je Unos, a bijelo Ponuda?“ | Pilule u zaglavlju sada znače jedno: **bijela = ekran koji je otvoren**; **kvačica ✓ = korak koji je nalog prošao**; **zelena točka = korak u kojem je nalog sada** (status). Tooltip objašnjava. | `app.js` (`koraci`), `app.css` (`.pill`) |
| 7 | „Da se prikaz optimizacije ne skida automatski kao PDF svaki put; pregled na centralnom ekranu, PDF po želji.“ | Klik na sličicu ili **„Pregled shema“** otvara **pregled na ekranu**: svaka ploča velika s brojevima i mjerama komada, iskorištenje, korisni ostatak, popis elemenata i trake; gumbi „Krojni nacrt PDF“ i „Potvrdi ovo slaganje“. **Svi PDF-ovi se otvaraju u pregledniku (inline)** umjesto da se skidaju — krojni nacrt, ponuda, narudžbenica, naljepnice. | `GET /api/optimizacija/{oid}/pregled`, `sheme.png?list=n&h=620`, `pdf_inline()` u `nalozi_api.py`, `ekrani.js` (`pregledSlaganja`) |

Usput popravljeno: Postavke → polja optimizacije bila su prazna (API vraća popis, ekran je čitao rječnik); dijalozi se zatvaraju tipkom Esc i pri promjeni ekrana; `SyntaxWarning` u `spajanje.py`.

## Dopuna (17. 9., popodne) — ekran unosa i boje restlova

Igor je od tri ponuđene varijante unosa (A jedan red, B skica uz mjere, C tipkovnica; slike `docs/ekrani_proba/varijante_*`) izabrao **B s korekcijama**:
tri zone jasno odvojene crtom i razmakom — **Mjere** (L × W, kom fiksne širine, naziv, napomena, Prihvati) | **Kantiranje** (mala daska s
**velikim kućicama** rubova 58 × 46 px na pravim stranama; klik = aktivna traka, dvoklik na dasku = sva 4 ruba; „svi rubovi“ / „bez trake“) |
**Traka** (popis traka materijala, klik = aktivna, „+ ABS“ / „+ MEL“) — sve u srednjem panelu, uz kućice za unos, miš više ne ide na drugi kraj
ekrana. Velika SVG skica i panel „Trake“ u desnom stupcu su maknuti (desno ostaju „Za potvrdu“ i „Nalog“). `app.js` (`skicaMini`), `app.css` (`.unos3`, `.zona`, `.skm`).

**Slaganje ploča kao podizbor unosa** (Igorov crtež): srednji donji panel ima kartice **„Elementi“** i **„Slaganje ploča“** (s oznakom potvrđeno / čeka
potvrdu za odabrani materijal); kartica Slaganje pokazuje isti blok kao ekran ponude (sličice, brojke, „Potvrdi slaganje“, „Pregled shema“, PDF) i gumb
**„Optimiziraj“** (novi Hub prijedlog auto / najbolje). `app.js` (`S.unosTab`), `ekrani.js` izvozi `optBlok / optBanner / veziOpt / legendaSheme`.

**Boje na shemama (Igor):** zeleno = iskorišteno za naručene mjere, **plavo = naš restl** (korisni ostatak ≥ 400 × 400 i ≥ 1 m², ne naplaćuje se —
crta se uz širinu za uzdužno, uz duljinu za poprečno slaganje), **rozo = kupčev restl** (sve ostalo na ploči, naplaćuje se kupcu). Legenda ispod
kartica i u pregledu. `hub/ispis/sheme_png.py` (`BOJA_NAS`, `BOJA_KUPAC`).

## Dopuna 2 (17. 9., popodne)

- **Daska u kantiranju:** bez teksta u sredini; mjere zalijepljene uz rub kojem pripadaju (L uz dužu stranu, okomito; W uz kraću, dolje); daska 20 % veća, kućice rubova 30 % manje (44 × 34 px).
- **Pregled slaganja:** sve ploče iste veličine (visina 400 px, ili 340 kad ih je > 4; širina iz omjera ploče), više ploča u redu, kraći natpisi — što manje skrolanja; „naš restl“ u natpisu plavo.
- **Uvoz PanelWizard `.pnl`** (Igor: „uvoz ne da .pnl iz PW-a“): dokument 02 §3.5 je rekao „ne parsirati“, ali ured često ima samo PW-ov nalog. Format je rastavljen na stvarnim datotekama (`_BLAGO_ADRIJANA\02_panelwizard`, 8 datoteka): zaglavlje 4 B, zatim zapisi od 630 B (int32 L, W, ?, kom; naziv[30]; int16 zastavice MEL ×4 i ABS ×4; 4 naziva trake[30]; program (CPO)[60]) do prvog praznog zapisa; materijal je polje od 25 znakova u repu datoteke (pouzdanije od imena datoteke — PW ga krati: `RP SLATE VULCANO K2877`, `IV_HR_EVOKE_SUNSET_19`), debljina iz naziva („18 MM“ ili „… 18“). Čita se SAMO to; sheme i postavke i dalje iz CPO-a / PDF-a. `nalog_io.read_pnl`, `uvoz_datoteka.uvezi_pnl`, `POST /api/nalog/{id}/uvoz` prima `.pnl`, dijalog „Uvoz datoteke“ nudi `.pnl`. Test na stvarnoj datoteci (35 el / 93 kom, trake i MEL/ABS zastavice). **Za potvrdu s Igorom:** redoslijed četiri polja trake = L, O, D, G (kao CPW) — provjeriti na jednom PW nalogu s različitim trakama po stranama.
- Testovi: **151 prolazi sa stvarnim podacima** (`HUB_TEST_DATA` = putanja do `05_NALOZI_ZA_TEST`).

## Dopuna 3 (17. 9., popodne) — slaganje i ponuda su dva ekrana (D-89)

Igor: „Pregled i korekcija ponude treba biti razdvojeno od prikaza shema i potvrde slaganja (koji su korak prije ponude). Novi ekran ponude
dodaje redak kao u Pantheonu, povlači artikle i cijene iz Pantheona, pretraga po identu i nazivu.“

- **Koraci naloga su sada pet:** 1 Unos → **2 Slaganje** → **3 Ponuda** → 4 Skladište → 5 Pila / nesting (pilule u zaglavlju, `KORAK` u `app.js`).
- **Ekran Slaganje** (`#/nalog/{id}/slaganje`): pojas (čeka / potvrđeno), kartica po materijalu sa sličicama, „Potvrdi slaganje“, „Pregled shema“, PDF,
  alternative; legenda boja; u podnožju koliko je materijala potvrđeno, ploča i m² za naplatu; „Ponuda →“. Isti blok ostaje i kao kartica u unosu.
- **Ekran Ponuda** (`#/nalog/{id}/ponuda`, stara ruta `/obracun` radi): samo stavke i verzije. Ako slaganje nije potvrđeno — crveni pojas s gumbom
  „Otvori slaganje“ (brojke su Hubov prijedlog, verzija ponude ne prolazi). **Novi redak na dnu tablice kao u Pantheonu:** upišeš ident ili dio naziva
  (bez dijakritike: „bjela“ nađe BIJELA) → padajući popis iz šifrarnika (ident, naziv, JM, cijena) → strelice / Enter ili klik → količina → Enter doda.
  Cijena prazna = iz Pantheona, rabat prazan = s naloga po grupi (grupa iz klasifikacije identa: OK okov, US usluga, IV/TR/RP/ZO materijal).
  **Ručni redci se uređuju izravno u tablici** (količina, cijena, rabat; prazno = natrag na Pantheon / nalog), × ih briše. Izračunate stavke
  (iz elemenata) ostaju samo za čitanje — mijenjaju se kroz unos i slaganje. `PUT /api/rucne/{id}`, `GET /api/sifrarnik/identi` (pretraga po riječima, bez dijakritike).
- Dijalog „+ Dodaj artikl“ je maknut (zamijenio ga je redak u tablici).

## Dopuna 4 (17. 9., navečer) — ponuda kao Pantheon, čišćenje zaglavlja (D-90)

1. **Nadmjera trake se ne spominje** ni u programu ni na dokumentu — to je postavka definirana jednom (D-77). Stavke traka i kantiranja nemaju
   napomenu („PW metri … nadmjera 10 % unutra …“ je maknuto), uvjeti na ponudi kažu samo „trake i kantiranje po dužnom metru“.
   **Kantiranje = isti metri kao traka** (s nadmjerom, naviše na cijeli metar) — dosad je bilo „točni metri“, pa su se traka i kantiranje razlikovali.
2. **Ekran Ponuda:** naslov **PONUDA 2026-00001** (velik, uočljiv) s verzijom, kupcem i nalogom; **zbroj** (ukupno bez rabata, rabat, ukupno neto,
   PDV 25 %, ZA PLATITI) stoji u stupcu Iznos i **lijepi se za dno** dok tablica skrola; **Napomena** (gumb) — tekst za cijeli dokument, ispisuje se
   ispod uvjeta i vidi se u zaglavlju ekrana; **Rabat na sve…** (jedan postotak za sve, ili odvojeno materijal / usluge — upisuje se na nalog);
   **svaka stavka se mijenja proizvoljno** u tablici (količina, cijena, rabat) — izračunate stavke dobiju korekciju za TU ponudu (žuti redak, ↺ vraća
   izračunato; tablica `korekcija_stavke`, shema v15), ručne mijenjaju sebe. Verzije ponude su kartice bez vodoravnog skrolanja.
   PDF: kad ima rabata, zbroj pokazuje i „Ukupno bez rabata“ i „Rabat“.
3. **Zaglavlje samo s koracima:** četvrtasti gumbi (status, Događaji, Slaganje →, Upiši radne stavke, Nova verzija…, Stanje / Restlovi…) su preseljeni
   s vrha u **alatnu traku na ekranu** (gornji desni dio radnog prostora), na svim ekranima odjednom (`ljuska()`); u zaglavlju ostaju logo, naziv naloga
   i zaobljene pilule koraka.

## Dopuna 5 (17. 9., navečer) — Igorov drugi krug na ponudi, skladištu i pili

- **Zbroj poravnat sa stupcem Iznos** — na ekranu su redci zbroja pravi redci tablice (lijepe se za dno jedan iznad drugog), na PDF-u stupci tablice
  sada zbrajaju točno širinu okvira pa zbroj stoji pod „Iznos €“ s istim odmakom.
- **„Grupe“ maknuto; „Zbroji iste idente“** (opcija naloga `zbroji_idente`, shema v16): isti ident + ista cijena + isti rabat → jedan redak sa zbrojenom
  količinom (npr. USLUGA REZANJA s više materijala). Korekcija takvog retka vrijedi za zbrojeni redak.
- **„Upiši radne stavke“ maknuto** — to je bio ostatak iz CLI faze (D-69): upisivao je trenutni obračun u `obracun_stavka` bez verzije. Na ekranu je
  obračun uvijek živ, a snimku radi „Nova verzija ponude“, pa gumb nije imao svrhu.
- **Verzije ponude** pokazuju iznos **s PDV-om** (neto u napomeni).
- **Tok nakon potvrde:** na ponudi potvrđenog naloga gumb **„→ Skladište (rezerviraj materijal)“** (status skladište, Hub sam rezervira); na skladištu
  **„Rezerviraj materijal“** za nalog u statusu potvrđeno = prijelaz u skladište (zato prije nije bilo zelene točke — rezerviralo je bez promjene
  statusa), zatim **„→ Pila / nesting“**.
- **Ekran Pila / nesting pojednostavljen:** po materijalu samo potvrđeno slaganje (sličica, ploče, m², „Pregled shema“, „Krojni nacrt“) + put, bez
  alternativa i banner-a — slaganje je odlučeno u koraku 2; drukčije slaganje ima smisla samo pri spajanju naloga (i tamo ostaje). **Mape izvoza
  (nesting, pila) su postavke** (`mapa_nesting`, `mapa_pila`, Postavke → Optimizacija i obračun), na ekranu samo piše kamo ide.

## Dopuna 6 (17. 9., kasno) — ponuda bez podnožja, sve verzije dostupne; PITANJE optimizacije (D-91 PREDLOŽENO)

- Ekran ponude više nema statistiku u podnožju (zbroj je u tablici).
- **Sve verzije ponude** (i stare / zamijenjene / poslane) imaju **PDF** (za poslanu — spremljeni PDF; za staru bez datoteke — PDF iz snimke stavki
  s datumom slanja) i gumb **„Stavke“** — tablica te verzije s neto i s PDV-om, za usporedbu; najnovija verzija gore.
- **Optimizacija — Igorov prigovor:** pila ne reže kao nesting; realno reže trake (uzdužno ili poprečno), iz njih poprečne rezove, pa uže komade.
  Hubov „najmanje m²“ (kolone / best-fit / mix iz D-71) daje sheme koje na pili znače puno prekrajanja. Igor želi: **zadano za naplatu i
  narudžbu = ono što pila realno reže**, Hubov minimum ostaje kao rezerva, a u svakom trenutku se može odlučiti rezati realno. Opcije su iznesene
  Igoru u razgovoru (A–D), odluka čeka — do tada se ništa u optimizatoru ne mijenja.

## Dopuna 7 (17. 9., kasno navečer) — zadano slaganje je realno za pilu (D-91 ODLUČENO, opcija B)

- Igor je prihvatio prijedlog **B**. Ekran slaganja sada pokazuje **„Realno za pilu / najbolje“** kao zadani prijedlog — najmanje m² među
  slaganjima koja pila stvarno može izrezati: trake (uzdužno ili poprečno) → poprečni rezovi → uže pod-trake, do dopuštene razine, s najviše
  dopuštenog broja različitih širina u traci i bez miješane orijentacije. Ispod, pod „Ostale varijante“, stoji **„Hub rezerva (najmanje m²)“**
  samo kad štedi materijal, s razlikom (npr. 10 pl · 55,16 m² (−3,90)) i ⚠ čiji opis kaže zašto pila tako ne reže (npr. „traka 900 ima 3 širine
  komada (najviše 2)“, „rez 4. razine“, „ploče se ne režu u istom smjeru“). Rezerva se smije potvrditi kad god Igor procijeni da ju pila može
  izrezati — ponuda, narudžba i stroj uvijek prate ono što je potvrđeno.
- **Ograničenja pile su postavke** (Postavke → Optimizacija i obračun, na dnu): najviše razina rezanja (2 | 3 | 4), najviše različitih širina u
  traci (0 = bez), najmanji komad 4. razine (mm, 0 = bez), miješana orijentacija dopuštena (0 | 1). Početno **3 / 2 / 0 / 0**. Nakon promjene
  postavki: na nalogu „Optimiziraj“ (unos) računa iznova.
- „Alternativa…“ nudi: Realno za pilu (zadano) · Hub rezerva · Uzdužno · Poprečno · Trake × brzo / najbolje; uzdužno / poprečno / trake također
  poštuju ograničenja. Ako nijedno slaganje ne prolazi ograničenja (npr. vrlo strogo postavljena), uzme se najbolje bez ograničenja i to piše
  pod prijedlogom.
- Probni nalog HUMER_OMIS_1 (5 materijala, 279 komada): IV BIJELI NK 18 zadano 11 ploča / 59,06 m², rezerva 10 ploča / 55,16 m² (−3,90);
  ostali materijali — zadano i rezerva jednaki (rezerva se ne prikazuje). Računanje 0,5–9 s po materijalu.
- Gumbi preimenovani da se ne miješa „Hub prijedlog“ s „Hub rezerva“: „Izračunaj slaganje“, „Potvrdi zadano slaganje“ / „Potvrdi sva zadana
  slaganja (n)“.

## Dopuna 8 (17. 9., popodne) — Igorov prolaz na VM-u: uvoz više datoteka, promjene između verzija, Proizvodnja

Igor je prošao nalog na VM-u („sve je ok“) i javio četiri stvari. Sve je napravljeno i provjereno u Chromiumu na HUMER-ovih 5 kupčevih CPW-ova.

- **Uvoz više datoteka kupca odjednom.** „Uvoz datoteke“ na ekranu unosa sada prima više datoteka: odabir s Ctrl / Shift ili povlačenje u
  okvir. Popis prije uvoza (s × za micanje), zatim Hub uvozi jednu po jednu u isti nalog i uz svaku piše rezultat (`53 el / 174 kom · za potvrdu 2`).
  Ista datoteka drugi put → „već uvezena — preskočeno“ (hash, kao dosad); datoteka koja nije .CPW / .PNL / .CSV odmah je označena i ne šalje se;
  greška jedne ne zaustavlja ostale — dijalog tada ostane otvoren s popisom, uvezene su u nalogu. Izbor „izvor“ vrijedi za .CPW (kupčev PPW /
  PanelWizard); .PNL i .CSV prepoznaju se po nastavku. Proba: 5 datoteka → 121 el / 278 kom u jednom koraku. Slika `docs/ekrani_proba/17b_uvoz_vise_datoteka.png`.
- **Sažetak promjena ispod novije verzije ponude.** Uz svaku verziju koja ima prethodnu: „prema v2 **+184,80 €** s PDV-om (neto +147,84)“,
  do 4 najveće promjene (zeleno `+` dodano, crveno `−` uklonjeno, inače `24 → 36 KOM`, `cijena 2,04 → 1,80`, `rabat 0 → 30 %`) s razlikom iznosa,
  brojevi „1 dodano · 2 promijenjeno“ i, kad ih je više, „sve promjene (n)“ → tablica svih. Ista stavka u dvije verzije = isti ident na istom
  materijalu naloga (usluge i ručne stavke bez materijala i po nazivu). Nepromijenjena verzija: „bez promjena u odnosu na v2“. Računa server
  (`ponuda.promjene()`, polje `promjene` u `GET /api/nalog/{id}/ponude`). Slika `docs/ekrani_proba/17b_verzije_promjene.png`.
- **Gumbi verzije u jednom redu:** PDF · Stavke · **Pošalji kupcu** (svijetlo žuto) · **Kupac potvrdio** (svijetlo plavo); eSlog na potvrđenoj
  verziji u istom redu. Stupac verzija na širokom ekranu (≥ 1500 px) 420 px.
- **Korak 5 „Pila / nesting“ → „Proizvodnja“.** Pilula, naslov i gumb na skladištu („→ Proizvodnja“); adresa `#/nalog/N/proizvodnja` (stara
  `/pila` i dalje radi). Kartice materijala su u **punoj visini** (sheme i gumbi uvijek cijeli, bez skrolanja unutar kartice) i složene kao na
  ekranu slaganja (sličica lijevo, podaci desno); skrola cijeli ekran, a „Izvoz na stroj“ i „Spajanje“ ostaju vidljivi desno. Status naloga
  `pila_nesting` na popisu naloga i dalje se zove „Pila / nesting“ (nalog je na stroju). Slika `docs/ekrani_proba/17b_proizvodnja.png`.
- Testovi: novi `tests/test_ekrani_2026_09_17b.py` (promjene između verzija: dodano / uklonjeno / količina / rabat / bez promjena, zbroj razlika =
  razlika neto; uvoz tri CPW-a redom u isti nalog, ponovljena datoteka preskočena, krivi tip 400). **159 testova prolazi** sa stvarnim podacima.

## Kako to izgleda Igoru nakon kopiranja

1. Na PC-u `deploy\1_KOPIRAJ_HUB_NA_VM.bat` (lozinka VM korisnika Igor), na VM-u zatvoriti prozor Huba (Ctrl+C) i ponovno `C:\Paneli\Hub\deploy\2_VM_HUB_POSTAVI.bat` — `hub.db` se sam podigne na zadnju shemu (nove postavke pile dodaju se same).
2. `http://192.168.5.201:8766/` radi kao dosad (bez prijave) dok se u **Postavke → Korisnici i prijava** ne postavi prva lozinka — od tada svi ulaze s lozinkom; korisnici bez lozinke prijave se praznom i postave svoju.
3. Za potpis u mailu: svakom korisniku upisati ime i prezime, funkciju, e-mail, telefon (Uredi). Za podnožje ponude: postavke `tvrtka_oib`, `tvrtka_iban`, `tvrtka_tel`.

## Otvoreno / za Igora

- Rabat u ručnoj stavci: prazno = rabat naloga po grupi (usluga → rabat usluga, okov/materijal → rabat materijala) — je li to očekivano?
- PDF ponude: treba li i **HTML tijelo maila** dobiti isti izgled (sada je jednostavna tablica; logo u mailu često blokiraju klijenti)?
- Prava po ulogama (D-86): zasad samo admin uređuje korisnike; sve ostalo vide i rade svi (D-34).
