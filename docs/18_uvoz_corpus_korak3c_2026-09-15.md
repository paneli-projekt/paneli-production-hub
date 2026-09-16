# Paneli Production Hub — 18: Uvoz Corpusovog paketa (kralježnica korak 3c)

Stanje 15. 9. 2026. navečer. Treći ulaz u standardni nalog (D-30 ulaz B) sada radi na stvarnom paketu: tehnička priprema izveze projekt iz
Corpusa kao dosad, Hub tu mapu pročita, provjeri, otvori nalog vlastite proizvodnje i pošalje elemente na nesting i na pilu — bez ijedne
izmjene u Corpusovim datotekama (D-29: Corpus ostaje CAM autoritet). Time je zatvoren ostatak koraka 3 za ulaznu stranu; ostaju čitanje
rezultata natrag (.mno, sheme) i stvarno spajanje naloga.

## 1. Što se radi

    py -m hub.nalozi.uvoz_corpus --db hub.db --mapa "C:\Users\bolko\Desktop\CNC PROGRAMI\NESTING\TEST BUSENJE" --kupac HUMER [--suho]
    POST /api/nalozi/uvoz-corpus  {mapa, kupac_id | kupac_kratki, projekt, suho, tko}

Mapa je ona u koju Corpus izvozi (`…\NESTING\<PROJEKT>`) ili bilo koja mapa koja sadrži cijeli paket. Hub u njoj nađe:

| Što | Gdje | Uloga |
|---|---|---|
| CPW po materijalu | sestrinska mapa `<PROJEKT_S_PODVLAKAMA>\` (ili bilo gdje ispod zadane mape) | **svi** elementi naloga, i oni za pilu |
| CSV | `<PROJEKT>\<PROJEKT>.CSV` | koji elementi idu na **nesting** (D-55/2) |
| CIX | `<PROJEKT>\*.cix` | program po elementu; kopira se nepromijenjen |
| CIX za kant | `<PROJEKT>\HORIZONTALNO_BUSENJE\*.cix` (+ `.wmf`) | drugi program elementa (`PROGRAM2`, D-55/3); kopira se u istoimenu podmapu |

`--suho` samo pročita i provjeri paket (brojke, greške, upozorenja) i ne otvara nalog — to je ono što će ekran pokazati prije „Uvezi“.

## 2. Što Hub provjeri prije nego išta upiše

Greška zaustavlja uvoz **prije prvog upisa** (nalog se ne otvara, registar imena ostaje netaknut):

- element s programom nema CIX datoteku u paketu; element s `PROGRAM2` nema drugi CIX
- mjere u CIX-u (`LPX × LPY`) nisu mjere elementa iz CPW-a (bilo koji smjer, tolerancija 0,6 mm)
- CSV redak nema odgovarajući element u CPW-u (po CIX imenu, inače po šifri materijala + mjerama + cjelini + poziciji)
- element ima CNC obradu u CIX-u (bušenje, utor, krivolinija), a nije u CSV listi — išao bi na pilu s bušenjem (D-29)
- Corpusovo ime CIX-a već pripada **drugom, živom** elementu u Hubu (D-23, D-55) — preimenovati u Corpusu
- više CSV datoteka u paketu, nijedan CPW, prazan CPW, mapa ne postoji

Upozorenje ne zaustavlja, nego se vrati uz nalog: CIX datoteke koje nitko ne spominje (u uzorku: dva leđa MDF-a — Corpus im napravi
konturu iako idu na pilu), količina u CSV-u drukčija od CPW-a, CIX za kant izvan podmape, materijal čiji dio elemenata nije u CSV-u,
nema CSV-a (sve ide na pilu), CPW koji nije Corpusov (nema stupce cjelina / CIX).

## 3. Što nastane

- **Nalog** `KUPAC_PROJEKT_BROJ` s `vrsta = vlastita_proizvodnja`, `izvor = corpus`, `corpus_projekt = <ime iz Corpusa>` (D-55/4).
  Kupca projekta tehnička priprema ne zna, pa se zadaje pri uvozu (`--kupac` / `kupac_id`) ili ured kasnije promijeni.
- **Materijali** kroz šifrarnik po Winstore šifri iz CPW-a (`W908ST2-18`, `IV000054-3` — D-57), s **putem**: ima elemenata u CSV-u → `nesting`,
  inače → `pila`. Upisuje se u `put` i `put_prijedlog` — Corpus je put već odredio, voditelj ga smije promijeniti (D-34).
- **Elementi** s cjelinom i pozicijom (`EL_BUSENJE` / `L_BOK` — ID iz Corpusa koji mora ostati na etiketi, D-55/5), oba programa,
  `cix_ime` + `cix_izvor = corpus`, i **`obrada`** pročitana iz CIX-a: `22 bus, 2 utora` / `4 bus, 12 bus kant` / `kontura` / `krivolinija`.
  Polica bez programa a u CSV-u dobiva Corpusov CIX iz CSV stupca (bNest ga treba za konturu). Leđa MDF nemaju CIX i idu na pilu.
- **Registar imena** (D-23): svako Corpusovo ime (i ono za kant) upisano uz element, izvor `corpus`.
- **Dokumenti** naloga: CPW-ovi (hash — isti se ne uvozi dvaput), CSV i svaki CIX s **izvornom putanjom** — odatle ih izvoz kopira.

## 4. Izvoz za Corpusov nalog

`export_nesting` za element s `cix_izvor = corpus` **ne generira CIX nego kopira izvorni** (bajt po bajt; uz CIX za kant ide i `.wmf`),
u `<NALOG>\NESTING\` odnosno `<NALOG>\NESTING\HORIZONTALNO_BUSENJE\` — točno kako operater nestinga već ima od Corpusa. Prvo se provjeri da
svi izvorni CIX-ovi još postoje na disku, pa se tek onda kopira — nestala datoteka daje poruku, ne pola paketa. Elementi bez Corpusovog
CIX-a (ako ih voditelj pošalje na nesting) dobivaju Hubov CIX i ime kao dosad. `export_pila` uzima materijale s `put = pila` (leđa).
Ponovni izvoz vraća ista imena (registar).

**Novo pravilo u registru (D-66):** Corpusovo ime čiji je element obrisan (probni ili krivo otvoren nalog) isti Corpus projekt smije
ponovno preuzeti — datoteka je ista pa pregaženja nema. Hubova (`H…`) i PPNEST-ova imena se nikad ne vraćaju (D-23). Bez toga bi svaki
ponovni uvoz istog paketa (i svaka provjera na testnim nalozima) stao na „ime već zauzeto“.

## 5. Mjera uspjeha — stvarni uzorak TEST BUSENJE (dokument 14)

| | Corpus / PW / bNest (14. 9.) | Hub (15. 9.) |
|---|---|---|
| Elementi / komadi | 15 / 15 u 3 CPW-a | **15 / 15**, 3 materijala, svi sigurni po šifri |
| Nesting | CSV 13 elemenata, 2 bNest projekta | **13 elemenata, 2 paketa** (IV BIJELI NK 18 → 10 el, IV SIVI TAMNI PE 19 → 3 el) |
| CIX | 15 + 4 u `HORIZONTALNO_BUSENJE` | **13 + 4 = 17** kopirano (2 leđa nemaju program — ostaju u paketu, ne prenose se); `cmp` = identično, `.wmf` uz kant |
| Pila | `S0_06374` MDF BIJELI 4 MM, 2 leđa | **HUB_00001**, 2 el, 1 ploča, put `pila` |
| Obrada iz CIX-a | 2 el. bušenje, 2 utor, 1 krivolinija (NALOG.txt) | L/D_BOK: `22 bus, 2 utora` (×4, dva s `krivolinija`); POD/STROP: `4 bus, 12 bus kant`; FR: `8 bus`; police/leđa: `kontura` |
| Za potvrdu | — | 1 traka (`SIVA_TAMNA-1/22`: dva kandidata, D-58) — jedna potvrda ureda, pa alias |

Hubov CSV za bNest nosi Corpusove stupce (cjelina, pozicija, PROGRAM1, PROGRAM2, CIX) u 28-stupčanom profilu koji bNest već čita (D-55/1).

## 6. Provjera i testovi

- `hub.nalozi.provjera` sada uvozi i `_CORPUS_UZORAK` (mapa `01_ulaz_corpus`) kao jedan nalog — ispis pokazuje `nesting 13 el, pila 2 el, CIX 17`
  i upozorenja paketa; probni nalozi se brišu s `--obrisi` kao dosad, a imena se odvezuju.
- `tests/test_uvoz_corpus.py` (6 testova, sintetički paket bez stvarnih podataka): čitač CIX-a, Corpusovi stupci CPW-a, uvoz + izvoz na nesting
  (kopija oba CIX-a) + pila, sve greške iz §2 ne otvaraju nalog, brisanje naloga i ponovni uvoz, API. **94 testa prolaze** sa stvarnim podacima.
- Novi modul `hub/formati/cix_citaj.py` — čita bSolid CIX (MAINDATA + makroi `BG` po strani, `CUT_X/Y`, `GEO`/`LINE_EP`/`ARC_*`, `ROUTG`) i vraća
  mjere, broj bušenja vertikalno / u kant, utore, krivoliniju, `ima_obradu` i kratak opis. Isti čitač može kasnije služiti i za obračun CNC obrade.

## 7. Što ostaje (korak 3, ostatak)

(a) čitanje rezultata natrag — CPO sheme → PNG, stvarna potrošnja iz `.mno` i razdioba po nalozima (D-38);
(b) stvarno spajanje malih naloga (D-54/B) — jedan CSV+CIX paket, oznaka naloga na elementu, razdioba potrošnje.
Za Corpus put dodatno: završni korak toka za vlastitu proizvodnju (ponuda → korekcija → interna izdatnica, D-56) ide u korak 4 (obračun).
