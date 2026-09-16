# -*- coding: utf-8 -*-
"""Uvoz Corpusovog paketa u nalog (D-29, D-30 ulaz B, D-55; 08 §4.3) — kralježnica korak 3c.

Tehnička priprema iz Corpusa izveze mapu projekta (`...\\NESTING\\<PROJEKT>`): CSV za nesting + CIX po elementu
(+ podmapa `HORIZONTALNO_BUSENJE` s drugim CIX-om za bušenje u kant), a CPW-ove po materijalu u sestrinsku mapu
`<PROJEKT_S_PODVLAKAMA>`. Hub tu mapu pročita, spoji i PROVJERI — ništa ne mijenja u datotekama (Corpus je CAM autoritet):

  * CPW = svi elementi po materijalu (i oni koji idu na pilu); CSV = samo elementi za nesting (D-55/2)
  * svaki element s programom mora imati CIX datoteku; mjere u CIX-u (LPX × LPY) moraju biti mjere elementa
  * element s PROGRAM2 mora imati i drugi CIX (D-55/3) — Hub prenosi oba
  * imena CIX-a idu u registar (D-23) — Corpusovo ime koje je već zauzeto zaustavlja uvoz (D-55), ne preimenuje se
  * put po materijalu: ima elemenata u CSV-u → nesting, inače → pila (leđa MDF); voditelj to može promijeniti (D-34)
  * nalog je uvijek `vrsta = vlastita_proizvodnja` (D-55/4); ID elementa iz Corpusa (cjelina + pozicija) ostaje na etiketi (D-55/5)

    py -m hub.nalozi.uvoz_corpus --db hub.db --mapa "C:\\...\\NESTING\\TEST BUSENJE" [--kupac HUMER] [--suho]
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

from .. import db
from ..db import sada, dnevnik
from ..formati import nalog_io, cix_citaj
from ..sifrarnici.nazivi import norm
from . import nalozi as N, uvoz_datoteka as U, export_nesting as EN

PODMAPA_KANT = "HORIZONTALNO_BUSENJE"


class CorpusGreska(ValueError):
    pass


def _nadji(mapa, uzorak, rekurzivno=True):
    out = set()
    for u in {uzorak, uzorak.lower(), uzorak.upper()}:
        out |= {os.path.normpath(p) for p in glob.glob(os.path.join(mapa, "**", u) if rekurzivno else os.path.join(mapa, u), recursive=rekurzivno)}
    return sorted(out)


def pronadji_paket(mapa):
    """Što je u mapi: CPW-ovi (i u sestrinskoj mapi s podvlakama), CSV, CIX-ovi (glavni i za kant), S3D projekt, ime projekta."""
    mapa = os.path.normpath(mapa)
    if not os.path.isdir(mapa):
        raise CorpusGreska("mapa ne postoji: %s" % mapa)
    cpw = _nadji(mapa, "*.cpw")
    csv = _nadji(mapa, "*.csv")
    cix = _nadji(mapa, "*.cix")
    if not cpw:                                        # Corpus CPW-ove piše u sestrinsku mapu <PROJEKT_S_PODVLAKAMA>
        sestra = os.path.join(os.path.dirname(mapa), os.path.basename(mapa).replace(" ", "_"))
        if os.path.isdir(sestra) and sestra != mapa:
            cpw = _nadji(sestra, "*.cpw")
    kant = {os.path.splitext(os.path.basename(p))[0].upper(): p for p in cix if PODMAPA_KANT.lower() in p.lower().split(os.sep)}
    glavni = {os.path.splitext(os.path.basename(p))[0].upper(): p for p in cix if PODMAPA_KANT.lower() not in p.lower().split(os.sep)}
    s3d = _nadji(mapa, "*.s3d") or _nadji(os.path.dirname(mapa), "*.s3d", rekurzivno=False)
    if csv:
        projekt = os.path.splitext(os.path.basename(csv[0]))[0]
    elif cix:
        projekt = os.path.basename(os.path.dirname(glavni[next(iter(glavni))] if glavni else cix[0]))
    else:
        projekt = os.path.basename(mapa)
    return dict(mapa=mapa, projekt=projekt, cpw=cpw, csv=csv, cix=glavni, cix_kant=kant, s3d=s3d)


def _kljuc_el(sifra_mat, L, W, cjelina, pozicija):
    a, b = sorted((round(float(L), 1), round(float(W), 1)))
    return (norm(sifra_mat or ""), a, b, norm(cjelina or ""), norm(pozicija or ""))


def procitaj_paket(paket):
    """Pročitaj CPW-ove i CSV, spoji ih po CIX imenu / mjerama, provjeri CIX-ove. Ništa ne piše.
    Vraća dict(elementi=[...po CPW-u...], greske=[], upozorenja=[], nesting=n, pila=n, cix=n)."""
    greske, upozorenja = [], []
    if not paket["cpw"]:
        greske.append("nema nijedne CPW datoteke (Corpus ih piše po materijalu u mapu %s)" % os.path.basename(paket["mapa"]).replace(" ", "_"))
    if len(paket["csv"]) > 1:
        greske.append("više CSV datoteka u paketu: %s — Hub očekuje jednu po projektu" % ", ".join(os.path.basename(p) for p in paket["csv"]))
    if greske:
        raise CorpusGreska("; ".join(greske))
    po_cpw = []                                        # [(putanja, [elementi])]
    svi = []
    for p in paket["cpw"]:
        els = nalog_io.read_cpw(p)
        if not els:
            upozorenja.append("%s: prazna datoteka" % os.path.basename(p))
        for e in els:
            e["_cpw"] = p
            e["_csv"] = None
            e["cix_izvor"] = None
        po_cpw.append((p, els))
        svi += els
    if not svi:
        raise CorpusGreska("CPW datoteke nemaju nijedan element")
    if not all(e.get("corpus") for e in svi):
        upozorenja.append("neke CPW datoteke nisu Corpusove (nemaju stupce cjelina / CIX): %s"
                          % ", ".join(sorted({os.path.basename(e["_cpw"]) for e in svi if not e.get("corpus")})))
    # CSV → elementi za nesting; spoji na CPW element po CIX imenu (kad CPW ima program) ili po materijalu + mjerama + cjelini + poziciji
    csv_els = nalog_io.read_ppnest_csv(paket["csv"][0]) if paket["csv"] else []
    if not csv_els:
        upozorenja.append("nema CSV liste za nesting — svi materijali idu na pilu" if not paket["csv"] else "CSV lista je prazna")
    po_cix = {e["program1"].upper(): e for e in svi if e.get("program1")}
    slobodni = collections.defaultdict(list)
    for e in svi:
        slobodni[_kljuc_el(e.get("sifra_mat") or e["mat"], e["L"], e["W"], e.get("cjelina"), e.get("pozicija"))].append(e)
    for r in csv_els:
        ime = (r.get("cix") or r.get("program1") or "").strip().upper()
        cilj = po_cix.get(ime) if ime else None
        if cilj is not None and cilj["_csv"] is None:
            cilj["_csv"] = r
            continue
        k = _kljuc_el(r.get("sifra_mat") or r["mat"], r["L"], r["W"], r.get("cjelina"), r.get("pozicija"))
        kand = [e for e in slobodni.get(k, []) if e["_csv"] is None and not e.get("program1")]
        if not kand:
            greske.append("CSV redak %s (%s %gx%g, %s) nema odgovarajući element u CPW-u" % (r["rb"], r.get("sifra_mat") or r["mat"], r["L"], r["W"], ime or "bez CIX"))
            continue
        kand[0]["_csv"] = r
    # CIX po elementu
    for e in svi:
        r = e["_csv"]
        ime = (e.get("program1") or (r or {}).get("cix") or "").strip()
        e["cix"] = ime
        e["cix_izvor"] = "corpus" if ime else None
        e["_obrada"] = {}
        if r:
            e["god"] = r.get("god") or 0
            e["prolaza"] = r.get("prolaza") or e.get("prolaza")
            e["napomena"] = r.get("napomena") or ""
            if int(r["kom"]) != int(e["kom"]):
                upozorenja.append("%s %s: količina u CSV-u (%s) nije kao u CPW-u (%s)" % (e.get("naziv") or "", ime, r["kom"], e["kom"]))
        oznaka = "%s %gx%g %s" % (e.get("naziv") or "?", e["L"], e["W"], ime or "")
        if ime:
            put = paket["cix"].get(ime.upper()) or paket["cix_kant"].get(ime.upper())
            if not put:
                greske.append("%s: nema CIX datoteke %s.cix u paketu" % (oznaka, ime))
            else:
                try:
                    d = cix_citaj.procitaj(put)
                except ValueError as ex:
                    greske.append("%s: %s" % (oznaka, ex))
                    continue
                if not cix_citaj.odgovara_elementu(d, e["L"], e["W"]):
                    greske.append("%s: CIX %s ima mjere %gx%g, element %gx%g" % (oznaka, ime, d["L"] or 0, d["W"] or 0, e["L"], e["W"]))
                e["_obrada"] = dict(cix=dict(ime=ime, put=put, opis=d["opis"], busenja=d["busenja"], busenja_h=d["busenja_h"], utora=d["utora"],
                                             krivolinija=d["krivolinija"], deb=d["deb"]), ima_obradu=d["ima_obradu"])
                if r is None:
                    upozorenja.append("%s: ima CIX, a nije u CSV listi za nesting" % oznaka)
        p2 = (e.get("program2") or "").strip()
        if p2:
            put2 = paket["cix_kant"].get(p2.upper()) or paket["cix"].get(p2.upper())
            if not put2:
                greske.append("%s: nema CIX datoteke za horizontalno bušenje %s.cix (podmapa %s)" % (oznaka, p2, PODMAPA_KANT))
            else:
                if p2.upper() not in paket["cix_kant"]:
                    upozorenja.append("%s: CIX za kant %s nije u podmapi %s" % (oznaka, p2, PODMAPA_KANT))
                try:
                    d2 = cix_citaj.procitaj(put2)
                    e["_obrada"]["cix2"] = dict(ime=p2, put=put2, opis=d2["opis"], busenja_h=d2["busenja_h"] or d2["busenja"])
                    e["_obrada"]["ima_obradu"] = True
                except ValueError as ex:
                    greske.append("%s: %s" % (oznaka, ex))
        if e["_obrada"]:
            e["_obrada"]["opis"] = ", ".join(x for x in (e["_obrada"].get("cix", {}).get("opis"), e["_obrada"].get("cix2", {}).get("opis")) if x)
    # element bez CSV retka, a s obradom u CIX-u, ne smije na pilu (D-29)
    for e in svi:
        if e["_csv"] is None and e["_obrada"].get("ima_obradu"):
            greske.append("%s %s: ima CNC obradu (%s), a nije u CSV listi za nesting" % (e.get("naziv") or "?", e["cix"], e["_obrada"]["opis"]))
    # CIX datoteke koje nitko ne spominje
    koristeni = {(e["cix"] or "").upper() for e in svi} | {(e.get("program2") or "").upper() for e in svi}
    visak = sorted(k for k in list(paket["cix"]) + list(paket["cix_kant"]) if k not in koristeni)
    if visak:
        upozorenja.append("CIX datoteke bez elementa u CPW/CSV (ne prenose se): %s" % ", ".join(visak[:8]) + (" …" if len(visak) > 8 else ""))
    nesting = sum(1 for e in svi if e["_csv"] is not None)
    return dict(elementi=po_cpw, svi=svi, csv=paket["csv"][0] if paket["csv"] else None, greske=greske, upozorenja=upozorenja,
                nesting=nesting, pila=len(svi) - nesting, cix=sum(1 for e in svi if e["cix"]) + sum(1 for e in svi if e.get("program2")),
                komada=sum(int(e["kom"]) for e in svi))


def uvezi_paket(conn, mapa, tko="web", kupac_id=None, kupac_kratki=None, projekt=None, izvor="corpus", broj=None, redni=None, suho=False):
    """Cijeli Corpus paket → novi nalog (vlastita proizvodnja). Greške u paketu zaustavljaju uvoz prije ijednog upisa.
    Vraća (nalog_id | None, izvještaj)."""
    paket = pronadji_paket(mapa)
    c = procitaj_paket(paket)
    izv = dict(projekt=projekt or paket["projekt"], mapa=paket["mapa"], cpw=[os.path.basename(p) for p in paket["cpw"]],
               csv=os.path.basename(c["csv"]) if c["csv"] else None, s3d=[os.path.basename(p) for p in paket["s3d"]],
               elemenata=len(c["svi"]), komada=c["komada"], nesting=c["nesting"], pila=c["pila"], cix=c["cix"],
               greske=c["greske"], upozorenja=c["upozorenja"], materijali=[], suho=suho)
    if c["greske"]:
        raise CorpusGreska("paket %s nije ispravan: " % izv["projekt"] + "; ".join(c["greske"]))
    zauzeta = [e["cix"] for e in c["svi"] if e["cix"] and (r := conn.execute("SELECT element_id FROM cix_registar WHERE ime = ?", (e["cix"],)).fetchone())
               and r["element_id"] is not None]
    if zauzeta:
        raise CorpusGreska("ime CIX datoteke već pripada drugom elementu u Hubu: %s — preimenovati u Corpusu (D-23, D-55)" % ", ".join(sorted(set(zauzeta))[:8]))
    if suho:
        return None, izv
    try:
        n = N.novi_nalog(conn, tko, kupac_id=kupac_id, kupac_kratki=kupac_kratki, projekt=izv["projekt"], vrsta="vlastita_proizvodnja",
                         izvor=izvor, corpus_projekt=paket["projekt"], broj=broj, redni=redni)
        nid = n["id"]
        uk = dict(datoteke=0, materijali_novi=0, materijali_spojeni=0, elementi=0, komada=0, za_potvrdu_materijal=0, za_potvrdu_rub=0, preskoceno=0)
        for p, els in c["elementi"]:
            ids = []
            st = U.uvezi_elemente(conn, nid, els, tko, "corpus", datoteka=p, vrsta_dok="cpw_ulaz", ids=ids)
            uk["datoteke"] += 1
            for k in st:
                uk[k] += st[k]
            for e, eid in zip(els, ids):
                conn.execute("UPDATE element SET obrada_json = ?, obrada = ? WHERE id = ?",
                             (json.dumps(e["_obrada"], ensure_ascii=False) if e["_obrada"] else None, (e["_obrada"] or {}).get("opis") or None, eid))
                e["_id"] = eid
        # put po materijalu (D-34: voditelj potvrđuje; Hub predlaže iz CSV-a) + registar imena (D-23)
        for nm in conn.execute("SELECT id, naziv_ulaz FROM nalog_materijal WHERE nalog_id = ?", (nid,)).fetchall():
            els_m = [e for e in c["svi"] if conn.execute("SELECT nalog_materijal_id FROM element WHERE id = ?", (e["_id"],)).fetchone()[0] == nm["id"]]
            u_csv = sum(1 for e in els_m if e["_csv"] is not None)
            put = "nesting" if u_csv else "pila"
            conn.execute("UPDATE nalog_materijal SET put = ?, put_prijedlog = ? WHERE id = ?", (put, put, nm["id"]))   # Corpus je put već odredio (D-55/2); voditelj smije promijeniti
            izv["materijali"].append(dict(nalog_materijal_id=nm["id"], ulaz=nm["naziv_ulaz"], put=put, elemenata=len(els_m), u_csv=u_csv))
            if 0 < u_csv < len(els_m):
                izv["upozorenja"].append("%s: %d od %d elemenata nije u CSV listi — idu na nesting bez Corpusovog CIX-a (Hub će ga napraviti)"
                                         % (nm["naziv_ulaz"], len(els_m) - u_csv, len(els_m)))
        for e in c["svi"]:
            for ime in (e["cix"], e.get("program2")):
                if ime and not EN.registriraj(conn, ime, e["_id"], nid, "corpus"):
                    raise CorpusGreska("ime CIX datoteke '%s' već pripada drugom elementu (D-23)" % ime)
        for vrsta, put in ([("csv", c["csv"])] if c["csv"] else []) + [("cix", e["_obrada"][k]["put"]) for e in c["svi"] for k in ("cix", "cix2") if k in e["_obrada"]]:
            conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, datum) VALUES (?, ?, ?, ?)", (nid, vrsta, os.path.abspath(put), sada()))
        dnevnik(conn, tko, "nalog", nid, "uvoz_corpus", "%s: %d CPW, %d el / %d kom, nesting %d, pila %d, CIX %d, za potvrdu %d mat + %d rub"
                % (paket["projekt"], len(paket["cpw"]), len(c["svi"]), c["komada"], c["nesting"], c["pila"], c["cix"], uk["za_potvrdu_materijal"], uk["za_potvrdu_rub"]))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    izv.update(nalog_id=nid, naziv=n["naziv"], uvoz=uk)
    return nid, izv


def main(argv=None):
    ap = argparse.ArgumentParser(description="Uvoz Corpusovog paketa (CPW + CSV + CIX) u nalog vlastite proizvodnje")
    ap.add_argument("--db")
    ap.add_argument("--mapa", required=True, help="mapa izvoza iz Corpusa (…\\NESTING\\<PROJEKT>) ili mapa koja sadrži cijeli paket")
    ap.add_argument("--kupac", help="kratki naziv kupca za naziv naloga (zadano KUPAC)")
    ap.add_argument("--projekt", help="naziv projekta za naziv naloga (zadano ime iz Corpusa)")
    ap.add_argument("--suho", action="store_true", help="samo provjeri paket, ne upisuj nalog")
    ap.add_argument("--tko", default="web")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    try:
        nid, izv = uvezi_paket(conn, a.mapa, a.tko, kupac_kratki=a.kupac, projekt=a.projekt, suho=a.suho)
    except CorpusGreska as e:
        print("GRESKA:", e)
        return 1
    print("%s%s: %d CPW, CSV %s, %d el / %d kom — nesting %d, pila %d, CIX %d" % ("[suho] " if a.suho else "", izv["projekt"], len(izv["cpw"]), izv["csv"] or "—",
                                                                                 izv["elemenata"], izv["komada"], izv["nesting"], izv["pila"], izv["cix"]))
    if nid:
        print("   nalog %s (id %d)" % (izv["naziv"], nid))
        for m in izv["materijali"]:
            print("   %-28s %-8s %2d el (u CSV-u %d)" % (m["ulaz"][:28], m["put"], m["elemenata"], m["u_csv"]))
    for u in izv["upozorenja"]:
        print("   PAZI:", u)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
