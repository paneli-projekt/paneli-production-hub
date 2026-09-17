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
    POST /api/nalog/{id}/uvoz?izvor=           multipart datoteka CPW, PNL (PanelWizard) ili PPNEST CSV → materijali + elementi kroz šifrarnik
    POST /api/nalog/{id}/ponovi-prepoznavanje  nakon potvrda
    POST /api/nalozi/uvoz-corpus               {mapa, kupac_id | kupac_kratki, projekt, suho, tko} cijeli Corpus paket → novi nalog vlastite proizvodnje (D-55)
    POST /api/rezultat/nesting                 {put | mapa, suho, tko} bNest .mno → stvarna potrošnja po materijalu naloga, razdioba spojenog posla (D-38)
    GET  /api/nalog/{id}/rezultati             naplaćeno (Hub, PW-metoda) vs potrošeno (bNest) po materijalu + sheme (PNG) za ekran
    GET  /api/slika?put=                       PNG sheme rezanja (samo putanje zabilježene u dokumentima naloga)
    GET  /api/nalog/{id}/obracun               stavke ponude iz obračuna (bez upisa) — ekran 3            POST …/obracun {pravila, tko} upiše radne stavke
    GET  /api/nalog/{id}/ponude                verzije ponude;  POST /api/nalog/{id}/ponude {pravila, tko, potvrdi_opt} nova verzija iz obračuna (D-40)
    PUT  /api/nalog/{id}/stavka {kljuc, kolicina?, cijena?, rabat?, ponisti?}   korekcija izračunate stavke (D-90)
    GET  /api/nalog/{id}/rucne  POST {pantheon_ident, kolicina, grupa, naziv?, jm?, cijena?, rabat?, napomena}  PUT /api/rucne/{id} {kolicina, cijena, rabat…}  DELETE /api/rucne/{id}   ručne stavke ponude (D-87)
    GET  /api/sifrarnik/identi?q=&klasif=      pretraga Pantheon identa (za ručne stavke)
    GET  /api/nalog/{id}/optimizacija          potvrđeno slaganje + prijedlozi po materijalu (D-75)
    POST /api/nalog/{id}/materijal/{nm}/optimizacija {nacin, dubina, tko}  novi prijedlog;  POST /api/optimizacija/{oid}/potvrdi {tko}
    POST /api/nalog/{id}/optimizacija/pripremi {nm, tko}   zadani prijedlog (realno za pilu) + Hub rezerva kad štedi m² (D-91)
    GET  /api/optimizacija/{oid}/sheme.png?h=&list=   sličica slaganja (sve ploče / jedna) za ekran;  GET …/pregled  listovi + elementi (JSON)
    GET  /api/postavke/optimizacija            skrivene postavke (kerf, kerf_pile, nadmjera_trake, obracun_rezanja…, D-77); POST {kljuc: vrijednost}
    GET  /api/nalog/{id}/ispis/krojni.pdf      krojni nacrt PDF iz potvrđenog slaganja (D-76); ?materijal=nm (jedan) ?oid= (prijedlog) ?mapa= ; POST … {materijal, mapa, tko} napravi i zabilježi
    GET  /api/ponuda/{vid}                     verzija sa stavkama;  POST /api/ponuda/{vid}/eslog {mapa, broj}  POST /api/ponuda/{vid}/poslana {na, mail_tekst}
    POST /api/ponuda/{vid}/potvrdi             {ponuda_pantheon, datum, nacin, rok_obecan, prioritet, mapa, tko} dijalog 3b → nalog potvrđen + eSlog
    POST /api/ponuda/{vid}/posalji             {na, tekst, cc, mapa, suho, tko} ponuda kupcu mailom s PDF-om (D-41); GET /api/mail/postavke
    POST /api/nalog/{id}/izdatnica             {mapa, tko} vlastita proizvodnja: korekcija po stvarnom stanju (.mno) → verzija izdatnica (D-56)
    GET  /api/nalog/{id}/elementi-export       element-zapis za exporte (korak 3)
    GET  /api/spajanje?prag=1&status=          prijedlozi spajanja malih naloga u jedan nesting posao (D-54)
    POST /api/spajanje/izvezi                  {nm_ids[], mapa, stil, suho, forsiraj, tko} korak B: jedan CSV+CIX paket iz više naloga (SPOJ_…)
    GET  /api/spajanje/poslovi                 spojeni poslovi s nalozima i je li se .mno vratio
    POST /api/nalog/{id}/izvoz/nesting         {mapa, stil, suho, tko} CSV + CIX za bNest po materijalu (korak 3, D-23/D-24)
    POST /api/nalog/{id}/izvoz/pw              {mapa, zaglavlje_jednom, samo_pila, suho, tko} CPW za PanelWizard (D-11)
    POST /api/nalog/{id}/izvoz/pila            {mapa, suho, sve, tko} optimizacija + CPO za pilu (D-19/D-21/D-22)
    GET  /api/nalog/{id}/grupe                 korak 6: majke (niz goda, mali komadi) i sklopovi lijepljenja s članovima;  POST … {tko} ponovno primijeni pravila
    POST /api/nalog/element/{eid}/niz          {fronte[{L, W, rubovi, naziv, napomena}], smjer, tko} kupčev veći komad ('skica N') → niz goda iz upisanih fronti (D-70)
    GET  /api/majka/{id}/skica.png             skica majke (rezovi, oznake) za ekran / operatera
"""
import os
import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from .. import db
from ..nalozi import nalozi as N, kupci as K, uvoz_datoteka as U, spajanje as SP, export_nesting as EX, export_pw as EW, export_pila as EP, uvoz_corpus as UC, rezultat_nesting as RN
from ..nalozi import obracun as OC, ponuda as PO, optimiziraj as OP, grupe as G

router = APIRouter()
_ctx = {}   # puni app.py: {"veza": callable, "brava": Lock}


def _c():
    return _ctx["veza"]()


def _brava():
    return _ctx["brava"]


def _rollback():
    """Neuspjeli zahtjev ne smije ostaviti otvorenu transakciju na dijeljenoj vezi — sljedeći tuđi commit bi je upisao."""
    try:
        c = _c()
        if c.in_transaction:
            c.rollback()
    except Exception:
        pass


def pdf_inline(put, media_type="application/pdf"):
    """PDF se otvara u pregledniku (inline), ne skida se automatski (Igor, 17. 9.); ime datoteke ostaje za „Spremi kao“."""
    from fastapi.responses import FileResponse
    from urllib.parse import quote
    ime = os.path.basename(put)
    return FileResponse(put, media_type=media_type, headers={"Content-Disposition": "inline; filename*=UTF-8''%s" % quote(ime)})


def _greska(fn, *a, **kw):
    """Pozovi funkciju modula; poslovna greška → 400, sve ostalo → 500, u oba slučaja s rollbackom."""
    try:
        return fn(*a, **kw)
    except (N.NalogGreska, EX.ExportGreska, SP.SpajanjeGreska, OC.ObracunGreska, PO.PonudaGreska, OP.OptimizacijaGreska, G.GrupeGreska, ValueError) as e:
        _rollback()
        raise HTTPException(400, str(e))
    except HTTPException:
        _rollback()
        raise
    except Exception:
        _rollback()
        raise


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
        return _greska(K.novi_hub_kupac, _c(), p.tko, p.ime, mjesto=p.mjesto, telefon=p.telefon, email=p.email, adresa=p.adresa, posta=p.posta,
                       oib=p.oib, napomena=p.napomena, vrsta=p.vrsta)


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
        return _greska(K.uredi_kupca, _c(), kupac_id, p.tko, **polja)


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
    napomena_ponude: Optional[str] = None
    zbroji_idente: Optional[int] = None
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
    forsiraj: bool = False                 # izvoz i iz statusa unos / ponuda (samo za probe)
    tko: str = "web"


@router.post("/api/nalog/{nalog_id}/izvoz/nesting")
def nalog_izvoz_nesting(nalog_id: int, p: IzvozNesting):
    """CSV + CIX za bNest, po materijalu. `suho=true` samo izračuna paket i ne dira ni disk ni bazu."""
    with _brava():
        return _greska(EX.izvezi, _c(), nalog_id, p.mapa, p.tko, p.stil, samo_nesting=not p.sve, suho=p.suho, forsiraj=p.forsiraj)



class IzvozPW(BaseModel):
    mapa: str
    zaglavlje_jednom: bool = False
    samo_pila: bool = False
    suho: bool = False
    tko: str = "web"


@router.post("/api/nalog/{nalog_id}/izvoz/pw")
def nalog_izvoz_pw(nalog_id: int, p: IzvozPW):
    """CPW za PanelWizard, po materijalu (paralelni rad, D-11). Zadano izvozi sve materijale naloga."""
    with _brava():
        return _greska(EW.izvezi, _c(), nalog_id, p.mapa, p.tko, header_once=p.zaglavlje_jednom, samo_pila=p.samo_pila, suho=p.suho)


class IzvozPila(BaseModel):
    mapa: str
    suho: bool = False
    sve: bool = False
    forsiraj: bool = False
    tko: str = "web"


@router.post("/api/nalog/{nalog_id}/izvoz/pila")
def nalog_izvoz_pila(nalog_id: int, p: IzvozPila):
    """Optimizacija + CPO za pilu, po materijalu (D-19 izbor načina, D-21 kerf, D-22 broj programa).
    `suho=true` složi sheme i vrati brojke bez pisanja — to ekran pokazuje prije slanja na pilu."""
    with _brava():
        return _greska(EP.izvezi, _c(), nalog_id, p.mapa, p.tko, samo_pila=not p.sve, suho=p.suho, forsiraj=p.forsiraj)

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
    obrub: Optional[float] = None          # mm; poslano null = natrag na zadano (10, radne ploče 0)
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
        if "obrub" in p.model_fields_set:
            polja["obrub"] = p.obrub                       # i null (zadano)
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
    niz: Optional[str] = None            # korak 6: oznaka niza goda 'A1' / 'E1H' / 'C1-2' ('' = makni)
    ljepljenje: Optional[str] = None     # korak 6: sloj sklopa 'A1' / 'A2' ('' = makni)
    tko: str = "web"


class GrupeP(BaseModel):
    tko: str = "web"


class NizIzMajke(BaseModel):
    fronte: List[dict]                   # [{L, W, rubovi{L,O,D,G}, naziv, napomena}] redom uz god
    smjer: str = "V"                     # V okomito (jedna iznad druge) | H vodoravno
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


# ---------------------------------------------------------------- korak 6: majke i sklopovi (D-70 / D-79 / D-80)
@router.get("/api/nalog/{nalog_id}/grupe")
def nalog_grupe(nalog_id: int):
    with _brava():
        _greska(N.nalog, _c(), nalog_id)
        return dict(majke=G.pregled(_c(), nalog_id))


@router.post("/api/nalog/{nalog_id}/grupe")
def nalog_grupe_primijeni(nalog_id: int, p: GrupeP):
    with _brava():
        return _greska(G.primijeni, _c(), nalog_id, p.tko)


@router.post("/api/nalog/element/{eid}/niz")
def element_niz_iz_majke(eid: int, p: NizIzMajke):
    with _brava():
        return _greska(G.niz_iz_kupceve_majke, _c(), eid, p.fronte, p.tko, p.smjer)


@router.get("/api/majka/{majka_id}/skica.png")
def majka_skica(majka_id: int):
    import tempfile
    from fastapi.responses import FileResponse
    with _brava():
        m = _greska(G.majka, _c(), majka_id)
        put = os.path.join(tempfile.gettempdir(), "hub_majka_%d.png" % majka_id)
        if not G.skica_png(_c(), majka_id, put):
            raise HTTPException(500, "matplotlib nije instaliran — skica se ne može nacrtati")
    return FileResponse(put, media_type="image/png")


# ---------------------------------------------------------------- uvoz Corpus paketa (D-29, D-55)
class UvozCorpus(BaseModel):
    mapa: str                              # mapa izvoza iz Corpusa na disku poslužitelja / mrežnom disku (…\NESTING\<PROJEKT>)
    kupac_id: Optional[int] = None
    kupac_kratki: Optional[str] = None
    projekt: Optional[str] = None
    suho: bool = False                     # samo provjeri paket (greške, upozorenja, brojke), ne otvaraj nalog
    tko: str = "web"


@router.post("/api/nalozi/uvoz-corpus")
def nalozi_uvoz_corpus(p: UvozCorpus):
    """Corpusov paket (CPW po materijalu + CSV + CIX, i podmapa HORIZONTALNO_BUSENJE) → novi nalog `vlastita_proizvodnja`.
    Paket s greškom (element bez CIX-a, krive mjere u CIX-u, zauzeto ime) vraća 400 i ne otvara nalog."""
    with _brava():
        c = _c()
        nid, izv = _greska(UC.uvezi_paket, c, p.mapa, p.tko, kupac_id=p.kupac_id, kupac_kratki=p.kupac_kratki, projekt=p.projekt, suho=p.suho)
        if nid:
            izv["za_potvrdu"] = N.za_potvrdu(c, nid)
            izv["sazetak"] = N.pregled(c, nid)["sazetak"]
        return izv


class SpajanjeIzvoz(BaseModel):
    nm_ids: List[int]                      # nalog_materijal.id iz prijedloga (stavke[].nm_id)
    mapa: str
    stil: str = "bsolid"
    suho: bool = False
    forsiraj: bool = False
    tko: str = "web"


@router.post("/api/spajanje/izvezi")
def spajanje_izvezi(p: SpajanjeIzvoz):
    """Voditelj je odabrao naloge (isti materijal) → jedan nesting posao `SPOJ_<MATERIJAL>_<zig>` (D-54/B). Obračun naloga se ne mijenja."""
    with _brava():
        return _greska(SP.izvezi_spojeno, _c(), p.nm_ids, p.mapa, p.tko, p.stil, p.suho, p.forsiraj)


@router.get("/api/spajanje/poslovi")
def spajanje_poslovi(limit: int = 100):
    with _ctx["brava"]:
        return SP.poslovi(_c(), limit)


# ---------------------------------------------------------------- obračun i ponuda (korak 4; D-18, D-20, D-40, D-56)
class ObracunP(BaseModel):
    pravila: bool = True                   # pravilo načete ploče (1/3–2/3)
    tko: str = "web"


@router.get("/api/nalog/{nalog_id}/obracun")
def nalog_obracun(nalog_id: int, pravila: bool = True):
    """Stavke ponude izračunate sada (ne upisuje) — ekran 3 obračun."""
    with _ctx["brava"]:
        return _greska(OC.izracunaj, _c(), nalog_id, pravila)


@router.post("/api/nalog/{nalog_id}/obracun")
def nalog_obracun_upisi(nalog_id: int, p: ObracunP):
    with _brava():
        return _greska(OC.upisi, _c(), nalog_id, p.tko, p.pravila)


class RucnaP(BaseModel):
    pantheon_ident: str
    kolicina: float
    grupa: str = "usluga"
    naziv: Optional[str] = None
    jm: Optional[str] = None
    cijena: Optional[float] = None
    rabat: Optional[float] = None
    napomena: Optional[str] = None
    tko: str = "web"


@router.get("/api/nalog/{nalog_id}/rucne")
def nalog_rucne(nalog_id: int):
    """Ručne stavke ponude (D-87) — artikli koje ured sam doda (okov, usluga, bilo koji ident)."""
    with _ctx["brava"]:
        c = _c()
        _greska(N.nalog, c, nalog_id)
        return OC.rucne(c, nalog_id)


@router.post("/api/nalog/{nalog_id}/rucne")
def nalog_rucna_dodaj(nalog_id: int, p: RucnaP):
    with _brava():
        return _greska(OC.dodaj_rucnu, _c(), nalog_id, p.pantheon_ident, p.kolicina, p.grupa, p.naziv, p.jm, p.cijena, p.rabat, p.napomena, p.tko)


class RucnaIzmjenaP(BaseModel):
    kolicina: Optional[float] = None
    cijena: Optional[float] = None
    rabat: Optional[float] = None
    naziv: Optional[str] = None
    jm: Optional[str] = None
    napomena: Optional[str] = None
    ponisti: Optional[List[str]] = None       # polja koja se vraćaju na zadano (cijena / rabat)
    tko: str = "web"


@router.put("/api/rucne/{rucna_id}")
def rucna_promijeni(rucna_id: int, p: RucnaIzmjenaP):
    """Korekcija ručne stavke na ekranu ponude (kao redak u Pantheonu): količina, cijena, rabat, naziv."""
    polja = {k: v for k, v in p.dict().items() if k not in ("tko", "ponisti") and v is not None}
    for k in (p.ponisti or []):
        polja[k] = None
    with _brava():
        return _greska(OC.promijeni_rucnu, _c(), rucna_id, p.tko, **polja)


class KorekcijaP(BaseModel):
    kljuc: str
    kolicina: Optional[float] = None
    cijena: Optional[float] = None
    rabat: Optional[float] = None
    ponisti: Optional[List[str]] = None       # polja koja se vraćaju na izračunato
    tko: str = "web"


@router.put("/api/nalog/{nalog_id}/stavka")
def nalog_stavka_korekcija(nalog_id: int, p: KorekcijaP):
    """Korekcija izračunate stavke ponude (D-90): količina / cijena / rabat; `ponisti` vraća polje na izračunato; sva tri prazna = korekcija se briše."""
    polja = {a: getattr(p, a) for a in ("kolicina", "cijena", "rabat") if getattr(p, a) is not None}
    for a in (p.ponisti or []):
        polja[a] = ""
    with _brava():
        c = _c()
        if not polja:
            return _greska(OC.korigiraj_stavku, c, nalog_id, p.kljuc, p.tko)
        r = _greska(OC.korigiraj_stavku, c, nalog_id, p.kljuc, p.tko, **polja)
        if r.get("kolicina") is None and r.get("cijena") is None and r.get("rabat") is None:
            _greska(OC.korigiraj_stavku, c, nalog_id, p.kljuc, p.tko)
        return r


@router.delete("/api/rucne/{rucna_id}")
def rucna_obrisi(rucna_id: int, tko: str = "web"):
    with _brava():
        return _greska(OC.obrisi_rucnu, _c(), rucna_id, tko)


@router.get("/api/sifrarnik/identi")
def sifrarnik_identi(q: str = "", klasif: Optional[str] = None, limit: int = 30):
    """Pretraga Pantheon identa (ident / naziv / klasif) za ručne stavke ponude."""
    from ..sifrarnici.nazivi import norm
    q = (q or "").strip()
    rijeci = norm(q).split()                       # bez dijakritike (ŠARKA = sarka), sve riječi moraju biti u nazivu ili identu
    with _ctx["brava"]:
        c = _c()
        sql = "SELECT ident, naziv, klasif, jm, cijena_neto, aktivan FROM pantheon_ident" + (" WHERE klasif = ?" if klasif else "")
        out = []
        for r in c.execute(sql, ([klasif.upper()] if klasif else [])):
            polje = norm(r["naziv"]) + " " + r["ident"].upper()
            if all(w in polje for w in rijeci):
                out.append(dict(r))
    out.sort(key=lambda r: (not r["aktivan"], not r["ident"].upper().startswith(q.upper()), r["ident"]))
    return out[:max(1, min(int(limit), 200))]


@router.get("/api/nalog/{nalog_id}/ponude")
def nalog_ponude(nalog_id: int):
    with _ctx["brava"]:
        c = _c()
        _greska(N.nalog, c, nalog_id)
        return PO.verzije(c, nalog_id)


class PonudaNovaP(ObracunP):
    potvrdi_opt: Optional[bool] = None     # True: sam potvrdi Hubov prijedlog slaganja (probe, D-75)


@router.post("/api/nalog/{nalog_id}/ponude")
def nalog_nova_ponuda(nalog_id: int, p: PonudaNovaP):
    """Nova verzija ponude iz obračuna; nalog iz 'unos' prelazi u 'ponuda'. Traži potvrđeno slaganje svakog materijala (D-75)."""
    with _brava():
        return _greska(PO.nova_verzija, _c(), nalog_id, p.tko, p.pravila, potvrdi_opt=p.potvrdi_opt)


# ---------------------------------------------------------------- optimizacija s potvrdom (D-75) i postavke (D-77)
class OptimizacijaP(BaseModel):
    nacin: str = "auto"                    # auto | hub | uzduzno | poprecno | trake (D-91)
    dubina: str = "najbolje"               # brzo | najbolje
    tko: str = "web"


class TkoP(BaseModel):
    tko: str = "web"


class PripremiP(BaseModel):
    nm: Optional[int] = None               # samo taj materijal; None = svi bez potvrde
    svjeze: bool = False                   # True = računaj iznova i kad prijedlozi postoje (gumb Optimiziraj)
    tko: str = "web"


@router.get("/api/nalog/{nalog_id}/optimizacija")
def nalog_optimizacija(nalog_id: int):
    with _ctx["brava"]:
        c = _c()
        _greska(N.nalog, c, nalog_id)
        return _greska(OP.pregled, c, nalog_id)


@router.post("/api/nalog/{nalog_id}/optimizacija/pripremi")
def nalog_optimizacija_pripremi(nalog_id: int, p: PripremiP):
    """D-91: za materijale bez potvrde napravi zadani prijedlog (realno za pilu) i, kad štedi m², Hub rezervu; vraća pregled kao GET."""
    with _brava():
        c = _c()
        _greska(N.nalog, c, nalog_id)
        _greska(OP.pripremi_prijedloge, c, nalog_id, p.tko, p.nm, p.svjeze)
        c.commit()
        return _greska(OP.pregled, c, nalog_id)


@router.post("/api/nalog/{nalog_id}/materijal/{nm_id}/optimizacija")
def nalog_optimizacija_prijedlog(nalog_id: int, nm_id: int, p: OptimizacijaP):
    """Novi prijedlog slaganja materijala (način × dubina); ekran ga pokaže uz sheme i razliku prema automatskom."""
    with _brava():
        c = _c()
        m = _greska(N.materijal_naloga, c, nm_id)
        if not m or m["nalog_id"] != nalog_id:
            raise HTTPException(404, "materijal %s nije u nalogu %s" % (nm_id, nalog_id))
        return _greska(OP.predlozi, c, nm_id, p.nacin, p.dubina, p.tko)


@router.get("/api/optimizacija/{oid}/pregled")
def optimizacija_pregled(oid: int):
    """Pregled slaganja na ekranu (bez PDF-a): listovi, elementi, statistika, trake."""
    from ..ispis import sheme_png as SPNG, krojni as KR
    with _brava():
        try:
            r = SPNG.pregled(_c(), oid)
        except (KR.IspisGreska, ValueError) as e:
            raise HTTPException(400, str(e))
    if not r:
        raise HTTPException(404, "optimizacija %s ne postoji" % oid)
    return r


@router.get("/api/optimizacija/{oid}/sheme.png")
def optimizacija_sheme_png(oid: int, h: int = 150, list: int = 0):
    """Sličica slaganja (sve ploče u redu, uspravno) za ekran obračuna / pile — vidi se odmah, bez PDF-a; ?list=n = jedna ploča s brojevima i mjerama."""
    from fastapi.responses import FileResponse
    from ..ispis import sheme_png as SPNG, krojni as KR
    with _brava():
        try:
            put = SPNG.png(_c(), oid, visina_px=max(80, min(h, 900)), list_br=list or None)
        except (KR.IspisGreska, ValueError) as e:
            raise HTTPException(400, str(e))
        except ImportError:
            raise HTTPException(500, "matplotlib nije instaliran — sličica se ne može nacrtati")
    if not put:
        raise HTTPException(404, "optimizacija %s nema sheme" % oid)
    return FileResponse(put, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.post("/api/optimizacija/{oid}/potvrdi")
def optimizacija_potvrdi(oid: int, p: TkoP):
    """Prijedlog → potvrđeno slaganje (jedino za ponudu, pilu i nabavu). `ponuda_poslana` = treba nova verzija ponude."""
    with _brava():
        return _greska(OP.potvrdi, _c(), oid, p.tko)


POSTAVKE_OPT = ("kerf", "kerf_pile", "nadmjera_trake", "obracun_rezanja", "ident_rezanje_rez", "ident_rezanje_m", "mapa_nesting", "mapa_pila",
                "pila_max_razina", "pila_max_sirina_u_traci", "pila_min_komad_4", "pila_mijesana_orijentacija")


def _postavke_opt(c):
    return [dict(r) for r in c.execute("SELECT kljuc, vrijednost, opis FROM postavke WHERE kljuc IN (%s) ORDER BY kljuc" % ",".join("?" * len(POSTAVKE_OPT)), POSTAVKE_OPT)]


@router.get("/api/postavke/optimizacija")
def postavke_optimizacija():
    with _ctx["brava"]:
        return _postavke_opt(_c())


@router.post("/api/postavke/optimizacija")
def postavke_optimizacija_upisi(p: dict):
    """{kljuc: vrijednost, …} — samo ključevi iz POSTAVKE_OPT; brojčane se provjere."""
    with _brava():
        c = _c()
        tko = p.pop("tko", "web")
        for k, v in p.items():
            if k not in POSTAVKE_OPT:
                raise HTTPException(400, "nepoznata postavka %s" % k)
            if k in ("kerf", "kerf_pile", "nadmjera_trake", "pila_min_komad_4"):
                try:
                    float(str(v).replace(",", "."))
                except ValueError:
                    raise HTTPException(400, "%s mora biti broj" % k)
                v = str(v).replace(",", ".")
            if k == "pila_max_razina" and str(v) not in ("2", "3", "4"):
                raise HTTPException(400, "pila_max_razina: 2 | 3 | 4")
            if k == "pila_max_sirina_u_traci" and not str(v).isdigit():
                raise HTTPException(400, "pila_max_sirina_u_traci mora biti cijeli broj (0 = bez ograničenja)")
            if k == "pila_mijesana_orijentacija" and str(v) not in ("0", "1"):
                raise HTTPException(400, "pila_mijesana_orijentacija: 0 | 1")
            if k == "obracun_rezanja" and v not in ("m2", "rezova", "m_reza"):
                raise HTTPException(400, "obracun_rezanja: m2 | rezova | m_reza")
            c.execute("UPDATE postavke SET vrijednost = ? WHERE kljuc = ?", (str(v), k))
            db.dnevnik(c, tko, "postavke", k, "promjena", str(v))
        c.commit()
        return _postavke_opt(c)


@router.get("/api/ponuda/{vid}")
def ponuda_verzija(vid: int):
    with _ctx["brava"]:
        return _greska(PO.verzija, _c(), vid)


class EslogP(BaseModel):
    mapa: Optional[str] = None
    broj: Optional[str] = None
    tko: str = "web"


@router.post("/api/ponuda/{vid}/eslog")
def ponuda_eslog(vid: int, p: EslogP):
    with _brava():
        return dict(eslog=_greska(PO.napisi_eslog, _c(), vid, p.mapa, p.tko, p.broj))


class PoslanaP(BaseModel):
    na: Optional[str] = None
    mail_tekst: Optional[str] = None
    tko: str = "web"


class PosaljiP(BaseModel):
    na: Optional[str] = None               # zadano e-mail kupca iz Huba
    tekst: Optional[str] = None
    cc: Optional[str] = None
    mapa: Optional[str] = None
    suho: bool = False                     # sastavi PDF i poruku, ne šalji
    tko: str = "web"


@router.post("/api/ponuda/{vid}/posalji")
def ponuda_posalji(vid: int, p: PosaljiP):
    """Ponuda kupcu mailom s PDF-om (D-41). Bez SMTP lozinke → 400 s uputom; ured može poslati ručno i označiti /poslana."""
    from ..nalozi import mail as M
    with _brava():
        try:
            return _greska(PO.posalji, _c(), vid, p.tko, p.na, p.tekst, p.cc, p.mapa, p.suho)
        except M.MailGreska as e:
            _rollback()
            raise HTTPException(400, str(e))


@router.get("/api/mail/postavke")
def mail_postavke():
    from ..nalozi import mail as M
    with _ctx["brava"]:
        p = M.postavke_smtp(_c())
        p.pop("lozinka", None)
        return p


@router.post("/api/ponuda/{vid}/poslana")
def ponuda_poslana(vid: int, p: PoslanaP):
    with _brava():
        return _greska(PO.oznaci_poslanu, _c(), vid, p.tko, p.na, p.mail_tekst)


class PotvrdaP(BaseModel):
    ponuda_pantheon: Optional[str] = None
    datum: Optional[str] = None
    nacin: Optional[str] = None            # mail | telefon | osobno
    rok_obecan: Optional[str] = None
    prioritet: Optional[str] = None
    mapa: Optional[str] = None
    tko: str = "web"


@router.post("/api/ponuda/{vid}/potvrdi")
def ponuda_potvrdi(vid: int, p: PotvrdaP):
    """Dijalog 3b „Kupac potvrdio“: verzija potvrđena, nalog → potvrdjeno, eSlog XML za Pantheon."""
    with _brava():
        return _greska(PO.potvrdi, _c(), vid, p.tko, p.ponuda_pantheon, p.mapa, datum=p.datum, nacin=p.nacin, rok_obecan=p.rok_obecan, prioritet=p.prioritet)


@router.post("/api/nalog/{nalog_id}/izdatnica")
def nalog_izdatnica(nalog_id: int, p: EslogP):
    with _brava():
        return _greska(PO.korekcija_po_stvarnom, _c(), nalog_id, p.tko, p.mapa)


# ---------------------------------------------------------------- rezultat nestinga (.mno) i sheme (D-38, D-34)
class RezultatNesting(BaseModel):
    put: Optional[str] = None              # jedna .mno datoteka
    mapa: Optional[str] = None             # ili mapa bNest projekata — svi .mno ispod nje, već uvezeni se preskaču
    suho: bool = False
    tko: str = "web"


@router.post("/api/rezultat/nesting")
def rezultat_nesting(p: RezultatNesting):
    """bNest rezultat → `optimizacija` (engine bNest) za svaki materijal naloga čiji su dijelovi u poslu; spojeni posao se razdijeli po kvadraturi."""
    if not (p.put or p.mapa):
        raise HTTPException(400, "treba put (.mno) ili mapa")
    with _brava():
        if p.put:
            return _greska(RN.upisi, _c(), p.put, p.tko, p.suho)
        return _greska(RN.upisi_mapu, _c(), p.mapa, p.tko, p.suho)


@router.get("/api/nalog/{nalog_id}/rezultati")
def nalog_rezultati(nalog_id: int):
    """Po materijalu: zadnji Hubov izvoz na pilu (ploče, naplata, sheme PNG) i zadnji bNest rezultat (stvarno potrošeno) — D-38."""
    with _ctx["brava"]:
        c = _c()
        _greska(N.nalog, c, nalog_id)
        return RN.usporedba(c, nalog_id)


class IspisP(BaseModel):
    materijal: Optional[int] = None
    oid: Optional[int] = None
    mapa: Optional[str] = None
    tko: str = "web"


@router.get("/api/nalog/{nalog_id}/ispis/krojni.pdf")
def nalog_ispis_krojni(nalog_id: int, materijal: Optional[int] = None, oid: Optional[int] = None, mapa: Optional[str] = None):
    """Krojni nacrt (PDF) — svi materijali naloga koji se slažu na ploču ili jedan (`materijal`); iz potvrđenog slaganja, bez potvrde s oznakom PRIJEDLOG.
    Datoteka se napiše u mapu ispisa i vrati; ne bilježi se kao dokument (za to POST)."""
    from fastapi.responses import FileResponse
    from ..ispis import krojni as KR
    with _brava():
        c = _c()
        _greska(N.nalog, c, nalog_id)
        try:
            r = KR.napravi(c, nalog_id, mapa, materijal, oid, "web", zabiljezi=False)
        except (KR.IspisGreska, OP.OptimizacijaGreska) as e:
            raise HTTPException(400, str(e))
        return pdf_inline(r["put"])


@router.post("/api/nalog/{nalog_id}/ispis/krojni.pdf")
def nalog_ispis_krojni_zabiljezi(nalog_id: int, p: IspisP):
    from ..ispis import krojni as KR
    with _brava():
        c = _c()
        _greska(N.nalog, c, nalog_id)
        try:
            return KR.napravi(c, nalog_id, p.mapa, p.materijal, p.oid, p.tko)
        except (KR.IspisGreska, OP.OptimizacijaGreska) as e:
            _rollback()
            raise HTTPException(400, str(e))


@router.get("/api/slika")
def slika(put: str):
    """PNG sheme — vraća se samo datoteka koja je zabilježena kao dokument (png) nekog naloga."""
    from fastapi.responses import FileResponse
    with _ctx["brava"]:
        r = _c().execute("SELECT 1 FROM dokument WHERE vrsta = 'png' AND putanja = ?", (os.path.abspath(put),)).fetchone()
    if not r or not os.path.isfile(put):
        raise HTTPException(404, "nema takve slike")
    return FileResponse(put, media_type="image/png")


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
        elif ime.lower().endswith(".pnl"):
            st = _greska(U.uvezi_pnl, c, nalog_id, putanja, tko)
        else:
            raise HTTPException(400, "podržane su datoteke .CPW, .PNL (PanelWizard) i .CSV (PPNEST)")
        return dict(st, datoteka=ime, za_potvrdu=N.za_potvrdu(c, nalog_id), sazetak=N.pregled(c, nalog_id)["sazetak"])
