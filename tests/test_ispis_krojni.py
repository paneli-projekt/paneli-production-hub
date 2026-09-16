# -*- coding: utf-8 -*-
"""D-76 / D-77 (korak 5b, drugi dio): krojni nacrt PDF iz potvrđenog slaganja — listovi + statistika, identi materijala i traka,
pretinac iz Regal trake (prilagodnik s lažnim poslužiteljem), oznaka PRIJEDLOG bez potvrde, API."""
import io
import json
import os
import pytest

from hub.nalozi import nalozi as N, optimiziraj as OP
from hub.ispis import krojni as KR
from hub.skladiste import trake as RT
from tests.test_nalozi import baza  # noqa: F401
from tests.test_obracun_ponuda import baza_o  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog


def _pdf_stranica(put):
    b = open(put, "rb").read()
    return b.count(b"/Type /Page") - b.count(b"/Type /Pages"), len(b)


def test_krojni_nacrt(baza_o, tmp_path, monkeypatch):
    pytest.importorskip("reportlab")
    nid, nm, e1, e2 = _nalog(baza_o, status="ponuda")
    N.uredi_element(baza_o, e2["id"], "TEST", napomena="CNC 2xFI35")
    OP.AUTO_POTVRDA = False
    # bez potvrde: nacrt postoji, ali nosi PRIJEDLOG
    r0 = KR.napravi(baza_o, nid, str(tmp_path), None, None, "TEST", zabiljezi=False)
    assert r0["potvrdjeno"] is False and os.path.exists(r0["put"])
    p = OP.predlozi(baza_o, nm, "auto", "najbolje", "IVANA")
    OP.potvrdi(baza_o, p["id"], "IVANA")
    # lažna Regal traka: pretinac i metri po identu
    class _Odg(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False
    stanje = {"rev": 3, "stanje": {"lok": {"TR000168": "R2-04-B"}, "q": {"TR000168": {"m": 87.5, "mt": "2026-09-16 07:00"}}}}
    monkeypatch.setattr(RT.urllib.request, "urlopen", lambda url, timeout=2.0: _Odg(json.dumps(stanje).encode("utf-8")))
    RT.ocisti_kes()
    d = KR.podaci(baza_o, nm)
    assert d["slaganje"]["potvrdjeno"] and d["slaganje"]["potvrdio"] and d["statistika"]["ploca"] == 1
    assert d["materijal"]["ident"] == "IV000090" and d["elementi"][0]["oznake_abs"] == "1DA" and d["elementi"][0]["oznake_mel"] == "" and d["elementi"][1]["napomena"] == "CNC 2xFI35"
    t = d["trake"][0]
    assert t["ident"] == "TR000168" and t["pretinac"] == "R2-04-B" and t["preostalo"] == 87.5 and abs(t["metri_tocno"] - 2.0) < 1e-6 and abs(t["metri"] - 2.2) < 1e-6
    assert d["listovi"][0]["komadi"] == 3 and d["listovi"][0]["ostatak"]                  # 3 komada na jednoj ploči, ostatak koristan
    r = KR.napravi(baza_o, nid, str(tmp_path), None, None, "IVANA")
    assert r["potvrdjeno"] and r["listova"] == 1 and r["stranica"] == 2 and r["put"].endswith(".pdf")
    stranica, velicina = _pdf_stranica(r["put"])
    assert stranica == 2 and velicina > 8000
    assert baza_o.execute("SELECT COUNT(*) FROM dokument WHERE nalog_id = ? AND vrsta = 'pdf_krojni'", (nid,)).fetchone()[0] == 1
    # jedan materijal + zadani prijedlog (oid) umjesto potvrđenog
    alt = OP.predlozi(baza_o, nm, "poprecno", "brzo", "IVANA")
    r2 = KR.napravi(baza_o, nid, str(tmp_path), nm, alt["id"], "IVANA", zabiljezi=False)
    assert r2["potvrdjeno"] is False and "IV_BIJELI" in os.path.basename(r2["put"])
    # Regal traka nedostupna → pretinac None, ništa ne pada
    monkeypatch.setattr(RT.urllib.request, "urlopen", lambda url, timeout=2.0: (_ for _ in ()).throw(OSError("nema veze")))
    RT.ocisti_kes()
    assert RT.pretinac(baza_o, "TR000168") is None and KR.podaci(baza_o, nm)["trake"][0]["pretinac"] is None


def test_api_ispis(baza_o, monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("reportlab")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    from hub.sifrarnici import prepoznaj as P
    monkeypatch.setenv("HUB_DB", str(baza_o.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    nid, nm, e1, e2 = _nalog(baza_o, status="ponuda")
    c = TestClient(A.app, raise_server_exceptions=False)
    r = c.get("/api/nalog/%d/ispis/krojni.pdf?mapa=%s" % (nid, tmp_path))
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/pdf") and r.content[:4] == b"%PDF"
    r = c.post("/api/nalog/%d/ispis/krojni.pdf" % nid, json=dict(mapa=str(tmp_path), tko="IVANA"))
    assert r.status_code == 200 and r.json()["listova"] >= 1
    assert c.get("/api/nalog/9999/ispis/krojni.pdf").status_code in (400, 404)


def test_naziv_ide_na_etiketu_kad_nema_napomene(baza_o, tmp_path):
    """Kupčev PPW piše napomenu u 2. polje CPW-a (naziv elementa) — na etiketu (CPO napomena) mora ići kad element nema zasebnu napomenu."""
    from hub.nalozi import export_pila as EP
    from hub.formati import cpo_rw
    nid, nm, e1, e2 = _nalog(baza_o, status="ponuda")
    N.uredi_element(baza_o, e1["id"], "TEST", naziv="CNC SKICA nut za golu")
    N.uredi_element(baza_o, e2["id"], "TEST", naziv="BOK", napomena="NUT DUZA")
    els = {e["element_id"]: e for e in N.elementi_za_export(baza_o, nid)}
    assert els[e1["id"]]["napomena"] == "CNC SKICA nut " and els[e2["id"]]["napomena"] == "NUT DUZA"      # 14 znakova (D-38), napomena ima prednost
    baza_o.execute("UPDATE nalog SET status = 'potvrdjeno' WHERE id = ?", (nid,)); baza_o.commit()
    r = EP.izvezi(baza_o, nid, str(tmp_path), "TEST")
    d = cpo_rw.parse(r["paketi"][0]["cpo"])
    assert sorted(o["note"].strip() for o in d["ord"]) == ["CNC SKICA nut", "NUT DUZA"] and d["prt"][0]["note"].strip() in ("CNC SKICA nut", "NUT DUZA")
