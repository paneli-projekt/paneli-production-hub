# -*- coding: utf-8 -*-
"""Uvoz šifrarnika u Hub bazu — jedna naredba, idempotentna (može se ponavljati svaki dan nakon izvoza iz Pantheona).

    py -m hub.sifrarnici.uvoz --db hub.db --pantheon ..\\..\\ph_identi.csv --winstore ..\\04_STROJEVI\\NESTING\\11092026.XML --kupci ..\\..\\ph_subjekti.csv --poste ..\\..\\ph_poste.csv

Redoslijed: Pantheon identi → materijali i trake → ispravci ureda (D-51: debljina, „ne koristi se“, ručne Winstore veze) → aliasi (kopija alias.csv iz skilla krojna-ponuda, zadano) i potvrđeni parovi
iz ponuda → Winstore XML (povezivanje kodova) → zadane trake po materijalu (po nazivu) → kupci (ph_subjekti.csv); ukupno ≈ 5 s. Ispisuje statistiku i nepovezane
Winstore kodove. Ponovni uvoz ne briše ono što je čovjek potvrdio (aliasi, zadane trake).
"""
import argparse
import os
import sys

from .. import db
from . import pantheon, winstore, aliasi, ispravci

# kopija references/alias.csv iz skilla krojna-ponuda (369 ručno provjerenih parova, kolovoz 2026) — koristi se ako --alias nije zadan
ALIAS_ZADANI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "podaci", "alias_krojna_ponuda.csv")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Uvoz šifrarnika (Pantheon identi, Winstore ploče, aliasi) u Hub bazu")
    ap.add_argument("--db", default=None, help="putanja SQLite baze (zadano: HUB_DB ili ./hub.db)")
    ap.add_argument("--pantheon", help="ph_identi.csv (IzvozPantheon_v2.ps1)")
    ap.add_argument("--winstore", help="Winstore XML izvoz inventara")
    ap.add_argument("--alias", help="alias.csv (pw_naziv,ident); zadano: hub/sifrarnici/podaci/alias_krojna_ponuda.csv")
    ap.add_argument("--kupci", help="ph_subjekti.csv (kupci iz Pantheona, korak 2)")
    ap.add_argument("--poste", help="ph_poste.csv (nazivi mjesta uz kupce)")
    ap.add_argument("--ispravci", nargs="?", const=ispravci.ZADANI_CSV, default=ispravci.ZADANI_CSV,
                    help="odluke ureda o šifrarniku (D-51); zadano: hub/sifrarnici/podaci/ispravci_sifrarnika.csv")
    ap.add_argument("--bez-ispravaka", dest="ispravci", action="store_const", const=None, help="ne primjenjuj ispravke ureda")
    ap.add_argument("--bez-aliasa", action="store_true", help="ne uvozi alias.csv")
    ap.add_argument("--bez-zadanih-traka", action="store_true", help="ne izvodi zadane trake po nazivu")
    ap.add_argument("--detaljno", action="store_true", help="ispiši sve nepovezane Winstore kodove i dodatne kodove")
    ap.add_argument("--tko", default="uvoz")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")      # Windows konzola bez UTF-8: ne rušiti se na znaku koji se ne može ispisati
    conn = db.spoji(a.db)
    if a.pantheon:
        st = pantheon.uvezi_pantheon(conn, a.pantheon, a.tko)
        print("Pantheon: %(identi)d identa, %(materijali)d materijala (%(novi_materijali)d novih, %(izbaceni_materijali)d izbačenih), "
              "%(trake)d traka (%(nove_trake)d novih, %(izbacene_trake)d izbačenih)" % st)
    alias = a.alias or (ALIAS_ZADANI if os.path.exists(ALIAS_ZADANI) else None)
    if alias and not a.bez_aliasa:
        st = aliasi.uvezi_alias_csv(conn, alias, a.tko)
        print("Aliasi: %d materijala, %d traka, %d nepoznatih identa" % (st["materijali"], st["trake"], len(st["nepoznati"])))
        for al, ident in st["nepoznati"][:10]:
            print("   nepoznat ident %s za alias '%s'" % (ident, al))
    if a.ispravci:
        n, presk = ispravci.ucitaj_csv(conn, a.ispravci, a.tko)
        st = ispravci.primijeni(conn, a.tko)
        print("Ispravci ureda (%d): debljina %d (+%d umjesto naziva), ne koristi se %d, Winstore kod %d"
              % (n, st["debljina"], st["debljina_umjesto_naziva"], st["ne_koristi_se"], st["winstore_kod"]))
        for x in ispravci.naziv_ispravljen(conn):
            print("   ispravak vise nije potreban: %s - naziv u Pantheonu sada kaze %s mm" % (x["ident"], x["debljina"]))
        for vrsta, kljuc, vrij in st["nepoznati"]:
            print("   nepoznat ident: %s %s -> %s" % (vrsta, kljuc, vrij))
    for opis, d, n in pantheon.primijeni_zadane_debljine(conn, a.tko):
        print("Zadana debljina po vrsti: %-12s %s mm -> %d materijala" % (opis, d, n))
    n = aliasi.upisi_potvrdjene(conn, a.tko)
    print("Potvrđene zadane trake iz ponuda: %d" % n)
    if a.winstore:
        st = winstore.uvezi_winstore(conn, a.winstore, a.tko)
        print("Winstore: %d stavki, %d kodova; povezano %d novih%s + %d otprije + %d dodatnih kodova istog materijala; nepovezano %d"
              % (st["stavke"], st["kodova"], st["povezano"], (" (%s)" % ", ".join("%s %d" % kv for kv in sorted(st["po_razini"].items()))) if st["povezano"] else "",
                 st["vec_povezano"], len(st["dodatni"]), len(st["nepovezano"])))
        sa_stanjem = [x for x in st["nepovezano"] if x[3]]
        bez_stanja = len(st["nepovezano"]) - len(sa_stanjem)
        if sa_stanjem:
            print("   nepovezani kodovi SA STANJEM (ploce su na skladistu, a nemaju ident):")
            for kod, opis, zasto, kom in sorted(sa_stanjem, key=lambda x: -x[3]):
                print("   %-16s %-44s %3d kom   %s" % (kod, opis[:44], kom, zasto if a.detaljno else ""))
        if bez_stanja:
            print("   + %d kodova bez stanja (stari dekori, ambalaza) — popis s --detaljno; nalazi su u dokumentu 11 §5.2" % bez_stanja)
        if a.detaljno:
            for kod, ident, prvi in st["dodatni"]:
                print("   dodatni kod %-14s -> %s (materijal pamti %s)" % (kod, ident, prvi))
            for kod, opis, zasto, kom in st["nepovezano"]:
                if not kom:
                    print("   %-16s %-44s %s" % (kod, opis[:44], zasto))
    if a.ispravci:
        for x in ispravci.neslaganje_debljine(conn):
            print("PAZI: kod %s je u Winstoreu %s mm, a ident %s (%s) je %s mm - uskladiti jedno od dvoje"
                  % (x["kod"], x["debljina_winstore"], x["ident"], x["naziv"][:40], x["debljina_identa"]))
    if not a.bez_zadanih_traka:
        up, bez = aliasi.izvedi_zadane_trake(conn, tko=a.tko)
        print("Zadane trake po nazivu: upisano %d, bez pogotka %d" % (up, bez))
    if a.kupci:
        from ..nalozi.kupci import uvezi_kupce
        st = uvezi_kupce(conn, a.kupci, a.poste, a.tko)
        print("Kupci: %(kupaca)d kupaca (%(novih)d novih, %(neaktivnih)d neaktivnih) od %(redova)d subjekata" % st)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
