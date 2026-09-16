# Paneli Production Hub — 20: Web katalog i konfigurator korpusa (prijedlog za odobrenje)

Stanje 15. 9. 2026. navečer. Igor želi javnu web stranicu po principu meble.pl/na-wymiar: katalog korpusa, cjenik koji se računa
odmah, upute za sastavljanje i narudžba koja bez prepisivanja završi kao nalog u Hubu. Ovo je **popis tipova korpusa i parametara
koje treba odobriti prije nego se išta programira** — ništa u ovom dokumentu još nije kod. Veza na ranije: I-07 (portal za kupce),
D-40 (ponuda iz Huba, cijene iz Pantheona), D-48 (krajnji kupci), D-30 (dva ulaza u standardni nalog), memorija „online korpusi“
(tržišno istraživanje od 13. 9.).

**Sažetak u tri rečenice.** Web stranica ne računa ništa sama: svaki tip korpusa je *recept* koji iz mjera i opcija kupca napravi
popis elemenata s rubovima i okovom, a cijenu i nalog radi Hub istim pravilima kao za ured. Za početak predlažem **17 tipova** (od
63 koliko ih ima meble.pl) i **jednu razinu isporuke** — rezane i kantirane ploče s okovom u paketu (ono što pogon već radi svaki dan),
bušenje i sastavljanje tek u drugoj fazi. Preduvjet je korak 4 kralježnice (obračun + ponuda), jer bez njega web nema što računati.

## 1. Kako to radi meble.pl (nalaz, 15. 9.)

Pogledane su kategorija `na-wymiar/szafki-kuchenne` i dvije stranice proizvoda (donji standardni, gornji s klapnom).

| Što | Kako je kod njih |
|---|---|
| Katalog | ~63 „proizvoda“ = tipova korpusa u 5 skupina: donji, gornji, sudoper, visoki (słupki), dodaci (sokl, blenda, fronta perilice) |
| Mjere | slobodne, **u koraku 1 mm**, s rasponom po tipu: donji Š 600–1200 / V 250–1000 / D 300–700; gornji Š 250–1800 / V 205–600 / D 200–600 |
| Materijal | Egger iveral (390+ dekora) ili Rehau akril za fronte; dekor korpusa i fronte biraju se odvojeno; smjer goda bira kupac |
| Traka | 0,8 ili 2 mm, posebno za korpus i za frontu; traka fronte u boji fronte ili korpusa |
| Vrata / police | bez fronte, 1 vrata L/D, 2 vrata, samo korpus; 0–5 polica (više polica traži minimalnu visinu); raspored bušenja polica po shemi 32 mm |
| Okov | Blum Clip Top 110 soft-close zadano (uz „basic / optimum / premium“), Aventos HK-XS za klapne, Tip-On, ručke iz popisa, nogice 100 mm |
| Sastavljanje | **flat-pack**, ploče izbušene; opcije: tipla + konfirmat (zadano), samo tipla, bez bušenja, tipla + ekscentar |
| Posebnosti | bočnica može biti produžena (0–100 mm) ili spuštena (0–150 mm); izrez u leđima za vješalice |
| Cijena | odmah na ekranu, mijenja se sa svakom promjenom; „točnost rezanja 0,2 mm“ |
| Upute | PDF po tipu (npr. `DST_lewe.pdf`), 3D prikaz u konfiguratoru, svaki element etiketiran s brojem i mjerom |
| Rok / dostava | 13 radnih dana; dostava po veličini narudžbe; unos u stan besplatan |

Ono što treba preuzeti kao princip: **tip korpusa = parametri + pravila**, a ne gotov proizvod s fiksnom cijenom; korpus i fronta
biraju se odvojeno; upute i etikete nastaju iz istih podataka kao rezanje.

## 2. Što web stranica jest u odnosu na Hub

    web (katalog, konfigurator, košarica)  →  Hub API (recept → elementi, obračun, nalog)  →  isti tok kao danas (D-35)

- **Recepti su u Hubu**, ne na webu. Web pokazuje i šalje parametre; Hub iz njih radi elemente, rubove, okov, cijenu. Isti recept vrijedi
  i kad Ivana u uredu za kupca na telefonu „složi“ korpus — nema drugog cjenika.
- **Cijene** su iz Pantheona (`pantheon_ident`, D-40), rabat po kupcu (D-40), krajnji kupac 0 % (D-48). Web ne smije imati vlastiti cjenik.
- **Šifrarnik** materijala i traka je Hubov; za web se materijal samo označi „nudi se online“ (novi stupac `materijal.web` — popis dekora
  bira Igor, §7 pitanje 4).
- **Narudžba s weba = nalog** `vrsta = usluga`, novi `izvor = web`, kupac po D-48 (fizička osoba u Hubu, u Pantheon kao „Krajnji kupac“;
  tvrtka s OIB-om kao svoj subjekt). Status i dalje po D-35: `ponuda` → ured potvrdi (ili automatski nakon uplate, §6) → `potvrdjeno`
  → skladište → pila / nesting.
- **Javna stranica ne stoji na VM-u 192.168.5.201.** Vanjski poslužitelj (npr. Hetzner, ~5–10 €/mj) drži web i košaricu; Hub na VM-u
  se s njim spaja sigurnim kanalom (VPN / tunel), a ne otvorenim portom. Ako Hub padne, web i dalje prima narudžbe i dostavi ih kad se
  veza vrati (zato košarica mora znati cijenu i bez Huba — §5).

## 3. Razina isporuke — prva odluka

meble.pl isporučuje izbušen flat-pack. Kod nas bušenje danas radi samo nesting iz Corpusovih CIX-ova (D-29), a rezanje + kantiranje bez
bušenja je dnevni posao (10–15 naloga). Zato tri razine, redom kako ih ima smisla uvoditi:

| Razina | Što kupac dobije | Što Hub mora znati | Kad |
|---|---|---|---|
| **A — kroj** | rezane i kantirane ploče + okov u paketu (šarke, nogice, spojnice, leđa) + upute za bušenje/sastavljanje na papiru | recept → elementi + rubovi + okov (isto što i danas radi ured iz krojne liste) | **MVP** |
| **B — izbušeno** | kao A, ali s bušenjem za šarke, police, spojnice → sklapa se odvijačem | recept → i CIX predložak po tipu (Hub već piše CIX za nesting, D-60) | faza 2, nakon dogovora s voditeljem (svaki web nalog ide na nesting) |
| **C — sastavljeno** | gotov korpus | montaža + ambalaža + dostava gabarita | kasnije, samo ako istraživanje od 13. 9. pokaže potražnju |

Preporuka: **MVP = razina A**, jer ne traži nijedan novi proces u pogonu, a kupcu (stolar, DIY) daje ono što danas ionako naručuje
na papiru — samo brže i bez pogreške u prepisivanju. Razina B je ono što meble.pl prodaje i vjerojatno je pravi cilj za krajnjeg kupca;
ali traži CIX predloške po tipu, koje treba napraviti i provjeriti s tehničkom pripremom i operaterom nestinga.

## 4. Popis tipova korpusa — prijedlog

Šifra tipa je stalna (koristi se u receptu, na etiketi, u uputama). **Prvi val = 17 tipova označenih ●**; ostalo (○) dodaje se kad prvi
val proradi. Mjere su korpusa bez fronte i bez nogica; rasponi su prijedlog za potvrdu s tehničkom pripremom.

### 4.1 Donji korpusi (DK) — V zadano 720, D zadano 510 (+ fronta = 530), nogice 100 zasebno

| Šifra | Tip | Š | V | D | Posebne opcije | Val |
|---|---|---|---|---|---|---|
| DK-1V | donji, 1 vrata (L/D) | 150–600 | 300–1000 | 300–700 | police 0–4 | ● |
| DK-2V | donji, 2 vrata | 600–1200 | 300–1000 | 300–700 | police 0–4 | ● |
| DK-OT | donji otvoreni (bez fronte) | 150–1200 | 300–1000 | 300–700 | police 0–4 | ● |
| DK-L2 | donji ladičar, 2 ladice | 300–1200 | 600–1000 | 450–600 | visine ladica iz popisa vodilica | ● |
| DK-L3 | donji ladičar, 3 ladice | 300–1200 | 600–1000 | 450–600 | isto | ● |
| DK-L4 | donji ladičar, 4 ladice | 300–1200 | 700–1000 | 450–600 | isto | ○ |
| DK-VL | donji, 1 vrata + 1 unutarnja ladica | 400–1000 | 600–1000 | 450–600 | | ○ |
| DK-SU | sudoper (bez poda ili s izrezom, bez polica) | 450–1200 | 600–1000 | 450–700 | 1 ili 2 vrata; opcija s blendom umjesto gornje fronte | ● |
| DK-PE | za ugradbenu pećnicu (niša 600 × 595) | 600 | 720 | 510–600 | ladica ispod pećnice da / ne | ● |
| DK-PL | za ploču za kuhanje (bez gornje vezice) | 600–900 | 600–1000 | 450–700 | 1 / 2 vrata / ladice | ○ |
| DK-CA | uski cargo (bočni izvlačni) | 150–300 | 600–1000 | 450–600 | fronta se veže na koš | ○ |
| DK-KS | kutni slijepi (s praznim dijelom) | 900–1300 | 300–1000 | 300–700 | slijepi dio L/D, širina slijepog dijela | ● |
| DK-KL | kutni L (dvije fronte pod 90°) | 900×900–1000×1000 | 300–1000 | 510–600 | lazy susan da / ne | ○ |

### 4.2 Gornji korpusi (GK) — V zadano 720 (opcija 900), D zadano 320

| Šifra | Tip | Š | V | D | Posebne opcije | Val |
|---|---|---|---|---|---|---|
| GK-1V | gornji, 1 vrata (L/D) | 150–600 | 300–1200 | 200–450 | police 0–4 | ● |
| GK-2V | gornji, 2 vrata | 600–1200 | 300–1200 | 200–450 | police 0–4 | ● |
| GK-OT | gornji otvoreni | 150–1200 | 200–1200 | 200–450 | police 0–4 | ● |
| GK-KL | gornji s klapnom (Aventos HK / HF ili plinski podizač) | 300–1200 | 300–800 | 200–450 | vrsta podizača iz popisa | ● |
| GK-NA | za napu (ugradbena, niša 600 / 900) | 600 / 900 | 300–800 | 300–350 | | ● |
| GK-MV | za mikrovalnu (niša ~ 380 mm) | 600 | 400–800 | 320–450 | s klapnom iznad da / ne | ○ |
| GK-OC | s ocjeđivačem posuđa (bez polica, žica) | 600 / 800 / 900 | 600–900 | 300–350 | | ○ |
| GK-KS | kutni slijepi | 800–1200 | 600–1200 | 300–350 | slijepi dio L/D | ○ |
| GK-KL2 | kutni L gornji (2 fronte pod 90°) | 600×600 | 600–1200 | 300–350 | | ○ |

### 4.3 Visoki korpusi (VK) — D zadano 560, nogice 100 zasebno

| Šifra | Tip | Š | V | D | Posebne opcije | Val |
|---|---|---|---|---|---|---|
| VK-PO | visoki s policama (ostava), 2 vrata gore/dolje | 300–900 | 1400–2400 | 300–600 | police 2–8, podjela fronti | ● |
| VK-PE | za pećnicu + (mikrovalnu), niša 600 × 595 (+ 380) | 600 | 1400–2400 | 560–600 | niše: pećnica / mikro / obje; ladica ispod | ● |
| VK-HL | za ugradbeni hladnjak (niša 1780 / 1940 / 2030) | 600 | 1900–2400 | 560–600 | visina niše iz popisa | ● |
| VK-CA | visoki cargo (izvlačni) | 300–450 | 1400–2400 | 500–560 | | ○ |
| VK-ZA | visoki s unutarnjim ladicama (space tower) | 450–600 | 1400–2400 | 500–560 | | ○ |

### 4.4 Dodaci (DO) — nemaju korpus, samo elementi

| Šifra | Tip | Parametri | Val |
|---|---|---|---|
| DO-SO | sokl (letva ispod donjih) | duljina, visina 100 / 120 / 150, dekor, traka; kopče za nogice | ● |
| DO-BL | blenda (ispuna, zatvarač prema zidu / stropu) | Š × V, dekor, traka | ● |
| DO-FP | fronta perilice / hladnjaka | Š × V, dekor fronte, traka 1 ili 2 mm | ● |
| DO-ZB | završna bočnica / obloga bočnice (vidljiva strana) | Š × V, dekor, traka | ○ |
| DO-PO | dodatna polica | Š × D, dekor, traka | ● |
| DO-RP | radna ploča po mjeri (D-37 pravila: 1,4 m minimum, > 2,7 m = cijela 4,1 m) | duljina, dekor iz popisa, obrada rubova | ○ (poslije; D-37 već ima pravilo) |

Prvi val = 17 tipova: DK-1V, DK-2V, DK-OT, DK-L2, DK-L3, DK-SU, DK-PE, DK-KS, GK-1V, GK-2V, GK-OT, GK-KL, GK-NA, VK-PO, VK-PE,
VK-HL + dodaci DO-SO, DO-BL, DO-FP, DO-PO (dodaci se broje kao jedan „tip“ jer su svi isti recept: jedna ploča).

## 5. Parametri — što kupac bira

Zajednički za sve korpuse (redom kako ih vidi na ekranu):

1. **Mjere** Š × V × D u mm, korak 1 mm, raspon po tipu (§4). Uz mjeru web odmah crta skicu (kao D-59 na ekranu unosa).
2. **Materijal korpusa** — dekor iz Hubovog šifrarnika s oznakom `web`, debljina 18 mm (19 mm ako je dekor takav — Hub zna debljinu po
   identu, D-52). Za start: bijela + 10–20 dekora koje Igor odabere (§7 pitanje 4).
3. **Fronta** — bez fronte / ista kao korpus / drugi dekor iz istog popisa. MVP: samo iveral. MDF lak, akril i furnir kasnije (drugi
   dobavljač, drugi rok).
4. **Traka** — zadano ABS 1 mm u boji materijala (D-31 „ABS-ISTI“); opcija 2 mm na frontama; 0,5 mm (MEL-ISTI) nudi se samo za nevidljive
   rubove kao „ekonomična kantiranja“ ili se uopće ne nudi (§7 pitanje 5). Traka fronte u boji fronte ili korpusa.
5. **God** — za dekore s godom: okomito / vodoravno (samo fronte; korpus uvijek po pravilu recepta). Hub već vodi `element.god`.
6. **Vrata / fronte** — po tipu: L / D / 2 vrata / bez; kod ladičara visine ladica iz popisa vodilica.
7. **Police** — broj (raspon po tipu), Hub iz visine računa razmak; polica je element s trakom samo na prednjem rubu.
8. **Okov** — paket po tipu iz Pantheon identa (okov već ide u `okov_stavka`, D-32):
   - šarke: standard soft-close (zadano) / premium (Blum Clip top Blumotion) — 2 kom po vratima do 900 mm, 3 kom iznad;
   - vodilice ladica: jedna linija (npr. Blum Tandembox Antaro ili što Pantheon ima najviše) s visinama iz popisa;
   - podizač klapne: iz popisa (Aventos HK-S / HK / HF, plinski);
   - nogice 100 mm (4 kom do 900 mm, 6 kom iznad) + kopče sokla;
   - spojnice: konfirmat + tipla (zadano) / ekscentar (razina B);
   - nosači polica 4 kom po polici; vješalice za gornje (2 kom);
   - ručke: bez (Tip-On / gola fronta) ili iz kratkog popisa — MVP: **bez ručki**, kupac kupuje sam (§7 pitanje 6).
9. **Leđa** — HDF / MDF 3 mm bijela (zadano, u utoru ili s preklopom), ili bez leđa. MDF 3 mm ide na pilu (D-29) — Hub to već zna.
10. **Bočnica produžena / spuštena** (meble.pl 0–100 / 0–150 mm) — **ne u MVP-u**; kad zatreba, to je samo drugi V bočnice.
11. **Količina** korpusa i **napomena** (14 znakova ide na etiketu, D-38; ostalo u nalog).

Što kupac **ne bira** (pravilo recepta, isto za sve): fuga fronti 2 mm (fronta = otvor − 4 mm po širini, − 4 mm po visini), preklop
fronte na korpus, debljina leđa, razmak rupa za police 32 mm, način spajanja poda/stropa (pod na bočnice, gornja vezica kod donjih).
Ove konstante moraju doći od **tehničke pripreme iz Corpusa** — tamo su standardi već definirani i po njima se danas gradi (D-29). Ne
izmišljati druge.

## 6. Kako parametri postaju cijena i nalog

### 6.1 Recept (primjer DK-2V, Š 800 × V 720 × D 510, 18 mm, 1 polica, leđa MDF 3 mm)

| Element | Kom | L × W (mm) | Rubovi (D-62 popis) | Iz čega |
|---|---|---|---|---|
| bočnica | 2 | 720 × 510 | prednji rub ABS 1 (A1); ostali bez | V × D |
| pod | 1 | 764 × 510 | prednji A1 | Š − 2·18 |
| gornja vezica prednja/stražnja | 2 | 764 × 100 | prednja: A1 | Š − 36 |
| polica | 1 | 760 × 490 | prednji A1 | Š − 36 − 4, D − 20 |
| leđa MDF 3 mm | 1 | 716 × 796 | bez | (V − 4) × (Š − 4), s preklopom |
| fronta | 2 | 716 × 396 | sva 4 A1 (ili A2 = 2 mm) | (V − 4) × ((Š − 6) / 2) |

Brojke su ilustracija; **stvarne formule po tipu uzeti iz Corpusovih standarda** (§5, zadnji odlomak). Okov: 4 šarke, 4 nogice,
4 nosača polica, 8 konfirmata, tiple, 20 vijaka za leđa.

### 6.2 Cijena na webu vs. obračun u Hubu

Hubov obračun radi PW-metodom po cijelom nalogu (D-18/D-19: optimizacija → m² za naplatu). Web mora dati cijenu **odmah, po korpusu**,
prije nego nalog postoji, pa treba jednostavnije pravilo koje daje isti red veličine:

    cijena korpusa = Σ elemenata (L × W) × faktor_iskorištenja × cijena_m²(materijal)
                   + Σ metara trake (× 1,10, zaokruženo naviše, D-20) × cijena_m(traka)
                   + usluga rezanja (m²) + usluga kantiranja (m)
                   + okov (Pantheon cijene) + [razina B: usluga bušenja po elementu]
                   − rabat kupca (D-40)

`faktor_iskorištenja` se kalibrira iz benchmarka (40 ponuda, 05 §5.6) tako da web cijena bude **jednaka ili malo viša** od onoga što bi
Hub naplatio PW-metodom — nikad niža. Pravilo za kupca: **cijena s weba je konačna**; ako Hubov obračun kasnije izađe niže, razlika
je marža, ako izađe više, Hub to prijavi uredu kao „web ispod obračuna“ (kalibracija se popravlja, kupac ne dobiva novi račun).
Ovo je nova odluka (**D-68 PREDLOŽENO**, DECISIONS.md).

Web treba cjenik lokalno (kopija iz Huba jednom dnevno), da košarica radi i kad VM nije dostupan (§2).

### 6.3 Narudžba → nalog

1. Košarica → „Naruči“ → kupac upiše ime, e-mail, telefon, (OIB za tvrtku), preuzimanje u Osijeku ili dostava.
2. Web pošalje Hubu: popis korpusa s parametrima + podatke kupca. Hub: kupac po D-48 (traži ponavljača po telefonu / e-mailu / imenu),
   nalog `KUPAC_WEB_BROJ` (npr. `HORVAT_WEB_00123`), `izvor = web`, elementi iz recepta, okov u `okov_stavka` (`potvrdjeno`, jer je iz
   recepta), obračun, ponuda (PDF + mail, D-40/D-41).
3. **Plaćanje MVP: predračun / virman** (bez kartica) — ured vidi uplatu i potvrđuje (D-35, ručna potvrda kao danas). Kartice
   (CorvusPay / Stripe) tek kad se vidi promet; tada uplata = automatska potvrda.
4. Dalje sve kao svaki nalog: skladište, upozorenje za nabavu (D-42), pila / nesting (put: leđa MDF → pila; ostalo po voditelju ili
   po pravilu „web nalozi → nesting“ ako je razina B).
5. Kupcu: e-mail „potvrđeno, rok X“ (rok = `rok_obecan`, D-35) i, uz paket, **popis elemenata s brojevima etiketa + upute** (§6.4).

### 6.4 Upute za sastavljanje

Nastaju iz istih podataka kao nalog, po tipu, kao PDF:
- popis elemenata s mjerama i oznakama etiketa (etiketa nosi naziv naloga i napomenu, D-38 — dodati **oznaku pozicije** `L_BOK`, `POD`…
  kao u Corpusu, `element.pozicija` već postoji);
- popis okova s količinama;
- skica sklapanja po tipu (jedna statična po tipu za MVP; kotirana po mjerama kupca u fazi 2);
- razina A: gdje bušiti (kote rupa za šarke i police po 32 mm shemi) — to je ono što kupac najviše treba kad dobije nebušene ploče;
- razina B: samo redoslijed sklapanja.

Na webu je uz svaki tip javni primjer PDF-a (kao meble.pl), da kupac vidi što dobiva prije narudžbe.

## 7. Što treba od Igora — odluke prije početka

1. **Razina isporuke za MVP** (§3): A (kroj + okov + upute) — preporučeno; ili odmah B (izbušeno, svaki web nalog na nesting)?
2. **Prvi val tipova** (§4, ●): potvrditi / izbaciti / dodati. Posebno: treba li DK-PL (ploča za kuhanje) i GK-MV (mikrovalna) u prvi val?
3. **Zadane mjere i rasponi** (§4): potvrđuje tehnička priprema iz Corpusovih standarda — tko to gleda i kad (Corpus standardi = izvor
   istine za recepte, §5)?
4. **Dekori za web**: koji identi (bijela + koliko dekora), i nudi li se 19 mm uz 18 mm? Popis se označi u Hubu (`materijal.web`).
5. **Trake**: samo ABS 1 mm (+ 2 mm fronte), ili i MEL 0,5 mm kao jeftinija opcija?
6. **Okov**: koja linija šarki / vodilica / podizača je „naša“ (ident u Pantheonu), nude li se ručke uopće?
7. **Cijena** (D-68): slažeš li se da je web cijena konačna i kalibrirana na ≥ PW obračun? Marža na okov ista kao danas?
8. **Plaćanje i dostava**: MVP predračun + preuzimanje u Osijeku; dostava — samo HR, po paketu ili paušal? (istraživanje od 13. 9. ima
   poglavlje logistika — čekati ga?)
9. **Tko potvrđuje web nalog** — ured kao svaki (D-35), ili automatski nakon uplate?
10. **Domena i hosting**: web ide na paneliprojekt.hr (nova stranica, memorija web-stranica) kao dio nje, ili posebna domena
    (npr. korpusi.paneliprojekt.hr)? Pružatelj e-pošte (D-41) treba i za web potvrde.

Što Igor daje uz odluke (jednom, bez programiranja): fotografije 5–10 gotovih korpusa / kuhinja, kratke tekstove o tvrtki i načinu
rada, popis dekora, popis identa okova, Corpusov standard korpusa (jedan projekt po tipu iz prvog vala — dovoljno je izvoz CPW + CSV
kao u `_CORPUS_UZORAK`, iz njega Hub sam pročita formule).

## 8. Redoslijed rada (kad odluke padnu)

| # | Korak | Preduvjet | Gdje |
|---|---|---|---|
| 0 | **Korak 4 kralježnice — obračun + ponuda** (već planirano) | — | Hub |
| 1 | Tablica `tip_korpusa` + `recept` u Hubu; recept → elementi + rubovi + okov; test protiv Corpusovih projekata po tipu (mjere elemenata moraju izaći iste) | Corpus standardi | Hub |
| 2 | Web cijena (§6.2) + kalibracija na benchmarku; API `POST /api/web/cijena` i `POST /api/web/narudzba` | korak 0 | Hub |
| 3 | Javna stranica: katalog 17 tipova, konfigurator sa skicom, košarica, narudžba, cjenik lokalno | 1, 2, dekori, fotografije | vanjski poslužitelj |
| 4 | Upute PDF po tipu + popis elemenata s etiketama | 1 | Hub |
| 5 | Probne narudžbe (Igor, ured, 2–3 stolara) → ispravci → javno | 3, 4 | — |
| 6 | Razina B (CIX predlošci po tipu), kartice, dostava, više tipova i materijala | promet | Hub + web |

Procjena: koraci 1–4 su nekoliko tjedana rada u sesijama nakon koraka 0, pod uvjetom da Corpus standardi stignu odmah. Najveći rizik
nije kod nego **recepti**: ako se formule ne poklapaju s onim što tehnička priprema stvarno gradi, kupac dobije ploče koje se ne
sklapaju — zato test u koraku 1 (Hubov recept mora dati iste elemente kao Corpus za isti korpus) ide prije ijednog ekrana.

## 9. Što ovaj dokument mijenja u postojećem

- **I-07 (portal za kupce)** se proširuje: uz web unos krojne liste dolazi i konfigurator korpusa; oba na istom Hub API-ju.
- **D-30** dobiva treći ulaz u standardni nalog: `izvor = web` (uz kupac_ppw / excel / rukopis / corpus / ručno).
- **Šifrarnik**: novi stupac `materijal.web` (nudi se online), nova tablica `tip_korpusa` / `recept` (korak 1 iz §8).
- **Etiketa**: uz naziv naloga i napomenu, pozicija elementa (`L_BOK`, `POD`…) — potrebno kupcu da spoji ploču s uputom.
- Nova odluka **D-68 PREDLOŽENO** (web cijena konačna, kalibrirana ≥ PW obračun) — u DECISIONS.md.
