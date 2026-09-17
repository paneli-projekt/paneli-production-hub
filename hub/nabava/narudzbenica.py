# -*- coding: utf-8 -*-
"""nabava/narudzbenica.py — narudžbenica dobavljaču (D-42/5): nastaje u Hubu (iz potreba ili ručno, Sanela), po dobavljaču, šalje se mailom
kao ponuda (D-41), ZATVARA se automatski iz eSlog primke koju Knjiga radi za Pantheon (isti XML puni i Hub).

Tok:  potrebe (skladiste.pogled.potrebe_ukupno → manjak po identu)  →  `iz_potreba`: jedan NACRT po dobavljaču (dobavljač identa iz
      Pantheona, `pantheon_ident.dobavljac`; bez dobavljača → „NEPOZNAT DOBAVLJAČ“ nacrt koji Sanela preraspodijeli)  →  Sanela doradi
      (dodaj / ukloni / promijeni količinu, zaliha unaprijed bez naloga)  →  `posalji` (PDF + mail, status poslana)  →  primka:
      `uvezi_primku_eslog` čita eSlog XML (StevilkaArtiklaDodatna SA = naš ident, Kolicina + EnotaMere, dobavljač SE, ReferencniDokumenti ON =
      broj naše narudžbenice ako ga dobavljač vrati) i po identu FIFO zatvara otvorene stavke (poslana → djelomicno → zaprimljena); m² → ploče
      preko dimenzije ploče iz šifrarnika. Ručno `zaprimi` za primke bez eSlog-a.

    py -m hub.nabava.narudzbenica --db hub.db --iz-potreba [--dobavljac "IVERPAN d.o.o."] --tko SANELA
    py -m hub.nabava.narudzbenica --db hub.db --popis [--status nacrt,poslana]
    py -m hub.nabava.narudzbenica --db hub.db --posalji N-2026-001 [--na mail@dobavljac.hr] [--suho] --tko SANELA
    py -m hub.nabava.narudzbenica --db hub.db --primka ..\\..\\eslog_uvoz\\primka.xml --tko SANELA
"""
import argparse
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

from ..db import sada, dnevnik, postavka, postavi

STATUSI = ("nacrt", "poslana", "djelomicno", "zaprimljena", "ponistena")
OTVORENE = ("poslana", "djelomicno")
NEPOZNAT = "NEPOZNAT DOBAVLJAČ"


class NabavaGreska(Exception):
    pass


# ---------------------------------------------------------------- dobavljači
def dobavljaci(conn):
    """Dobavljači iz Pantheona (po identima) spojeni s Hubovim podacima (e-mail, kontakt): [{naziv, email, kontakt, identa, aktivan}]."""
    out = {}
    for r in conn.execute("SELECT dobavljac, COUNT(*) AS n FROM pantheon_ident WHERE dobavljac <> '' AND aktivan = 1 GROUP BY dobavljac"):
        out[r["dobavljac"]] = dict(naziv=r["dobavljac"], email=None, kontakt=None, identa=r["n"], aktivan=1, id=None)
    for r in conn.execute("SELECT * FROM dobavljac"):
        d = out.setdefault(r["naziv"], dict(naziv=r["naziv"], identa=0))
        d.update(id=r["id"], email=r["email"], kontakt=r["kontakt"], napomena=r["napomena"], aktivan=r["aktivan"])
    return sorted(out.values(), key=lambda d: (-(d.get("identa") or 0), d["naziv"]))


def upisi_dobavljaca(conn, naziv, email=None, kontakt=None, napomena=None, tko="web"):
    conn.execute("INSERT INTO dobavljac (naziv, email, kontakt, napomena) VALUES (?, ?, ?, ?) ON CONFLICT(naziv) DO UPDATE SET "
                 "email = COALESCE(excluded.email, dobavljac.email), kontakt = COALESCE(excluded.kontakt, dobavljac.kontakt), napomena = COALESCE(excluded.napomena, dobavljac.napomena)",
                 (naziv.strip(), email, kontakt, napomena))
    dnevnik(conn, tko, "dobavljac", None, "upis", "%s %s" % (naziv, email or ""))
    conn.commit()
    return conn.execute("SELECT * FROM dobavljac WHERE naziv = ?", (naziv.strip(),)).fetchone()


def email_dobavljaca(conn, naziv):
    r = conn.execute("SELECT email FROM dobavljac WHERE naziv = ?", (naziv,)).fetchone()
    return r["email"] if r and r["email"] else None


def _norm(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper().replace("Đ", "D").replace("Š", "S").replace("Ž", "Z").replace("Č", "C").replace("Ć", "C"))


def nadji_dobavljaca(conn, naziv):
    """Naziv iz eSlog primke → naziv dobavljača kakav Hub vodi (normalizirana usporedba, bez d.o.o. i sl.) ili None."""
    if not naziv:
        return None
    cilj = _norm(re.sub(r"\b(d\.?o\.?o\.?|j\.?d\.?o\.?o\.?|d\.?d\.?|obrt)\b", "", naziv, flags=re.I))
    if not cilj:
        return None
    kand = [d["naziv"] for d in dobavljaci(conn)]
    for k in kand:
        if _norm(re.sub(r"\b(d\.?o\.?o\.?|j\.?d\.?o\.?o\.?|d\.?d\.?|obrt)\b", "", k, flags=re.I)) == cilj:
            return k
    for k in kand:
        kn = _norm(k)
        if cilj in kn or kn in cilj:
            return k
    return None


# ---------------------------------------------------------------- narudžbenica
def _broj(conn):
    god = sada()[:4]
    k = "brojac_narudzbenica_%s" % god
    n = int(postavka(conn, k, "0") or 0) + 1
    postavi(conn, k, str(n), "brojač narudžbenica po godini")
    return "N-%s-%03d" % (god, n)


def nova(conn, dobavljac, tko, stavke=(), napomena=None, ocekivano=None, commit=True):
    """Nova narudžbenica (nacrt). stavke: [{ident, kom, jm, dimenzija, nalog_materijal_id, naziv}]. Vraća red s stavkama."""
    from ..nalozi.nalozi import korisnik_id
    if not dobavljac:
        raise NabavaGreska("narudžbenica treba dobavljača")
    broj = _broj(conn)
    cur = conn.execute("INSERT INTO narudzbenica (broj, dobavljac, datum, narucio_id, ocekivano, status, napomena) VALUES (?, ?, ?, ?, ?, 'nacrt', ?)",
                       (broj, dobavljac.strip(), sada()[:10], korisnik_id(conn, tko), ocekivano, napomena))
    nid = cur.lastrowid
    for s in stavke:
        dodaj_stavku(conn, nid, s["ident"], s["kom"], jm=s.get("jm"), dimenzija=s.get("dimenzija"), nalog_materijal_id=s.get("nalog_materijal_id"),
                     naziv=s.get("naziv"), commit=False)
    dnevnik(conn, tko, "narudzbenica", nid, "nova", "%s %s: %d stavki" % (broj, dobavljac, len(stavke)))
    if commit:
        conn.commit()
    return red(conn, nid)


def dodaj_stavku(conn, nid, ident, kom, jm=None, dimenzija=None, nalog_materijal_id=None, naziv=None, commit=True):
    n = conn.execute("SELECT status FROM narudzbenica WHERE id = ?", (nid,)).fetchone()
    if not n:
        raise NabavaGreska("nema narudžbenice %s" % nid)
    if n["status"] != "nacrt":
        raise NabavaGreska("stavke se mijenjaju samo u nacrtu (status %s)" % n["status"])
    pi = conn.execute("SELECT ident, naziv, jm FROM pantheon_ident WHERE ident = ?", (ident,)).fetchone()
    if not pi:
        raise NabavaGreska("nepoznat ident %s" % ident)
    if not kom or float(kom) <= 0:
        raise NabavaGreska("količina mora biti > 0")
    m = conn.execute("SELECT ploca_L, ploca_W FROM materijal WHERE pantheon_ident = ?", (ident,)).fetchone()
    if dimenzija is None and m and m["ploca_L"] and m["ploca_W"]:
        dimenzija = "%g×%g" % (m["ploca_L"], m["ploca_W"])
    if jm is None:
        jm = "PLOČA" if m else (pi["jm"] or "KOM")
    st = conn.execute("SELECT id, kom FROM narudzbenica_st WHERE narudzbenica_id = ? AND pantheon_ident = ? AND nalog_materijal_id IS ?",
                      (nid, ident, nalog_materijal_id)).fetchone()
    if st:
        conn.execute("UPDATE narudzbenica_st SET kom = kom + ? WHERE id = ?", (float(kom), st["id"]))
    else:
        conn.execute("INSERT INTO narudzbenica_st (narudzbenica_id, pantheon_ident, naziv, kom, jm, dimenzija, nalog_materijal_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (nid, ident, naziv or pi["naziv"], float(kom), jm, dimenzija, nalog_materijal_id))
    if commit:
        conn.commit()


def ukloni_stavku(conn, stavka_id, commit=True):
    st = conn.execute("SELECT s.id, n.status FROM narudzbenica_st s JOIN narudzbenica n ON n.id = s.narudzbenica_id WHERE s.id = ?", (stavka_id,)).fetchone()
    if not st:
        raise NabavaGreska("nema stavke %s" % stavka_id)
    if st["status"] != "nacrt":
        raise NabavaGreska("stavke se mijenjaju samo u nacrtu")
    conn.execute("DELETE FROM narudzbenica_st WHERE id = ?", (stavka_id,))
    if commit:
        conn.commit()


def promijeni_stavku(conn, stavka_id, kom, commit=True):
    st = conn.execute("SELECT s.id, n.status FROM narudzbenica_st s JOIN narudzbenica n ON n.id = s.narudzbenica_id WHERE s.id = ?", (stavka_id,)).fetchone()
    if not st or st["status"] != "nacrt":
        raise NabavaGreska("stavke se mijenjaju samo u nacrtu")
    if float(kom) <= 0:
        return ukloni_stavku(conn, stavka_id, commit)
    conn.execute("UPDATE narudzbenica_st SET kom = ? WHERE id = ?", (float(kom), stavka_id))
    if commit:
        conn.commit()


def red(conn, nid):
    r = conn.execute("SELECT n.*, k.oznaka AS narucio FROM narudzbenica n LEFT JOIN korisnik k ON k.id = n.narucio_id WHERE n.id = ? OR n.broj = ?", (nid, nid)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["stavke"] = [dict(s, otvoreno=round(s["kom"] - s["zaprimljeno_kom"], 3)) for s in conn.execute(
        "SELECT s.*, nm.nalog_id, n.naziv AS nalog FROM narudzbenica_st s LEFT JOIN nalog_materijal nm ON nm.id = s.nalog_materijal_id "
        "LEFT JOIN nalog n ON n.id = nm.nalog_id WHERE s.narudzbenica_id = ? ORDER BY s.id", (r["id"],))]
    d["email"] = email_dobavljaca(conn, r["dobavljac"])
    return d


def popis(conn, status=None, dobavljac=None):
    sql = "SELECT n.*, (SELECT COUNT(*) FROM narudzbenica_st s WHERE s.narudzbenica_id = n.id) AS stavki, " \
          "(SELECT COALESCE(SUM(s.kom - s.zaprimljeno_kom), 0) FROM narudzbenica_st s WHERE s.narudzbenica_id = n.id) AS otvoreno FROM narudzbenica n WHERE 1 = 1"
    a = []
    if status:
        st = [x.strip() for x in status.split(",")]
        sql += " AND n.status IN (%s)" % ", ".join("?" * len(st)); a += st
    if dobavljac:
        sql += " AND n.dobavljac = ?"; a.append(dobavljac)
    return [dict(r) for r in conn.execute(sql + " ORDER BY n.id DESC", a)]


# ---------------------------------------------------------------- iz potreba (D-42/5)
def iz_potreba(conn, tko, dobavljac=None, samo_manjak=True):
    """Iz potreba preko svih potvrđenih naloga napravi NACRT po dobavljaču (ploče u KOM ploča, trake u M naviše). Ident bez dobavljača
    u Pantheonu ide u nacrt 'NEPOZNAT DOBAVLJAČ'. Ono što je već na otvorenoj narudžbenici ne naručuje se dvaput (manjak to već računa).
    Vraća [narudžbenica]."""
    from ..skladiste import pogled as SK
    u = SK.potrebe_ukupno(conn)
    po_dob = {}
    for z in u["za_nabavu"]:
        if samo_manjak and not z["kom"]:
            continue
        pi = conn.execute("SELECT dobavljac FROM pantheon_ident WHERE ident = ?", (z["ident"],)).fetchone()
        dob = (pi["dobavljac"] if pi and pi["dobavljac"] else None) or NEPOZNAT
        if dobavljac and dob != dobavljac:
            continue
        kom = int(math.ceil(z["kom"] - 1e-9))
        po_dob.setdefault(dob, []).append(dict(ident=z["ident"], kom=kom, jm=z["jm"], naziv=z["naziv"], nalog_materijal_id=None))
    out = []
    for dob, stavke in po_dob.items():
        n = nova(conn, dob, tko, stavke, napomena="iz potreba %s (D-42/5)" % sada()[:10], commit=False)
        out.append(n)
    conn.commit()
    return out


# ---------------------------------------------------------------- slanje (D-41 mehanizam)
def posalji(conn, nid, tko, na=None, suho=False, mapa=None, tekst=None):
    """PDF + mail dobavljaču; status → poslana. Bez adrese (ni argument ni dobavljac.email) → greška. suho: sastavi, ne šalji, status ostaje."""
    from ..nalozi import mail as M
    from ..ispis import narudzbenica as PDF
    d = red(conn, nid)
    if not d:
        raise NabavaGreska("nema narudžbenice %s" % nid)
    if d["status"] not in ("nacrt", "poslana"):
        raise NabavaGreska("narudžbenica %s je %s" % (d["broj"], d["status"]))
    if not d["stavke"]:
        raise NabavaGreska("narudžbenica %s nema stavki" % d["broj"])
    na = na or d["email"]
    if not na and not suho:
        raise NabavaGreska("dobavljač %s nema e-mail — upisati ga (dobavljac.email) ili zadati adresu" % d["dobavljac"])
    mapa = mapa or postavka(conn, "mapa_narudzbenice", os.path.join(os.path.dirname(conn.execute("PRAGMA database_list").fetchone()[2] or "."), "NARUDZBENICE"))
    put = PDF.napravi(conn, d["id"], mapa)
    predmet = "Narudžba %s — Paneli projekt d.o.o." % d["broj"]
    from .. import korisnici as KO
    tekst = tekst or ("Poštovani,\n\nu prilogu je narudžba %s (%d stavki). Molimo potvrdu roka isporuke.\n\nLijep pozdrav,\n%s\n" % (d["broj"], len(d["stavke"]), KO.potpis(conn, tko)))
    rez = M.posalji(conn, na or "(bez adrese)", predmet, tekst, prilozi=[put] if put else (), tko=tko, suho=suho)
    if not suho:
        conn.execute("UPDATE narudzbenica SET status = 'poslana', poslano_kada = ?, poslano_na = ?, put_pdf = ? WHERE id = ?", (sada(), na, put, d["id"]))
        dnevnik(conn, tko, "narudzbenica", d["id"], "poslana", "%s → %s" % (d["broj"], na))
    else:
        conn.execute("UPDATE narudzbenica SET put_pdf = ? WHERE id = ?", (put, d["id"]))
    conn.commit()
    return dict(red(conn, d["id"]), mail=rez, pdf=put)


def ponisti(conn, nid, tko, razlog=None):
    d = red(conn, nid)
    if not d:
        raise NabavaGreska("nema narudžbenice %s" % nid)
    if d["status"] == "zaprimljena":
        raise NabavaGreska("zaprimljena narudžbenica se ne poništava")
    conn.execute("UPDATE narudzbenica SET status = 'ponistena', napomena = COALESCE(napomena || '; ', '') || ? WHERE id = ?", ("poništena: " + (razlog or ""), d["id"]))
    dnevnik(conn, tko, "narudzbenica", d["id"], "ponistena", razlog or "")
    conn.commit()
    return red(conn, d["id"])


# ---------------------------------------------------------------- zaprimanje
def _osvjezi_status(conn, nid):
    r = conn.execute("SELECT COALESCE(SUM(kom), 0) AS kom, COALESCE(SUM(zaprimljeno_kom), 0) AS z FROM narudzbenica_st WHERE narudzbenica_id = ?", (nid,)).fetchone()
    st = "zaprimljena" if r["z"] >= r["kom"] - 1e-6 else ("djelomicno" if r["z"] > 0 else "poslana")
    conn.execute("UPDATE narudzbenica SET status = ? WHERE id = ? AND status IN ('poslana', 'djelomicno', 'zaprimljena')", (st, nid))
    return st


def zaprimi(conn, nid, stavke, tko, ref=None, commit=True):
    """Ručna primka: stavke = {ident: kom} u JM narudžbenice. Višak iznad naručenog se prijavi, ne odbija (dobavljač zna poslati više)."""
    d = red(conn, nid)
    if not d:
        raise NabavaGreska("nema narudžbenice %s" % nid)
    if d["status"] not in OTVORENE + ("nacrt",):
        raise NabavaGreska("narudžbenica %s je %s" % (d["broj"], d["status"]))
    upoz = []
    for ident, kom in stavke.items():
        st = [s for s in d["stavke"] if s["pantheon_ident"] == ident]
        if not st:
            upoz.append("%s nije na narudžbenici %s" % (ident, d["broj"])); continue
        conn.execute("UPDATE narudzbenica_st SET zaprimljeno_kom = zaprimljeno_kom + ?, primka_ref = COALESCE(?, primka_ref) WHERE id = ?", (float(kom), ref, st[0]["id"]))
        if st[0]["zaprimljeno_kom"] + float(kom) > st[0]["kom"] + 1e-6:
            upoz.append("%s: zaprimljeno %g > naručeno %g" % (ident, st[0]["zaprimljeno_kom"] + float(kom), st[0]["kom"]))
    status = _osvjezi_status(conn, d["id"])
    dnevnik(conn, tko, "narudzbenica", d["id"], "primka", "%s %s: %s → %s" % (d["broj"], ref or "", ", ".join("%s %g" % kv for kv in stavke.items()), status))
    if commit:
        conn.commit()
    return dict(red(conn, d["id"]), upozorenja=upoz)


def citaj_primku_eslog(putanja):
    """eSlog račun / primka (skill primke-pantheon, Knjiga) → dict(broj, datum, dobavljac, narudzba_ref, stavke:[{ident, naziv, kolicina, jm}])."""
    root = ET.parse(putanja).getroot()
    rac = root.find(".//Racun") if root.find(".//Racun") is not None else root

    def t(el, path):
        x = el.find(path) if el is not None else None
        return (x.text or "").strip() if x is not None and x.text else ""
    dob = ""
    for p in rac.findall("PodatkiPodjetja"):
        if t(p, "NazivNaslovPodjetja/VrstaPartnerja") in ("SE", "SU") and not dob:
            dob = t(p, "NazivNaslovPodjetja/NazivPartnerja/NazivPartnerja1")
    ref = ""
    for r in rac.findall("ReferencniDokumenti"):
        if r.get("VrstaDokumenta") == "ON":
            ref = t(r, "StevilkaDokumenta")
    st = []
    for p in rac.findall("PostavkeRacuna"):
        ident = ""
        for d in p.findall("DodatnaIdentifikacijaArtikla"):
            if t(d, "VrstaKodeArtiklaDodatna") in ("SA", "IN", "PV") and not ident:
                ident = t(d, "StevilkaArtiklaDodatna")
        if not ident:
            ident = t(p, "Postavka/IdentifikacijaArtikla/StevilkaArtikla")
        try:
            kol = float(t(p, "KolicinaArtikla/Kolicina").replace(",", "."))
        except ValueError:
            kol = 0.0
        st.append(dict(ident=ident.upper(), naziv=t(p, "OpisiArtiklov/OpisArtikla/OpisArtikla1"), kolicina=kol, jm=t(p, "KolicinaArtikla/EnotaMere")))
    return dict(broj=t(rac, "GlavaRacuna/StevilkaRacuna"), datum=t(rac, "DatumiRacuna/DatumRacuna")[:10], dobavljac=dob, narudzba_ref=ref, stavke=st,
                datoteka=os.path.basename(putanja))


def _u_jm_narudzbe(conn, ident, kolicina, jm_primke, jm_narudzbe):
    """m² s primke → ploče (dimenzija ploče iz šifrarnika); MTR/M → M; inače 1:1."""
    jp = (jm_primke or "").upper()
    if jm_narudzbe == "PLOČA" and jp in ("M2", "MTK", "M²"):
        m = conn.execute("SELECT ploca_L, ploca_W FROM materijal WHERE pantheon_ident = ?", (ident,)).fetchone()
        if m and m["ploca_L"] and m["ploca_W"]:
            return kolicina / (m["ploca_L"] * m["ploca_W"] / 1e6), "m² → ploče (%g×%g)" % (m["ploca_L"], m["ploca_W"])
        return kolicina, "m² bez dimenzije ploče — 1:1"
    return kolicina, None


def uvezi_primku_eslog(conn, putanja, tko, commit=True):
    """eSlog primka → zatvara otvorene narudžbenice: po broju naše narudžbe (ReferencniDokumenti ON) ako ga dobavljač vrati, inače po dobavljaču
    i identu FIFO (najstarija poslana prva). Vraća izvještaj: spojeno, nespojeno (ident nije ni na jednoj otvorenoj), dobavljač."""
    p = citaj_primku_eslog(putanja)
    if not p["stavke"]:
        raise NabavaGreska("%s: nema stavki" % p["datoteka"])
    dob = nadji_dobavljaca(conn, p["dobavljac"])
    kand = []
    if p["narudzba_ref"]:
        kand = [r for r in popis(conn, status="poslana,djelomicno") if r["broj"] == p["narudzba_ref"].strip()]
    if not kand:
        kand = [r for r in popis(conn, status="poslana,djelomicno") if not dob or r["dobavljac"] == dob or r["dobavljac"] == NEPOZNAT]
        kand.sort(key=lambda r: r["id"])
    spojeno, nespojeno, pretvorbe = [], [], []
    ref = "%s %s" % (p["broj"], p["datum"])
    dirnute = set()
    for s in p["stavke"]:
        ostalo = s["kolicina"]
        for n in kand:
            for st in conn.execute("SELECT * FROM narudzbenica_st WHERE narudzbenica_id = ? AND pantheon_ident = ? AND kom - zaprimljeno_kom > 1e-6 ORDER BY id",
                                   (n["id"], s["ident"])).fetchall():
                if ostalo <= 1e-9:
                    break
                kol, opis = _u_jm_narudzbe(conn, s["ident"], ostalo, s["jm"], st["jm"])   # kol = `ostalo` izraženo u JM narudžbe
                if opis and opis not in pretvorbe:
                    pretvorbe.append("%s: %s" % (s["ident"], opis))
                f = kol / ostalo if ostalo else 1.0
                uzmi = min(kol, st["kom"] - st["zaprimljeno_kom"])
                conn.execute("UPDATE narudzbenica_st SET zaprimljeno_kom = zaprimljeno_kom + ?, primka_ref = ? WHERE id = ?", (uzmi, ref, st["id"]))
                dirnute.add(n["id"])
                spojeno.append(dict(ident=s["ident"], narudzbenica=n["broj"], kom=round(uzmi, 3), jm=st["jm"]))
                ostalo -= uzmi / f if f else uzmi
        if ostalo > 1e-6:
            nespojeno.append(dict(ident=s["ident"], naziv=s["naziv"], kolicina=round(ostalo, 3), jm=s["jm"]))
    statusi = {n: _osvjezi_status(conn, n) for n in dirnute}
    dnevnik(conn, tko, "narudzbenica", None, "eSlog primka", "%s %s: spojeno %d, nespojeno %d" % (p["datoteka"], p["dobavljac"], len(spojeno), len(nespojeno)))
    if commit:
        conn.commit()
    return dict(datoteka=p["datoteka"], racun=p["broj"], datum=p["datum"], dobavljac_primke=p["dobavljac"], dobavljac=dob, narudzba_ref=p["narudzba_ref"],
                spojeno=spojeno, nespojeno=nespojeno, pretvorbe=pretvorbe, statusi={conn.execute("SELECT broj FROM narudzbenica WHERE id = ?", (k,)).fetchone()[0]: v for k, v in statusi.items()})


# ---------------------------------------------------------------- CLI
def main(argv=None):
    from .. import db
    ap = argparse.ArgumentParser(description="Nabava (D-42/5): narudžbenice iz potreba, slanje, primke")
    ap.add_argument("--db"); ap.add_argument("--tko", default="cli")
    ap.add_argument("--iz-potreba", action="store_true"); ap.add_argument("--dobavljac")
    ap.add_argument("--popis", action="store_true"); ap.add_argument("--status")
    ap.add_argument("--posalji", metavar="BROJ"); ap.add_argument("--na"); ap.add_argument("--suho", action="store_true"); ap.add_argument("--mapa")
    ap.add_argument("--primka", metavar="XML")
    ap.add_argument("--dobavljaci", action="store_true")
    a = ap.parse_args(argv)
    conn = db.spoji(a.db)
    if a.dobavljaci:
        for d in dobavljaci(conn):
            print("%-40s %4d identa  %s" % (d["naziv"], d.get("identa") or 0, d.get("email") or "-"))
    if a.iz_potreba:
        for n in iz_potreba(conn, a.tko, a.dobavljac):
            print("%s %s: %d stavki" % (n["broj"], n["dobavljac"], len(n["stavke"])))
            for s in n["stavke"]:
                print("   %s %-40s %g %s" % (s["pantheon_ident"], (s["naziv"] or "")[:40], s["kom"], s["jm"]))
    if a.popis:
        for n in popis(conn, a.status):
            print("%s %-12s %-30s %s stavki, otvoreno %g" % (n["broj"], n["status"], n["dobavljac"][:30], n["stavki"], n["otvoreno"]))
    if a.posalji:
        r = posalji(conn, a.posalji, a.tko, na=a.na, suho=a.suho, mapa=a.mapa)
        print("%s → %s (%s), PDF %s" % (r["broj"], r["mail"]["na"], "suho" if a.suho else "poslano", r["pdf"]))
    if a.primka:
        r = uvezi_primku_eslog(conn, a.primka, a.tko)
        print("primka %s (%s): spojeno %d, nespojeno %d, statusi %s" % (r["racun"], r["dobavljac"] or r["dobavljac_primke"], len(r["spojeno"]), len(r["nespojeno"]), r["statusi"]))
        for x in r["nespojeno"]:
            print("   NESPOJENO", x)
    return 0


if __name__ == "__main__":
    sys.exit(main())
