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

## 4. Što ostaje u koraku 5b

Krojni nacrt PDF po materijalu u PW rasporedu (listovi s komadima, mjerama, oznakama i kant trokutićima, ostatak, legenda kantova, barkod programa;
statistika s identima materijala i traka + skladišna mjesta iz Winstorea / Regal trake, kantiranje po dekorima) — D-76 / D-77; zatim radni nalog,
pick-lista, izdatnica na istom modulu.
