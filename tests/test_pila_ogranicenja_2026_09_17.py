# -*- coding: utf-8 -*-
"""D-91 (opcija B, Igor 17. 9. 2026.): zadano slaganje = ono što pila realno reže uz ograničenja iz postavki (razine rezanja, širine u traci,
najmanji komad 4. razine, miješana orijentacija); Hubov minimum bez ograničenja ostaje kao rezerva „hub“ s prikazanom razlikom m²."""
import pytest

from hub.optimizacija import pila_optimizator as po
from hub.nalozi import nalozi as N, optimiziraj as OP
from tests.test_nalozi import baza  # noqa: F401
from tests.test_obracun_ponuda import baza_o  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog

DIJ = [(1, 600, 1200, 4), (2, 450, 800, 6), (3, 300, 700, 5), (4, 550, 350, 8), (5, 200, 900, 3), (6, 400, 400, 7)]
OGR = dict(max_razina=3, max_sirina=2, min_komad_4=0, mijesana=0)


def _razine(sheets):
    return max(r for s in sheets for r, _, _, _ in po.sheme_u_cuts(s))


def test_dopusteno_prepoznaje_prekrsaje():
    # čisto trake: 1 širina, 2 razine → dopušteno i uz najstrože ograničenje
    sh = po.slozi_trake(DIJ, (2800, 2070), 10, 5.0, False, "trake")
    assert po.dopusteno(sh, DIJ, dict(max_razina=2, max_sirina=1, min_komad_4=0, mijesana=0))[0]
    assert _razine(sh) <= 2
    # slobodno uzdužno slaganje ima više širina u traci / 4. razinu → razlozi su ispisani
    sh = po.slozi(DIJ, (2800, 2070), 10, 5.0, False, "uzduzno", "w", True)
    ok, razlozi = po.dopusteno(sh, DIJ, dict(max_razina=2, max_sirina=1, min_komad_4=0, mijesana=0))
    assert not ok and razlozi and all(isinstance(r, str) for r in razlozi)
    # miješani smjer po ploči → nije dopušteno bez „mijesana“
    a = po.slozi(DIJ, (2800, 2070), 10, 5.0, False, "uzduzno")
    b = po.slozi(DIJ, (2800, 2070), 10, 5.0, False, "poprecno")
    ok, razlozi = po.dopusteno([a[0], b[0]], DIJ, OGR)
    assert not ok and any("smjer" in r for r in razlozi)
    assert po.dopusteno([a[0], b[0]], DIJ, dict(OGR, mijesana=1))[0] or _razine([a[0], b[0]]) > 3


def test_slozi_uz_ogranicenja_postuje_ih():
    for mr, ms in ((2, 1), (3, 2), (3, 1), (4, 2)):
        ogr = dict(max_razina=mr, max_sirina=ms, min_komad_4=150, mijesana=0)
        for nacin in ("uzduzno", "poprecno"):
            for fn in (lambda: po.slozi(DIJ, (2800, 2070), 10, 5.0, False, nacin, "w", True, ogr),
                       lambda: po.slozi_trake(DIJ, (2800, 2070), 10, 5.0, False, nacin, True, 3, ogr)):
                sh = fn()
                ok, razlozi = po.dopusteno(sh, DIJ, ogr)
                assert ok, (mr, ms, nacin, razlozi)
                assert _razine(sh) <= mr


def test_najbolje_s_ogranicenjima_vraca_dopusteno_i_sve_kandidate():
    sh0, oc0, opis0, kand0 = po.najbolje(DIJ, (2800, 2070), 10, 5.0, False)
    assert all(len(k) == 9 and k[8] is True for k in kand0)                     # bez ogr: 9. član uvijek True
    sh, oc, opis, kand = po.najbolje(DIJ, (2800, 2070), 10, 5.0, False, ogr=OGR)
    assert po.dopusteno(sh, DIJ, OGR)[0] and "izvan-ogranicenja" not in opis
    assert any(k[8] for k in kand) and any(not k[8] for k in kand)                # ima i dopuštenih i nedopuštenih kandidata
    assert oc["m2_naplata"] >= oc0["m2_naplata"] - 1e-9                          # ograničenje nikad ne daje manje m² od slobodnog minimuma
    najbolji_dop = min(k[0] for k in kand if k[8])
    assert abs(najbolji_dop - oc["m2_naplata"]) < 1e-9
    # s godom (orijentacija fiksna) također radi
    shg, ocg, opisg, _ = po.najbolje(DIJ, (2800, 2070), 10, 5.0, True, ogr=OGR)
    assert po.dopusteno(shg, DIJ, OGR)[0]


def test_postavke_i_nacin_hub(baza_o):
    conn = baza_o
    o = OP.ogranicenja_pile(conn)
    assert o == dict(max_razina=3, max_sirina=2, min_komad_4=0, mijesana=0)      # početne vrijednosti (Igor: 3 razine, 2 širine, bez miješane)
    conn.execute("UPDATE postavke SET vrijednost = '9' WHERE kljuc = 'pila_max_razina'")
    conn.execute("UPDATE postavke SET vrijednost = '1' WHERE kljuc = 'pila_mijesana_orijentacija'"); conn.commit()
    o = OP.ogranicenja_pile(conn)
    assert o["max_razina"] == 4 and o["mijesana"] == 1
    conn.execute("UPDATE postavke SET vrijednost = '3' WHERE kljuc = 'pila_max_razina'")
    conn.execute("UPDATE postavke SET vrijednost = '0' WHERE kljuc = 'pila_mijesana_orijentacija'"); conn.commit()
    nid, nm, e1, e2 = _nalog(conn, status="unos")
    for idx, W, L, kom in DIJ:
        N.dodaj_element(conn, nm, "TEST", L=L, W=W, kom=kom, naziv="E%d" % idx)
    conn.commit()
    a = OP.izracunaj(conn, nm, "auto", "najbolje")
    h = OP.izracunaj(conn, nm, "hub", "najbolje")
    assert a["dopusteno"] and a["napomena"] is None and a["ogranicenja"]["max_razina"] == 3
    assert h["oc"]["m2_naplata"] <= a["oc"]["m2_naplata"] + 1e-9
    assert "hub" in OP.NACINI
    # prijedlozi za ekran: auto uvijek; hub samo kad štedi m² — i tada s razlikom prema auto
    OP.pripremi_prijedloge(conn, nid, "IVANA"); conn.commit()
    pr = [x for x in OP.pregled(conn, nid) if x["nalog_materijal_id"] == nm][0]
    nacini = [x["nacin_trazen"] for x in pr["prijedlozi"]]
    assert nacini[0] == "auto"
    if h["oc"]["m2_naplata"] < a["oc"]["m2_naplata"] - 0.005:
        assert "hub" in nacini
        hp = [x for x in pr["prijedlozi"] if x["nacin_trazen"] == "hub"][0]
        assert hp["razlika_m2_prema_auto"] < 0
    else:
        assert "hub" not in nacini
    # ponovni poziv ne duplira prijedloge
    OP.pripremi_prijedloge(conn, nid, "IVANA"); conn.commit()
    pr2 = [x for x in OP.pregled(conn, nid) if x["nalog_materijal_id"] == nm][0]
    assert len(pr2["prijedlozi"]) == len(pr["prijedlozi"])
    # eksplicitni hub prijedlog kroz predlozi() i potvrda rade kao i dosad
    r = OP.predlozi(conn, nm, "hub", "brzo", "IVANA")
    assert r["nacin_trazen"] == "hub" and r["status"] == "prijedlog"
    assert OP.potvrdi(conn, r["id"], "IVANA")["status"] == "potvrdjeno"


def test_api_postavke_pile(baza_o, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    from hub.sifrarnici import prepoznaj as P
    monkeypatch.setenv("HUB_DB", str(baza_o.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    c = TestClient(A.app, raise_server_exceptions=False)
    p = {x["kljuc"]: x["vrijednost"] for x in c.get("/api/postavke/optimizacija").json()}
    assert p["pila_max_razina"] == "3" and p["pila_max_sirina_u_traci"] == "2" and p["pila_mijesana_orijentacija"] == "0"
    assert c.post("/api/postavke/optimizacija", json={"pila_max_razina": "5", "tko": "IGOR"}).status_code == 400
    assert c.post("/api/postavke/optimizacija", json={"pila_mijesana_orijentacija": "da", "tko": "IGOR"}).status_code == 400
    r = c.post("/api/postavke/optimizacija", json={"pila_max_razina": "4", "pila_max_sirina_u_traci": "0", "tko": "IGOR"})
    assert r.status_code == 200 and {x["kljuc"]: x["vrijednost"] for x in r.json()}["pila_max_razina"] == "4"
    nid, nm, e1, e2 = _nalog(baza_o, status="unos")
    for nacin in ("auto", "hub"):
        r = c.post("/api/nalog/%d/materijal/%d/optimizacija" % (nid, nm), json={"nacin": nacin, "dubina": "brzo", "tko": "IVANA"})
        assert r.status_code == 200 and r.json()["nacin_trazen"] == nacin


def test_api_pripremi_prijedloge(baza_o, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    from hub.sifrarnici import prepoznaj as P
    monkeypatch.setenv("HUB_DB", str(baza_o.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    c = TestClient(A.app, raise_server_exceptions=False)
    nid, nm, e1, e2 = _nalog(baza_o, status="unos")
    for idx, W, L, kom in DIJ:
        N.dodaj_element(baza_o, nm, "TEST", L=L, W=W, kom=kom, naziv="E%d" % idx)
    baza_o.commit()
    r = c.post("/api/nalog/%d/optimizacija/pripremi" % nid, json={"nm": nm, "tko": "IVANA"})
    assert r.status_code == 200
    mat = [x for x in r.json() if x["nalog_materijal_id"] == nm][0]
    nacini = [x["nacin_trazen"] for x in mat["prijedlozi"]]
    assert nacini[0] == "auto" and set(nacini) <= {"auto", "hub"}
    assert c.post("/api/nalog/%d/optimizacija/pripremi" % nid, json={"tko": "IVANA"}).status_code == 200
    # svjeze: novi auto prijedlog zamjenjuje stari (isti broj živih prijedloga)
    r2 = c.post("/api/nalog/%d/optimizacija/pripremi" % nid, json={"nm": nm, "svjeze": True, "tko": "IVANA"}).json()
    mat2 = [x for x in r2 if x["nalog_materijal_id"] == nm][0]
    assert len(mat2["prijedlozi"]) == len(mat["prijedlozi"]) and mat2["prijedlozi"][0]["id"] != mat["prijedlozi"][0]["id"]
