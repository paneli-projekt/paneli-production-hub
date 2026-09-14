# -*- coding: utf-8 -*-
"""Uvoz šifrarnika u Hub bazu — jedna naredba, idempotentna (može se ponavljati svaki dan nakon izvoza iz Pantheona).

    py -m hub.sifrarnici.uvoz --db hub.db --pantheon ..\\..\\ph_identi.csv --winstore ..\\04_STROJEVI\\NESTING\\11092026.XML --kupci ..\\..\\ph_subjekti.csv --poste ..\\..\\ph_poste.csv

Redoslijed: Pantheon identi → materijali i trake → aliasi (kopija alias.csv iz skilla krojna-ponuda, zadano) i potvrđeni parovi
iz ponuda → Winstore XML (povezivanje kodova) → zadane trake po materijalu (po nazivu) → kupci (ph_subjekti.csv); ukupno ≈ 5 s. Ispisuje statistiku i nepovezane
Winstore kodove. Ponovni uvoz ne briše ono što je čovjek potvrdio (aliasi, zadane trake).
"""
import argparse
import os
import sys

from .. import db
from . import pantheon, winstore, aliasi

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
    ap.add_argument("--bez-aliasa", action="store_true", help="ne uvozi alias.csv")
    ap.add_argument("--bez-zadanih-traka", action="store_true", help="ne izvodi zadane trake po nazivu")
    ap.add_argument("--tko", default="uvoz")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")      # Windows konzola bez UTF-8: ne rušiti se na znaku koji se ne može ispisati
    conn = db.spoji(a.db)
    if a.pantheon:
        st = pantheon.uvezi_pantheon(conn, a.pantheon, a.tko)
        print("Pantheon: %(identi)d identa, %(materijali)d materijala (%(novi_materijali)d novih), %(trake)d traka (%(nove_trake)d novih)" % st)
    alias = a.alias or (ALIAS_ZADANI if os.path.exists(ALIAS_ZADANI) else None)
    if alias and not a.bez_aliasa:
        st = aliasi.uvezi_alias_csv(conn, alias, a.tko)
        print("Aliasi: %d materijala, %d traka, %d nepoznatih identa" % (st["materijali"], st["trake"], len(st["nepoznati"])))
        for al, ident in st["nepoznati"][:10]:
            print("   nepoznat ident %s za alias '%s'" % (ident, al))
    n = aliasi.upisi_potvrdjene(conn, a.tko)
    print("Potvrđene zadane trake iz ponuda: %d" % n)
    if a.winstore:
        st = winstore.uvezi_winstore(conn, a.winstore, a.tko)
        print("Winstore: %d stavki, %d kodova, povezano %d (%s) + %d već povezano, nepovezano %d" % (st["stavke"], st["kodova"], st["povezano"],
              ", ".join("%s %d" % kv for kv in sorted(st["po_razini"].items())), st["vec_povezano"], len(st["nepovezano"])))
        for kod, ident, prvi in st["dodatni"]:
            print("   dodatni kod %-14s -> %s (materijal pamti %s)" % (kod, ident, prvi))
        for kod, opis, zasto in st["nepovezano"]:
            print("   %-16s %-44s %s" % (kod, opis[:44], zasto))
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
