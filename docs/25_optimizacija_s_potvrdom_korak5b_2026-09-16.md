# Paneli Production Hub — 25: Optimizacija s potvrdom (korak 5b, prvi dio — D-75 / D-77)

Stanje 16. 9. 2026. Igorovo pravilo: **ponuda i izvoz na pilu uvijek koriste isto slaganje**, jer se iz tog dokumenta naručuje materijal.
Hub predlaže, čovjek provjeri i potvrdi. Drugi dio koraka 5b (krojni nacrt PDF u PW rasporedu, D-76) slijedi.

## 1. Tok

1. **Prijedlog** — `py -m hub.nalozi.optimiziraj --db hub.db --nalog 12` ili `POST /api/nalog/{id}/obracun` (upis obračuna sam napravi prijedlog
   za svaki materijal bez potvrde): Hub po D-19 složi materijal s najmanje površine za naplatu (svi dopušteni načini, puna pretraga) i upiše ga u
   `optimizacija` sa statusom `prijedlog` i **snimkom slaganja** (`slaganje_json`: ploče, trake, komadi po elementu, ploča, obrez, kerf).
2. **Alternativa na zahtjev** — `POST /api/nalog/{id}/materijal/{nm}/optimizacija {nacin, dubina}`: način `auto | uzduzno | poprecno | trake` ×
   dubina `brzo | najbolje`. Uz svaki prijedlog stoji razlika prema automatskom (`razlika_m2_prema_auto`, `razlika_ploca_prema_auto`) — na BOGDANIC
   IV BIJELI NK 18: auto 27,35 m² (30 s), uzdužno/brzo 28,98 m² (1 s), „+1,63 m² prema auto“. „Brzo“ = osnovni kandidati bez startova, smjera po
   ploči i dotjerivanja zadnje ploče.
3. **Potvrda** — `POST /api/optimizacija/{oid}/potvrdi {tko}` / `--potvrdi ID --tko IVANA`: prijedlog postaje `potvrdjeno` (tko, kad), dotadašnje
   potvrđeno `zamijenjeno`; događaj u nalogu. Ako nalog već ima poslanu ili potvrđenu ponudu, odgovor nosi `ponuda_poslana: true` i događaj kaže
   „PONUDA JE VEĆ POSLANA, treba nova verzija“.
4. **Iz potvrđenog slaganja idu sve tri stvari:** obračun / ponuda (`obracun.izracunaj` čita snimku — stavka ploče nosi „(potvrđeno)“), CPO za pilu
   (`export_pila` piše CPO iz iste snimke, ne optimira iznova, i na isti red upiše program, sheme i dokument) i nabava (broj ploča iz istog reda).
5. **Bez potvrde nema ponude ni izvoza**: `nova_verzija` i `export_pila` stanu s porukom „optimizacija nije potvrđena za: …“. Iznimke: `--suho` pokazuje
   Hubov prijedlog (ne piše), `--forsiraj` i `--potvrdi-opt` / `potvrdi_opt` (probe, CLI) sami potvrde auto prijedlog s napomenom „potvrđeno automatski“.
6. **Promjena elemenata** (mjere, komadi, ploča) nakon prijedloga ili potvrde → red postaje `zastarjelo` (hash elemenata), treba novi prijedlog.

`GET /api/nalog/{id}/optimizacija` daje po materijalu: treba li slaganje (RP/ZO ne), potvrđeno, živi prijedlozi — to je ekran za potvrdu.

## 2. Postavke (D-77) — `GET/POST /api/postavke/optimizacija`

| Ključ | Zadano | Što radi |
|---|---|---|
| `kerf` | 16 | kerf za korisni ostatak i naplatu (PW „Podesi alat“) |
| `kerf_pile` | 5 | fizički kerf pile — slaganje i CPO (D-72) |
| `nadmjera_trake` | 10 | % iznad Σ stranica za metre trake u ponudi (stavka piše „nadmjera 10 % unutra“) |
| `obracun_rezanja` | m2 | `m2` po m² ploče (US000002 / US000013) · `rezova` po broju rezova (`ident_rezanje_rez`, zadano US000303) · `m_reza` po dužnom metru (`ident_rezanje_m` — prazno, pa Hub upozori i računa po m²) |

Postavke su globalne; ponuda nosi snimku brojki (D-69/3), pa promjena ne mijenja stare ponude. Ekran za njih ide među skrivene postavke (uz mail).

## 3. Shema v10 i testovi

`optimizacija` + `status`, `nacin_trazen`, `dubina`, `slaganje_json`, `elementi_hash`, `kerf`, `obrez`, `potvrdio_id`, `potvrdjeno`, `napomena`
(migracija sama pri prvom pokretanju); `usporedba` naplaćeno vs potrošeno gleda samo potvrđeni Hubov red. Postojeći testovi rade s automatskom
potvrdom (`tests/conftest.py`), pravilo se testira u `tests/test_optimizacija_potvrda.py` (prijedlog → potvrda → ista brojka u ponudi i CPO-u, zamjena
uz poslanu ponudu, zastarijevanje, načini × dubine, postavke D-77, API). **114 testova prolazi** sa stvarnim podacima.

## 4. Krojni nacrt PDF (drugi dio, isti dan — D-76 / D-77)

    py -m hub.ispis.krojni --db hub.db --nalog 12 [--materijal 40] [--oid 17] [--mapa C:\ISPISI]
    GET  /api/nalog/{id}/ispis/krojni.pdf?materijal=40      (PDF u odgovoru; bez `materijal` svi materijali naloga koji se slažu na ploču)
    POST /api/nalog/{id}/ispis/krojni.pdf {materijal, mapa, tko}   (napravi i zabilježi kao dokument `pdf_krojni`)

`hub/ispis/krojni.py` (reportlab) iz **potvrđenog slaganja** (D-75) radi ono što operater danas čita s PW-ovog ispisa, ali kao Hubov dokument —
po Igorovim uputama 16. 9.: naslov sličan PW-u, ne isti, s logom Paneli_ Production Hub; **crno-bijelo i štedljivo** (bez ispuna i boja);
**oznake kantiranja kao u PW** (puni trokutić na rubu komada, vrh prema van; kad materijal ima više traka uz trokutić stoji broj kanta,
legenda „Kant 1. = TR001254 ABS 1/22 JELA CLAY · R2-04-B“); **ploča uspravno** — duža stranica 2800 je okomita na A4.

- **List po ploči:** zaglavlje (logo, naziv, program `HUB_00012` s barkodom Code 39, List x / y), blok nalog · materijal (ident + naziv + Winstore kod
  + stanje na skladištu) · ploča (mjere, debljina, god, obrez) · slaganje (način, kerf pile / obračuna) · **tko je potvrdio i kad**; redak lista
  (smjer, komada, rezova, iskorištenje, m² dijelova, korisni ostatak); crtež s brojem elementa, napomenom / nazivom, mjerama u komadu, trokutićima
  kantiranja, rezovima (točkasto) i natpisom OSTATAK; legenda kantova; podnožje s datumom ispisa.
- **Statistika:** tablica elemenata (naziv, mjere, kom, god, oznake `2DA 2KA` kao PW, **kant po rubu L·O·D·G**, napomena), ploče i površina
  (ident, Winstore, potrošene ploče, m² ploča / dijelova / **za naplatu** s kriterijem ostatka, korisni ostaci), **kantiranje po traci** (Kant n.,
  ident, naziv, točni metri, metri za ponudu s nadmjerom iz postavke, **pretinac iz Regal trake, metri na roli**).
- Bez potvrđenog slaganja nacrt se napravi iz Hubovog prijedloga s crvenom oznakom **PRIJEDLOG — nije za pilu**; `--oid` ispisuje konkretan prijedlog
  (alternativu) radi usporedbe prije potvrde.
- **Regal traka:** `hub/skladiste/trake.py` čita `GET /api/stanje` (postavka `regal_traka_url`, zadano `http://192.168.5.201:8080`) — `lok` → pretinac,
  `q` → metri; keš 60 s; kad nije dostupna, polje ostaje prazno i ništa ne staje (D-63/D-64: Hub samo čita).
- Winstore nema mjesto na regalu u izvozu, pa za ploče piše kod i stanje u komadima.

**Igorove dorade izgleda (16. 9. popodne, ugrađene):** puni trokutić = ABS, prazni = melamin; mjere komada uz desni (okomita, zaokrenuto) i donji rub,
veći font, odmaknute od trokutića; ploča zrcalno po visini — prve trake gore, ostatak dolje kao u PW; zaglavlje bez kerfa obračuna (samo kerf pile),
`God` kao zaseban redak **DA / NE** podebljano; statistika s kolonama **Melamin** i **ABS** kao PW (`1DP`, `2DA 2KA`) uz kant po rubu; PLOČE /
POVRŠINA SVIH PLOČA / POVRŠINA ZA NAPLATU kao tri uočljive kućice; kantiranje po traci samo **Količina m** (metri s nadmjerom), bez „točno m“.

Probni PDF-ovi: `docs/sheme_proba/krojni_proba_JELA.pdf` (HUMER JELA TAVERNA, 6 listova + 2 stranice statistike — usporedivo s
`05_NALOZI_ZA_TEST\_HUMER_OMIS\02_panelwizard\JELA TAVERNA 19MM.pdf`) i `krojni_proba.pdf` (BOGDANIC BIJELI NK 18, dvije trake → Kant 1. / Kant 2.).
Testovi: `tests/test_ispis_krojni.py` (podaci, lažna Regal traka, PRIJEDLOG, dokument, API). **116 testova prolazi.**

## 5. Što ostaje u koraku 5b

Radni nalog / popis elemenata, pick-lista traka (D-63), izdatnica i narudžbenica na istom modulu `hub/ispis/`; ekran s gumbom „Ispis“ dolazi s web ekranima.
