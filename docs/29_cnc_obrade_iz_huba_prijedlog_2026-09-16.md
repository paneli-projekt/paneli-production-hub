# Paneli Production Hub — 29: Standardne CNC obrade iz Huba (prijedlog, D-84 PREDLOŽENO)

Igorova ideja 16. 9. 2026. navečer: kupci koji naručuju OBRAĐENI materijal (rupe za šarke, nut za leđa / lesonit, raster rupa, lijepljenje…) danas
dobiju napomenu na naljepnici, a operater na Roveru program radi RUČNO na stroju. Hub bi mogao te jednostavne programe sam napraviti (CIX) i
operater bi ih pozivao bar kodom s naljepnice — kao što danas radi za Corpusove programe.

## 1. Gdje to pripada

Ne u optimizator (on slaže ploče), nego u **element naloga**: uz mjere, količinu i trake element dobiva **strukturiranu obradu** (vrsta + parametri)
umjesto slobodnog teksta u napomeni. Iz nje Hub izvodi troje koje danas ide odvojeno i ručno: (1) **CIX program** za Rover / nesting, (2) **stavku
usluge** u ponudi (obračun već čita napomenu: `fi35` → US000149, `NUT/FALC` → US000016, `UREZ GOLA` → US002075 — D-69), (3) **tekst na etiketi**
i **bar kod programa** (D-38 / D-78).

## 2. Što već postoji u Hubu

* Hub već PIŠE CIX (`hub/formati/nalog_io.cix_text`: `MAINDATA` LPX/LPY/LPZ + `GEO` / `ROUTG` kontura) i bNest ga čita (HUMER 89 CIX-ova, dokument 15).
* Hub već ČITA Corpusove CIX-ove s obradom (`hub/formati/cix_citaj.py`): vertikalno bušenje `BG` (SIDE=0, X, Y, DIA, DP), horizontalno bušenje
  u kant `BG` (SIDE=1/3, drugi CIX u `HORIZONTALNO_BUSENJE`), utor `CUT_X` / `CUT_Y` (X, Y, DP, L, `TNM="LAMA120"`), krivolinija. **Gramatika
  makroa je poznata iz stvarnog uzorka** (`_CORPUS_UZORAK\TEST BUSENJE`: 25 bušenja, 2 utora) — Hub bi pisao ISTE makroe, pa bSolid ne treba ništa novo.
* Registar imena programa (`cix_registar`, `H0000123`, D-23/D-60), put „pila pa Rover na izrezanom komadu“ već postoji za fronte iz niza i komade iz majke
  (`NESTING\NIZ\`, `NESTING\MAJKA\`, D-81) — isti put za komade s obradom rezane na pili.
* Naljepnica pile (OSI, predložak `PANELI BAR VECA NALJEPNICA`) **već ima dva bar koda** (polja iz CPO-a); bSolid naljepnica nosi naziv programa. Znači
  mehanizam „skeniraj → Rover učita program“ postoji, treba samo u polje koje bar kod čita upisati Hubovo ime CIX-a (`cpo_rw` piše PRT1/PRT4 polja; za
  Corpus se u ORD2 već piše oznaka elementa, D-65/7).

## 3. Prijedlog (D-84)

**Katalog standardnih obrada** (postavke Huba, ured ih ne tipka svaki put), svaka s parametrima i s uslugom za ponudu:

| Obrada | Parametri (zadano → potvrditi s Igorom) | CIX | Usluga |
|---|---|---|---|
| Šarke (lonac fi 35) | broj šarki, strana, razmak od ruba lonca (npr. 22,5 mm), položaj od gornjeg / donjeg ruba (npr. 100 mm), dubina 13 | `BG` DIA 35 DP 13 (+ 2 × fi 8 za pločicu?) | US000149 × kom |
| Nut za leđa | strana(e), širina 4 mm (MDF 3 mm, D-57), dubina, udaljenost od ruba (npr. 10 mm) | `CUT_X` / `CUT_Y` (LAMA) | US000016 × m |
| Raster rupa (System 32) | fi 5, dubina 13, korak 32, udaljenost od prednjeg / stražnjeg ruba (37), od gore / dolje | `BG` × n | ? (po rupi ili po komadu) |
| Rupe za ladice / klizače, spojnice (fi 8, fi 15 ekscentar) | po tipu okova | `BG`, horizontalno `BG` SIDE 1/3 u drugom CIX-u | ? |
| LED urez | duljina, širina, dubina | `CUT_X` / `ROUTG` | US002075 × m |

**Tok:** ured uz element klikne obradu i upiše parametre (ekran 2, blok „Obrada“ na klik — D-14) → Hub crta skicu komada s rupama (kao skica niza) da ured
i kupac vide ISTO → obračun sam doda uslugu → izvoz: element s obradom ide na **nesting** (CIX u paketu, bNest ga izbuši u nestingu — kao Corpus) ili,
kad materijal ide na **pilu**, CIX u `NESTING\CNC\` + ime programa u polje bar koda na CPO-u → operater skenira naljepnicu na Roveru. Program i skica idu
u dokumente naloga; ime iz registra, nikad se ne ponavlja.

**Redoslijed ugradnje (prijedlog):** (1) katalog + parametri uz element + CIX s `BG` / `CUT_X` (vertikalno) + skica + usluga — 1–2 dana, bez novih
tablica osim `element.obrada_json` koji već postoji; (2) bar kod na naljepnici pile (koje polje čita LEDITOR); (3) horizontalno bušenje (drugi CIX)
i spojnice; (4) rukopis / Excel kupca → prepoznavanje obrade iz teksta („2 šarke lijevo“) kao prijedlog za potvrdu (D-15: `provjeri=True`).

## 4. Pitanja za Igora

1. Popis standardnih obrada koje kupci stvarno naručuju i njihovi ZADANI parametri (šarka: lonac, razmak od ruba, položaji; nut: širina / dubina / udaljenost;
   raster: 32 / 37 / fi 5?). Najbolje: fotografija ili skica jednog stvarnog komada svake vrste + kako je naplaćen (ident usluge).
2. Koje polje CPO-a puni bar kod na naljepnici pile (LEDITOR predložak `PANELI BAR VECA NALJEPNICA`, dva bar koda) — i koje polje danas nosi Corpusov program.
3. Ide li komad s obradom radije na nesting (bNest izbuši u istom prolazu) ili se i dalje reže na pili pa nosi na Rover — ili oboje, po veličini naloga (D-29 danas kaže: obrada → uvijek nesting).
4. Prioritet: prije web ekrana, ili zajedno s ekranom 2 (blok „Obrada“ ionako treba nacrtati)?
