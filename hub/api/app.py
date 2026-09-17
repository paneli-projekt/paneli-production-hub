# -*- coding: utf-8 -*-
"""HTTP API Huba (FastAPI): korak 1 šifrarnik materijala i traka (ovdje), korak 2 kupci / nalozi / elementi (hub/api/nalozi_api.py).

    set HUB_DB=C:\\hub\\hub.db
    py -m uvicorn hub.api.app:app --host 0.0.0.0 --port 8766
    → http://192.168.5.201:8766/docs  (automatska dokumentacija i isprobavanje)

Krajnje točke:
    GET  /api/zdravlje                          stanje baze (broj materijala, traka, aliasa, zadnji uvozi)
    GET  /api/sifrarnik/materijali?q=&vrsta=    pretraga materijala (naziv, kratki naziv, ident, alias, Winstore kod)
    GET  /api/sifrarnik/materijali/{ident}      jedan materijal + aliasi + zadane trake + Winstore stanje
    GET  /api/sifrarnik/trake?q=&klasa=         pretraga traka
    GET  /api/sifrarnik/prepoznaj?naziv=&debljina=&kod=&sirina=     tekst iz naloga → materijal (razina, kandidati)
    GET  /api/sifrarnik/prepoznaj-traku?oznaka=&materijal=          oznaka ruba → traka + usluga kantiranja (D-20)
    POST /api/sifrarnik/alias        {alias, ident, tko, izvor}                      potvrda: tekst → materijal (D-32)
    POST /api/sifrarnik/alias-traka  {oznaka, traka, materijal?, klasa?, tko, izvor} potvrda: oznaka → traka (+ zadana traka materijala)
    + krajnje točke koraka 2 (kupci, nalozi, materijali naloga, elementi, statusi, uvoz datoteka) — vidi nalozi_api.py
    + prijava korisnika (POST /api/prijava, /api/odjava, GET /api/ja, /api/korisnici) — vidi korisnici_api.py (D-88)
Jedna dijeljena SQLite veza uz bravu (keš prepoznavanja živi uz vezu); Hub nikad ne piše u Pantheon (D-02).
"""
import os
import threading
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .. import db
from ..sifrarnici import prepoznaj as P
from ..sifrarnici.nazivi import norm

VERZIJA = "0.2 (šifrarnik + nalozi)"
app = FastAPI(title="Paneli Production Hub", version=VERZIJA, description="API Huba — šifrarnik materijala i traka, kupci, nalozi i elementi")
_brava = threading.Lock()
_veza = None


def veza():
    global _veza
    if _veza is None:
        import sqlite3
        _veza = sqlite3.connect(db.putanja_baze(), check_same_thread=False)
        _veza.row_factory = sqlite3.Row
        _veza.execute("PRAGMA foreign_keys = ON")
        db.init(_veza)
    return _veza


def _red(r):
    return dict(r) if r is not None else None


from . import nalozi_api                      # korak 2: kupci, nalozi, elementi
nalozi_api._ctx.update(veza=veza, brava=_brava)
app.include_router(nalozi_api.router)
from . import skladiste_api                   # Warehouse (D-64): skladište i nabava
skladiste_api._ctx.update(veza=veza, brava=_brava)
app.include_router(skladiste_api.router)
from . import korisnici_api                   # prijava s lozinkom, sesije, potpis (D-88)
korisnici_api._ctx.update(veza=veza, brava=_brava)
app.include_router(korisnici_api.router)
app.middleware("http")(korisnici_api.provjera_prijave)

# ---------------------------------------------------------------- web ekrani (hub/web: index.html + app.js + ekrani.js, bez builda)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
_WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
app.mount("/static", StaticFiles(directory=_WEB), name="static")


@app.get("/", include_in_schema=False)
def web_index():
    return FileResponse(os.path.join(_WEB, "index.html"))


# ---------------------------------------------------------------- zdravlje
@app.get("/api/zdravlje")
def zdravlje():
    with _brava:
        c = veza()
        n = lambda t: c.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
        zadnji = c.execute("SELECT entitet, kada, detalji FROM dnevnik WHERE sto = 'uvoz' ORDER BY id DESC LIMIT 5").fetchall()
        return dict(ok=True, verzija=VERZIJA, baza=db.putanja_baze(), shema=c.execute("SELECT MAX(verzija) FROM shema_verzija").fetchone()[0],
                    materijala=n("materijal"), traka=n("traka"), aliasa=n("materijal_alias"), aliasa_traka=n("traka_alias"), kupaca=n("kupac"), naloga=n("nalog"),
                    zadanih_traka=n("materijal_traka"), winstore_ploca=n("winstore_ploca"), winstore_izvoz=db.postavka(c, "winstore_izvoz"),
                    zadnji_uvozi=[_red(r) for r in zadnji])


# ---------------------------------------------------------------- materijali
_MAT_SQL = ("SELECT m.id, m.pantheon_ident AS ident, m.naziv_pantheon AS naziv, m.naziv_kratki, m.vrsta, m.obitelj_rp, m.debljina, m.dekor, m.dekor_kod, "
            "m.winstore_kod, m.ploca_L, m.ploca_W, m.god, m.sirina_rp, m.samo_cijela, m.aktivan, p.cijena_prodajna, p.cijena_neto, p.jm "
            "FROM materijal m LEFT JOIN pantheon_ident p ON p.ident = m.pantheon_ident ")


@app.get("/api/sifrarnik/materijali")
def materijali(q: str = "", vrsta: Optional[str] = None, aktivni: int = 1, limit: int = Query(50, le=500)):
    """Pretraga: svaka riječ upita mora biti u nazivu / kratkom nazivu / identu / Winstore kodu, ili je upit točan alias."""
    with _brava:
        c = veza()
        out = []
        n = norm(q)
        if n:
            a = c.execute("SELECT materijal_id FROM materijal_alias WHERE alias_norm = ?", (n,)).fetchone()
            if a:
                out.append(dict(_red(c.execute(_MAT_SQL + "WHERE m.id = ?", (a[0],)).fetchone()), pogodak="alias"))
        uvjeti, par = [], []
        for w in n.split():
            uvjeti.append("m.trazi LIKE ?")           # trazi = naziv u oba pisanja + ident + kratki naziv + Winstore kod (bez dijakritika)
            par.append("%" + w + "%")
        if vrsta:
            uvjeti.append("m.vrsta = ?")
            par.append(vrsta.upper())
        if aktivni:
            uvjeti.append("m.aktivan = 1")
        sql = _MAT_SQL + ("WHERE " + " AND ".join(uvjeti) if uvjeti else "") + " ORDER BY m.vrsta, m.naziv_pantheon LIMIT ?"
        for r in c.execute(sql, par + [limit]):
            if not any(o["id"] == r["id"] for o in out):
                out.append(dict(_red(r), pogodak="naziv"))
        return dict(upit=q, broj=len(out), materijali=out)


@app.get("/api/sifrarnik/materijali/{ident}")
def materijal(ident: str):
    with _brava:
        c = veza()
        m = c.execute(_MAT_SQL + "WHERE m.pantheon_ident = ?", (ident.upper(),)).fetchone()
        if not m:
            raise HTTPException(404, "nema materijala %s" % ident)
        aliasi = [_red(r) for r in c.execute("SELECT alias, izvor, potvrdio, kada FROM materijal_alias WHERE materijal_id = ? ORDER BY alias", (m["id"],))]
        trake = [_red(r) for r in c.execute("SELECT mt.klasa, t.pantheon_ident AS traka, t.naziv, mt.izvor, mt.potvrdio FROM materijal_traka mt "
                                            "JOIN traka t ON t.id = mt.traka_id WHERE mt.materijal_id = ? ORDER BY mt.klasa", (m["id"],))]
        winstore = [_red(r) for r in c.execute("SELECT materijal_kod, L, W, debljina, god, kom_ukupno, drop_ploca, izvoz FROM winstore_ploca "
                                               "WHERE materijal_id = ? ORDER BY drop_ploca, L DESC", (m["id"],))]
        return dict(_red(m), aliasi=aliasi, zadane_trake=trake, winstore=winstore)


# ---------------------------------------------------------------- trake
@app.get("/api/sifrarnik/trake")
def trake(q: str = "", klasa: Optional[str] = None, aktivni: int = 1, limit: int = Query(50, le=500)):
    with _brava:
        c = veza()
        uvjeti, par = [], []
        for w in norm(q).split():
            uvjeti.append("t.trazi LIKE ?")
            par.append("%" + w + "%")
        if klasa:
            uvjeti.append("t.klasa = ?")
            par.append(klasa.replace(".", ","))
        if aktivni:
            uvjeti.append("t.aktivan = 1")
        sql = ("SELECT t.id, t.pantheon_ident AS ident, t.naziv, t.vrsta, t.debljina, t.sirina, t.klasa, t.dekor, t.kod, t.dobavljac, t.regal_traka_ident, t.aktivan, "
               "p.cijena_prodajna, p.cijena_neto FROM traka t LEFT JOIN pantheon_ident p ON p.ident = t.pantheon_ident "
               + ("WHERE " + " AND ".join(uvjeti) if uvjeti else "") + " ORDER BY t.klasa, t.naziv LIMIT ?")
        out = [dict(_red(r), usluga=P.usluga_kantiranja(r["klasa"])) for r in c.execute(sql, par + [limit])]
        return dict(upit=q, broj=len(out), trake=out)


# ---------------------------------------------------------------- prepoznavanje
@app.get("/api/sifrarnik/prepoznaj")
def prepoznaj(naziv: str, debljina: Optional[float] = None, kod: Optional[str] = None, sirina: Optional[float] = None):
    """Tekst kako piše u nalogu / CPW / CSV → materijal. razina: alias | winstore | naziv (sigurno) | za_potvrdu | nema."""
    with _brava:
        return P.prepoznaj_materijal(veza(), naziv, debljina=debljina, winstore_kod=kod, sirina_ploce=sirina).kao_dict()


@app.get("/api/sifrarnik/prepoznaj-traku")
def prepoznaj_traku(oznaka: str, materijal: Optional[str] = None):
    """Oznaka ruba ('ABS-ISTI', 'MEL-ISTI', '1/22 JELA TAVERNA') + ident materijala → traka i usluga kantiranja."""
    with _brava:
        c = veza()
        mid = None
        if materijal:
            m = c.execute("SELECT id FROM materijal WHERE pantheon_ident = ?", (materijal.upper(),)).fetchone()
            if not m:
                raise HTTPException(404, "nema materijala %s" % materijal)
            mid = m[0]
        r = P.prepoznaj_traku(c, oznaka, materijal_id=mid)
        return dict(r.kao_dict(), usluga=P.usluga_kantiranja(r.klasa))


# ---------------------------------------------------------------- potvrde (D-32: potvrđeno jednom → idući put bez pitanja)
class Alias(BaseModel):
    alias: str
    ident: str
    tko: str = "web"
    izvor: str = "rucno"


class AliasTrake(BaseModel):
    oznaka: str
    traka: str
    materijal: Optional[str] = None
    klasa: Optional[str] = None
    tko: str = "web"
    izvor: str = "rucno"


@app.post("/api/sifrarnik/alias")
def potvrdi_alias(a: Alias):
    with _brava:
        c = veza()
        m = c.execute("SELECT id, naziv_pantheon FROM materijal WHERE pantheon_ident = ?", (a.ident.upper(),)).fetchone()
        if not m:
            raise HTTPException(404, "nema materijala %s" % a.ident)
        if not a.alias.strip():
            raise HTTPException(400, "prazan alias")
        P.potvrdi_materijal(c, a.alias, m[0], a.tko, a.izvor)
        db.dnevnik(c, a.tko, "materijal_alias", m[0], "potvrda", "%s → %s" % (a.alias, a.ident))
        c.commit()
        return dict(ok=True, alias=a.alias, ident=a.ident.upper(), naziv=m[1])


@app.post("/api/sifrarnik/alias-traka")
def potvrdi_alias_trake(a: AliasTrake):
    with _brava:
        c = veza()
        t = c.execute("SELECT id, naziv, klasa FROM traka WHERE pantheon_ident = ?", (a.traka.upper(),)).fetchone()
        if not t:
            raise HTTPException(404, "nema trake %s" % a.traka)
        mid = None
        if a.materijal:
            m = c.execute("SELECT id FROM materijal WHERE pantheon_ident = ?", (a.materijal.upper(),)).fetchone()
            if not m:
                raise HTTPException(404, "nema materijala %s" % a.materijal)
            mid = m[0]
        P.potvrdi_traku(c, a.oznaka, t[0], a.tko, materijal_id=mid, izvor=a.izvor, klasa=a.klasa)
        db.dnevnik(c, a.tko, "traka_alias", t[0], "potvrda", "%s → %s (%s)" % (a.oznaka, a.traka, a.materijal or "opće"))
        c.commit()
        return dict(ok=True, oznaka=a.oznaka, traka=a.traka.upper(), naziv=t[1], klasa=a.klasa or t[2], materijal=a.materijal)
