# -*- coding: utf-8 -*-
"""Provjera koraka 3: je li ono što Hub izveze isti posao kao ono što danas izlazi iz PPNEST-a / PanelWizarda.

Za svaki testni nalog: uveze se PPNEST-ov izvoz (CPW za PW, CSV za bNest), pa se iz Huba izveze natrag i usporedi s
originalom. Uspoređuje se ono što stroj i obračun stvarno troše — debljina, mjere, komadi i maska rubova po elementu —
a ne tekst naziva (Hub namjerno piše svoj kratki naziv materijala i pravi naziv trake iz Pantheona).

    py -m hub.alati.provjera_exporta --db hub.db --nalozi ..\\05_NALOZI_ZA_TEST [--md ..\\20_ANALIZA\\provjera_exporta.md] [--obrisi]

Ispis po nalogu i materijalu: elemenata / komada kod PPNEST-a i kod Huba + ISTO ili popis razlika.
"""
import argparse
import glob
import io
import os
import re
import shutil
import sys
import tempfile

from .. import db
from ..nalozi import nalozi as N, provjera as P, export_nesting as EN, export_pw as EPW
from ..formati import nalog_io


def _maska(tipovi):
    return "".join((t or "-") for t in tipovi)


def citaj_cpw(putanja):
    """Original CPW → multiskup (deb, L, W, kom, maska rubova)."""
    out = []
    deb = ""
    for red in io.open(putanja, encoding="cp1250", errors="replace").read().splitlines():
        d = red.split(";")
        if not d:
            continue
        if d[0] == "MATERIJAL" and len(d) > 2:
            deb = str(float(d[2] or 0))
        elif d[0] == "ELEMENT" and len(d) > 8:
            out.append((deb, d[2], d[3], d[4], _maska(x.strip() for x in d[5:9])))
    return sorted(out)


def citaj_csv(putanja):
    """Original PPNEST CSV → isti oblik. Tip ruba u CSV-u nije zapisan (stupci RUBx su prazni), pa se gleda ima li ruba."""
    out = []
    for e in nalog_io.read_ppnest_csv(putanja):
        out.append((str(float(e["deb"] or 0)), nalog_io._fmt(e["L"]), nalog_io._fmt(e["W"]), str(e["kom"]),
                    _maska("T" if (e["traka"].get(r) or "").strip() else "" for r in ("L", "O", "D", "G"))))
    return sorted(out)


def iz_huba(paketi_els):
    out = []
    for e in paketi_els:
        out.append((str(float(e["deb"] or 0)), nalog_io._fmt(e["L"]), nalog_io._fmt(e["W"]), str(e["kom"]),
                    _maska(e["tip"][r] for r in ("L", "O", "D", "G"))))
    return sorted(out)


def bez_tipa(red):
    return tuple(red[:4])


def usporedi(a, b):
    """Vraća (isti, razlike) — razlike su (samo_original, samo_hub) po cijelom retku i po retku bez tipa ruba."""
    if a == b:
        return True, dict(samo_original=[], samo_hub=[], samo_tip=[])
    sa, sb = sorted(a), sorted(b)
    ma, mb = [bez_tipa(x) for x in sa], [bez_tipa(x) for x in sb]
    samo_tip = ma == mb                                  # iste mjere i komadi, razlikuje se samo M/A
    return False, dict(samo_original=[x for x in sa if x not in sb][:8], samo_hub=[x for x in sb if x not in sa][:8],
                       samo_tip=samo_tip)


def _tip_iz_naziva(tekst):
    """Vrsta trake koju sam naziv u nalogu tvrdi: 'M' do 0,5 mm, 'A' deblje; None kad se iz naziva ne vidi."""
    t = (tekst or "").strip().upper()
    if not t:
        return None
    if t.startswith("MEL") or t.startswith("0,5") or t.startswith("0.5"):
        return "M"
    m = re.match(r"^(\d+[,.]?\d*)\s*/\s*\d+", t)
    if m:
        return "M" if float(m.group(1).replace(",", ".")) <= 0.5 else "A"
    return None                                     # 'ABS-ISTI' / '1/22 ISTI' rješava zadana traka materijala


def nesklad_ma(koren):
    """Koliko puta se u PPNEST-ovom CPW-u slovo M/A ne slaže s trakom koju ta ista linija imenuje.

    To je razlog zašto Hubov CPW nije doslovno isti: Hub slovo izvodi iz prepoznate trake, PPNEST ga je preuzimao
    onako kako ga je operater kliknuo, pa se zna razići s upisanim nazivom trake."""
    uk = dict(provjereno=0, slaze=0, M_a_traka_je_ABS=0, A_a_traka_je_MEL=0)
    po_nalogu = {}
    for d in sorted(glob.glob(os.path.join(koren, "_*"))):
        if not os.path.isdir(d):
            continue
        ime = os.path.basename(d)
        for p in sorted(glob.glob(os.path.join(d, "04_export_nesting", "**", "PANEL WIZARD", "*.[cC][pP][wW]"), recursive=True)):
            for red in io.open(p, encoding="cp1250", errors="replace").read().splitlines():
                c = red.split(";")
                if c[0] != "ELEMENT" or len(c) < 13:
                    continue
                for i in range(4):
                    tip, naziv = c[5 + i].strip().upper(), c[9 + i]
                    k = _tip_iz_naziva(naziv)
                    if not tip or not k:
                        continue
                    uk["provjereno"] += 1
                    if tip == k:
                        uk["slaze"] += 1
                    else:
                        kljuc = "M_a_traka_je_ABS" if tip == "M" else "A_a_traka_je_MEL"
                        uk[kljuc] += 1
                        po_nalogu.setdefault(ime, {}).setdefault(kljuc, set()).add(naziv.strip())
    return uk, po_nalogu


def provjeri(conn, koren, mapa_izvoza):
    rez = []
    P._BROJAC[0] = max([0] + [int(r[0].split("-")[1]) for r in conn.execute("SELECT broj FROM nalog WHERE broj LIKE 'PROV-%'")])
    for m in P.mape_naloga(koren):
        r = dict(mapa=m["mapa"])
        if m["pw"]:
            nid, _ = P._uvezi(conn, m["mapa"].lstrip("_"), m["pw"], "cpw", tko="PROVJERA")
            dat, _st = nalog_io.__name__, None
            izvor = []
            for p in P.U.najnovije_datoteke(m["pw"])[0]:
                izvor += citaj_cpw(p)
            hub = iz_huba(N.elementi_za_export(conn, nid))
            isti, raz = usporedi(sorted(izvor), hub)
            r["cpw"] = dict(nalog_id=nid, original=len(izvor), hub=len(hub),
                            kom_original=sum(int(x[3]) for x in izvor), kom_hub=sum(int(x[3]) for x in hub),
                            isti=isti, razlike=raz)
        if m["csv"]:
            nid, _ = P._uvezi(conn, m["mapa"].lstrip("_"), m["csv"], "csv", tko="PROVJERA")
            izvor = []
            for p in P.U.najnovije_datoteke(m["csv"])[0]:
                izvor += citaj_csv(p)
            hub = iz_huba(N.elementi_za_export(conn, nid))
            hub = [(a, b, c, d, _maska("T" if x != "-" else "" for x in e)) for a, b, c, d, e in hub]
            isti, raz = usporedi(sorted(izvor), sorted(hub))
            r["csv"] = dict(nalog_id=nid, original=len(izvor), hub=len(hub),
                            kom_original=sum(int(x[3]) for x in izvor), kom_hub=sum(int(x[3]) for x in hub),
                            isti=isti, razlike=raz)
        rez.append(r)
    return rez


def ispis(rez):
    red = "%-22s %-5s %6s %6s %7s %7s  %s"
    print(red % ("nalog", "izlaz", "el.PPN", "el.HUB", "kom.PPN", "kom.HUB", "rezultat"))
    ok = {"cpw": 0, "csv": 0}
    uk = {"cpw": 0, "csv": 0}
    for r in rez:
        for k in ("cpw", "csv"):
            d = r.get(k)
            if not d:
                continue
            uk[k] += 1
            ok[k] += 1 if d["isti"] else 0
            stanje = "ISTO" if d["isti"] else ("razlika samo u M/A" if d["razlike"]["samo_tip"] else "RAZLIKA")
            print(red % (r["mapa"][:22], k.upper(), d["original"], d["hub"], d["kom_original"], d["kom_hub"], stanje))
            if not d["isti"]:
                for x in d["razlike"]["samo_original"][:4]:
                    print("        samo PPNEST: deb %s  %s x %s  %s kom  rubovi %s" % x)
                for x in d["razlike"]["samo_hub"][:4]:
                    print("        samo HUB   : deb %s  %s x %s  %s kom  rubovi %s" % x)
    print()
    for k in ("cpw", "csv"):
        if uk[k]:
            print("%s: %d / %d naloga isto" % (k.upper(), ok[k], uk[k]))
    return ok, uk


def ispis_neslaganja(n, po_nalogu):
    print()
    print("PPNEST-ovo slovo M/A protiv trake koju sama linija imenuje: provjereno %d, slaze se %d, "
          "slovo M a traka je ABS %d, slovo A a traka je melamin %d"
          % (n["provjereno"], n["slaze"], n["M_a_traka_je_ABS"], n["A_a_traka_je_MEL"]))
    for ime, d in sorted(po_nalogu.items()):
        for k, v in sorted(d.items()):
            print("   %-20s %-18s %d vrsta trake: %s" % (ime[:20], k, len(v), ", ".join(sorted(v))[:70]))


def markdown(rez, ok, uk, n=None, po_nalogu=None):
    o = ["# Provjera izvoza (korak 3) — Hub vs PPNEST / PanelWizard", "",
         "Uspoređuje se debljina, mjere, komadi i maska rubova po elementu; nazivi materijala i traka se namjerno razlikuju.", "",
         "| Nalog | Izlaz | Elemenata PPNEST | Elemenata Hub | Komada PPNEST | Komada Hub | Rezultat |", "|---|---|---|---|---|---|---|"]
    for r in rez:
        for k in ("cpw", "csv"):
            d = r.get(k)
            if not d:
                continue
            stanje = "**ISTO**" if d["isti"] else ("razlika samo u oznaci M/A" if d["razlike"]["samo_tip"] else "**RAZLIKA**")
            o.append("| %s | %s | %d | %d | %d | %d | %s |" % (r["mapa"], k.upper(), d["original"], d["hub"],
                                                              d["kom_original"], d["kom_hub"], stanje))
    o += ["", "**Sažetak:** " + ", ".join("%s %d/%d" % (k.upper(), ok[k], uk[k]) for k in ("cpw", "csv") if uk[k])]
    if n:
        o += ["", "## Zašto se CPW razlikuje: slovo M/A u PPNEST-u", "",
              "PPNEST u CPW uz svaki rub piše slovo (`M` melamin, `A` ABS) i naziv trake. Na testnim nalozima se to dvoje "
              "ne slaže %d puta od %d provjerenih rubova: %d puta stoji `M` a imenovana traka je ABS od 1 ili 2 mm, "
              "%d puta stoji `A` a traka je melamin od 0,5 mm. Hub slovo izvodi iz prepoznate trake, pa te razlike ne prenosi."
              % (n["M_a_traka_je_ABS"] + n["A_a_traka_je_MEL"], n["provjereno"], n["M_a_traka_je_ABS"], n["A_a_traka_je_MEL"]),
              "", "| Nalog | Neslaganje | Trake |", "|---|---|---|"]
        for ime, d in sorted((po_nalogu or {}).items()):
            for k, v in sorted(d.items()):
                o.append("| %s | %s | %s |" % (ime, k.replace("_", " "), ", ".join(sorted(v))))
    return "\n".join(o) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Provjera izvoza (korak 3) na testnim nalozima")
    ap.add_argument("--db")
    ap.add_argument("--nalozi", required=True, help="mapa 05_NALOZI_ZA_TEST")
    ap.add_argument("--md", help="zapiši izvještaj u Markdown")
    ap.add_argument("--obrisi", action="store_true", help="obriši probne naloge nakon provjere")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    tmp = tempfile.mkdtemp(prefix="hub_izvoz_")
    try:
        rez = provjeri(conn, a.nalozi, tmp)
        ok, uk = ispis(rez)
        n, po_nalogu = nesklad_ma(a.nalozi)
        ispis_neslaganja(n, po_nalogu)
        if a.md:
            io.open(a.md, "w", encoding="utf-8").write(markdown(rez, ok, uk, n, po_nalogu))
            print("\nzapisano:", a.md)
        if a.obrisi:
            n = conn.execute("SELECT COUNT(*) FROM nalog WHERE izvor = 'provjera'").fetchone()[0]
            for r in conn.execute("SELECT id FROM nalog WHERE izvor = 'provjera'").fetchall():
                N.obrisi_nalog(conn, r["id"], "PROVJERA")
            conn.commit()
            print("obrisano probnih naloga:", n)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
