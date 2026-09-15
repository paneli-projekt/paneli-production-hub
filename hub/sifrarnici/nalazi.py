# -*- coding: utf-8 -*-
"""Nalazi o šifrarniku za ispravak u Pantheonu (D-45): identi bez debljine, isti ident za dvije debljine, Winstore kodovi bez identa,
dvostruki identi (isti naziv dvaput). Čita samo Hub bazu (napunjenu `hub.sifrarnici.uvoz`) i ništa ne mijenja.

    py -m hub.sifrarnici.nalazi --db hub.db --md ..\\20_ANALIZA\\13_nalazi_sifrarnika.md --csv ..\\20_ANALIZA\\13_identi_bez_debljine.csv

Pokrenuti ponovno nakon ispravaka u Pantheonu i novog uvoza — popis se skrati.
"""
import argparse
import csv
import sys

from .. import db

# Compact i zidne obloge: debljina im u Pantheonu redovito nije u nazivu, a NIJE ista za sve (compact 6 / 8 / 12 / 13, zidna 8 / 18),
# pa je Hub ne smije pogoditi — ured je kaže jednom po identu (D-51). Radne ploče i ploče stola rješava zadana debljina 38 mm (D-52).
VRSTE_POTVRDA = ("CP", "ZO")

P1 = "1 - isti ident za vise debljina"
P2 = "2 - ploce na stanju, debljina nepoznata"
P3 = "3 - koristi se, treba dopisati debljinu"
P4 = "4 - compact i zidne obloge, ured kaze debljinu"
P5 = "5 - ne koristi se"
REDOSLIJED = (P1, P2, P3, P4, P5)


def bez_debljine(conn):
    """Materijali bez debljine, razvrstani po tome koliko smetaju.

    Materijal se smatra "u upotrebi" ako ima potvrđen alias (iz ponuda / skilla krojna-ponuda), Winstore kod ili je već bio na nalogu.
    Ostali su uglavnom stari dekori i stavke koje nisu ploče (okov, masiv, profili) — ne treba ih dirati.
    """
    red = []
    for r in conn.execute(
            "SELECT m.id, m.pantheon_ident AS ident, m.naziv_pantheon AS naziv, m.vrsta, m.winstore_kod, "
            "(SELECT COUNT(DISTINCT w.debljina) FROM winstore_ploca w WHERE w.materijal_id = m.id AND w.ambalaza = 0) AS debljina_winstore, "
            "(SELECT GROUP_CONCAT(DISTINCT w.debljina) FROM winstore_ploca w WHERE w.materijal_id = m.id AND w.ambalaza = 0) AS debljine, "
            "(SELECT GROUP_CONCAT(DISTINCT w.materijal_kod) FROM winstore_ploca w WHERE w.materijal_id = m.id AND w.ambalaza = 0) AS kodovi, "
            "(SELECT COALESCE(SUM(w.kom_ukupno), 0) FROM winstore_ploca w WHERE w.materijal_id = m.id AND w.ambalaza = 0 AND w.drop_ploca = 0) AS kom, "
            "(SELECT COUNT(*) FROM materijal_alias a WHERE a.materijal_id = m.id) AS aliasa, "
            "(SELECT COUNT(*) FROM nalog_materijal nm WHERE nm.materijal_id = m.id) AS na_nalozima "
            "FROM materijal m WHERE m.debljina IS NULL AND m.aktivan = 1 AND m.ne_koristi_se = 0 ORDER BY m.pantheon_ident"):
        d = dict(r)
        d["koristi_se"] = bool(d["aliasa"] or d["na_nalozima"] or d["kodovi"])
        if (d["debljina_winstore"] or 0) > 1:
            d["prioritet"] = P1
        elif d["kom"]:
            d["prioritet"] = P2
        elif d["vrsta"] in VRSTE_POTVRDA:
            d["prioritet"] = P4
        elif d["koristi_se"]:
            d["prioritet"] = P3
        else:
            d["prioritet"] = P5
        red.append(d)
    return sorted(red, key=lambda x: (REDOSLIJED.index(x["prioritet"]), x["vrsta"] or "", x["ident"]))


def winstore_bez_identa(conn):
    """Kodovi iz zadnjeg Winstore izvoza koji nemaju Pantheon ident (ambalaža se ne broji, D-49)."""
    return [dict(r) for r in conn.execute(
        "SELECT materijal_kod AS kod, MAX(opis) AS opis, MAX(debljina) AS debljina, SUM(CASE WHEN drop_ploca = 0 THEN kom_ukupno ELSE 0 END) AS kom, "
        "SUM(CASE WHEN drop_ploca = 1 THEN kom_ukupno ELSE 0 END) AS ostataka FROM winstore_ploca "
        "WHERE materijal_id IS NULL AND ambalaza = 0 GROUP BY materijal_kod ORDER BY kom DESC, materijal_kod")]


def dvostruki(conn, tablica="materijal", stupac="naziv_pantheon"):
    """Dva identa s istim nazivom (npr. dvije 'ABS 1/22 CRNA MAT') — pri prepoznavanju uvijek traže potvrdu."""
    return [dict(r) for r in conn.execute(
        "SELECT UPPER(%s) AS naziv, COUNT(*) AS n, GROUP_CONCAT(pantheon_ident) AS identi FROM %s WHERE aktivan = 1 "
        "GROUP BY UPPER(%s) HAVING n > 1 ORDER BY naziv" % (stupac, tablica, stupac))]


def ambalaza(conn):
    r = conn.execute("SELECT COUNT(DISTINCT materijal_kod) AS kodova, SUM(kom_ukupno) AS kom FROM winstore_ploca WHERE ambalaza = 1").fetchone()
    return dict(r)


def sazetak(conn):
    bd = bez_debljine(conn)
    return dict(bez_debljine=bd, po_prioritetu={p: sum(1 for x in bd if x["prioritet"] == p) for p in REDOSLIJED},
                winstore_bez_identa=winstore_bez_identa(conn), dvostruki_materijali=dvostruki(conn),
                dvostruke_trake=dvostruki(conn, "traka", "naziv"), ambalaza=ambalaza(conn),
                materijala=conn.execute("SELECT COUNT(*) FROM materijal WHERE aktivan = 1 AND ne_koristi_se = 0").fetchone()[0],
                ispravci=[dict(r) for r in conn.execute("SELECT vrsta, kljuc, vrijednost, napomena FROM sifrarnik_ispravak ORDER BY vrsta, kljuc")],
                neslaganje=_neslaganje(conn), suvisni=_suvisni(conn))


def _suvisni(conn):
    from .ispravci import naziv_ispravljen
    try:
        return naziv_ispravljen(conn)
    except Exception:
        return []


def _neslaganje(conn):
    from .ispravci import neslaganje_debljine
    try:
        return neslaganje_debljine(conn)
    except Exception:
        return []


def _tablica(redovi, zaglavlje, red_fn):
    return ["| " + " | ".join(zaglavlje) + " |", "|" + "---|" * len(zaglavlje)] + [red_fn(x) for x in redovi]


def markdown(s):
    p = {k: [x for x in s["bez_debljine"] if x["prioritet"] == k] for k in REDOSLIJED}
    L = ["# Nalazi o šifrarniku — što ispraviti u Pantheonu (D-45)", "",
         "Generirano iz Hub baze (`py -m hub.sifrarnici.nalazi`), bez ikakve izmjene podataka.",
         "Hub radi i **bez** ovih ispravaka — sve što ne prepozna sigurno, pita na ekranu. Ispravci samo smanjuju broj pitanja uredu.", "",
         "**Ukratko:** od %d aktivnih materijala %d nema debljinu, a u Pantheonu stvarno treba dirati samo **%d identa** (1.1 + 1.3);"
         % (s["materijala"], len(s["bez_debljine"]), len(p[P1]) + len(p[P3])),
         ("uz to %s iz 1.4 gdje ured kaže debljinu; ostalo su stari dekori koji se ne koriste."
          % ("još %d compact / zidnih obloga" % len(p[P4]) if len(p[P4]) > 1 else "još jedan ident")) if p[P4]
         else "compact i zidne obloge su riješeni; ostalo su stari dekori koji se ne koriste.", "",
         "| Prioritet | Identa | Što napraviti |", "|---|---|---|",
         "| %s | %d | razdvojiti u dva identa (vidi 1.1) |" % (P1, len(p[P1])),
         "| %s | %d | dopisati debljinu (vidi 1.2) |" % (P2, len(p[P2])),
         "| %s | %d | dopisati debljinu u naziv (vidi 1.3) |" % (P3, len(p[P3])),
         "| %s | %d | upisati debljinu u Hub (vidi 1.4) |" % (P4, len(p[P4])),
         "| %s | %d | ništa — stari dekori i stavke koje nisu ploče |" % (P5, len(p[P5])), "",
         "## 1. Identi bez debljine", ""]
    if s["ispravci"]:
        L = L[:-2] + ["## 0. Što je ured već riješio u Hubu (%d)" % len(s["ispravci"]), "",
                      "Ove odluke žive u Hubu (`py -m hub.sifrarnici.ispravci`) i preživljavaju svaki novi uvoz — Pantheon ih ne mora imati.", ""]
        L += _tablica(s["ispravci"], ["Što", "Ident / kod", "Vrijednost", "Napomena"],
                      lambda x: "| %s | %s | %s | %s |" % (x["vrsta"], x["kljuc"], x["vrijednost"] or "", x["napomena"] or ""))
        if s["suvisni"]:
            L += ["", "Sljedeći ispravci `debljina_umjesto_naziva` više nisu potrebni — naziv u Pantheonu sada govori isto, pa se mogu obrisati:", ""]
            L += ["- `%s` (%s mm) — %s" % (x["ident"], x["debljina"], x["naziv"]) for x in s["suvisni"]]
        L += ["", "## 1. Identi bez debljine", ""]
    L += [
         "### 1.1 Isti ident za više debljina (%d)" % len(p[P1]), "",
         "Kad naziv nema debljinu, Hub je preuzima iz Winstorea. Kad Winstore za isti ident ima dvije, Hub ne zna koja je ploča koja",
         "— ne može ni izračunati broj ploča ni cijenu. Rješenje je dvoje: ured u Hubu kaže koja je debljina prava (D-51),",
         "ili se u Pantheonu naprave dva identa (`… 18` i `… 25`) pa se Winstore kodovi, koji već nose debljinu, povežu sami.", ""]
    L += (_tablica(p[P1], ["Ident", "Naziv u Pantheonu", "Winstore kodovi", "Debljine", "Na stanju"],
                   lambda x: "| %s | %s | %s | %s | %s kom |" % (x["ident"], x["naziv"], x["kodovi"] or "—", x["debljine"] or "—", x["kom"]))
          if p[P1] else ["Nema — nijedan ident više nema dvije debljine u Winstoreu."])
    L += ["", "### 1.2 Ploče na stanju bez poznate debljine (%d)" % len(p[P2]), ""]
    if p[P2]:
        L += _tablica(p[P2], ["Ident", "Naziv", "Winstore kod", "Na stanju"],
                      lambda x: "| %s | %s | %s | %s kom |" % (x["ident"], x["naziv"], x["kodovi"] or "—", x["kom"]))
    else:
        L.append("Nema — svaki materijal koji ima ploče na skladištu ima i debljinu (iz naziva ili iz Winstorea).")
    L += ["", "### 1.3 Koriste se, a nemaju debljinu (%d)" % len(p[P3]), "",
          "Ovi identi dolaze na ponude (imaju potvrđen alias iz ponuda) ili su bili na nalozima, ali im debljina nije u nazivu.",
          "Hub ih prepozna i radi dalje, ali debljinu mora uzeti iz datoteke naloga ili pitati ured. Dopisivanje debljine u naziv",
          "(npr. `IVERAL ZELENI 021 18`) briše to pitanje zauvijek.", ""]
    L += _tablica(p[P3], ["Ident", "Naziv u Pantheonu", "Vrsta", "Gdje se koristi"],
                  lambda x: "| %s | %s | %s | %s |" % (x["ident"], x["naziv"], x["vrsta"],
                                                       ", ".join(t for t in ("%d alias" % x["aliasa"] if x["aliasa"] else "",
                                                                             "%d put na nalogu" % x["na_nalozima"] if x["na_nalozima"] else "",
                                                                             "Winstore %s" % x["kodovi"] if x["kodovi"] else "") if t) or "—"))
    L += ["", "### 1.4 Compact i zidne obloge (%d) — ured kaže debljinu jednom" % len(p[P4]), "",
          "Radne ploče i ploče stola Hub zna sam (38 mm po pravilu). Compact i zidne obloge ne zna: u šifrarniku postoje",
          "compact ploče od 6, 8, 12 i 13 mm, a zidne od 8 i 18 mm, i to se iz naziva ne vidi. Ne pogađa se — Hub bi tada",
          "krivo izračunao i broj ploča i cijenu.", "",
          "Uz ovaj dokument ide obrazac **`13_compact_i_zidne_debljine.csv`**: ured upiše broj u stupac `vrijednost`, a zatim",
          "`py -m hub.sifrarnici.ispravci --db hub.db --csv 13_compact_i_zidne_debljine.csv` sve upiše odjednom.",
          "Reci Pantheonu ili Hubu — svejedno; ako debljina uđe u naziv u Pantheonu, ima prednost.", ""]
    L += (_tablica(p[P4], ["Ident", "Naziv u Pantheonu", "Vrsta", "Debljina?"],
                   lambda x: "| %s | %s | %s |  |" % (x["ident"], x["naziv"], x["vrsta"]))
          if p[P4] else ["Nema — ured je debljinu rekao za sve compact ploče i zidne obloge koje se koriste."])
    L += ["",
          "### 1.5 Ne koriste se (%d) — ne dirati" % len(p[P5]), "",
          "Stari dekori i stavke koje nisu ploče (masiv, profili, okov, lakirane fronte). Puni popis je u priloženom CSV-u.", "",
          "## 2. Winstore kodovi bez Pantheon identa (%d)" % len(s["winstore_bez_identa"]), "",
          "Kodovi iz Winstore izvoza koje Hub nije uspio spojiti ni s jednim identom. Ambalažne podloge se ne broje (D-49):",
          "%d kodova, %s ploča." % (s["ambalaza"]["kodova"] or 0, s["ambalaza"]["kom"] or 0), ""]
    sa, bez = [x for x in s["winstore_bez_identa"] if x["kom"] or x["ostataka"]], [x for x in s["winstore_bez_identa"] if not (x["kom"] or x["ostataka"])]
    L += ["### 2.1 Imaju stanje — ove riješiti (%d)" % len(sa), "",
          "Ploče fizički stoje na regalu, a Hub ih ne zna ni rezervirati ni potrošiti ni naplatiti: kad kupac naruči taj dekor,",
          "Hub će reći da ga nema. Tri su razloga i tri rješenja: (1) dekor postoji u Pantheonu, samo je kod drukčije zapisan",
          "→ upisati vezu u Hub (`--kod KOD=IDENT`) ili uskladiti kod u Winstoreu; (2) dekora nema u Pantheonu → otvoriti ident;",
          "(3) nije dekor nego stanje robe (`POVRAT OSTECENO`) → dogovoriti kako se vodi.", "",
          "Uz dokument ide obrazac **`13_winstore_kodovi_bez_identa.csv`**: operater nestinga uz regal upiše ident u stupac",
          "`vrijednost`, pa `py -m hub.sifrarnici.ispravci --db hub.db --csv 13_winstore_kodovi_bez_identa.csv` sve poveže odjednom.", ""]
    L += _tablica(sa, ["Kod", "Opis u Winstoreu", "Debljina", "Cijelih", "Ostataka"],
                  lambda x: "| %s | %s | %s | %s | %s |" % (x["kod"], x["opis"], x["debljina"] or "—", x["kom"], x["ostataka"]))
    L += ["", "### 2.2 Bez stanja (%d) — ne hitno" % len(bez), "",
          "Stari dekori koji su ostali u Winstore šifrarniku, a nema ih na skladištu. Smetaju tek ako se dekor ponovo naruči.", "",
          "<details><summary>Popis</summary>", ""]
    L += _tablica(bez, ["Kod", "Opis u Winstoreu", "Debljina"], lambda x: "| %s | %s | %s |" % (x["kod"], x["opis"], x["debljina"] or "—"))
    L += ["", "</details>"]
    if s["neslaganje"]:
        L += ["", "### 2.3 Debljina se ne slaže (%d)" % len(s["neslaganje"]), "",
              "Kod je povezan s identom, ali Winstore i Pantheon govore različitu debljinu — skladište i obračun bi se razišli.",
              "Ispraviti jedno od dvoje: kod u Winstoreu (npr. `…-25` → `…-26`) ili naziv identa u Pantheonu.", ""]
        L += _tablica(s["neslaganje"], ["Kod", "U Winstoreu", "Ident", "Naziv u Pantheonu", "Debljina identa"],
                      lambda x: "| %s | %s mm | %s | %s | %s mm |" % (x["kod"], x["debljina_winstore"], x["ident"], x["naziv"], x["debljina_identa"]))
    L += ["", "## 3. Dva identa s istim nazivom (%d materijala, %d traka)" % (len(s["dvostruki_materijali"]), len(s["dvostruke_trake"])), "",
          "Po nazivu se ne razlikuju, pa Hub kod njih uvijek traži potvrdu — ured mora izabrati ident ručno.",
          "Ako je jedan od dva neaktivan ili višak, zatvaranjem u Pantheonu pitanje nestaje.", ""]
    L += _tablica(s["dvostruki_materijali"] + s["dvostruke_trake"], ["Naziv", "Identi"],
                  lambda x: "| %s | %s |" % (x["naziv"], x["identi"]))
    L += ["", "## 4. Što napraviti, redom", "",
          "1. Razdvojiti %d identa iz 1.1 (to je jedino što Hub stvarno koči)." % len(p[P1]) if p[P1] else "1. ~~Isti ident za više debljina~~ — riješeno.",
          "2. Dopisati debljinu u naziv za %d identa iz 1.3." % len(p[P3]) if p[P3] else "2. ~~Identi bez debljine koji se koriste~~ — riješeno.",
          "3. Popuniti debljinu za %d iz 1.4 (obrazac `13_compact_i_zidne_debljine.csv`)." % len(p[P4]) if p[P4]
          else "3. ~~Compact i zidne obloge~~ — riješeno.",
          "4. Riješiti %d Winstore kodova sa stanjem iz 2.1 (upisati kod na ident ili otvoriti ident)." % len(sa)
          if sa else "4. ~~Winstore kodovi sa stanjem~~ — riješeno.",
          "4b. Uskladiti debljinu za %d koda iz 2.3." % len(s["neslaganje"]) if s["neslaganje"] else None,
          "5. Ako je lako: zatvoriti višak od dva istoimena identa iz 3.", "",
          "Ostalo (1.5, 2.2) ne dirati — stari dekori i stavke koje nisu ploče.", "",
          "Kad je ispravljeno, novi izvoz iz Pantheona i Winstorea pa:", "",
          "```", "py -m hub.sifrarnici.uvoz --db hub.db --pantheon ph_identi.csv --winstore <XML>",
          "py -m hub.sifrarnici.nalazi --db hub.db --md 13_nalazi_sifrarnika.md --csv 13_identi_bez_debljine.csv", "```", "",
          "Popisi u ovom dokumentu se tada skrate; kad su 1.1, 1.3, 1.4 i 2.1 prazni, šifrarnik je čist.",
          "Hub do tada radi normalno — sve nejasno završi na popisu „za potvrdu“ i ured odluči jednom, pa Hub zapamti.", ""]
    return "\n".join(x for x in L if x is not None) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Nalazi o šifrarniku (identi bez debljine, Winstore kodovi bez identa, dvostruki nazivi)")
    ap.add_argument("--db")
    ap.add_argument("--md", help="spremi Markdown izvještaj")
    ap.add_argument("--csv", help="spremi popis identa bez debljine (za Excel / ispravak u Pantheonu)")
    ap.add_argument("--obrazac", help="spremi obrazac za ured: compact i zidne obloge, prazan stupac 'vrijednost' (učitava ga hub.sifrarnici.ispravci --csv)")
    ap.add_argument("--obrazac-kodovi", help="spremi obrazac za operatera nestinga: Winstore kodovi sa stanjem bez identa, prazan stupac 'vrijednost'")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    s = sazetak(conn)
    print("Identi bez debljine: %d od %d aktivnih materijala" % (len(s["bez_debljine"]), s["materijala"]))
    for p in REDOSLIJED:
        print("   %-46s %d" % (p, s["po_prioritetu"][p]))
    print("Winstore kodovi bez identa: %d (ambalaza se ne broji: %s kodova)" % (len(s["winstore_bez_identa"]), s["ambalaza"]["kodova"]))
    print("Dva identa s istim nazivom: %d materijala, %d traka" % (len(s["dvostruki_materijali"]), len(s["dvostruke_trake"])))
    if a.md:
        open(a.md, "w", encoding="utf-8").write(markdown(s))
        print("Izvjestaj:", a.md)
    if a.csv:
        with open(a.csv, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["prioritet", "ident", "naziv", "vrsta", "koristi_se", "winstore_kodovi", "debljine_u_winstoreu", "na_stanju", "aliasa", "na_nalozima"])
            for x in s["bez_debljine"]:
                w.writerow([x["prioritet"], x["ident"], x["naziv"], x["vrsta"], "DA" if x["koristi_se"] else "",
                            x["kodovi"] or "", x["debljine"] or "", x["kom"], x["aliasa"], x["na_nalozima"]])
        print("CSV:", a.csv)
    if a.obrazac:
        red = [x for x in s["bez_debljine"] if x["prioritet"] in (P3, P4)]
        with open(a.obrazac, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["vrsta", "kljuc", "vrijednost", "napomena"])
            for x in red:
                w.writerow(["debljina", x["ident"], "", x["naziv"]])
        print("Obrazac za ured (%d redaka):" % len(red), a.obrazac)
    if a.obrazac_kodovi:
        red = [x for x in s["winstore_bez_identa"] if x["kom"] or x["ostataka"]]
        with open(a.obrazac_kodovi, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["vrsta", "kljuc", "vrijednost", "napomena"])
            for x in red:
                w.writerow(["winstore_kod", x["kod"], "", "%s | %s mm | %s cijelih, %s ostataka"
                            % (x["opis"], x["debljina"] or "?", x["kom"], x["ostataka"])])
        print("Obrazac za operatera nestinga (%d kodova):" % len(red), a.obrazac_kodovi)
    return 0


if __name__ == "__main__":
    sys.exit(main())
