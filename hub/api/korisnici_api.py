# -*- coding: utf-8 -*-
"""Prijava korisnika i sesije (D-88).

    POST /api/prijava   {oznaka, lozinka}        kolačić hub_sesija; vraća korisnika + treba_lozinka (prva prijava bez lozinke)
    POST /api/odjava
    GET  /api/ja                                 prijavljeni korisnik, prijava_obavezna, popis oznaka (za ekran prijave)
    POST /api/ja/lozinka {nova, stara?}          vlastita lozinka
    GET  /api/korisnici                          (admin) popis; POST {oznaka, ime, uloga, email, telefon, funkcija, potpis, aktivan, lozinka?}
    GET  /api/korisnici/{oznaka}/potpis          tekst potpisa za mail
Middleware: kad je prijava obavezna, svaki /api/* osim /api/prijava, /api/ja i /api/zdravlje traži valjan kolačić (401 → ekran prijave).
`tko` iz tijela zahtjeva tada MORA biti prijavljeni korisnik (web to radi sam) — dnevnik ne može nositi tuđe ime."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from .. import korisnici as KO

router = APIRouter()
_ctx = {}
KOLACIC = "hub_sesija"
SLOBODNO = ("/api/prijava", "/api/odjava", "/api/ja", "/api/zdravlje")


def _c():
    return _ctx["veza"]()


class PrijavaP(BaseModel):
    oznaka: str
    lozinka: str = ""


class LozinkaP(BaseModel):
    nova: str
    stara: Optional[str] = None
    oznaka: Optional[str] = None            # admin mijenja drugome


class KorisnikP(BaseModel):
    oznaka: str
    ime: Optional[str] = None
    uloga: Optional[str] = None
    email: Optional[str] = None
    telefon: Optional[str] = None
    funkcija: Optional[str] = None
    potpis: Optional[str] = None
    aktivan: Optional[int] = None
    lozinka: Optional[str] = None


def prijavljeni(request: Request):
    with _ctx["brava"]:
        return KO.iz_tokena(_c(), request.cookies.get(KOLACIC))


def _admin(request):
    k = prijavljeni(request)
    with _ctx["brava"]:
        obavezna = KO.prijava_obavezna(_c())
    if not obavezna:
        return k or dict(oznaka="WEB", uloga="admin")   # prije prve lozinke: svatko smije postaviti korisnike (bootstrap)
    if not k or k["uloga"] != "admin":
        raise HTTPException(403, "samo administrator")
    return k


@router.post("/api/prijava")
def prijava(p: PrijavaP, response: Response):
    with _ctx["brava"]:
        try:
            r = KO.prijava(_c(), p.oznaka, p.lozinka)
        except KO.KorisnikGreska as e:
            raise HTTPException(401, str(e))
    response.set_cookie(KOLACIC, r["token"], max_age=KO.SESIJA_DANA * 86400, httponly=True, samesite="lax")
    return dict(korisnik=r["korisnik"], treba_lozinka=r["treba_lozinka"])


@router.post("/api/odjava")
def odjava(request: Request, response: Response):
    with _ctx["brava"]:
        KO.odjava(_c(), request.cookies.get(KOLACIC))
    response.delete_cookie(KOLACIC)
    return dict(ok=True)


@router.get("/api/ja")
def ja(request: Request):
    k = prijavljeni(request)
    with _ctx["brava"]:
        c = _c()
        return dict(korisnik=k, prijava_obavezna=KO.prijava_obavezna(c), oznake=[dict(oznaka=x["oznaka"], ime=x["ime"]) for x in KO.popis(c) if x["aktivan"]],
                    potpis=KO.potpis(c, k["oznaka"]) if k else None)


@router.post("/api/ja/lozinka")
def moja_lozinka(p: LozinkaP, request: Request):
    k = prijavljeni(request)
    with _ctx["brava"]:
        c = _c()
        if p.oznaka and (not k or k["oznaka"] != p.oznaka.upper()):
            if KO.prijava_obavezna(c) and (not k or k["uloga"] != "admin"):
                raise HTTPException(403, "samo administrator mijenja tuđu lozinku")
            oznaka = p.oznaka
        else:
            if not k:
                raise HTTPException(401, "prijava")
            oznaka = k["oznaka"]
            if k["ima_lozinku"]:
                r = c.execute("SELECT lozinka_hash FROM korisnik WHERE oznaka = ?", (oznaka,)).fetchone()
                if not KO.lozinka_odgovara(p.stara or "", r["lozinka_hash"]):
                    raise HTTPException(400, "stara lozinka nije točna")
        try:
            return KO.postavi_lozinku(c, oznaka, p.nova, (k or {}).get("oznaka", "web"), zadrzi_token=request.cookies.get(KOLACIC) if (k and k["oznaka"] == oznaka) else None)
        except KO.KorisnikGreska as e:
            raise HTTPException(400, str(e))


@router.get("/api/korisnici")
def korisnici(request: Request):
    _admin(request)
    with _ctx["brava"]:
        return KO.popis(_c())


@router.post("/api/korisnici")
def korisnik_upisi(p: KorisnikP, request: Request):
    a = _admin(request)
    with _ctx["brava"]:
        c = _c()
        try:
            k = KO.upisi(c, p.oznaka, p.ime, p.uloga, p.email, p.telefon, p.funkcija, p.potpis, p.aktivan, a["oznaka"])
            if p.lozinka:
                KO.postavi_lozinku(c, p.oznaka, p.lozinka, a["oznaka"])
                k = KO.korisnik(c, p.oznaka)
        except KO.KorisnikGreska as e:
            raise HTTPException(400, str(e))
        return k


@router.get("/api/korisnici/{oznaka}/potpis")
def korisnik_potpis(oznaka: str):
    with _ctx["brava"]:
        return dict(oznaka=oznaka.upper(), potpis=KO.potpis(_c(), oznaka))


async def provjera_prijave(request: Request, call_next):
    """Middleware: kad je prijava obavezna, /api/* bez valjane sesije → 401."""
    put = request.url.path
    if put.startswith("/api/") and put not in SLOBODNO:
        with _ctx["brava"]:
            c = _c()
            if KO.prijava_obavezna(c):
                k = KO.iz_tokena(c, request.cookies.get(KOLACIC))
                if not k:
                    from fastapi.responses import JSONResponse
                    return JSONResponse({"detail": "prijava"}, status_code=401)
                request.state.korisnik = k
    return await call_next(request)
