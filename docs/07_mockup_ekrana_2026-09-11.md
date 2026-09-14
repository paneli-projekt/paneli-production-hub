# Paneli Production Hub — faza 2, korak 1: mockup ekrana (v0.1 11. 9. → v0.4 12. 9. 2026.)

Po D-14 (ekrani se prvo crtaju, pa kodiraju) i D-28 (faza 2 počinje mockupom s voditeljem proizvodnje i Igorom).
Igor je 11. 9. izabrao: **statični ekrani na jednom platnu** (ne klikabilni prototip) i **cijeli tok naloga** u prvom krugu.

## 1. Gdje je mockup

| Što | Gdje |
|---|---|
| Platno s 4 ekrana + bilješke s pitanjima (otvara se u pregledniku, može se uređivati i izvesti u PNG/PDF) | artefakt „Production Hub — mockup ekrana“ u Claude aplikaciji (galerija artefakata); offline kopija `20_ANALIZA\mockup\production-hub-mockup-ekrana.html` |
| Slike ekrana za ispis (1440 px širine) | `20_ANALIZA\mockup\1_Nalozi_popis.png … 4_Obracun_ponuda.png` |
| Izvor (generator ekrana, stil, raspored) | `30_NOVI_PROGRAM\docs\mockup\` (`build.py`, `shared.py`, `canvas.json`, `*.dc.html`) |

Napomena za sastanak: brojke na ekranima su **stvarne** (nalog HUMER_2823_OMIS, ponuda 26-010-002823, audit 05/06): broj ploča, m², metri
traka, Winstore stanje 11. 9., cijene iz šifrarnika. **Datumi, statusi i vremena u popisu naloga su ilustracija.**

## 2. Četiri ekrana = tok jednog naloga

1. **Nalozi (popis)** — jedan redak = jedan nalog kroz cijeli lanac (kupac, datum, tko je unio, broj materijala, stavki/kom, m², put pila/nesting,
   ponuda, status); filtri po statusu i „čeka odluku pila/nesting“, „s upozorenjem“; kartice: čeka odluku, upozorenja (npr. 2929 — materijal bez stavke
   u ponudi), rezultati sa strojeva, skladište. Statusi: unos → provjera → optimirano → ponuda → proizvodnja → zatvoren.
2. **Unos naloga** (ekran po D-14) — zaglavlje (kupac iz Pantheon šifrarnika subjekata, naziv naloga kakav očekuju PW/bNest, Hub broj automatski,
   datum, izradio, kerf 16 uz napomenu da u CPO ide 5, ponuda, napomena); uvoz elemenata (CPW iz PPW-a, Excel, foto/sken rukopisa → AI čitanje s oznakom
   PROVJERI); materijali kao kartice s brojem stavki/kom i putem; za aktivni materijal: Pantheon ident/naziv s aliasima → u pozadini Winstore kod,
   dimenzija ploče, debljina, god, glodalo za CIX; Hub prijedlog puta + skladište (Winstore ploče, restlovi kandidati); zadane trake po materijalu
   (oznaka u nalogu → TR ident → adresa u regal-traci); red za unos elementa u ritmu PPNEST-a (L, W, kom, 4 kvačice rubova A/M, traka, napomena, CNC,
   Enter); tablica elemenata sa skicom rubova; sažetak (stavki, kom, m², metri traka, ploče PW-metodom) i provjere prije spremanja.
3. **Pila / nesting i export** — po materijalu: Hub prijedlog s razlogom (pravilo iz odgovora 8: pila = MDF 3 mm, radne/zidne/compact ploče, restlovi,
   < 1 ploče; ostalo nesting), izbor voditelja, ploče PW-metodom, skladište, export (bNest CSV+CIX s imenima H000…; pila CPO HUB_xxxxx u Z:\Krojne_liste;
   CPW za PW u paralelnom radu) i rezultat sa stroja (bNest .mno: 9 i 5 ploča). Panel „rezultati sa strojeva“ = watcher na mape; restlovi za upis.
4. **Obračun → ponuda** — stavke po materijalu: ploče m² (PW-metoda), usluga rezanja, traka (PW metri naviše na cijeli metar, D-20), kantiranje
   (točno PW metri), RP po dužnom metru (⚠ pravilo nije potvrđeno), okov i ručne usluge sažeto; prekidač „količine iz PW / Hub optimizator“;
   provjere (svaki materijal ima stavku, D-20, razlike prema PW-u); „naplaćeno vs potrošeno“ (HUMER: +2 ploče ≈ 11,6 m² ≈ 263 €); izlaz eSlog XML /
   PDF / Excel.

Izgled namjerno prati **Regal traku** (isti fontovi IBM Plex Sans + Barlow Condensed, iste boje, gumbi, kartice), da djelatnici imaju jedan poznati izgled
za sve interne alate.

## 3. Što je iz odluka ugrađeno u ekrane

D-02 (skladište Huba = istina za ploče/restlove/trake), D-06 (Pantheon samo eSlog), D-11 (paralelni rad, CPW za PW), D-14, D-15 (AI samo s provjerom),
D-18 (obračun PW-metodom uvijek), D-19 (način optimizacije: min m²), D-20 (trake), D-21 (kerf 16 / CPO 5), D-22 (HUB_xxxxx), D-23 (imena CIX H000…),
D-24 (Pantheon ident ↔ Winstore kod), D-25 (etikete ostaju u OSI-ju), odgovor 8 (pravilo pila/nesting), odgovor 12 (korisnici: Ivana, Goran, Sanela,
voditelj, Igor).

## 4. Pitanja za sastanak s voditeljem proizvodnje (ista su na platnu kao bilješke)

> **12. 9. 2026.:** Igor je na ova pitanja (i na pitanja iz 08) odgovorio kroz checklistu — odgovori i status su u **09_checklista_odgovori_2026-09-12.md**,
> odluke u DECISIONS D-33 … D-38. Do kraja dana odgovorena su sva pitanja (etiketa: 14 znakova napomene; „naplaćeno vs potrošeno“ tek nakon nestinga, vidi operater).

**Popis naloga**
1. Tko otvara nalog (Ivana/Goran) i tko ga prebacuje u „Proizvodnja“ — voditelj?
2. Treba li voditelju poseban pogled „čeka odluku pila/nesting“ ili je filter u popisu dovoljan?
3. Naziv naloga ostaje PREZIME_BROJ_… (kako PW i bNest očekuju) + Hub broj u pozadini — OK?

**Unos naloga**
4. Zadržati ritam iz PPNEST-a (mjere → kom → rubovi → napomena → Enter, 4 kvačice A/M) ili unos kao tablica (kao Excel)?
5. Zadana traka po materijalu + iznimka po elementu — dovoljno za sve slučajeve (npr. bijela ploča s trakom drugog dekora, kao HUMER „taverna“ na IV BIJELI 18)?
6. God se naslijedi od materijala — treba li ga moći isključiti po elementu (kao u PW-u)?
7. Kerf (16) vidljiv u zaglavlju ili sakriven u postavke?
8. Napomena elementa ide na etiketu i u CSV — koliko znakova stane na etiketu?
9. Uvoz rukopisa: ekran „original + prepoznato + potvrdi“ — tko potvrđuje?

**Pila / nesting i export**
10. Hub predlaže put, voditelj potvrđuje — treba li prije potvrde vidjeti sheme (PNG) ili je dovoljan broj ploča?
11. Kad Winstore pokaže 0 ploča: tko rezervira restl ili javlja nabavu (Sanela / voditelj)?
12. Operater nestinga: nastavlja iz mape `C:\PPNESTING\<kupac>\NESTING` ili otvara Hub?
13. Paralelni rad (D-11): CPW za PanelWizard generirati uvijek automatski ili samo na klik?
14. Rezultat s pile: OSI ne vraća datoteku — potvrđuje li operater u Hubu „izrezano“ ili to ostaje praćenju proizvodnje (D-03)?

**Obračun → ponuda**
15. Radne ploče (RP): jedinica u ponudi je M — pravilo za količinu nije potvrđeno (HUMER: elementi 4,99 m, ponuda 2,4 m). Koje je pravilo? → *Riješeno 12. 9.: D-37 (600 mm po metru / 900 mm pola-cijela); HUMER-ovi elementi su u ponudi kao `PLOČA STOLA CIJELA` 2 KOM — moja usporedba s 2,4 m bila je kriva stavka. Ekran 4 se ispravlja u v0.3.*
16. Ručne usluge (CNC, bušenje, LED urez, nut, ljepljenje…) ostaju ručni unos — tko ih upisuje i kada?
17. Okov: AI prijedlog identa + potvrda — u Hubu ili i dalje izravno u Pantheonu?
18. Zaključavanje ponude i slanje eSlog XML-a: tko smije (Ivana / Goran / Igor)?
19. Prikaz „naplaćeno vs potrošeno“ — vidljiv svima ili samo Igoru?

## 4a. v0.2 (12. 9. 2026.) — ekran „Unos naloga“ po Igorovoj napomeni

Napomena: v0.1 je bio „šuma podataka“ — korisnik koji unosi gubi pozornost na bitno; unos mjera treba zadržati princip PW-a/PPNEST-a (grafika daske s
oznakama kantiranja), može kompaktnije, ali ljudi su na to naučeni.

Što je promijenjeno:
- **Na radnom ekranu ostaje samo ono što treba pri unosu**: zaglavlje u jednom retku (kupac, nalog, datum, izradio, napomena), traka materijala, redak
  aktivnog materijala (ident, naziv, debljina, god, Winstore kod i stanje), **unos elementa s daskom**, tablica elemenata, sažetak s gumbima.
- **Unos elementa kao u PPNEST-u**: lijevo 1. mjera (god) / 2. mjera / kom / napomena + Prihvati (Enter), Ažuriraj, Obriši; iznad daske padajući
  izbornici MELAMIN (MEL-ISTI) i ABS (1/22 JELA TAVERNA) = zadane trake materijala; okomita daska s mjerama, uz svaki rub par prekidača **M / A** i
  naziv trake; kantirani rub crta se zeleno (ABS) ili smeđe (melamin). Tablica ima istu mini-dasku po retku.
- **Sve ostalo je na klik** (ekran 2b): Zaglavlje (Hub broj, ponuda, kerf, napomena), Uvoz (CPW / Excel / rukopis / Corpus paket), Detalji materijala
  (Winstore kod, ploča, glodalo, aliasi, skladište, prijedlog puta), Trake (oznaka u nalogu → TR ident → regal), Provjere.
- Primjer je promijenjen na materijal **IV BIJELI NK 18** (53 stavke, 174 kom) jer ima stvarnu mješavinu rubova (1 / 3 / 4 strane, ABS i melamin).
- **Oznake traka (Igor, 12. 9., D-31)**: prekidači M / A zadržavaju naučena slova; značenje: `MEL-ISTI` = ABS iste boje 0,5 mm, `ABS-ISTI` = ABS iste
  boje 1 mm (zadano, 95 %), `ABS-ISTI 2mm` = 2 mm (rijetko, bira se u izborniku ABS iznad daske), druga boja = naziv trake iz Pantheona. Panel „Trake“
  mapira oznake po materijalu na TR ident; naljepnica i ponuda nastaju iz istog izbora. Panel „ABS ▾“ na ekranu 2b pokazuje tko/kada/kako bira.
- **Varijanta B (12. 9., brand iz `20_ANALIZA\new_mockup`)**: isti ekran s logom (tri ploče: antracit / drvo / narančasta) i tamnim zaglavljem; po Igorovoj
  napomeni narančasta ostaje samo kao tanki naglasak (crta ispod aktivnog taba, donja crta u logu), akcija i aktivno stanje su antracit s bijelim tekstom,
  radne površine svijetle, font Inter. Ploče iz new_mockup su AI-generirane — za upotrebu treba vektorski logo (SVG) i jedan oblik wordmarka (bez donje crte
  u „Production_Hub“). Ako se izabere B, isti tokeni idu i na Regal traku. Artboard 2B na platnu, slika `mockup\2B_Unos_naloga_varijanta_B_brand.png`.
- Varijanta B, dorada 12. 9.: logo u jednom retku (3D znak + „Paneli_ Production Hub“), antracit posvijetljen 15 % (#5A5F64) za zaglavlje i gumbe.
- **Varijanta C (12. 9.) — neovisan UX prijedlog** (bez oslanjanja na brand ploče, logo i PPNEST raspored): cijeli unos na jednom ekranu 1440×980 bez
  skrolanja — lijeva traka s ikonama, lijevo materijali, u sredini tablica elemenata s redom za unos na vrhu (Tab/Enter, rubovi L/D/G/B jednim slovom
  — → A → M, mjere ostaju za serije), desno inspektor s daskom koja prati odabrani redak; papirnata pozadina, jedan naglasak (mahovina zelena), rubovi
  ABS plavo / MEL žuto-smeđe, brojevi u monospace. Kompromis: unos ide kroz tablicu, a daska je prikaz i kontrola — brže za velike količine, ali traži
  navikavanje. Artboard C na platnu, slika `mockup\2C_Unos_naloga_varijanta_C_neovisni_UX.png`, izvor `docs\mockup\build_c.py`.
- **Varijanta D (12. 9.) — hibrid**: raspored iz C (jedan ekran bez skrolanja, lijeva traka, materijali lijevo, desni stupac stalno vidljiv: trake,
  materijal/skladište, sažetak, provjere) + unos kroz dasku iz B/PPNEST-a (mjere, kom, napomena, MEL-ISTI/ABS izbornici, M/A prekidači po rubu,
  Enter) + brand iz B (logo u jednom retku, antracit #5A5F64, narančasta samo u logu). Slika `mockup\2D_Unos_naloga_varijanta_D_hibrid.png`,
  izvor `docs\mockup\build_d.py`.
- **Igorov izbor (12. 9.)**: najskloniji je hibridu D; ostale varijante i ekrani se ne diraju dok ne uskladi s ostalim korisnicima.
- **Okov i obrade u D** (odgovor na pitanje „gdje je unos okova“): okov i obrade su grupe naloga na istoj razini kao materijali — u lijevom stupcu
  ispod materijala („Ostalo u nalogu“: Okov · Obrade i usluge). Klik na Okov mijenja sredinu u popis okova: uvoz Excela / fotografije kupca ili popisa
  iz Corpusa, alias-tablica → ident bez pitanja, inače AI prijedlog s oznakom „potvrdi“ (D-15), redak za brzi ručni unos (traži + kom + Enter).
  Obrade i usluge (bušenje, nut, CNC, LED urez…) ista logika: ručno danas, iz Corpusovog CIX-a kasnije (I-14). Sve tri grupe idu u jednu ponudu
  (eSlog XML) redoslijedom materijali → okov → usluge. Artboard „D · Okov“ na platnu, slika `mockup\2D_Okov_obrade.png`, izvor `build_d_okov.py`;
  podaci stvarni (OKOV (48).xlsx → identi iz ponude 26-010-002823).
- **Rječnik sučelja (Igor, 12. 9.)**: u aplikaciji nigdje ne piše „AI“ — ne izgleda profesionalno. Umjesto toga neutralni pojmovi: rukopis →
  „prepoznavanje“, prijedlog identa → status „za potvrdu“ / „potvrđeno“, panel „Kako se prepoznaje ident“ (alias-tablica → prepoznavanje po nazivu →
  potvrđeni par ulazi u aliase). Isto vrijedi za oznake odluka (D-xx, I-xx) — ostaju u dokumentima i bilješkama, ne na ekranima.
- Prijedlog tipkovnice (za raspravu, pitanje 6 na platnu): `L` `D` `G` `B` uključuju rub (drugi pritisak = melamin), `Enter` prihvati, `F2` ispravi
  zadnji, `Esc` očisti.

## 4b. v0.3 (12. 9. 2026., navečer) — svi ekrani u stilu D, novi tok naloga

Igor je potvrdio hibrid D kao dizajn (D-39) uz dopunu: **boje središnjeg dijela ekrana u nijansama varijante C** (papir `#F6F4EF`, mahovina
zelena `#2E6B57` za odabir i glavnu akciju, ABS plavo `#2F5D8C` / MEL jantar `#B7791F`), **zaglavlje nepromijenjeno** (antracit `#5A5F64`, logo u
jednom retku, narančasta samo u logu). Stare varijante (v0.1, v0.2, B, C, D-prototip) maknute su s platna; datoteke idu u `arhiva\`
(`20_ANALIZA\mockup\ARHIVIRAJ_STARE.cmd` premješta, ništa ne briše).

| Ekran | Datoteka (PNG u `20_ANALIZA\mockup\`) | Što je ugrađeno |
|---|---|---|
| 1 Nalozi (popis) | `v03_1_Nalozi_popis.png` | D-33 naziv `KUPAC_NAZIV_BROJ`; D-35 statusi Unos → Ponuda (čeka kupca) → Potvrđeno → Skladište → Pila/nesting → Proizvodnja → Zatvoren; D-34 voditelj radi iz istog popisa (filter); kartice desno: čeka kupca, potvrđeno → skladište, čeka voditelja, rezultati, skladište |
| 2 Unos naloga | `v03_2_Unos_naloga.png` | D-36 rubovi samo mišem (M/A uz dasku), bez prečaca; god iz Winstorea, gašenje uz potvrdu; kerf u Zaglavlju; D-31 izbornici MEL-ISTI / ABS; D-38 napomena s brojačem 14 znakova; D-32 Okov i Obrade kao grupe lijevo |
| 2b Okov i obrade | `v03_2b_Okov_obrade.png` | D-32: alias-tablica → ident, inače prepoznavanje po nazivu + „za potvrdu“; obrade i usluge ured pri obračunu (D-38); jedan eSlog |
| 3 Obračun → ponuda | `v03_3_Obracun_ponuda.png` | D-35 ponuda prije proizvodnje, stanje „čeka potvrdu kupca“, gumb „Kupac potvrdio → skladište“; D-18 količine PW-metodom; **D-37 RP = PLOČA STOLA CIJELA 2 KOM** (ispravak v0.1); D-38 usluge ured, zaključavaju Ivana i Goran; okov kao grupa |
| 4 Skladište nakon potvrde | `v03_4_Skladiste_nakon_potvrde.png` | **novi ekran** (D-35): Winstore / Hub skladište / restlovi / regal-traka po materijalu, UPOZORENJE, POPIS ZA NABAVU (Sanela), rezervacije po nalogu; ništa prije potvrde kupca |
| 5 Pila / nesting | `v03_5_Pila_nesting.png` | D-34 sheme uvijek vidljive (PW-metoda + rezultat s nestinga), voditelj potvrđuje put; nesting iz mape; CPW automatski; D-38 „naplaćeno vs potrošeno“ tek nakon .mno — ovdje, ne na obračunu; pregled svih materijala (put, ploče, export, rezultat) |

Koraci naloga u zaglavlju: 1 Unos · 2 Ponuda · 3 Skladište · 4 Pila / nesting (proizvodnja i „izrezano“ ostaju praćenju, D-03). Winstore brojke su
stvarne (W908ST2-18 13, K2665AI-19 0, W908ST2-16 0); stanje za pila-materijale, role traka, adrese regala i mini-sheme su ilustracija.
Izvor: `30_NOVI_PROGRAM\docs\mockup\v03\` (`build_v03.py`, `v03_base.py`, `canvas.json`, `*.dc.html`); platno = isti artefakt (verzija 16).

v0.3.1 (Igorove primjedbe na boje, isti dan): retci s nazivom grupe u tablicama (materijal, okov, usluge) dobili su svijetlo sivu pozadinu
`#E9ECEF` s tankim rubom da se ne stapaju s papirom; oznake puta više nisu pune tamne (crna / smeđa) nego meke nijanse kao ostale oznake —
nesting tirkiz `#1E6E76` na `#DAEBEC`, pila drvo `#7A5230` na `#F0E4D6`; adrese pretinaca traka su identične regal-traci (žuto `#F5C518`,
tamni tekst, tanki rub `#8A6D02`, Barlow Condensed).


## 4c. v0.4 (12. 9. 2026., kasno navečer) — ponuda iz Huba, potvrda kupca, događaji naloga, Nabava

Nastavak v0.3.1 prije prezentacije kolegama: ugrađeno je ono što je odlučeno nakon v0.3 (D-40 ponuda iz Huba, D-42 nabava i temelji za praćenje)
i što ne ovisi o povratnim informacijama Ivane, Gorana i voditelja. Platno = isti artefakt „Production Hub — mockup ekrana“ (verzija 17),
9 artboarda; slike `20_ANALIZA\mockup\v04_*.png`; offline kopija `20_ANALIZA\mockup\production-hub-mockup-ekrana.html`;
izvor `30_NOVI_PROGRAM\docs\mockup\v04\` (`build_v04.py` + `v04_base.py`, `canvas.json`, `shot.py` za PNG).

| Ekran | Datoteka (PNG) | Što je novo / promijenjeno |
|---|---|---|
| 1 Nalozi (popis) | `v04_1_Nalozi_popis.png` | kartica „Potvrđeno → skladište“ vodi manjak u Nabavu; lijeva traka ima „Nabava“ (na svim ekranima) |
| 2 Unos naloga · 2b Okov | `v04_2_Unos_naloga.png`, `v04_2b_Okov_obrade.png` | nepromijenjeno (osim trake) |
| **3 Obračun → ponuda iz Huba** | `v04_3_Obracun_ponuda.png` | **D-40**: glavna akcija „Pošalji kupcu“ (zaglavlje, podnožje, panel „Slanje kupcu“: za / od `ponuda@paneliprojekt.hr` / predmet / PDF privitak); ponuda do potvrde nosi Hub broj `2026-02823 · v3`; stupac **Rabat** i iznos po stavci = količina × cijena × (1 − rabat), dvije stope kupca u zaglavlju stavki (Humer 15 % / 20 %), PDV 25 % i ukupno; verzije v1 → v3 s vlastitim PDF-om; „Stanje ponude“: nacrt → pošalji → čeka kupca (podsjetnik 7 dana) → kupac potvrdio → eSlog; eSlog gumb više nije na ekranu — ide sam uz potvrdu, „Pošalji u Pantheon odmah“ ostaje kao iznimka (D-11) |
| **3b Kupac potvrdio (dijalog)** | `v04_3b_Kupac_potvrdio.png` | novi mali ekran (620×620): datum potvrde, način (e-mail / telefon / osobno), **rok obećan kupcu** (službeni), rok kupca (napomena), prioritet, tko (iz prijave); popis onoga što Hub napravi na „Potvrdi“ (zaključaj verziju, događaj, eSlog u Pantheon, provjera skladišta, rezervacija, manjak u Nabavu); kvačica „Pošalji eSlog u Pantheon odmah“ |
| **3c Događaji naloga** | `v04_3c_Dogadjaji_naloga.png` | novi mali ekran (760×740, na klik iz Zaglavlja): rokovi i potvrda kupca u zaglavlju, dnevnik iz → u / tko / kada / što (od unosa do potvrde puta), buduće korake upisuje praćenje; osobe po koraku u podnožju (10 §1, §4) |
| 4 Skladište nakon potvrde | `v04_4_Skladiste_nakon_potvrde.png` | odjeljak „Popis za nabavu“ postao „Manjak za nalog“ s gumbom „Otvori u Nabavi“ (Hub ga sam preda modulu nabava); traka ABS 1/22 JELA CLAY prikazana kao „u dolasku 15.09.“; „Što dalje“ prepisano (narudžbenica → primka iz Knjige zatvara) |
| 5 Pila / nesting | `v04_5_Pila_nesting.png` | nepromijenjeno |
| **6 Nabava (Sanela)** | `v04_6_Nabava.png` | **D-42, 10 §3 i §6** — novi ekran, korisnik SA: lijevo Potrebe · manjak / Narudžbenice / Očekivane dobave / Zaprimljeno + dobavljači; sredina tablica POTREBE preko svih potvrđenih naloga (treba Σ, nalozi, fizičko, rezervirano, naručeno, raspoloživo = fizičko − rezervirano + naručeno, manjak, prijedlog „naruči N“ + „iskustveno“ za zalihu unaprijed) i NARUDŽBENICA nacrt N-2026-043 IVERPAN (stavke s vezom na naloge ili „zaliha“, očekivana dobava, status nacrt → poslana → djelomično zaprimljena → zaprimljena, „Pošalji dobavljaču (e-mail)“); desno Kasni (djelomična dobava), Otvorene narudžbenice, Nalozi koji čekaju nabavu, Kako Hub računa; podnožje objašnjava automatsko zatvaranje iz eSlog primke (Knjiga se ne mijenja) |

Pravilo iz §4a provedeno dosljedno: na ekranima više nema oznaka odluka (D-xx / I-xx) — generator ih pri zapisu uklanja (`strip_dxx`) i odbija
ekran na kojem bi ostala oznaka ili riječ „AI“; obrazloženja s oznakama ostaju samo u bilješkama na platnu i ovdje. Brojke na ekranu 3 su iz
stvarne ponude 2823 (rabat 15 % / 20 %, PDV 25 %); ukupno s rabatom na mockupu je 4.673,44 € bez PDV-a (ponuda 2823 ima drukčiji skup stavki —
mockup prikazuje samo dio okova i usluga sažeto). Ilustracija su: e-mail kupca (u Hubu iz šifrarnika kupaca — preduvjet D-40 (1)), datumi i vremena,
verzije v1/v2, nalozi BLAGO / VARGA / BOGDANIĆ, narudžbenice N-2026-04x, primke PR-118x, dobavljači po materijalu.

Pitanja za prezentaciju v0.4 (uz ona iz §4): za Ivanu / Gorana — je li dijalog potvrde (3b) dovoljan ili potvrdu upisuju iz popisa naloga bez
otvaranja ponude; treba li „Pošalji kupcu“ tražiti pregled PDF-a prije slanja; što u mail ide kao tekst (predložak). Za Sanelu — treba li narudžbenici
Pantheonov broj ili je Hubov `N-2026-xxx` dovoljan; koji dobavljači imaju minimalne količine / „samo cijele ploče“ (D-37b); tko smije poslati narudžbu;
je li pregled potreba po materijalu (a ne po nalogu) ono što danas radi u starom programu. Za voditelja — treba li vremenska crta (3c) i njemu, i
gdje: u popisu naloga ili samo u nalogu.

## 5. Sljedeći korak

Prezentacija v0.4 Ivani, Goranu, Saneli i voditelju (ekrani 3, 3b, 4, 5, 6) → povratne informacije → v0.5 (ispravci) → Igor odobrava → kod
kralježnice (04 §4): šifrarnik materijala i traka s aliasima (korak 1), pa nalog + elementi i ekran „Unos naloga“ (korak 2), s tablicama iz 10 §4 od početka.
