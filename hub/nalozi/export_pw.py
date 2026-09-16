# -*- coding: utf-8 -*-
"""Izvoz naloga u CPW za PanelWizard (kralježnica korak 3, 04 §4; paralelni rad D-11).

PanelWizard ostaje "motor" pile i radi obračun dok Hub ne preuzme oboje. Da se može voziti paralelno — isti nalog kroz
Hub i kroz PW, pa usporediti — Hub piše istu CPW datoteku koju je dosad pisao PPNEST, u istu mapu `<NALOG>\\PANEL WIZARD\\`.

    py -m hub.nalozi.export_pw --db hub.db --nalog 9 --mapa C:\\PPNESTING
    py -m hub.nalozi.export_pw --db hub.db --nalog 9 --mapa . --suho

Za razliku od nestinga (`export_nesting`) ovdje se izvoze SVI materijali naloga, i oni koje voditelj šalje na nesting —
PW radi obračun za cijeli nalog, ne samo za ono što ide na pilu.

Materijal je u CPW-u slobodan tekst (02 §3.1) — PW ga ne traži u svom šifrarniku. Hub zato piše svoj kratki naziv
(`IV_BIJELI_NK_18`), pa ista ploča uvijek daje isto ime datoteke bez obzira kako ju je kupac napisao; PPNEST je pisao
tekst kakav je stigao (`IV_BIJELI_NK_18_MM`).
"""
import argparse
import os
import sys

from .. import db
from ..db import sada, dnevnik
from ..formati import nalog_io
from . import nalozi as N
from .export_nesting import ExportGreska, _bez_dij, _po_materijalu, _dogadjaj_izvoza, uz_rollback

MAPA = "PANEL WIZARD"


@uz_rollback
def izvezi(conn, nalog_id, mapa, tko="web", header_once=False, samo_pila=False, suho=False, vrijeme=None):
    """Napiši po jednu CPW datoteku za svaki materijal naloga u `<mapa>/<NAZIV NALOGA>/PANEL WIZARD/`.

    header_once: False (zadano) ponavlja FORMAT/MATERIJAL ispred svakog elementa — točno kao PPNEST; True piše zaglavlje
                 jednom (uredniji zapis, PW prihvaća oboje, 05 §2).
    samo_pila:   izvezi samo ono što ide na pilu (za slučaj da se PW koristi još samo kao optimizator pile).
    suho:        samo izračunaj što bi nastalo, ne diraj disk ni bazu.
    """
    n = N.nalog(conn, nalog_id)
    els = N.elementi_za_export(conn, nalog_id)
    if not els:
        raise ExportGreska("nalog %s nema elemenata" % n["naziv"])
    zig = (vrijeme or __import__("datetime").datetime.now()).strftime("%d%m%y_%H%M%S")
    korijen = os.path.join(mapa, n["naziv"], MAPA)
    paketi, preskoceno = [], []
    for nm_id, grupa in _po_materijalu(els):
        m = N.materijal_naloga(conn, nm_id)
        if samo_pila and (m["put"] or "") != "pila":
            preskoceno.append(dict(materijal=m["naziv_kratki"] or m["naziv_ulaz"], razlog="ne ide na pilu", elemenata=len(grupa)))
            continue
        deb = grupa[0]["deb"]
        if not deb:
            preskoceno.append(dict(materijal=m["naziv_kratki"] or m["naziv_ulaz"], razlog="nepoznata debljina", elemenata=len(grupa)))
            continue
        for e in grupa:
            e["mat"] = _bez_dij(e["mat"])
        put = os.path.join(korijen, "%s_%s_%s.CPW" % (_bez_dij(n["naziv"]), grupa[0]["mat"], zig))
        p = dict(nalog_materijal_id=nm_id, materijal=grupa[0]["mat"], ident=m["ident"], debljina=deb,
                 elemenata=len(grupa), komada=sum(x["kom"] for x in grupa),
                 m2=round(sum(x["L"] * x["W"] * x["kom"] for x in grupa) / 1e6, 3),
                 cpw=put, put_naloga=m["put"] or "", nepotvrden=not m["materijal_id"])
        if not suho:
            os.makedirs(korijen, exist_ok=True)
            nalog_io.write_cpw(grupa, put, header_once=header_once)
            conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, datum) VALUES (?, ?, ?, ?)",
                         (nalog_id, "cpw", put, sada()))
        paketi.append(p)
    if not paketi:
        raise ExportGreska("nema nijednog materijala za PanelWizard (%s)"
                           % ("; ".join("%s: %s" % (x["materijal"], x["razlog"]) for x in preskoceno) or "nalog je prazan"))
    if not suho:
        dnevnik(conn, tko, "nalog", nalog_id, "izvoz_cpw",
                "%s: %d datoteka, %d elemenata" % (n["naziv"], len(paketi), sum(x["elemenata"] for x in paketi)))
        _dogadjaj_izvoza(conn, n, tko, "izvoz za PanelWizard: %d datoteka" % len(paketi), "mapa:" + korijen)
        conn.commit()
    return dict(nalog=n["naziv"], mapa=korijen, paketi=paketi, preskoceno=preskoceno, suho=suho)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Izvoz naloga u CPW za PanelWizard (korak 3, D-11)")
    ap.add_argument("--db")
    ap.add_argument("--nalog", type=int, required=True, help="id naloga")
    ap.add_argument("--mapa", default=".", help="korijen izvoza (nastaje <mapa>\\<NALOG>\\PANEL WIZARD\\)")
    ap.add_argument("--samo-pila", action="store_true", help="izvezi samo materijale koji idu na pilu")
    ap.add_argument("--zaglavlje-jednom", action="store_true", help="FORMAT/MATERIJAL jednom umjesto ispred svakog elementa")
    ap.add_argument("--suho", action="store_true", help="samo pokaži što bi nastalo, ne piši ništa")
    ap.add_argument("--tko", default="web")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    try:
        r = izvezi(conn, a.nalog, a.mapa, a.tko, header_once=a.zaglavlje_jednom, samo_pila=a.samo_pila, suho=a.suho)
    except ExportGreska as e:
        print("GRESKA:", e)
        return 1
    print("%s%s -> %s" % ("[suho] " if a.suho else "", r["nalog"], r["mapa"]))
    for p in r["paketi"]:
        print("   %-28s %4s mm  %3d el / %3d kom  %7.2f m2   %s%s"
              % (p["materijal"][:28], p["debljina"], p["elemenata"], p["komada"], p["m2"],
                 os.path.basename(p["cpw"]), "   PAZI: materijal nije potvrden" if p["nepotvrden"] else ""))
    for x in r["preskoceno"]:
        print("   preskoceno: %-28s %s (%d el.)" % ((x["materijal"] or "?")[:28], x["razlog"], x["elemenata"]))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
