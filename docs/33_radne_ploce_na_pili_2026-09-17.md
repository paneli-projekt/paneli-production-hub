# 33 — Radne ploče, ploče stola i zidne obloge na pili (17. 9. 2026., D-92)

## Što je Igor javio

„Ploče stolova i radne ploče se sada ne optimiraju, a trebale bi — režu se uvijek na pili. Dužina 4100 mm, radna ploča 600, ploča stola 900.“

Pravilo prodaje postoji od 12. 9. (**D-37**), ali ga Hub nije provodio: radne ploče, ploče stola i zidne obloge bile su izbačene iz slaganja („po dužnom metru — nema slaganja“), u ponudu su išle kao zbroj duljina × komada, a izvoz na pilu za nalog s radnom pločom stao bi na „slaganje nije potvrđeno“. Igor je 17. 9. odgovorio na četiri pitanja.

## Pravila (D-37 + Igorovi odgovori → D-92)

| | Radna ploča 600 | Ploča stola 900 | Zidna obloga 640 |
|---|---|---|---|
| Slaganje | komad iza komada (duljina uz 4100, jedan komad u širini) | smiju se i uži komadi jedan uz drugi (trake uz duljinu) | komad iza komada |
| Naplata po ploči | zbroj duljina ≤ 2,7 m → točni metri (naviše na cm), **najmanje 1,4 m po ploči**; > 2,7 m → cijela 4,1 m | iskorištena duljina ≤ 2,05 m → **pola** (2,05 m), inače **cijela** (4,1 m) | uvijek **cijela** (4,1 m) |
| Ident u ponudi | ident dekora (RADNA PLOČA …) | **ident dekora** (PLOČA STOLA …) × 2,05 / 4,1 m — ne generički POLA / CIJELA | ident dekora |
| Rezanje US000303 | 2 reza × komad | 2 reza × komad | **4 reza × komad** (krajca se sa svih strana) |

Jedinica identa: M → metri; M2 → metri × širina ploče; KOM → broj započetih ploča uz upozorenje „provjeriti“.
Naš restl (plavo na shemi): samo kad ploča NIJE naplaćena cijela — ostatak uz duljinu ploče, iz njega skladište dobiva prijedlog restla.

## Kako radi u Hubu

- **Slaganje (korak 2)**: radne ploče, ploče stola i zidne obloge dobivaju prijedlog i potvrdu kao svi materijali; na kartici umjesto „m² za naplatu“ piše npr. „4,10 m za naplatu (radna ploča — ploča 1: 3,52 m → cijela 4,1 m)“. Hub rezerva se ne nudi (za komad iza komada nema razlike).
- **Ponuda (korak 3)**: stavka materijala nosi pravilo po ploči („ploča stola: ploča 1: 3,88 m → cijela 4,1 m; ploča 2: 2,11 m → cijela 4,1 m (potvrđeno)“), rezanje 2 ili 4 reza po komadu. Bez potvrđenog slaganja upozorenje kao za iveral.
- **Pregled shema i krojni nacrt**: po ploči „za naplatu x m (cijela / pola / najmanje 1,4 m)“, ostatak uz duljinu; statistika „ZA NAPLATU x m“.
- **Proizvodnja**: CPO za pilu iz potvrđenog slaganja; bez upozorenja „element na punu mjeru ploče“ (radna ploča pune dubine je normalna). Spajanje za nesting ih ne nudi.
- Kod: novi `hub/optimizacija/radne_ploce.py`; izmjene `nalozi/optimiziraj.py` (slaganje, `obitelj_rp`), `nalozi/obracun.py`, `nalozi/export_pila.py`, `nalozi/spajanje.py`, `ispis/krojni.py`, `ispis/sheme_png.py`, `web/ekrani.js`.

## Provjera

- `tests/test_radne_ploce_2026_09_17.py`: pravila po ploči (2,9 m → cijela; 2,6 m → 2,6 i restl 1490 mm; 0,9 → 1,4; 3,0 + 2,5 → dvije ploče 6,6 m), stol HUMER 2880 + 2110 → 2 × cijela, dva komada 440 jedan uz drugi → pola, zidna → cijela i 4 reza; cijeli nalog od prijedloga do CPO-a, krojnog nacrta i prijedloga restla. **162 testa prolaze** sa stvarnim podacima.
- PanelWizardovi `.pnl` iz testnih naloga kroz Hub (radna 600):

| Nalog | Komadi | Hub | Za naplatu |
|---|---|---|---|
| HUMER RP BASANIT SAND | 2265 | 1 ploča | 2,27 m |
| MAZUR RP HR CREMONA CANNOLO | 1600, 1900, 1650 | 2 ploče (1900 + 1650 / 1600) | 4,1 (cijela) + 1,6 = 5,7 m |
| BLAGO RP SLATE VULCANO | 2600 | 1 ploča | 2,6 m |

- Probni nalog u pregledniku (radna 2265 + 1250, stol 2880 + 2110 + 2 × 1000 × 440, zidna 2 × 1200): radna 4,1 m (cijela), stol 8,2 m (2 × cijela), zidna 4,1 m; slike `docs/ekrani_proba/17c_slaganje_radne_ploce.png`, `17c_ponuda_radne_ploce.png`.

## Dopuna (17. 9., kasno) — obrub ploče po materijalu, zeleni gumbi, „Optimizacija“ (D-93)

- **Obrub (rubljenje) ploče** je polje u dijalogu materijala na ekranu unosa („Obrub (rubljenje) mm“) i redak „Obrub“ u podacima materijala. Zadano **10 mm**; **radne ploče, ploče stola i zidne obloge 0 mm**. Upisani obrub vrijedi za optimizaciju, CPO za pilu, krojni nacrt i obračun; prazno polje vraća zadano. Zadani obrub i dalje pada na 0 kad element ima punu mjeru ploče (D-65/10); upisani se poštuje, a kad element s njim ne stane, poruka kaže da se obrub smanji. Promjena obruba poništi potvrđenu optimizaciju tog materijala (treba novu). Shema **v17** (`nalog_materijal.obrub`, migracija sama). Postojeće potvrđene optimizacije iverala ostaju valjane (isti izračun kao prije); radne ploče s komadima užim od ploče dobivaju 0 umjesto 10 pa traže novu optimizaciju.
- **Gumbi** koji su bili tamno zeleni (glavni gumbi, gumbi alatne trake, odabrani filtar) sada su **#4F8F32**.
- **„Slaganje“ → „Optimizacija“** u koraku 2, gumbima, natpisima, porukama na ekranu i krojnom nacrtu („Optimizacija čeka potvrdu“, „Potvrdi optimizaciju“, „Izračunaj optimizaciju“, kartica „Optimizacija“ na unosu). Adresa `#/nalog/N/optimizacija` (stara `/slaganje` i dalje radi).
- Slike `docs/ekrani_proba/17d_materijal_obrub.png`, `17d_optimizacija_gumbi.png`. **163 testa prolaze.**

## Ispravak (17. 9., navečer) — komad radne ploče se ne okreće

Igor na probi (RP ARCTIS DC, god uključen, elementi 500 × 600, 2000 × 600, 500 × 600): Hub je komad 500 × 600 okrenuo (600 uz duljinu, 500 u širinu) — pila bi odrezala zaobljeni rub. **Prva mjera (L) uvijek ide uz duljinu ploče, druga (W) je dubina** — za radnu ploču, zidnu oblogu i ploču stola, bez obzira na god. Element kojem je W veći od širine ploče više se ne okreće sam nego javlja „dubina W je veća od širine ploče — prva mjera (L) je dužina“. Proba nakon ispravka: 0,5 + 2,0 + 0,5 m na jednoj ploči, sva tri pune dubine 600, 4 reza, zbroj 3,0 m → cijela 4,1 m; prva proba (0,5 + 2,0) → 2,5 m (prije 2,6 zbog okrenutog komada). Slika `docs/ekrani_proba/17e_radna_ploca_orijentacija.png`.

## Otvoreno / za Igora

1. **Radna ili stol iz PanelWizardovog naziva**: PW piše „RP BASANIT SAND“ bez 600 / 900, pa Hub svaki takav materijal pita „za potvrdu“ (radna i ploča stola istog dekora imaju jednake bodove). Kad se potvrdi sa „zapamti“, alias bi zauvijek vodio na jednu obitelj. Prijedlog: komad širi od 600 mm → sigurno ploča stola; inače pitati kao sada, bez pamćenja obitelji. Igor odlučuje.
2. **Identi s jedinicom KOM** (9 radnih, 3 ploče stola, dio zidnih): količina = broj ploča uz upozorenje — treba li drukčije?
3. **Skladište / nabava**: Winstore ne vodi radne ploče; potreba za nabavu radnih ploča i dalje se ne računa u pločama (nije dirano).
4. Komad dulji od 4100 (spoj radne ploče): Hub ne slaže, stavka ide po zbroju duljina uz upozorenje — spoj ured dodaje ručno.
