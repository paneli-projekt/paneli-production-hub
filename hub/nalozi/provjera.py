# -*- coding: utf-8 -*-
"""Provjera koraka 2 na testnim nalozima (05_NALOZI_ZA_TEST): svaki nalog se uveze dvaput — iz PPNEST-ovih CPW datoteka
(04_export_nesting\\<NALOG>\\PANEL WIZARD\\*.CPW) i iz PPNEST CSV-ova za bNest (…\\NESTING\\*.CSV) — pa se uspoređuju
materijali, broj elemenata, komada i m² (moraju biti isti: to su dva izvoza istog naloga). Uz to HUMER-ov kupčev PPW (01_ulaz_kupca).

    py -m hub.nalozi.provjera --db hub.db --nalozi ..\\05_NALOZI_ZA_TEST [--md izvjestaj.md] [--kupci ..\\..\\ph_subjekti.csv]

Ispisuje po nalogu: materijali (ident ili „za potvrdu“), elementi / kom / m² iz CPW-a i CSV-a, rubovi za potvrdu; na kraju sažetak.
Radi na privremenoj kopiji podataka u istoj bazi (nalozi ostaju u bazi s izvorom 'provjera' — obrisati s --obrisi).
"""
import argparse
import glob
import os
import sys

from .. import db
from . import nalozi as N, uvoz_datoteka as U


def mape_naloga(koren):
    out = []
    for d in sorted(glob.glob(os.path.join(koren, "_*"))):
        if not os.path.isdir(d):
            continue
        pw = sorted({os.path.normpath(p) for p in glob.glob(os.path.join(d, "04_export_nesting", "**", "PANEL WIZARD", "*.[cC][pP][wW]"), recursive=True)})
        csvs = sorted({os.path.normpath(p) for p in glob.glob(os.path.join(d, "04_export_nesting", "**", "NESTING", "*.[cC][sS][vV]"), recursive=True)})
        kupac = sorted({os.path.normpath(p) for p in glob.glob(os.path.join(d, "01_ulaz_kupca", "*.[cC][pP][wW]"))})
        out.append(dict(mapa=os.path.basename(d), pw=pw, csv=csvs, kupac=kupac))
    return out


def _uvezi(conn, naziv, datoteke, izvor, tko="PROVJERA"):
    dijelovi = naziv.split("_", 1)
    n = N.novi_nalog(conn, tko, kupac_kratki=dijelovi[0], projekt=dijelovi[1] if len(dijelovi) > 1 else "", izvor="provjera")
    datoteke, starije = U.najnovije_datoteke(datoteke)
    uk = dict(datoteke=0, materijali_novi=0, materijali_spojeni=0, elementi=0, komada=0, za_potvrdu_materijal=0, za_potvrdu_rub=0, preskoceno=0,
              preskocene_starije=[os.path.basename(p) for p in starije])
    for p in datoteke:
        st = U.uvezi_ppnest_csv(conn, n["id"], p, tko) if p.lower().endswith(".csv") else U.uvezi_cpw(conn, n["id"], p, tko, izvor)
        uk["datoteke"] += 1
        for k in st:
            uk[k] += st[k]
    return n["id"], uk


def provjeri(conn, koren):
    rez = []
    for m in mape_naloga(koren):
        r = dict(mapa=m["mapa"])
        for kljuc, dat, izvor in (("cpw", m["pw"], "cpw"), ("csv", m["csv"], "csv"), ("kupac", m["kupac"], "kupac_ppw")):
            if not dat:
                r[kljuc] = None
                continue
            nid, uk = _uvezi(conn, m["mapa"].lstrip("_"), dat, izvor)
            p = N.pregled(conn, nid)
            r[kljuc] = dict(nalog_id=nid, naziv=p["naziv"], uvoz=uk, sazetak=p["sazetak"],
                            materijali=[dict(ulaz=x["naziv_ulaz"], deb=x["debljina_ulaz"], ident=x["ident"], naziv=x["naziv"], provjeri=x["provjeri"],
                                             elemenata=x["elemenata"], komada=x["komada"], m2=x["m2"]) for x in p["materijali"]],
                            za_potvrdu=p["za_potvrdu"])
        if r["cpw"] and r["csv"]:
            a, b = r["cpw"]["sazetak"], r["csv"]["sazetak"]
            r["slaze_se"] = (a["elemenata"], a["komada"], round(a["m2"], 2)) == (b["elemenata"], b["komada"], round(b["m2"], 2)) and \
                            {x["ident"] for x in r["cpw"]["materijali"]} == {x["ident"] for x in r["csv"]["materijali"]}
        else:
            r["slaze_se"] = None
        rez.append(r)
    return rez


def sazetak(rez):
    s = dict(naloga=len(rez), slaze_se=sum(1 for r in rez if r["slaze_se"]), usporedivo=sum(1 for r in rez if r["slaze_se"] is not None),
             materijala=0, materijala_sigurno=0, elemenata=0, komada=0, rubova_za_potvrdu=0, stavki_za_potvrdu=0)
    for r in rez:
        for k in ("cpw", "csv", "kupac"):
            if not r[k]:
                continue
            s["materijala"] += len(r[k]["materijali"])
            s["materijala_sigurno"] += sum(1 for x in r[k]["materijali"] if not x["provjeri"] and x["ident"])
            s["elemenata"] += r[k]["sazetak"]["elemenata"]
            s["komada"] += r[k]["sazetak"]["komada"]
            s["rubova_za_potvrdu"] += r[k]["uvoz"]["za_potvrdu_rub"]
            s["stavki_za_potvrdu"] += len(r[k]["za_potvrdu"])
    return s


def ispis(rez, s, out=sys.stdout):
    w = out.write
    for r in rez:
        w("== %s  (CPW <-> CSV %s)\n" % (r["mapa"], {True: "SLAŽE SE", False: "RAZLIKA", None: "—"}[r["slaze_se"]]))
        for k in ("cpw", "csv", "kupac"):
            x = r[k]
            if not x:
                continue
            sz = x["sazetak"]
            w("   %-6s %-24s %2d mat, %3d el, %4d kom, %7.2f m2, za potvrdu %d%s\n" % (k, x["naziv"], sz["materijala"], sz["elemenata"], sz["komada"], sz["m2"], sz["za_potvrdu"],
                                                                              ("; starije verzije preskočene: " + ", ".join(x["uvoz"]["preskocene_starije"])) if x["uvoz"].get("preskocene_starije") else ""))
            for m in x["materijali"]:
                w("          %-26s %-9s %-42s %s\n" % ((m["ulaz"] or "")[:26], m["ident"] or "—", (m["naziv"] or "")[:42], "ZA POTVRDU" if m["provjeri"] or not m["ident"] else ""))
            for z in x["za_potvrdu"]:
                w("          za potvrdu %s '%s' %s: %s\n" % (z["vrsta"], z["tekst"], z.get("klasa") or "", ", ".join("%s %s" % (c["ident"], c["naziv"][:30]) for c in z["kandidati"][:2])))
    w("\n== Sažetak: %d naloga; CPW <-> CSV slaže se %d / %d; materijala %d (sigurno %d); elemenata %d, komada %d; rubova za potvrdu %d; stavki za potvrdu %d\n"
      % (s["naloga"], s["slaze_se"], s["usporedivo"], s["materijala"], s["materijala_sigurno"], s["elemenata"], s["komada"], s["rubova_za_potvrdu"], s["stavki_za_potvrdu"]))


def markdown(rez, s):
    L = ["# Provjera koraka 2 — uvoz testnih naloga kroz šifrarnik", "",
         "| Nalog | Izvor | Materijala | Elemenata | Komada | m² | Za potvrdu | CPW ↔ CSV |", "|---|---|---|---|---|---|---|---|"]
    for r in rez:
        for k in ("cpw", "csv", "kupac"):
            x = r[k]
            if not x:
                continue
            sz = x["sazetak"]
            L.append("| %s | %s | %d | %d | %d | %.2f | %d | %s |" % (r["mapa"], k, sz["materijala"], sz["elemenata"], sz["komada"], sz["m2"], sz["za_potvrdu"],
                                                                   {True: "slaže se", False: "RAZLIKA", None: "—"}[r["slaze_se"]] if k == "cpw" else ""))
    L += ["", "Sažetak: %d naloga; CPW ↔ CSV slaže se %d / %d; materijala %d (sigurno %d); elemenata %d, komada %d; stavki za potvrdu %d"
          % (s["naloga"], s["slaze_se"], s["usporedivo"], s["materijala"], s["materijala_sigurno"], s["elemenata"], s["komada"], s["stavki_za_potvrdu"]), "",
          "## Materijali po nalogu (CPW)", "", "| Nalog | Ulazni naziv | Ident | Pantheon naziv | Elemenata | Komada | m² |", "|---|---|---|---|---|---|---|"]
    for r in rez:
        for k in ("cpw", "kupac"):
            x = r[k]
            if not x:
                continue
            for m in x["materijali"]:
                L.append("| %s (%s) | %s | %s | %s | %d | %d | %.2f |" % (r["mapa"], k, m["ulaz"], m["ident"] or "za potvrdu", m["naziv"] or "—", m["elemenata"], m["komada"], m["m2"]))
    L += ["", "## Stavke za potvrdu", "", "| Nalog | Vrsta | Tekst | Klasa | Kandidati |", "|---|---|---|---|---|"]
    for r in rez:
        for k in ("cpw", "csv", "kupac"):
            x = r[k]
            if not x:
                continue
            for z in x["za_potvrdu"]:
                L.append("| %s (%s) | %s | %s | %s | %s |" % (r["mapa"], k, z["vrsta"], z["tekst"], z.get("klasa") or "", "; ".join("%s %s" % (c["ident"], c["naziv"]) for c in z["kandidati"][:3])))
    return "\n".join(L) + "\n"


def obrisi_provjere(conn):
    ids = [r[0] for r in conn.execute("SELECT id FROM nalog WHERE izvor = 'provjera'")]
    for nid in ids:
        conn.execute("DELETE FROM element WHERE nalog_materijal_id IN (SELECT id FROM nalog_materijal WHERE nalog_id = ?)", (nid,))
        conn.execute("DELETE FROM nalog_materijal WHERE nalog_id = ?", (nid,))
        conn.execute("DELETE FROM dogadjaj WHERE nalog_id = ?", (nid,))
        conn.execute("DELETE FROM dokument WHERE nalog_id = ?", (nid,))
        conn.execute("DELETE FROM nalog WHERE id = ?", (nid,))
    conn.commit()
    return len(ids)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--nalozi", required=True, help="mapa 05_NALOZI_ZA_TEST")
    ap.add_argument("--md", help="spremi Markdown izvještaj")
    ap.add_argument("--kupci", help="ph_subjekti.csv (uvoz kupaca prije provjere)")
    ap.add_argument("--poste", help="ph_poste.csv")
    ap.add_argument("--obrisi", action="store_true", help="na kraju obriši naloge provjere iz baze")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    if a.kupci:
        from .kupci import uvezi_kupce
        print("Kupci:", uvezi_kupce(conn, a.kupci, a.poste, "PROVJERA"))
    rez = provjeri(conn, a.nalozi)
    s = sazetak(rez)
    ispis(rez, s)
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(markdown(rez, s))
        print("Izvještaj:", a.md)
    if a.obrisi:
        print("Obrisano naloga provjere:", obrisi_provjere(conn))
    return 0


if __name__ == "__main__":
    sys.exit(main())
