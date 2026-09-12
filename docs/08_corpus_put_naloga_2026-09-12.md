# Paneli Production Hub — 08: treći put naloga — Corpus (tehnička priprema) — analiza i prijedlog uklapanja

Stanje 12. 9. 2026. Povod: Igorova napomena da audit nije obuhvatio put naloga iz **Corpusa**. Ovo je analiza iz onoga što već imamo u
datotekama + prijedlog; **uzorci Corpus paketa još ne postoje u mapi** (popis što treba u §6). Odluke iz ovoga su PREDLOŽENE (D-29, D-30), ne odlučene.

## 1. Što je novo

Do sada je Hub imao dva ulaza: (A) kupac šalje CPW iz PPW-a / Excel / rukopis → ured prekucava u PPNEST → CSV+CIX za nesting, CPW za PW → pila/nesting →
obračun → ponuda. Treći ulaz (B): **tehnička priprema radi projekt za vlastitu proizvodnju (sastavljanje, montaža) u Corpusu**, a Corpus sam generira:
- **CPW po materijalu** → učitavaju se u PanelWizard radi obračuna i otvaranja naloga proizvodnji (program za OSI raskrajač);
- **CSV + CIX za nesting** → ne nose samo konturu za rezanje, nego i **bušenje i dodatnu obradu (utori, krivolinije…)**.

Razlika prema ulazu A je bitna: kod A element je pravokutnik s 4 ruba i napomenom, a CNC obradu operater programira sam u bSolidu po napomeni;
kod B je **CAM već napravljen u Corpusu** — Hub ga ne smije ni ponavljati ni „popravljati“.

## 2. Što o Corpusu već znamo iz datoteka (bez uzorka)

1. **CPW format JE Corpusov.** Svaki CPW koji imamo počinje s `FORMAT;CORPUS->PW;002600;` — klijentska aplikacija PPW 5.2 i PPNEST samo oponašaju
   Corpusov izvoz za PanelWizard (02 §3.1). Posljedica: Hubov čitač CPW-a (`nalog_io.read_cpw`, test D-10 prošao za obje varijante zaglavlja) po svemu
   sudeći čita i Corpusov CPW bez promjene. Za potvrdu treba jedan pravi Corpus CPW (naziv elementa, oznake rubova, naziv materijala).
2. **bNest već prima Corpusove artikle.** Snimka `04_STROJEVI\NESTING\screenshots\CSV UCITANI.png` (10. 9., 11:56) prikazuje bNest projekt `_PPEXPORT(6)`
   s artiklima `1-L_BOK-14451FF1A2C`, `2-D_BOK-…`, `3-POD-…`, `4-STROP-…`, opis `EL1-L_BOK`, materijal **`W908ST2-18`**, 800×560×18 — to je
   Corpusovo imenovanje (element = korpus EL1, pozicije L_BOK / D_BOK / POD / STROP, jedinstveni sufiks). Dakle: (a) Corpusov izvoz **već nosi Winstore
   kod materijala** (ili ga je operater mapirao u bNest bazi materijala), (b) bNest ima uvozni profil koji čita taj CSV. Treba provjeriti je li to isti
   28-stupčani profil kao za PPNEST (vjerojatno — PPNEST je 2023. pisan da proizvede ono što je bNest već uvozio iz Corpusa) ili drugi profil.
3. **Model podataka ovo već djelomično predviđa** (04 §2): `element.cjelina`, `element.pozicija_u_korpusu`, `element.izvor`, `element.obrada`,
   `dokument.vrsta`. Fali samo izvor `corpus` i oznaka „CIX generirao Corpus“.

## 3. Analiza — što Hub za Corpus nalog treba, a što ne smije

| Korak | Danas (Corpus put) | Hub — prijedlog | Zašto |
|---|---|---|---|
| Ulaz | Corpus izvozi CPW (po materijalu) + CSV+CIX u mapu izvoza | Hub **uvozi Corpus paket** iz mape: CPW → elementi/rubovi/materijali; CSV+CIX → priloženi dokumenti + podaci o obradi | isti standardni nalog kao za kupce, bez prekucavanja |
| Obračun | CPW → PW → krojna PDF → količine u Pantheon | isto kao ulaz A: PW-metoda (D-18), trake D-20; PW-brojke u paralelnom radu (D-11) | jedno pravilo za sve naloge |
| Nesting | operater učita Corpusov CSV+CIX u bNest | Hub **ne generira CIX** — provjeri paket, registrira imena, kopira u mapu bNesta (pass-through) | CAM je u Corpusu (bušenje, utori, krivolinije); Hubov CIX je samo pravokutnik |
| Pila | PW iz CPW-a → CPO → OSI | Hub iz CPW-a → CPO `HUB_xxxxx` (kao ulaz A), **samo za elemente bez CNC obrade** | element s bušenjem/konturom ne može na pilu |
| Etikete | OSI (pila) / bSolid (nesting) iz Corpusovih podataka | nepromijenjeno (D-25) | — |
| Rezultat | .mno u bNest projektu | isti watcher kao za ulaz A → potrošnja, restlovi | — |

Ključno načelo: **Corpus ostaje autoritet za geometriju i obradu (CAM), Hub je autoritet za nalog, put, skladište i obračun.** Hub s Corpusovim
CIX-om radi samo tri stvari: **provjeri** (paket konzistentan), **registrira** (jedinstvena imena, veza element ↔ CIX) i **proslijedi**.

### 3.1 Što Hub može pročitati iz Corpusovog CIX-a (bez da ga mijenja)
CIX je tekstualni format (isti kao naš, 05 §2): zaglavlje `LPX/LPY/LPZ` (dimenzije, debljina) + makroi. Corpusov CIX uz `ROUTG` (kontura) sadrži
vjerojatno `BH`/`BV` (bušenje), `GROOVE`/`ROUT` (utori), lukove u konturi (krivolinija). Hub iz toga deterministički izvuče:
- `ima_obradu` (da/ne) → **put = nesting/Rover obavezno** (pravilo iz odgovora 8 dobiva iznimku: obrada pobjeđuje veličinu);
- brojače: `busenja`, `utori_m`, `kontura_m`, `krivolinija` (da/ne) → prikaz u nalogu i kasnije **usluge CNC u ponudi iz stvarnih operacija**
  (danas ručno: „USLUGA P-BUŠENJA 5/8 MM 569 KOM“, „USLUGA REZANJA CNC 1,98 M“, „USLUGA NUT KANT 5,38 M“ — vidi HUMER 06 §5) → IDEJE I-14;
- kontrolu: `LPX×LPY×LPZ` i količina iz CSV-a = element iz CPW-a (isti paket, ista mjera).

### 3.2 Imena CIX datoteka (D-23) kod Corpusa
Corpusova imena (`1-L_BOK-14451FF1A2C.cix`) imaju jedinstveni sufiks po elementu projekta, pa je rizik pregazivanja u bNestu manji nego kod
PPNEST-ovih `ddMMyy_HHmmss`. Hub svejedno vodi **registar imena**: Corpusovo ime ostaje (operater i etikete ga poznaju), a preimenuje se **samo pri
sudaru** — i tada Hub prepiše i stupac CIX u CSV-u, da paket ostane cjelina. Ne uvoditi `H0001234` imena za Corpus naloge (nepotrebno, a ruši vezu
s Corpusovim projektom).

### 3.3 Materijali i šifrarnik
Corpus ima vlastitu bazu materijala (naziv u CPW-u, kod u CSV-u). To je 4. način imenovanja (uz Pantheon, PW/PPNEST, Winstore) — rješava ga **ista
alias-tablica** (D-24): Corpus naziv → Hub materijal → Winstore kod + Pantheon ident. Ako Corpusov CSV već nosi Winstore kod (snimka to sugerira), mapiranje
je trivijalno; ako nosi Corpusov naziv, alias se upiše jednom po materijalu.

## 4. Prijedlog uklapanja u koncept (kratko)

1. **Tri ulaza, jedan standardni nalog.** `nalog.izvor` = `kupac_ppw | kupac_excel | kupac_rukopis | corpus | rucno`; `nalog.vrsta` =
   `usluga` (rezanje/kantiranje za kupca) | `vlastita_proizvodnja` (projekt tehničke pripreme); `nalog.corpus_projekt` (ime/ID projekta, mapa izvoza).
2. **Element iz Corpusa** nosi `izvor='corpus'`, `naziv` i `cjelina/pozicija` iz Corpusa (EL1 · L_BOK), `cix_ime` = Corpusova datoteka,
   `cix_izvor='corpus'`, `obrada_json` iz CIX-a (§3.1). Rubovi i trake iz CPW-a kao i danas.
3. **Modul `import.corpus`**: prepozna paket u mapi (CPW-ovi + CSV + CIX istog projekta), učita, provjeri (svaki CPW element ima CIX; SIFRA MAT
   poznat; LPZ = debljina; imena jedinstvena), predloži put po materijalu **i po elementu** (obrada → nesting), pokaže sažetak (materijali, elementi,
   bušenja, utori, krivolinije) i traži potvrdu. Ništa se ne prekucava.
4. **Export**: nesting = pass-through Corpusovih CSV+CIX u `C:\PPNESTING\<kupac>\NESTING\` (ili mapu koju operater koristi za `_PPEXPORT`) uz
   registraciju; pila = Hubov CPO iz CPW-a samo za elemente bez obrade (MDF 3 mm, leđa, radne ploče, ostalo bez CNC-a); PW CPW = original iz Corpusa
   (paralelni rad, D-11) — Hub ga ne mora ponovno pisati.
5. **Obračun**: isti kalkulator (PW-metoda). Otvoreno je **kamo brojke idu** za vlastitu proizvodnju: ponuda/račun kupcu projekta (kao danas iz PW-a?)
   ili interni radni nalog / izdatnica materijala u Pantheonu — pitanje 4 u §6. Kasnije (I-14): usluge CNC iz CIX operacija umjesto ručnog unosa.
6. **Mockup v0.2** (nakon uzorka): na ekranu 2 kartica uvoza „Corpus paket (CPW + CSV + CIX)“ i stupac „Obrada“ u tablici elemenata (bušenje / utor /
   kontura); na ekranu 3 u stupcu Export „CIX: Corpus (proslijeđeno), 12 bušenja · 2 utora · 1 krivolinija“ umjesto „Generiraj CSV+CIX“; na ekranu 1
   filtar `vrsta` (usluga / vlastita proizvodnja).
7. **PPNEST** ostaje zamijenjen samo za ulaz A (kupci). Za ulaz B Hub zamjenjuje PanelWizard (obračun + CPO) i ručno prenošenje datoteka, ne Corpus.

## 5. Rizici i što treba provjeriti na uzorku

- **CSV profil**: ako Corpusov CSV nema PPNEST-ovih 28 stupaca, Hub ga ne mora pretvarati — prosljeđuje ga kakav jest, ali onda mora znati koji
  stupac je CIX ime, materijal i količina (za provjere). Ako bNest ima dva uvozna profila, Hub to bilježi u `dokument.vrsta`.
- **CPW iz Corpusa vs. CIX iz Corpusa**: jesu li količine i redoslijed elemenata usklađeni (jedan CIX po elementu s `kom` u CSV-u, ili po komadu)?
- **Elementi s obradom na pili**: ima li slučajeva gdje Corpus element ide na pilu pa na Rover (obrada nakon rezanja)? Ako da, put „pila + CNC“ je
  treća opcija, ne iznimka.
- **Nazivi bez dijakritika**: Corpusovi nazivi (`L_BOK`, `POD`) su već bez Š/Č/Ć; napomene možda nisu — isto pravilo kao za PW (05 §5.2).
- **Kodiranje i separator** Corpusovog CSV-a (UTF-8 / cp1250, `;`) — PPNEST piše UTF-8 bez BOM-a.

## 6. Što trebam od Igora / tehničke pripreme

**Uzorak (jedan projekt, po mogućnosti s bušenjem, utorom i jednom krivolinijom)** u `05_NALOZI_ZA_TEST\_<IME>_CORPUS\` po predlošku naloga:
`01_ulaz_kupca` = Corpusov izvoz (svi CPW + CSV + svi CIX, točno kako izlaze iz Corpusa, s imenom mape izvoza), `02_panelwizard` = što je PW napravio od
tih CPW-ova (PDF krojne, CPO), `04_export_nesting` = bNest rezultat (.mno, projekt), `05_pantheon` = dokument koji je iz toga nastao (ponuda / račun /
radni nalog). Uz to snimka ekrana Corpusovih postavki izvoza (koji izvoz daje CSV+CIX, koji CPW) i, ako postoji, snimka bNest uvoznog profila.

**Pitanja (odgovori idu u DECISIONS):**
1. Corpus: verzija i modul za CNC izvoz; nosi li Corpusov CSV Winstore kod materijala ili Corpusov naziv?
2. Je li bNest uvozni profil isti za PPNEST i Corpus CSV (jedan profil) ili su dva?
3. Tko radi u Corpusu (imena, računala) i u koju mapu izvozi (`_PPEXPORT`?); ide li paket operateru nestinga preko mreže ili USB-a?
4. Obračun za projekte vlastite proizvodnje: PW brojke idu u ponudu/račun kupcu projekta ili u interni radni nalog/izdatnicu? Radi li Pantheon radni nalog
   tehnička priprema ili ured?
5. Idu li Corpusovi elementi ikad na pilu pa na Rover (obrada nakon rezanja), ili sve s obradom ide isključivo nestingom?
6. Koriste li se Corpusove etikete (za montažu) uz bSolid etikete, i treba li ID elementa iz Corpusa ostati na etiketi (veza s montažom)?
7. Radi li tehnička priprema u Corpusu i uslužne naloge za kupce (kad kupac pošalje nacrt), ili je Corpus samo za vlastitu proizvodnju?

## 7. Prijedlog odluka i ideja

- **D-29 PREDLOŽENO** — Corpus ostaje CAM autoritet: za naloge iz Corpusa Hub ne generira CIX, nego uvozi paket (CPW + CSV + CIX), provjerava ga,
  registrira imena i prosljeđuje bNestu; Hub generira samo CPO za pilu (elementi bez obrade) i obračun. Element s CNC obradom uvijek ide na nesting.
- **D-30 PREDLOŽENO** — Tri ulaza u isti standardni nalog: kupac (PPW CPW / Excel / rukopis, Hub zamjenjuje PPNEST + PW), Corpus (Hub zamjenjuje PW i
  ručni prijenos datoteka), ručni unos. `nalog.vrsta` razlikuje uslugu i vlastitu proizvodnju; obračun je isti, odredište brojki ovisi o vrsti (pitanje 4).
- **I-14** — Usluge CNC u ponudi iz CIX operacija (bušenja kom, utori m, kontura m) umjesto ručnog unosa; validirati na 5 postojećih ponuda.
- **I-15** — Corpus → Hub izravno (Corpusov popis elemenata s korpusima/pozicijama, ako postoji izvoz s više podataka od CPW-a) — temelj za praćenje
  montaže po korpusu kad dođe praćenje proizvodnje (D-03, I-06).
