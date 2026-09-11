# Paneli Production Hub — DECISIONS (odluke s obrazloženjem)

Jedna odluka = jedan redak-blok. Status: ODLUČENO / PREDLOŽENO (čeka Igora) / ODBAČENO. Novije odluke idu na kraj.

## 2026-09-10

**D-01 ODLUČENO — Faza 1 je AUDIT; puna aplikacija ne gradi se dok Igor ne odobri rezultate.**
Zašto: pouzdanost i ispravnost podataka važnije od brzine; prvo razumjeti formate i tok.

**D-02 ODLUČENO — Warehouse modul Huba je izvor istine za količine ploča, restlova i traka; Pantheon je financijska istina.**
Zašto: Pantheon nema restlove ni lokacije; ulaz robe ide u oba iz istog eSlog XML-a, mjesečno usklađenje s izvještajem razlika.

**D-03 ODLUČENO — Praćenje proizvodnje ostaje zaseban sustav (stari APEX), Hub ga ne gradi u fazi 1.**
Zašto: zahtjevno, radi sa starim programom. Hub ipak daje stabilan ID naloga i količine operacija kao izlaz koji čeka. Vidi P-02.

**D-04 ODLUČENO — Naziv projekta i aplikacije: "Paneli Production Hub" (mapa `Paneli_Production_Hub`).**

**D-05 ODLUČENO — Testni nalozi: jedan nalog = jedna mapa u `05_NALOZI_ZA_TEST` (predložak `_PREDLOZAK_NALOGA`); `Obrada kupaca` se više ne koristi za testove.**
Zašto: isti nalog kroz pilu i nesting na jednom mjestu = benchmark.

**D-06 ODLUČENO — Pantheon se čita preko izvoza (`IzvozPantheon_v2.ps1` → `ph_*.csv`), Hub nikad ne piše u Pantheon bazu; ulaz u Pantheon isključivo eSlog XML.**

**D-07 ODLUČENO — Iskoristiti postojeće: skill `krojna-ponuda` (obračun, eSlog, rukopis), `regal-traka` (trake, preko API-ja, bez refaktora), `primke-pantheon`. PanelWizard = referenca i benchmark, bez kopiranja koda.**

**D-08 ODLUČENO — Modul "znanje tvrtke" (RAG) gradi se kasnije KAO MODUL Huba s istim korisnicima i pravima, ne kao zasebna aplikacija. AnythingLLM samo kao brzi pilot (što ljudi pitaju, koji dokumenti daju dobre odgovore).**
Zašto: Instagram "$3.500 setup" je marketing; pravi posao je skupljanje i strukturiranje raspršenog znanja, slaba točka su katalozi s tablicama/cijenama. Vidi IDEJE_KASNIJE I-01.

**D-09 ODLUČENO (11.9.2026.) — Kriterij "audit je gotov": Igor pročitao 02/03/04, odgovorio na 12 pitanja iz 04 §5, i za 3 testna naloga (HUMER, BRATEK, ROMIC) cijeli lanac ulaz → nalog → CSV+CIX / CPW → CPO+MNO → obračun prošao "na papiru" (tablica benchmark_nalozi.csv se slaže s ponudom uz objašnjene razlike).**

**D-10 ODLUČENO (11.9.2026.) — Formati za pilu (OSI .cpo) i nesting (bNest CSV+CIX) su analizirani i parseri rade na svim testnim datotekama (02_formati). Preostali tehnički dokaz PRIJE koda Huba: (a) bNest učita CSV+CIX koje generira Hub-skripta, (b) OSI učita .cpo koji Hub prepiše iz postojećeg (bit-za-bit test), (c) PanelWizard učita Hubov CPW.**
Zašto: čitanje je dokazano, pisanje još nije — to je jedini pravi rizik formata.

**D-11 ODLUČENO (11.9.2026.) — Migracija: paralelni rad PanelWizard + Hub najmanje 1 mjesec; Hub prvo preuzima unos naloga i ponudu (PPNEST + ručni dio), PW ostaje optimizator pile; prekidač po materijalu/nalogu, ne "big bang".**

**D-12 ODLUČENO (11.9.2026.) — Zajednički temelji Huba i praćenja proizvodnje odlučuju se sada: šifrarnik kupaca (Pantheon acSubject), format broja naloga, korisnici, materijali s aliasima žive u Hubu i izlažu se API-jem; praćenje proizvodnje ih čita, ne duplicira.**

**D-13 ODLUČENO (11.9.2026.) — Git od prvog commita (`30_NOVI_PROGRAM` = repo) s PRIVATNIM repozitorijem na GitHubu (kod i izvan firme za slučaj kvara VM-a), automatski dnevni backup SQLite baze na VM-u + kopija na Z:, README + DECISIONS + IDEJE_KASNIJE kao obavezna dokumentacija.**

**D-14 ODLUČENO (11.9.2026.) — Dizajn ekrana: voditelj proizvodnje i Igor sudjeluju od prvog ekrana (unos naloga); ekrani se prvo crtaju (mockup) pa kodiraju.**

## 2026-09-11

**D-15 ODLUČENO (11.9.2026.) — AI sloj u Hubu: jedan modul `ai` s malim sučeljem (`ai.run(zadatak, ulaz)`), usmjeravanje po IMENU ZADATKA kroz konfiguraciju, ne po vrsti pružatelja. LLM nikad nije autoritet: izlaz uvijek `provjeri=True`, deterministički dio (obračun, optimizacija, skladište, CNC, exporti) ne zove `ai`. U fazi 1 pružatelji su samo `claude` i `none`; Ollama / lokalni GPU server se ne instalira dok ne postoji izmjeren use-case (kandidat: normalizacija naziva materijala — ali prvo alias-tablica).**
Zašto: Igorov prijedlog "AI Gateway" je ispravan u principu (Hub → sloj → Claude/lokalni/deterministički), ali kao zaseban servis i s kategorijama LOCAL_FAST/LOCAL_PRIVATE/CLOUD_REASONING bio bi overengineering za 10–15 naloga dnevno; isti učinak daje modul + konfiguracija. Rizici lokalnih modela: hrvatski jezik i čitanje rukopisa (vision) su slabi kod 7–8B modela — upravo tamo gdje Hubu AI najviše treba. Vidi IDEJE I-10, I-11.

**D-16 ODLUČENO (11.9.2026.) — Hub dugoročno dobiva VLASTITI optimizator pile "kao PanelWizard"; Biesseov optimizator uz OSI se ne razmatra. Razvija se kao black-box reverse engineering iz datoteka (CPW ulazi, CPO sheme, krojne PDF) — bez dekompilacije PW900.exe i bez kopiranja koda (D-07 ostaje). Mjera uspjeha = automatski benchmark protiv PW-ovih shema u CPO-u (broj ploča, iskorištenje, broj rezova, prihvaćanje operatera).**
Zašto: neovisnost o VB6 programu čiji je razvoj stao; Hub je dizajniran s optimizatorom kao zamjenjivim modulom (`optimizacija.engine`). Redoslijed: prvo CPO writer koji OSI prihvaća (round-trip test), pa rekonstrukcija PW-ovih shema iz CUT1 zapisa, pa vlastiti algoritam. Ne ulazi u fazu 1 "kralježnice", ide paralelno.

**D-17 ODLUČENO (11.9.2026., potvrđeno kroz D-09/D-10) — Redoslijed za vlastiti optimizator (dopuna D-16): (1) kalkulator količina za obračun koji reproducira PW-ove brojke (ploče, m² za naplatu, metri traka) za SVE naloge; (2) CPO writer + jednostavni giljotinski optimizator za ono što pila stvarno reže (MDF 3 mm, radne/zidne/compact ploče, restlovi, mali nalozi); (3) tek onda "PW-kvaliteta" na velikim serijama, ako ikad zatreba (te serije idu na nesting).**
Zašto: Igorova napomena 11.9. — PW danas služi prvenstveno za obračun, a ne za optimizaciju proizvodnje; velike serije reže bNest.
Napomena: korak (1) već postoji kao prototip u skillu krojna-ponuda (`scripts/optimizator.py`, kalibriran na PW, validiran 20/20 na ponudama; `upit2cpw.py` = CPW writer) — preseliti u Hub i mjeriti na 50 CPO-a.

**D-18 ODLUČENO (11.9.2026.) — Obračun ostaje kao dosad: količine za ponudu (m² za naplatu po pravilu korisnog ostatka, usluga rezanja, metri trake + kantiranje) računaju se "PW-metodom" za SVAKI nalog, bez obzira ide li na pilu ili nesting. Stvarna potrošnja s nestinga (.mno) se u Hubu evidentira, ali ne mijenja ponudu.**
Zašto: kontinuitet cijena prema kupcima; kalkulator obračuna (D-17 korak 1) mora reproducirati PW-ove brojke, a razlika naplaćeno/potrošeno postaje interni izvještaj (marža po nalogu).

**D-19 ODLUČENO (11.9.2026., pravilo iz prakse koje je Igor potvrdio) — Izbor načina optimizacije za obračun (PW-metoda, D-18): materijal S GODOM → probaju se samo uzdužni načini (Trake brzo, Trake standardno, Uzdužno brzo, Uzdužno standardno, Uzdužno na veliko); materijal BEZ GODA (npr. bijela iverica za korpuse) → uz njih i Poprečno brzo / Poprečno standardno / Poprečno na veliko. Valjan je rezultat s NAJMANJOM površinom za naplatu (m²). Hub to radi automatski (pokrene sve dopuštene načine, uzme minimum) i uz rezultat zapiše koji je način pobijedio.**
Zašto: tako operater radi danas u PW-u ručno (desni klik na žarulju, više pokušaja); pravilo "minimum m²" čini obračun determinističkim i usporedivim između PW-a i Huba (D-11). Postavke koje uz to vrijede: kerf 16 mm, rub 10 mm, korisni ostatak ≥ 400 × 400 mm i ≥ 1 m² (05 §5.3).

**D-20 ODLUČENO (11.9.2026.) — Pravilo za metre trake u ponudi: PW metri (= Σ stranica × 1,10, dakle 10 % otpada je VEĆ unutra) zaokruženi na cijeli metar naviše po traci/materijalu; usluga kantiranja = točno PW metri (kao ponuda BRATEK 26-010-003231). Skill `krojna-ponuda` danas množi PW metre s još 1,10 (dvostruki dodatak) — uskladiti s ovom odlukom.**
Zašto: u 06 (D-09) tri ponude imaju tri različita zaokruživanja (BRATEK naviše na metar; HUMER ručno +1…+19 %; skill ×1,10); Hub treba jedno pravilo da bi ponude bile usporedive (D-11) i da kupci plaćaju dosljedno. Igor je izabrao osnovno pravilo bez dodatnih postotaka; skill `krojna-ponuda` uskladiti (ukloniti drugi ×1,10).

**D-21 ODLUČENO (11.9.2026.) — Kerf: jedan kerf po nalogu za slaganje I obračun (zadano 16 mm kao PW "Podesi alat", korisnik može promijeniti); u CPO za pilu upisuje se fizički kerf 5,00, a na pilu ide ISTA shema kao za obračun (pila ima više zraka). Naplata = ono što je složeno.**

**D-22 ODLUČENO (11.9.2026.) — Brojevi programa za pilu: novi globalni niz Huba `HUB_xxxxx` (neovisan o operateru, bez sudara s PW-ovim I_/SA_ u paralelnom radu); operater se bilježi u Hubu, ne u imenu.**

**D-23 ODLUČENO (11.9.2026.) — Imena CIX datoteka za bNest: kratki globalni id iz brojača Huba (`H0001234`), jedinstven zauvijek (bNest pregazi istoimenu datoteku); čitljivost daje CSV (RN, naziv elementa, napomena).**

**D-24 ODLUČENO (11.9.2026.) — Identitet materijala: djelatnici u ponudi i nalogu rade s Pantheon identom/nazivom (IV000090, "IVERAL BIJELI NK W908 ST2 18 MM"); Hub u pozadini pri izradi nesting CSV-a upisuje Winstore `MaterialCode` (npr. `W908ST2-18`) u stupac SIFRA MAT — to je ključ po kojem bNest/Winstore nalazi ploču. Dimenzija ploče dolazi iz šifrarnika (Winstore kod `<dekor>-<deb>-<L>X<W>`), ne upisuje se po nalogu.**
Zašto: potvrđeno na PPNEST CSV-ovima — SIFRA MAT = Winstore MaterialCode (W908ST2-18, K2665AI-19, 27045OF-19, VSM06-18 … svi postoje u Winstore XML-u), a tipfeleri (`K5574IR_19` s donjom crtom, `K2739DC-19` kojeg nema) danas prolaze bez kontrole — alias-tablica Huba to zatvara.

**D-25 ODLUČENO (11.9.2026.) — Etikete na pili ostaju kako jesu: OSI printa iz podataka u CPO-u; Hub u fazi 1 samo pazi da CPO nosi iste podatke kao PW-ov (naziv elementa, nalog, rubovi).**

**D-26 ODLUČENO (11.9.2026.) — Optimizator za fazu 1: sadašnji Hubov optimizator (+4,0 % m² prema PW na benchmarku, 05 §5.6) je dovoljan za pilu i usporedbu; u paralelnom radu ponude idu iz PW brojki (D-11/D-18); PW-kvaliteta (D-16) razvija se paralelno i mjeri istim benchmarkom.**

**D-27 ODLUČENO (11.9.2026.) — Repozitorij: privatni repo u GitHub ORGANIZACIJI tvrtke (Igor otvara organizaciju i poziva); Hub radi na VM-u 192.168.5.201 (uz Knjigu i regal-traka); `30_NOVI_PROGRAM` = radna kopija repozitorija.**

**D-28 ODLUČENO (11.9.2026.) — AUDIT ODOBREN (D-01 ispunjen: D-09 i D-10 prošli, dokumenti 00–06). Faza 1 zatvorena 11.9.2026.; kreće faza 2: mockup prvih ekrana s voditeljem proizvodnje i Igorom (D-14), repozitorij (D-27), kralježnica aplikacije po planu iz 04 §4.**

Informacija (nije odluka): Winstore XML nastaje RUČNIM izvozom iz Winstorea (operater nestinga); Hub ga u fazi 1 čita iz dogovorene mape; automatski izvoz/API = pitanje za Biesse (IDEJE).

---
**Stanje 11.9.2026. (večer): sve odluke D-01 – D-28 su ODLUČENE; audit odobren, faza 2 počinje. Audit (faza 1) je zatvoren po kriteriju D-09 čim 3 naloga prođu lanac "na papiru"; preduvjet za kod = D-10 (tri testa pisanja formata) — **ISPUNJEN 11.9.2026.** (bNest ✓, PW ✓, OSI simulacija ✓; vidi 05 §5).**
