# Paneli Production Hub — 09: checklista pitanja za ekrane i tok (odgovori Igora, 12. 9. 2026.)

Pitanja su skupljena iz 07 (mockup, pitanja za sastanak) i 08 (Corpus). Igor je odgovorio korak po korak; „ne znam sada“ = čeka usuglašavanje s
kolegama. Odluke iz ovoga su upisane u DECISIONS: D-29, D-30 i D-32 potvrđeni (ODLUČENO), nove D-33 … D-38. Rezultat (kraj dana 12. 9.): **svih 23
pitanja odgovoreno** — #7 i #19 Igor je odgovorio u trećem krugu; dvije stvari za provjeru (§2) riješene u drugom krugu istog dana.

| # | Pitanje | Odgovor | Status |
|---|---|---|---|
| 1 | Naziv naloga | **KUPAC/PREZIME _ KUPČEV NAZIV NALOGA _ BROJ** (npr. `HUMER_OMIS_2823`); Hub broj u pozadini | odgovoreno (D-33) — primjer potvrđen |
| 2 | Tko otvara nalog i prebacuje u „Proizvodnja“ | **Ured (Ivana/Goran) otvara i prebacuje**; voditelj potvrđuje put pila/nesting | odgovoreno (D-34) |
| 3 | Poseban pogled za voditelja | **Ne — filter u zajedničkom popisu je dovoljan** | odgovoreno (D-34) |
| 4 | Rubovi: miš ili tipke | **Samo miš na prekidače M/A, kao dosad** (bez prečaca L/D/G/B) | odgovoreno (D-36) |
| 5 | God po elementu | **God iz Winstorea (`Grain=1`) obavezno uključen; može se ugasiti po elementu uz pitanje „materijal ima god u strukturi — sigurno?“** | odgovoreno (D-36) |
| 6 | Kerf 16 | **U panelu Zaglavlje naloga** (na klik, mijenja se po nalogu) | odgovoreno (D-36) |
| 7 | Napomena elementa — broj znakova na etiketi | **14 znakova** (Hub broji pri unosu, prvih 14 ide na etiketu, ostatak ostaje u nalogu/CSV-u) | odgovoreno (D-38, 3. krug) |
| 8 | Tko potvrđuje prepoznate elemente iz rukopisa | **Onaj tko unosi nalog** | odgovoreno (D-34) |
| 9 | Zadana traka po materijalu + iznimka po elementu | **Da, pokriva sve slučajeve** | odgovoreno (D-36) |
| 10 | Voditelj prije potvrde puta | **Sheme (PNG) uvijek vidljive** uz svaki materijal | odgovoreno (D-34) |
| 11 | Winstore 0 ploča — tko reagira | **Tok: ponuda iz Huba → čeka potvrdu kupca → nakon potvrde provjera skladišta; Hub daje upozorenje i popis za nabavu** | odgovoreno (D-35) |
| 12 | Operater nestinga | **Iz mape, kao danas** (Hub zapiše CSV+CIX u dogovorenu mapu) | odgovoreno (D-34) |
| 13 | CPW za PW u paralelnom radu | **Uvijek automatski** | odgovoreno (D-36) |
| 14 | Potvrda „izrezano“ s pile | **Ostaje praćenju proizvodnje** (Hub bilježi samo da je CPO poslan) | odgovoreno (D-34) |
| 15 | Radne ploče (RP) — pravilo količine | **600 mm (RADNA PLOČA, M): ploča 4,1 m; minimalna narudžba 1,4 m; ako mjera (ili zbroj mjera) prijeđe 2,7 m prodaje se cijela ploča 4,1 m.** Dopuna: **900 mm (PLOČA STOLA) isključivo pola 2,05 m ili cijela 4,1 m; dekori po narudžbi samo cijela (popis dobavljača slijedi); u ponudi „PLOČA STOLA CIJELA <dekor> n kom“** | odgovoreno (D-37) — provjera na HUMER-u prošla, vidi §2 |
| 16 | Ručne usluge — tko i kada | **Ured pri obračunu** (grupa „Obrade i usluge“ na ekranu obračuna) | odgovoreno (D-38) |
| 17 | Okov | **U Hubu** (grupa uz nalog, isti eSlog) | odgovoreno (D-32 potvrđen) |
| 18 | Tko zaključava ponudu / šalje eSlog | **Ivana i Goran (ured)** | odgovoreno (D-38) |
| 19 | „Naplaćeno vs potrošeno“ — tko vidi | **Realno nitko dok se ne napravi optimizacija na bNestu; onda vidi operater nestinga** → u Hubu prikaz tek iz .mno rezultata, na ekranu pila/nesting, bez zasebnog prava | odgovoreno (D-38, 3. krug) |
| 20 | D-29 Corpus = CAM autoritet, Hub ne generira CIX | **Da** | odgovoreno (D-29 potvrđen) |
| 21 | Obračun za vlastitu proizvodnju | **Oboje**: ponuda/račun kupcu projekta + interni radni nalog / izdatnica materijala | odgovoreno (D-30 potvrđen) |
| 22 | Corpus elementi na pilu pa Rover | **Ne — obrada = uvijek nesting** | odgovoreno (D-29) |
| 23 | Corpus i za uslužne naloge kupaca | **Ne — samo vlastita proizvodnja** | odgovoreno (D-30) |

## 1. Što iz odgovora mijenja ekrane (za mockup v0.3, nakon usuglašavanja s kolegama)

- **Tok naloga dobiva korak „ponuda čeka kupca“ prije proizvodnje** (odgovor 11): Unos → Ponuda (poslana, čeka potvrdu) → Potvrđeno →
  Skladište (upozorenje + popis za nabavu) → Pila / nesting → Proizvodnja → Zatvoren. Danas mockup ima Unos → Provjera → Optimirano → Ponuda →
  Proizvodnja; redoslijed se okreće: ponuda ide PRIJE optimizacije za proizvodnju, a obračun PW-metodom radi se već pri ponudi (što D-18 i predviđa).
- Naziv naloga: `KUPAC_NAZIV_BROJ` (npr. `HUMER_OMIS_2823`) umjesto današnjeg `HUMER_2823_OMIS` — primjer potvrđen.
- Obračun radnih ploča po D-37: 600 mm po metru (min 1,4 m, > 2,7 m cijela), 900 mm „Ploča stola“ pola / cijela (KOM) — ekran 4 dobiva stavku `PLOČA STOLA CIJELA 2 KOM` umjesto „4,99 m“.
- Ekran pila/nesting: sheme (PNG) uvijek prikazane uz materijal, ne na klik.
- Unos: bez tipkovničkih prečaca za rubove; god: kvačica naslijeđena iz Winstore `Grain`, gašenje uz potvrdu.
- Obračun: grupa „Obrade i usluge“ puni se na ekranu obračuna (ured), ne pri unosu; okov u Hubu.
- Corpus nalozi: vrsta „vlastita proizvodnja“ → izlaz = ponuda kupcu + interni radni nalog (dva dokumenta iz istog obračuna).
- Unos: polje napomene elementa s brojačem „14“ — prvih 14 znakova ide na etiketu (CPO / lbl.xml), duži tekst ostaje u nalogu i CSV-u.
- „Naplaćeno vs potrošeno“ seli s ekrana obračuna na ekran pila/nesting, u panel „rezultat sa stroja“ — pojavljuje se tek kad Hub pročita .mno (D-18).

## 2. Za provjeru — riješeno u drugom krugu (12. 9. popodne)

- **RP pravilo na HUMER-u — PROŠLO.** Elementi 2880 × 900 i 2110 × 900 (CPO I_01916) su PLOČA STOLA (900 mm): oba > 2,05 m → 2 × cijela.
  Ponuda 26-010-002823, red 30: `RP000136 PLOČA STOLA CIJELA` **2 KOM** (opis „BASANIT SAND / 2880X900 1K 1KOM + 2110X900MM 1K 1KOM“) — točno po pravilu.
  Moj raniji „nesklad 6,21 m vs 2,4 m“ bio je greška u čitanju ponude: red 31 `RP000259 RADNA PLOČA BASANIT SAND` 2,40 M (600 mm) je zasebna stavka
  koja nije u CPO-u. Ispravljeno u DECISIONS D-37 i u 06 (redak I_01916); ekran 4 mockupa (RP 4,99 m, „pravilo nije potvrđeno“) ispravlja se u v0.3.
- **Naziv naloga — potvrđen**: `HUMER_OMIS_2823` (KUPAC_NAZIV_BROJ).
- ROMIC SA_015896 (RADNA PLOČA 600 mm, elementi 2010 + 2300 = 4,31 m) u ponudi ima 4,41 M — Igor: ručno zaokruživanje pri narudžbi zbog mogućeg
  oštećenja u transportu, nije pravilo (kalkulator daje točne metre, ured po potrebi ručno korigira).
- Popis dobavljača / dekora koji se prodaju samo kao cijela ploča 4,1 m (zastavica „samo cijela“ u šifrarniku RP): sada nije bitan, Igor dopunjuje kasnije.

## 3. Otvoreno

Ništa — sva pitanja iz checkliste odgovorena 12. 9. Popis dekora „samo cijela ploča“ (D-37b) Igor dopunjuje kasnije, kad bude bitan.
