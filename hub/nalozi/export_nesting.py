# -*- coding: utf-8 -*-
"""Izvoz naloga na nesting: CSV + CIX za bNest (kralježnica korak 3, 04 §4).

Zamjenjuje ono što danas radi PPNEST: iz naloga po MATERIJALU nastaje jedna CSV lista elemenata (28 stupaca, isti profil
koji bNest već čita) i jedna CIX datoteka po elementu. Mape su kao dosad — `<mapa>/<NALOG>/NESTING/`.

    py -m hub.nalozi.export_nesting --db hub.db --nalog 12 --mapa C:\\PPNESTING
    py -m hub.nalozi.export_nesting --db hub.db --nalog 12 --mapa . --stil ppnest --suho

Dvije stvari koje Hub radi, a PPNEST nije:
  * **ime CIX datoteke je jedinstveno zauvijek** (D-23) — bNest datoteku s istim imenom pregazi bez pitanja, a to se već
    dogodilo. Hub imena dijeli iz brojača i upisuje ih u `cix_registar`; ime se ne oslobađa ni kad se element obriše.
  * **SIFRA MAT je Winstore kod** iz šifrarnika (D-24), ne prepisani tekst — pa bNest nađe ploču bez ručnog mapiranja.

Element koji već ima CIX ime (npr. iz Corpusa, D-55) zadržava svoje — Hub ga samo registrira i proslijedi.
"""
import argparse
import os
import sys

from .. import db
from ..db import sada, dnevnik, postavka, postavi
from ..formati import nalog_io
from . import nalozi as N

PREFIKS = "H"          # Hubova imena: H0000001 — razlikuju se od PPNEST-ovih (ddmmyy_HHmmss) i Corpusovih (14 hex znamenki)


class ExportGreska(Exception):
    pass


def _bez_dij(s):
    return nalog_io.bez_dijakritika(s or "").upper().replace(" ", "_").replace("/", "_")


def registriraj(conn, ime, element_id=None, nalog_id=None, izvor="hub"):
    """Upiši ime u registar. Vraća False ako je ime već zauzeto DRUGIM elementom (D-23)."""
    r = conn.execute("SELECT element_id FROM cix_registar WHERE ime = ?", (ime,)).fetchone()
    if r:
        return r["element_id"] == element_id
    conn.execute("INSERT INTO cix_registar (ime, element_id, nalog_id, izvor, kada) VALUES (?, ?, ?, ?, ?)",
                 (ime, element_id, nalog_id, izvor, sada()))
    return True


def novo_ime(conn, element_id=None, nalog_id=None):
    """Sljedeće slobodno Hub ime iz brojača (`postavke.brojac_cix`), preskačući sve što je registar već vidio."""
    n = int(postavka(conn, "brojac_cix", "0") or 0)
    for _ in range(1000000):
        n += 1
        ime = "%s%07d" % (PREFIKS, n)
        if registriraj(conn, ime, element_id, nalog_id, "hub"):
            postavi(conn, "brojac_cix", str(n), "zadnje dodijeljeno ime CIX datoteke (D-23)")
            return ime
    raise ExportGreska("brojač CIX imena je pun")


def dodijeli_imena(conn, nalog_id, tko="web"):
    """Svakom elementu naloga bez CIX imena dodijeli novo i registriraj ga; postojeća imena samo registrira.
    Vraća (novih, registriranih_otprije)."""
    novo, staro = 0, 0
    for r in conn.execute(
            "SELECT e.id, e.cix_ime, e.cix_izvor FROM element e JOIN nalog_materijal nm ON nm.id = e.nalog_materijal_id "
            "WHERE nm.nalog_id = ? ORDER BY nm.rb, nm.id, e.rb, e.id", (nalog_id,)).fetchall():
        if r["cix_ime"]:
            if not registriraj(conn, r["cix_ime"], r["id"], nalog_id, r["cix_izvor"] or "corpus"):
                raise ExportGreska("ime CIX datoteke '%s' već pripada drugom elementu — preimenovati prije izvoza (D-23)" % r["cix_ime"])
            staro += 1
            continue
        conn.execute("UPDATE element SET cix_ime = ?, cix_izvor = 'hub' WHERE id = ?", (novo_ime(conn, r["id"], nalog_id), r["id"]))
        novo += 1
    conn.commit()
    return novo, staro


def _po_materijalu(els):
    red = []
    for e in els:
        if not red or red[-1][0] != e["nalog_materijal_id"]:
            red.append((e["nalog_materijal_id"], []))
        red[-1][1].append(e)
    return red


def izvezi(conn, nalog_id, mapa, tko="web", stil="bsolid", samo_nesting=True, suho=False, vrijeme=None):
    """Napiši CSV + CIX po materijalu u `<mapa>/<NAZIV NALOGA>/NESTING/`. Vraća popis paketa (jedan po materijalu).

    samo_nesting: preskoči materijale koje je voditelj poslao na pilu (`nalog_materijal.put = 'pila'`).
    suho: samo izračunaj što bi nastalo, ne diraj disk ni bazu (za provjeru i za ekran prije izvoza).
    """
    n = N.nalog(conn, nalog_id)
    if not suho:
        dodijeli_imena(conn, nalog_id, tko)
    els = N.elementi_za_export(conn, nalog_id)
    if not els:
        raise ExportGreska("nalog %s nema elemenata" % n["naziv"])
    zig = (vrijeme or __import__("datetime").datetime.now()).strftime("%d%m%y_%H%M%S")
    korijen = os.path.join(mapa, n["naziv"], "NESTING")
    paketi, preskoceno = [], []
    for nm_id, grupa in _po_materijalu(els):
        m = N.materijal_naloga(conn, nm_id)
        if samo_nesting and (m["put"] or "") == "pila":
            preskoceno.append(dict(materijal=m["naziv_kratki"] or m["naziv_ulaz"], razlog="ide na pilu", elemenata=len(grupa)))
            continue
        if not m["materijal_id"]:
            preskoceno.append(dict(materijal=m["naziv_ulaz"], razlog="materijal nije potvrđen", elemenata=len(grupa)))
            continue
        deb = grupa[0]["deb"]
        if not deb:
            preskoceno.append(dict(materijal=m["naziv_kratki"], razlog="nepoznata debljina", elemenata=len(grupa)))
            continue
        try:
            nalog_io.alat_za_debljinu(deb)                      # nesting ne reže deblje od 26 mm
        except ValueError as e:
            preskoceno.append(dict(materijal=m["naziv_kratki"], razlog=str(e), elemenata=len(grupa)))
            continue
        for i, e in enumerate(grupa, 1):                        # rb unutar paketa kreće od 1, kao kod PPNEST-a
            e["rb"] = i
            e["mat"] = _bez_dij(e["mat"])
        baza_ime = "%s_%s_%s" % (_bez_dij(n["naziv"]), _bez_dij(grupa[0]["mat"]), zig)
        csv_put = os.path.join(korijen, baza_ime + ".CSV")
        p = dict(nalog_materijal_id=nm_id, materijal=grupa[0]["mat"], ident=m["ident"], winstore_kod=m["winstore_kod"] or "",
                 debljina=deb, elemenata=len(grupa), komada=sum(x["kom"] for x in grupa),
                 m2=round(sum(x["L"] * x["W"] * x["kom"] for x in grupa) / 1e6, 3),
                 csv=csv_put, cix=[os.path.join(korijen, (x["cix"] or "") + ".cix") for x in grupa],
                 bez_winstore_koda=not (m["winstore_kod"] or ""))
        if not suho:
            os.makedirs(korijen, exist_ok=True)
            nalog_io.write_ppnest_csv(grupa, csv_put)
            nalog_io.write_cix(grupa, korijen, stil=stil)
            for vrsta, put in [("csv", csv_put)] + [("cix", x) for x in p["cix"]]:
                conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, datum) VALUES (?, ?, ?, ?)", (nalog_id, vrsta, put, sada()))
        paketi.append(p)
    if not paketi:
        raise ExportGreska("nema nijednog materijala za nesting (%s)" % ("; ".join("%s: %s" % (x["materijal"], x["razlog"]) for x in preskoceno) or "nalog je prazan"))
    if not suho:
        dnevnik(conn, tko, "nalog", nalog_id, "izvoz_nesting",
                "%s: %d paketa, %d elemenata, %d CIX" % (n["naziv"], len(paketi), sum(x["elemenata"] for x in paketi),
                                                         sum(len(x["cix"]) for x in paketi)))
        conn.execute("INSERT INTO dogadjaj (nalog_id, kada, tko_id, iz_statusa, u_status, razlog, veza) "
                     "VALUES (?, ?, (SELECT id FROM korisnik WHERE oznaka = ?), ?, ?, ?, ?)",
                     (nalog_id, sada(), tko, n["status"], n["status"],
                      "izvoz na nesting: %d paketa, %d CIX" % (len(paketi), sum(len(x["cix"]) for x in paketi)), "mapa:" + korijen))
        conn.commit()
    return dict(nalog=n["naziv"], mapa=korijen, paketi=paketi, preskoceno=preskoceno, stil=stil, suho=suho)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Izvoz naloga na nesting: CSV + CIX za bNest (korak 3)")
    ap.add_argument("--db")
    ap.add_argument("--nalog", type=int, required=True, help="id naloga")
    ap.add_argument("--mapa", default=".", help="korijen izvoza (nastaje <mapa>\\<NALOG>\\NESTING\\)")
    ap.add_argument("--stil", choices=("bsolid", "ppnest"), default="bsolid", help="postavke CIX-a: bsolid (operater) ili ppnest")
    ap.add_argument("--sve", action="store_true", help="izvezi i materijale koje je voditelj poslao na pilu")
    ap.add_argument("--suho", action="store_true", help="samo pokaži što bi nastalo, ne piši ništa")
    ap.add_argument("--tko", default="web")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    try:
        r = izvezi(conn, a.nalog, a.mapa, a.tko, a.stil, samo_nesting=not a.sve, suho=a.suho)
    except ExportGreska as e:
        print("GRESKA:", e)
        return 1
    print("%s%s -> %s" % ("[suho] " if a.suho else "", r["nalog"], r["mapa"]))
    for p in r["paketi"]:
        print("   %-28s %-12s %4s mm  %3d el / %3d kom  %7.2f m2  %d CIX%s"
              % (p["materijal"][:28], p["winstore_kod"] or "-", p["debljina"], p["elemenata"], p["komada"], p["m2"], len(p["cix"]),
                 "   PAZI: nema Winstore koda" if p["bez_winstore_koda"] else ""))
        print("      %s" % os.path.basename(p["csv"]))
    for x in r["preskoceno"]:
        print("   preskoceno: %-28s %s (%d el.)" % ((x["materijal"] or "?")[:28], x["razlog"], x["elemenata"]))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
