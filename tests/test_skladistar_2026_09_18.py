# -*- coding: utf-8 -*-
"""Skladištarev ekran i izdavanje (D-95, Igor 18. 9.): Winstore je automatsko skladište i sam poslužuje svoje ploče, a skladištar
izdaje restlove i materijale kojih Winstore nema; ručni unos restla pokriva i komad koji kupac ostavi nama."""
import json

import pytest

from hub.nalozi import nalozi as N, optimiziraj as OP
from hub.skladiste import pogled as SK, restlovi as RS
from tests.test_nalozi import baza  # noqa: F401
from tests.test_obracun_ponuda import baza_o  # noqa: F401
from tests.test_skladiste import skl, _mid  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog


def test_u_winstoreu(skl):
    """Materijal iz zadnjeg izvoza drži Winstore; radna ploča i zidna obloga nikad."""
    mid = _mid(skl, "IV000090")
    assert SK.u_winstoreu(skl, mid) is True
    assert SK.u_winstoreu(skl, mid, "RP") is False and SK.u_winstoreu(skl, mid, "ZO") is False
    drugi = skl.execute("SELECT id FROM materijal WHERE pantheon_ident != 'IV000090' LIMIT 1").fetchone()[0]
    assert SK.u_winstoreu(skl, drugi) is False                                    # nema ga u Winstore izvozu
    assert SK.u_winstoreu(skl, None) is False


def test_winstore_izdaje_sam_a_ostalo_ceka_skladistara(skl):
    """Ploče iz Winstorea idu u izdano same, materijal izvan Winstorea čeka skladištara i vidi se na njegovom ekranu."""
    nid, nm, e1, e2 = _nalog(skl, status="potvrdjeno")
    OP.potvrdi(skl, OP.predlozi(skl, nm, "auto", "najbolje", "IVANA")["id"], "IVANA")
    N.postavi_status(skl, nid, "skladiste", "IVANA")
    N.postavi_status(skl, nid, "pila_nesting", "IVANA")
    assert skl.execute("SELECT status FROM rezervacija WHERE nalog_materijal_id = ?", (nm,)).fetchone()[0] == "izdano"
    assert SK.ceka_izdavanje(skl, nid) == []                                      # Winstore ga je poslužio sam
    # isti nalog, ali materijal kojeg Winstore ne drži
    skl.execute("DELETE FROM winstore_ploca"); skl.commit()
    nid2, nm2, _, _ = _nalog(skl, status="potvrdjeno")
    OP.potvrdi(skl, OP.predlozi(skl, nm2, "auto", "najbolje", "IVANA")["id"], "IVANA")
    N.postavi_status(skl, nid2, "skladiste", "IVANA")
    N.postavi_status(skl, nid2, "pila_nesting", "IVANA")
    ceka = SK.ceka_izdavanje(skl, nid2)
    assert len(ceka) == 1 and ceka[0]["nalog_materijal_id"] == nm2 and ceka[0]["kom"] >= 1 and ceka[0]["restlovi"] == []
    assert skl.execute("SELECT status FROM rezervacija WHERE nalog_materijal_id = ?", (nm2,)).fetchone()[0] == "rezervirano"
    assert SK.izdaj_materijal(skl, nm2, "SKLADISTAR") == 1
    assert skl.execute("SELECT status FROM rezervacija WHERE nalog_materijal_id = ?", (nm2,)).fetchone()[0] == "izdano"
    assert SK.ceka_izdavanje(skl, nid2) == []


def test_api_skladistar(skl, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    monkeypatch.setenv("HUB_DB", str(skl.dir / "hub.db"))
    A._veza = None
    c = TestClient(A.app, raise_server_exceptions=False)
    mid = _mid(skl, "IV000090")
    ident = skl.execute("SELECT pantheon_ident FROM materijal WHERE id = ?", (mid,)).fetchone()[0]
    # ručni restl koji je kupac ostavio nama
    r = c.post("/api/skladiste/restlovi", json=dict(ident=ident, L=1200, W=600, lokacija="A001", izvor="kupac", tko="SKLADISTAR"))
    assert r.status_code == 200
    x = r.json()
    assert x["status"] == "slobodan" and "kupac ostavio nama" in (x["napomena"] or "") and x["izvor"] == "kupac"
    assert c.post("/api/skladiste/restlovi", json=dict(ident=ident, L=500, W=500, izvor="nesto")).status_code == 400
    # jedan restl po oznaci + QR stranica
    g = c.get("/api/skladiste/restl/" + x["oznaka"])
    assert g.status_code == 200 and g.json()["oznaka"] == x["oznaka"]
    assert c.get("/api/skladiste/restl/R9999").status_code == 404
    qr = c.get("/r/" + x["oznaka"])
    assert qr.status_code == 200 and "#/restl/" + x["oznaka"] in qr.text
    # izdavanje kroz API
    skl.execute("DELETE FROM winstore_ploca"); skl.commit()
    nid, nm, _, _ = _nalog(skl, status="potvrdjeno")
    OP.potvrdi(skl, OP.predlozi(skl, nm, "auto", "najbolje", "IVANA")["id"], "IVANA")
    N.postavi_status(skl, nid, "skladiste", "IVANA"); N.postavi_status(skl, nid, "pila_nesting", "IVANA")
    lst = c.get("/api/skladiste/izdavanje").json()
    assert [y["nalog_materijal_id"] for y in lst] == [nm]
    assert c.post("/api/skladiste/izdaj", json=dict(nm=nm, tko="SKLADISTAR")).json()["izdano"] == 1
    assert c.get("/api/skladiste/izdavanje").json() == []
    A._veza = None


def test_ekran_skladistara():
    import os
    web = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hub", "web")
    js = open(os.path.join(web, "ekrani.js"), encoding="utf-8").read()
    for x in ("E.skladistar", "E.restl", "/api/skladiste/izdavanje", "/api/skladiste/izdaj", "Skeniraj QR", "Kupac ga je ostavio nama",
              "Potvrdi i zalijepi QR", "Ispravi mjeru", "Otpiši"):
        assert x in js, x
