# -*- coding: utf-8 -*-
"""Rezultat nestinga natrag u Hub: bNest `.mno` → stvarna potrošnja ploča po materijalu naloga, razdioba po nalozima (D-38, D-54).

bNest za svaki posao (jedan materijal) zapiše `<projekt>\\OUT\\<projekt>.mno` — XML s `FOGLIO` po ploči (`SheetInfo` mjere i Winstore
šifra, `QTY` ponavljanja, `StatisticInfo PartUsedArea`) i `PROFILO` po dijelu (`OptimizedSourceName` = CIX, `LPX/LPY`, `POS` položaj,
`CUSTOM_DESCR_n` = stupci CSV-a: 2 = RN (naziv naloga), 3 = cjelina, 4 = pozicija, 5 = šifra materijala, 11 = CIX, 22 = količina).
Hub iz toga zna: koliko je ploča stvarno otišlo, iskorištenje, koji dio je na kojoj ploči — i, kad je posao spojen iz više naloga (D-54),
koliki dio ploča pripada kojem nalogu (po kvadraturi dijelova, D-38). Dio se veže na element Huba po imenu CIX-a (registar, D-23).

    py -m hub.nalozi.rezultat_nesting --db hub.db --mno "C:\\...\\OUT\\HUMER_OMIS_9_IV_BIJELI_NK_18_...mno"
    py -m hub.nalozi.rezultat_nesting --db hub.db --mapa C:\\bNest\\projekti     (svi .mno ispod mape, već uvezeni se preskaču)
"""
import argparse
import glob
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET

from .. import db
from ..db import sada, dnevnik
from . import nalozi as N


class RezultatGreska(ValueError):
    pass


def _f(x, zadano=0.0):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return zadano


def _ci(prof):
    return {c.get("name"): (c.get("value") or "") for c in prof.findall("INFO/CUSTOM_INFO")}


def procitaj(put):
    """→ dict(projekt, datum, sifra_mat, ploce=[…], dijelovi=[…], ploca, m2_bruto, m2_dijelova, iskoristenje, po_nalogu{naziv: …})."""
    try:
        t = ET.parse(put).getroot()
    except ET.ParseError as e:
        raise RezultatGreska("%s nije čitljiv XML: %s" % (put, e))
    if t.tag != "NESTING_RESULT":
        raise RezultatGreska("%s nije bNest rezultat (korijen %s)" % (put, t.tag))
    descr = (t.findtext("COMMESSA/DESCR") or "").split(";")
    r = dict(put=os.path.abspath(put), projekt=descr[0].strip() if descr else os.path.splitext(os.path.basename(put))[0],
             datum=descr[1].strip() if len(descr) > 1 else "", sifra_mat="", ploce=[], dijelovi=[])
    for f in t.findall("FOGLIO"):
        si = f.find("SheetInfo")
        st = f.find("StatisticInfo")
        qty = int(_f(f.get("QTY"), 1) or 1)
        L, W, deb = _f(si.get("DX")), _f(si.get("DY")), _f(si.get("DZ"))
        pl = dict(id=int(_f(f.get("ID"), len(r["ploce"]) + 1)), qty=qty, L=L, W=W, deb=deb, sifra_mat=si.get("Materiale") or "",
                  restl=(si.get("Resto") or "0") not in ("0", "", "False"), m2_bruto=L * W / 1e6,
                  m2_dijelova=_f(st.get("PartUsedArea") if st is not None else 0) / 1e6, bsolid=f.get("PATH") or "", dijelova=0)
        r["sifra_mat"] = r["sifra_mat"] or pl["sifra_mat"]
        for prof in f.findall("NOME/PROFILO"):
            ci = _ci(prof)
            cix = os.path.splitext((prof.findtext("OptimizedSourceName[@Value]") or prof.find("OptimizedSourceName").get("Value") or ""))[0]
            var = {v.get("NAME"): _f(v.text) for v in prof.findall("VARIABILE")}
            for pos in prof.findall("POS"):
                d = dict(ploca=pl["id"], cix=cix, naziv=(prof.find("PartName").get("Value") if prof.find("PartName") is not None else ""),
                         nalog=ci.get("CUSTOM_DESCR_2", ""), cjelina=ci.get("CUSTOM_DESCR_3", ""), pozicija=ci.get("CUSTOM_DESCR_4", ""),
                         L=var.get("LPX", 0.0), W=var.get("LPY", 0.0), x=_f(pos.findtext("X")), y=_f(pos.findtext("Y")), deg=_f(pos.findtext("DEG")))
                d["m2"] = d["L"] * d["W"] / 1e6
                r["dijelovi"].append(d)
                pl["dijelova"] += 1
        r["ploce"].append(pl)
    r["ploca"] = sum(p["qty"] for p in r["ploce"])
    r["m2_bruto"] = round(sum(p["m2_bruto"] * p["qty"] for p in r["ploce"]), 4)
    r["m2_dijelova"] = round(sum(p["m2_dijelova"] * p["qty"] for p in r["ploce"]), 4)
    r["iskoristenje"] = round(r["m2_dijelova"] / r["m2_bruto"], 4) if r["m2_bruto"] else 0.0
    qty_po_ploci = {p["id"]: p["qty"] for p in r["ploce"]}
    po_nalogu = {}
    for d in r["dijelovi"]:
        z = po_nalogu.setdefault(d["nalog"] or "?", dict(dijelova=0, m2=0.0))
        z["dijelova"] += qty_po_ploci.get(d["ploca"], 1)
        z["m2"] += d["m2"] * qty_po_ploci.get(d["ploca"], 1)
    uk = sum(z["m2"] for z in po_nalogu.values()) or 1.0
    for z in po_nalogu.values():                                    # razdioba po kvadraturi (D-38): udio × ploče
        z["m2"] = round(z["m2"], 4)
        z["udio"] = round(z["m2"] / uk, 4)
        z["ploca"] = round(z["udio"] * r["ploca"], 2)
    r["po_nalogu"] = po_nalogu
    return r


def _hash(put):
    return hashlib.sha1(open(put, "rb").read()).hexdigest()


def _elementi_po_cix(conn, imena):
    """cix ime → (element_id, nalog_materijal_id, nalog_id) preko registra (D-23), inače preko element.cix_ime."""
    out = {}
    for ime in set(i for i in imena if i):
        r = conn.execute("SELECT e.id, e.nalog_materijal_id, nm.nalog_id FROM element e JOIN nalog_materijal nm ON nm.id = e.nalog_materijal_id "
                         "WHERE e.cix_ime = ? COLLATE NOCASE", (ime,)).fetchone()
        if not r:
            reg = conn.execute("SELECT element_id FROM cix_registar WHERE ime = ? COLLATE NOCASE AND element_id IS NOT NULL", (ime,)).fetchone()
            if reg:
                r = conn.execute("SELECT e.id, e.nalog_materijal_id, nm.nalog_id FROM element e JOIN nalog_materijal nm ON nm.id = e.nalog_materijal_id WHERE e.id = ?",
                                 (reg["element_id"],)).fetchone()
        if r:
            out[ime.upper()] = (r["id"], r["nalog_materijal_id"], r["nalog_id"])
    return out


def upisi(conn, put, tko="web", suho=False):
    """Pročitaj .mno i upiši rezultat u `optimizacija` (engine bNest) za svaki materijal naloga čiji su dijelovi u poslu.
    Vraća izvještaj: rezultat + veze (po materijalu naloga: ploča, m2, udio) + upozorenja. Isti .mno (hash) drugi put se preskače."""
    r = procitaj(put)
    h = _hash(put)
    vec = conn.execute("SELECT nalog_id FROM dokument WHERE vrsta = 'mno' AND hash = ?", (h,)).fetchone()
    izv = dict(put=r["put"], projekt=r["projekt"], sifra_mat=r["sifra_mat"], ploca=r["ploca"], m2_bruto=r["m2_bruto"], m2_dijelova=r["m2_dijelova"],
               iskoristenje=r["iskoristenje"], dijelova=len(r["dijelovi"]), po_nalogu=r["po_nalogu"], veze=[], upozorenja=[], preskoceno=bool(vec), suho=suho)
    if vec:
        izv["upozorenja"].append("ovaj .mno je već uvezen (nalog id %s)" % vec["nalog_id"])
        return izv
    veze = _elementi_po_cix(conn, [d["cix"] for d in r["dijelovi"]])
    nepoznati = sorted({d["cix"] for d in r["dijelovi"] if d["cix"].upper() not in veze})
    if nepoznati:
        izv["upozorenja"].append("%d dijelova nema element u Hubu (CIX: %s%s)" % (len(nepoznati), ", ".join(nepoznati[:6]), " …" if len(nepoznati) > 6 else ""))
    if not veze:
        izv["upozorenja"].append("nijedan dio nije vezan uz nalog u Hubu — rezultat nije upisan")
        return izv
    qty = {p["id"]: p["qty"] for p in r["ploce"]}
    po_nm = {}
    for d in r["dijelovi"]:
        v = veze.get(d["cix"].upper())
        if not v:
            continue
        z = po_nm.setdefault(v[1], dict(nalog_id=v[2], dijelova=0, m2=0.0, elementi=set()))
        z["dijelova"] += qty.get(d["ploca"], 1)
        z["m2"] += d["m2"] * qty.get(d["ploca"], 1)
        z["elementi"].add(v[0])
    uk_m2 = sum(d["m2"] * qty.get(d["ploca"], 1) for d in r["dijelovi"]) or 1.0
    for nm_id, z in po_nm.items():
        m = N.materijal_naloga(conn, nm_id)
        n = N.nalog(conn, z["nalog_id"])
        udio = z["m2"] / uk_m2
        el_uk = conn.execute("SELECT COUNT(*), COALESCE(SUM(kom), 0) FROM element WHERE nalog_materijal_id = ?", (nm_id,)).fetchone()
        v = dict(nalog_id=z["nalog_id"], nalog=n["naziv"], nalog_materijal_id=nm_id, materijal=m["naziv_kratki"] or m["naziv_ulaz"], ident=m["ident"],
                 dijelova=z["dijelova"], komada_u_nalogu=int(el_uk[1]), m2_dijelova=round(z["m2"], 4), udio=round(udio, 4),
                 ploca=round(udio * r["ploca"], 2), m2_bruto=round(udio * r["m2_bruto"], 4), spojeno=len(po_nm) > 1)
        if z["dijelova"] < int(el_uk[1]):
            v["napomena"] = "u poslu je %d od %d komada materijala" % (z["dijelova"], int(el_uk[1]))
        if m["winstore_kod"] and r["sifra_mat"] and m["winstore_kod"].upper() != r["sifra_mat"].upper():
            izv["upozorenja"].append("%s: bNest je rezao %s, a materijal naloga ima šifru %s" % (n["naziv"], r["sifra_mat"], m["winstore_kod"]))
        izv["veze"].append(v)
    if suho:
        return izv
    try:
        for v in izv["veze"]:
            cur = conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, hash, datum) VALUES (?, 'mno', ?, ?, ?)", (v["nalog_id"], r["put"], h, sada()))
            conn.execute("INSERT INTO optimizacija (nalog_materijal_id, engine, nacin, datum, broj_ploca, iskoristenje, m2_dijelova, m2_ploca, "
                         "m2_za_naplatu, rezova, sheme_json, dokument_id) VALUES (?, 'bNest', ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)",
                         (v["nalog_materijal_id"], "spojeno" if v["spojeno"] else "nesting", sada(), v["ploca"], r["iskoristenje"], v["m2_dijelova"], v["m2_bruto"],
                          json.dumps(dict(projekt=r["projekt"], datum_bnest=r["datum"], ploce=r["ploce"], po_nalogu=r["po_nalogu"], udio=v["udio"],
                                          dijelovi=[d for d in r["dijelovi"] if veze.get(d["cix"].upper(), (0, None))[1] == v["nalog_materijal_id"]]),
                                     ensure_ascii=False), cur.lastrowid))
            conn.execute("UPDATE nalog_materijal SET status_opt = 'nesting_gotov' WHERE id = ?", (v["nalog_materijal_id"],))
            posao = conn.execute("SELECT sp.id, sp.naziv FROM spojeni_posao sp JOIN spojeni_posao_stavka s ON s.posao_id = sp.id "
                                 "WHERE s.nalog_materijal_id = ? AND ? LIKE sp.naziv || '%'", (v["nalog_materijal_id"], r["projekt"])).fetchone()
            if posao:                                                           # bNest projekt nosi ime našeg CSV-a → posao je gotov
                conn.execute("UPDATE spojeni_posao SET mno_dokument_id = COALESCE(mno_dokument_id, ?) WHERE id = ?", (cur.lastrowid, posao["id"]))
                v["spojeni_posao"] = posao["naziv"]
            dnevnik(conn, tko, "nalog_materijal", v["nalog_materijal_id"], "rezultat_nesting",
                    "%s: %s ploča (udio %.0f %% od %d), isk. %.1f %%, %d dijelova" % (r["projekt"], v["ploca"], v["udio"] * 100, r["ploca"], r["iskoristenje"] * 100, v["dijelova"]))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return izv


def upisi_mapu(conn, mapa, tko="web", suho=False):
    """Svi .mno ispod mape (bNest projekti); već uvezeni (hash) se preskaču. Vraća popis izvještaja."""
    out = []
    for p in sorted({os.path.normpath(x) for u in ("*.mno", "*.MNO") for x in glob.glob(os.path.join(mapa, "**", u), recursive=True)}):
        try:
            out.append(upisi(conn, p, tko, suho))
        except RezultatGreska as e:
            out.append(dict(put=p, greska=str(e), veze=[], upozorenja=[], preskoceno=False))
    return out


def usporedba(conn, nalog_id):
    """Naplaćeno (PW-metoda, Hub) vs potrošeno (bNest) po materijalu naloga (D-38) — zadnji zapis svakog engine-a."""
    out = []
    for nm in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? ORDER BY rb, id", (nalog_id,)).fetchall():
        m = N.materijal_naloga(conn, nm["id"])
        red = dict(nalog_materijal_id=nm["id"], materijal=m["naziv_kratki"] or m["naziv_ulaz"], ident=m["ident"], put=m["put"], hub=None, bnest=None)
        for eng, k in (("hub", "hub"), ("bNest", "bnest")):
            r = conn.execute("SELECT id, nacin, datum, broj_ploca, iskoristenje, m2_dijelova, m2_ploca, m2_za_naplatu, rezova, sheme_json FROM optimizacija "
                             "WHERE nalog_materijal_id = ? AND engine = ? AND (status IS NULL OR status = 'potvrdjeno') ORDER BY id DESC LIMIT 1", (nm["id"], eng)).fetchone()
            if r:
                d = dict(r)
                try:
                    d["sheme_json"] = json.loads(d["sheme_json"]) if d["sheme_json"] else None
                except ValueError:
                    pass
                red[k] = d
        sp = conn.execute("SELECT sp.naziv, sp.mno_dokument_id FROM spojeni_posao sp JOIN spojeni_posao_stavka s ON s.posao_id = sp.id "
                          "WHERE s.nalog_materijal_id = ? ORDER BY sp.id DESC LIMIT 1", (nm["id"],)).fetchone()
        red["spojeni_posao"] = dict(naziv=sp["naziv"], rezultat_stigao=bool(sp["mno_dokument_id"])) if sp else None
        if red["hub"] and red["bnest"]:
            red["razlika_ploca"] = round((red["bnest"]["broj_ploca"] or 0) - (red["hub"]["broj_ploca"] or 0), 2)
        out.append(red)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rezultat nestinga (.mno) → potrošnja ploča po materijalu naloga")
    ap.add_argument("--db")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--mno", help="jedna .mno datoteka")
    g.add_argument("--mapa", help="mapa bNest projekata (svi .mno ispod nje)")
    ap.add_argument("--suho", action="store_true", help="samo pročitaj i poveži, ne upisuj")
    ap.add_argument("--tko", default="web")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    try:
        rez = [upisi(conn, a.mno, a.tko, a.suho)] if a.mno else upisi_mapu(conn, a.mapa, a.tko, a.suho)
    except RezultatGreska as e:
        print("GRESKA:", e)
        return 1
    for r in rez:
        if r.get("greska"):
            print("%s: GRESKA %s" % (os.path.basename(r["put"]), r["greska"]))
            continue
        print("%s%s: %s  %d ploca, isk. %.1f %%, %d dijelova, %.2f m2 dijelova / %.2f m2 ploca%s"
              % ("[suho] " if a.suho else "", r["projekt"], r["sifra_mat"], r["ploca"], r["iskoristenje"] * 100, r["dijelova"], r["m2_dijelova"], r["m2_bruto"],
                 "   (preskočeno — već uvezen)" if r["preskoceno"] else ""))
        for v in r["veze"]:
            print("   %-28s %-26s %5.2f ploca (%3.0f %%)  %d dijelova%s" % (v["nalog"][:28], (v["materijal"] or "")[:26], v["ploca"], v["udio"] * 100, v["dijelova"],
                                                                       "   " + v["napomena"] if v.get("napomena") else ""))
        for u in r["upozorenja"]:
            print("   PAZI:", u)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
