# -*- coding: utf-8 -*-
"""Uvoz postojećih datoteka u nalog kroz šifrarnik (D-30 ulazi A i B):
  CPW  — kupčev PPW (01_ulaz_kupca), PanelWizard / PPNEST export, Corpus paket (FORMAT;CORPUS->PW)
  CSV  — PPNEST CSV za bNest (SIFRA MAT = Winstore kod → razina 'winstore')
Čitanje datoteka je u hub.formati.nalog_io (read_cpw, read_ppnest_csv); ovdje je samo grupiranje po materijalu, prepoznavanje i upis.
Isti materijal u više datoteka (PPNEST izvozi po jednu CPW/CSV po materijalu, ponekad dvije za isti) spaja se u jedan materijal naloga.
Svaka datoteka se bilježi u `dokument` (vrsta cpw_ulaz | cpw_pw | csv, hash) — dvaput isti sadržaj se ne uvozi.
"""
import glob
import hashlib
import os
import re

from ..db import sada, dnevnik
from ..formati import nalog_io
from ..sifrarnici.nazivi import norm
from . import nalozi as N


def _hash(putanja):
    return hashlib.sha1(open(putanja, "rb").read()).hexdigest()


def _kljuc(mat, deb):
    return (norm(mat), round(float(deb or 0), 1))


def _nadji_materijal(conn, nalog_id, mat, deb):
    """Postojeći materijal naloga s istim ulaznim nazivom i debljinom (spajanje više datoteka istog materijala)."""
    for r in conn.execute("SELECT id, naziv_ulaz, debljina_ulaz FROM nalog_materijal WHERE nalog_id = ?", (nalog_id,)):
        if r["naziv_ulaz"] and _kljuc(r["naziv_ulaz"], r["debljina_ulaz"]) == _kljuc(mat, deb):
            return r["id"]
    return None


def uvezi_elemente(conn, nalog_id, elementi, tko, izvor, datoteka=None, vrsta_dok=None):
    """Zajednički dio: elementi u nalog_io zapisu (mat, deb, sifra_mat, L, W, kom, god, traka{}, tip{}, cix, napomena) → materijali + elementi."""
    st = dict(materijali_novi=0, materijali_spojeni=0, elementi=0, komada=0, za_potvrdu_materijal=0, za_potvrdu_rub=0, preskoceno=0)
    if datoteka:
        h = _hash(datoteka)
        vec = conn.execute("SELECT id FROM dokument WHERE nalog_id = ? AND hash = ?", (nalog_id, h)).fetchone()
        if vec:
            st["preskoceno"] = 1
            return st
        conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, hash, datum) VALUES (?, ?, ?, ?, ?)", (nalog_id, vrsta_dok or "cpw_ulaz", os.path.abspath(datoteka), h, sada()))
    nm_po_kljucu = {}
    for e in elementi:
        k = _kljuc(e["mat"], e["deb"])
        if k not in nm_po_kljucu:
            nm_id = _nadji_materijal(conn, nalog_id, e["mat"], e["deb"])
            if nm_id:
                st["materijali_spojeni"] += 1
            else:
                nm, rez = N.dodaj_materijal(conn, nalog_id, tko, naziv_ulaz=e["mat"], debljina_ulaz=float(e["deb"]) if e["deb"] else None,
                                            winstore_kod_ulaz=(e.get("sifra_mat") or None), god=(1 if e.get("god") else None) if izvor == "csv" else None)
                nm_id = nm["id"]
                st["materijali_novi"] += 1
                if nm["provjeri"]:
                    st["za_potvrdu_materijal"] += 1
            nm_po_kljucu[k] = nm_id
        el = N.dodaj_element(conn, nm_po_kljucu[k], tko, e["L"], e["W"], e["kom"], naziv=(e.get("naziv") or None),
                             rubovi=e.get("traka") or {}, tipovi=e.get("tip") or {}, god=("H" if e.get("god") else None),
                             napomena=(e.get("napomena") or None), izvor=izvor, cix_ime=(e.get("cix") or None),
                             cix_izvor=("ppnest" if izvor == "csv" else None))
        st["elementi"] += 1
        st["komada"] += int(e["kom"])
        if el["provjeri"]:
            st["za_potvrdu_rub"] += 1
    dnevnik(conn, tko, "nalog", nalog_id, "uvoz", "%s: %d materijala (%d spojeno), %d elemenata, %d kom, za potvrdu %d mat + %d rub"
            % (os.path.basename(datoteka) if datoteka else izvor, st["materijali_novi"], st["materijali_spojeni"], st["elementi"], st["komada"],
               st["za_potvrdu_materijal"], st["za_potvrdu_rub"]))
    conn.commit()
    return st


def uvezi_cpw(conn, nalog_id, putanja, tko, izvor="cpw"):
    """CPW datoteka (kupac / PW / Corpus). izvor: 'kupac_ppw' | 'cpw' | 'corpus'."""
    els = nalog_io.read_cpw(putanja)
    for e in els:
        e["naziv"] = e.get("napomena") or ""       # u CPW-u je 2. polje naziv elementa; PPNEST ga piše prazno
        e["napomena"] = ""
    return uvezi_elemente(conn, nalog_id, els, tko, izvor, datoteka=putanja, vrsta_dok="cpw_ulaz" if izvor == "kupac_ppw" else "cpw_pw")


def uvezi_ppnest_csv(conn, nalog_id, putanja, tko):
    els = nalog_io.read_ppnest_csv(putanja)
    return uvezi_elemente(conn, nalog_id, els, tko, "csv", datoteka=putanja, vrsta_dok="csv")


_PPNEST_IME = re.compile(r"^(?P<osnova>.+?)_(?P<datum>\d{6})_(?P<vrijeme>\d{6})(?: \(\d+\))?\.(?P<ext>cpw|csv)$", re.I)


def najnovije_datoteke(datoteke):
    """PPNEST pri ponovnom izvozu istog materijala ostavlja i staru datoteku (isti naziv, drugi datum_vrijeme) — uzmi samo najnoviju
    po osnovi imena. Vraća (za_uvoz, preskocene_starije)."""
    po_osnovi = {}
    ostale = []
    for p in datoteke:
        m = _PPNEST_IME.match(os.path.basename(p))
        if not m:
            ostale.append(p)
            continue
        k = (os.path.dirname(p), m.group("osnova").lower(), m.group("ext").lower())
        po_osnovi.setdefault(k, []).append((m.group("datum")[4:6] + m.group("datum")[2:4] + m.group("datum")[0:2] + m.group("vrijeme"), p))
    za_uvoz, starije = list(ostale), []
    for k, lst in po_osnovi.items():
        lst.sort()
        za_uvoz.append(lst[-1][1])
        starije += [p for _, p in lst[:-1]]
    return sorted(za_uvoz), sorted(starije)


def uvezi_mapu(conn, nalog_id, mapa, tko, uzorak="*.CPW", izvor="cpw", samo_najnovije=True):
    """Sve datoteke iz mape (bez duplikata — Windows glob ne razlikuje velika/mala slova); starije verzije istog PPNEST izvoza se preskaču."""
    datoteke = sorted({os.path.normpath(p) for u in {uzorak, uzorak.lower(), uzorak.upper()} for p in glob.glob(os.path.join(mapa, u))})
    starije = []
    if samo_najnovije:
        datoteke, starije = najnovije_datoteke(datoteke)
    ukupno = dict(datoteke=0, materijali_novi=0, materijali_spojeni=0, elementi=0, komada=0, za_potvrdu_materijal=0, za_potvrdu_rub=0, preskoceno=0,
                  preskocene_starije=[os.path.basename(p) for p in starije])
    for p in datoteke:
        st = uvezi_ppnest_csv(conn, nalog_id, p, tko) if p.lower().endswith(".csv") else uvezi_cpw(conn, nalog_id, p, tko, izvor)
        ukupno["datoteke"] += 1
        for k in st:
            ukupno[k] += st[k]
    return ukupno
