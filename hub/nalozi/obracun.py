# -*- coding: utf-8 -*-
"""Obračun naloga → stavke ponude (kralježnica korak 4; D-18, D-19, D-20, D-32, D-40; pravila skilla krojna-ponuda).

Za svaki materijal naloga Hub PW-metodom složi ploče (isti optimizator kao za pilu, D-19: najmanja površina za naplatu) i iz toga
izvede stavke kakve danas ured tipka u Pantheon — istim redoslijedom (materijali → trake i kantiranje → usluge → okov, D-32):

  ploča       m² za naplatu (korisni ostatak odbijen) + pravilo načete ploče: >2/3 cijela, 1/3–2/3 +0,25 m², <1/3 minimum 1/3
              (svaki dodatak piše u `pravilo`, ured ga vidi i može maknuti); restl (ploča naloga nije standardna) = cijela površina;
              radna / zidna ploča (RP, ZO) po dužnom metru = Σ dulja stranica × kom
  rezanje     US000002 (iveral i sve ostalo) / US000013 (MDF do 8 mm) po m² ploče; RP/ZO: US000303 = 2 reza × komada
  traka       PW metri (Σ stranica × kom × 1,10 — 10 % otpada je već unutra) zaokruženi NAVIŠE na cijeli metar po traci (D-20)
  kantiranje  US000003 (0,5 mm) / US000011 (1 i 2 mm /22) / US000012 (/44) = TOČNI PW metri po klasi trake (D-20)
  CNC         iz CIX-a (Corpus) ili napomene elementa: fi35 → US000149 (kom), NUT / FALC → US000016 (m), UREZ GOLA → US002075 (m);
              ostala obrada iz CIX-a (bušenje, utor, krivolinija) samo se JAVI (usluga po skici, ured dodaje ručno)
  okov        potvrđene stavke iz `okov_stavka` (D-32; nikad se ne pogađa)

Cijena je neto cijena iz Pantheona (`pantheon_ident.cijena_neto`, D-40 — u Hubu se ne mijenja); rabat je s naloga:
`rabat_materijal` za ploče, trake i okov, `rabat_usluge` za rezanje, kantiranje i CNC. Stavke se pišu u `obracun_stavka`
(bez verzije ponude = radni obračun); `ponuda.py` ih snimi u verziju.

    py -m hub.nalozi.obracun --db hub.db --nalog 12 [--bez-pravila]
"""
import argparse
import json
import math
import re
import sys

from .. import db
from ..db import sada, dnevnik, postavka
from ..optimizacija import pila_optimizator as OPT, obracun as OB
from ..sifrarnici import prepoznaj as P
from . import nalozi as N, optimiziraj as OP

US_REZANJE, US_REZANJE_MDF, US_REZ_RP = "US000002", "US000013", "US000303"
KERF_SLAGANJA = 5.0
US_FI35, US_NUT, US_UREZ_GOLA = "US000149", "US000016", "US002075"
MDF_TANKI_MM = 8
STANDARDNE_PLOCE = [(2800, 2070), (2780, 2050), (2800, 1300), (2440, 1220), (2800, 1220), (2800, 2100), (2620, 2070), (4100, 600), (4100, 640),
                    (4100, 900), (4200, 1300), (3050, 1300), (2800, 1250)]
TOL_PLOCE = 35
PDV = 0.25


class ObracunGreska(ValueError):
    pass


def _ident(conn, ident):
    r = conn.execute("SELECT ident, naziv, jm, cijena_neto, cijena_prodajna, aktivan FROM pantheon_ident WHERE ident = ?", (ident,)).fetchone()
    return dict(r) if r else None


def _standardna(L, W):
    return any((abs(L - a) <= TOL_PLOCE and abs(W - b) <= TOL_PLOCE) or (abs(L - b) <= TOL_PLOCE and abs(W - a) <= TOL_PLOCE) for a, b in STANDARDNE_PLOCE)


def pravilo_nacete_ploce(m2_naplata, ploca_kom, ploca_m2):
    """Skill krojna-ponuda §1 (Igor, kolovoz 2026): udio zadnje načete ploče f → >2/3 cijela ploča, 1/3–2/3 +0,25 m², <1/3 minimum 1/3;
    granični f 0,28–0,33 → +0,25 i oznaka PROVJERI. Vraća (m2, opis|None, provjeri)."""
    if not ploca_kom or not ploca_m2:
        return round(m2_naplata, 2), None, False
    zadnja = m2_naplata - (ploca_kom - 1) * ploca_m2
    f = zadnja / ploca_m2
    if f <= 0 or f >= 0.999:
        return round(m2_naplata, 2), None, False
    if f > 2 / 3:
        return round(m2_naplata + (ploca_m2 - zadnja), 2), "načeta ploča %.0f %% > 2/3 → cijela ploča (+%.2f m²)" % (f * 100, ploca_m2 - zadnja), False
    if f > 1 / 3:
        return round(m2_naplata + 0.25, 2), "načeta ploča %.0f %% (1/3–2/3) → +0,25 m²" % (f * 100), False
    if f > 0.28:
        return round(m2_naplata + 0.25, 2), "načeta ploča %.0f %% (granično uz 1/3) → +0,25 m² — PROVJERI" % (f * 100), True
    dod = ploca_m2 / 3 - zadnja
    return round(m2_naplata + dod, 2), "načeta ploča %.0f %% < 1/3 → minimum 1/3 ploče (+%.2f m²)" % (f * 100, dod), False


def _ploca(m):
    L = m["ploca_L"] or m["m_ploca_L"] or 2800
    W = m["ploca_W"] or m["m_ploca_W"] or 2070
    return float(L), float(W)


def _obrada_elementa(el):
    """CNC iz CIX-a (obrada_json, Corpus) ili napomene: (fi35_rupa, nut_m, urez_m, ostalo_opis)."""
    nap = (el["napomena"] or "").upper()
    kom = int(el["kom"])
    fi35 = 0
    m = re.search(r"CNC\s*(\d)\s*X?\s*FI\s*35", nap)
    if m:
        fi35 = int(m.group(1)) * kom
    nut = float(el["L"]) / 1000 * kom if re.search(r"\b(NUT|FALC)\b", nap) else 0.0
    urez = float(el["L"]) / 1000 * kom if "UREZ" in nap and "GOL" in nap else 0.0
    ostalo = []
    if "SKICA" in nap or re.search(r"\bCNC\s*[A-Z]\b", nap):
        ostalo.append("po skici: %s" % (el["napomena"] or "").strip())
    if el.get("obrada_json"):
        try:
            o = json.loads(el["obrada_json"])
        except ValueError:
            o = {}
        if o.get("ima_obradu"):
            ostalo.append("CIX: %s" % (o.get("opis") or "obrada"))
    return fi35, nut, urez, ostalo


def izracunaj(conn, nalog_id, pravila=True, kerf=None):
    """Sve stavke naloga (bez upisa). Vraća dict(stavke=[…], upozorenja=[…], po_materijalu=[…], neto, pdv, ukupno)."""
    n = N.nalog(conn, nalog_id)
    rab_m = float(n["rabat_materijal"] or 0)
    rab_u = float(n["rabat_usluge"] or 0)
    kerf = kerf if kerf is not None else OP.kerf_pile(conn)     # slaganje s fizičkim kerfom pile kao PW (D-72, postavka kerf_pile); korisni ostatak se računa s 16 (OB.KERF_OBRACUN)
    faktor_trake = 1 + float(postavka(conn, "nadmjera_trake", "10") or 0) / 100     # D-77: nadmjera trake (PW 10 %)
    rez_nacin = (postavka(conn, "obracun_rezanja", "m2") or "m2").strip()             # D-77: m2 | rezova | m_reza
    stavke, upoz, po_mat = [], [], []
    els_sve = N.elementi_za_export(conn, nalog_id)

    def rezanje(mat, deb, m2, oc, nm_id):
        """Usluga rezanja po postavci obracun_rezanja (D-77): m² ploče (zadano), broj rezova ili dužni metar reza."""
        if rez_nacin == "rezova" and oc and oc.get("rezova"):
            add(postavka(conn, "ident_rezanje_rez", US_REZ_RP) or US_REZ_RP, oc["rezova"], "rezanje", "rezanje po broju rezova (%d)" % oc["rezova"], nm_id)
            return
        if rez_nacin == "m_reza":
            ident = (postavka(conn, "ident_rezanje_m", "") or "").strip()
            if ident and oc and oc.get("m_reza"):
                add(ident, round(oc["m_reza"], 2), "rezanje", "rezanje po dužnom metru reza", nm_id)
                return
            upoz.append("obračun rezanja po dužnom metru nije moguć (%s) — stavka po m² ploče" % ("nema identa usluge (postavka ident_rezanje_m)" if not ident else "nema duljine rezova"))
        add(US_REZANJE_MDF if (mat["vrsta"] == "MDF" and deb and deb <= MDF_TANKI_MM) else US_REZANJE, m2, "rezanje", "rezanje po m² ploče", nm_id)

    def slaganje(nm_id, dijelovi, ploca, trim, god):
        """Potvrđeno slaganje (D-75) ako postoji, inače Hubov prijedlog uz upozorenje. Vraća (sheets, oc, nacin, potvrdjeno)."""
        s = OP.slaganje(conn, nm_id)
        if s:
            sheets, pl, tr, kf, gd, red = s
            return sheets, OPT.ocijeni(sheets, pl, tr), red["nacin"], True
        s = OP.prijedlog_auto(conn, nm_id)                       # živi prijedlog s istim elementima — ne računa se dvaput
        if s:
            sheets, pl, tr, kf, gd, red = s
            return sheets, OPT.ocijeni(sheets, pl, tr), red["nacin"], False
        sheets, oc, nacin, _ = OPT.najbolje(dijelovi, ploca, trim, kerf, god)
        return sheets, oc, nacin, False

    def add(ident, kolicina, grupa, pravilo, nm_id=None, naziv=None, jm=None, rabat=None):
        if not ident or kolicina <= 0:
            return None
        pi = _ident(conn, ident)
        if not pi:
            upoz.append("ident %s nema u šifrarniku (%s) — stavka bez cijene" % (ident, pravilo))
            pi = dict(ident=ident, naziv=naziv or ident, jm=jm or "KOM", cijena_neto=None, aktivan=1)
        elif not pi["aktivan"]:
            upoz.append("ident %s (%s) nije aktivan u Pantheonu" % (ident, pi["naziv"]))
        r = rab_u if grupa in ("rezanje", "kantiranje", "usluga") else rab_m
        if rabat is not None:
            r = rabat
        s = dict(rb=len(stavke) + 1, pantheon_ident=ident, naziv=pi["naziv"], kolicina=round(float(kolicina), 3), jm=pi["jm"] or jm or "KOM",
                 cijena=round(pi["cijena_neto"], 2) if pi["cijena_neto"] is not None else None, rabat=r, grupa=grupa, pravilo=pravilo, nalog_materijal_id=nm_id)
        s["iznos"] = round(s["kolicina"] * (s["cijena"] or 0) * (1 - r / 100), 2)
        stavke.append(s)
        return s

    for nm in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? ORDER BY rb, id", (nalog_id,)).fetchall():
        m = N.materijal_naloga(conn, nm["id"])
        els = [e for e in els_sve if e["nalog_materijal_id"] == nm["id"]]
        if not m["materijal_id"]:
            upoz.append("%s: materijal nije potvrđen — bez stavke" % (m["naziv_ulaz"] or "?"))
            continue
        if not els:
            continue
        mat = conn.execute("SELECT vrsta, obitelj_rp, debljina, naziv_kratki FROM materijal WHERE id = ?", (m["materijal_id"],)).fetchone()
        deb = m["debljina"] or m["debljina_ulaz"] or 0
        pL, pW = _ploca(m)
        komada = sum(int(e["kom"]) for e in els)
        pm = dict(nalog_materijal_id=nm["id"], ident=m["ident"], materijal=m["naziv_kratki"] or m["naziv_ulaz"], vrsta=mat["vrsta"], elemenata=len(els), komada=komada,
                  m2_dijelova=round(sum(e["L"] * e["W"] * e["kom"] for e in els) / 1e6, 3))
        if mat["vrsta"] in ("RP", "ZO"):                         # po dužnom metru + 2 reza po komadu
            metara = round(sum(max(e["L"], e["W"]) * e["kom"] for e in els) / 1000, 2)
            add(m["ident"], metara, "materijal", "RP/ZO po dužnom metru (Σ dulja stranica × kom)", nm["id"])
            add(US_REZ_RP, 2 * komada, "rezanje", "2 reza × %d kom" % komada, nm["id"])
            pm.update(nacin="dužni metar", kolicina=metara, jm="M")
        elif m["ploca_L"] or m["ploca_W"]:                        # restl / vlastita ploča: cijela površina (skill §2)
            n_pl, oc, potvrdjeno = 1, None, False
            try:
                dijelovi = [(k + 1, float(e["W"]), float(e["L"]), int(e["kom"])) for k, e in enumerate(els)]
                sheets, oc, nacin, potvrdjeno = slaganje(nm["id"], dijelovi, (pL, pW), 10, bool(m["god"]))
                n_pl = oc["ploca"]
            except ValueError:
                upoz.append("%s: elementi ne stanu na restl %gx%g" % (pm["materijal"], pL, pW))
            if not potvrdjeno:
                upoz.append("%s: optimizacija nije potvrđena (D-75) — brojke su Hubov prijedlog" % pm["materijal"])
            m2 = round(n_pl * pL * pW / 1e6, 2)
            add(m["ident"], m2, "materijal", "restl %gx%g × %d — cijela površina" % (pL, pW, n_pl), nm["id"])
            rezanje(mat, deb, m2, oc, nm["id"])
            pm.update(nacin="restl", kolicina=m2, jm="M2", ploca=n_pl, optimizacija_potvrdjena=potvrdjeno)
        else:
            dijelovi = [(k + 1, float(e["W"]), float(e["L"]), int(e["kom"])) for k, e in enumerate(els)]
            trim = 10
            if any(e["L"] > pL - 2 * trim or e["W"] > pW - 2 * trim for e in els):
                trim = 0                                          # element na punu mjeru ploče: bez obreza (D-65/10)
            try:
                sheets, oc, nacin, potvrdjeno = slaganje(nm["id"], dijelovi, (pL, pW), trim, bool(m["god"]))
            except ValueError as e:
                upoz.append("%s: ne može se složiti (%s) — bez stavke" % (pm["materijal"], e))
                continue
            if not potvrdjeno:
                upoz.append("%s: optimizacija nije potvrđena (D-75) — brojke su Hubov prijedlog" % pm["materijal"])
            m2 = oc["m2_naplata"]
            pravilo = "PW-metoda %s%s: %d ploča, %.2f m² za naplatu" % (nacin, " (potvrđeno)" if potvrdjeno else "", oc["ploca"], m2)
            provjeri = False
            if pravila:
                m2, opis, provjeri = pravilo_nacete_ploce(m2, oc["ploca"], pL * pW / 1e6)
                if opis:
                    pravilo += "; " + opis
            add(m["ident"], m2, "materijal", pravilo, nm["id"])
            rezanje(mat, deb, m2, oc, nm["id"])
            pm.update(nacin=nacin, kolicina=m2, jm="M2", ploca=oc["ploca"], m2_pw=oc["m2_naplata"], provjeri=provjeri, ostaci=oc.get("ostaci"),
                      optimizacija_potvrdjena=potvrdjeno)
        # trake ovog materijala: po TR identu (Σ stranica × kom × 1,10) — u ponudi idu odmah iza ploče, kao što ured piše (D-32)
        kant_m, kant_klasa = {}, {}
        for e in els:
            el = N.element(conn, e["element_id"])
            for i, strana in enumerate(("L", "O", "D", "G"), 1):
                tid = el["rub%d_traka" % i]
                if not tid:
                    if el["rub%d_kod" % i]:
                        upoz.append("%s: rub '%s' bez trake (nije potvrđen)" % (pm["materijal"], el["rub%d_kod" % i]))
                    continue
                ln = float(el["L"]) if strana in ("L", "D") else float(el["W"])
                kant_m[tid] = kant_m.get(tid, 0.0) + ln * int(el["kom"]) / 1000.0 * faktor_trake
                kant_klasa[tid] = el["rub%d_klasa" % i]
            fi35, nut, urez, ostalo = _obrada_elementa(dict(el, obrada_json=el.get("obrada_json")))
            if fi35:
                add(US_FI35, fi35, "usluga", "CNC fi35 iz napomene (%s)" % el["napomena"], nm["id"])
            if nut:
                add(US_NUT, round(nut, 2), "usluga", "NUT/FALC po duljini (%s ×%d)" % (el["L"], el["kom"]), nm["id"])
            if urez:
                add(US_UREZ_GOLA, round(urez, 2), "usluga", "UREZ GOLA po duljini (%s ×%d)" % (el["L"], el["kom"]), nm["id"])
            for o in ostalo:
                upoz.append("%s el. %s (%gx%g): obrada %s — usluga se dodaje ručno" % (pm["materijal"], el["naziv"] or el["rb"], el["L"], el["W"], o))
        # trake i kantiranje (D-20): metri naviše po traci, usluga točni metri po klasi — sve uz ovaj materijal
        kant_po_klasi = {}
        for tid, metri in kant_m.items():
            add(tid, math.ceil(metri - 1e-9), "traka", "PW metri %.2f (nadmjera %g %% unutra) naviše na cijeli m" % (metri, (faktor_trake - 1) * 100), nm["id"])
            us = P.usluga_kantiranja(kant_klasa.get(tid))
            if us:
                kant_po_klasi[us] = kant_po_klasi.get(us, 0.0) + metri
            else:
                upoz.append("traka %s: nepoznata klasa — kantiranje nije obračunato" % tid)
        for us, metri in kant_po_klasi.items():
            add(us, round(metri, 2), "kantiranje", "točni PW metri po klasi trake", nm["id"])
        pm["kant_m"] = {k: round(v, 2) for k, v in kant_m.items()}
        po_mat.append(pm)
    # okov (D-32): samo potvrđeno
    for o in conn.execute("SELECT * FROM okov_stavka WHERE nalog_id = ? ORDER BY id", (nalog_id,)).fetchall():
        if o["status"] != "potvrdjeno" or not o["pantheon_ident"]:
            upoz.append("okov '%s' nije potvrđen — nije u ponudi" % (o["naziv"] or o["izvor_tekst"] or "?"))
            continue
        add(o["pantheon_ident"], o["kom"] or 0, "okov", "okov iz naloga")
    neto = round(sum(s["iznos"] for s in stavke), 2)
    upoz = list(dict.fromkeys(upoz))                # isto upozorenje jednom
    return dict(nalog_id=nalog_id, naziv=n["naziv"], stavke=stavke, upozorenja=upoz, po_materijalu=po_mat, rabat_materijal=rab_m, rabat_usluge=rab_u,
                nepotvrdjene_optimizacije=[x["materijal"] for x in po_mat if x.get("optimizacija_potvrdjena") is False],
                neto=neto, pdv=round(neto * PDV, 2), ukupno=round(neto * (1 + PDV), 2), bez_cijene=[s["pantheon_ident"] for s in stavke if s["cijena"] is None])


def upisi(conn, nalog_id, tko="web", pravila=True):
    """Izračunaj i zamijeni radne stavke naloga (one bez verzije ponude). Vraća izvještaj kao `izracunaj` + `upisano`."""
    try:
        OP.pripremi_prijedloge(conn, nalog_id, tko)              # D-75: prijedlog slaganja za svaki nepotvrđeni materijal (ekran ga pokaže za potvrdu)
        r = izracunaj(conn, nalog_id, pravila)
        conn.execute("DELETE FROM obracun_stavka WHERE nalog_id = ? AND ponuda_verzija_id IS NULL", (nalog_id,))
        for s in r["stavke"]:
            conn.execute("INSERT INTO obracun_stavka (nalog_id, rb, pantheon_ident, naziv, kolicina, jm, cijena, rabat, grupa, pravilo, nalog_materijal_id) "
                         "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (nalog_id, s["rb"], s["pantheon_ident"], s["naziv"], s["kolicina"], s["jm"], s["cijena"], s["rabat"],
                                                            s["grupa"], s["pravilo"], s["nalog_materijal_id"]))
        dnevnik(conn, tko, "nalog", nalog_id, "obracun", "%d stavki, neto %.2f EUR%s" % (len(r["stavke"]), r["neto"], (", %d upozorenja" % len(r["upozorenja"])) if r["upozorenja"] else ""))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    r["upisano"] = len(r["stavke"])
    return r


def stavke(conn, nalog_id, ponuda_verzija_id=None):
    q = "SELECT * FROM obracun_stavka WHERE nalog_id = ? AND ponuda_verzija_id IS ? ORDER BY rb, id"
    out = [dict(r) for r in conn.execute(q, (nalog_id, ponuda_verzija_id)).fetchall()]
    for s in out:
        s["iznos"] = round((s["kolicina"] or 0) * (s["cijena"] or 0) * (1 - (s["rabat"] or 0) / 100), 2)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Obračun naloga → stavke ponude (korak 4)")
    ap.add_argument("--db")
    ap.add_argument("--nalog", type=int, required=True)
    ap.add_argument("--bez-pravila", action="store_true", help="bez pravila načete ploče (čisti PW m²)")
    ap.add_argument("--suho", action="store_true", help="samo izračunaj, ne upisuj")
    ap.add_argument("--tko", default="web")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    try:
        r = izracunaj(conn, a.nalog, not a.bez_pravila) if a.suho else upisi(conn, a.nalog, a.tko, not a.bez_pravila)
    except (ObracunGreska, N.NalogGreska) as e:
        print("GRESKA:", e)
        return 1
    print("%s%s  (rabat materijal %g %%, usluge %g %%)" % ("[suho] " if a.suho else "", r["naziv"], r["rabat_materijal"], r["rabat_usluge"]))
    for s in r["stavke"]:
        print("  %2d. %-10s %-38s %9.2f %-3s x %8s  = %9.2f   %s" % (s["rb"], s["pantheon_ident"], (s["naziv"] or "")[:38], s["kolicina"], s["jm"],
                                                                     ("%.2f" % s["cijena"]) if s["cijena"] is not None else "?", s["iznos"], s["pravilo"] or ""))
    print("  neto %.2f  PDV %.2f  ukupno %.2f EUR" % (r["neto"], r["pdv"], r["ukupno"]))
    for u in r["upozorenja"]:
        print("  PAZI:", u)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
