# Paneli Production Hub — IDEJE_KASNIJE (parking)

Ovdje se parkiraju ideje koje NISU u fazi 1. Jedan blok po ideji: što, zašto, kada bi imalo smisla, veza na odluku.

**I-01 Modul "znanje tvrtke" (RAG)** — dokumenti (procedure, dobavljači, standardi, katalozi) → vektorska baza → Claude odgovara djelatnicima iz njih; unutar Huba, isti korisnici/prava. Prije toga: skupiti i strukturirati znanje; opcionalno pilot u AnythingLLM-u. Slaba točka: katalozi s tablicama/cijenama. (D-08, vidi i memorija interni-agent)

**I-02 Vlastiti optimizator pile** — istraživački POC paralelno s fazom 1; ground truth = PW-ove sheme u CPO datotekama (50 materijala u testovima). Metrike: iskorištenje, broj rezova/shema, prihvaćanje operatera. Treba stvarna ograničenja Sektora 450 (glavni rezovi, max duljina, obrez).

**I-03 Automatska odluka pila vs. nesting** — pravilo po CNC obradi, debljini, količini; danas voditelj, cilj administrator pri otvaranju naloga. Čeka odgovor na pitanje 8 iz 04.

**I-04 Etikete iz Huba** — jedan predložak za pilu i nesting (Zebra ZT411 ZPL, 102×64), QR s ID-om elementa; danas dva sustava etiketa.

**I-05 Nesting restlovi** — čitati `.mno` (pozicije dijelova) i automatski predlagati korisni ostatak zadnje ploče kao restl s QR-om.

**I-06 Praćenje proizvodnje u Hubu** — kad stari APEX sustav dođe na red; temelji (kupci, nalozi, korisnici, materijali) pripremljeni u Hubu (D-12). *Dopuna 12. 9.:* što Hub bilježi već sada (događaji, rokovi, osobe, rezervacije, operacije po elementu, narudžbenice) i što praćenje dobiva API-jem — dokument 10, prijedlog D-42.

**I-07 Portal za kupce** — zamjena PPW 5.2 (2020., CPW bez šifri materijala): web unos krojne liste s izborom materijala iz Hubovog šifrarnika; CPW ostaje kao uvoz za stare kupce.

**I-08 Mjesečno usklađenje Hub ↔ Pantheon** — izvještaj razlika u stanju ploča/traka (ph_stock.csv vs Hub), nakon što Warehouse radi.

**I-09 Kontrola ponude protiv naloga** — "svaki materijal u nalogu ima stavku u ponudi" (nalaz ponuda 26-010-002929 bez rb 1–2) — može i prije Huba kao provjera u skillu krojna-ponuda.

**I-10 Lokalni AI (Ollama) na centralnom "Paneli AI serveru" u LAN-u** — tek kad modul `ai` (D-15) pokaže zadatak koji je čest, jednostavan i privatan (npr. sažimanje napomena iz proizvodnje/montaže, klasifikacija naloga, embeddinzi za RAG). Prije kupnje GPU-a: testirati kvalitetu na hrvatskom s 3–5 stvarnih zadataka i usporediti s Claudeom; mjeriti točnost, ne brzinu. Jedan server, ne Ollama po računalu.

**I-11 "Paneli Copilot"** — pitanja Hubu prirodnim jezikom ("naloge za KBC koji kasne i razlog"). LLM prevodi pitanje u strukturirani upit (imenovani upiti/filteri Huba), podatke dohvaća Hub deterministički, LLM samo formulira odgovor. Preduvjet: praćenje proizvodnje (I-06) i stabilan API naloga. Isti modul `ai`, zadatak `upit_u_filter`.

**I-12 Winstore automatski izvoz / API** — danas operater ručno izvozi XML inventara (11092026.XML); pitati Biesse ima li Winstore zakazani izvoz, bazu koju Hub smije čitati ili uvoz (rezervacija ploča za nalog, ulaz robe). Dok toga nema, Hub čita XML iz dogovorene mape jednom dnevno i prijavljuje razlike prema Pantheonu. (D-24, 05 §1.2)

**I-13 Optimizator PW-kvalitete** — Hubov optimizator je +4,0 % m² prema PW-u na 42 materijala (05 §5.6); poznati uzroci: PW smije zadnju traku "u daleki obrub" (jedan obrub umjesto dva), bolje kombinira širine traka i bira raspored koji ostavlja jedan veliki ostatak. Sljedeći koraci: lokalna pretraga po redoslijedu traka, kandidat-širine iz kombinacija do 4 komada, cilj = ≤ PW na benchmarku (`benchmark_optimizator.py`). Tek kad Hub preuzme obračun (kraj paralelnog rada, D-11). (D-16, D-26)

**I-14 Usluge CNC u ponudi iz CIX operacija** — za naloge iz Corpusa (D-29) Hub čita CIX (bušenja kom, utori m, kontura/krivolinija m) i predlaže stavke koje se danas unose ručno (USLUGA P-BUŠENJA, USLUGA REZANJA CNC, USLUGA NUT KANT — vidi HUMER 06 §5). Prvo validirati na 5 postojećih ponuda, tek onda automatski. (08 §3.1)

**I-15 Corpus → Hub izravno** — ako Corpus ima izvoz s više podataka od CPW-a (popis elemenata s korpusima i pozicijama, okov po korpusu), Hub ga čita umjesto samo CPW-a; temelj za praćenje montaže po korpusu kad dođe praćenje proizvodnje (D-03, I-06). (08 §7)

**I-16 Potvrda ponude gumbom u mailu** — kad ponude idu iz Huba (D-40), u mail se može dodati gumb „Potvrdi ponudu“ (jednokratni link) koji sam prebaci nalog u „Potvrđeno“ i pokrene provjeru skladišta (D-35). Ured danas potvrdu upisuje ručno (često telefonom), pa gumb ide tek kad se vidi koliko kupaca odgovara mailom. Uz to: automatski podsjetnik kupcu nakon N dana bez odgovora.

## I-20 Hub umjesto bNesta (Igorovo hipotetsko pitanje, 15. 9. 2026.)
Dva različita posla: (a) **slaganje dijelova na ploču** (pravokutni nesting, s godom, bez giljotinskog ograničenja) — realno u Hubu (maxrects / skyline heuristike + isti pristup „više kandidata, najbolji“ kao na pili), mjerilo su postojeći `.mno` rezultati (88–95 % popunjenosti); (b) **program za Rover** (bSolid po ploči: putanje alata, ulazi/izlazi, redoslijed, zajednički rezovi, držanje sitnih dijelova, vakuum zone, etikete, evidencija ostataka) — to je Biesseov CAM i tu Hub nema što tražiti bez dugog pilota na stroju. Vrijedan međukorak bez rizika: Hub sam složi nesting **za procjenu** (broj ploča za obračun i prijedloge spajanja umjesto neto m², usporedba s bNestom po .mno), a bNest i dalje generira program. Zamjena bNesta u proizvodnji ne prije nego Hub godinu dana radi pilu i obračun.

**I-17 Optimizator paralelno po jezgrama** — kandidati u `najbolje` (načini × varijante) su neovisni, pa se mogu računati u više procesa (`multiprocessing`, varijante kao imenovane funkcije umjesto lambda). Na PC-u s 4–8 jezgri najveći nalozi (I_01840, I_02025, SA_016431: 22–35 s) pali bi na 5–10 s bez ikakve promjene rezultata. Tek ako obračun na ekranu zasmeta; do tada ništa (22 §5).

**I-18 Hubova procjena nestinga** — Hub ne zamjenjuje bNest (Igorovo pitanje 15. 9.: nesting s pravim konturama i alatima je bNestov posao), ali bi za planiranje i za D-54 prijedloge spajanja mogao procijeniti broj ploča na nestingu iz pravokutnog slaganja s bNestovim razmakom (danas prijedlozi računaju iz neto m², D-65 „ostaje“). Kalibrirati na `.mno` rezultatima (dokument 19: HUMER 9 vs 11, 5 vs 6) prije nego uđe u prijedloge.
