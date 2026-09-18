# -*- coding: utf-8 -*-
"""Warehouse kao pogled (D-64) + rezervacije i potrebe (D-42/4, D-42/5), status Skladište (D-35), restl kao prijedlog iz sheme (D-64/3).
Sintetički: nalog POD 800×560×2 + BOK 400×300 na IV000090 (1 ploča, ostatak koristan), Winstore 3 ploče W908ST2-18, Regal traka lažirana."""
import io
import json
import pytest

from hub.nalozi import nalozi as N, optimiziraj as OP
from hub.skladiste import pogled as SK, ploce as PL, restlovi as RS, trake as TR
from tests.test_nalozi import baza  # noqa: F401
from tests.test_obracun_ponuda import baza_o  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog


@pytest.fixture
def skl(baza_o, monkeypatch):
    b = baza_o
    b.execute("INSERT INTO winstore_ploca (kod, materijal_kod, opis, L, W, debljina, god, kom_ukupno, kom_interno, kom_eksterno, drop_ploca, izvoz, materijal_id) "
              "SELECT 'W908ST2-18-2800-2070', 'W908ST2-18', 'IVERAL BIJELI NK', 2800, 2070, 18, 0, 3, 3, 0, 0, '16092026.XML', id FROM materijal WHERE pantheon_ident = 'IV000090'")
    b.execute("INSERT INTO winstore_ploca (kod, materijal_kod, opis, L, W, debljina, god, kom_ukupno, kom_interno, kom_eksterno, drop_ploca, izvoz, materijal_id) "
              "SELECT 'W908ST2-18-1200-800', 'W908ST2-18', 'IVERAL BIJELI NK', 1200, 800, 18, 0, 2, 2, 0, 1, '16092026.XML', id FROM materijal WHERE pantheon_ident = 'IV000090'")
    b.commit()
    OP.AUTO_POTVRDA = False

    class _Odg(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False
    stanje = {"rev": 3, "stanje": {"lok": {"TR000168": "R2-04-B"}, "q": {"TR000168": {"m": 2.0, "mt": "2026-09-16 07:00"}}}}
    monkeypatch.setattr(TR.urllib.request, "urlopen", lambda url, timeout=2.0: _Odg(json.dumps(stanje).encode("utf-8")))
    TR.ocisti_kes()
    yield b
    TR.ocisti_kes()


def _mid(b, ident="IV000090"):
    return b.execute("SELECT id FROM materijal WHERE pantheon_ident = ?", (ident,)).fetchone()[0]


def test_ploce_pogled_nad_winstoreom(skl):
    mid = _mid(skl)
    s = PL.stanje(skl, ident="IV000090")
    assert len(s) == 1 and s[0]["kom"] == 3 and s[0]["drop_kom"] == 2 and s[0]["winstore_kod"] == "W908ST2-18" and len(s[0]["kodovi"]) == 2
    assert PL.kom(skl, mid) == 3 and PL.lokacija(skl, mid) == "W908ST2-18"
    st = SK.stanje_materijala(skl, mid)
    assert st["ploce"] == dict(fizicko=3, rezervirano=0.0, naruceno=0.0, raspolozivo=3.0, lokacija="W908ST2-18", drop=2, izvoz="16092026.XML")
    assert st["restlovi"]["kom"] == 0


def test_potrebe_provjera_rezervacija_i_prijedlog_restla(skl):
    nid, nm, e1, e2 = _nalog(skl, status="potvrdjeno")
    # bez potvrđenog slaganja: broj ploča nepoznat, trake poznate
    p = SK.potrebe_naloga(skl, nid)[0]
    assert p["ploce"] is None and "nije potvrđena" in p["upozorenje"]
    t = list(p["trake"].values())[0]
    assert t["ident"] == "TR000168" and abs(t["metri_tocno"] - 2.2) < 1e-6 and t["metri"] == 3        # (800×2 + 400) × 1,10 = 2,2 → 3 m
    OP.potvrdi(skl, OP.predlozi(skl, nm, "auto", "najbolje", "IVANA")["id"], "IVANA")
    p = SK.potrebe_naloga(skl, nid)[0]
    assert p["ploce"] == 1 and p["potvrdjena"] and p["najveci"] == (800, 560)
    pr = SK.provjera_naloga(skl, nid)
    m = pr["materijali"][0]
    assert m["manjak"] == 0 and m["stanje"]["ploce"]["raspolozivo"] == 3 and m["restl_kandidati"] == []
    tr = list(m["trake"].values())[0]
    assert tr["na_roli"] == 2.0 and tr["pretinac"] == "R2-04-B" and tr["manjak"] == 1.0               # treba 3 m, na roli 2
    assert any("traka TR000168" in u for u in pr["upozorenja"]) and pr["za_nabavu"][0]["jm"] == "M" and not pr["ok"]
    # trake naloga zbrojene po identu — vlastiti redak kao i ploče (Igor, 18. 9.)
    t0 = pr["trake"][0]
    assert len(pr["trake"]) == 1 and t0["ident"] == "TR000168" and t0["potrebno"] == 3 and t0["na_roli"] == 2.0
    assert t0["manjak"] == 1.0 and t0["pretinac"] == "R2-04-B" and t0["materijali"] == [pr["materijali"][0]["naziv"]]
    assert [(z["ident"], z["jm"]) for z in pr["za_nabavu"]] == [("TR000168", "M")]      # traka se u nabavu upisuje jednom, ne po materijalu
    # status Skladište (D-35): Hub rezervira ploču, predloži restl iz sheme i vrati provjeru
    d = N.postavi_status(skl, nid, "skladiste", "IVANA")
    assert d["skladiste"]["materijali"][0]["rezervirano_ovaj"] == 1
    rez = skl.execute("SELECT * FROM rezervacija WHERE nalog_materijal_id = ? AND status = 'rezervirano'", (nm,)).fetchall()
    assert len(rez) == 1 and rez[0]["winstore_kod"] == "W908ST2-18" and rez[0]["kom"] == 1
    pri = RS.prijedlozi(skl, nid)
    assert len(pri) == 1 and pri[0]["oznaka"] == "R0001" and pri[0]["status"] == "prijedlog" and pri[0]["ident"] == "IV000090"
    assert pri[0]["L"] >= 2000 and pri[0]["m2"] >= 1.0 and "ostatak 1/1" in pri[0]["napomena"]
    assert RS.stanje(skl, ident="IV000090") == []                                                          # prijedlog nije na stanju
    # drugi nalog istog materijala vidi rezervaciju prvog; s 3 ploče na stanju raspoloživo 2
    nid2, nm2, _, _ = _nalog(skl, projekt="DRUGI", status="potvrdjeno")
    OP.potvrdi(skl, OP.predlozi(skl, nm2, "auto", "najbolje", "IVANA")["id"], "IVANA")
    m2 = SK.provjera_naloga(skl, nid2)["materijali"][0]
    assert m2["stanje"]["ploce"]["rezervirano"] == 1 and m2["stanje"]["ploce"]["raspolozivo"] == 2 and m2["manjak"] == 0
    skl.execute("UPDATE winstore_ploca SET kom_ukupno = 1 WHERE kod = 'W908ST2-18-2800-2070'"); skl.commit()
    m2 = SK.provjera_naloga(skl, nid2)["materijali"][0]
    assert m2["stanje"]["ploce"]["raspolozivo"] == 0 and m2["manjak"] == 1
    # naručeno vraća raspoloživo (otvorena narudžbenica)
    skl.execute("INSERT INTO narudzbenica (broj, dobavljac, datum, status) VALUES ('N-2026-001', 'IVERPAN', '2026-09-16', 'poslana')")
    skl.execute("INSERT INTO narudzbenica_st (narudzbenica_id, pantheon_ident, kom, jm) VALUES (1, 'IV000090', 5, 'KOM')"); skl.commit()
    m2 = SK.provjera_naloga(skl, nid2)["materijali"][0]
    assert m2["stanje"]["ploce"]["naruceno"] == 5 and m2["manjak"] == 0
    # potreba preko svih potvrđenih naloga (D-42/5): 2 ploče, fizičko 1, naručeno 5 → manjak 0; trake 6 m vs 2 na roli
    u = SK.potrebe_ukupno(skl)
    mm = u["materijali"][0]
    assert mm["potrebno"] == 2 and mm["fizicko"] == 1 and mm["rezervirano"] == 1 and mm["naruceno"] == 5 and mm["manjak"] == 0 and len(mm["nalozi"]) == 2
    assert u["trake"][0]["potrebno"] == 6 and u["trake"][0]["na_roli"] == 2.0 and u["trake"][0]["manjak"] == 4.0 and u["nepoznato"] == []
    skl.execute("UPDATE narudzbenica SET status = 'zaprimljena'"); skl.commit()
    assert SK.potrebe_ukupno(skl)["materijali"][0]["manjak"] == 1
    # skladištar potvrdi prijedlog restla → na stanju; na stroj = izdano; zatvoren = potrošeno
    r = RS.potvrdi_restl(skl, "R0001", "SKLADISTAR", lokacija="B004")
    assert r["status"] == "slobodan" and r["lokacija"] == "B004" and r["potvrdio"] == "SKLADISTAR"
    assert RS.stanje(skl, ident="IV000090")[0]["kom"] == 1 and RS.lokacija(skl, "R0001") == "B004"
    N.postavi_status(skl, nid, "pila_nesting", "IVANA")
    assert skl.execute("SELECT status FROM rezervacija WHERE nalog_materijal_id = ?", (nm,)).fetchone()[0] == "izdano"
    assert SK.stanje_materijala(skl, _mid(skl))["ploce"]["rezervirano"] == 1                              # izdano još drži broj do zatvaranja
    N.postavi_status(skl, nid, "proizvodnja", "IVANA"); N.postavi_status(skl, nid, "zatvoren", "IVANA")
    assert skl.execute("SELECT status FROM rezervacija WHERE nalog_materijal_id = ?", (nm,)).fetchone()[0] == "potroseno"
    assert SK.stanje_materijala(skl, _mid(skl))["ploce"]["rezervirano"] == 0
    # natrag iz skladišta u potvrđeno oslobađa
    N.postavi_status(skl, nid2, "skladiste", "IVANA")
    assert skl.execute("SELECT COUNT(*) FROM rezervacija WHERE nalog_materijal_id = ? AND status = 'rezervirano'", (nm2,)).fetchone()[0] == 1
    N.postavi_status(skl, nid2, "potvrdjeno", "IVANA")
    assert skl.execute("SELECT COUNT(*) FROM rezervacija WHERE nalog_materijal_id = ? AND status = 'rezervirano'", (nm2,)).fetchone()[0] == 0
    # ponovni ulazak u skladište s istim slaganjem zadržava isti prijedlog restla (idempotentno); novo slaganje ga zamjenjuje
    N.postavi_status(skl, nid2, "skladiste", "IVANA"); N.postavi_status(skl, nid2, "potvrdjeno", "IVANA"); N.postavi_status(skl, nid2, "skladiste", "IVANA")
    assert [x["oznaka"] for x in RS.prijedlozi(skl, nid2)] == ["R0002"] and skl.execute("SELECT COUNT(*) FROM restl WHERE nalog_materijal_id = ?", (nm2,)).fetchone()[0] == 1
    N.postavi_status(skl, nid2, "potvrdjeno", "IVANA"); N.postavi_status(skl, nid2, "ponuda", "IVANA")
    N.uredi_element(skl, [e for e in N.elementi_konacni(skl, nm2)][0]["id"], "TEST", kom=3)
    N.postavi_status(skl, nid2, "potvrdjeno", "IVANA")
    OP.potvrdi(skl, OP.predlozi(skl, nm2, "auto", "najbolje", "IVANA")["id"], "IVANA")
    N.postavi_status(skl, nid2, "skladiste", "IVANA")
    assert [x["oznaka"] for x in RS.prijedlozi(skl, nid2)] == ["R0003"] and skl.execute("SELECT status FROM restl WHERE oznaka = 'R0002'").fetchone()[0] == "otpisan"


def test_restl_za_nalog_na_restlu(skl):
    mid = _mid(skl)
    r1 = RS.novi_restl(skl, mid, 1500, 900, "SKLADISTAR", lokacija="A001", potvrdio="SKLADISTAR")
    r2 = RS.novi_restl(skl, "IV000090", 700, 600, "SKLADISTAR", lokacija="A002", potvrdio="SKLADISTAR")
    assert r1["oznaka"] == "R0001" and r2["oznaka"] == "R0002" and r1["status"] == "slobodan" and r1["razina"] == "ident"
    assert [k["oznaka"] for k in RS.kandidati(skl, mid, 800, 560)] == ["R0001"]                # 700×600 ne prima 800×560
    assert [k["oznaka"] for k in RS.kandidati(skl, mid, 600, 650)] == ["R0001", "R0002"]       # okrenuto stane
    nid, nm, e1, e2 = _nalog(skl, status="potvrdjeno")
    skl.execute("UPDATE nalog_materijal SET ploca_L = 1500, ploca_W = 900 WHERE id = ?", (nm,)); skl.commit()
    pr = SK.provjera_naloga(skl, nid)["materijali"][0]
    assert pr["na_restlu"] and [k["oznaka"] for k in pr["restl_kandidati"]] == ["R0001"] and pr["manjak"] == 0
    with pytest.raises(ValueError, match="nije slobodan|drugi ident|nema"):
        RS.rezerviraj(skl, nm, "R0009", "IVANA")
    pr = SK.rezerviraj_nalog(skl, nid, "IVANA", restlovi={nm: r1["id"]})
    assert pr["materijali"][0]["restl_rezerviran"][0]["oznaka"] == "R0001" and RS.restl(skl, "R0001")["status"] == "rezerviran"
    with pytest.raises(ValueError, match="nije slobodan"):
        RS.rezerviraj(skl, nm, "R0001", "IVANA")
    assert skl.execute("SELECT COUNT(*) FROM rezervacija WHERE nalog_materijal_id = ? AND restl_id IS NOT NULL AND status = 'rezervirano'", (nm,)).fetchone()[0] == 1
    assert SK.oslobodi_nalog(skl, nid, "IVANA") == 1 and RS.restl(skl, "R0001")["status"] == "slobodan"
    SK.rezerviraj_nalog(skl, nid, "IVANA", restlovi={nm: r1["id"]})
    N.postavi_status(skl, nid, "skladiste", "IVANA"); N.postavi_status(skl, nid, "pila_nesting", "IVANA")
    assert RS.restl(skl, "R0001")["status"] == "rezerviran"                                  # restl izdaje skladištar, ne automat (D-95)
    ceka = SK.ceka_izdavanje(skl, nid)
    assert len(ceka) == 1 and [x["oznaka"] for x in ceka[0]["restlovi"]] == ["R0001"]
    assert SK.izdaj_materijal(skl, nm, "SKLADISTAR") == 1
    r = RS.restl(skl, "R0001")
    assert r["status"] == "potrosen" and r["nalog_izlaz"] and RS.stanje(skl, ident="IV000090")[0]["kom"] == 1        # ostaje R0002
    with pytest.raises(ValueError, match="je potrosen"):
        RS.potvrdi_restl(skl, "R0001", "SKLADISTAR")
    o = RS.odbaci_restl(skl, "R0002", "SKLADISTAR", razlog="puknuo")
    assert o["status"] == "otpisan" and "puknuo" in o["napomena"] and RS.stanje(skl, ident="IV000090") == []
    s = RS.sazetak(skl)
    assert s["po_statusu"] == {"potrosen": 1, "otpisan": 1}


def test_api_skladiste(skl, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    monkeypatch.setenv("HUB_DB", str(skl.dir / "hub.db"))
    A._veza = None
    nid, nm, e1, e2 = _nalog(skl, status="potvrdjeno")
    OP.potvrdi(skl, OP.predlozi(skl, nm, "auto", "najbolje", "IVANA")["id"], "IVANA")
    c = TestClient(A.app, raise_server_exceptions=False)
    try:
        r = c.get("/api/skladiste/stanje").json()
        assert r["broj"] == 1 and r["materijali"][0]["ident"] == "IV000090" and r["materijali"][0]["ploce"]["fizicko"] == 3
        r = c.get("/api/nalog/%d/skladiste" % nid).json()
        assert r["materijali"][0]["ploce"] == 1 and r["materijali"][0]["manjak"] == 0 and r["za_nabavu"][0]["ident"] == "TR000168"
        r = c.post("/api/nalog/%d/skladiste/rezerviraj" % nid, json=dict(tko="IVANA")).json()
        assert r["materijali"][0]["rezervirano_ovaj"] == 1
        r = c.get("/api/skladiste/prijedlozi", params=dict(nalog=nid)).json()
        assert r["broj"] == 1 and r["prijedlozi"][0]["oznaka"] == "R0001"
        r = c.post("/api/skladiste/restlovi/R0001/potvrdi", json=dict(tko="SKLADISTAR", lokacija="C003")).json()
        assert r["status"] == "slobodan" and r["lokacija"] == "C003"
        r = c.post("/api/skladiste/restlovi", json=dict(ident="IV000090", L=900, W=700, lokacija="C004", tko="SKLADISTAR")).json()
        assert r["oznaka"] == "R0002" and r["status"] == "slobodan"
        assert c.post("/api/skladiste/restlovi", json=dict(ident="IV999999", L=900, W=700)).status_code == 400
        r = c.get("/api/skladiste/restlovi", params=dict(ident="IV000090")).json()
        assert r["broj"] == 2
        r = c.get("/api/skladiste/materijal/%d" % _mid(skl)).json()
        assert r["restlovi"]["kom"] == 2 and len(r["rezervacije"]) == 1 and r["rezervacije"][0]["nalog"]
        r = c.get("/api/skladiste/potrebe").json()
        assert r["materijali"][0]["potrebno"] == 1 and r["trake"][0]["manjak"] == 1.0
        assert c.get("/api/skladiste/trake", params=dict(ident="TR000168")).json()["pretinac"] == "R2-04-B"
        assert c.get("/api/skladiste/restlovi/sazetak").json()["ukupno"] == 2
        r = c.post("/api/nalog/%d/skladiste/oslobodi" % nid, json=dict(tko="IVANA")).json()
        assert r["oslobodjeno"] == 1
    finally:
        A._veza = None


# ------------------------------------------------------------------ B. stvarni podaci: HUMER kupčev PPW + Winstore XML + evidencija restlova
from tests.test_sifrarnik import DATA, WIN_XML, stvarni, stvarna_baza   # noqa: E402,F401
from tests.test_restlovi import XLSM                                     # noqa: E402
import os                                                                # noqa: E402


@stvarni
def test_stvarni_humer_skladiste(stvarna_baza):
    from hub.nalozi import provjera as PR
    if not os.path.exists(WIN_XML) or not os.path.exists(XLSM):
        pytest.skip("nema Winstore XML ili RESTLOVI_V7.xlsm")
    b = stvarna_baza
    RS.uvezi_excel(b, XLSM, "TEST")
    humer = [m for m in PR.mape_naloga(DATA) if m["mapa"] == "_HUMER_OMIS"][0]
    nid, uk = PR._uvezi(b, "HUMER_OMIS", humer["kupac"], "kupac_ppw")
    for s in ("ponuda", "potvrdjeno"):
        N.postavi_status(b, nid, s, "TEST")
    for nm in b.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? ORDER BY rb", (nid,)).fetchall():
        m = N.materijal_naloga(b, nm["id"])
        if m["vrsta"] in ("RP", "ZO"):
            continue
        OP.potvrdi(b, OP.predlozi(b, nm["id"], "auto", "brzo", "TEST")["id"], "TEST")
    pr = SK.provjera_naloga(b, nid)
    mats = {m["ident"]: m for m in pr["materijali"]}
    assert len(mats) == 5
    bij = mats["IV000090"]                                                     # IV BIJELI NK 18: W908ST2-18 u Winstoreu, restlovi u evidenciji
    assert bij["ploce"] and bij["ploce"] >= 8 and bij["stanje"]["ploce"]["fizicko"] > 0 and bij["stanje"]["ploce"]["lokacija"] == "W908ST2-18"
    assert bij["stanje"]["restlovi"]["kom"] >= 1 and isinstance(bij["restl_kandidati"], list)
    assert all(m["ploce"] for m in mats.values() if m["vrsta"] not in ("RP", "ZO")) and pr["upozorenja"] is not None
    d = N.postavi_status(b, nid, "skladiste", "TEST")
    assert d["skladiste"]["materijali"][0]["rezervirano_ovaj"] == mats[d["skladiste"]["materijali"][0]["ident"]]["ploce"]
    pri = RS.prijedlozi(b, nid)
    assert all(min(p["L"], p["W"]) >= 150 and (p["m2"] >= 0.35 or max(p["L"], p["W"]) >= 2000) for p in pri)   # prag čuvanja restla (D-95)
    u = SK.potrebe_ukupno(b)
    assert u["materijali"] and sum(m["potrebno"] for m in u["materijali"]) == sum(m["ploce"] or 0 for m in mats.values())
    assert u["trake"] and all(t["potrebno"] > 0 for t in u["trake"])
    PR.obrisi_provjere(b)
