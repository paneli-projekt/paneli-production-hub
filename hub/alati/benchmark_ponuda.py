# -*- coding: utf-8 -*-
"""Benchmark obračuna (korak 4): Hubove stavke ponude vs stvarne Pantheon ponude iz testnih naloga (05_NALOZI_ZA_TEST\\_*\\05_pantheon\\*.pdf).

Za svaki nalog: uveze se PPNEST-ov izvoz (CPW iz PANEL WIZARD mape; HUMER kupčev PPW), Hub napravi obračun, a iz PDF-a ponude
(pdftotext) čitaju se stavke (ident, količina, cijena, rabat). Usporedba po identu: količina Hub vs ponuda, cijena Hub vs ponuda.

    py -m hub.alati.benchmark_ponuda --db hub.db --nalozi ..\\05_NALOZI_ZA_TEST [--md izvjestaj.md]
"""
import argparse
import glob
import os
import re
import subprocess
import sys

from .. import db
from ..nalozi import provjera as PR, obracun as OC

RE_STAVKA = re.compile(r"^\s*(\d+)\s+((?:IV|RP|US|TR|OK|PR|AP)\d{6})\s+(.+?)\s{2,}([\d.,]+)\s+(M2|M|KOM|KPT|PAR)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)", re.M)


def _num(x):
    x = x.replace(",", ".")
    return float(x.replace(".", "", x.count(".") - 1)) if x.count(".") > 1 else float(x)


def ponuda_iz_pdf(pdf):
    try:
        txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    except FileNotFoundError:
        return None
    br = re.search(r"Ponuda br\. (\S+)", txt)
    stavke = [dict(rb=int(m.group(1)), ident=m.group(2), naziv=m.group(3).strip(), kolicina=_num(m.group(4)), jm=m.group(5), cijena=_num(m.group(6)),
                   rabat=_num(m.group(7)), pdv=_num(m.group(8)), iznos=_num(m.group(9))) for m in RE_STAVKA.finditer(txt)]
    return dict(broj=br.group(1) if br else os.path.basename(pdf), stavke=stavke, neto=round(sum(s["iznos"] for s in stavke), 2))


def usporedi(hub, ponuda):
    """Po identu: zbroj količina Hub vs ponuda; cijena; što Hub nema / ponuda nema."""
    h, p = {}, {}
    for s in hub["stavke"]:
        z = h.setdefault(s["pantheon_ident"], dict(kolicina=0.0, cijena=s["cijena"], naziv=s["naziv"], jm=s["jm"], grupa=s["grupa"]))
        z["kolicina"] += s["kolicina"]
    for s in ponuda["stavke"]:
        z = p.setdefault(s["ident"], dict(kolicina=0.0, cijena=s["cijena"], naziv=s["naziv"], jm=s["jm"], rabat=s["rabat"]))
        z["kolicina"] += s["kolicina"]
    redovi = []
    for ident in sorted(set(h) | set(p), key=lambda i: (i[:2] != "IV" and i[:2] != "RP", i)):
        a, b = h.get(ident), p.get(ident)
        r = dict(ident=ident, naziv=(a or b)["naziv"], jm=(a or b)["jm"], hub=round(a["kolicina"], 2) if a else None, ponuda=round(b["kolicina"], 2) if b else None,
                 cijena_hub=a["cijena"] if a else None, cijena_ponuda=b["cijena"] if b else None, grupa=a["grupa"] if a else ("okov" if ident.startswith("OK") else "rucno"))
        if a and b:
            r["razlika"] = round(a["kolicina"] - b["kolicina"], 2)
            r["razlika_pct"] = round((a["kolicina"] - b["kolicina"]) / b["kolicina"] * 100, 1) if b["kolicina"] else None
            r["cijena_ista"] = a["cijena"] is not None and abs(a["cijena"] - b["cijena"]) < 0.011
        redovi.append(r)
    zajednicki = [r for r in redovi if r["hub"] is not None and r["ponuda"] is not None]
    return dict(redovi=redovi, zajednickih=len(zajednicki), samo_hub=[r["ident"] for r in redovi if r["ponuda"] is None], samo_ponuda=[r["ident"] for r in redovi if r["hub"] is None],
                cijena_ista=sum(1 for r in zajednicki if r.get("cijena_ista")),
                kolicina_do_5pct=sum(1 for r in zajednicki if r.get("razlika_pct") is not None and abs(r["razlika_pct"]) <= 5),
                neto_hub_zajednicki=round(sum((r["hub"] or 0) * (r["cijena_hub"] or 0) for r in zajednicki), 2),
                neto_ponuda_zajednicki=round(sum((r["ponuda"] or 0) * (r["cijena_ponuda"] or 0) for r in zajednicki), 2))


def benchmark(conn, koren):
    out = []
    for m in PR.mape_naloga(koren):
        pdfs = sorted(glob.glob(os.path.join(koren, m["mapa"], "05_pantheon", "*.[pP][dD][fF]")))
        dat, izvor = (m["kupac"], "kupac_ppw") if m["kupac"] else ((m["pw"], "cpw") if m["pw"] else (m["csv"], "csv"))
        if not pdfs or not dat:
            continue
        pon = ponuda_iz_pdf(pdfs[0])
        if not pon or not pon["stavke"]:
            out.append(dict(mapa=m["mapa"], greska="ponuda se ne može pročitati: %s" % os.path.basename(pdfs[0])))
            continue
        nid, uk = PR._uvezi(conn, m["mapa"].lstrip("_"), dat, izvor)
        # ponuda je s rabatom kupca — uzmi rabate iz same ponude da se iznosi mogu usporediti
        rab = {s["ident"][:2]: s["rabat"] for s in pon["stavke"]}
        conn.execute("UPDATE nalog SET rabat_materijal = ?, rabat_usluge = ? WHERE id = ?", (rab.get("IV", rab.get("TR", 15)), rab.get("US", 20), nid))
        conn.commit()
        hub = OC.izracunaj(conn, nid)
        u = usporedi(hub, pon)
        out.append(dict(mapa=m["mapa"], nalog_id=nid, izvor=izvor, ponuda=pon["broj"], stavki_hub=len(hub["stavke"]), stavki_ponuda=len(pon["stavke"]),
                        neto_hub=hub["neto"], neto_ponuda=pon["neto"], upozorenja=hub["upozorenja"], po_materijalu=hub["po_materijalu"], **u))
    return out


def markdown(rez):
    L = ["# Benchmark obračuna — Hub vs Pantheon ponude (testni nalozi)", "",
         "| Nalog | Ponuda | Izvor | Stavki Hub / ponuda | Zajednički identi | Količina ±5 % | Cijena ista | Neto zajedničkih Hub / ponuda | Samo Hub | Samo ponuda |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rez:
        if r.get("greska"):
            L.append("| %s | — | — | %s | | | | | | |" % (r["mapa"], r["greska"]))
            continue
        L.append("| %s | %s | %s | %d / %d | %d | %d | %d | %.2f / %.2f | %s | %s |" % (
            r["mapa"], r["ponuda"], r["izvor"], r["stavki_hub"], r["stavki_ponuda"], r["zajednickih"], r["kolicina_do_5pct"], r["cijena_ista"],
            r["neto_hub_zajednicki"], r["neto_ponuda_zajednicki"], ", ".join(r["samo_hub"]) or "—", ", ".join(r["samo_ponuda"]) or "—"))
    for r in rez:
        if r.get("greska"):
            continue
        L += ["", "## %s — ponuda %s" % (r["mapa"], r["ponuda"]), "", "| Ident | Naziv | JM | Hub | Ponuda | Razlika | % | Cijena Hub / ponuda |", "|---|---|---|---|---|---|---|---|"]
        for x in r["redovi"]:
            L.append("| %s | %s | %s | %s | %s | %s | %s | %s / %s |" % (
                x["ident"], x["naziv"][:40], x["jm"], "—" if x["hub"] is None else x["hub"], "—" if x["ponuda"] is None else x["ponuda"],
                x.get("razlika", "—"), ("%+.1f" % x["razlika_pct"]) if x.get("razlika_pct") is not None else "—",
                "—" if x["cijena_hub"] is None else x["cijena_hub"], "—" if x["cijena_ponuda"] is None else x["cijena_ponuda"]))
        for u in r["upozorenja"]:
            L.append("- PAZI: %s" % u)
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--nalozi", required=True)
    ap.add_argument("--md")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    rez = benchmark(conn, a.nalozi)
    for r in rez:
        if r.get("greska"):
            print("%-20s %s" % (r["mapa"], r["greska"]))
            continue
        print("%-20s %-16s %2d/%2d stavki, zajednickih %2d, kolicina +-5%%: %2d, cijena ista %2d, neto zaj. %9.2f / %9.2f   samo Hub: %s   samo ponuda: %s"
              % (r["mapa"], r["ponuda"], r["stavki_hub"], r["stavki_ponuda"], r["zajednickih"], r["kolicina_do_5pct"], r["cijena_ista"],
                 r["neto_hub_zajednicki"], r["neto_ponuda_zajednicki"], ",".join(r["samo_hub"]) or "-", ",".join(r["samo_ponuda"]) or "-"))
    if a.md:
        open(a.md, "w", encoding="utf-8").write(markdown(rez))
        print("Izvjestaj:", a.md)
    PR.obrisi_provjere(conn)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
