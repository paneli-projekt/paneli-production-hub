# -*- coding: utf-8 -*-
"""API kostur (hub/api/app.py) na sintetičkom šifrarniku iz test_sifrarnik.py — bez pokretanja poslužitelja (TestClient)."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from hub import db
from hub.sifrarnici import pantheon, winstore, aliasi, prepoznaj as P
from hub.api import app as A
from tests.test_sifrarnik import PH_IDENTI, WINSTORE_XML


@pytest.fixture
def klijent(tmp_path, monkeypatch):
    (tmp_path / "ph.csv").write_text(PH_IDENTI, encoding="utf-8")
    (tmp_path / "w.XML").write_text(WINSTORE_XML, encoding="utf-8")
    monkeypatch.setenv("HUB_DB", str(tmp_path / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    c = A.veza()
    pantheon.uvezi_pantheon(c, str(tmp_path / "ph.csv"), "TEST")
    aliasi.upisi_potvrdjene(c, "TEST")
    winstore.uvezi_winstore(c, str(tmp_path / "w.XML"), "TEST")
    yield TestClient(A.app)
    c.close()
    A._veza = None
    P.ocisti_kes()


def test_zdravlje(klijent):
    z = klijent.get("/api/zdravlje").json()
    assert z["ok"] and z["materijala"] == 13 and z["traka"] == 10 and z["zadanih_traka"] == 3


def test_pretraga(klijent):
    r = klijent.get("/api/sifrarnik/materijali", params=dict(q="bijeli nk 18")).json()
    assert r["broj"] == 1 and r["materijali"][0]["ident"] == "IV000090" and r["materijali"][0]["winstore_kod"] == "W908ST2-18"
    r = klijent.get("/api/sifrarnik/materijali", params=dict(q="PVC_CRNI_MAT_18")).json()        # alias iz ponude
    assert r["materijali"][0]["pogodak"] == "alias" and r["materijali"][0]["ident"] == "IV000671"
    r = klijent.get("/api/sifrarnik/materijali", params=dict(q="W908ST2")).json()
    assert r["materijali"][0]["ident"] == "IV000090"
    r = klijent.get("/api/sifrarnik/materijali", params=dict(q="", vrsta="RP")).json()
    assert {m["ident"] for m in r["materijali"]} == {"RP000001", "RP000102"}
    d = klijent.get("/api/sifrarnik/materijali/IV000090").json()
    assert d["naziv_kratki"] == "IV BIJELI NK 18" and [t["klasa"] for t in d["zadane_trake"]] == ["0,5/22", "1/22", "2/22"]
    assert sum(w["kom_ukupno"] for w in d["winstore"] if not w["drop_ploca"]) == 12
    assert klijent.get("/api/sifrarnik/materijali/IV999999").status_code == 404
    r = klijent.get("/api/sifrarnik/trake", params=dict(q="bijeli", klasa="1/22")).json()
    assert [t["ident"] for t in r["trake"]] == ["TR000168"] and r["trake"][0]["usluga"] == "US000011"


def test_prepoznaj_i_potvrda(klijent):
    r = klijent.get("/api/sifrarnik/prepoznaj", params=dict(naziv="IV_BIJELI_NK_18_MM")).json()
    assert r["razina"] == "naziv" and r["ident"] == "IV000090" and r["siguran"]
    r = klijent.get("/api/sifrarnik/prepoznaj", params=dict(naziv="XXX", kod="VSM2-18")).json()
    assert (r["razina"], r["ident"]) == ("winstore", "IV000671")
    r = klijent.get("/api/sifrarnik/prepoznaj", params=dict(naziv="IV_SIVI_TAMNI_19")).json()
    assert (r["razina"], r["ident"]) == ("alias", "IV001168")                  # alias iz ponude (aliasi.ALIASI_MATERIJALA)
    r = klijent.get("/api/sifrarnik/prepoznaj", params=dict(naziv="IV SIVI TAMNI 19mm")).json()
    assert r["razina"] == "za_potvrdu" and len(r["kandidati"]) == 2             # MN ili PE — čovjek odlučuje
    p = klijent.post("/api/sifrarnik/alias", json=dict(alias="IV SIVI TAMNI 19mm", ident="IV001168", tko="IVANA", izvor="ponuda 26-010-002924")).json()
    assert p["ok"]
    r = klijent.get("/api/sifrarnik/prepoznaj", params=dict(naziv="iv sivi tamni 19MM")).json()
    assert (r["razina"], r["ident"]) == ("alias", "IV001168")
    assert klijent.post("/api/sifrarnik/alias", json=dict(alias="X", ident="IV999999")).status_code == 404
    t = klijent.get("/api/sifrarnik/prepoznaj-traku", params=dict(oznaka="ABS-ISTI", materijal="IV000090")).json()
    assert (t["razina"], t["ident"], t["klasa"], t["usluga"]) == ("zadana", "TR000168", "1/22", "US000011")
    t = klijent.get("/api/sifrarnik/prepoznaj-traku", params=dict(oznaka="MEL-ISTI", materijal="IV000090")).json()
    assert (t["ident"], t["usluga"]) == ("TR000017", "US000003")
    t = klijent.get("/api/sifrarnik/prepoznaj-traku", params=dict(oznaka="MEL CRNA NK", materijal="IV000090")).json()
    assert not t["siguran"]
    p = klijent.post("/api/sifrarnik/alias-traka", json=dict(oznaka="MEL CRNA NK", traka="TR000100", materijal="IV000090", klasa="0,5/22", tko="IVANA")).json()
    assert p["ok"] and p["klasa"] == "0,5/22"
    t = klijent.get("/api/sifrarnik/prepoznaj-traku", params=dict(oznaka="MEL CRNA NK", materijal="IV000090")).json()
    assert (t["razina"], t["ident"]) == ("alias", "TR000100")
    z = klijent.get("/api/zdravlje").json()
    assert z["aliasa"] == 6 and z["aliasa_traka"] == 1        # 5 iz ponuda + 1 potvrda; TR001254 (taverna) nije u sintetičkom skupu


def test_web_ekrani_serviraju_se(klijent):
    """Web ekrani (hub/web) idu s istog poslužitelja: / = index.html, /static/app.js i ekrani.js postoje i registriraju sve ekrane."""
    r = klijent.get("/")
    assert r.status_code == 200 and "/static/app.js" in r.text and "Hub.start()" in r.text
    js = klijent.get("/static/app.js").text + klijent.get("/static/ekrani.js").text
    for e in ("ekrani.nalozi", "ekrani.nalog_unos", "E.nalog_obracun", "E.nalog_skladiste", "E.nalog_pila", "E.skladiste", "E.nabava", "E.sifrarnik", "E.postavke"):
        assert e in js, e
    import re
    assert not re.search(r"D-\d\d", js + klijent.get("/static/app.css").text)     # na ekranu (ni u kodu ekrana) nema oznaka odluka


def test_regal_traka_neuspjeh_se_pamti(klijent, monkeypatch):
    """Kad Regal traka ne odgovara, neuspjeh se pamti 60 s — ekran skladišta ne čeka timeout po svakom identu."""
    from hub.skladiste import trake as RT
    import hub.api.app as A
    pozivi = []
    def lazni(url, timeout=2.0):
        pozivi.append(url); raise OSError("nema veze")
    monkeypatch.setattr(RT.urllib.request, "urlopen", lazni)
    RT.ocisti_kes()
    c = A.veza()
    assert RT.stanje(c, "TR000168")["dostupno"] is False and RT.metri(c, "TR000017") is None and RT.pretinac(c, "TR000016") is None
    assert len(pozivi) == 1
    RT.ocisti_kes()
