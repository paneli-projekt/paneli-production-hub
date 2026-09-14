# -*- coding: utf-8 -*-
"""Provjera šifrarnika na testnim nalozima (04 §4, korak 1 — kriterij prihvaćanja):
svih 50 CPO materijala i ponudbeni identi iz benchmark_nalozi.csv mapirani bez ručnog rada; trake iz CPW/CSV oznaka prepoznate.

    py -m hub.sifrarnici.provjera --db hub.db --nalozi 05_NALOZI_ZA_TEST --benchmark 20_ANALIZA\\benchmark_nalozi.csv [--md izvjestaj.md]

Ispisuje tablicu po datoteci (razina prepoznavanja, ident, očekivani ident iz ponude) i sažetak; s --md sprema Markdown izvještaj.
"""
import argparse
import csv
import glob
import os
import sys
from collections import Counter

from .. import db
from ..formati.parseri import parse_cpo, parse_cpw, parse_ppnest_csv
from . import prepoznaj as P


def _datoteke(mapa, *uzorci):
    """Sve datoteke po uzorcima, bez duplikata (Windows glob ne razlikuje velika i mala slova)."""
    return sorted({os.path.normpath(p) for u in uzorci for p in glob.glob(os.path.join(mapa, "**", u), recursive=True)})


def cpo_materijali(mapa):
    out = []
    for p in _datoteke(mapa, "*.cpo", "*.CPO"):
        d = parse_cpo(p)
        inv = d["inv"][0] if d["inv"] else {}
        nalog = os.path.relpath(p, mapa).split(os.sep)[0]
        out.append(dict(nalog=nalog, datoteka=os.path.basename(p), naziv=inv.get("name") or d.get("material", ""), naziv_hdr=d.get("material", ""),
                        debljina=d.get("thickness"), sirina=inv.get("W"), izvor="cpo"))
    return out


def cpw_materijali(mapa):
    out = []
    for p in _datoteke(mapa, "*.CPW", "*.cpw"):
        els = parse_cpw(p)
        nalog = os.path.relpath(p, mapa).split(os.sep)[0]
        for (mat, deb) in sorted({(e["materijal"], e["debljina"]) for e in els}):
            trake = sorted({t.strip() for e in els if e["materijal"] == mat for t in e["traka"] if t and t.strip()})
            out.append(dict(nalog=nalog, datoteka=os.path.basename(p), naziv=mat, debljina=float(deb) if deb else None, sirina=None, izvor="cpw", trake=trake))
    return out


def csv_materijali(mapa):
    out = []
    for p in _datoteke(mapa, "*.CSV", "*.csv"):
        rows = parse_ppnest_csv(p)
        nalog = os.path.relpath(p, mapa).split(os.sep)[0]
        for (kod, mat, deb) in sorted({(r["SIFRA MAT"], r["MAT NAZIV"], r["MAT DEB"]) for r in rows}):
            trake = sorted({r[k].strip() for r in rows for k in ("TR1SIFRA", "TRS2IFRA", "TR3SIFRA", "TR4SIFRA") if r.get(k) and r[k].strip()})
            out.append(dict(nalog=nalog, datoteka=os.path.basename(p), naziv=mat, debljina=float(deb) if deb else None, sirina=None, izvor="csv", winstore_kod=kod, trake=trake))
    return out


def ucitaj_benchmark(putanja):
    if not putanja or not os.path.exists(putanja):
        return {}
    out = {}
    with open(putanja, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            out[(r["nalog"], r["cpo"])] = r.get("ponuda_ident", "").strip()
    return out


def provjeri(conn, mapa, benchmark=None):
    bench = ucitaj_benchmark(benchmark)
    rez = dict(cpo=[], cpw=[], csv=[], trake=[])
    for m in cpo_materijali(mapa):
        r = P.prepoznaj_materijal(conn, m["naziv"], debljina=m["debljina"], sirina_ploce=m["sirina"])
        ocek = bench.get((m["nalog"], m["datoteka"]), "")
        rez["cpo"].append(dict(m, rez=r, ocekivano=ocek, tocno=(None if not ocek else r.ident == ocek)))
    for m in cpw_materijali(mapa):
        r = P.prepoznaj_materijal(conn, m["naziv"], debljina=m["debljina"])
        rez["cpw"].append(dict(m, rez=r))
        for t in m.get("trake", []):
            rt = P.prepoznaj_traku(conn, t, materijal_id=r.id if r.siguran else None)
            rez["trake"].append(dict(nalog=m["nalog"], datoteka=m["datoteka"], materijal=r.ident, oznaka=t, rez=rt))
    for m in csv_materijali(mapa):
        r = P.prepoznaj_materijal(conn, m["naziv"], debljina=m["debljina"], winstore_kod=m.get("winstore_kod"))
        rez["csv"].append(dict(m, rez=r))
    return rez


def sazetak(rez):
    s = {}
    for k in ("cpo", "cpw", "csv", "trake"):
        c = Counter(x["rez"].razina for x in rez[k])
        s[k] = dict(ukupno=len(rez[k]), sigurno=sum(1 for x in rez[k] if x["rez"].siguran), razine=dict(c))
    s["cpo"]["tocno_vs_ponuda"] = sum(1 for x in rez["cpo"] if x["tocno"])
    s["cpo"]["s_ponudom"] = sum(1 for x in rez["cpo"] if x["ocekivano"])
    s["cpo"]["krivo_vs_ponuda"] = [(x["datoteka"], x["naziv"], x["rez"].ident, x["ocekivano"]) for x in rez["cpo"] if x["ocekivano"] and x["tocno"] is False]
    return s


def ispis(rez, s, out=sys.stdout):
    w = out.write
    w("== CPO materijali (%d) — sigurno %d, po razinama %s; točno vs ponuda %d / %d\n" % (s["cpo"]["ukupno"], s["cpo"]["sigurno"], s["cpo"]["razine"], s["cpo"]["tocno_vs_ponuda"], s["cpo"]["s_ponudom"]))
    for x in rez["cpo"]:
        r = x["rez"]
        oz = "OK " if x["tocno"] else ("XX " if x["tocno"] is False else "   ")
        w("%s%-15s %-26s %-10s %-9s %-46s %s\n" % (oz, x["datoteka"], x["naziv"][:26], r.razina, r.ident or "—", (r.naziv or "")[:46], ("ponuda " + x["ocekivano"]) if x["ocekivano"] else ""))
        if not r.siguran:
            for i, n, sc in r.kandidati[:3]:
                w("      kandidat %s %s (%.1f)\n" % (i, n[:50], sc))
    w("\n== CPW materijali (%d) — sigurno %d, %s\n" % (s["cpw"]["ukupno"], s["cpw"]["sigurno"], s["cpw"]["razine"]))
    for x in rez["cpw"]:
        r = x["rez"]
        if not r.siguran:
            w("   %-58s %-28s %-10s %s — %s\n" % (x["datoteka"][:58], x["naziv"][:28], r.razina, r.ident or "—", r.objasnjenje[-60:]))
    w("\n== PPNEST CSV materijali (%d) — sigurno %d, %s\n" % (s["csv"]["ukupno"], s["csv"]["sigurno"], s["csv"]["razine"]))
    for x in rez["csv"]:
        r = x["rez"]
        if not r.siguran:
            w("   %-58s %-28s %-10s %s\n" % (x["datoteka"][:58], x["naziv"][:28], r.razina, r.ident or "—"))
    w("\n== Trake iz CPW oznaka (%d) — sigurno %d, %s\n" % (s["trake"]["ukupno"], s["trake"]["sigurno"], s["trake"]["razine"]))
    vidjeno = set()
    for x in rez["trake"]:
        r = x["rez"]
        kljuc = (x["materijal"], x["oznaka"])
        if kljuc in vidjeno:
            continue
        vidjeno.add(kljuc)
        w("   %-9s %-22s %-10s %-9s %-40s %s\n" % (x["materijal"] or "—", x["oznaka"][:22], r.razina, r.ident or "—", (r.naziv or "")[:40], r.klasa or ""))
        if not r.siguran:
            for i, n, sc in r.kandidati[:2]:
                w("      kandidat %s %s (%.1f)\n" % (i, n[:44], sc))


def markdown(rez, s):
    L = ["# Provjera šifrarnika na testnim nalozima", "",
         "| Skup | Ukupno | Sigurno | Razine |", "|---|---|---|---|"]
    for k, ime in (("cpo", "CPO materijali (pila, PW)"), ("cpw", "CPW materijali"), ("csv", "PPNEST CSV materijali (SIFRA MAT)"), ("trake", "Trake iz CPW oznaka")):
        L.append("| %s | %d | %d | %s |" % (ime, s[k]["ukupno"], s[k]["sigurno"], ", ".join("%s %d" % kv for kv in sorted(s[k]["razine"].items()))))
    L += ["", "CPO vs ident u ponudi (benchmark_nalozi.csv): točno %d / %d" % (s["cpo"]["tocno_vs_ponuda"], s["cpo"]["s_ponudom"]), "",
          "| Datoteka | Naziv u CPO | Razina | Hub ident | Pantheon naziv | Ponuda |", "|---|---|---|---|---|---|"]
    for x in rez["cpo"]:
        r = x["rez"]
        L.append("| %s | %s | %s | %s | %s | %s |" % (x["datoteka"], x["naziv"], r.razina, r.ident or "—", (r.naziv or "").replace("|", "/"), x["ocekivano"] or "—"))
    L += ["", "## Trake (oznaka u CPW → traka)", "", "| Materijal | Oznaka | Razina | Traka | Naziv | Klasa |", "|---|---|---|---|---|---|"]
    vidjeno = set()
    for x in rez["trake"]:
        k = (x["materijal"], x["oznaka"])
        if k in vidjeno:
            continue
        vidjeno.add(k)
        r = x["rez"]
        L.append("| %s | %s | %s | %s | %s | %s |" % (x["materijal"] or "—", x["oznaka"], r.razina, r.ident or "—", r.naziv or "—", r.klasa or ""))
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--nalozi", required=True, help="mapa 05_NALOZI_ZA_TEST")
    ap.add_argument("--benchmark", help="20_ANALIZA/benchmark_nalozi.csv")
    ap.add_argument("--md", help="spremi Markdown izvještaj")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")      # Windows konzola bez UTF-8: ne rušiti se na znaku koji se ne može ispisati
    conn = db.spoji(a.db)
    rez = provjeri(conn, a.nalozi, a.benchmark)
    s = sazetak(rez)
    ispis(rez, s)
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(markdown(rez, s))
        print("\nIzvještaj:", a.md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
