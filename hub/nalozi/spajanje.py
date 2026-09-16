# -*- coding: utf-8 -*-
"""Prijedlozi spajanja malih naloga u jedan nesting posao (D-54).

Više naloga koji čekaju proizvodnju često traže isti materijal, svaki u količini manjoj od jedne ploče — pa svaki
zasebno ide na pilu. Ako se ti dijelovi režu zajedno, stane ih se više na istu ploču i posao ide na nesting, koji je
brži i precizniji. Hub to samo PREDLAŽE; voditelj odlučuje što spaja (D-34).

    py -m hub.nalozi.spajanje --db hub.db
    py -m hub.nalozi.spajanje --db hub.db --md prijedlozi.md --prag 1
    py -m hub.nalozi.spajanje --db hub.db --izvezi 12,15,18 --mapa C:\PPNESTING [--suho] [--forsiraj]   (korak B: stvarno spajanje)

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
        d["ploca"] = d["m2"] / d["ploca_m2"] if d["ploca_m2"] else 0.0     # neto m² dijelova / ploča — procjena, ne PW-metoda (D-18); dovoljno za prijedlog
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
        if r["restl"] or (r["debljina"] or 0) > 26:          # vezano na restl, ili deblje nego što nesting reže (nalog_io.alat_za_debljinu)
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
    ap.add_argument("--izvezi", help="korak B: id-ovi materijala naloga (nm_id iz prijedloga) odvojeni zarezom → jedan CSV+CIX paket")
    ap.add_argument("--mapa", default=".", help="korijen izvoza (nastaje <mapa>\\SPOJ_<MATERIJAL>_<zig>\\NESTING\\)")
    ap.add_argument("--stil", choices=("bsolid", "ppnest"), default="bsolid")
    ap.add_argument("--suho", action="store_true")
    ap.add_argument("--forsiraj", action="store_true", help="i nalozi koji još nisu potvrđeni (probe)")
    ap.add_argument("--tko", default="web")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    if a.izvezi:
        try:
            r = izvezi_spojeno(conn, [x for x in a.izvezi.split(",") if x.strip()], a.mapa, a.tko, a.stil, a.suho, a.forsiraj)
        except (SpajanjeGreska, ValueError) as e:
            print("GRESKA:", e)
            return 1
        print("%s%s -> %s" % ("[suho] " if a.suho else "", r["naziv"], r["mapa"]))
        print("   %-28s %-12s %4s mm  %d naloga  %3d el / %3d kom  %7.2f m2  %d CIX%s" % (r["materijal"][:28], r["winstore_kod"] or "-", r["debljina"], r["naloga"],
                                                                                      r["elemenata"], r["komada"], r["m2"], len(r["cix"]), " (%d iz Corpusa)" % r["cix_corpus"] if r["cix_corpus"] else ""))
        for st in r["stavke"]:
            print("      %-28s %3d el / %3d kom  %6.2f m2  (put prije: %s)" % (st["nalog"][:28], st["elemenata"], st["komada"], st["m2"], st["put_prije"] or "—"))
        for u in r["upozorenja"]:
            print("   PAZI:", u)
        conn.close()
        return 0
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


# ---------------------------------------------------------------- stvarno spajanje (korak B): jedan CSV + CIX paket iz više naloga
class SpajanjeGreska(ValueError):
    pass


def _nm_za_spajanje(conn, nm_ids):
    from . import nalozi as N
    out = []
    for nm_id in nm_ids:
        m = N.materijal_naloga(conn, int(nm_id))
        m["nalog"] = N.nalog(conn, m["nalog_id"])
        out.append(m)
    return out


def izvezi_spojeno(conn, nm_ids, mapa, tko="web", stil="bsolid", suho=False, forsiraj=False, vrijeme=None):
    """Više materijala naloga (isti materijal) → JEDAN nesting posao: `<mapa>\\SPOJ_<MATERIJAL>_<zig>\\NESTING\\` s jednim CSV-om
    (RN = naziv naloga po elementu, pa etiketa i .mno znaju čiji je dio) i CIX-om po elementu (Hubov ili kopija Corpusovog).
    Svaki nalog zadržava svoj obračun (D-18); ovdje se bilježi samo da je rezan u spojenom poslu (`spojeni_posao`, D-54/B)."""
    import os
    import datetime
    from ..db import sada, dnevnik
    from ..formati import nalog_io
    from . import nalozi as N, export_nesting as EX
    nm_ids = [int(x) for x in nm_ids]
    if len(set(nm_ids)) < 2:
        raise SpajanjeGreska("za spajanje trebaju barem dva materijala naloga")
    mats = _nm_za_spajanje(conn, nm_ids)
    if any(not m["materijal_id"] for m in mats):
        raise SpajanjeGreska("svi materijali moraju biti potvrđeni (ident)")
    if len({m["materijal_id"] for m in mats}) > 1:
        raise SpajanjeGreska("spajaju se samo nalozi ISTOG materijala (%s)" % ", ".join(sorted({m["ident"] for m in mats})))
    if len({m["nalog_id"] for m in mats}) < len(mats):
        raise SpajanjeGreska("isti nalog je naveden dvaput")
    if any(m["ploca_L"] or m["ploca_W"] for m in mats):
        raise SpajanjeGreska("materijal vezan na restl / vlastitu ploču se ne spaja")
    upozorenja = []
    for m in mats:
        upozorenja += EX.provjeri_spremnost(conn, m["nalog"], forsiraj, suho)
    deb = mats[0]["debljina"] or mats[0]["debljina_ulaz"]
    if not deb:
        raise SpajanjeGreska("nepoznata debljina materijala")
    try:
        nalog_io.alat_za_debljinu(deb)
    except ValueError as e:
        raise SpajanjeGreska(str(e))
    if not suho:
        for m in mats:
            EX.dodijeli_imena(conn, m["nalog_id"], tko)
    grupa, stavke = [], []
    for m in mats:
        els = [e for e in N.elementi_za_export(conn, m["nalog_id"]) if e["nalog_materijal_id"] == m["id"]]
        if not els:
            raise SpajanjeGreska("%s: materijal nema elemenata" % m["nalog"]["naziv"])
        stavke.append(dict(nalog_id=m["nalog_id"], nalog=m["nalog"]["naziv"], nalog_materijal_id=m["id"], elemenata=len(els),
                           komada=sum(x["kom"] for x in els), m2=round(sum(x["L"] * x["W"] * x["kom"] for x in els) / 1e6, 3), put_prije=m["put"]))
        grupa += els
    mat_ime = EX._bez_dij(mats[0]["naziv_kratki"] or mats[0]["naziv_ulaz"] or mats[0]["ident"])
    zig = (vrijeme or datetime.datetime.now()).strftime("%d%m%y_%H%M%S")
    naziv = "SPOJ_%s_%s" % (mat_ime, zig)
    korijen = os.path.join(mapa, naziv, "NESTING")
    for i, e in enumerate(grupa, 1):
        e["rb"] = i
        e["mat"] = mat_ime
    csv_put = os.path.join(korijen, naziv + ".CSV")
    kopije, hub_pise = EX._prenesi_corpus_cix(grupa, korijen, suho)
    cix = [os.path.join(korijen, (x["cix"] or "") + ".cix") for x in hub_pise] + kopije
    rez = dict(naziv=naziv, mapa=korijen, csv=csv_put, materijal=mat_ime, ident=mats[0]["ident"], winstore_kod=mats[0]["winstore_kod"] or "",
               debljina=deb, naloga=len(stavke), elemenata=len(grupa), komada=sum(x["kom"] for x in grupa),
               m2=round(sum(x["L"] * x["W"] * x["kom"] for x in grupa) / 1e6, 3), cix=cix, cix_corpus=len(kopije), stavke=stavke,
               stil=stil, suho=suho, upozorenja=upozorenja, bez_winstore_koda=not (mats[0]["winstore_kod"] or ""))
    if suho:
        return rez
    try:
        os.makedirs(korijen, exist_ok=True)
        nalog_io.write_ppnest_csv(grupa, csv_put)
        nalog_io.write_cix(hub_pise, korijen, stil=stil)
        cur = conn.execute("INSERT INTO spojeni_posao (naziv, materijal_id, kada, tko_id, mapa, csv, elemenata, komada, m2, cix) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (naziv, mats[0]["materijal_id"], sada(), N.korisnik_id(conn, tko), korijen, csv_put, rez["elemenata"], rez["komada"], rez["m2"], len(cix)))
        posao_id = cur.lastrowid
        for st, m in zip(stavke, mats):
            conn.execute("INSERT INTO spojeni_posao_stavka (posao_id, nalog_id, nalog_materijal_id, elemenata, komada, m2) VALUES (?,?,?,?,?,?)",
                         (posao_id, st["nalog_id"], st["nalog_materijal_id"], st["elemenata"], st["komada"], st["m2"]))
            conn.execute("UPDATE nalog_materijal SET put = 'nesting', status_opt = ? WHERE id = ?", ("spojeno:" + naziv, st["nalog_materijal_id"]))
            conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, datum) VALUES (?, 'csv', ?, ?)", (st["nalog_id"], csv_put, sada()))
            for x in cix:
                if any(os.path.splitext(os.path.basename(x))[0] in ((e["cix"] or ""), (e.get("program2") or "")) for e in grupa if e["nalog_materijal_id"] == st["nalog_materijal_id"]):
                    conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, datum) VALUES (?, 'cix', ?, ?)", (st["nalog_id"], x, sada()))
            EX._dogadjaj_izvoza(conn, m["nalog"], tko, "izvoz na nesting u spojenom poslu %s (%d naloga, %d el)" % (naziv, len(stavke), rez["elemenata"]), "mapa:" + korijen)
        dnevnik(conn, tko, "spojeni_posao", posao_id, "izvoz_nesting", "%s: %d naloga, %d el / %d kom, %d CIX" % (naziv, len(stavke), rez["elemenata"], rez["komada"], len(cix)))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    rez["posao_id"] = posao_id
    return rez


def poslovi(conn, limit=100):
    """Spojeni poslovi s nalozima koje sadrže (najnoviji prvi) i je li se rezultat (.mno) vratio."""
    out = []
    for p in conn.execute("SELECT sp.*, m.pantheon_ident ident, m.naziv_kratki FROM spojeni_posao sp LEFT JOIN materijal m ON m.id = sp.materijal_id "
                          "ORDER BY sp.id DESC LIMIT ?", (limit,)).fetchall():
        d = dict(p)
        d["stavke"] = [dict(r) for r in conn.execute("SELECT s.*, n.naziv nalog, n.status FROM spojeni_posao_stavka s JOIN nalog n ON n.id = s.nalog_id "
                                                     "WHERE s.posao_id = ? ORDER BY s.id", (p["id"],)).fetchall()]
        d["rezultat_stigao"] = bool(p["mno_dokument_id"])
        out.append(d)
    return out
