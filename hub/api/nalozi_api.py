# -*- coding: utf-8 -*-
"""API korak 2: kupci, nalozi, materijali naloga, elementi, statusi, uvoz datoteka (mockup ekrani 1 i 2).

    GET  /api/kupci?q=&subjekt=                pretraga kupaca (naziv, mjesto, OIB, telefon); subjekt='Krajnji kupac' = interna baza osoba pod tim ključem
    GET  /api/kupci/kljucevi                   'Krajnji kupac' (broj osoba) + vlastiti subjekti — prvi izbor na ekranu
    GET  /api/kupci/slicni?ime=&telefon=&email= ponavljači: postojeći kupac s istim telefonom / e-mailom / imenom (D-48)
    POST /api/kupci                            {ime, mjesto, telefon, email, adresa, posta, napomena, vrsta, tko, svejedno} novi kupac otvoren u Hubu
                                               (fizička osoba → račun na 'Krajnji kupac'); bez svejedno=true vraća 409 ako postoji sličan
    GET  /api/kupci/{id}    PUT /api/kupci/{id}  {email, telefon, rabat_materijal, rabat_usluge, dani_placanja, napomena, vrsta, pantheon_subjekt_racun, tko}
    GET  /api/nalozi?status=&q=                popis naloga (ekran 1)
    POST /api/nalozi                           {kupac_id | kupac_kratki, projekt, vrsta, izvor, kerf, napomena, rok_kupca, tko}
    GET  /api/nalog/{id}                       cijeli nalog (ekran 2): materijali, elementi, zadane trake, događaji, za potvrdu
    PUT  /api/nalog/{id}                       zaglavlje naloga
    POST /api/nalog/{id}/status                {status, tko, razlog, datum, nacin, rok_obecan, prioritet}   (D-35, dijalog 3b)
    POST /api/nalog/{id}/materijali            {ident | naziv_ulaz, debljina_ulaz, winstore_kod_ulaz, god, traka_zadana, tko}
    PUT  /api/nalog/materijal/{nm}             {put, god, traka_zadana, ploca_L, ploca_W, napomena, rb, tko}
    DELETE /api/nalog/materijal/{nm}?tko=
    POST /api/nalog/materijal/{nm}/potvrdi     {ident, tko, zapamti}          čovjek bira materijal za tekst iz datoteke (D-32)
    POST /api/nalog/materijal/{nm}/potvrdi-traku {oznaka, traka, tko, zapamti}
    POST /api/nalog/materijal/{nm}/elementi    {L, W, kom, naziv, rubovi{L,O,D,G}, god, napomena, tko}
    PUT  /api/nalog/element/{id}    DELETE /api/nalog/element/{id}?tko=
    POST /api/nalog/{id}/uvoz?izvor=           multipart datoteka CPW ili PPNEST CSV → materijali + elementi kroz šifrarnik
    POST /api/nalog/{id}/ponovi-prepoznavanje  nakon potvrda
    GET  /api/nalog/{id}/elementi-export       element-zapis za exporte (korak 3)
    GET  /api/spajanje?prag=1&status=          prijedlozi spajanja malih naloga u jedan nesting posao (D-54)
    POST /api/nalog/{id}/izvoz/nesting         {mapa, stil, suho, tko} CSV + CIX za bNest po materijalu (korak 3, D-23/D-24)
"""
import os
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from .. import db
from ..nalozi import nalozi as N, kupci as K, uvoz_datoteka as U, spajanje as SP, export_nesting as EX

router = APIRouter()
_ctx = {}   # puni app.py: {"veza": callable, "brava": Lock}


def _c():
    return _ctx["veza"]()


def _brava():
    return _ctx["brava"]


def _greska(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except N.NalogGreska as e:
        raise HTTPException(400, str(e))


# ---------------------------------------------------------------- kupci
class KupacUredi(BaseModel):
    email: Optional[str] = None
    telefon: Optional[str] = None
    rabat_materijal: Optional[float] = None
    rabat_usluge: Optional[float] = None
    dani_placanja: Optional[int] = None
    napomena: Optional[str] = None
    vrsta: Optional[str] = None                      # krajnji | tvrtka | obrt (prijelaz, D-48)
    pantheon_subjekt_racun: Optional[str] = None     # kome u Pantheonu ide ponuda / račun
    naziv: Optional[str] = None                      # samo kupci otvoreni u Hubu
    adresa: Optional[str] = None
    posta: Optional[str] = None
    mjesto: Optional[str] = None
    oib: Optional[str] = None
    aktivan: Optional[int] = None
    tko: str = "web"


class KupacNovi(BaseModel):
    ime: str
    mjesto: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    adresa: Optional[str] = None
    posta: Optional[str] = None
    oib: Optional[str] = None
    napomena: Optional[str] = None
    vrsta: str = "krajnji"
    svejedno: bool = False                           # true = otvori i ako postoji sličan kupac
    tko: str = "web"


@router.get("/api/kupci")
def kupci(q: str = "", aktivni: int = 1, limit: int = 30, subjekt: Optional[str] = None, vrsta: Optional[str] = None):
    """subjekt='Krajnji kupac' → interna baza fizičkih osoba pod tim ključem (D-48); bez subjekta → svi kupci."""
    with _brava():
        return dict(upit=q, subjekt=subjekt, kupci=K.trazi_kupce(_c(), q, aktivni=bool(aktivni), limit=min(limit, 200), subjekt=subjekt, vrsta=vrsta))


@router.get("/api/kupci/kljucevi")
def kupci_kljucevi():
    """Ključevi za izbor kupca na ekranu: 'Krajnji kupac' (broj osoba pod njim) i vlastiti subjekti."""
    with _brava():
        return K.subjekti_za_pantheon(_c())


@router.get("/api/kupci/slicni")
def kupci_slicni(ime: Optional[str] = None, telefon: Optional[str] = None, email: Optional[str] = None):
    with _brava():
        return dict(slicni=[dict(k, razlog=r) for k, r in K.slicni_kupci(_c(), ime=ime, telefon=telefon, email=email)])


@router.post("/api/kupci")
def kupac_novi(p: KupacNovi):
    with _brava():
        slicni = K.slicni_kupci(_c(), ime=p.ime, telefon=p.telefon, email=p.email)
        if slicni and not p.svejedno:
            raise HTTPException(409, dict(poruka="postoji sličan kupac — izaberi postojećeg ili pošalji svejedno=true",
                                          slicni=[dict(id=k["id"], naziv=k["naziv"], mjesto=k["mjesto"], telefon=k["telefon"], email=k["email"], razlog=r) for k, r in slicni]))
        try:
            return K.novi_hub_kupac(_c(), p.tko, p.ime, mjesto=p.mjesto, telefon=p.telefon, email=p.email, adresa=p.adresa, posta=p.posta,
                                    oib=p.oib, napomena=p.napomena, vrsta=p.vrsta)
        except ValueError as e:
            raise HTTPException(400, str(e))


@router.get("/api/kupci/{kupac_id}")
def kupac(kupac_id: int):
    with _brava():
        k = K.kupac(_c(), kupac_id)
        if not k:
            raise HTTPException(404, "nema kupca %d" % kupac_id)
        k["nalozi"] = N.popis(_c(), kupac_id=kupac_id, limit=20)
        return k


@router.put("/api/kupci/{kupac_id}")
def kupac_uredi(kupac_id: int, p: KupacUredi):
    with _brava():
        if not K.kupac(_c(), kupac_id):
            raise HTTPException(404, "nema kupca %d" % kupac_id)
        polja = {k: v for k, v in p.model_dump().items() if k != "tko" and v is not None}
        try:
            return K.uredi_kupca(_c(), kupac_id, p.tko, **polja)
        except ValueError as e:
            raise HTTPException(400, str(e))


# ---------------------------------------------------------------- nalozi
class NalogNovi(BaseModel):
    kupac_id: Optional[int] = None
    kupac_kratki: Optional[str] = None
    projekt: str = ""
    vrsta: str = "usluga"
    izvor: str = "rucno"
    kerf: Optional[float] = None
    napomena: Optional[str] = None
    rok_kupca: Optional[str] = None
    corpus_projekt: Optional[str] = None
    tko: str = "web"


class NalogUredi(BaseModel):
    naziv: Optional[str] = None
    kupac_id: Optional[int] = None
    vrsta: Optional[str] = None
    kerf: Optional[float] = None
    rabat_materijal: Optional[float] = None
    rabat_usluge: Optional[float] = None
    rok_kupca: Optional[str] = None
    rok_obecan: Optional[str] = None
    prioritet: Optional[str] = None
    napomena: Optional[str] = None
    corpus_projekt: Optional[str] = None
    tko: str = "web"


class Status(BaseModel):
    status: str
    tko: str = "web"
    razlog: Optional[str] = None
    datum: Optional[str] = None          # potvrda kupca (dijalog 3b)
    nacin: Optional[str] = None          # mail | telefon | osobno
    rok_obecan: Optional[str] = None
    prioritet: Optional[str] = None
    veza: Optional[str] = None


@router.get("/api/nalozi")
def nalozi(status: Optional[str] = None, q: Optional[str] = None, limit: int = 200):
    with _brava():
        return dict(statusi=[dict(kod=s, naziv=N.STATUS_NAZIV[s]) for s in N.STATUSI], nalozi=N.popis(_c(), status=status, q=q, limit=min(limit, 1000)))


@router.post("/api/nalozi")
def nalog_novi(p: NalogNovi):
    with _brava():
        return _greska(N.novi_nalog, _c(), p.tko, kupac_id=p.kupac_id, kupac_kratki=p.kupac_kratki, projekt=p.projekt, vrsta=p.vrsta, izvor=p.izvor,
                       kerf=p.kerf, napomena=p.napomena, rok_kupca=p.rok_kupca, corpus_projekt=p.corpus_projekt)


@router.get("/api/nalog/{nalog_id}")
def nalog_pregled(nalog_id: int):
    with _brava():
        return _greska(N.pregled, _c(), nalog_id)


@router.put("/api/nalog/{nalog_id}")
def nalog_uredi(nalog_id: int, p: NalogUredi):
    with _brava():
        polja = {k: v for k, v in p.model_dump().items() if k != "tko" and v is not None}
        return _greska(N.uredi_nalog, _c(), nalog_id, p.tko, **polja)


@router.post("/api/nalog/{nalog_id}/status")
def nalog_status(nalog_id: int, p: Status):
    with _brava():
        return _greska(N.postavi_status, _c(), nalog_id, p.status, p.tko, razlog=p.razlog, veza=p.veza, datum=p.datum, nacin=p.nacin,
                       rok_obecan=p.rok_obecan, prioritet=p.prioritet)


@router.get("/api/nalog/{nalog_id}/dogadjaji")
def nalog_dogadjaji(nalog_id: int):
    with _brava():
        _greska(N.nalog, _c(), nalog_id)
        return N.dogadjaji(_c(), nalog_id)


@router.post("/api/nalog/{nalog_id}/ponovi-prepoznavanje")
def nalog_ponovi(nalog_id: int, tko: str = "web"):
    with _brava():
        _greska(N.nalog, _c(), nalog_id)
        return dict(za_potvrdu=N.ponovi_prepoznavanje(_c(), nalog_id, tko), stavke=N.za_potvrdu(_c(), nalog_id))


class IzvozNesting(BaseModel):
    mapa: str
    stil: str = "bsolid"
    suho: bool = False
    sve: bool = False
    tko: str = "web"


@router.post("/api/nalog/{nalog_id}/izvoz/nesting")
def nalog_izvoz_nesting(nalog_id: int, p: IzvozNesting):
    """CSV + CIX za bNest, po materijalu. `suho=true` samo izračuna paket i ne dira ni disk ni bazu."""
    with _ctx["brava"]:
        try:
            return EX.izvezi(_c(), nalog_id, p.mapa, p.tko, p.stil, samo_nesting=not p.sve, suho=p.suho)
        except EX.ExportGreska as e:
            raise HTTPException(400, str(e))



class IzvozPW(BaseModel):
    mapa: str
    zaglavlje_jednom: bool = False
    samo_pila: bool = False
    suho: bool = False
    tko: str = "web"


@router.post("/api/nalog/{nalog_id}/izvoz/pw")
def nalog_izvoz_pw(nalog_id: int, p: IzvozPW):
    """CPW za PanelWizard, po materijalu (paralelni rad, D-11). Zadano izvozi sve materijale naloga."""
    with _ctx["brava"]:
        try:
            return EW.izvezi(_c(), nalog_id, p.mapa, p.tko, header_once=p.zaglavlje_jednom, samo_pila=p.samo_pila, suho=p.suho)
        except EX.ExportGreska as e:
            raise HTTPException(400, str(e))


class IzvozPila(BaseModel):
    mapa: str
    suho: bool = False
    sve: bool = False
    tko: str = "web"


@router.post("/api/nalog/{nalog_id}/izvoz/pila")
def nalog_izvoz_pila(nalog_id: int, p: IzvozPila):
    """Optimizacija + CPO za pilu, po materijalu (D-19 izbor načina, D-21 kerf, D-22 broj programa).
    `suho=true` složi sheme i vrati brojke bez pisanja — to ekran pokazuje prije slanja na pilu."""
    with _ctx["brava"]:
        try:
            return EP.izvezi(_c(), nalog_id, p.mapa, p.tko, samo_pila=not p.sve, suho=p.suho)
        except EX.ExportGreska as e:
            raise HTTPException(400, str(e))

@router.get("/api/spajanje")
def spajanje_prijedlozi(prag: float = 1.0, status: Optional[str] = None):
    """Materijali koje traži više naloga koji čekaju rezanje — prijedlog da se izrežu zajedno na nestingu (D-54).
    Ništa ne mijenja; voditelj odlučuje. `status` = zarezom odvojeni statusi (zadano: potvrdjeno, skladiste, pila_nesting)."""
    statusi = tuple(x.strip() for x in status.split(",") if x.strip()) if status else SP.STATUSI_ZA_REZANJE
    with _ctx["brava"]:
        return SP.sazetak(_c(), statusi, prag)


@router.get("/api/nalog/{nalog_id}/elementi-export")
def nalog_export(nalog_id: int):
    with _brava():
        return _greska(N.elementi_za_export, _c(), nalog_id)


# ---------------------------------------------------------------- materijali naloga
class MaterijalNaloga(BaseModel):
    ident: Optional[str] = None
    naziv_ulaz: Optional[str] = None
    debljina_ulaz: Optional[float] = None
    winstore_kod_ulaz: Optional[str] = None
    god: Optional[int] = None
    traka_zadana: str = "ABS-ISTI"
    napomena: Optional[str] = None
    tko: str = "web"


class MaterijalUredi(BaseModel):
    put: Optional[str] = None
    put_prijedlog: Optional[str] = None
    god: Optional[int] = None
    traka_zadana: Optional[str] = None
    ploca_L: Optional[float] = None
    ploca_W: Optional[float] = None
    napomena: Optional[str] = None
    rb: Optional[int] = None
    tko: str = "web"


class PotvrdaMaterijala(BaseModel):
    ident: str
    tko: str = "web"
    zapamti: bool = True


class PotvrdaTrake(BaseModel):
    oznaka: str
    traka: str
    tko: str = "web"
    zapamti: bool = True


def _materijal_id(ident):
    r = _c().execute("SELECT id FROM materijal WHERE pantheon_ident = ?", (ident.upper(),)).fetchone()
    if not r:
        raise HTTPException(404, "nema materijala %s" % ident)
    return r[0]


@router.post("/api/nalog/{nalog_id}/materijali")
def materijal_dodaj(nalog_id: int, p: MaterijalNaloga):
    with _brava():
        mid = _materijal_id(p.ident) if p.ident else None
        nm, rez = _greska(N.dodaj_materijal, _c(), nalog_id, p.tko, materijal_id=mid, naziv_ulaz=p.naziv_ulaz, debljina_ulaz=p.debljina_ulaz,
                          winstore_kod_ulaz=p.winstore_kod_ulaz, god=p.god, traka_zadana=p.traka_zadana, napomena=p.napomena)
        return dict(nm, prepoznavanje=rez.kao_dict() if rez else None)


@router.put("/api/nalog/materijal/{nm_id}")
def materijal_uredi(nm_id: int, p: MaterijalUredi):
    with _brava():
        polja = {k: v for k, v in p.model_dump().items() if k != "tko" and v is not None}
        return _greska(N.uredi_materijal, _c(), nm_id, p.tko, **polja)


@router.delete("/api/nalog/materijal/{nm_id}")
def materijal_obrisi(nm_id: int, tko: str = "web"):
    with _brava():
        _greska(N.obrisi_materijal, _c(), nm_id, tko)
        return dict(ok=True)


@router.post("/api/nalog/materijal/{nm_id}/potvrdi")
def materijal_potvrdi(nm_id: int, p: PotvrdaMaterijala):
    with _brava():
        return _greska(N.potvrdi_materijal_naloga, _c(), nm_id, _materijal_id(p.ident), p.tko, zapamti=p.zapamti)


@router.post("/api/nalog/materijal/{nm_id}/potvrdi-traku")
def materijal_potvrdi_traku(nm_id: int, p: PotvrdaTrake):
    with _brava():
        t = _c().execute("SELECT id FROM traka WHERE pantheon_ident = ?", (p.traka.upper(),)).fetchone()
        if not t:
            raise HTTPException(404, "nema trake %s" % p.traka)
        _greska(N.potvrdi_traku_naloga, _c(), nm_id, p.oznaka, t[0], p.tko, zapamti=p.zapamti)
        nm = N.materijal_naloga(_c(), nm_id)
        return dict(ok=True, za_potvrdu=N.za_potvrdu(_c(), nm["nalog_id"]))


# ---------------------------------------------------------------- elementi
class ElementNovi(BaseModel):
    L: float
    W: float
    kom: int
    naziv: Optional[str] = None
    rubovi: Optional[dict] = None        # {"L": "ABS-ISTI", "O": "", "D": "MEL-ISTI", "G": "1/22 JELA TAVERNA"}
    god: Optional[str] = None            # H | V
    napomena: Optional[str] = None
    izvor: str = "rucno"
    tko: str = "web"


class ElementUredi(BaseModel):
    L: Optional[float] = None
    W: Optional[float] = None
    kom: Optional[int] = None
    naziv: Optional[str] = None
    rubovi: Optional[dict] = None
    god: Optional[str] = None
    napomena: Optional[str] = None
    obrada: Optional[str] = None
    rb: Optional[int] = None
    tko: str = "web"


@router.post("/api/nalog/materijal/{nm_id}/elementi")
def element_dodaj(nm_id: int, p: ElementNovi):
    with _brava():
        return _greska(N.dodaj_element, _c(), nm_id, p.tko, p.L, p.W, p.kom, naziv=p.naziv, rubovi=p.rubovi, god=p.god, napomena=p.napomena, izvor=p.izvor)


@router.put("/api/nalog/element/{eid}")
def element_uredi(eid: int, p: ElementUredi):
    with _brava():
        polja = {k: v for k, v in p.model_dump().items() if k != "tko" and v is not None}
        return _greska(N.uredi_element, _c(), eid, p.tko, **polja)


@router.delete("/api/nalog/element/{eid}")
def element_obrisi(eid: int, tko: str = "web"):
    with _brava():
        _greska(N.obrisi_element, _c(), eid, tko)
        return dict(ok=True)


# ---------------------------------------------------------------- uvoz datoteke
@router.post("/api/nalog/{nalog_id}/uvoz")
async def nalog_uvoz(nalog_id: int, datoteka: UploadFile = File(...), izvor: str = "kupac_ppw", tko: str = "web"):
    """CPW (kupac / PW / Corpus) ili PPNEST CSV. Datoteka se sprema u mapu ulaza uz bazu (postavka 'mapa_ulaz') i bilježi u dokument."""
    sadrzaj = await datoteka.read()
    with _brava():
        c = _c()
        n = _greska(N.nalog, c, nalog_id)
        mapa = db.postavka(c, "mapa_ulaz") or os.path.join(os.path.dirname(os.path.abspath(db.putanja_baze())), "ulaz")
        cilj = os.path.join(mapa, re.sub(r"[^A-Za-z0-9_.-]+", "_", n["naziv"]))
        os.makedirs(cilj, exist_ok=True)
        ime = re.sub(r"[^A-Za-z0-9_. ()-]+", "_", os.path.basename(datoteka.filename or "datoteka"))
        putanja = os.path.join(cilj, ime)
        with open(putanja, "wb") as f:
            f.write(sadrzaj)
        if ime.lower().endswith(".csv"):
            st = _greska(U.uvezi_ppnest_csv, c, nalog_id, putanja, tko)
        elif ime.lower().endswith(".cpw"):
            st = _greska(U.uvezi_cpw, c, nalog_id, putanja, tko, izvor)
        else:
            raise HTTPException(400, "podržane su datoteke .CPW i .CSV (PPNEST)")
        return dict(st, datoteka=ime, za_potvrdu=N.za_potvrdu(c, nalog_id), sazetak=N.pregled(c, nalog_id)["sazetak"])
