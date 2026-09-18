# 38 — Winstore: dokumentirano sučelje `WINSTORE_EXCHANGE`

**18. 9. 2026.** · Izvor: upute proizvođača s Winstore računala — `IntegrationR103.ENG` („Integration with external software“, rev. 1.03) i `Integration Credentials.ENG`, uz postavke `C:\SPV\Settings\WINSTORE\WINSTORE.xini`.

---

## 1. Ukratko

Winstore **već ima sučelje za vanjski softver** i upute za njega leže na samom stroju. Ne treba ni ručni XML izvoz ni čitanje unutarnje baze: sve ide kroz zasebnu SQL Server bazu **`WINSTORE_EXCHANGE`**, s vlastitim korisnikom (`external`, lozinka je u uputi `Integration Credentials`). Upute sučelje zovu „integracija s optimizatorima“ — a Hub je točno to.

Postavke stroja (`WINSTORE.xini`): poslužitelj `LOCALHOST\THMI`, glavna baza `WINSTORE`, korisnik `algoritmo` (lozinka šifrirana u datoteci — **ne prepisivati**). Automatsko skladište zove se `WINSTORE`, ručno odlaganje ostataka `DROPS`.

## 2. Što Hub može ČITATI

| Pogled | Sadržaj | Čemu nam služi |
|---|---|---|
| **`vBoardsDropsStatus`** | Code, L, W, T, Grain, MaterialCode, MaterialDescription, **IsDrop** (1 = restl, 0 = ploča), **Stored**, **StoredInternal** (automatsko skladište), **StoredExternal** (vanjska skladišta), **Booked** | **Živo stanje.** Raspoloživo = `Stored − Booked`. Zamjenjuje ručni XML izvoz i rješava svježinu stanja iz D-95 §7 |
| `vDropsExtPgm` | restlovi: mjere, materijal, **SiteName** (radno mjesto), **InAutomaticStore**, CreationDate, polja rezervacije | Gdje koji restl fizički stoji |
| `vMaterialsBooking` | rezervacija ploča po redu (QueueType: 10 izlaz, **20 SELCO**, **30 ROVER**, 40 sljedeći korak) | Hub rezervira ploče u samom Winstoreu, ne samo kod sebe |
| `vMaterialsExPgm` | zaključavanje materijala dok optimizator računa | Da dva programa ne uzmu istu ploču |

## 3. Što Hub može PISATI

| Tablica | Operacija | Sadržaj |
|---|---|---|
| `tMaterialsOp` | `+` dodaj/izmijeni, `-` obriši | materijali (kod, naziv, debljina, god, boja) i ploče (kod, materijal, L, W, grupa) |
| **`tExternalDropsOp`** | `+M` definiraj i smjesti, `+P` smjesti po picking listi, `>` premjesti, `-` obriši | **restlovi u vanjskom skladištu**, sa `SiteBarcode` = barkod radnog mjesta |
| `tWarehouseInOut` | zapis, `Direction` `+` ulaz / `-` izlaz | stvarni ulaz i izlaz ploče ili restla iz skladišta, s `Batch` i dodatnim podacima |
| `tBuiltStacks` / `tBuiltStacksRows` | čitanje | **što je stvarno složeno** po picking listi: ploča, mjere, materijal, količina, radno mjesto, rok isporuke, podaci obrade |
| `tTagExchange` | zapis/čitanje | generička razmjena vrijednosti s vanjskom automatikom |

**Protokol je isti za sve tablice:** upiše se redak s `ProcessingDate = NULL`; supervizor ga obradi i upiše `ProcessingDate` te `ProcessingError` — prazan niz znači uspjeh, inače `[Polje]:[kod]` (npr. `1004` materijal je u upotrebi, `1005` restl je već u skladištu, `1007` zamrznut restl). Dakle **potvrda obrade postoji**, ne piše se naslijepo.

**Rezervacija je obavezan obred:** dok računa, optimizator mora „zamrznuti“ restlove (`BookingId` + `FreezingCode`), a nakon računa osloboditi neiskorištene i označiti iskorištene (`BookingDate`, `BookingCode`). Popis oznaka optimizatora u uputi je: 0 = bez rezervacije, SPAZIO3D, Optiplanning, Ardis, **„od tu nadalje slobodno“** — Hub dobiva svoj broj.

## 4. Što to mijenja za Hub

1. **Stanje ploča postaje živo.** `vBoardsDropsStatus` se čita kad god treba; ručni izvoz i „uvoz svakih 30 min“ postaju nepotrebni. Odluka D-95 §7 (starost stanja na ekranu) time gubi razlog postojanja u sadašnjem obliku.
2. **Rezervacija postaje stvarna.** Danas Hub rezervira samo kod sebe; preko `vMaterialsBooking` rezervacija vrijedi i u Winstoreu, pa drugi nalog ili drugi program ne može uzeti istu ploču.
3. **Izdavanje se može zatvarati samo od sebe** — `tWarehouseInOut` javlja stvarni izlaz, pa Hub ne mora čekati da netko klikne „izdano“ za ploče koje Winstore poslužuje.
4. **Plan vs stvarno** — `tBuiltStacksRows` daje što je stvarno složeno za koji nalog, bez skupljanja `.mno` datoteka (nadopunjuje ideju I‑21).
5. **Naši restlovi bi mogli u Winstore kao „vanjski“** (`tExternalDropsOp` vodi restlove u vanjskom skladištu, sa SiteBarcode mjesta) — tada bi jedna slika pokrivala i automatsko skladište i naš regal. **Ne sada**: D-95 kaže da je Hub evidencija restlova, a `PSADrops` se ne koristi. Vrijedi znati da je put otvoren.

## 5. Oprez prije ijednog upisa

- **Prvo samo čitanje.** `vBoardsDropsStatus` je bezopasan `SELECT`. Pisanje u `tMaterialsOp`, `tExternalDropsOp` i rezervacije dira sustav koji upravlja strojem — tek nakon dogovora s Biesseom i na praznom hodu.
- **Mrežni pristup treba provjeriti.** Baza je na `192.168.5.212`, instanca `THMI`. SQL Browser radi, ali nije poznato je li uključen TCP/IP i je li port otvoren prema mreži; to je zahvat na stroju.
- **Korisnik `external`** iz upute možda nije stvoren na ovoj instanci — provjerava se prvim spajanjem. (Korisnik `SeedXP` nije `sysadmin`, pa preko njega ne ide.)
- **Revizija upute je 1.03 iz 2018., a instalirani Winstore je 1.0.4** — provjeriti odgovaraju li imena pogleda i tablica; zato prvi korak i jest popis onoga što u bazi stvarno postoji.
- Lozinke iz `WINSTORE.xini` i iz upute **ne prepisuju se** ni u jedan dokument ovog projekta.

## 6. Prvi korak

`20_ANALIZA\skripte\WINSTORE_TEST_EXCHANGE.bat` — pokreće se **na PANELI-PC** (ondje gdje Hub radi), pita lozinku (ne sprema je), spaja se na `192.168.5.212\THMI`, bazu `WINSTORE_EXCHANGE`, i **samo čita**: popis tablica i pogleda, broj redaka u `vBoardsDropsStatus` i prvih 20 redaka. Ako to prođe, sve ostalo iz ovog dokumenta je dostupno.

## 7. Proba čitanja je prošla (18. 9. 2026., 14:01)

`WINSTORE_TEST_EXCHANGE.bat` pokrenut s Igorova računala (DESKTOP-7Q8JPT0) — **spajanje na `192.168.5.212\THMI` radi preko mreže, s prijavom `external`, bez ikakvog zahvata na stroju.** Poslužitelj: Microsoft SQL Server 2014 SP3 (12.0.6024.0).

**U bazi je 13 objekata** — 8 tablica i 5 pogleda:

| Tablice | Pogledi |
|---|---|
| `tMaterialsOp`, **`tBoardsOp`**, `tExternalDropsOp`, `tWarehouseInOut`, `tBuiltStacks`, `tBuiltStacksRows`, `tTagExchange`, `tV109` | `vBoardsDropsStatus`, **`vBoardsDropsStatusEx`**, `vDropsExtPgm`, `vMaterialsBooking`, `vMaterialsExPgm` |

Dvije ispravke upute: ploče imaju **vlastitu tablicu `tBoardsOp`** (uputa je i za ploče navela `tMaterialsOp` — očita pogreška u pisanju), a postoji i nedokumentirani pogled **`vBoardsDropsStatusEx`** koji treba pogledati prije nego se odabere izvor.

**Što je stvarno u podacima (18. 9. u 14:01):**

- `vBoardsDropsStatus`: **525 redaka, sve ploče, nijedan restl** — što se slaže s tim da se `PSADrops` ne koristi; `vDropsExtPgm` je prazan.
- Šifre su **točno one koje Hub već ima** iz XML izvoza (`W908ST2-18-2800-2070`, `3025SN-18-2800X2070`, `IV000301-16-2800X1840`…), a materijal i naziv odgovaraju `winstore_ploca.materijal_kod` i opisu. **Preslikavanje je jedan-na-jedan, bez novog šifrarnika.**
- Stupci se poklapaju sa starim XML-om: `Stored` ↔ `TotalQty`, `StoredInternal` ↔ `InternalQty`, `StoredExternal` ↔ `ExternalQty` — **uz `Booked`, kojega u XML-u nikad nije bilo.**
- `tWarehouseInOut`: živa kretanja, zadnje istog dana u 12:43 — izlazi (`-`) prema stroju i ulazi (`+`) 17. 9. popodne.
- `tBuiltStacks`: 10 hrpa istog dana, radno mjesto `TR1`, **`QueueType` 30 = ROVER** — dakle nesting slaganja se bilježe.

**Zaključak:** stanje ploča može biti živo već danas, samo čitanjem, bez Biessea i bez ijedne promjene na stroju. Ručni XML izvoz postaje rezerva, ne izvor.

## 8. Što je ugrađeno (18. 9. 2026.)

| Dio | Gdje |
|---|---|
| Čitanje pogleda i uvoz u `winstore_ploca` | `hub/sifrarnici/winstore_sql.py` — `procitaj`, `osvjezi`, `provjeri`, `osvjezi_ako_treba`, CLI `py -m hub.sifrarnici.winstore_sql --provjeri` |
| Zajednički upis za XML i bazu | `hub/sifrarnici/winstore.py` — `uvezi_stavke` (XML uvoz je sad samo tanki omotač oko njega) |
| Novi stupac `winstore_ploca.rezervirano` | `Booked` iz Winstorea; shema **v19** |
| Postavke i krajnje točke | `GET/POST /api/postavke/winstore`, `POST /api/winstore/provjeri`, `POST /api/winstore/osvjezi` |
| Ekran | Postavke → kartica **Winstore**: prekidač, poslužitelj, baza, korisnik, lozinka (upisuje se, natrag se ne šalje), koliko minuta stanje smije biti staro, gumbi **Provjeri vezu** i **Osvježi sada**, oznaka svježine stanja |
| Samo osvježavanje | `/api/skladiste/stanje` prije odgovora pozove `osvjezi_ako_treba` — ako je stanje starije od zadanog, Hub ga sam povuče; neuspjeh se zapiše u dnevnik i ekran radi sa zadnjim poznatim stanjem |
| Priprema na VM-u | `deploy\4_WINSTORE_PRIPREMI.bat` — instalira `pymssql` i provjeri vezu; `pymssql` namjerno **nije** u `requirements.txt` da neuspjeh instalacije ne sruši redovni deploy |

Uvoz XML-a radi i dalje, nepromijenjen, kao rezerva. **190 testova.**

Prvo pokretanje na VM-u: `4_WINSTORE_PRIPREMI.bat`, pa u Postavkama upisati lozinku, uključiti prekidač i spremiti.
