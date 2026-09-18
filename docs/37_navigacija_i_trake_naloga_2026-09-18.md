# 37 — Bočni izbornik, raspored radnji i trake na skladištu naloga

**18. 9. 2026.** · Igorove napomene: raspored gumba pod SKLADIŠTE je nelogičan; sve radnje na lijevu stranu; trake na skladištu naloga u vlastitu tablicu kao ploče.

---

## 1. Što je bilo krivo

Bočni izbornik imao je jednu stavku **Skladište**, a ispod nje četiri gumba koji su otvarali stvari iz tri različita svijeta: *Stanje* (ploče), *Restlovi* (popis), *Dekori za potvrdu* (posao ureda) i *Skladištar* (poseban ekran s izdavanjem, skenerom i potvrdama). „Skladištar“ je pritom bio **radno mjesto kao naziv ekrana**, a ne tema — pa se isti restl potvrđivao na dva mjesta, a izdavanje se nije moglo naći ni pod čim.

## 2. Nova podjela — dvije teme, svaka sa svojim podizborom

| Bočni izbornik | Podizbor | Što je unutra |
|---|---|---|
| **Skladište** | **Stanje** | ploče (Winstore) i restlovi po materijalu, pretraga |
| | **Izdavanje** | ono što skladištar mora izdati rukom: restlovi i materijali kojih Winstore nema; jedan gumb *Izdano* po stavci |
| **Restlovi** | **Popis** | svi restlovi, filtri po statusu, pretraga, *+ Restl*, naljepnice |
| | **Za potvrdu** | skener QR-a, prijedlozi restlova iz shema (*Potvrdi* / *Odbaci*), *+ Novi restl* |
| | **Dekori za potvrdu** | dekori iz evidencije restlova bez sigurnog identa |

Ekran **Skladištar** je ukinut. Poveznica `#/skladistar` i dalje radi — vodi na **Restlovi → Za potvrdu**, pa stari zabilježeni linkovi ne pucaju. QR naljepnice vode na `#/restl/OZNAKA` i nisu se mijenjale.

Zašto tako: *Skladište* odgovara na pitanje „ima li toga i gdje je“, *Restlovi* na „što nam je ostalo i je li potvrđeno“. Skladištar tijekom smjene radi samo u dvije kartice — **Skladište → Izdavanje** i **Restlovi → Za potvrdu** — i obje su sada u bočnom izborniku, bez skrivenog ekrana.

## 3. Sve radnje na lijevoj strani

Prema skici: alatna traka ekrana (podizbori, gumbi, polja za pretragu) i zaglavlja ploča više ne guraju sadržaj udesno.

- `.alatna` je `justify-content:flex-start`, a razmaknica `.grow` unutar nje je neutralizirana;
- isto u zaglavljima ploča (`.pane .hd`) — pretrage i gumbi koji su stajali desno sad slijede naslov slijeva;
- polja za pretragu preseljena su iz zaglavlja tablice u alatnu traku, uz podizbor, pa je sve na istoj visini.

Nije mijenjano: gumbi **na kraju retka** u popisima (*Potvrdi / Odbaci / Izdano*) i **desni gumb u kartici** (*Otpiši*) — to su radnje nad tim retkom, a ne izbornik; ako Igor želi i njih lijevo, to je jedan potez.

## 4. Trake na ekranu Skladište naloga

Trake su bile stisnute u zadnji stupac tablice ploča, po jedan red teksta za svaku, bez zajedničkog zbroja. Sada su **vlastita tablica ispod ploča**, istog rasporeda:

| Traka | Potrebno | Raspoloživo | Pozicija | Status | Na materijalima |
|---|---|---|---|---|---|
| naziv + ident i klasa | metri s nadmjerom | metri na roli (Regal traka) | pretinac (npr. `R7-08-C`) | Dostupno / Manjak *x* m / Stanje nepoznato | materijali koji tu traku troše |

Dvije ispravke u računu koje su došle s tim:

1. **Metri se zbrajaju po traci, ne po materijalu.** Ista traka na tri materijala prije se zaokruživala tri puta (2,2 m + 2,2 m + 2,2 m → 3 + 3 + 3 = 9 m); sada se zbraja točno pa zaokružuje jednom (6,6 → 7 m).
2. **U „Za nabavu“ traka ulazi jednom**, s ukupnim manjkom, a ne jednom po materijalu. Popis *Za nabavu* tako sadrži i ploče i trake kojih nema dovoljno — isto pravilo, ista tablica.

Kad Regal traka ne odgovara, stupac *Raspoloživo* piše `?`, status je *Stanje nepoznato* i traka **ne ulazi** u nabavu — Hub ne izmišlja manjak iz nedostupnog izvora.

## 5. Kod i testovi

| Datoteka | Izmjena |
|---|---|
| `hub/web/app.js` | nova stavka bočnog izbornika **Restlovi** + ikona |
| `hub/web/ekrani.js` | `E.skladiste` (stanje, izdavanje), novi `E.restlovi` (popis, za potvrdu, dekori), `E.skladistar` → preusmjerenje; tablica traka na skladištu naloga |
| `hub/web/app.css` | radnje lijevo (`.alatna`, `.pane .hd`); maknut stari zbijeni stupac traka |
| `hub/skladiste/pogled.py` | `trake_naloga()` — zbroj po traci; `provjera_naloga()` vraća `trake` i upisuje traku u nabavu jednom |
| `tests/test_navigacija_2026_09_18.py` | 4 nova testa (izbornik, podizbori, radnje lijevo, tablica traka) |
| `tests/test_skladiste.py` | provjera zbroja traka i nabave |

**184 testa**, shema ostaje **v18** (nema promjene baze).
