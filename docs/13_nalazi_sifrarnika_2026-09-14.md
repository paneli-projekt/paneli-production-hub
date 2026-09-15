# Nalazi o šifrarniku — što ispraviti u Pantheonu (D-45)

Generirano iz Hub baze (`py -m hub.sifrarnici.nalazi`), bez ikakve izmjene podataka.
Hub radi i **bez** ovih ispravaka — sve što ne prepozna sigurno, pita na ekranu. Ispravci samo smanjuju broj pitanja uredu.

**Ukratko:** od 1573 aktivnih materijala 236 nema debljinu, a u Pantheonu stvarno treba dirati samo **0 identa** (1.1 + 1.3);
compact i zidne obloge su riješeni; ostalo su stari dekori koji se ne koriste.

| Prioritet | Identa | Što napraviti |
|---|---|---|
| 1 - isti ident za vise debljina | 0 | razdvojiti u dva identa (vidi 1.1) |
| 2 - ploce na stanju, debljina nepoznata | 0 | dopisati debljinu (vidi 1.2) |
| 3 - koristi se, treba dopisati debljinu | 0 | dopisati debljinu u naziv (vidi 1.3) |
| 4 - compact i zidne obloge, ured kaze debljinu | 0 | upisati debljinu u Hub (vidi 1.4) |
| 5 - ne koristi se | 236 | ništa — stari dekori i stavke koje nisu ploče |

## 0. Što je ured već riješio u Hubu (66)

Ove odluke žive u Hubu (`py -m hub.sifrarnici.ispravci`) i preživljavaju svaki novi uvoz — Pantheon ih ne mora imati.

| Što | Ident / kod | Vrijednost | Napomena |
|---|---|---|---|
| debljina | IV000106 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): IVERAL ZELENI 021 |
| debljina | IV000259 | 13 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT PLOČA CRNA - CRNA ISPUNA 080FH |
| debljina | IV000417 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): MDF FRONTA PVC FP0204 ANTRACIT |
| debljina | IV000651 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): IVERAL U12188XM/ML SVJETLO SIVA V100A |
| debljina | IV000661 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): AKRIL CASHMERE VA -115 |
| debljina | IV000686 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): MDF FRONTA FP0605 PICASSO INOX |
| debljina | IV000722 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): PVC BIJELI KAMEN VHG-20 |
| debljina | IV000784 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT F637 ST10 |
| debljina | IV000802 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA OBLOGA F812/H050 |
| debljina | IV000806 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): IVERAL MIDNIGHT PLAVA K099 |
| debljina | IV000849 | 13 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT MANGO 0010 FH CRNA ISPUNA |
| debljina | IV000851 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): IVERAL K096 GLINENO SIVA |
| debljina | IV000885 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT FANGO S CRNOM JEZGROM 2206AP |
| debljina | IV000920 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT F187 |
| debljina | IV000921 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT KARA 0566 FH CRNA ISPUNA |
| debljina | IV000959 | 13 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT TORTONA 2289 FH |
| debljina | IV000960 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): IVERAL K353 CHARCOAL FLOW |
| debljina | IV000961 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): MDF FRONTA FP0608 KAŠMIR ZLATNA |
| debljina | IV000994 | 18 | Igor 14.9.2026.: dopunjeno i u nazivu u Pantheonu |
| debljina | IV001018 | 13 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT H1180 ST37 HALIFAX NATURAL |
| debljina | IV001032 | 19 | Igor 14.9.2026.: MDF U665 PM/ST9 MAT je 19 mm (U665PM-18 je drugi artikl) |
| debljina | IV001036 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): IVERAL H1242 SHEFFIELD BAGREM NATUR |
| debljina | IV001079 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT F800 ST9 |
| debljina | IV001101 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT F244 |
| debljina | IV001114 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT SLIM LINE SLATE VULCANO S CRNOM JEZGROM-K2877PH |
| debljina | IV001141 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA OBLOGA F234ST76/F251ST9 |
| debljina | IV001223 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT SLIM LINE MARBLE EMPERADOR S CRNOM JEZGROM K2884PH |
| debljina | IV001224 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT SLIM LINE SLATE CRNI SA CRNOM JEZGROM 0190SL |
| debljina | IV001225 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT SLIM LINE CRNI S CRNOM JEZGROM 2190OM |
| debljina | IV001266 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT EXT CAVE S CRNOM JEZGROM 0428NN/NW |
| debljina | IV001267 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT SILVRETTA S CRNOM JEZGROM 0229FH |
| debljina | IV001272 | 18 | Igor 14.9.2026. (obrazac compact i zidne obloge): IVERAL MACADAMIA K681 DP |
| debljina | IV001274 | 19 | Igor 14.9.2026.: IVERAL FURNIR HRAST 1 KLASA je 19 mm |
| debljina | IV001304 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT FANGO S CRNOM JEZGROM 2206FH |
| debljina | IV001307 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): COMPACT U999 ST76 12/650MM |
| debljina | RP000092 | 15 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA KAINDL |
| debljina | RP000201 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA U702 ST89 |
| debljina | RP000207 | 12 | Igor 14.9.2026. (obrazac compact i zidne obloge): RP COMPACT F222 ST76 TERRA TESINA CERAMIC |
| debljina | RP000224 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA F229 ST75 |
| debljina | RP000227 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA F226/F229 |
| debljina | RP000229 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA F121/F117 |
| debljina | RP000241 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA OBLOGA F800 ST9/H1313 ST10 |
| debljina | RP000247 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA F108/F208 ST75 |
| debljina | RP000253 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA F227 |
| debljina | RP000257 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA F095 ST87/F093 ST7 |
| debljina | RP000305 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA W1000 ST76 |
| debljina | RP000306 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA F186 ST9/F032 ST78 |
| debljina | RP000308 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA H1180 ST37 |
| debljina | RP000309 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA H3157/H2033 |
| debljina | RP000312 | 8 | Igor 14.9.2026. (obrazac compact i zidne obloge): ZIDNA PLOČA F836 ST75/F267 ST76 |
| debljina_umjesto_naziva | IV001290 | 19 | Igor 14.9.2026.: ploca je 19 mm, naziv u Pantheonu jos kaze 18 - bit ce ispravljen u Pantheonu |
| ne_koristi_se | IV000633 | 1 | Igor 14.9.2026.: ne koristi se - za taj dekor postoje IV000941 (18 mm) i IV001106 (25 mm) |
| ne_koristi_se | IV000698 | 1 | Igor 14.9.2026.: ZIDNA OBLOGA PURE se ne koristi, debljina nije bitna |
| winstore_kod | 0162PE-25 | IV000079 | Operater 14.9.2026. (obrazac Winstore kodova) |
| winstore_kod | 0227-19 | IV000328 | Operater 14.9.2026. (obrazac Winstore kodova) |
| winstore_kod | 0514AM-18 | IV000405 | Operater 14.9.2026. (obrazac Winstore kodova) |
| winstore_kod | 2800AB-19 | IV000065 | Operater 14.9.2026. (obrazac Winstore kodova) |
| winstore_kod | 37737ND-19 | IV000052 | Operater 14.9.2026. (obrazac Winstore kodova) |
| winstore_kod | H1277ST9-18 | IV000886 | Operater 14.9.2026. (obrazac Winstore kodova) |
| winstore_kod | H3303ST10-18 | IV000941 | Hamilton hrast natur 18 mm (Winstore jos vodi stari ST10 kod) |
| winstore_kod | H3303ST10-25 | IV001106 | Hamilton hrast natur 25 mm (Winstore jos vodi stari ST10 kod) |
| winstore_kod | IV000065-25 | IV001027 | Operater 14.9.2026.; Igor: hrast furnir 26 mm - IV001027 ce dobiti novi kod u Winstoreu, naknadno |
| winstore_kod | IV000115-19 | IV000115 | Operater 14.9.2026. (obrazac Winstore kodova) |
| winstore_kod | K4892DP-19 | IV000507 | Operater 14.9.2026. (obrazac Winstore kodova) |
| winstore_kod | MOSAICOFB35-19 | IV001290 | Operater 14.9.2026. (obrazac Winstore kodova) |
| winstore_kod | U999TM28-18 | IV000988 | Operater 14.9.2026.; Igor: ploca je zbilja 19,6 mm - sifra u Winstoreu ce biti izmijenjena |

## 1. Identi bez debljine

### 1.1 Isti ident za više debljina (0)

Kad naziv nema debljinu, Hub je preuzima iz Winstorea. Kad Winstore za isti ident ima dvije, Hub ne zna koja je ploča koja
— ne može ni izračunati broj ploča ni cijenu. Rješenje je dvoje: ured u Hubu kaže koja je debljina prava (D-51),
ili se u Pantheonu naprave dva identa (`… 18` i `… 25`) pa se Winstore kodovi, koji već nose debljinu, povežu sami.

Nema — nijedan ident više nema dvije debljine u Winstoreu.

### 1.2 Ploče na stanju bez poznate debljine (0)

Nema — svaki materijal koji ima ploče na skladištu ima i debljinu (iz naziva ili iz Winstorea).

### 1.3 Koriste se, a nemaju debljinu (0)

Ovi identi dolaze na ponude (imaju potvrđen alias iz ponuda) ili su bili na nalozima, ali im debljina nije u nazivu.
Hub ih prepozna i radi dalje, ali debljinu mora uzeti iz datoteke naloga ili pitati ured. Dopisivanje debljine u naziv
(npr. `IVERAL ZELENI 021 18`) briše to pitanje zauvijek.

| Ident | Naziv u Pantheonu | Vrsta | Gdje se koristi |
|---|---|---|---|

### 1.4 Compact i zidne obloge (0) — ured kaže debljinu jednom

Radne ploče i ploče stola Hub zna sam (38 mm po pravilu). Compact i zidne obloge ne zna: u šifrarniku postoje
compact ploče od 6, 8, 12 i 13 mm, a zidne od 8 i 18 mm, i to se iz naziva ne vidi. Ne pogađa se — Hub bi tada
krivo izračunao i broj ploča i cijenu.

Uz ovaj dokument ide obrazac **`13_compact_i_zidne_debljine.csv`**: ured upiše broj u stupac `vrijednost`, a zatim
`py -m hub.sifrarnici.ispravci --db hub.db --csv 13_compact_i_zidne_debljine.csv` sve upiše odjednom.
Reci Pantheonu ili Hubu — svejedno; ako debljina uđe u naziv u Pantheonu, ima prednost.

Nema — ured je debljinu rekao za sve compact ploče i zidne obloge koje se koriste.

### 1.5 Ne koriste se (236) — ne dirati

Stari dekori i stavke koje nisu ploče (masiv, profili, okov, lakirane fronte). Puni popis je u priloženom CSV-u.

## 2. Winstore kodovi bez Pantheon identa (73)

Kodovi iz Winstore izvoza koje Hub nije uspio spojiti ni s jednim identom. Ambalažne podloge se ne broje (D-49):
28 kodova, 57 ploča.

### 2.1 Imaju stanje — ove riješiti (2)

Ploče fizički stoje na regalu, a Hub ih ne zna ni rezervirati ni potrošiti ni naplatiti: kad kupac naruči taj dekor,
Hub će reći da ga nema. Tri su razloga i tri rješenja: (1) dekor postoji u Pantheonu, samo je kod drukčije zapisan
→ upisati vezu u Hub (`--kod KOD=IDENT`) ili uskladiti kod u Winstoreu; (2) dekora nema u Pantheonu → otvoriti ident;
(3) nije dekor nego stanje robe (`POVRAT OSTECENO`) → dogovoriti kako se vodi.

Uz dokument ide obrazac **`13_winstore_kodovi_bez_identa.csv`**: operater nestinga uz regal upiše ident u stupac
`vrijednost`, pa `py -m hub.sifrarnici.ispravci --db hub.db --csv 13_winstore_kodovi_bez_identa.csv` sve poveže odjednom.

| Kod | Opis u Winstoreu | Debljina | Cijelih | Ostataka |
|---|---|---|---|---|
| U125ST9-18 | IVERAL PJESCANO ZUTI 18MM | 18.0 | 2 | 0 |
| 1111PO-18 | POVRAT OSTECENO | 18.0 | 1 | 0 |

### 2.2 Bez stanja (71) — ne hitno

Stari dekori koji su ostali u Winstore šifrarniku, a nema ih na skladištu. Smetaju tek ako se dekor ponovo naruči.

<details><summary>Popis</summary>

| Kod | Opis u Winstoreu | Debljina |
|---|---|---|
| 000111-19 | NEPOZNATI DEKOR 19MM | 19.0 |
| 001-19 | REST PLOCA | 19.0 |
| 0077FH-18 | IVERAL GRAFIT 0077FH 18MM | 18.0 |
| 0114PE-16 | IVERAL BIJELA 0114PE 16MM | 16.0 |
| 0197SU-18 | IVERAL CHINCHILLLA 0197SU 18MM | 18.0 |
| 0344BS-18 | IVERAL TRESNJA SVIJETLA 0344BS 18MM | 18.0 |
| 0514AG-18 | AKRIL IVORY 0514AG 18MM | 18.0 |
| 0836RN-19 | IVERAL LAGOS 0836RN 19MM | 19.0 |
| 1101BS-19 | IVERAL WHITE RAL 1101 BS 19MM | 19.0 |
| 2124FH-18 | IVERAL CAMOMILLA 2124FH 18MM | 18.0 |
| 2190AE-19 | IVERAL CRNI 2190AE 19MM | 19.0 |
| 2190CN-19 | IVERAL CRNI CN 2190 CN 19MM | 19.0 |
| 2191PE-19 | IVERAL SIVI NK 2191 PE 19MM | 19.0 |
| 22458MN-19 | IVERAL AVOKADO ZELENA 22458 MN 19MM | 19.0 |
| 22864MN-19 | IVERAL CURCUMA YELLOW 22864MN 19MM | 19.0 |
| 24230BS-19 | IVERAL ADOBE GREY 24230BS 19MM | 19.0 |
| 2443AT-19 | IVERAL JELA CLAY K2443AT 19MM | 19.0 |
| 27193PE-19 | IVERAL PLATINASTO SIVI 27193PE 19MM | 19.0 |
| 32360AN-19 | IVERAL HRAST CASTELL 32360 AN 19MM | 19.0 |
| 34141RI-19 | IVERAL HRAST SANREMO BRONCA 34141RI 19MM | 19.0 |
| 34217RI-19 | IVERAL HRAST SANREMO KRISTAL 34217RI 19MM | 19.0 |
| 37166OM-19 | MDF TAUPE 37166OM 19MM | 19.0 |
| 37706MN-19 | IVERAL BUKVA CORE 37706MN 19MM | 19.0 |
| 38932PR-25 | IVERAL HRAST DIVLJI 38932R 25MM | 25.0 |
| 4035NI-19 | IVERAL NOCE PAVIA 4035 NI 19MM | 19.0 |
| 4037PM-19 | IVERAL ROVERER NEWPORT OAK 4037PM 19MM | 19.0 |
| 42238BETON-19 | BETON ART INFINITY RESTL 19MM | 19.0 |
| 517HP-18 | IVERAL SONOMA FURNIR 517HP 18MM | 18.0 |
| 517HP-25 | IVERAL SONOMA FURNIR 517HP 25MM | 25.0 |
| 5580GT-19 | IVERAL TITAN ANTRACIT 5580 GT 19MM | 19.0 |
| 6299AG-18 | AKRIL COBALT SJAJ 6299AG 18MM | 18.0 |
| 6299AM-18 | AKRIL COBALT 6299AM 18MM | 18.0 |
| 6299BS-18 | IVERAL KOBALT SIVA 6299BS 18MM | 18.0 |
| 647HG-18 | PVC MATT BUTE WHITE 647 HG 18MM | 18.0 |
| 7166AG-18 | AKRIL LATE SJAJ 7166AG 18MM | 18.0 |
| 7166AM-18 | AKRIL LATTE MAT 7166AM 18MM | 18.0 |
| E1P2-18 | IVERICA SIROVA E1P2 18MM | 18.0 |
| FA42-18 | IVERAL CLEAF PENELOPE FA42 18MM | 18.0 |
| FP0203-18 | PVC SVJETLI KREM FP0203 18MM | 18.0 |
| FP0206-18 | PVC CAPUCCINO FP0206 18MM | 18.0 |
| H1180ST37-18 | IVERAL H1180 ST37 18MM | 18.0 |
| H1242ST10-18 | IVERAL H1242 ST10 18MM | 18.0 |
| H3041TM12-18 | IVERAL EUKALIPTUS NATUR H3041TM12 18MM | 18.0 |
| H3090ST9-18 | IVERAL H3090 ST9 18MM | 18.0 |
| H3730ST10-18 | H3730ST10 18MM | 18.0 |
| K096SU-18 | IVERAL GLINENO SIVA K096SU 18MM | 18.0 |
| K2405AN-19 | IVERAL BOR POLAR URUS K2405AN 19MM | 19.0 |
| K2816AN-19 | IVERAL VENDELA MINDO K2816AN 19MM | 19.0 |
| K353RT-18 | IVERAL CHARCOALFLOW K353RT 18MM | 18.0 |
| K4447HO-19 | IVERAL ANTIQUE EXPRESSIVE K4447HO 19MM | 19.0 |
| K4886AN-19 | IVERAL WALNUT ELEGANCE K4886AN 19MM | 19.0 |
| K5411RI-19 | IVERAL HRAST ENDGRAIN PURE K5411RI 19MM | 19.0 |
| K5414RO-25 | IVERAL HRAST ENDGRAIN CLASSIC K5414 RO 25MM | 25.0 |
| K5574IR-25 | IVERAL HRAST EVOKE SUNSET K5574 25MM | 25.0 |
| K5801GT-18 | IVERAL CROSS BRASS K5801 18MM | 18.0 |
| K681PD-18 | IVERAL MACADAMIA K681 PD 18MM | 18.0 |
| MDF3-3MM | MDF3MM | 3.5 |
| MDF6-6 | MDF SIROVI MDF6 6MM | 6.0 |
| SM0132-18 | PVC ZELENA SALVIA SM0132 18MM | 18.0 |
| U11102XM-18 | IVERAL U11102XM 18MM | 18.0 |
| U12188ML-18 | IVERAL U12188ML 18MM | 18.0 |
| U665PM-18 | MDF U665PM 18MM | 18.0 |
| U775ST9-18 | IVERAL U775_ST9 BIJELO SIVA | 18.0 |
| U961ST17-18 | IVERAL U961 ST17 18MM | 18.0 |
| U961ST9-25 | IVERAL U961 ST7 25MM | 25.0 |
| U999ST7-10 | IVERAL U999ST7 10MM | 10.0 |
| U999TM-18 | IVERAL U999TM28 18MM | 18.0 |
| VA115-18 | AKRIL KASMIR VA115 18MM | 18.0 |
| VA116-19 | AKRIL METALIC GREY VA116 19MM | 19.0 |
| W1200ST9-18 | IVERAL PORCULAN BIJELA W1200 ST9 18MM | 18.0 |
| W960ST7-25 | IVERAL W960 ST7 25MM | 25.0 |

</details>

### 2.3 Debljina se ne slaže (2)

Kod je povezan s identom, ali Winstore i Pantheon govore različitu debljinu — skladište i obračun bi se razišli.
Ispraviti jedno od dvoje: kod u Winstoreu (npr. `…-25` → `…-26`) ili naziv identa u Pantheonu.

| Kod | U Winstoreu | Ident | Naziv u Pantheonu | Debljina identa |
|---|---|---|---|---|
| IV000065-25 | 25.0 mm | IV001027 | IVERAL FURNIR HRAST 26MM E/EB | 26.0 mm |
| U999TM28-18 | 18.0 mm | IV000988 | IVERAL U999 TM28 CRNI GOD 19,6MM | 19.6 mm |

## 3. Dva identa s istim nazivom (2 materijala, 9 traka)

Po nazivu se ne razlikuju, pa Hub kod njih uvijek traži potvrdu — ured mora izabrati ident ručno.
Ako je jedan od dva neaktivan ili višak, zatvaranjem u Pantheonu pitanje nestaje.

| Naziv | Identi |
|---|---|
| ŠPERPLOČA BUKVA 10MM | IV000177,IV000905 |
| ŠPERPLOČA OKUME 10MM | IV000103,IV000353 |
| ABS 1/22  HEMLOCK WETLAND K4945 SV | TR000723,TR000724 |
| ABS 1/22 BETON ART TERRA GREY | TR001006,TR001021 |
| ABS 1/22 JASEN LIMPIDO GOLD | TR001250,TR001261 |
| ABS 1/22 U755 ST9 | TR001168,TR001312 |
| ABS 1/44 F206 ST9 | TR000911,TR001050 |
| ABS 1/44 HRAST PALLIDUS | TR001221,TR001237 |
| ABS 1/44 MARBLE EMPERADOR | TR001207,TR001248 |
| ABS 2/44 BRIJEST | TR000122,TR000212 |
| ABS 2/44 IBERIJSKI JAVOR | TR000630,TR000716 |

## 4. Što napraviti, redom

1. ~~Isti ident za više debljina~~ — riješeno.
2. ~~Identi bez debljine koji se koriste~~ — riješeno.
3. ~~Compact i zidne obloge~~ — riješeno.
4. Riješiti 2 Winstore kodova sa stanjem iz 2.1 (upisati kod na ident ili otvoriti ident).
4b. Uskladiti debljinu za 2 koda iz 2.3.
5. Ako je lako: zatvoriti višak od dva istoimena identa iz 3.

Ostalo (1.5, 2.2) ne dirati — stari dekori i stavke koje nisu ploče.

Kad je ispravljeno, novi izvoz iz Pantheona i Winstorea pa:

```
py -m hub.sifrarnici.uvoz --db hub.db --pantheon ph_identi.csv --winstore <XML>
py -m hub.sifrarnici.nalazi --db hub.db --md 13_nalazi_sifrarnika.md --csv 13_identi_bez_debljine.csv
```

Popisi u ovom dokumentu se tada skrate; kad su 1.1, 1.3, 1.4 i 2.1 prazni, šifrarnik je čist.
Hub do tada radi normalno — sve nejasno završi na popisu „za potvrdu“ i ured odluči jednom, pa Hub zapamti.

