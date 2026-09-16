# -*- coding: utf-8 -*-
"""Čitanje bSolid CIX datoteke (Corpus / bSolid / Hub) — samo čitanje, datoteka se ne mijenja (D-29: Corpus je CAM autoritet).

Iz CIX-a Hub deterministički izvuče ono što treba za provjeru i etiketu (08 §3.1, dokument 14 §3.4):
  mjere (LPX × LPY × LPZ), broj bušenja po strani (makro BG: SIDE 0 = vertikalno, 1–4 = horizontalno u kant),
  utore (CUT_X / CUT_Y), konturu (GEO + ROUTG; pravokutnik = 5 × LINE_EP) i je li kontura krivolinijska (više točaka ili luk).
Ništa se ne interpretira dalje — što alat radi s tim odlučuje operater u bSolidu.
"""
import collections
import re

_MAKRO = re.compile(r"BEGIN MACRO(.*?)END MACRO", re.S)
_PARAM = re.compile(r"PARAM,NAME=(\w+),VALUE=\"?([^\"\r\n]*?)\"?\s*$", re.M)


def _broj(s):
    try:
        return float(str(s).replace(",", "."))
    except (TypeError, ValueError):
        return None


def procitaj(putanja):
    """→ dict(L, W, deb, busenja, busenja_h, utora, kontura_tocaka, lukova, krivolinija, ima_obradu, makroi{ime: broj}, opis)."""
    txt = open(putanja, "rb").read().decode("latin-1")
    if "BEGIN ID CID3" not in txt and "BEGIN MAINDATA" not in txt:
        raise ValueError("%s nije bSolid CIX (nema CID3 / MAINDATA)" % putanja)
    md = dict(re.findall(r"^\s*(LPX|LPY|LPZ)=(\S+)", txt, re.M))
    makroi = collections.Counter()
    busenja = busenja_h = utora = lukova = 0
    tocaka = 0
    for blok in _MAKRO.findall(txt):
        m = re.search(r"NAME=(\w+)", blok)
        if not m:
            continue
        ime = m.group(1)
        makroi[ime] += 1
        par = dict(_PARAM.findall(blok))
        if ime == "BG":
            if str(par.get("SIDE", "0")).strip() in ("0", ""):
                busenja += 1
            else:
                busenja_h += 1
        elif ime in ("CUT_X", "CUT_Y", "CUT_G", "CUT_GEO"):
            utora += 1
        elif ime == "LINE_EP":
            tocaka += 1
        elif ime.startswith("ARC_"):
            lukova += 1
    krivolinija = lukova > 0 or tocaka > 5             # pravokutna kontura = 5 LINE_EP (natrag u početnu točku)
    d = dict(L=_broj(md.get("LPX")), W=_broj(md.get("LPY")), deb=_broj(md.get("LPZ")),
             busenja=busenja, busenja_h=busenja_h, utora=utora, kontura_tocaka=tocaka, lukova=lukova,
             krivolinija=krivolinija, ima_obradu=bool(busenja or busenja_h or utora or krivolinija), makroi=dict(makroi))
    d["opis"] = opis(d)
    return d


def opis(d):
    """Kratak tekst za ekran / etiketu: '22 bus, 2 utora' / 'kontura' / '12 bus kant'."""
    dijelovi = []
    if d.get("busenja"):
        dijelovi.append("%d bus" % d["busenja"])
    if d.get("busenja_h"):
        dijelovi.append("%d bus kant" % d["busenja_h"])
    if d.get("utora"):
        dijelovi.append("%d utor%s" % (d["utora"], "" if d["utora"] == 1 else "a"))
    if d.get("krivolinija"):
        dijelovi.append("krivolinija")
    return ", ".join(dijelovi) if dijelovi else "kontura"


def odgovara_elementu(d, L, W, deb=None, tol=0.6):
    """CIX mjere = mjere elementa (bilo koji smjer); debljina uz toleranciju (Corpus MDF 4 vs ploča 3, D-57 → deb se ne provjerava strogo)."""
    if d["L"] is None or d["W"] is None:
        return False
    a, b = sorted((float(L), float(W)))
    c, e = sorted((d["L"], d["W"]))
    return abs(a - c) <= tol and abs(b - e) <= tol
