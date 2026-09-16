# Paneli Production Hub — 24: „Što ako“ — rizici u radu i što se tada radi

Stanje 15. 9. 2026. Popis na Igorov zahtjev, nakon pitanja o ovisnosti Huba o AI-ju. Poredano po tome koliko bi zaboljelo, ne po vjerojatnosti.
Za svaku stavku: kako se primijeti, što Hub radi sam, što čovjek radi, i što napraviti unaprijed da bude bezbolno. AI je namjerno na dnu —
u radu Hub o njemu ne ovisi (dokument u razgovoru 15. 9.: nula vanjskih poziva u kodu).

## 1. Padne VM / računalo na kojem Hub radi

**Primijeti se:** ekrani ne rade, `py -m …` ne postoji. **Utjecaj:** ured ne može otvarati naloge ni slati na strojeve; strojevi rade s onim što je
već u mapama (CSV+CIX, CPO) — proizvodnja stane tek kad potroši pripremljeno.
**Što se radi:** Hub je jedna mapa (`30_NOVI_PROGRAM`) + jedna datoteka baze (`hub.db`) + `smtp_lozinka.txt`. Na bilo kojem PC-u s Pythonom:
`git clone` (ili kopija mape), `pip install -r requirements.txt`, vratiti zadnji `hub.db` iz sigurnosne kopije, pokrenuti API. Pola sata.
**Unaprijed:** noćna kopija `hub.db` na drugi disk / NAS (`copy hub.db \\NAS\hub\hub_%date%.db` u Task Scheduleru) — **ovo je jedina stvar bez
koje se gubi rad ureda**; kod je u Gitu. Jedna osoba osim Igora zna tri naredbe iz README-a.

## 2. Pokvari se baza (`hub.db`) ili je netko obriše

**Primijeti se:** API javlja grešku pri svakom pozivu, ili nalozi nestanu. **Što Hub radi sam:** SQLite je u WAL načinu, svaki izvoz i uvoz je
transakcija s rollbackom (D-65/9) — pola upisa ne ostaje. **Što se radi:** vratiti sinoćnju kopiju; nalozi od jutra ponovno se uvezu iz datoteka
(CPW/CSV su i dalje u mapama kupaca), a šifrarnik iz Pantheona jednim `py -m hub.sifrarnici.uvoz`. **Unaprijed:** kopija kao u točki 1; probno
vraćanje kopije jednom napraviti, ne samo snimati.

## 3. Pantheon promijeni izvoz (stupci u `ph_identi.csv`, `ph_subjekti.csv`, cijene)

**Primijeti se:** `py -m hub.sifrarnici.uvoz` stane s porukom o stupcu koji nedostaje, ili — gore — uveze krive cijene tiho. **Što Hub radi sam:**
uvoz provjerava obvezne stupce i ne prepisuje aliase ni ispravke ureda (D-51); ponude nose snimku cijene u verziji, pa stare ponude ostaju točne.
**Što se radi:** ako je promjena imena stupca — jedan redak u `pantheon.py`; ako su cijene sumnjive — usporediti s prethodnim uvozom (Hub pamti
`azurirano`). **Unaprijed:** uvoz ispisuje broj identa i broj promijenjenih cijena; ako je promijenjenih više od npr. 30 %, ne primijeniti bez pogleda
(vrijedi dodati kao automatsku provjeru). Najveći realni rizik u ovom popisu, jer se događa tiho.

## 4. OSI pila ne pročita Hubov CPO ili sheme ne odgovaraju

**Primijeti se:** operater na pili — program se ne učita ili rez ne odgovara shemi. **Što Hub radi sam:** svaki CPO prolazi `cpo_rw.validate`
(stablo rezova, mjere), zapis je bajt-po-bajt u PW-ovom obliku (16), sheme su nacrtane iz istog stabla. **Što se radi:** paralelno razdoblje
(D-73) postoji baš za ovo — PW je još mjesec dana instaliran, isti nalog se pusti kroz PW. Datoteku koja nije prošla sačuvati (`03_export_pila`
testnog naloga) i to postaje test. **Unaprijed:** prvih dva tjedna PW reže, Hub uspoređuje (D-73/2).

## 5. Biesse promijeni bNest uvoz (CSV profil) ili format CIX-a / `.mno`

**Primijeti se:** bNest ne učita Hubov CSV ili ne nađe materijal; ili Hub ne pročita `.mno`. **Što Hub radi sam:** CSV je isti 28-stupčani profil
koji bNest već čita (15), CIX je standardni bSolid (14 §3.4), `.mno` čitač javlja „nije bNest rezultat“ umjesto da upiše krivo. **Što se radi:** za
CSV — operater privremeno uvozi kroz PPNEST-ov profil (bNest ih čita istim profilom); za `.mno` — potrošnja se ne knjiži dok se čitač ne prilagodi,
obračun ostaje PW-metoda (D-18), ništa ne staje. **Unaprijed:** prije svake nadogradnje bNesta / bSolida pustiti Corpus uzorak (`_CORPUS_UZORAK`) —
to je pet minuta i pokriva CSV, oba CIX-a i `.mno`.

## 6. Corpus nova verzija promijeni CPW / CSV izvoz

**Primijeti se:** `uvoz_corpus` stane s porukom (nema CIX-a, kriv stupac). Hub **ne uvozi paket s greškom** (D-66/2), pa nema tihe štete.
**Što se radi:** tehnička priprema šalje uzorak kao 14. 9., čitač se prilagodi (do sada su razlike bile jedan stupac). **Unaprijed:** isti test kao u 5.

## 7. Winstore promijeni XML ili stanje ploča je krivo

**Primijeti se:** `uvoz` javlja da nema stupca, ili skladište pokazuje besmislene količine. **Što Hub radi sam:** uvoz zamjenjuje cijeli inventar
(ne zbraja, D-65), ambalaža se preskače (D-49), kod → ident veze koje je ured potvrdio ostaju. **Što se radi:** stanje je informativno dok nema
Warehouse modula; ponuda i izvozi ne ovise o njemu. **Unaprijed:** ništa posebno.

## 8. Padne mail hostinga ili se promijeni lozinka

**Primijeti se:** `posalji` vrati poruku „slanje nije uspjelo“ / „lozinka nije postavljena“, ponuda ostaje u nacrtu. **Što se radi:** ured pošalje
PDF (Hub ga je već napravio u mapi `ponude`) svojim mailom i klikne „poslana“; nova lozinka u `smtp_lozinka.txt`. Ništa se ne gubi.

## 9. Mrežna mapa za strojeve nije dostupna

**Primijeti se:** izvoz javi grešku pri pisanju; Hub tada **ne upisuje ni u bazu** (rollback). **Što se radi:** izvesti u lokalnu mapu (`--mapa`) i
prenijeti ručno; kad se mreža vrati, ponovni izvoz daje **ista imena** CIX-a (registar, D-23), pa nema duplikata.

## 10. Ljudska greška: krivi ident potvrđen, obrisan nalog, kriva potvrda kupca

**Što Hub radi sam:** svaka potvrda, izvoz i status su u `dnevnik` i `dogadjaj` (tko, kad, što); alias se može poništiti; nalog se nakon potvrde ne
briše nego zatvara (D-65/2); ponuda ima verzije, potvrđena se ne mijenja. **Što se radi:** krivi alias → obrisati u šifrarniku i ponoviti
prepoznavanje na nalogu (`ponovi-prepoznavanje`); krivi status → dopušten korak natrag do potvrde kupca (D-46/3). **Unaprijed:** korisnici s
oznakama (Ivana, Goran, Sanela…) da dnevnik ima ime, ne „web“.

## 11. Nadogradnja Pythona ili biblioteka pokvari nešto

**Primijeti se:** testovi. **Što se radi:** `py -m pytest` prije i poslije svake nadogradnje — 109 testova sa stvarnim podacima (postaviti
`HUB_TEST_DATA`) pokriva sve izvoze i obračun; pad testa = ne nadograđivati. **Unaprijed:** verzije su u `requirements.txt`; Python na PC-u je 3.14,
Hub je pisan za 3.10+.

## 12. Onaj tko piše kod (ja) nije dostupan

**Utjecaj na rad:** nikakav — Hub ne zove nikakav vanjski servis. **Utjecaj na razvoj:** kod je standardni Python koji svaki programer čita; testovi
kažu što mora raditi; DECISIONS kaže zašto; dokumenti 01–24 kažu kako je nastalo. Drugi čovjek ili drugi model preuzima bez mene. **Unaprijed:**
push u Git nakon svakog dana rada (`GIT_POSALJI.cmd`) — danas je 56 datoteka izvan Gita.

## 13. AI (Claude) nedostupan ili skup

**Utjecaj:** nula u proizvodnom toku — nijedan korak (nalog, izvoz, obračun, ponuda, eSlog) ne zove AI (D-15). Planirane AI udobnosti (rukopis s
fotografije, prijedlog identa okova) rade s prekidačem `none`: ured upiše ručno kao danas. To je najmanji rizik na popisu, i namjerno.

## Tri stvari koje vrijedi napraviti odmah

1. Noćna kopija `hub.db` na drugi disk (točka 1) — Task Scheduler, jedan redak.
2. Push u Git nakon svakog dana rada (točka 12).
3. Corpus uzorak kao „dimni test“ prije svake nadogradnje bNesta, bSolida ili Corpusa (točke 5 i 6) — `py -m hub.nalozi.provjera --db hub.db --nalozi ..\05_NALOZI_ZA_TEST --obrisi`.
