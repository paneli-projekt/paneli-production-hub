# Paneli Production Hub — 20: Stvarno spajanje malih naloga u jedan nesting posao (kralježnica korak 3e)

Stanje 15. 9. 2026. kasno navečer. Time je **korak 3 kralježnice zatvoren**: Hub šalje na sve strojeve (CSV + CIX, CPW, CPO), prima
Corpusov paket, crta sheme, knjiži rezultat nestinga — i sada spaja više malih naloga u jedan nesting posao, što je bio zadnji dio D-54.

## 1. Što se radi

    py -m hub.nalozi.spajanje --db hub.db                                 (prijedlozi — kao dosad, D-54/A)
    py -m hub.nalozi.spajanje --db hub.db --izvezi 40,17,22 --mapa C:\PPNESTING [--suho] [--forsiraj]
    POST /api/spajanje/izvezi {nm_ids, mapa, stil, suho, forsiraj, tko}      GET /api/spajanje/poslovi

Voditelj iz prijedloga odabere naloge (`stavke[].nm_id` = materijal naloga) i Hub napravi **jedan** paket
`<mapa>\SPOJ_<MATERIJAL>_<ddmmyy_HHmmss>\NESTING\` s jednim CSV-om i CIX-om po elementu — operater nestinga ga učita kao svaki drugi.
U CSV-u je `RN = naziv naloga` **po elementu**, pa etiketa iz bSolida (koja RN već nosi, 14. 9.) i `.mno` (`CUSTOM_DESCR_2`) znaju čiji je
koji dio. Imena CIX-a su iz registra (D-23) — ponovni izvoz istih naloga daje ista imena; Corpusovi CIX-ovi se kopiraju (D-66).

Pravila: samo nalozi **istog materijala** (ident), svi potvrđeni i bez stavki za potvrdu, u statusu za stroj (D-65/1; `--forsiraj` za probe),
ne deblji od 26 mm, ne vezani na restl; isti nalog ne može dvaput. Greška zaustavlja prije ijednog upisa; `--suho` pokaže paket bez pisanja.

## 2. Što se zabilježi

Shema v9: `spojeni_posao` (naziv, materijal, mapa, CSV, brojke, tko, kada, `mno_dokument_id` kad se rezultat vrati) + `spojeni_posao_stavka`
po nalogu (elemenata, komada, m²). Svaki nalog: materijal dobije `put = nesting` i `status_opt = spojeno:<POSAO>`, dokumenti (CSV + svoji
CIX-ovi), događaj „izvoz na nesting u spojenom poslu SPOJ_… (3 naloga, 26 el)“. **Obračun se ne mijenja** — svaki nalog ostaje svoj
(D-18); spajanje je samo način rezanja.

Kad se vrati `.mno` (dokument 19), bNest projekt nosi ime našeg CSV-a, pa Hub posao označi gotovim, razdijeli ploče po nalozima po kvadraturi
(D-38) i u `GET /api/nalog/{id}/rezultati` uz materijal pokaže `spojeni_posao` (naziv, je li rezultat stigao).

## 3. Mjera uspjeha — stvarni testni nalozi

Na 9 testnih naloga Hub daje 11 prijedloga; prvi je **IV BIJELI NK 16 (IV000002): 7 naloga, zasebno 7 ploča → spojeno 4**. Od njih tri bez
otvorenih potvrda spojena su u `SPOJ_IV_BIJELI_NK_16_150926_110009`: HUMER_OMIS (10 el / 28 kom / 4,60 m²) + BOGDANIC_IVA ×2 (8 el / 18 kom /
2,83 m² svaki) = 26 elemenata, 64 komada, 10,26 m², 26 CIX, jedan CSV u kojem svaki redak nosi svoj nalog.

## 4. Testovi

`tests/test_spajanje_b.py`: greške (jedan nalog, isti dvaput, nepotvrđen), suho, izvoz (CSV s RN po elementu, CIX, posao + stavke, put i
status materijala, dokumenti, događaj), ponovni izvoz s istim imenima, `.mno` natrag → razdioba i posao gotov, brisanje probnog naloga,
API. **100 testova prolazi** sa stvarnim podacima.

## 5. Korak 3 — zatvoren. Sljedeće: korak 4

Obračun + ponuda iz Huba (D-18/D-19/D-20/D-40): kalkulator PW-metodom iz `hub/optimizacija/obracun.py`, cjenik iz `pantheon_ident`, rabat s
naloga, usluge (kantiranje, CNC obrada — sada čitljiva iz CIX-a, dokument 18), verzije ponude, eSlog XML (skill krojna-ponuda), usporedba s 40
ponuda iz benchmarka; za vlastitu proizvodnju završni korak ponuda → korekcija po stvarnom stanju (`.mno`, dokument 19) → interna izdatnica (D-56).
