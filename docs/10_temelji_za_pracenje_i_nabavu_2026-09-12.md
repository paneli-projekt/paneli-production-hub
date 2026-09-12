# Paneli Production Hub — 10: idući korak unaprijed — što Hub mora pripremiti za praćenje proizvodnje i narudžbenice (12. 9. 2026.)

Igorova napomena 12. 9. navečer: u cijelom procesu treba misliti i na idući korak — kontrolu procesa proizvodnje koja će izrasti iz Huba, i na
narudžbenice (u Hubu ili u Knjizi?): što sve treba proslijediti — rokovi, odgovorne osobe, raspoloživo i rezervirano stanje skladišta…
Ovaj dokument je analiza, ne plan gradnje: praćenje proizvodnje ostaje zaseban sustav i kasnije (D-03, I-06); ovdje se odlučuje **što Hub
bilježi već sada** (jeftino, jer podatak ionako nastaje) da se poslije ništa ne prekucava i ne prepravlja.

## 1. Načelo: Hub je izvor istine za NALOG, praćenje je potrošač

Praćenje proizvodnje ne smije ponovno unositi ni kupca, ni elemente, ni materijale, ni rokove — sve to čita iz Huba preko API-ja (D-12).
Zato Hub već u fazi 1 bilježi četiri stvari koje ekrani zasad ne pokazuju posebno, ali ih baza mora imati:

| Što | Gdje nastaje | Zašto sada |
|---|---|---|
| **Događaji naloga** (dnevnik promjena statusa: iz → u, tko, kada, razlog) | svaki gumb koji mijenja status (Spremi, Pošalji kupcu, Kupac potvrdio, Potvrdi skladište, Potvrdi put…) | to je vremenska crta naloga; praćenje i „naplaćeno vs potrošeno“ vise na njoj; ne može se rekonstruirati naknadno |
| **Rokovi** (rok kupca, planirani rok, rok dobave materijala) | unos (kupac), potvrda kupca (ured), skladište (nabava) | praćenje planira po rokovima; bez datuma potvrde nema mjerenja „koliko dugo od potvrde do isporuke“ |
| **Osobe po koraku** (unio, zaključao ponudu, potvrdio skladište, potvrdio put, naručio) | automatski iz prijave korisnika | „odgovorna osoba“ nije jedno polje nego niz; Hub ih ionako zna |
| **Rezervacije skladišta** (po nalogu i materijalu, sa statusom) | ekran 4 (skladište nakon potvrde) | raspoloživo = fizičko − rezervirano; praćenje treba znati što je izdano u proizvodnju |

Sve četiri stvari su u modelu iz 04 §2 djelomično predviđene (`dnevnik`, `rezervacija`); dopune su u §4.

## 2. Što će praćenje proizvodnje trebati od Huba (popis za predaju)

Kad praćenje dođe na red, od Huba očekuje — sve preko API-ja, ništa ručno:

1. **Identitet**: Hub broj naloga (D-33), naziv `KUPAC_NAZIV_BROJ`, kupac (Pantheon subjekt), vrsta naloga (usluga / vlastita proizvodnja, D-30).
2. **Elemente s operacijama**: za svaki element Hub već zna što se s njim radi — rezanje (pila ili nesting, D-29), kantiranje po rubu (koje trake,
   koliko metara), CNC obrade (iz napomena i, za Corpus naloge, iz CIX-a: bušenje, utor, kontura — I-14), ljepljenje, gotova mjera. To je
   **popis operacija** koji praćenje otkvačuje; Hub ga izvodi iz podataka koje već ima, ne traži novi unos.
3. **Putove i programe**: koji materijal ide na pilu (CPO HUB_xxxxx), koji na nesting (CSV+CIX, imena H000…), rezultat sa stroja (.mno, broj ploča).
4. **Rokove i prioritet**: rok kupca, planirani rok, datum potvrde, prioritet (ako ga voditelj postavi).
5. **Osobe**: tko je unio, tko potvrdio put, tko je operater (nesting / pila) — zadnje dvoje upisuje praćenje, ne Hub.
6. **Materijal**: rezervirano / izdano / potrošeno po nalogu, očekivane dobave (iz narudžbenica, §3), restlovi vezani uz nalog.
7. **Dokumente**: sheme (PNG), CPO, CIX, ponuda PDF, etikete — Hub ih već vodi u tablici `dokument`.
8. **Etikete**: ako će praćenje skenirati po elementu, element mora imati stabilan ID/QR na etiketi (I-04) — to je jedina stvar koju treba
   odlučiti PRIJE nego etikete ostanu u OSI-ju (D-25): u fazi 1 ostaju kako jesu, ali Hub element-ID rezervira i upisuje u CPO/CSV polje
   koje strojevi već nose (napomena / CabInfo).
9. **Obračun**: stavke ponude (za post-kalkulaciju: naplaćeno vs potrošeno + sati rada = marža po nalogu, D-18).
10. **Za vlastitu proizvodnju** (Corpus): korpusi i pozicije elemenata (I-15) — temelj praćenja montaže po korpusu.

## 3. Narudžbenice — u Hubu ili u Knjizi?

Potreba za narudžbom nastaje u Hubu (ekran 4: popis za nabavu nakon potvrde kupca, D-35), a zatvara se u Knjizi (račun dobavljača → primka →
Pantheon; isti eSlog puni i Hub skladište, D-02). Narudžbenica je dokument između ta dva kraja.

| | Narudžbenica u Hubu | Narudžbenica u Knjizi |
|---|---|---|
| Podaci koje treba | nalog, materijal, manjak, dobavljač, rok — sve već u Hubu | Knjiga bi morala čitati naloge i manjkove iz Huba (dupliranje) |
| Slanje dobavljaču | isti sustav slanja kao ponude (D-41), s adrese nabave | Knjiga danas ne šalje mailove |
| Zatvaranje (roba stigla) | Hub ne vidi račun dobavljača | Knjiga ga vidi — tu se stavke računa spajaju s narudžbom |
| Očekivane dobave za planiranje | u Hubu odmah (raspoloživo + naručeno) | Hub bi ih morao dohvaćati iz Knjige |

**Prijedlog (D-42): narudžbenica nastaje i živi u Hubu (modul `nabava`), a zatvara se automatski iz primke.** *(Prvotno „zatvara se u Knjizi“ — nakon odgovora 2 u §6: Knjiga se ne mijenja, Hub spaja stavke primke s otvorenim narudžbenicama sam.)* Hub iz popisa za nabavu složi
narudžbenicu po dobavljaču (ident, naziv, kom, dimenzija ploče, za koje naloge), pošalje je mailom i vodi status: nacrt → poslana →
djelomično zaprimljena → zaprimljena, s očekivanim datumom. Zatvaranje: isti eSlog primke koji Knjiga radi za Pantheon stiže i Hubu
(mapa ili API) i puni Hub skladište (D-02); Hub pri tom ulazu sam spoji stavke primke s otvorenim narudžbenicama istog dobavljača (ident +
količina) i označi ih zaprimljenima, pa se rezervacija naloga pretvara u fizičku ploču bez ručnog rada. Knjiga se ne mijenja (danas samo
uvozi račune). Pantheonova „narudžba dobavljaču“ se ne koristi (nije financijski dokument; financije počinju primkom).

Što narudžbenica mora nositi: dobavljač (Pantheon subjekt), stavke (ident, naziv, kom, JM, dimenzija, dekor), za koje naloge (više naloga se
skupi u jednu narudžbu), tko naručio, datum, očekivani datum dobave, napomena („samo cijele ploče“ za dekore po narudžbi, D-37b), status.

## 4. Dopune modela podataka (04 §2) — što se dodaje sada

```
nalog            + rok_obecan (službeni — ured pri potvrdi), rok_kupca (napomena), prioritet, potvrda_kupca_datum, potvrda_kupca_nacin (mail|telefon|osobno), potvrdio_id,
                   vrsta (usluga|vlastita_proizvodnja), rabat_materijal, rabat_usluge (D-40)
dogadjaj         id, nalog_id, kada, tko, iz_statusa, u_status, razlog, veza (npr. narudzbenica_id, dokument_id)      ← vremenska crta
rezervacija      + status (rezervirano|izdano|potrosjeno|oslobodjeno), izdao_id, izdano_kada                              (postoji, dopuna)
narudzbenica     id, dobavljac_pantheon, broj, datum, narucio_id, ocekivano, status, poslano_kada, napomena
narudzbenica_st  id, narudzbenica_id, pantheon_ident, naziv, kom, jm, dimenzija, nalog_materijal_id (0..n — zaliha unaprijed nema nalog), zaprimljeno_kom, primka_ref
operacija        id, nalog_id, nalog_materijal_id (prazno = operacija cijelog naloga: pakiranje, okov, isporuka), stroj (pila|nesting|rover|kanterica|cnc|ljepljenje|pakiranje),
                 kolicina (programi / ploče / elementi / metri), detalj_json (elementi)
                 ← jedinica = nalog × materijal × stroj (Igor 12.9.); Hub je IZVODI iz naloga (put, rubovi, CIX); status upisuje praćenje, ne Hub
element          + hub_uid (stabilan ID — rezerviran, na etiketu tek ako praćenje jednom krene po elementu, I-04)
```

API koji praćenje i Knjiga dobivaju od Huba (uz postojeće `/api/nalog`, `/api/restl`, `/api/traka/potrosnja`):
`/api/nalog/{id}` (nalog + materijali + elementi + operacije + dokumenti + rokovi), `/api/nalog/{id}/dogadjaji`, `/api/skladiste/stanje`
(fizičko, rezervirano, naručeno po materijalu), `/api/nabava/potrebe` (Σ po materijalu preko svih potvrđenih naloga), `/api/narudzbenice?status=otvorena&dobavljac=`, `POST /api/primka` (eSlog primke → ulaz robe + zatvaranje narudžbenica).

## 5. Što se NE radi sada

Ne gradi se ekran praćenja, ne skeniraju se etikete, ne planira se kapacitet strojeva, ne upisuju se sati rada. Hub dobiva samo priključke:
polja iz §4, dnevnik događaja i API. Trošak je mali (polja i jedna tablica više), a bez toga bi praćenje moralo krenuti od nule.

## 6. Igorovi odgovori (12. 9. navečer) i što mijenjaju

1. **Sanela naručuje kroz sustav narudžbi u starom programu kontrole proizvodnje**: pregleda naloge koje otvara i iskustveno naručuje robu
   unaprijed. → Narudžbenice sele u Hub (modul `nabava`) kao zamjena za taj dio starog programa. Dvije posljedice: (a) Hub Saneli daje
   **pregled potreba preko svih potvrđenih naloga** (Σ potrebno po materijalu − fizičko − rezervirano + već naručeno), ne samo popis po
   jednom nalogu; (b) stavka narudžbenice **može biti bez naloga** (zaliha unaprijed, „iskustveno“) — veza na nalog je opcija, ne obveza.
2. **Knjiga danas samo uvozi račun dobavljača** (stavke → Pantheon). → Zatvaranje narudžbenice NE ide kroz Knjigu nego kroz Hub: isti eSlog
   primke koji Knjiga radi za Pantheon puni i Hub skladište (D-02); Hub pri tom ulazu sam spoji stavke s otvorenim narudžbenicama istog
   dobavljača (ident + količina) i označi ih zaprimljenima. Knjiga se ne mijenja — treba samo da eSlog primke stigne i Hubu (mapa ili API).
3. **Službeni rok je onaj koji ured obeća** pri potvrdi (rjeđe onaj koji kupac traži). → `nalog.rok_obecan` je glavni rok (upisuje ured na
   „Kupac potvrdio“), `rok_kupca` je opcionalna napomena; praćenje planira po obećanom.
4. **Praćenje je bilo po stroju i po nalogu**, ne po materijalu — ali, Igorova dopuna odmah zatim: *kad se već slaže od početka, želi
   praćenje i po materijalu unutar naloga.* → Jedinica praćenja = **nalog × materijal × stroj** (pila ili nesting/Rover, kanterica, CNC,
   ljepljenje); operacije koje su po cijelom nalogu (pakiranje, okov, isporuka) imaju materijal = prazno. Hubu je to prirodno: `nalog_materijal`
   već postoji, a exporti su ionako po materijalu (CPO po materijalu, CSV+CIX po materijalu, .mno po materijalu), pa Hub za svaki materijal
   naloga daje: rezanje (program / nesting projekt, broj ploča), kantiranje (metri po traci), CNC (elementi s obradom), ljepljenje. To su
   „količine operacija“ iz D-03. Element-ID na etiketi (I-04) zasad nije potreban; elementi ostaju detalj ispod materijala.

Time je D-42 potvrđen (ODLUČENO) s tim dopunama. Za mockup: ekran „Nabava“ (Sanelin pregled potreba + narudžbenice) ide u v0.4 uz
ekran skladišta.
