# -*- coding: utf-8 -*-
"""Prijedlozi spajanja malih naloga u jedan nesting posao (D-54).

Više naloga koji čekaju proizvodnju često traže isti materijal, svaki u količini manjoj od jedne ploče — pa svaki
zasebno ide na pilu. Ako se ti dijelovi režu zajedno, stane ih se više na istu ploču i posao ide na nesting, koji je
brži i precizniji. Hub to samo PREDLAŽE; voditelj odlučuje što spaja (D-34).

    py -m hub.nalozi.spajanje --db hub.db
    py -m hub.nalozi.spajanje --db hub.db --md prijedlozi.md --prag 1

Uvjet za prijedlog: zbroj svih naloga za taj materijal >= 1 ploča (to je ujedno uvjet da se uopće reže na nestingu).
Obračun se ne mijenja — svaki nalog se i dalje računa zasebno (D-18); spajanje je samo način rezanja.
"""
import argparse
import sys

from .. import db

# nalozi koji čekaju rezanje: potvrđeni i pripremljeni, ali još nisu u proizvodnji ni zatvoreni (D-35)
STATUSI_ZA_REZANJE = ("potvrdjeno", "skladiste", "pila_nesting")


def _redovi(conn, statusi):
    q = """
    SELECT n.id nalog_id, n.broj, n.naziv, n.status, n.rok_obecan, n.prioritet,
           nm.id nm_id, nm.put, nm.ploca_L nm_L, nm.ploca_W nm_W,
           m.id materijal_id, m.pantheon_ident ident, m.naziv_kratki kratki, m.naziv_pantheon naziv_pun,
           m.debljina, m.god, m.winstore_kod, COALESCE(nm.ploca_L, m.ploca_L) pL, COALESCE(nm.ploca_W, m.ploca_W) pW,
           SUM(e.L * e.W * e.kom) / 1e6 m2, SUM(e.kom) kom, COUNT(*) redaka
    FROM nalog n
    JOIN nalog_materijal nm ON nm.nalog_id = n.id
    JOIN materijal m ON m.id = nm.materijal_id
    JOIN element e ON e.nalog_materijal_id = nm.id
    WHERE n.status IN (%s) AND nm.provjeri = 0
    GROUP BY nm.id ORDER BY m.pantheon_ident, n.broj""" % ",".join("?" * len(statusi))
    out = []
    for r in conn.execute(q, statusi):
        d = dict(r)
        d["ploca_m2"] = ((d["pL"] or 2800) * (d["pW"] or 2070)) / 1e6
        d["ploca"] = d["m2"] / d["ploca_m2"] if d["ploca_m2"] else 0.0
        d["restl"] = bool(d["nm_L"] or d["nm_W"])            # nalog je vezan na konkretnu ploču/restl — ne spaja se
        out.append(d)
    return out


def _cijelih(x):
    return int(-(-x // 1))            # ploča se kupuje cijela


def kandidati(conn, statusi=STATUSI_ZA_REZANJE, prag_ploca=1.0):
    """Materijali koje traži više naloga; prijedlog samo ako zbroj dosegne prag (zadano 1 ploča = uvjet za nesting).

    Prijedlog ima smisla u dva slučaja: (a) barem jedan nalog je sam ispod ploče — danas bi išao na pilu, spojen ide na
    nesting; (b) zaokruživanje na cijele ploče gubi ploču ili više. Grupe u kojima svaki nalog i sam puni ploču bez
    gubitka se preskaču. Vraća naloge, zbroj kvadrature, ploče zasebno vs. spojeno i najraniji rok.
    """
    po_materijalu = {}
    for r in _redovi(conn, statusi):
        if r["restl"]:
            continue
        po_materijalu.setdefault(r["materijal_id"], []).append(r)
    out = []
    for mid, lst in po_materijalu.items():
        if len(lst) < 2:
            continue
        zbroj = sum(x["ploca"] for x in lst)
        if zbroj < prag_ploca:
            continue
        zasebno = sum(_cijelih(x["ploca"]) for x in lst)
        spojeno = _cijelih(zbroj)
        ispod = sum(1 for x in lst if x["ploca"] < 1)
        if not ispod and zasebno == spojeno:
            continue          # svaki nalog i sam puni ploču i zaokruživanje ništa ne gubi — spajanje ne donosi ništa
        rokovi = sorted(x["rok_obecan"] for x in lst if x["rok_obecan"])
        p = lst[0]
        out.append(dict(materijal_id=mid, ident=p["ident"], naziv=p["kratki"] or p["naziv_pun"], naziv_pun=p["naziv_pun"],
                        debljina=p["debljina"], god=p["god"], winstore_kod=p["winstore_kod"],
                        naloga=len(lst), ispod_ploce=ispod,
                        m2=round(sum(x["m2"] for x in lst), 2), kom=sum(x["kom"] for x in lst),
                        ploca=round(zbroj, 2), ploca_zasebno=zasebno, ploca_spojeno=spojeno, usteda=zasebno - spojeno,
                        rok_najraniji=rokovi[0] if rokovi else None,
                        stavke=[dict(nalog_id=x["nalog_id"], broj=x["broj"], naziv=x["naziv"], status=x["status"],
                                     put=x["put"], m2=round(x["m2"], 2), kom=x["kom"], ploca=round(x["ploca"], 2),
                                     rok_obecan=x["rok_obecan"], prioritet=x["prioritet"], nm_id=x["nm_id"]) for x in
                                sorted(lst, key=lambda y: -y["ploca"])]))
    # najprije prijedlozi koji naloge s pile prebacuju na nesting, pa oni koji štede ploče
    return sorted(out, key=lambda x: (-(x["ispod_ploce"] + x["usteda"]), -x["ispod_ploce"], -x["ploca"]))


def sazetak(conn, statusi=STATUSI_ZA_REZANJE, prag_ploca=1.0):
    red = _redovi(conn, statusi)
    kand = kandidati(conn, statusi, prag_ploca)
    return dict(prijedlozi=kand, redaka=len(red), naloga=len({x["nalog_id"] for x in red}),
                ispod_ploce=sum(1 for x in red if x["ploca"] < 1 and not x["restl"]),
                na_restlu=sum(1 for x in red if x["restl"]),
                usteda=sum(x["usteda"] for x in kand), prag=prag_ploca, statusi=list(statusi))


def markdown(s):
    L = ["# Prijedlozi spajanja naloga za nesting", "",
         "Nalozi koji čekaju rezanje (%s) i traže isti materijal. Hub predlaže, voditelj odlučuje — ništa se ne spaja samo." % ", ".join(s["statusi"]), "",
         "Uvjet: zbroj svih naloga za taj materijal je barem %s ploča (ispod toga se ionako ne isplati nesting)." % s["prag"], "",
         "**Stanje:** %d naloga, %d kombinacija nalog × materijal, od toga %d ispod jedne ploče%s. "
         % (s["naloga"], s["redaka"], s["ispod_ploce"], (", %d vezano na restl (ne spaja se)" % s["na_restlu"]) if s["na_restlu"] else ""),
         "Prijedloga: **%d** — spajanjem bi %d naloga umjesto na pilu otišlo na nesting, a razlika u pločama je %d."
         % (len(s["prijedlozi"]), sum(x["ispod_ploce"] for x in s["prijedlozi"]), s["usteda"]), ""]
    if not s["prijedlozi"]:
        L += ["Trenutno nema materijala koji bi se isplatilo spojiti.", ""]
        return "\n".join(L)
    for i, k in enumerate(s["prijedlozi"], 1):
        L += ["## %d. %s — %s (%s)" % (i, k["ident"], k["naziv"], k["naziv_pun"]), "",
              "%d naloga%s · %s m² · %d komada · %s ploča ukupno · zasebno %d ploča → spojeno %d (razlika %d)%s%s"
              % (k["naloga"], (" (**%d ispod ploče — danas bi išli na pilu**)" % k["ispod_ploce"]) if k["ispod_ploce"] else "",
                 k["m2"], k["kom"], k["ploca"], k["ploca_zasebno"], k["ploca_spojeno"], k["usteda"],
                 " · najraniji rok %s" % k["rok_najraniji"] if k["rok_najraniji"] else "",
                 " · materijal s godom" if k["god"] else ""), "",
              "| Nalog | Kupac / naziv | m² | Ploča | Komada | Put | Rok |", "|---|---|---|---|---|---|---|"]
        for x in k["stavke"]:
            L.append("| %s | %s | %s | %s%s | %d | %s | %s |" % (
                x["broj"], x["naziv"], x["m2"], x["ploca"], " ⟵ ispod ploče" if x["ploca"] < 1 else "",
                x["kom"], x["put"] or "—", x["rok_obecan"] or "—"))
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Prijedlozi spajanja malih naloga u jedan nesting posao (D-54)")
    ap.add_argument("--db")
    ap.add_argument("--prag", type=float, default=1.0, help="najmanji zbroj u pločama da bi se spajanje predložilo (zadano 1)")
    ap.add_argument("--status", action="append", default=[], help="status naloga koji se gleda (može više puta)")
    ap.add_argument("--md", help="spremi Markdown izvještaj")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    s = sazetak(conn, tuple(a.status) or STATUSI_ZA_REZANJE, a.prag)
    print("Nalozi koji cekaju rezanje: %d (%d kombinacija nalog x materijal, %d ispod jedne ploce)" % (s["naloga"], s["redaka"], s["ispod_ploce"]))
    for k in s["prijedlozi"]:
        print("\n%-10s %-30s %d naloga (%d ispod ploce), %s ploca ukupno; zasebno %d -> spojeno %d (razlika %d)"
              % (k["ident"], (k["naziv"] or "")[:30], k["naloga"], k["ispod_ploce"], k["ploca"], k["ploca_zasebno"], k["ploca_spojeno"], k["usteda"]))
        for x in k["stavke"]:
            print("      %-12s %-24s %6.2f m2 = %4.2f ploce %s" % (x["broj"], x["naziv"][:24], x["m2"], x["ploca"],
                                                                   "<- ispod ploce" if x["ploca"] < 1 else ""))
    print("\nPrijedloga: %d; na nesting bi umjesto na pilu otislo %d naloga, razlika u plocama %d"
          % (len(s["prijedlozi"]), sum(x["ispod_ploce"] for x in s["prijedlozi"]), s["usteda"]))
    if a.md:
        open(a.md, "w", encoding="utf-8").write(markdown(s))
        print("Izvjestaj:", a.md)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
