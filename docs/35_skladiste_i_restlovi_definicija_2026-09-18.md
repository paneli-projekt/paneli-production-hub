# 35 — Skladište i restlovi: definicija (odgovoreno 18. 9. 2026.)

**Odluka:** D-95 · **Zamjenjuje prijedloge:** D-82 (restlovi), D-83 (rezervacije i tok), dopunjuje D-85 (nabava)
Igor je 18. 9. odgovorio na sva pitanja; ovdje je dogovoreno stanje. Kod se piše po ovome.

## 1. Analiza evidencije (1 363 restla, 1 535 komada, 1 735 m²)

Mjereno na `RESTLOVI_V7.xlsm` da se prag ne pogađa:

| | |
|---|---|
| medijan restla | **0,90 m²** — polovica stanja je ispod 1 m² |
| najmanji | 430 × 100 mm (0,04 m²) |
| kraća stranica | medijan 545 mm; četvrtina restlova uža od 388 mm |
| trake ≥ 2 400 mm i uže od 400 mm | **127 komada** (medijan širine 300 mm) |
| compact i akril | medijan 0,49 / 0,78 m²; 81 % compacta ispod 1 m² |

Staro pravilo Huba (kraća ≥ 400 mm i ≥ 1 m²) otvorilo bi samo **41 %** onoga što stvarno stoji u regalu (70 % m²). Zato novi prag:

| Pravilo | Restlova | m² |
|---|---|---|
| **≥ 0,35 m² ili traka ≥ 2 000 × 150 mm** | **1 174 (86 %)** | **1 676 (97 %)** |

## 2. Restl — što je i kad nastaje

1. **Prag (ispravak Igor, 18. 9.):** restl je ostatak **≥ 0,35 m²**, ili traka **duža od 2 000 mm i šira od 150 mm** (npr. 2800 × 195 iz evidencije). Prag je u Postavkama.
2. **Obračun se ne mijenja:** kupcu se i dalje ne naplaćuje samo ostatak ≥ 400 × 400 mm i ≥ 1 m². Komade između tog i novog praga zadržavamo u regalu iako ih je kupac platio — kako radi i danas.
3. **Radne ploče, ploče stola i zidne obloge:** njihovi ostaci vode se kao i svi drugi restlovi (QR, stanje), mjera duljina × 600 / 900 / 640. Ako je ploča naplaćena kupcu cijela, ostatak je kupčev i vodi se samo ako ga ostavi nama.
4. **Restl od kupca:** kupac ponekad ostavi svoje komade nama — skladištar ih upisuje ručno na svom ekranu, s oznakom da su došli od kupca. Ista mogućnost pokriva i ostatke ručnog reza i povrate s montaže.
5. **Prijedlog iz sheme:** Hub nakon potvrđene optimizacije predloži restl; na stanju je tek kad ga skladištar potvrdi (QR, po potrebi ispravljena mjera). **Prijedlog se ne gasi sam** — stoji dok ga netko ne potvrdi ili odbaci, uz popis „čeka potvrdu N dana“.
6. **Škart se ne mjeri.**

## 3. Rezervacije i izdavanje

1. Rezervacija nastaje u statusu **Skladište**, iz **potvrđene** optimizacije. Restl za nalog bira čovjek iz kandidata.
2. **Winstore je automatsko skladište i sam poslužuje ploče.** Za materijale u Winstoreu Hub ne vodi izdavanje: smanjenje stanja dolazi iz **novog XML izvoza**, a Hubova rezervacija se zatvara kad nalog ode na stroj. Hub u Winstore ne piše.
3. **Skladištar izdaje samo restlove i materijale kojih nema u Winstoreu** — jedan klik po materijalu naloga, cijela količina.
4. **Zaboravljene rezervacije:** popis rezervacija starijih od **14 dana** na ekranu Skladište, s gumbom Oslobodi (ured ili voditelj). Ništa se ne oslobađa samo.
5. Razlika plan / stvarno iz `.mno` javlja se kao upozorenje; pune ploče ispravlja Winstore, restlove Hub.

## 4. Što Winstore ne drži (Hub vodi sam)

Provjereno na izvozu 11. 9.: nema nijedne ploče duže od 3 050 mm, unutra su iveral, MDF, akril i PVC (2800 × 2070 i slično).

Izvan Winstorea, i Hub im vodi stanje: **radne ploče i ploče stola · zidne obloge · compact i HPL · lesonit, šper, OSB i sirove ploče.**

* **Ulaz:** skladištar upiše prijem odmah kad roba stigne, a kad dođe **eSlog primka** Hub usporedi količine i javi razliku.
* **Izlaz:** skladištar potvrdi izdavanje.
* **Inventura:** ručno, kao kod restlova.

## 5. Winstore izvoz — svježina stanja

Danas izvoz pokreće operater ručno, po potrebi. Dogovoreno:

1. Na VM-u se svakih **30 minuta** vrti uvoz: uzme najnoviji XML iz dogovorene mape, uveze ga i zapiše rezultat; ekran piše koliko je stanje staro i upozorava kad prijeđe zadani broj sati.
2. Skripta `20_ANALIZA\skripte\WINSTORE_PREGLED.bat` (samo čita) pokreće se na Winstore računalu — iz nje se vidi ima li **WINSTORE store manager 1.2.1.0** vlastitu bazu koju možemo čitati, postoji li automatski izvoz i gdje XML završava. Prema nalazu se odlučuje ide li se na izravno čitanje (stanje uvijek svježe) ili ostaje uvoz iz mape.

## 6. Inventura, uloge i uređaji

1. **Prvi obilazak** s QR naljepnicama po regalima; Hub pokazuje napredak. Restlovi s oznakom **PROVJERI** (137) ostaju na stanju i nude se za naloge, uz vidljivo „provjeriti prije rezanja“.
2. **Otpis** smije skladištar, uz zapis imena i razloga.
3. **Ured** potvrđuje dekor (koji je ident); potvrda vrijedi za sve restlove tog dekora i postaje alias.
4. **8 dekora bez identa u Pantheonu** (21 restl) ostaje bez identa i dobiva poveznicu naknadno, kad se utvrdi koji su to dekori.
5. **Uređaj:** u skladištu je računalo, Wi-Fi postoji, a skladištar po potrebi dobiva mobitel ili tablet. Ekran se radi tako da radi na oboje: na računalu popis s tražilicom, na mobitelu QR i veliki gumbi.

## 7. Nabava

Dobavljač stavke = dobavljač identa u Pantheonu; ident bez dobavljača ide u nacrt „NEPOZNAT DOBAVLJAČ“. **Sanela šalje narudžbenice sama**, bez odobrenja. Naručeno ulazi u raspoloživo tek kad je narudžbenica poslana. Primka iz Knjige zatvara narudžbenicu i potvrđuje ulaz.

## 8. Slike dekora (Egger, Kaindl, Kronospan, Fundermax, Cleaf)

Veže se na ident preko `dekor_kod` (W908 ST2, K2665 AI, 27045 OF…); jedna slika vrijedi za sve debljine istog dekora. U `01_PANELWIZARD` nema nijedne slike, pa gotovog izvora kod nas nema.

1. **Ručno dodavanje s ekrana** (povuci sliku ili slikaj uzorak mobitelom) — sprema se izvan koda, u `C:\Paneli\Hub\dekori\`.
2. **Skupni uvoz iz mape** kad dobavljač ili Sanela daju paket slika nazvanih po kodu.
3. Automatsko skidanje s dobavljačevih stranica zasad **ne**.

Slike se prikazuju **samo na internim ekranima**: šifrarnik, materijal naloga, restlovi, skladištarev ekran. Na ponudi kupcu ne.

## 9. Redoslijed rada

**Napravljeno 18. 9.:** prag restla u Postavkama (kartica Restlovi) i prijedlozi restlova po novom pravilu; skladištarev ekran `#/skladistar` (QR → stranica restla, potvrda s lokacijom, ispravak mjere, otpis, ručni restl uključujući „kupac ga je ostavio nama“) i izdavanje: Winstore svoje ploče izdaje sam, a skladištar potvrđuje restlove i materijale kojih Winstore nema. 175 testova.

1. **Skladištarev ekran**: QR / oznaka restla, potvrda restla, ispravak mjere, otpis, ručni unos (uključujući restl od kupca), izdavanje restlova i materijala izvan Winstorea.
2. **Pravila restlova**: novi prag u Postavkama, ostaci radnih ploča, popis „čeka potvrdu“.
3. **Uvoz Winstore XML-a svakih 30 minuta** + starost stanja na ekranu; pregled Winstore računala kad stigne ispis skripte.
4. **Stanje ploča izvan Winstorea**: ulaz (upis + primka), izlaz, inventura.
5. **Zaboravljene rezervacije** (14 dana) i razlika plan / stvarno iz `.mno`.
6. **Slike dekora**: ručno dodavanje i skupni uvoz.
