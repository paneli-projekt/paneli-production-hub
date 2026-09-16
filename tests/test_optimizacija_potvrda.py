# -*- coding: utf-8 -*-
"""D-75 / D-77 (korak 5b): optimizacija s potvrdom — prijedlog → potvrda → ista brojka u ponudi i u CPO-u; alternative (način × dubina);
promjena elemenata → zastarjelo; bez potvrde nema ponude ni izvoza; skrivene postavke (nadmjera trake, obračun rezanja, kerf)."""
import json
import pytest

from hub.nalozi import nalozi as N, obracun as OC, ponuda as PO, optimiziraj as OP, export_pila as EP
from hub.nalozi.export_nesting import ExportGreska
from tests.test_nalozi import baza  # noqa: F401
from tests.test_obracun_ponuda import baza_o  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog


@pytest.fixture
def rucno(baza_o):
    OP.AUTO_POTVRDA = False
    return baza_o


def test_prijedlog_potvrda_i_ista_brojka(rucno, tmp_path):
    nid, nm, e1, e2 = _nalog(rucno, status="ponuda")
    # bez potvrde: obračun radi (prijedlog) ali upozori; ponuda i izvoz stanu
    r = OC.izracunaj(rucno, nid)
    assert r["nepotvrdjene_optimizacije"] and any("nije potvrđena" in u for u in r["upozorenja"])
    with pytest.raises(PO.PonudaGreska, match="nije potvrđena"):
        PO.nova_verzija(rucno, nid, "IVANA")
    rucno.execute("UPDATE nalog SET status = 'potvrdjeno' WHERE id = ?", (nid,)); rucno.commit()
    with pytest.raises(ExportGreska, match="nije potvrđena"):
        EP.izvezi(rucno, nid, str(tmp_path), "TEST")
    assert EP.izvezi(rucno, nid, str(tmp_path), "TEST", suho=True)["paketi"][0]["optimizacija_potvrdjena"] is False   # suho = pregled prijedloga
    rucno.execute("UPDATE nalog SET status = 'ponuda' WHERE id = ?", (nid,)); rucno.commit()
    # upis obračuna napravi auto prijedlog za ekran
    OC.upisi(rucno, nid, "IVANA")
    pr = OP.pregled(rucno, nid)
    mat = [x for x in pr if x["nalog_materijal_id"] == nm][0]
    assert mat["treba"] and mat["potvrdjeno"] is None and len(mat["prijedlozi"]) == 1
    p = mat["prijedlozi"][0]
    assert p["status"] == "prijedlog" and p["nacin_trazen"] == "auto" and p["dubina"] == "najbolje" and p["broj_ploca"] == 1
    # alternativa: poprečno / brzo — razlika prema auto se vidi
    alt = OP.predlozi(rucno, nm, "poprecno", "brzo", "IVANA")
    assert alt["nacin"].startswith("poprecno") and "razlika_m2_prema_auto" in alt
    assert len([x for x in OP.pregled(rucno, nid) if x["nalog_materijal_id"] == nm][0]["prijedlozi"]) == 2
    # potvrda auto prijedloga → ponuda i CPO iz istog slaganja
    pot = OP.potvrdi(rucno, p["id"], "IVANA")
    assert pot["status"] == "potvrdjeno" and pot["potvrdio_id"] and not pot["ponuda_poslana"]
    assert OP.potvrdjena(rucno, nm)["id"] == p["id"]
    r2 = OC.izracunaj(rucno, nid)
    assert not r2["nepotvrdjene_optimizacije"]
    ploca = [s for s in r2["stavke"] if s["grupa"] == "materijal"][0]
    assert "(potvrđeno)" in ploca["pravilo"]
    v = PO.nova_verzija(rucno, nid, "IVANA")
    assert v["verzija"] == 1
    rucno.execute("UPDATE nalog SET status = 'potvrdjeno' WHERE id = ?", (nid,)); rucno.commit()
    izv = EP.izvezi(rucno, nid, str(tmp_path), "TEST")
    pk = izv["paketi"][0]
    assert pk["optimizacija_potvrdjena"] and pk["optimizacija_id"] == p["id"] and pk["ploca"] == pot["broj_ploca"]
    assert abs(pk["m2_za_naplatu"] - pot["m2_za_naplatu"]) < 1e-6           # ISTA brojka u ponudi i na pili (D-75)
    red = rucno.execute("SELECT status, dokument_id, sheme_json FROM optimizacija WHERE id = ?", (p["id"],)).fetchone()
    assert red["status"] == "potvrdjeno" and red["dokument_id"] and json.loads(red["sheme_json"])["program"] == pk["program"]
    assert rucno.execute("SELECT COUNT(*) FROM optimizacija WHERE nalog_materijal_id = ? AND engine = 'hub'", (nm,)).fetchone()[0] == 2   # bez novog reda pri izvozu
    # druga potvrda (alternativa) zamjenjuje prvu; ponuda je poslana → upozorenje da treba nova verzija
    rucno.execute("UPDATE ponuda_verzija SET status = 'poslana' WHERE id = ?", (v["id"],)); rucno.commit()
    pot2 = OP.potvrdi(rucno, alt["id"], "GORAN")
    assert pot2["ponuda_poslana"] is True
    assert rucno.execute("SELECT status FROM optimizacija WHERE id = ?", (p["id"],)).fetchone()[0] == "zamijenjeno"
    dog = rucno.execute("SELECT razlog FROM dogadjaj WHERE nalog_id = ? ORDER BY id DESC LIMIT 1", (nid,)).fetchone()[0]
    assert "PONUDA JE VEĆ POSLANA" in dog


def test_promjena_elemenata_zastari_potvrdu(rucno):
    nid, nm, e1, e2 = _nalog(rucno, status="unos")
    p = OP.predlozi(rucno, nm, "auto", "najbolje", "IVANA")
    OP.potvrdi(rucno, p["id"], "IVANA")
    N.uredi_element(rucno, e1["id"], "TEST", kom=5)
    assert OP.potvrdjena(rucno, nm) is None
    assert rucno.execute("SELECT status FROM optimizacija WHERE id = ?", (p["id"],)).fetchone()[0] == "zastarjelo"
    p2 = OP.predlozi(rucno, nm, "auto", "najbolje", "IVANA")
    with pytest.raises(OP.OptimizacijaGreska):
        OP.potvrdi(rucno, p["id"], "IVANA")                     # stari prijedlog se ne može potvrditi
    OP.potvrdi(rucno, p2["id"], "IVANA")
    assert OP.potvrdjena(rucno, nm)["id"] == p2["id"]
    assert OP.nepotvrdjeni(rucno, nid) == []


def test_brzo_i_nacini(rucno):
    nid, nm, e1, e2 = _nalog(rucno, status="unos")
    for nacin in OP.NACINI:
        for dubina in OP.DUBINE:
            r = OP.izracunaj(rucno, nm, nacin, dubina)
            assert r["st"]["ploca"] >= 1 and r["oc"]["m2_naplata"] > 0
            if nacin != "auto":
                assert r["nacin"].startswith(nacin)
    with pytest.raises(OP.OptimizacijaGreska):
        OP.izracunaj(rucno, nm, "dijagonalno", "brzo")


def test_postavke_d77(rucno):
    nid, nm, e1, e2 = _nalog(rucno, status="ponuda")
    r0 = OC.izracunaj(rucno, nid)
    traka0 = [s for s in r0["stavke"] if s["grupa"] == "traka"][0]
    rez0 = [s for s in r0["stavke"] if s["grupa"] == "rezanje"][0]
    assert rez0["pantheon_ident"] == "US000002" and "nadmjera 10 %" in traka0["pravilo"]
    rucno.execute("UPDATE postavke SET vrijednost = '20' WHERE kljuc = 'nadmjera_trake'")
    rucno.execute("UPDATE postavke SET vrijednost = 'rezova' WHERE kljuc = 'obracun_rezanja'")
    rucno.execute("INSERT OR IGNORE INTO pantheon_ident (ident, naziv, klasif, jm, cijena_prodajna, cijena_neto, pdv, aktivan, azurirano) VALUES ('US000303','USLUGA REZ','US','KOM',1.25,1.0,25,1,'t')")
    rucno.commit()
    r1 = OC.izracunaj(rucno, nid)
    traka1 = [s for s in r1["stavke"] if s["grupa"] == "traka"][0]
    rez1 = [s for s in r1["stavke"] if s["grupa"] == "rezanje"][0]
    assert "nadmjera 20 %" in traka1["pravilo"] and rez1["pantheon_ident"] == "US000303" and rez1["jm"] == "KOM" and rez1["kolicina"] >= 1
    rucno.execute("UPDATE postavke SET vrijednost = 'm_reza' WHERE kljuc = 'obracun_rezanja'"); rucno.commit()
    r2 = OC.izracunaj(rucno, nid)
    assert [s for s in r2["stavke"] if s["grupa"] == "rezanje"][0]["pantheon_ident"] == "US000002" and any("dužnom metru" in u for u in r2["upozorenja"])


def test_api_optimizacija(rucno, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    from hub.sifrarnici import prepoznaj as P
    monkeypatch.setenv("HUB_DB", str(rucno.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    nid, nm, e1, e2 = _nalog(rucno, status="ponuda")
    c = TestClient(A.app, raise_server_exceptions=False)
    assert c.post("/api/nalog/%d/ponude" % nid, json={"tko": "IVANA"}).status_code == 400
    p = c.post("/api/nalog/%d/materijal/%d/optimizacija" % (nid, nm), json={"nacin": "uzduzno", "dubina": "brzo", "tko": "IVANA"}).json()
    assert p["status"] == "prijedlog" and p["nacin"].startswith("uzduzno")
    assert c.post("/api/optimizacija/%d/potvrdi" % p["id"], json={"tko": "IVANA"}).json()["status"] == "potvrdjeno"
    pr = c.get("/api/nalog/%d/optimizacija" % nid).json()
    assert [x for x in pr if x["nalog_materijal_id"] == nm][0]["potvrdjeno"]["id"] == p["id"]
    assert c.post("/api/nalog/%d/ponude" % nid, json={"tko": "IVANA"}).status_code == 200
    ps = c.get("/api/postavke/optimizacija").json()
    assert {x["kljuc"] for x in ps} >= {"kerf", "kerf_pile", "nadmjera_trake", "obracun_rezanja"}
    assert c.post("/api/postavke/optimizacija", json={"nadmjera_trake": "12,5", "tko": "IGOR"}).status_code == 200
    assert [x for x in c.get("/api/postavke/optimizacija").json() if x["kljuc"] == "nadmjera_trake"][0]["vrijednost"] == "12.5"
    assert c.post("/api/postavke/optimizacija", json={"obracun_rezanja": "krivo"}).status_code == 400
