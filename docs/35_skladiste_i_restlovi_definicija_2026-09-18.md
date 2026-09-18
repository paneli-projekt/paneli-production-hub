# 35 — Skladište i restlovi: potpuna definicija (prijedlog za potvrdu)

**Datum:** 18. 9. 2026. · **Spaja i dovršava:** D-82 (pravila restlova), D-83 (rezervacije i tok), D-85 (nabava) · **Novo:** slike dekora
**Kod se ne dira dok ovo ne potvrdiš.** Svaka točka ima moj prijedlog; ti odgovaraš „da“ ili kako treba biti. Popis svih odluka na jednom mjestu je u §8.

Mape `06_SKLADISTE_I_RESTLOVI\pravila`, `lokacije_ploca` i `fotografije_oznaka` su prazne — u njima piše upravo ono što ovdje treba odlučiti: „od koje dimenzije se restl čuva, tko odlučuje, što se baca, kako se vodi ulaz ploča“. Zato ovaj dokument.

## 0. Što već radi (da se zna razlika između „postoji“ i „nije dogovoreno“)

| Radi | Ne postoji ili nije dogovoreno |
|---|---|
| Uvoz evidencije restlova (1 363 restla, 90 % vezano na idente), dekori za potvrdu | Prag od kojeg se ostatak uopće čuva; što s ostacima radnih ploča |
| Prijedlog restla iz potvrđene optimizacije (≥ 400 × 400 i ≥ 1 m²), potvrda / odbacivanje | Rok za potvrdu prijedloga; ručni unos restla s ekrana |
| Rezervacija ploča i restla u statusu Skladište, izdavanje na stroj, oslobađanje | Što sa zaboravljenim rezervacijama; razlika plan / stvarno iz `.mno` |
| QR naljepnice restlova (A4, 2 × 5), adresa `/r/R1364` | Ekran koji se otvori na tom QR-u (skladištarev ekran na mobitelu) |
| Stanje punih ploča iz Winstorea, trake iz Regal trake | Stanje ploča koje Winstore ne vodi (radne ploče, ploče stola, zidne obloge) |
| Potrebe za nabavu preko svih naloga, narudžbenica, primka iz eSloga | Tko odobrava narudžbu; e-mailovi dobavljača |
| — | Slike dekora (Egger, Kaindl, Kronospan, Fundermax, Cleaf) |

## 1. Što je restl i kad nastaje

**1.1 Prag — od koje mjere se ostatak čuva.** Sada: ≥ 400 × 400 mm **i** ≥ 1 m² (D-19), isti prag po kojem se ostatak ne naplaćuje kupcu.
*Prijedlog:* prag ostaje zadani, ali se upisuje u Postavke i može biti **manji za skupe materijale** — compact, akril, HPL, furnir ≥ 0,5 m², iveral i MDF ≥ 1 m². Napiši brojke ako su drukčije; ovo je jedina točka koju ne mogu pogoditi iz podataka.

**1.2 Ostatak radne ploče, ploče stola i zidne obloge.** Optimizacija ih već računa (ostatak uz duljinu, najmanje 400 mm), npr. 1 200 × 600.
*Prijedlog:* vode se kao obični restl s QR-om, mjera `duljina × 600 / 900 / 640`, samo kad ploča nije naplaćena kupcu kao cijela.

**1.3 Tko odlučuje da restl postoji.** Hub predloži iz potvrđene optimizacije; **na stanju je tek kad ga skladištar potvrdi** (zalijepi QR, po potrebi ispravi mjeru). Neodgovoreno stanje = nema restla. Ovo ostaje kako je predloženo (D-64/3).

**1.4 Rok za prijedlog.** Sada prijedlog stoji zauvijek.
*Prijedlog:* prijedlog koji nitko ne potvrdi **14 dana** ide u „nije potvrđen“ s napomenom i ne broji se — inače stanje laže, a nitko to ne primijeti.

**1.5 Restl koji ne dolazi iz sheme** (ručni rez, povrat s montaže, ostatak od ranije): skladištar ili ured ga upisuje na ekranu (ident, mjere, lokacija) i odmah dobije QR. API već postoji, treba ekran.

**1.6 Škart.** Sve ispod praga se ne evidentira; taj m² je ionako naplaćen kupcu. *Pitanje:* želiš li mjerenje škarta po nalogu (koliko m² je bačeno) ili to ne trebaš?

## 2. Rezervacije i izdavanje

**2.1 Rezervacija** nastaje kad nalog uđe u status **Skladište**, iz **potvrđene** optimizacije (bez potvrde Hub ne zna količinu i javlja upozorenje). Restl za nalog bira čovjek iz ponuđenih kandidata — Hub ne pogađa.

**2.2 Izdano** = kad nalog ode **na stroj** (pila / nesting): rezervacija → izdano, rezervirani restl → potrošen. Alternativa je čekati povratak `.mno`, ali tada ploče danima stoje „rezervirane“. *Prijedlog: ostaje na slanju na stroj.*

**2.3 Razlika plan / stvarno.** Kad se vrati `.mno` s pile ili nestinga, Hub usporedi planirane i stvarno potrošene ploče i **javi razliku**. Pune ploče se ispravljaju u **Winstoreu** (on je istina), restlove Hub ispravlja sam. Hub nikad ne piše u Winstore.

**2.4 Djelomično izdavanje** (nalog se reže u dva navrata) *prijedlog:* ne vodimo — izdaje se cijeli materijal naloga. Ako se to kod vas događa često, reci pa ćemo dodati „izdaj N ploča“.

**2.5 Zaboravljene rezervacije.** Popis rezervacija starijih od **14 dana** na ekranu Skladište, s gumbom Oslobodi. Oslobađa ured ili voditelj.

## 3. Inventura, potvrde i tko što smije

**3.1 Prvi obilazak.** Ispis naljepnica po regalima (A001…, SATOR B), skladištar prolazi policu po policu: **Potvrdi** / **Ispravi mjeru** / **Otpiši**. Hub pokazuje napredak (npr. 420 / 1 363). Realno 2–3 poludana, radi se po regalu, ne odjednom.

**3.2 Uređaj.** Skladištarev ekran radi u pregledniku na mobitelu ili tabletu, ali Hub je na lokalnoj mreži (`192.168.5.201:8766`). *Pitanje:* ima li skladištar mobitel / tablet i doseže li Wi-Fi u skladište? Ako ne, Hub ispisuje papirnati popis po regalu, a ured naknadno upisuje — sporije, ali radi.

**3.3 Tko što smije:** skladištar potvrđuje restl, ispravlja mjeru i otpisuje; **ured** potvrđuje dekor (koji je ident); voditelj / administrator briše i oslobađa rezervacije. *Pitanje:* smije li skladištar otpisati restl sam ili to mora voditelj?

**3.4 Restlovi s oznakom PROVJERI** (137 iz evidencije: izgrebano, više mjera). *Prijedlog:* broje se na stanju i nude se za naloge, ali s vidljivom oznakom „provjeriti prije rezanja“.

**3.5 Dekori za potvrdu:** 57 dekora (140 restlova) čeka jedan prolaz ureda, 8 dekora nema ident u Pantheonu (`(FRANJIC)`, `IV U775`, `SKUPIII`, `H 1345`…, 21 restl). *Pitanje:* otvaraju li se ti identi u Pantheonu ili ostaju „bez identa“ (vide se u skladištu, ne ulaze u obračun)?

**3.6 Redovna inventura:** jednom u tri mjeseca izvještaj „nije viđeno od…“. Nije obavezno, reci želiš li.

## 4. Winstore, radne ploče i nabava

**4.1 Winstore je istina za pune ploče** koje vodi (nesting regal). Hub ga samo čita i, kad se ne slažu, javi razliku.

**4.2 Ploče koje Winstore ne vodi** — radne ploče, ploče stola, zidne obloge (a možda i compact / furnir; reci koje sve). Danas im nitko ne vodi stanje.
*Prijedlog:* Hub vodi vlastito stanje za te skupine: **ulaz** iz eSlog primke (već imamo), **izlaz** kad nalog ode na stroj, **inventura** ručno kao kod restlova. Posao je oko jednog dana. Alternativa je da se ne vodi stanje nego se naručuje po nalogu — jednostavnije, ali onda Hub ne može reći „imamo li“.

**4.3 Ulaz robe.** *Pitanje:* kako se danas vodi ulaz ploča — samo primkom u Pantheonu ili netko još upisuje u Winstore? Od toga ovisi hoće li Hub uzimati ulaz iz primke ili iz Winstorea.

**4.4 Nabava (D-85).** Dobavljač stavke = dobavljač identa u Pantheonu; ident bez dobavljača ide u nacrt „NEPOZNAT DOBAVLJAČ“. E-mailove dobavljača upisuje Sanela jednom. Naručeno u raspoloživo ulazi tek kad je narudžbenica **poslana**. Primka iz Knjige zatvara narudžbenicu.
*Pitanje:* odobrava li narudžbu netko prije slanja (ti ili voditelj) ili je Sanela šalje sama?

**4.5 Nesting ostaci** ostaju u Winstoreu kao Drop; Hub ih pokazuje uz materijal, ali ih ne vodi kao svoje restlove.

## 5. Ekran skladištara (ono što QR otvori)

Jedna stranica, veliki gumbi, radi na mobitelu: dekor i **slika dekora**, ident, mjere, lokacija, status; gumbi **Potvrdi**, **Ispravi mjeru**, **Otpiši**, **Rezerviraj za nalog**. Ista stranica služi za inventuru (skeniraj → potvrdi) i za svakodnevno traženje („gdje je ovaj restl“).

## 6. Slike dekora (Egger, Kaindl, Kronospan, Fundermax, Cleaf)

**Zašto:** skladištar i ured dekor prepoznaju okom, ne po šifri. Slika uz restl i uz materijal naloga skraćuje traženje i sprječava krivi rez.

**Na što se veže:** na ident, preko `dekor_kod` koji Hub već ima (`W908 ST2`, `K2665 AI`, `27045 OF`, `VSM-06`). Jedna slika vrijedi za sve debljine istog dekora.

**Izvori — provjerio sam što imamo:** u `01_PANELWIZARD` nema nijedne slike dekora, dakle gotovog izvora kod nas nema. Ostaje troje:

1. **Ručno dodavanje s ekrana** — u Šifrarniku povučeš sliku na dekor (ili slikaš uzorak mobitelom). Hub je sprema u `C:\Paneli\Hub\dekori\` (izvan koda, ne ide u Git). Najbrže za dekore koje stvarno koristite.
2. **Skupni uvoz iz mape** — ako Sanela ili dobavljač daju paket slika nazvanih po kodu (`H1277ST9.jpg`), Hub ih poveže sam, a što ne prepozna javi.
3. **Automatsko skidanje s dobavljačevih stranica** po kodu. Izvedivo za Egger i Kronospan, lomljivo (promjena stranice = prestane raditi) i treba provjeriti smijemo li slike koristiti. Ne bih time počinjao.

*Prijedlog:* koraci 1 i 2 odmah (oko jednog dana), korak 3 samo ako se pokaže da vrijedi.

**Gdje se slika vidi:** šifrarnik (sličica u popisu), materijal na nalogu i u dijalogu materijala, popis restlova, skladištarev ekran. *Pitanje:* i na ponudi kupcu? Tehnički lako, ali slike dobavljača na vlastitom dokumentu traže njihovo dopuštenje — za interne ekrane to nije sporno.

## 7. Redoslijed rada nakon tvoje potvrde

1. **Skladištarev ekran + QR + potvrde** — bez toga inventura ne može početi.
2. **Pravila restlova**: pragovi u Postavkama, ostaci radnih ploča, rok prijedloga, ručni unos.
3. **Rezervacije**: zaboravljene rezervacije, razlika plan / stvarno iz `.mno`.
4. **Stanje ploča koje Winstore ne vodi** (radne ploče, zidne obloge).
5. **Slike dekora** — koraci 1 i 2.
6. **Nabava**: dobavljači, odobrenje, zatvaranje primkom.

## 8. Popis odluka koje trebam

| # | Pitanje | Moj prijedlog |
|---|---|---|
| 1 | Od koje mjere se restl čuva? | ≥ 400 × 400 mm i ≥ 1 m²; skupi materijali ≥ 0,5 m² |
| 2 | Ostatak radne ploče je restl? | Da, s QR-om, kad ploča nije naplaćena cijela |
| 3 | Prijedlog restla bez potvrde 14 dana | Sam se gasi uz napomenu |
| 4 | Mjerenje škarta po nalogu | Ne vodimo |
| 5 | „Izdano“ pri slanju na stroj | Da |
| 6 | Djelomično izdavanje naloga | Ne vodimo |
| 7 | Zaboravljene rezervacije | Popis nakon 14 dana, oslobađa ured ili voditelj |
| 8 | Tko smije otpisati restl | Skladištar |
| 9 | Restlovi PROVJERI | Na stanju, s oznakom „provjeriti prije rezanja“ |
| 10 | 8 dekora bez identa u Pantheonu | Otvoriti idente (ili reci da ostaju bez identa) |
| 11 | Mobitel / tablet i Wi-Fi u skladištu | Treba; ako nema — papirnati popis |
| 12 | Stanje ploča koje Winstore ne vodi | Hub ih vodi sam (ulaz iz primke, izlaz s naloga) |
| 13 | Kako se danas vodi ulaz ploča | (trebam odgovor) |
| 14 | Odobrenje narudžbe prije slanja | (trebam odgovor) |
| 15 | Slike dekora: ručno + skupni uvoz | Da; automatsko skidanje zasad ne |
| 16 | Slike dekora i na ponudi kupcu | Zasad samo interno |
