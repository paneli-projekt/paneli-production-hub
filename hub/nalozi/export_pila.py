# -*- coding: utf-8 -*-
"""Izvoz naloga na pilu: optimizacija + CPO za Selco OSI (kralježnica korak 3, 04 §4).

Zamjenjuje ono što danas radi PanelWizard: iz naloga se po MATERIJALU složi shema rezanja (D-18/D-19) i napiše jedna
`.cpo` datoteka koju pila učita. Program dobiva Hubov broj `HUB_00001` (D-22) — vlastiti niz koji se ne sudara s PW-ovim
`I_` / `SA_` dok se radi paralelno.

    py -m hub.nalozi.export_pila --db hub.db --nalog 12 --mapa C:\\PILA
    py -m hub.nalozi.export_pila --db hub.db --nalog 12 --mapa . --suho

Kerf (D-21): slaganje i obračun idu po kerfu naloga (zadano 16 mm, kao PW „Podesi alat"), a u samu CPO datoteku se
upisuje fizički kerf pile 5,00 — na pilu ide ISTA shema po kojoj je obračunato.
Način optimizacije bira Hub po D-19 (materijal s godom samo uzdužno, bez goda i poprečno; pobjeđuje najmanja površina
za naplatu) i zapiše koji je pobijedio.
"""
import argparse
import json
import os
import sys

from .. import db
from ..db import sada, dnevnik, postavka, postavi
from ..formati import cpo_rw
from ..optimizacija import pila_optimizator as OPT
from . import nalozi as N
from .export_nesting import ExportGreska, _bez_dij, _po_materijalu

MAPA = "PILA"
PREFIKS = "HUB_"
PLOCA = (2800, 2070)        # standardna ploča (02 §1); materijal s vlastitom mjerom je nadjačava
TRIM = 10                   # obrez sa svih strana
KERF_PILE = 5.0             # fizički kerf koji ide u CPO (D-21)


def novi_program(conn):
    """Sljedeći broj programa pile iz brojača (`postavke.brojac_pila`) — Hubov niz HUB_00001 (D-22)."""
    n = int(postavka(conn, "brojac_pila", "0") or 0) + 1
    postavi(conn, "brojac_pila", str(n), "zadnji dodijeljeni broj programa pile (D-22)")
    return "%s%05d" % (PREFIKS, n)


def _ploca(m):
    L = m["ploca_L"] or m["m_ploca_L"] or PLOCA[0]
    W = m["ploca_W"] or m["m_ploca_W"] or PLOCA[1]
    return (float(L), float(W))


def izvezi(conn, nalog_id, mapa, tko="web", samo_pila=True, suho=False, vrijeme=None, zapisi_optimizaciju=True):
    """Složi i napiši `.cpo` za svaki materijal naloga koji ide na pilu, u `<mapa>/<NAZIV NALOGA>/PILA/`.

    samo_pila: preskoči materijale koje je voditelj poslao na nesting (`put = 'nesting'`).
    suho: složi i izračunaj, ali ne piši ni datoteku ni u bazu (to je ono što ekran pokazuje prije slanja na pilu).
    """
    n = N.nalog(conn, nalog_id)
    els = N.elementi_za_export(conn, nalog_id)
    if not els:
        raise ExportGreska("nalog %s nema elemenata" % n["naziv"])
    kerf_naloga = float(n["kerf"] or 16)
    korijen = os.path.join(mapa, n["naziv"], MAPA)
    paketi, preskoceno = [], []
    for nm_id, grupa in _po_materijalu(els):
        m = N.materijal_naloga(conn, nm_id)
        ime_m = m["naziv_kratki"] or m["naziv_ulaz"] or ""
        if samo_pila and (m["put"] or "") == "nesting":
            preskoceno.append(dict(materijal=ime_m, razlog="ide na nesting", elemenata=len(grupa)))
            continue
        if not grupa[0]["deb"]:
            preskoceno.append(dict(materijal=ime_m, razlog="nepoznata debljina", elemenata=len(grupa)))
            continue
        for e in grupa:
            e["mat"] = _bez_dij(e["mat"])
        prog = "HUB_SUHO" if suho else novi_program(conn)
        bajtovi, st, greske, oc, nacin = OPT.napravi_cpo(
            grupa, prog, n["kupac_naziv"] or n["naziv"], material=grupa[0]["mat"], ploca=_ploca(m), trim=TRIM,
            kerf=KERF_PILE, when=vrijeme, kerf_slaganja=kerf_naloga)
        if greske:
            raise ExportGreska("shema za %s nije valjana: %s" % (ime_m, "; ".join(greske[:3])))
        put = os.path.join(korijen, prog + ".cpo")
        p = dict(nalog_materijal_id=nm_id, materijal=grupa[0]["mat"], ident=m["ident"], debljina=grupa[0]["deb"],
                 program=prog, elemenata=len(grupa), komada=sum(x["kom"] for x in grupa), cpo=put, nacin=nacin,
                 ploca=st["ploca"], m2_dijelova=st["m2_dijelova"], m2_za_naplatu=oc["m2_naplata"],
                 iskoristenje=st["iskoristenje"], rezova=sum(len(x["cuts"]) for x in cpo_rw.parse(bajtovi)["pat"]),
                 bajtova=len(bajtovi))
        if not suho:
            os.makedirs(korijen, exist_ok=True)
            open(put, "wb").write(bajtovi)
            cur = conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, datum) VALUES (?, ?, ?, ?)",
                               (nalog_id, "cpo", put, sada()))
            if zapisi_optimizaciju:
                conn.execute("INSERT INTO optimizacija (nalog_materijal_id, engine, nacin, datum, broj_ploca, iskoristenje, "
                             "m2_dijelova, m2_ploca, m2_za_naplatu, rezova, sheme_json, dokument_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                             (nm_id, "hub", nacin, sada(), st["ploca"], st["iskoristenje"], st["m2_dijelova"],
                              st["m2_bruto"], oc["m2_naplata"], p["rezova"], json.dumps(dict(program=prog, kerf=kerf_naloga)), cur.lastrowid))
        paketi.append(p)
    if not paketi:
        raise ExportGreska("nema nijednog materijala za pilu (%s)"
                           % ("; ".join("%s: %s" % (x["materijal"], x["razlog"]) for x in preskoceno) or "nalog je prazan"))
    if not suho:
        dnevnik(conn, tko, "nalog", nalog_id, "izvoz_cpo",
                "%s: %d programa, %d ploca" % (n["naziv"], len(paketi), sum(x["ploca"] for x in paketi)))
        conn.execute("INSERT INTO dogadjaj (nalog_id, kada, tko_id, iz_statusa, u_status, razlog, veza) "
                     "VALUES (?, ?, (SELECT id FROM korisnik WHERE oznaka = ?), ?, ?, ?, ?)",
                     (nalog_id, sada(), tko, n["status"], n["status"],
                      "izvoz na pilu: %s" % ", ".join(x["program"] for x in paketi), "mapa:" + korijen))
        conn.commit()
    return dict(nalog=n["naziv"], mapa=korijen, kerf=kerf_naloga, paketi=paketi, preskoceno=preskoceno, suho=suho)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Izvoz naloga na pilu: optimizacija + CPO (korak 3, D-21/D-22)")
    ap.add_argument("--db")
    ap.add_argument("--nalog", type=int, required=True, help="id naloga")
    ap.add_argument("--mapa", default=".", help="korijen izvoza (nastaje <mapa>\\<NALOG>\\PILA\\)")
    ap.add_argument("--sve", action="store_true", help="izvezi i materijale koje je voditelj poslao na nesting")
    ap.add_argument("--suho", action="store_true", help="samo pokaži što bi nastalo, ne piši ništa")
    ap.add_argument("--tko", default="web")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    try:
        r = izvezi(conn, a.nalog, a.mapa, a.tko, samo_pila=not a.sve, suho=a.suho)
    except ExportGreska as e:
        print("GRESKA:", e)
        return 1
    print("%s%s -> %s   (kerf slaganja %s mm, u CPO ide %s)" % ("[suho] " if a.suho else "", r["nalog"], r["mapa"], r["kerf"], KERF_PILE))
    for p in r["paketi"]:
        print("   %-10s %-26s %4s mm  %3d el / %3d kom  %2d ploca  isk. %5.1f%%  naplata %7.2f m2  (%s)"
              % (p["program"], p["materijal"][:26], p["debljina"], p["elemenata"], p["komada"], p["ploca"],
                 100 * (p["iskoristenje"] or 0), p["m2_za_naplatu"], p["nacin"]))
        print("      %s   %d rezova" % (os.path.basename(p["cpo"]), p["rezova"]))
    for x in r["preskoceno"]:
        print("   preskoceno: %-26s %s (%d el.)" % ((x["materijal"] or "?")[:26], x["razlog"], x["elemenata"]))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
