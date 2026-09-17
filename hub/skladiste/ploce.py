# -*- coding: utf-8 -*-
"""skladiste/ploce.py — prilagodnik za PUNE PLOČE (D-64): vlasnik broja je Winstore (dnevni XML → `winstore_ploca`, hub.sifrarnici.winstore).

Winstore pokriva SVE pune ploče (Igor, 16. 9.), pa Hub ploče nigdje drugdje ne broji: `stanje` čita zadnji izvoz po materijalu
(ambalaža isključena, D-49; Winstoreovi „Drop" ostaci se broje zasebno kao informacija — restlovi Huba su tablica `restl`).
Lokacija ploče je njezin Winstore kod (regal nestinga nema adresu pretinca). Rezervacija (D-42/4) živi u `rezervacija`
(winstore_kod + kom) i ne dira Winstore; raspoloživo = fizičko − rezervirano + naručeno računa `skladiste.pogled`.
"""
from ..db import sada, dnevnik


def _mat_where(materijal_id, ident):
    w, a = "", []
    if materijal_id:
        w += " AND m.id = ?"; a.append(materijal_id)
    if ident:
        w += " AND m.pantheon_ident = ?"; a.append(ident)
    return w, a


def stanje(conn, materijal_id=None, ident=None, samo_sa_stanjem=True):
    """Pune ploče po materijalu iz zadnjeg Winstore izvoza:
    [{materijal_id, ident, naziv, debljina, winstore_kod, kom, interno, eksterno, drop_kom, izvoz, kodovi:[{kod, materijal_kod, L, W, kom, drop}]}]."""
    w, a = _mat_where(materijal_id, ident)
    sql = ("SELECT w.kod, w.materijal_kod, w.L, w.W, w.kom_ukupno, w.kom_interno, w.kom_eksterno, w.drop_ploca, w.izvoz, "
           "m.id AS mid, m.pantheon_ident, m.naziv_pantheon, m.debljina, m.winstore_kod FROM winstore_ploca w JOIN materijal m ON m.id = w.materijal_id "
           "WHERE w.ambalaza = 0%s ORDER BY m.pantheon_ident, w.drop_ploca, w.kod" % w)
    out = {}
    for r in conn.execute(sql, a):
        o = out.setdefault(r["mid"], dict(materijal_id=r["mid"], ident=r["pantheon_ident"], naziv=r["naziv_pantheon"], debljina=r["debljina"],
                                          winstore_kod=r["winstore_kod"] or r["materijal_kod"], kom=0, interno=0, eksterno=0, drop_kom=0,
                                          izvoz=r["izvoz"], kodovi=[]))
        if r["drop_ploca"]:
            o["drop_kom"] += r["kom_ukupno"]
        else:
            o["kom"] += r["kom_ukupno"]; o["interno"] += r["kom_interno"]; o["eksterno"] += r["kom_eksterno"]
        o["kodovi"].append(dict(kod=r["kod"], materijal_kod=r["materijal_kod"], L=r["L"], W=r["W"], kom=r["kom_ukupno"], drop=bool(r["drop_ploca"])))
    lst = list(out.values())
    if samo_sa_stanjem:
        lst = [o for o in lst if o["kom"] or o["drop_kom"]]
    return lst


def kom(conn, materijal_id):
    """Fizičko stanje punih ploča materijala (bez Drop i ambalaže) — 0 kad ga Winstore nema."""
    r = conn.execute("SELECT COALESCE(SUM(kom_ukupno), 0) FROM winstore_ploca WHERE materijal_id = ? AND ambalaza = 0 AND drop_ploca = 0", (materijal_id,)).fetchone()
    return int(r[0] or 0)


def lokacija(conn, materijal_id):
    """Gdje operater nalazi ploču: Winstore kod materijala (regal nestinga) ili None."""
    r = conn.execute("SELECT winstore_kod FROM materijal WHERE id = ?", (materijal_id,)).fetchone()
    if r and r["winstore_kod"]:
        return r["winstore_kod"]
    r = conn.execute("SELECT materijal_kod FROM winstore_ploca WHERE materijal_id = ? AND ambalaza = 0 LIMIT 1", (materijal_id,)).fetchone()
    return r["materijal_kod"] if r else None


AKTIVNE = ("rezervirano", "izdano")


def rezervirano(conn, materijal_id, bez_nm=None):
    """Σ rezerviranih punih ploča materijala (status rezervirano / izdano); bez_nm = ne računaj rezervaciju tog materijala naloga."""
    sql = ("SELECT COALESCE(SUM(r.kom), 0) FROM rezervacija r JOIN nalog_materijal nm ON nm.id = r.nalog_materijal_id "
           "WHERE nm.materijal_id = ? AND r.restl_id IS NULL AND r.status IN ('rezervirano', 'izdano')")
    a = [materijal_id]
    if bez_nm:
        sql += " AND nm.id <> ?"; a.append(bez_nm)
    return float(conn.execute(sql, a).fetchone()[0] or 0)


def rezerviraj(conn, nm_id, kom_, tko, winstore_kod=None, commit=True):
    """Rezerviraj punih ploča za materijal naloga (zamjenjuje prijašnju aktivnu rezervaciju ploča tog materijala naloga). Vraća id."""
    from ..nalozi.nalozi import korisnik_id
    if not winstore_kod:
        m = conn.execute("SELECT materijal_id FROM nalog_materijal WHERE id = ?", (nm_id,)).fetchone()
        winstore_kod = lokacija(conn, m["materijal_id"]) if m and m["materijal_id"] else None
    conn.execute("UPDATE rezervacija SET status = 'oslobodjeno' WHERE nalog_materijal_id = ? AND restl_id IS NULL AND status = 'rezervirano'", (nm_id,))
    cur = conn.execute("INSERT INTO rezervacija (nalog_materijal_id, winstore_kod, kom, status, datum, korisnik_id) VALUES (?, ?, ?, 'rezervirano', ?, ?)",
                       (nm_id, winstore_kod, float(kom_), sada(), korisnik_id(conn, tko)))
    dnevnik(conn, tko, "rezervacija", cur.lastrowid, "rezerviraj", "nm %d: %g ploča %s" % (nm_id, kom_, winstore_kod or ""))
    if commit:
        conn.commit()
    return cur.lastrowid


def oslobodi(conn, nm_id, tko, commit=True):
    cur = conn.execute("UPDATE rezervacija SET status = 'oslobodjeno' WHERE nalog_materijal_id = ? AND restl_id IS NULL AND status = 'rezervirano'", (nm_id,))
    if cur.rowcount:
        dnevnik(conn, tko, "rezervacija", None, "oslobodi", "nm %d: %d rezervacija ploča" % (nm_id, cur.rowcount))
    if commit:
        conn.commit()
    return cur.rowcount
