# -*- coding: utf-8 -*-
"""ispis/krojni.py — KROJNI NACRT (PDF) po materijalu naloga, iz POTVRĐENOG slaganja (D-75 / D-76 / D-77, korak 5b).

Isto što operater danas čita s PanelWizardovog ispisa — list po ploči (komadi s brojem, napomenom, mjerama i oznakama kantiranja,
ostatak, legenda traka, barkod programa) + statistika (elementi s oznakama 2DA 2KA, ploče, površina za naplatu, kantiranje po traci) —
ali kao Hubov dokument: identi materijala i traka, Winstore kod i stanje, pretinac trake iz Regal trake, tko je potvrdio slaganje.
Bez potvrde nacrt se ispisuje s oznakom PRIJEDLOG (nije za pilu).

    py -m hub.ispis.krojni --db hub.db --nalog 12 [--materijal 40] [--mapa C:\\ISPISI] [--oid 17]
    GET /api/nalog/{id}/ispis/krojni.pdf?materijal=40           (PDF; bez `materijal` = svi materijali naloga u jednom PDF-u)
"""
import argparse
import datetime
import os
import sys

from .. import db
from ..db import sada, dnevnik, postavka
from ..nalozi import nalozi as N, optimiziraj as OP, sheme as SH, grupe as G
from ..optimizacija import obracun as OB, pila_optimizator as OPT
from ..skladiste import trake as RT

OVDJE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(OVDJE, "logo-mark.png")
# Ispis je crno-bijeli i štedljiv (Igor, 16. 9. 2026.): bez ispuna i boja; oznake kantiranja kao u PW — puni trokutić na rubu,
# uz njega broj kanta kad materijal ima više traka (Kant 1., Kant 2. … u legendi)


class IspisGreska(Exception):
    pass


# ---------------------------------------------------------------- podaci
def _oznake_kanta(e_tip, e_traka):
    """PW oznake kantiranja, odvojeno kao u PW statistici: (melamin, abs) — nDP/nKP = duže/kraće stranice melamin (PVC), nDA/nKA = ABS.
    L/D = duže, O/G = kraće (D-61)."""
    br = {}
    for strana in ("L", "D", "O", "G"):
        if not (e_traka.get(strana) or "").strip():
            continue
        vrsta = "A" if (e_tip.get(strana) or "A") == "A" else "P"
        k = ("D" if strana in ("L", "D") else "K") + vrsta
        br[k] = br.get(k, 0) + 1
    mel = " ".join("%d%s" % (br[k], k) for k in ("DP", "KP") if k in br)
    abs_ = " ".join("%d%s" % (br[k], k) for k in ("DA", "KA") if k in br)
    return mel, abs_


def podaci(conn, nm_id, oid=None):
    """Sve za nacrt jednog materijala: nalog, materijal, elementi (s trakama), slaganje (sheets + geometrija po ploči), statistika, kantiranje."""
    m = N.materijal_naloga(conn, nm_id)
    if not m:
        raise IspisGreska("materijal naloga %s ne postoji" % nm_id)
    n = N.nalog(conn, m["nalog_id"])
    m0, els, dijelovi, ploca, trim, god, h = OP.ulaz_materijala(conn, nm_id)
    if not els:
        raise IspisGreska("%s: nema elemenata" % (m["naziv_kratki"] or m["naziv_ulaz"]))
    # slaganje: zadani red / potvrđeno / živi auto prijedlog / izračun bez upisa
    red, sheets, potvrdjeno = None, None, False
    if oid:
        red = conn.execute("SELECT * FROM optimizacija WHERE id = ? AND nalog_materijal_id = ?", (oid, nm_id)).fetchone()
        if not red or not red["slaganje_json"]:
            raise IspisGreska("optimizacija %s nije slaganje ovog materijala" % oid)
        red = dict(red)
        potvrdjeno = red["status"] == "potvrdjeno"
    else:
        s = OP.slaganje(conn, nm_id)
        if s:
            red, potvrdjeno = s[5], True
        else:
            s = OP.prijedlog_auto(conn, nm_id)
            red = s[5] if s else None
    import json
    if red:
        sn = json.loads(red["slaganje_json"])
        sheets, ploca, trim, kerf, god = sn["sheets"], tuple(sn["ploca"]), sn["trim"], sn["kerf"], sn["god"]
        nacin = red["nacin"]
    else:
        r = OP.izracunaj(conn, nm_id, "auto", "najbolje")
        sheets, kerf, nacin = r["sheets"], r["kerf"], r["nacin"]
    kerf_obracun = float(postavka(conn, "kerf", "16") or 16)
    faktor_trake = 1 + float(postavka(conn, "nadmjera_trake", "10") or 0) / 100
    # geometrija po ploči (ista kao sheme.py / cpo_rw.validate)
    d = dict(inv=[dict(L=float(ploca[0]), W=float(ploca[1]), trim=[float(trim)] * 4)], ctl2=[kerf],
             pat=[dict(no=i + 1, dir=s["dir"], qty=1, cuts=OPT.sheme_u_cuts(s)) for i, s in enumerate(sheets)])
    geo = SH.geometrija(d)
    # trake: metri po KONAČNOJ mjeri pravih elemenata (i članova majki — majka se reže, komadi se kantiraju; korak 6)
    trake = {}

    def _traka(el, i, strana):
        tid = el["rub%d_traka_id" % i]
        if tid and tid not in trake:
            vrsta = "MEL" if N.tip_ruba(el["rub%d_klasa" % i], el["rub%d_kod" % i]) == "M" else "ABS"
            n_vrste = sum(1 for t in trake.values() if t["vrsta"] == vrsta) + 1
            trake[tid] = dict(id=tid, ident=el["rub%d_traka" % i], naziv=el["rub%d_naziv" % i], klasa=el["rub%d_klasa" % i],
                              vrsta=vrsta, broj=n_vrste, oznaka="%s %d" % (vrsta, n_vrste), rb=len(trake) + 1,
                              metri=0.0, metri_tocno=0.0, pretinac=None, preostalo=None)
        return tid
    for el in N.elementi_konacni(conn, nm_id):
        for i, strana in enumerate(("L", "O", "D", "G"), 1):
            tid = _traka(el, i, strana)
            if tid:
                ln = float(el["L"]) if strana in ("L", "D") else float(el["W"])
                trake[tid]["metri_tocno"] += ln * int(el["kom"]) / 1000.0
    # elementi koji se REŽU (mjera za rezanje, element-majke umjesto članova) s oznakama kantiranja na tom komadu
    elementi = []
    for k, e in enumerate(els):
        el = N.element(conn, e["element_id"])
        rub = {}
        for i, strana in enumerate(("L", "O", "D", "G"), 1):
            tid = _traka(el, i, strana)
            if tid:
                rub[strana] = tid
            elif el["rub%d_kod" % i]:
                rub[strana] = "?"                                   # rub naručen, traka nije potvrđena
        po_traci = {}
        for strana, tid in rub.items():
            if tid in trake:
                k2 = ("D" if strana in ("L", "D") else "K") + ("P" if trake[tid]["vrsta"] == "MEL" else "A")
                po_traci.setdefault(tid, {})[k2] = po_traci.setdefault(tid, {}).get(k2, 0) + 1
        oznake_po_traci = {tid: " ".join("%d%s" % (br[k2], k2) for k2 in ("DA", "KA", "DP", "KP") if k2 in br) for tid, br in po_traci.items()}
        nap = (el["napomena"] or "")[:60]
        if e.get("rez_razlog") == "suziti":
            nap = ("%s · konačna %s × %s" % (el["napomena_rez"], _mm(e["L_kon"]), _mm(e["W_kon"])) + ((" · " + nap) if nap else ""))[:80]
        elif e.get("rez_razlog") == "sloj":
            nap = ("%s · sirova mjera sloja" % el["napomena_rez"] + ((" · " + nap) if nap else ""))[:80]
        elif e.get("vrsta") == "majka":
            nap = ("%s · reže se po skici majke" % el["napomena_rez"])[:80]
        elementi.append(dict(idx=k + 1, id=e["element_id"], naziv=e.get("naziv") or "", L=float(e["L"]), W=float(e["W"]), kom=int(e["kom"]),
                             god=int(e.get("god", 0)), napomena=nap, napomena_etiketa=e.get("napomena") or "", vrsta=e.get("vrsta") or "element",
                             rub=rub, tip=dict(e.get("tip", {})), oznake_mel=_oznake_kanta(e.get("tip", {}), e.get("traka", {}))[0],
                             oznake_abs=_oznake_kanta(e.get("tip", {}), e.get("traka", {}))[1], oznake_po_traci=oznake_po_traci))
    for t in trake.values():
        t["metri"] = t["metri_tocno"] * faktor_trake
        t["pretinac"] = RT.pretinac(conn, t["ident"])
        t["preostalo"] = RT.metri(conn, t["ident"])
    # ploče: po listu
    L, W = ploca
    listovi = []
    for i, (s, g) in enumerate(zip(sheets, geo)):
        m2_dio = sum(w * hh for (x, y, w, hh, idx) in g["pravokutnici"] if idx is not None) / 1e6
        ost = OB.ostatak_ploce(s["dir"], [st["w"] for st in s["strips"]], ploca, trim, kerf_obracun)
        komadi = [(x, y, w, hh, idx) for (x, y, w, hh, idx) in g["pravokutnici"] if idx is not None]
        listovi.append(dict(br=i + 1, dir=s["dir"], pravokutnici=g["pravokutnici"], komadi=len(komadi), m2_dijelova=round(m2_dio, 3),
                            iskoristenje=round(m2_dio / (L * W / 1e6), 4), rezova=len(g["pravokutnici"]), ostatak=ost, strips=s["strips"]))
    oc = OPT.ocijeni(sheets, ploca, trim, kerf_obracun)
    m2_dijelova = sum(x["m2_dijelova"] for x in listovi)
    m2_ploca = len(sheets) * L * W / 1e6
    stanje = conn.execute("SELECT COALESCE(SUM(kom_ukupno), 0) FROM winstore_ploca WHERE materijal_id = ? AND ambalaza = 0 AND drop_ploca = 0",
                          (m["materijal_id"],)).fetchone()[0] if m["materijal_id"] else None
    program = None
    if red and red.get("sheme_json"):
        try:
            program = json.loads(red["sheme_json"]).get("program")
        except ValueError:
            program = None
    potvrdio = None
    if red and red.get("potvrdio_id"):
        r = conn.execute("SELECT oznaka, ime FROM korisnik WHERE id = ?", (red["potvrdio_id"],)).fetchone()
        potvrdio = (r["ime"] or r["oznaka"]) if r else None
    majke = [mk for mk in G.pregled(conn, n["id"]) if mk["nalog_materijal_id"] == nm_id]      # korak 6: skice majki i sklopova ovog materijala
    return dict(nalog=dict(id=n["id"], naziv=n["naziv"], broj=n["broj"], kupac=n["kupac_naziv"] or "", status=n["status"]), majke=majke,
                materijal=dict(nm_id=nm_id, ident=m["ident"], naziv=m["naziv"] or m["naziv_kratki"] or m["naziv_ulaz"], kratki=m["naziv_kratki"] or m["naziv_ulaz"],
                               winstore_kod=m["winstore_kod"], debljina=m["debljina"] or m["debljina_ulaz"], stanje_kom=stanje, put=m["put"]),
                ploca=dict(L=L, W=W, trim=trim, kerf_pile=kerf, kerf_obracun=kerf_obracun, god=bool(god)),
                slaganje=dict(nacin=nacin, potvrdjeno=potvrdjeno, potvrdio=potvrdio, potvrdjeno_kad=(red or {}).get("potvrdjeno"), oid=(red or {}).get("id"),
                              status=(red or {}).get("status") or "izračun", program=program),
                elementi=elementi, trake=sorted(trake.values(), key=lambda t: (t["vrsta"] != "ABS", t["broj"])), listovi=listovi,
                statistika=dict(ploca=len(sheets), m2_ploca=round(m2_ploca, 2), m2_dijelova=round(m2_dijelova, 2), m2_naplata=oc["m2_naplata"],
                                iskoristenje=round(m2_dijelova / m2_ploca, 4) if m2_ploca else 0, ostaci=oc["ostaci"], rezova=oc["rezova"],
                                komada=sum(e["kom"] for e in elementi), elemenata=len(elementi), faktor_trake=faktor_trake))


# ---------------------------------------------------------------- PDF
def _font():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for reg, bold in (("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"), ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
                      ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")):
        try:
            pdfmetrics.registerFont(TTFont("HubFont", reg))
            try:
                pdfmetrics.registerFont(TTFont("HubFontB", bold))
            except Exception:
                pdfmetrics.registerFont(TTFont("HubFontB", reg))
            return "HubFont", "HubFontB"
        except Exception:
            continue
    return "Helvetica", "Helvetica-Bold"


def _fmt(x, dec=2):
    s = ("%%.%df" % dec) % x
    return s.replace(".", ",")


def _mm(x):
    x = float(x or 0)
    return str(int(round(x))) if abs(x - round(x)) < 0.05 else ("%.1f" % x).replace(".", ",")


class _Nacrt:
    """Crtanje jednog materijala na reportlab canvas (A4 uspravno)."""

    def __init__(self, c, d, font, fontb, datum, ukupno_str):
        self.c, self.d, self.f, self.fb, self.datum, self.ukupno = c, d, font, fontb, datum, ukupno_str
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        self.PW, self.PH, self.mm = A4[0], A4[1], mm
        self.M = 12 * mm

    # -- zaglavlje / podnožje na svakom listu
    def zaglavlje(self, naslov, list_str):
        c, mm, d = self.c, self.mm, self.d
        from reportlab.lib import colors
        y0 = self.PH - self.M
        # zaglavlje: bez ispune (crno-bijeli, štedljiv ispis) — logo mali, tanka crta ispod
        if os.path.exists(LOGO):
            try:
                c.drawImage(LOGO, self.M, y0 - 12 * mm, height=10 * mm, width=10 * mm * 106 / 120.0, mask="auto", preserveAspectRatio=True)
            except Exception:
                pass
        c.setFillColor(colors.black)
        c.setFont(self.fb, 12)
        c.drawString(self.M + 12 * mm, y0 - 6 * mm, "Paneli_ Production Hub")
        c.setFont(self.f, 8.5)
        c.drawString(self.M + 12 * mm, y0 - 11.5 * mm, naslov[:60])
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.8)
        c.line(self.M, y0 - 16 * mm, self.PW - self.M, y0 - 16 * mm)
        # desno: program (barkod ispod, bijela pločica) + list
        prog = d["slaganje"]["program"] or d["nalog"]["naziv"]
        c.setFont(self.fb, 13)
        c.drawRightString(self.PW - self.M - 3 * mm, y0 - 6.5 * mm, prog)
        c.setFont(self.f, 8.5)
        c.drawRightString(self.PW - self.M - 3 * mm, y0 - 12 * mm, list_str)
        try:
            from reportlab.graphics.barcode import code39
            bc = code39.Standard39("*%s*" % prog, barWidth=0.25 * mm, barHeight=6.5 * mm, checksum=0, quiet=0, humanReadable=False)
            bc_w = bc.width
            x_bc = self.PW - self.M - 3 * mm - c.stringWidth(prog, self.fb, 13) - 12 * mm - bc_w
            c.setFillColor(colors.black)
            bc.drawOn(c, x_bc, y0 - 13 * mm)
        except Exception:
            pass
        c.setFillColor(colors.black)
        return y0 - 16 * mm

    def podnozje(self, str_):
        c, mm = self.c, self.mm
        from reportlab.lib import colors
        c.setStrokeColor(colors.HexColor("#bbbbbb"))
        c.setLineWidth(0.4)
        c.line(self.M, self.M + 6 * mm, self.PW - self.M, self.M + 6 * mm)
        c.setFont(self.f, 7.5)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawString(self.M, self.M + 2.5 * mm, "Paneli Production Hub · krojni nacrt · ispis %s" % self.datum)
        c.drawRightString(self.PW - self.M, self.M + 2.5 * mm, str_)
        c.setFillColor(colors.black)

    def info_blok(self, y):
        """Nalog / materijal / ploča / slaganje — dvije kolone; vraća donji y."""
        c, mm, d = self.c, self.mm, self.d
        from reportlab.lib import colors
        m, p, s, n = d["materijal"], d["ploca"], d["slaganje"], d["nalog"]
        lijevo = [("Nalog", "%s%s" % (n["naziv"], (" · " + n["kupac"]) if n["kupac"] and n["kupac"] not in n["naziv"] else "")),
                  ("Materijal", "%s  %s" % (m["ident"] or "—", m["naziv"] or "")),
                  ("Winstore", "%s%s" % (m["winstore_kod"] or "—", ("  · na stanju %d kom" % m["stanje_kom"]) if m["stanje_kom"] is not None and m["winstore_kod"] else ""))]
        desno = [("Ploča", "%s × %s × %s mm · obrez %s mm" % (_mm(p["L"]), _mm(p["W"]), _mm(m["debljina"] or 0), _mm(p["trim"]))),
                 ("God", "DA" if p["god"] else "NE"),
                 ("Slaganje", "%s · kerf %s mm" % (s["nacin"], _mm(p["kerf_pile"]))),
                 ("Potvrdio", ("%s, %s" % (s["potvrdio"] or "—", (s["potvrdjeno_kad"] or "")[:16].replace("T", " "))) if s["potvrdjeno"] else "— PRIJEDLOG, nije potvrđeno")]
        lijevo.append(("", ""))
        y -= 3 * mm
        kol = (self.PW - 2 * self.M) / 2
        for k, stupac in enumerate((lijevo, desno)):
            x = self.M + k * kol
            yy = y
            for lab, val in stupac:
                c.setFont(self.f, 7.5)
                c.setFillColor(colors.HexColor("#666666"))
                c.drawString(x, yy - 3.2 * mm, lab)
                c.setFillColor(colors.black)
                fnt = self.fb if lab in ("Nalog", "Materijal", "God") else self.f
                c.setFont(fnt, 10 if lab == "God" else 8.5)
                txt = val
                while c.stringWidth(txt, fnt, 8.5) > kol - 20 * mm and len(txt) > 4:
                    txt = txt[:-2]
                c.drawString(x + 18 * mm, yy - 3.2 * mm, txt)
                yy -= 4.6 * mm
        y -= 4 * 4.6 * mm + 1 * mm
        c.setStrokeColor(colors.HexColor("#cccccc"))
        c.setLineWidth(0.4)
        c.line(self.M, y, self.PW - self.M, y)
        return y

    def _trokut(self, X, Y, Wd, Hd, smjer, oznaka=None, puni=True):
        """Trokutić (kao PW) na sredini ruba komada, vrh na rubu: PUNI = ABS traka, PRAZNI = melamin (MEL); oznaka = broj kanta (kad ih je više)."""
        c, mm = self.c, self.mm
        from reportlab.lib import colors
        t = min(1.8 * mm, Wd / 4, Hd / 4)
        if t < 0.5 * mm:
            return
        p = c.beginPath()                              # trokutić unutar komada, vrh na rubu (pokazuje prema van, kao PW)
        if smjer == "dolje":
            cx, cy = X + Wd / 2, Y
            p.moveTo(cx - t, cy + 1.4 * t); p.lineTo(cx + t, cy + 1.4 * t); p.lineTo(cx, cy)
            tx, ty = cx + t + 0.6 * mm, cy + 0.4 * mm
        elif smjer == "gore":
            cx, cy = X + Wd / 2, Y + Hd
            p.moveTo(cx - t, cy - 1.4 * t); p.lineTo(cx + t, cy - 1.4 * t); p.lineTo(cx, cy)
            tx, ty = cx + t + 0.6 * mm, cy - 2.2 * mm
        elif smjer == "lijevo":
            cx, cy = X, Y + Hd / 2
            p.moveTo(cx + 1.4 * t, cy - t); p.lineTo(cx + 1.4 * t, cy + t); p.lineTo(cx, cy)
            tx, ty = cx + 1.4 * t + 0.5 * mm, cy + t + 0.3 * mm
        else:
            cx, cy = X + Wd, Y + Hd / 2
            p.moveTo(cx - 1.4 * t, cy - t); p.lineTo(cx - 1.4 * t, cy + t); p.lineTo(cx, cy)
            tx, ty = cx - 1.4 * t - 3.2 * mm, cy + t + 0.3 * mm
        p.close()
        c.setFillColor(colors.black)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.7)
        c.drawPath(p, stroke=0 if puni else 1, fill=1 if puni else 0)
        if oznaka and min(Wd, Hd) > 7 * mm:
            c.setFont(self.f, 5.5)
            c.drawString(tx, ty, oznaka)

    def legenda(self, y):
        """Legenda traka pri dnu lista: boja, oznaka, ident, naziv, pretinac."""
        c, mm, d = self.c, self.mm, self.d
        from reportlab.lib import colors
        c.setFont(self.fb, 8)
        c.drawString(self.M, y, "Kantiranje:")
        x = self.M + 22 * mm
        c.setFont(self.f, 7.5)
        for t in d["trake"]:
            c.setFillColor(colors.black)
            txt = "%s = %s %s%s" % (t["oznaka"], t["ident"] or "", (t["naziv"] or "")[:28], (" · " + t["pretinac"]) if t["pretinac"] else "")
            c.drawString(x, y, txt)
            x += 8 * mm + c.stringWidth(txt, self.f, 7.5)
            if x > self.PW - self.M - 50 * mm:
                x = self.M + 22 * mm
                y -= 4.2 * mm
        if not d["trake"]:
            c.drawString(x, y, "bez traka")
        else:
            c.setFont(self.f, 6.5)
            c.setFillColor(colors.HexColor("#555555"))
            c.drawRightString(self.PW - self.M, y, "▲ puni = ABS · △ prazni = melamin")
            c.setFillColor(colors.black)
        return y

    # -- list = jedna ploča
    def list_ploce(self, li, ukupno_listova):
        c, mm, d = self.c, self.mm, self.d
        from reportlab.lib import colors
        y = self.zaglavlje("Krojni nacrt · %s" % d["materijal"]["kratki"], "List %d / %d" % (li["br"], ukupno_listova))
        y = self.info_blok(y)
        # redak lista
        o = li["ostatak"]
        c.setFont(self.fb, 9)
        c.drawString(self.M, y - 5 * mm, "Ploča %d od %d" % (li["br"], ukupno_listova))
        c.setFont(self.f, 8.5)
        c.drawString(self.M + 30 * mm, y - 5 * mm, "smjer %s · komada %d · rezova %d · iskorištenje %s %% · dijelova %s m²%s" % (
            "uzdužno" if li["dir"] == "L" else "poprečno", li["komadi"], li["rezova"], _fmt(100 * li["iskoristenje"], 1), _fmt(li["m2_dijelova"]),
            (" · KORISNI OSTATAK %s × %s mm (%s m²)" % (_mm(o[0]), _mm(o[1]), _fmt(o[2]))) if o else ""))
        y -= 8 * mm
        # crtež: ploča USPRAVNO — duža stranica (L = 2800) je okomita na papiru, kao u PW (Igor, 16. 9.)
        # koordinate ploče (x uz L, y uz W) → papir: X = oy_papir + y, Y = ox_papir + x
        L, W = d["ploca"]["L"], d["ploca"]["W"]
        ax, ay = self.M, self.M + 22 * mm
        aw, ah = self.PW - 2 * self.M, y - ay - 4 * mm
        sk = min(aw / W, ah / L)
        ox = ax + (aw - W * sk) / 2
        oy = ay + ah - L * sk - 2 * mm                      # uz vrh, ispod retka lista
        c.setStrokeColor(colors.black)
        c.setLineWidth(1.0)
        c.rect(ox, oy, W * sk, L * sk, stroke=1, fill=0)
        trake = {t["id"]: t for t in d["trake"]}
        for (x, yy, w, h, idx) in li["pravokutnici"]:
            X, Y, Wd, Hd = ox + yy * sk, oy + (L - x - w) * sk, h * sk, w * sk     # zrcalno po visini: prve trake gore, ostatak dolje (kao PW)
            if idx is None:
                c.setStrokeColor(colors.black)
                c.setLineWidth(0.25)
                c.setDash(0.8, 2.5)
                c.rect(X, Y, Wd, Hd, stroke=1, fill=0)
                c.setDash()
                continue
            e = d["elementi"][idx - 1]
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.6)
            c.rect(X, Y, Wd, Hd, stroke=1, fill=0)
            # rubovi s trakom: duže (L, D) su uz dulju mjeru elementa; komad u ploči leži s L uz x ako w ≈ e.L
            uz_x = abs(w - e["L"]) < 0.6
            rub = e["rub"]
            vise = len(trake) > 1
            def trokut(strana, smjer):
                """Oznaka kantiranja kao u PW: puni trokutić na sredini ruba, vrh prema van; uz njega broj kanta kad ih je više."""
                tid = rub.get(strana)
                if not tid:
                    return
                self._trokut(X, Y, Wd, Hd, smjer, (str(trake[tid]["broj"]) if tid in trake else "?") if vise else None,
                             puni=(e["tip"].get(strana) or "A") != "M")
            if uz_x:                                     # dulja mjera elementa uz L ploče = uspravno na papiru: duže stranice L lijevo, D desno
                trokut("L", "lijevo"); trokut("D", "desno"); trokut("O", "dolje"); trokut("G", "gore")
            else:                                        # element okrenut: duže stranice vodoravno
                trokut("L", "dolje"); trokut("D", "gore"); trokut("O", "lijevo"); trokut("G", "desno")
            # tekst: broj + napomena, mjere
            c.setFillColor(colors.black)
            fs = 9 if min(Wd, Hd) > 9 * mm else 6
            c.setFont(self.fb, fs)
            c.drawString(X + 4 * mm if min(Wd, Hd) > 12 * mm else X + 1.5 * mm, Y + Hd - fs - 1.5 * mm, str(idx))
            nap = e["napomena"] or e["naziv"]                # kupčev PPW: tekst je u nazivu (nut za golu, skica 6)
            if nap and Wd > 22 * mm and Hd > 8 * mm:
                c.setFont(self.f, 6)
                txt = nap
                while c.stringWidth(txt, self.f, 6) > Wd - 8 * mm and len(txt) > 3:
                    txt = txt[:-2]
                c.drawString(X + 4 * mm + c.stringWidth(str(idx), self.fb, fs) + 1.5 * mm, Y + Hd - fs - 1.5 * mm, txt)
            # mjere kao u PW: okomita mjera uz DESNI rub (zaokrenuto), vodoravna uz DONJI rub; font veći
            fm = 9 if min(Wd, Hd) > 12 * mm else 7
            c.setFont(self.f, fm)
            okom, vodor = _mm(w), _mm(h)                   # w = uz L ploče (uspravno na papiru), h = uz W (vodoravno)
            t3 = min(1.8 * mm, Wd / 4, Hd / 4) + 1.5 * mm  # razmak od trokutića na sredini ruba
            tw_v, tw_o = c.stringWidth(vodor, self.f, fm), c.stringWidth(okom, self.f, fm)
            if Wd >= tw_v + 6 * mm and Hd > 4.5 * mm:
                cx = X + Wd / 2 - t3 - tw_v / 2 if Wd >= 2 * (t3 + tw_v / 2) + 4 * mm else X + Wd / 2   # lijevo od trokutića kad stane
                c.drawCentredString(cx, Y + 1.6 * mm if cx != X + Wd / 2 else Y + 4.8 * mm, vodor)
            if Hd >= tw_o + 6 * mm and Wd > 4.5 * mm:
                cy = Y + Hd / 2 - t3 - tw_o / 2 if Hd >= 2 * (t3 + tw_o / 2) + 4 * mm else Y + Hd / 2   # ispod trokutića kad stane
                c.saveState()
                c.translate(X + Wd - 1.4 * mm if cy != Y + Hd / 2 else X + Wd - 4.8 * mm, cy)   # desni rub: baza teksta uz rub, znakovi prema unutra
                c.rotate(90)
                c.drawCentredString(0, 0, okom)
                c.restoreState()
            if not (Wd >= tw_v + 6 * mm and Hd > 4.5 * mm) and not (Hd >= tw_o + 6 * mm and Wd > 4.5 * mm):
                mj = "%s × %s" % (okom, vodor)             # premali komad: obje mjere u sredini, sitno
                c.setFont(self.f, 5.5)
                if Hd > Wd:
                    c.saveState(); c.translate(X + Wd / 2 + 2, Y + Hd / 2); c.rotate(90); c.drawCentredString(0, 0, mj); c.restoreState()
                else:
                    c.drawCentredString(X + Wd / 2, Y + Hd / 2 - 2, mj)
        # ostatak
        if o:
            c.setFont(self.fb, 8)
            c.setFillColor(colors.black)
            if li["dir"] == "L":                          # ostatak uz kraj W = desni rub papira, cijelom visinom
                c.saveState()
                c.translate(ox + (W - o[1] / 2) * sk + 3, oy + L * sk / 2)
                c.rotate(90)
                c.drawCentredString(0, 0, "OSTATAK %s × %s" % (_mm(o[0]), _mm(o[1])))
                c.restoreState()
            else:                                        # ostatak uz kraj L = dno papira, cijelom širinom
                c.drawCentredString(ox + W * sk / 2, oy + (o[0] / 2) * sk - 3, "OSTATAK %s × %s" % (_mm(o[0]), _mm(o[1])))
            c.setFillColor(colors.black)
        # mjere ploče uz rub: W dolje, L uz lijevi rub (uspravno)
        c.setFont(self.f, 7)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawCentredString(ox + W * sk / 2, oy - 3.2 * mm, _mm(W))
        c.saveState()
        c.translate(ox - 2 * mm, oy + L * sk / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, _mm(L))
        c.restoreState()
        c.setFillColor(colors.black)
        self.legenda(self.M + 12 * mm)
        self.podnozje(self.ukupno)
        c.showPage()

    # -- statistika
    def statistika(self, listova):
        c, mm, d = self.c, self.mm, self.d
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import Table, TableStyle, Paragraph
        y = self.zaglavlje("Statistika · %s" % d["materijal"]["kratki"], "Statistika")
        y = self.info_blok(y)
        st, m = d["statistika"], d["materijal"]
        norm = ParagraphStyle("n", fontName=self.f, fontSize=7.5, leading=9)
        # elementi
        trake_l = sorted(d["trake"], key=lambda t: (t["vrsta"] != "ABS", t["broj"]))    # kolona po traci: ABS 1, ABS 2 …, MEL 1 … (Igor, 16. 9.)
        data = [["#", "Naziv", "Duž.", "Šir.", "Kom", "God"] + [t["oznaka"] for t in trake_l] + ["Napomena"]]
        for e in d["elementi"]:
            data.append([str(e["idx"]), Paragraph(e["naziv"], norm), _mm(e["L"]), _mm(e["W"]), str(e["kom"]), "God" if e["god"] else ""]
                        + [e["oznake_po_traci"].get(t["id"], "") for t in trake_l] + [Paragraph(e["napomena"], norm)])
        n_t = len(trake_l)
        w_t = 16 * mm if n_t <= 4 else max(11 * mm, (186 * mm - 7 * mm - 26 * mm - 12 * mm - 12 * mm - 9 * mm - 9 * mm - 30 * mm) / n_t)
        w_naziv = max(24 * mm, 36 * mm - max(0, n_t - 2) * 4 * mm)
        w_nap = max(24 * mm, 186 * mm - (7 + 12 + 12 + 9 + 9) * mm - w_naziv - n_t * w_t)
        t = Table(data, colWidths=[7 * mm, w_naziv, 12 * mm, 12 * mm, 9 * mm, 9 * mm] + [w_t] * n_t + [w_nap], repeatRows=1)
        t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), self.f), ("FONTSIZE", (0, 0), (-1, -1), 7.5), ("FONTNAME", (0, 0), (-1, 0), self.fb),
                               ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black), ("LINEBELOW", (0, 1), (-1, -1), 0.2, colors.HexColor("#999999")),
                               ("ALIGN", (2, 1), (4, -1), "RIGHT"), ("ALIGN", (6, 0), (5 + max(n_t, 1), -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5), ("TOPPADDING", (0, 0), (-1, -1), 1.5)]))
        w, h = t.wrap(self.PW - 2 * self.M, y - self.M - 10 * mm)
        y -= 3 * mm
        while True:
            parts = t.split(self.PW - 2 * self.M, y - self.M - 12 * mm)
            if not parts:
                break
            prvi = parts[0]
            w, h = prvi.wrap(self.PW - 2 * self.M, y - self.M - 12 * mm)
            prvi.drawOn(c, self.M, y - h)
            y -= h
            if len(parts) == 1:
                break
            t = parts[1]
            self.podnozje(self.ukupno)
            c.showPage()
            y = self.zaglavlje("Statistika · %s" % d["materijal"]["kratki"], "Statistika (nastavak)") - 4 * mm
        c.setFont(self.f, 6.5)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawString(self.M, y - 3.5 * mm, "Po traci: 1DA / 2DA = jedna / dvije duže stranice, 1KA / 2KA = kraće stranice (ABS); 1DP / 2DP i 1KP / 2KP = melamin (PVC).")
        c.drawString(self.M, y - 6.8 * mm, "ABS 1, ABS 2 … MEL 1 = trake iz legende na listovima; ista oznaka stoji uz trokutić na crtežu kad ih je više.")
        c.setFillColor(colors.black)
        y -= 12 * mm
        if y < self.M + 55 * mm:
            self.podnozje(self.ukupno)
            c.showPage()
            y = self.zaglavlje("Statistika · %s" % d["materijal"]["kratki"], "Statistika (nastavak)") - 4 * mm
        # PLOČE i POVRŠINA — tri uočljive kućice (Igor, 16. 9.)
        sirina = self.PW - 2 * self.M
        kut = [("PLOČE", "%d kom" % st["ploca"], "%s × %s × %s mm" % (_mm(d["ploca"]["L"]), _mm(d["ploca"]["W"]), _mm(m["debljina"] or 0))),
               ("POVRŠINA SVIH PLOČA", "%s m²" % _fmt(st["m2_ploca"]), "dijelova %s m² · iskorištenje %s %%" % (_fmt(st["m2_dijelova"]), _fmt(100 * st["iskoristenje"], 1))),
               ("POVRŠINA ZA NAPLATU", "%s m²" % _fmt(st["m2_naplata"]), "korisni ostatak odbijen (≥ 400 mm, ≥ 1 m²)")]
        kw = sirina / 3
        for i, (naslov, broj, opis) in enumerate(kut):
            x0 = self.M + i * kw
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.8 if i == 2 else 0.4)
            c.rect(x0, y - 17 * mm, kw - (2 * mm if i < 2 else 0), 17 * mm, stroke=1, fill=0)
            c.setFont(self.fb, 7.5)
            c.drawString(x0 + 3 * mm, y - 4.5 * mm, naslov)
            c.setFont(self.fb, 14)
            c.drawString(x0 + 3 * mm, y - 11 * mm, broj)
            c.setFont(self.f, 7)
            c.setFillColor(colors.HexColor("#555555"))
            c.drawString(x0 + 3 * mm, y - 15 * mm, opis)
            c.setFillColor(colors.black)
        y -= 21 * mm
        c.setFont(self.f, 8)
        c.drawString(self.M, y, "%s  %s · Winstore %s%s" % (m["ident"] or "—", (m["naziv"] or "")[:40], m["winstore_kod"] or "—",
                                                            ("  (na stanju %d kom)" % m["stanje_kom"]) if m["stanje_kom"] is not None and m["winstore_kod"] else ""))
        y -= 4.2 * mm
        c.drawString(self.M, y, "listova %d · rezova %d · korisni ostaci: %s" % (listova, st["rezova"],
                     ", ".join("%s × %s mm" % (_mm(o[0]), _mm(o[1])) for o in st["ostaci"]) if st["ostaci"] else "nema"))
        y -= 8 * mm
        c.setFont(self.fb, 9)
        c.drawString(self.M, y, "Kantiranje po traci (Σ stranica × kom + nadmjera %s %%)" % _mm((st["faktor_trake"] - 1) * 100))
        y -= 5 * mm
        data = [["", "Oznaka", "Ident", "Naziv trake", "Količina m", "Pretinac", "Na roli m"]]
        for t in d["trake"]:
            data.append(["", t["oznaka"], t["ident"] or "", t["naziv"] or "", _fmt(t["metri"], 2),
                         t["pretinac"] or "—", _fmt(t["preostalo"], 1) if t["preostalo"] is not None else "—"])
        if not d["trake"]:
            data.append(["", "", "", "bez traka", "", "", ""])
        tt = Table(data, colWidths=[6 * mm, 16 * mm, 22 * mm, 70 * mm, 22 * mm, 32 * mm, 18 * mm])
        sty = [("FONTNAME", (0, 0), (-1, -1), self.f), ("FONTSIZE", (0, 0), (-1, -1), 7.5), ("FONTNAME", (0, 0), (-1, 0), self.fb),
               ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black), ("LINEBELOW", (0, 1), (-1, -1), 0.2, colors.HexColor("#999999")),
               ("ALIGN", (4, 1), (4, -1), "RIGHT"), ("ALIGN", (6, 1), (6, -1), "RIGHT")]
        tt.setStyle(TableStyle(sty))
        w, h = tt.wrap(self.PW - 2 * self.M, y - self.M)
        tt.drawOn(c, self.M, y - h)

        y -= h + 4 * mm
        if not d["slaganje"]["potvrdjeno"]:
            c.setFont(self.fb, 9)
            c.setFillColor(colors.HexColor("#b00020"))
            c.drawString(self.M, y, "PRIJEDLOG — slaganje nije potvrđeno (D-75); nacrt nije za pilu dok ga netko ne potvrdi.")
            c.setFillColor(colors.black)
        self.podnozje(self.ukupno)
        c.showPage()
        if d.get("majke"):
            self.majke()

    def _skica(self, x0, y_vrh, sir_max, vis_max, L, W, clanovi, kerf=None):
        """Majka L × W (L vodoravno) s članovima; vraća visinu crteža. Crno-bijelo, mjere uz rubove."""
        c, mm = self.c, self.mm
        from reportlab.lib import colors
        sk = min(sir_max / max(L, 1), vis_max / max(W, 1))
        w, h = L * sk, W * sk
        y0 = y_vrh - h
        c.setLineWidth(0.8)
        c.rect(x0, y0, w, h, stroke=1, fill=0)
        c.setLineWidth(0.3)
        for m in clanovi:
            c.rect(x0 + m["x"] * sk, y0 + m["y"] * sk, m["L"] * sk, m["W"] * sk, stroke=1, fill=0)
            c.setFont(self.fb, 7 if min(m["L"], m["W"]) * sk > 6 * mm else 5)
            c.drawCentredString(x0 + (m["x"] + m["L"] / 2) * sk, y0 + (m["y"] + m["W"] / 2) * sk - 1 * mm, str(m["poz"]))
            c.setFont(self.f, 5.5)
            if min(m["L"], m["W"]) * sk > 9 * mm:
                c.drawCentredString(x0 + (m["x"] + m["L"] / 2) * sk, y0 + (m["y"] + m["W"] / 2) * sk - 3.5 * mm, "%s × %s" % (_mm(m["L"]), _mm(m["W"])))
        c.setFont(self.f, 7)
        c.drawCentredString(x0 + w / 2, y0 - 3.2 * mm, "%s mm" % _mm(L))
        c.saveState()
        c.translate(x0 + w + 3 * mm, y0 + h / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, "%s mm" % _mm(W))
        c.restoreState()
        return h + 5 * mm

    def majke(self):
        """Stranica 'Majke i sklopovi' (korak 6): za svaki niz goda, majku malih komada i sklop lijepljenja — skica s rezovima i članovi."""
        c, mm, d = self.c, self.mm, self.d
        from reportlab.lib import colors
        y = self.zaglavlje("Majke i sklopovi · %s" % d["materijal"]["kratki"], "Majke")
        c.setFont(self.f, 7.5)
        c.drawString(self.M, y - 4 * mm, "Veći komad se reže po ovoj skici (kerf pile između komada); trake i CNC obrada su po komadima, etiketa komada nosi oznaku (A2/3, IZ M1, LA1/2).")
        y -= 9 * mm
        for mk in d["majke"]:
            sk = mk["skica"]
            if mk["vrsta"] == "niz":
                ploce = [dict(L=sk["L"], W=sk["W"], clanovi=sk["clanovi"], naslov="NIZ GODA %s — %d fronti, smjer %s, kerf %s mm, majka %s × %s × %d kom"
                              % (mk["oznaka"], mk["clanova"], {"V": "okomito", "H": "vodoravno", "G": "mreža"}.get(mk["smjer"], mk["smjer"]), _mm(sk["kerf"]), _mm(sk["L"]), _mm(sk["W"]), mk["komada"] // max(mk["clanova"], 1)))]
            elif mk["vrsta"] == "mali":
                ploce = [dict(L=mj["L"], W=mj["W"], clanovi=mj["clanovi"], naslov="MAJKA %s — %d × komad %s × %s, %d majk%s, kerf %s mm; kant na majci: %s"
                              % (mk["oznaka"], mj["komada"], _mm(sk["komad"]["L"]), _mm(sk["komad"]["W"]), mj["majki"], "a" if mj["majki"] == 1 else "e", _mm(sk["kerf"]),
                                 " / ".join(k for k in sk["rub_kratki"] if k) or "—")) for mj in sk["majke"]]
            else:
                ploce = [dict(L=mk["L"], W=mk["W"], clanovi=[dict(poz="sloj %d" % s_["sloj"], x=0, y=0, L=s_["L"], W=s_["W"]) for s_ in sk["slojevi"][:1]],
                              naslov="SKLOP LIJEPLJENJA %s — %d slojeva, konačna %s × %s, %s mm; slojevi se režu na sirovu mjeru (+10), kant na sklopu"
                              % (mk["oznaka"], mk["clanova"], _mm(mk["L"]), _mm(mk["W"]), _mm(mk["debljina"] or 0)))]
            for p in ploce:
                vis = min(60 * mm, (self.PW - 2 * self.M - 10 * mm) * p["W"] / max(p["L"], 1)) + 14 * mm
                if y - vis - 6 * mm < self.M + 12 * mm:
                    self.podnozje(self.ukupno)
                    c.showPage()
                    y = self.zaglavlje("Majke i sklopovi · %s" % d["materijal"]["kratki"], "Majke (nastavak)") - 4 * mm
                c.setFont(self.fb, 8.5)
                c.drawString(self.M, y - 3 * mm, p["naslov"][:120])
                if mk["provjeri"] and mk["napomena"]:
                    c.setFont(self.f, 7)
                    c.setFillColor(colors.HexColor("#b00020"))
                    c.drawString(self.M, y - 6.5 * mm, "PROVJERI: " + mk["napomena"][:130])
                    c.setFillColor(colors.black)
                    y -= 3.5 * mm
                h = self._skica(self.M + 2 * mm, y - 6 * mm, self.PW - 2 * self.M - 10 * mm, 60 * mm, p["L"], p["W"], p["clanovi"])
                y -= h + 9 * mm
                # članovi
                c.setFont(self.f, 7)
                for cl in mk["clanovi"]:
                    if y < self.M + 12 * mm:
                        self.podnozje(self.ukupno)
                        c.showPage()
                        y = self.zaglavlje("Majke i sklopovi · %s" % d["materijal"]["kratki"], "Majke (nastavak)") - 4 * mm
                    c.drawString(self.M + 4 * mm, y, "%-8s %-30s %s × %s × %d%s   etiketa: %s" % (cl["majka_poz"] or "", (cl["naziv"] or "")[:30], _mm(cl["L"]), _mm(cl["W"]), cl["kom"],
                                                                                                  ("   reže se %s × %s" % (_mm(cl["rez_L"]), _mm(cl["rez_W"]))) if cl["rez_L"] else "", cl["napomena_rez"] or ""))
                    y -= 3.6 * mm
                y -= 4 * mm
        self.podnozje(self.ukupno)
        c.showPage()


def pdf(conn, nm_ids, put, oid=None):
    """PDF za jedan ili više materijala naloga (svaki: listovi + statistika). Vraća dict(put, materijala, listova, stranica)."""
    try:
        from reportlab.pdfgen import canvas as rc
        from reportlab.lib.pagesizes import A4
    except ImportError:
        raise IspisGreska("reportlab nije instaliran (pip install reportlab)")
    font, fontb = _font()
    datum = datetime.datetime.now().strftime("%d.%m.%Y. %H:%M")
    svi = [podaci(conn, nm, oid if len(nm_ids) == 1 else None) for nm in nm_ids]
    os.makedirs(os.path.dirname(os.path.abspath(put)), exist_ok=True)
    c = rc.Canvas(put, pagesize=A4)
    c.setTitle("Krojni nacrt %s" % svi[0]["nalog"]["naziv"])
    c.setAuthor("Paneli Production Hub")
    listova = 0
    for d in svi:
        nac = _Nacrt(c, d, font, fontb, datum, "%s · %s" % (d["nalog"]["naziv"], d["materijal"]["kratki"]))
        n = len(d["listovi"])
        for li in d["listovi"]:
            nac.list_ploce(li, n)
        nac.statistika(n)
        listova += n
    c.save()
    return dict(put=put, materijala=len(svi), listova=listova, stranica=c.getPageNumber() - 1, nalog=svi[0]["nalog"]["naziv"],
                potvrdjeno=all(d["slaganje"]["potvrdjeno"] for d in svi))


def _ime(d_nalog, nm_ids, conn):
    if len(nm_ids) == 1:
        m = N.materijal_naloga(conn, nm_ids[0])
        return "krojni_%s_%s.pdf" % (d_nalog, (m["naziv_kratki"] or m["naziv_ulaz"] or str(nm_ids[0])).replace(" ", "_").replace("/", "-"))
    return "krojni_%s.pdf" % d_nalog


def napravi(conn, nalog_id, mapa=None, nm_id=None, oid=None, tko="web", zabiljezi=True):
    """Napravi PDF (svi materijali koji se slažu na ploču ili jedan) u `<mapa>/<NALOG>/ISPIS/`; zabilježi kao dokument naloga."""
    n = N.nalog(conn, nalog_id)
    if nm_id:
        nm_ids = [nm_id]
    else:
        nm_ids = [r["id"] for r in conn.execute("SELECT nm.id FROM nalog_materijal nm WHERE nm.nalog_id = ? AND EXISTS (SELECT 1 FROM element e WHERE e.nalog_materijal_id = nm.id) "
                                                "ORDER BY nm.rb, nm.id", (nalog_id,)).fetchall() if OP.treba_optimizaciju(conn, r["id"])]
    if not nm_ids:
        raise IspisGreska("nalog %s nema materijala za krojni nacrt" % n["naziv"])
    if not mapa:
        mapa = postavka(conn, "mapa_ispisa")
    if not mapa:
        baza = conn.execute("PRAGMA database_list").fetchone()[2] or db.putanja_baze(None)
        mapa = os.path.join(os.path.dirname(os.path.abspath(baza)), "ispisi")
    put = os.path.join(mapa, n["naziv"], "ISPIS", _ime(n["naziv"], nm_ids, conn))
    r = pdf(conn, nm_ids, put, oid)
    if zabiljezi:
        conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, datum) VALUES (?, 'pdf_krojni', ?, ?)", (nalog_id, put, sada()))
        dnevnik(conn, tko, "nalog", nalog_id, "ispis_krojni", "%s: %d materijala, %d listova → %s" % (n["naziv"], r["materijala"], r["listova"], put))
        conn.commit()
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(description="Krojni nacrt PDF iz potvrđenog slaganja (D-75/D-76)")
    ap.add_argument("--db")
    ap.add_argument("--nalog", type=int, required=True)
    ap.add_argument("--materijal", type=int, help="nalog_materijal id (zadano: svi)")
    ap.add_argument("--oid", type=int, help="konkretan red optimizacije (prijedlog) umjesto potvrđenog")
    ap.add_argument("--mapa", help="mapa ispisa (zadano: postavka mapa_ispisa ili `ispisi` uz bazu)")
    ap.add_argument("--tko", default="cli")
    a = ap.parse_args(argv)
    conn = db.spoji(a.db)
    try:
        r = napravi(conn, a.nalog, a.mapa, a.materijal, a.oid, a.tko)
        print("%s: %d materijala, %d listova, %d stranica%s -> %s" % (r["nalog"], r["materijala"], r["listova"], r["stranica"],
                                                                      "" if r["potvrdjeno"] else " (PRIJEDLOG — nije potvrđeno)", r["put"]))
        return 0
    except (IspisGreska, OP.OptimizacijaGreska) as e:
        print("GREŠKA:", e)
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
