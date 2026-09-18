# -*- coding: utf-8 -*-
"""API Warehouse (D-64, ekrani 4 Skladište i 6 Nabava):

    GET  /api/skladiste/stanje?ident=&q=&limit=      pogled po materijalu: pune ploče (Winstore: fizičko, rezervirano, naručeno, raspoloživo, kod) + restlovi (kom, m²)
    GET  /api/skladiste/materijal/{mid}              jedan materijal: ploče, restlovi s lokacijama, rezervacije
    GET  /api/skladiste/restlovi?ident=&status=&za_potvrdu=&q=   popis restlova (status: slobodan,rezerviran,provjeri,prijedlog,potrosen,otpisan)
    GET  /api/skladiste/restlovi/sazetak             brojke (po statusu, za potvrdu, m² na stanju, zadnji uvoz)
    POST /api/skladiste/restlovi/uvoz                {putanja, tko}  uvoz evidencije RESTLOVI_V7.xlsm (idempotentno)
    POST /api/skladiste/restlovi                     {ident, L, W, kom, lokacija, napomena, tko}  ručno otvoren restl (skladištar)
    POST /api/skladiste/restlovi/{id}/potvrdi        {tko, lokacija, L, W}  skladištar potvrdio (QR zalijepljen): prijedlog / provjeri → slobodan
    POST /api/skladiste/restlovi/{id}/odbaci         {tko, razlog}  prijedloga nema / restl bačen → otpisan
    POST /api/skladiste/restlovi/potvrdi-dekor       {dekor, ident, tko}  dekor iz evidencije → ident (svi restlovi tog dekora + alias)
    GET  /api/skladiste/prijedlozi?nalog=            restlovi predloženi iz potvrđenih shema, čekaju skladištara (D-64/3)
    GET  /api/skladiste/restl/{oznaka}              jedan restl za skladištarev ekran (QR)
    GET  /api/skladiste/izdavanje?nalog=            što skladištar treba iznijeti: restlovi i materijali kojih Winstore nema (D-95)
    POST /api/skladiste/izdaj                       {nm, tko} skladištar potvrdio izdavanje jednog materijala naloga (D-95)
    GET  /api/skladiste/trake?ident=                 metri i pretinac iz Regal trake (čitanje, D-63)
    GET  /api/nalog/{id}/skladiste                   provjera naloga (D-35): potrebno / raspoloživo / manjak po materijalu, restl kandidati, trake, za nabavu
    POST /api/nalog/{id}/skladiste/rezerviraj        {restlovi: {nm_id: restl_id}, tko}  rezervacija ploča i restla + prijedlozi restlova
    POST /api/nalog/{id}/skladiste/oslobodi          {tko}
    GET  /api/skladiste/potrebe                      potreba preko svih potvrđenih naloga (D-42/5) — ekran Nabava
    GET  /api/skladiste/restlovi/naljepnice.pdf?oznake=|nalog=|status=&format=a4|rola   QR naljepnice restlova (D-64/3)
    GET  /r/{oznaka}                                 stranica restla za skeniranje QR-a (kao Regal traka /t/IDENT)
    GET  /api/nabava/dobavljaci   POST {naziv, email, kontakt}        dobavljači iz Pantheona + e-mail u Hubu
    GET  /api/nabava/narudzbenice?status=&dobavljac=                   popis;  POST {iz_potreba: true | dobavljac, stavke[], napomena, tko}
    GET  /api/nabava/narudzbenica/{id|broj}                            narudžbenica sa stavkama
    POST /api/nabava/narudzbenica/{id}/stavke {ident, kom, jm}         PUT /api/nabava/stavka/{sid} {kom}   DELETE /api/nabava/stavka/{sid}
    POST /api/nabava/narudzbenica/{id}/posalji {na, suho, mapa, tekst} PDF + mail dobavljaču → poslana (D-41 mehanizam)
    POST /api/nabava/narudzbenica/{id}/zaprimi {stavke{ident: kom}, ref}   ručna primka;  POST …/ponisti {razlog}
    POST /api/nabava/primka {putanja}                                  eSlog primka → zatvara otvorene narudžbenice po identu
"""
from typing import Dict, Optional

from fastapi import Request, APIRouter, HTTPException
from . import nalozi_api as NA
from pydantic import BaseModel

from ..skladiste import pogled as SK, restlovi as RS, ploce as PL, trake as TR
from ..nalozi import nalozi as N

router = APIRouter()
_ctx = {}


def _c():
    return _ctx["veza"]()


def _brava():
    return _ctx["brava"]


def _greska(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except (N.NalogGreska, ValueError) as e:
        try:
            _c().rollback()
        except Exception:
            pass
        raise HTTPException(400, str(e))


@router.get("/api/skladiste/stanje")
def stanje(ident: Optional[str] = None, q: Optional[str] = None, limit: int = 300):
    c = _c()
    sql = "SELECT id FROM materijal WHERE aktivan = 1 AND ne_koristi_se = 0"
    a = []
    if ident:
        sql += " AND pantheon_ident = ?"; a.append(ident)
    if q:
        sql += " AND (trazi LIKE ? OR pantheon_ident LIKE ?)"; a += ["%" + q.upper() + "%", "%" + q.upper() + "%"]
    sql += " AND (id IN (SELECT materijal_id FROM winstore_ploca WHERE ambalaza = 0) OR id IN (SELECT materijal_id FROM restl WHERE materijal_id IS NOT NULL)) ORDER BY pantheon_ident LIMIT ?"
    a.append(limit)
    with _brava():
        out = [SK.stanje_materijala(c, r["id"]) for r in c.execute(sql, a)]
    return dict(broj=len(out), materijali=out)


@router.get("/api/skladiste/materijal/{mid}")
def materijal(mid: int):
    with _brava():
        s = SK.stanje_materijala(_c(), mid)
        if not s:
            raise HTTPException(404, "nema materijala")
        s["ploce"]["kodovi"] = (PL.stanje(_c(), materijal_id=mid, samo_sa_stanjem=False) or [dict(kodovi=[])])[0]["kodovi"]
        s["rezervacije"] = [dict(r) for r in _c().execute(
            "SELECT r.*, n.naziv AS nalog FROM rezervacija r JOIN nalog_materijal nm ON nm.id = r.nalog_materijal_id JOIN nalog n ON n.id = nm.nalog_id "
            "WHERE nm.materijal_id = ? AND r.status IN ('rezervirano', 'izdano') ORDER BY r.id", (mid,))]
        return s


@router.get("/api/skladiste/restlovi")
def restlovi(ident: Optional[str] = None, status: Optional[str] = None, za_potvrdu: Optional[int] = None, q: Optional[str] = None, limit: int = 500):
    with _brava():
        r = RS.popis(_c(), ident=ident, status=status, za_potvrdu=None if za_potvrdu is None else bool(za_potvrdu), q=q, limit=limit)
    return dict(broj=len(r), restlovi=r)


@router.get("/api/skladiste/restlovi/sazetak")
def restlovi_sazetak():
    with _brava():
        return RS.sazetak(_c())


class Uvoz(BaseModel):
    putanja: str
    tko: str = "web"


@router.post("/api/skladiste/restlovi/uvoz")
def restlovi_uvoz(p: Uvoz):
    with _brava():
        return _greska(RS.uvezi_excel, _c(), p.putanja, p.tko)


class NoviRestl(BaseModel):
    ident: str
    L: float
    W: float
    kom: int = 1
    lokacija: Optional[str] = None
    napomena: Optional[str] = None
    izvor: str = "rucno"                 # rucno | kupac (komad koji je kupac ostavio nama, D-95)
    tko: str = "web"


@router.post("/api/skladiste/restlovi")
def restl_novi(p: NoviRestl):
    """Ručno otvoren restl (skladištar): ostatak ručnog reza, povrat s montaže ili komad koji je KUPAC ostavio nama (izvor 'kupac', D-95)."""
    if p.izvor not in ("rucno", "kupac"):
        raise HTTPException(400, "izvor: rucno | kupac")
    nap = p.napomena
    if p.izvor == "kupac":
        nap = ("kupac ostavio nama" + ("; " + nap if nap else ""))
    with _brava():
        return _greska(RS.novi_restl, _c(), p.ident, p.L, p.W, p.tko, kom=p.kom, lokacija=p.lokacija, napomena=nap, potvrdio=p.tko, izvor=p.izvor)


class Potvrda(BaseModel):
    tko: str = "web"
    lokacija: Optional[str] = None
    L: Optional[float] = None
    W: Optional[float] = None


@router.post("/api/skladiste/restlovi/{rid}/potvrdi")
def restl_potvrdi(rid: str, p: Potvrda):
    with _brava():
        return _greska(RS.potvrdi_restl, _c(), rid, p.tko, lokacija=p.lokacija, L=p.L, W=p.W)


class Odbaci(BaseModel):
    tko: str = "web"
    razlog: Optional[str] = None


@router.post("/api/skladiste/restlovi/{rid}/odbaci")
def restl_odbaci(rid: str, p: Odbaci):
    with _brava():
        return _greska(RS.odbaci_restl, _c(), rid, p.tko, razlog=p.razlog)


class PotvrdaDekora(BaseModel):
    dekor: str
    ident: str
    tko: str = "web"


@router.post("/api/skladiste/restlovi/potvrdi-dekor")
def restl_potvrdi_dekor(p: PotvrdaDekora):
    with _brava():
        n = _greska(RS.potvrdi_dekor, _c(), p.dekor, p.ident, p.tko)
        return dict(dekor=p.dekor, ident=p.ident, restlova=n)


@router.get("/api/skladiste/prijedlozi")
def prijedlozi(nalog: Optional[int] = None):
    with _brava():
        r = RS.prijedlozi(_c(), nalog)
    return dict(broj=len(r), prijedlozi=r)


@router.get("/api/skladiste/trake")
def trake(ident: str):
    with _brava():
        return TR.stanje(_c(), ident)


@router.get("/api/nalog/{nalog_id}/skladiste")
def nalog_skladiste(nalog_id: int):
    with _brava():
        _greska(N.nalog, _c(), nalog_id)
        return SK.provjera_naloga(_c(), nalog_id)


class Rezervacija(BaseModel):
    restlovi: Dict[str, int] = {}
    tko: str = "web"


@router.post("/api/nalog/{nalog_id}/skladiste/rezerviraj")
def nalog_rezerviraj(nalog_id: int, p: Rezervacija):
    with _brava():
        _greska(N.nalog, _c(), nalog_id)
        return _greska(SK.rezerviraj_nalog, _c(), nalog_id, p.tko, restlovi={int(k): v for k, v in p.restlovi.items()})


class Tko(BaseModel):
    tko: str = "web"


@router.post("/api/nalog/{nalog_id}/skladiste/oslobodi")
def nalog_oslobodi(nalog_id: int, p: Tko):
    with _brava():
        _greska(N.nalog, _c(), nalog_id)
        return dict(oslobodjeno=SK.oslobodi_nalog(_c(), nalog_id, p.tko))


@router.get("/api/skladiste/potrebe")
def potrebe():
    with _brava():
        return SK.potrebe_ukupno(_c())


# ---------------------------------------------------------------- naljepnice restlova (QR) + stranica za skeniranje
from fastapi import Response
from fastapi.responses import FileResponse, HTMLResponse
from ..ispis import naljepnica_restl as NL
from ..nabava import narudzbenica as NB
import os as _os
import tempfile as _tempfile
from html import escape as _esc


@router.get("/api/skladiste/restlovi/naljepnice.pdf")
def restl_naljepnice(oznake: Optional[str] = None, nalog: Optional[int] = None, status: Optional[str] = None, format: Optional[str] = None):
    """PDF naljepnica: ?oznake=R1364,R1365 | ?nalog=ID (prijedlozi tog naloga) | ?status=prijedlog; ?format=a4|rola."""
    with _brava():
        c = _c()
        if oznake:
            r = [x for x in (RS.restl(c, o.strip()) for o in oznake.split(",")) if x]
        elif nalog:
            r = RS.prijedlozi(c, nalog)
        else:
            r = RS.popis(c, status=status or "prijedlog")
        if not r:
            raise HTTPException(404, "nema restlova za naljepnice")
        put = NL.napravi(c, r, _tempfile.mkdtemp(prefix="hub_nalj_"), format_=format)
        if not put:
            raise HTTPException(500, "reportlab nije instaliran")
    return NA.pdf_inline(put)


@router.get("/api/skladiste/restl/{oznaka}")
def restl_jedan(oznaka: str):
    """Jedan restl za skladištarev ekran (QR): mjere, dekor, lokacija, status, napomena."""
    with _ctx["brava"]:
        r = RS.restl(_c(), oznaka.upper() if not oznaka.isdigit() else int(oznaka))
    if not r:
        raise HTTPException(404, "nema restla %s" % oznaka)
    return r


@router.get("/api/skladiste/izdavanje")
def izdavanje(nalog: Optional[int] = None):
    """Što skladištar treba iznijeti iz regala (D-95): rezervirani restlovi i materijali kojih Winstore ne drži."""
    with _ctx["brava"]:
        return SK.ceka_izdavanje(_c(), nalog)


class Izdaj(BaseModel):
    nm: int
    tko: str = "web"


@router.post("/api/skladiste/izdaj")
def izdaj(p: Izdaj):
    """Skladištar potvrdio izdavanje jednog materijala naloga: rezervacije → izdano, rezervirani restl → potrošen."""
    with _brava():
        n = _greska(SK.izdaj_materijal, _c(), p.nm, p.tko)
        return dict(izdano=n)


@router.get("/r/{oznaka}", response_class=HTMLResponse)
def restl_stranica(oznaka: str):
    """Što skladištar vidi kad skenira QR: otvara se skladištarev ekran tog restla u aplikaciji (potvrdi, ispravi mjeru, otpiši).
    Bez JavaScripta ostaje čitljiv ispis, pa QR radi i na starom čitaču."""
    o = _esc(oznaka.upper())
    with _brava():
        r = RS.restl(_c(), oznaka.upper())
    if not r:
        return HTMLResponse("<h1>%s</h1><p>Nema takvog restla.</p>" % o, status_code=404)
    redovi = [("Materijal", "%s %s" % (r["ident"] or "—", r.get("naziv_kratki") or r.get("naziv") or r.get("dekor_ulaz") or "")),
              ("Mjere", "%g × %g mm%s" % (r["L"], r["W"], (" × %d kom" % r["kom"]) if r["kom"] > 1 else "")), ("Debljina", "%s mm" % (r.get("debljina") or "?")),
              ("Lokacija", r.get("lokacija") or "—"), ("Status", r["status"] + (" (dekor za potvrdu)" if r["provjeri"] else "")),
              ("Napomena", r.get("napomena") or "")]
    body = "".join("<tr><th>%s</th><td>%s</td></tr>" % (_esc(k), _esc(str(v))) for k, v in redovi)
    return HTMLResponse('<!doctype html><html lang="hr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                        '<title>%s</title><script>location.replace("/#/restl/%s")</script>'
                        '<style>body{font-family:Inter,system-ui,sans-serif;margin:16px;color:#222}h1{font-size:2.2em;margin:0 0 8px}'
                        'table{border-collapse:collapse}th{text-align:left;padding:6px 12px 6px 0;color:#5A5F64}td{padding:6px 0}'
                        'a{display:inline-block;margin-top:14px;font-weight:700}</style></head>'
                        '<body><h1>%s</h1><table>%s</table><a href="/#/restl/%s">Otvori u Hubu</a></body></html>' % (o, o, o, body, o))


# ---------------------------------------------------------------- nabava (D-42/5)
def _greska_nb(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except (NB.NabavaGreska, ValueError) as e:
        try:
            _c().rollback()
        except Exception:
            pass
        raise HTTPException(400, str(e))
    except Exception as e:
        from ..nalozi.mail import MailGreska
        if isinstance(e, MailGreska):
            raise HTTPException(400, str(e))
        raise


@router.get("/api/nabava/dobavljaci")
def nabava_dobavljaci():
    with _brava():
        return NB.dobavljaci(_c())


class Dobavljac(BaseModel):
    naziv: str
    email: Optional[str] = None
    kontakt: Optional[str] = None
    napomena: Optional[str] = None
    tko: str = "web"


@router.post("/api/nabava/dobavljaci")
def nabava_dobavljac_upis(p: Dobavljac):
    with _brava():
        return dict(_greska_nb(NB.upisi_dobavljaca, _c(), p.naziv, p.email, p.kontakt, p.napomena, p.tko))


@router.get("/api/nabava/narudzbenice")
def narudzbenice(status: Optional[str] = None, dobavljac: Optional[str] = None):
    with _brava():
        return NB.popis(_c(), status=status, dobavljac=dobavljac)


class NovaNarudzbenica(BaseModel):
    dobavljac: Optional[str] = None
    iz_potreba: bool = False
    stavke: list = []
    napomena: Optional[str] = None
    ocekivano: Optional[str] = None
    tko: str = "web"


@router.post("/api/nabava/narudzbenice")
def narudzbenica_nova(p: NovaNarudzbenica):
    """iz_potreba=true → nacrti po dobavljaču iz potreba (D-42/5); inače ručna {dobavljac, stavke[{ident, kom, jm, nalog_materijal_id}]}."""
    with _brava():
        if p.iz_potreba:
            return _greska_nb(NB.iz_potreba, _c(), p.tko, p.dobavljac)
        return _greska_nb(NB.nova, _c(), p.dobavljac, p.tko, p.stavke, napomena=p.napomena, ocekivano=p.ocekivano)


@router.get("/api/nabava/narudzbenica/{nid}")
def narudzbenica(nid: str):
    with _brava():
        r = NB.red(_c(), nid)
    if not r:
        raise HTTPException(404, "nema narudžbenice")
    return r


class Stavka(BaseModel):
    ident: str
    kom: float
    jm: Optional[str] = None
    dimenzija: Optional[str] = None
    nalog_materijal_id: Optional[int] = None


@router.post("/api/nabava/narudzbenica/{nid}/stavke")
def narudzbenica_stavka(nid: int, p: Stavka):
    with _brava():
        _greska_nb(NB.dodaj_stavku, _c(), nid, p.ident, p.kom, jm=p.jm, dimenzija=p.dimenzija, nalog_materijal_id=p.nalog_materijal_id)
        return NB.red(_c(), nid)


class Kom(BaseModel):
    kom: float


@router.put("/api/nabava/stavka/{sid}")
def narudzbenica_stavka_kom(sid: int, p: Kom):
    with _brava():
        _greska_nb(NB.promijeni_stavku, _c(), sid, p.kom)
        return dict(ok=True)


@router.delete("/api/nabava/stavka/{sid}")
def narudzbenica_stavka_brisi(sid: int):
    with _brava():
        _greska_nb(NB.ukloni_stavku, _c(), sid)
        return dict(ok=True)


class Slanje(BaseModel):
    na: Optional[str] = None
    suho: bool = False
    mapa: Optional[str] = None
    tekst: Optional[str] = None
    tko: str = "web"


@router.post("/api/nabava/narudzbenica/{nid}/posalji")
def narudzbenica_posalji(nid: int, p: Slanje):
    with _brava():
        return _greska_nb(NB.posalji, _c(), nid, p.tko, na=p.na, suho=p.suho, mapa=p.mapa, tekst=p.tekst)


class Primka(BaseModel):
    stavke: Dict[str, float] = {}
    ref: Optional[str] = None
    tko: str = "web"


@router.post("/api/nabava/narudzbenica/{nid}/zaprimi")
def narudzbenica_zaprimi(nid: int, p: Primka):
    with _brava():
        return _greska_nb(NB.zaprimi, _c(), nid, p.stavke, p.tko, ref=p.ref)


class Ponisti(BaseModel):
    razlog: Optional[str] = None
    tko: str = "web"


@router.post("/api/nabava/narudzbenica/{nid}/ponisti")
def narudzbenica_ponisti(nid: int, p: Ponisti):
    with _brava():
        return _greska_nb(NB.ponisti, _c(), nid, p.tko, p.razlog)


class PrimkaEslog(BaseModel):
    putanja: str
    tko: str = "web"


@router.post("/api/nabava/primka")
def nabava_primka(p: PrimkaEslog):
    """eSlog primka (Knjiga → Pantheon) zatvara otvorene narudžbenice po identu (D-42/5)."""
    with _brava():
        return _greska_nb(NB.uvezi_primku_eslog, _c(), p.putanja, p.tko)


# ---------------------------------------------------------------- PDF ponude za ekran 3 (verzija koja već ima PDF, ili se napravi u mapu ispisa)
@router.get("/api/ponuda/{vid}/pdf")
def ponuda_pdf(vid: int, request: Request, svjeze: int = 0):
    """PDF ponude: poslana verzija = spremljeni PDF; nacrt (ili ?svjeze=1) = napravi sada, s kontaktom prijavljenog korisnika."""
    from ..nalozi import ponuda as PO, ponuda_pdf as PP
    from . import korisnici_api as KA
    k = KA.prijavljeni(request)
    with _brava():
        c = _c()
        try:
            v = PO.verzija(c, vid)
        except PO.PonudaGreska as e:
            raise HTTPException(404, str(e))
        put = v.get("pdf_putanja")
        if not put or not _os.path.exists(put) or svjeze or v["status"] == "nacrt":
            r = PP.napravi(c, vid, _tempfile.mkdtemp(prefix="hub_ponuda_"), tko=(k or {}).get("oznaka"))
            put = r.get("pdf") or r.get("html")
        if not put:
            raise HTTPException(500, "PDF nije napravljen")
    return NA.pdf_inline(put, "application/pdf" if put.lower().endswith(".pdf") else "text/html")


@router.get("/api/nabava/narudzbenica/{nid}/pdf")
def narudzbenica_pdf(nid: int):
    from ..ispis import narudzbenica as PDF
    with _brava():
        c = _c()
        d = NB.red(c, nid)
        if not d:
            raise HTTPException(404, "nema narudžbenice")
        put = d.get("put_pdf")
        if not put or not _os.path.exists(put):
            put = PDF.napravi(c, d["id"], _tempfile.mkdtemp(prefix="hub_nar_"))
        if not put:
            raise HTTPException(500, "reportlab nije instaliran")
    return NA.pdf_inline(put)
