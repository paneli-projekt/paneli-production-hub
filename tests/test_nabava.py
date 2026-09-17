# -*- coding: utf-8 -*-
"""Nabava (D-42/5): narudžbenica iz potreba po dobavljaču, slanje (PDF + mail), ručna primka, eSlog primka zatvara narudžbenicu (m² → ploče);
QR naljepnice restlova i stranica /r/{oznaka} (D-64/3)."""
import os
import pytest

from hub.nalozi import nalozi as N, optimiziraj as OP
from hub.skladiste import pogled as SK, restlovi as RS
from hub.nabava import narudzbenica as NB
from hub.ispis import naljepnica_restl as NL
from tests.test_nalozi import baza  # noqa: F401
from tests.test_obracun_ponuda import baza_o  # noqa: F401
from tests.test_skladiste import skl, _mid  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog

ESLOG = """<?xml version="1.0" encoding="UTF-8"?>
<IzdaniRacunEnostavni><Racun Id="data">
  <GlavaRacuna><VrstaRacuna>380</VrstaRacuna><StevilkaRacuna>8754/ZG/300</StevilkaRacuna></GlavaRacuna>
  <DatumiRacuna><VrstaDatuma>137</VrstaDatuma><DatumRacuna>2026-09-17T00:00:00</DatumRacuna></DatumiRacuna>
  %s
  <PodatkiPodjetja><NazivNaslovPodjetja><VrstaPartnerja>SE</VrstaPartnerja><NazivPartnerja><NazivPartnerja1>IVERPAN D.O.O.</NazivPartnerja1></NazivPartnerja></NazivNaslovPodjetja></PodatkiPodjetja>
  <PodatkiPodjetja><NazivNaslovPodjetja><VrstaPartnerja>BY</VrstaPartnerja><NazivPartnerja><NazivPartnerja1>PANELI PROJEKT d.o.o.</NazivPartnerja1></NazivPartnerja></NazivNaslovPodjetja></PodatkiPodjetja>
  %s
</Racun></IzdaniRacunEnostavni>"""
STAVKA = """<PostavkeRacuna><Postavka><StevilkaVrstice>%d</StevilkaVrstice></Postavka>
  <DodatnaIdentifikacijaArtikla><VrstaPodatkaArtikla>5</VrstaPodatkaArtikla><StevilkaArtiklaDodatna>%s</StevilkaArtiklaDodatna><VrstaKodeArtiklaDodatna>SA</VrstaKodeArtiklaDodatna></DodatnaIdentifikacijaArtikla>
  <OpisiArtiklov><KodaOpisaArtikla>F</KodaOpisaArtikla><OpisArtikla><VrstaArtikla>CU</VrstaArtikla><OpisArtikla1>%s</OpisArtikla1></OpisArtikla></OpisiArtiklov>
  <KolicinaArtikla><VrstaKolicine>47</VrstaKolicine><Kolicina>%s</Kolicina><EnotaMere>%s</EnotaMere></KolicinaArtikla></PostavkeRacuna>"""


def _primka(put, stavke, ref=None):
    r = '<ReferencniDokumenti VrstaDokumenta="ON"><StevilkaDokumenta>%s</StevilkaDokumenta></ReferencniDokumenti>' % ref if ref else ""
    put.write_text(ESLOG % (r, "".join(STAVKA % (i + 1, *s) for i, s in enumerate(stavke))), encoding="utf-8")
    return str(put)


@pytest.fixture
def nab(skl, monkeypatch):
    skl.execute("UPDATE pantheon_ident SET dobavljac = 'IVERPAN d.o.o.' WHERE ident = 'IV000090'")
    skl.execute("UPDATE winstore_ploca SET kom_ukupno = 0 WHERE kod = 'W908ST2-18-2800-2070'")           # nema ploča → manjak
    skl.commit()
    poslano = []
    from hub.nalozi import mail as M
    monkeypatch.setattr(M, "posalji", lambda conn, na, predmet, tekst, html=None, prilozi=(), cc=None, tko="web", nalog_id=None, suho=False:
                        poslano.append(dict(na=na, predmet=predmet, prilozi=list(prilozi), suho=suho)) or dict(poslano=not suho, na=na, predmet=predmet, prilozi=list(prilozi)))
    skl.poslano = poslano
    return skl


def test_narudzbenica_iz_potreba_slanje_primka(nab, tmp_path):
    nid, nm, e1, e2 = _nalog(nab, status="potvrdjeno")
    OP.potvrdi(nab, OP.predlozi(nab, nm, "auto", "najbolje", "IVANA")["id"], "IVANA")
    u = SK.potrebe_ukupno(nab)
    assert [(z["ident"], z["kom"], z["jm"]) for z in u["za_nabavu"]] == [("IV000090", 1, "PLOČA"), ("TR000168", 1.0, "M")]
    # iz potreba: jedan nacrt po dobavljaču; traka bez dobavljača → NEPOZNAT DOBAVLJAČ
    ns = NB.iz_potreba(nab, "SANELA")
    assert [(n["dobavljac"], n["broj"], len(n["stavke"])) for n in ns] == [("IVERPAN d.o.o.", "N-%s-001" % NB.sada()[:4], 1), (NB.NEPOZNAT, "N-%s-002" % NB.sada()[:4], 1)]
    n1 = ns[0]
    st = n1["stavke"][0]
    assert st["pantheon_ident"] == "IV000090" and st["kom"] == 1 and st["jm"] == "PLOČA" and st["dimenzija"] == "2800×2070" and n1["status"] == "nacrt"
    # nacrt se ne računa kao naručeno; dorada stavki
    assert SK.provjera_naloga(nab, nid)["materijali"][0]["stanje"]["ploce"]["naruceno"] == 0
    NB.dodaj_stavku(nab, n1["id"], "IV000090", 2)                                  # ista stavka → zbroj 3
    NB.dodaj_stavku(nab, n1["id"], "IV000671", 1, jm="PLOČA")
    d = NB.red(nab, n1["id"])
    assert [(s["pantheon_ident"], s["kom"]) for s in d["stavke"]] == [("IV000090", 3), ("IV000671", 1)]
    NB.promijeni_stavku(nab, d["stavke"][1]["id"], 0)                             # 0 = ukloni
    assert len(NB.red(nab, n1["id"])["stavke"]) == 1
    with pytest.raises(NB.NabavaGreska, match="nepoznat ident"):
        NB.dodaj_stavku(nab, n1["id"], "IV999999", 1)
    # slanje: bez e-maila greška; s e-mailom dobavljača PDF + mail → poslana
    with pytest.raises(NB.NabavaGreska, match="nema e-mail"):
        NB.posalji(nab, n1["id"], "SANELA", mapa=str(tmp_path))
    NB.upisi_dobavljaca(nab, "IVERPAN d.o.o.", email="narudzbe@iverpan.hr", tko="SANELA")
    assert [x for x in NB.dobavljaci(nab) if x["naziv"] == "IVERPAN d.o.o."][0]["email"] == "narudzbe@iverpan.hr"
    r = NB.posalji(nab, n1["id"], "SANELA", suho=True, mapa=str(tmp_path))
    assert r["status"] == "nacrt" and r["pdf"] and os.path.exists(r["pdf"]) and nab.poslano[-1]["suho"]
    r = NB.posalji(nab, n1["id"], "SANELA", mapa=str(tmp_path))
    assert r["status"] == "poslana" and r["poslano_na"] == "narudzbe@iverpan.hr" and nab.poslano[-1]["prilozi"][0].endswith("Narudzba_%s.pdf" % n1["broj"])
    with pytest.raises(NB.NabavaGreska):
        NB.dodaj_stavku(nab, n1["id"], "IV000090", 1)                              # poslana se ne mijenja
    # naručeno ulazi u raspoloživo: manjak ploča 0
    pr = SK.provjera_naloga(nab, nid)["materijali"][0]
    assert pr["stanje"]["ploce"]["naruceno"] == 3 and pr["manjak"] == 0
    assert SK.potrebe_ukupno(nab)["materijali"][0]["manjak"] == 0
    # ručna primka 1 → djelomično
    z = NB.zaprimi(nab, n1["id"], {"IV000090": 1}, "SKLADISTAR", ref="otpremnica 77")
    assert z["status"] == "djelomicno" and z["stavke"][0]["zaprimljeno_kom"] == 1 and z["stavke"][0]["otvoreno"] == 2
    assert SK.provjera_naloga(nab, nid)["materijali"][0]["stanje"]["ploce"]["naruceno"] == 2
    # eSlog primka: 11,592 m² = 2 ploče 2800×2070 → zaprimljena; nepoznati ident nespojen; dobavljač prepoznat bez d.o.o.
    p = _primka(tmp_path / "primka.xml", [("IV000090", "IVERAL BIJELI NK", "11.592", "M2"), ("IV000221", "IVERAL CRNI NK", "3", "M2")])
    iz = NB.uvezi_primku_eslog(nab, p, "KNJIGA")
    assert iz["dobavljac"] == "IVERPAN d.o.o." and iz["racun"] == "8754/ZG/300"
    assert iz["spojeno"] == [dict(ident="IV000090", narudzbenica=n1["broj"], kom=2.0, jm="PLOČA")] and iz["pretvorbe"] == ["IV000090: m² → ploče (2800×2070)"]
    assert [x["ident"] for x in iz["nespojeno"]] == ["IV000221"] and iz["statusi"] == {n1["broj"]: "zaprimljena"}
    d = NB.red(nab, n1["id"])
    assert d["status"] == "zaprimljena" and d["stavke"][0]["primka_ref"].startswith("8754/ZG/300")
    assert SK.provjera_naloga(nab, nid)["materijali"][0]["stanje"]["ploce"]["naruceno"] == 0
    with pytest.raises(NB.NabavaGreska, match="ne poništava"):
        NB.ponisti(nab, n1["id"], "SANELA")
    # primka koja citira naš broj narudžbe ide točno na nju (i kad dobavljač piše drukčije)
    n2 = NB.nova(nab, "IVERPAN d.o.o.", "SANELA", [dict(ident="IV000090", kom=2)])
    n3 = NB.nova(nab, "IVERPAN d.o.o.", "SANELA", [dict(ident="IV000090", kom=2)])
    for x in (n2, n3):
        NB.posalji(nab, x["id"], "SANELA", na="narudzbe@iverpan.hr", mapa=str(tmp_path))
    iz = NB.uvezi_primku_eslog(nab, _primka(tmp_path / "p2.xml", [("IV000090", "x", "5.796", "M2")], ref=n3["broj"]), "KNJIGA")
    assert iz["spojeno"][0]["narudzbenica"] == n3["broj"] and NB.red(nab, n2["id"])["status"] == "poslana"
    iz = NB.uvezi_primku_eslog(nab, _primka(tmp_path / "p3.xml", [("IV000090", "x", "17.388", "M2")]), "KNJIGA")     # 3 ploče: FIFO n2 (2) pa n3 (1)
    assert [(s["narudzbenica"], s["kom"]) for s in iz["spojeno"]] == [(n2["broj"], 2.0), (n3["broj"], 1.0)] and not iz["nespojeno"]
    assert NB.popis(nab, status="zaprimljena")[0]["broj"] in (n2["broj"], n3["broj"]) and len(NB.popis(nab, status="zaprimljena")) == 3
    assert NB.ponisti(nab, NB.nova(nab, "X", "SANELA")["id"], "SANELA", "greška")["status"] == "ponistena"


def test_naljepnice_restlova(skl, tmp_path):
    pytest.importorskip("reportlab")
    mid = _mid(skl)
    r1 = RS.novi_restl(skl, mid, 1500, 900, "SKLADISTAR", lokacija="A001", potvrdio="SKLADISTAR")
    r2 = RS.novi_restl(skl, mid, 700, 600, "SKLADISTAR", kom=3)
    assert NL.url_restla(skl, "R0001") == "http://192.168.5.201:8766/r/R0001"
    p = NL.napravi(skl, [r1, r2], str(tmp_path))
    assert p.endswith("Naljepnice_restl_R0001-R0002.pdf") and os.path.getsize(p) > 1500
    p2 = NL.napravi(skl, [r1], str(tmp_path), format_="rola")
    assert p2.endswith("Naljepnice_restl_R0001.pdf") and os.path.exists(p2)


def test_api_nabava_i_naljepnice(nab, monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    monkeypatch.setenv("HUB_DB", str(nab.dir / "hub.db"))
    A._veza = None
    nid, nm, e1, e2 = _nalog(nab, status="potvrdjeno")
    OP.potvrdi(nab, OP.predlozi(nab, nm, "auto", "najbolje", "IVANA")["id"], "IVANA")
    RS.novi_restl(nab, _mid(nab), 1500, 900, "SKLADISTAR", lokacija="A001", potvrdio="SKLADISTAR")
    c = TestClient(A.app, raise_server_exceptions=False)
    try:
        r = c.post("/api/nabava/narudzbenice", json=dict(iz_potreba=True, tko="SANELA")).json()
        assert len(r) == 2 and r[0]["dobavljac"] == "IVERPAN d.o.o."
        nid_ = r[0]["id"]
        assert c.post("/api/nabava/dobavljaci", json=dict(naziv="IVERPAN d.o.o.", email="n@iverpan.hr")).json()["email"] == "n@iverpan.hr"
        assert c.post("/api/nabava/narudzbenica/%d/stavke" % nid_, json=dict(ident="IV000671", kom=2, jm="PLOČA")).json()["stavke"][1]["pantheon_ident"] == "IV000671"
        assert c.post("/api/nabava/narudzbenica/%d/stavke" % nid_, json=dict(ident="XX", kom=2)).status_code == 400
        r = c.post("/api/nabava/narudzbenica/%d/posalji" % nid_, json=dict(tko="SANELA", mapa=str(tmp_path))).json()
        assert r["status"] == "poslana" and r["poslano_na"] == "n@iverpan.hr"
        assert c.get("/api/nabava/narudzbenice", params=dict(status="poslana")).json()[0]["id"] == nid_
        assert c.get("/api/nabava/narudzbenica/%s" % r["broj"]).json()["broj"] == r["broj"]
        r = c.post("/api/nabava/narudzbenica/%d/zaprimi" % nid_, json=dict(stavke={"IV000090": 1}, ref="otp 1")).json()
        assert r["status"] == "djelomicno"
        p = _primka(tmp_path / "e.xml", [("IV000671", "PVC", "2", "PCE")])
        r = c.post("/api/nabava/primka", json=dict(putanja=p)).json()
        assert r["spojeno"][0]["ident"] == "IV000671" and r["statusi"]
        r = c.get("/api/skladiste/restlovi/naljepnice.pdf", params=dict(oznake="R0001"))
        assert r.status_code == 200 and r.headers["content-type"] == "application/pdf" and len(r.content) > 1000
        assert c.get("/api/skladiste/restlovi/naljepnice.pdf", params=dict(status="prijedlog")).status_code == 404
        r = c.get("/r/R0001")
        assert r.status_code == 200 and "R0001" in r.text and "1500 × 900" in r.text and "A001" in r.text
        assert c.get("/r/R9999").status_code == 404
    finally:
        A._veza = None
