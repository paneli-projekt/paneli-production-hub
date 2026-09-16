# -*- coding: utf-8 -*-
"""Rezultati natrag u Hub (korak 3d): sheme rezanja iz CPO-a kao PNG (D-34) i bNest .mno → stvarna potrošnja, razdioba spojenog posla (D-38).
Sintetički dio radi bez stvarnih podataka; stvarni dio (HUB_TEST_DATA) koristi Corpus uzorak s bNest projektima."""
import glob
import json
import os
import pytest

from hub.nalozi import nalozi as N, export_pila as EP, sheme as SH, rezultat_nesting as RN, uvoz_corpus as UC, provjera as PR
from hub.formati import cpo_rw
from tests.test_nalozi import baza  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog
from tests.test_sifrarnik import DATA, HUB, stvarni, stvarna_baza  # noqa: F401

MNO = """<NESTING_RESULT SOLUTION_NAME="Complete Sectioning Solution">
<COMMESSA><DESCR>PROBA_W908 ; 09/15/2026 10:00:00 ; W908ST2-18_18</DESCR></COMMESSA>
<FOGLIO PATH="p_0001(1).bSolid" QTY="%(qty)d" NAME="W908ST2-18-2800-2070.xml" ID="1">
<SheetInfo Name="W908ST2-18-2800-2070" DX="2800" DY="2070" DZ="18" GrainDirection="N" Materiale="W908ST2-18" Resto="0"/>
<StatisticInfo PartUsedArea="1016000"/>
<NOME>%(profili)s</NOME>
</FOGLIO>
</NESTING_RESULT>"""
PROF = """<PROFILO><OptimizedSourceName Value="%(cix)s.cix"/><PartName Value="%(rb)d-%(poz)s-%(cix)s"/>
<VARIABILE NAME="LPX">%(L)g</VARIABILE><VARIABILE NAME="LPY">%(W)g</VARIABILE><VARIABILE NAME="LPZ">18</VARIABILE>
<INFO><CUSTOM_INFO name="CUSTOM_DESCR_1" value="PROBA_W908"/><CUSTOM_INFO name="CUSTOM_DESCR_2" value="%(nalog)s"/>
<CUSTOM_INFO name="CUSTOM_DESCR_3" value=""/><CUSTOM_INFO name="CUSTOM_DESCR_4" value="%(poz)s"/><CUSTOM_INFO name="CUSTOM_DESCR_5" value="W908ST2-18"/>
<CUSTOM_INFO name="CUSTOM_DESCR_11" value="%(cix)s"/><CUSTOM_INFO name="CUSTOM_DESCR_22" value="1"/></INFO>
<POS ID="1"><X>%(x)g</X><Y>10</Y><DEG>0</DEG></POS></PROFILO>"""


def _mno(put, dijelovi, qty=1):
    prof = "".join(PROF % dict(rb=i + 1, cix=d[0], poz=d[1], L=d[2], W=d[3], nalog=d[4], x=10 + i * 900) for i, d in enumerate(dijelovi))
    open(put, "w", encoding="utf-8").write(MNO % dict(qty=qty, profili=prof))
    return put


def test_sheme_png_uz_izvoz_na_pilu(baza, tmp_path):
    pytest.importorskip("matplotlib")
    nid, nm, e1, e2 = _nalog(baza, status="potvrdjeno")
    r = EP.izvezi(baza, nid, str(tmp_path), "TEST")
    p = r["paketi"][0]
    assert p["sheme"] and all(os.path.isfile(s["png"]) for s in p["sheme"]) and p["sheme"][0]["png"].endswith("HUB_00001_S1.png")
    assert sum(s["dijelova"] for s in p["sheme"]) == 3 and 0 < p["sheme"][0]["iskoristenje"] < 1
    assert baza.execute("SELECT COUNT(*) FROM dokument WHERE nalog_id = ? AND vrsta = 'png'", (nid,)).fetchone()[0] == len(p["sheme"])
    o = baza.execute("SELECT sheme_json FROM optimizacija WHERE nalog_materijal_id = ?", (nm,)).fetchone()
    assert json.loads(o[0])["sheme"][0]["shema"] == 1
    geo = SH.geometrija(cpo_rw.parse(p["cpo"]))
    assert len(geo) == len(p["sheme"]) and all(x[4] is None or 1 <= x[4] <= 2 for g in geo for x in g["pravokutnici"])
    u = RN.usporedba(baza, nid)
    assert u[0]["hub"]["broj_ploca"] == p["ploca"] and u[0]["bnest"] is None and u[0]["hub"]["sheme_json"]["sheme"]


def test_mno_potrosnja_i_razdioba(baza, tmp_path):
    # dva naloga istog materijala u JEDNOM bNest poslu (spojeno, D-54) — razdioba po kvadraturi (D-38)
    nid1, nm1, a1, a2 = _nalog(baza, projekt="PRVI", status="potvrdjeno")
    nid2, nm2, b1, b2 = _nalog(baza, projekt="DRUGI", status="potvrdjeno")
    for eid, ime in ((a1["id"], "H0000001"), (a2["id"], "H0000002"), (b1["id"], "H0000003")):
        baza.execute("UPDATE element SET cix_ime = ?, cix_izvor = 'hub' WHERE id = ?", (ime, eid))
    baza.commit()
    n1, n2 = N.nalog(baza, nid1)["naziv"], N.nalog(baza, nid2)["naziv"]
    mno = _mno(str(tmp_path / "PROBA_W908.mno"),
               [("H0000001", "POD", 800, 560, n1), ("H0000001", "POD", 800, 560, n1), ("H0000002", "BOK", 400, 300, n1), ("H0000003", "POD", 800, 560, n2),
                ("NEPOZNAT", "X", 500, 500, "TUDJI")], qty=2)
    r = RN.procitaj(mno)
    assert (r["ploca"], r["sifra_mat"], len(r["dijelovi"]), r["m2_bruto"]) == (2, "W908ST2-18", 5, 11.592) and r["po_nalogu"][n1]["dijelova"] == 6
    izv = RN.upisi(baza, mno, "TEST", suho=True)
    assert not izv["preskoceno"] and len(izv["veze"]) == 2 and "NEPOZNAT" in izv["upozorenja"][0]
    assert baza.execute("SELECT COUNT(*) FROM optimizacija").fetchone()[0] == 0
    izv = RN.upisi(baza, mno, "TEST")
    v = {x["nalog"]: x for x in izv["veze"]}
    m2_1, m2_2, m2_x = (2 * 0.448 + 0.12) * 2, 0.448 * 2, 0.25 * 2                   # × qty 2
    assert v[n1]["dijelova"] == 6 and v[n2]["dijelova"] == 2 and v[n1]["spojeno"] and v[n2]["spojeno"]
    assert abs(v[n1]["udio"] - m2_1 / (m2_1 + m2_2 + m2_x)) < 1e-3 and abs(v[n1]["ploca"] + v[n2]["ploca"] - 2 * (m2_1 + m2_2) / (m2_1 + m2_2 + m2_x)) < 0.02
    assert v[n2].get("napomena") == "u poslu je 2 od 3 komada materijala"
    rows = baza.execute("SELECT nalog_materijal_id, engine, nacin, broj_ploca, m2_dijelova FROM optimizacija ORDER BY id").fetchall()
    assert [(r[1], r[2]) for r in rows] == [("bNest", "spojeno")] * 2 and {r[0] for r in rows} == {nm1, nm2}
    assert baza.execute("SELECT status_opt FROM nalog_materijal WHERE id = ?", (nm1,)).fetchone()[0] == "nesting_gotov"
    # isti .mno drugi put se preskače; usporedba vraća bNest bez Huba
    izv2 = RN.upisi(baza, mno, "TEST")
    assert izv2["preskoceno"] and baza.execute("SELECT COUNT(*) FROM optimizacija").fetchone()[0] == 2
    u = RN.usporedba(baza, nid1)[0]
    assert u["hub"] is None and u["bnest"]["broj_ploca"] == v[n1]["ploca"] and u["bnest"]["sheme_json"]["udio"] == v[n1]["udio"]
    # Hub pila + bNest → razlika ploča (naplaćeno vs potrošeno, D-38)
    EP.izvezi(baza, nid1, str(tmp_path / "pila"), "TEST")
    u = RN.usporedba(baza, nid1)[0]
    assert u["hub"]["broj_ploca"] == 1 and u["razlika_ploca"] == round(v[n1]["ploca"] - 1, 2)
    # .mno bez ijednog poznatog dijela → ništa se ne upisuje; loš XML → greška
    izv3 = RN.upisi(baza, _mno(str(tmp_path / "tudji.mno"), [("X1", "A", 100, 100, "NITKO")]), "TEST")
    assert not izv3["veze"] and baza.execute("SELECT COUNT(*) FROM optimizacija").fetchone()[0] == 3
    (tmp_path / "los.mno").write_text("<a><b></a>")
    with pytest.raises(RN.RezultatGreska):
        RN.upisi(baza, str(tmp_path / "los.mno"), "TEST")
    (tmp_path / "drugi.mno").write_text("<PROGETTO/>")
    rez = RN.upisi_mapu(baza, str(tmp_path), "TEST")                            # mapa: greška po datoteci ne ruši ostale
    assert len(rez) == 4 and sum(1 for x in rez if x.get("greska")) == 2 and sum(1 for x in rez if x.get("preskoceno")) == 1   # tuđi .mno nije zabilježen pa se opet pročita


def test_api_rezultati(baza, monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    pytest.importorskip("matplotlib")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    from hub.sifrarnici import prepoznaj as P
    monkeypatch.setenv("HUB_DB", str(baza.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    nid, nm, e1, e2 = _nalog(baza, status="potvrdjeno")
    baza.execute("UPDATE element SET cix_ime = 'H0000009', cix_izvor = 'hub' WHERE id = ?", (e1["id"],))
    baza.commit()
    c = TestClient(A.app, raise_server_exceptions=False)
    try:
        r = c.post("/api/nalog/%d/izvoz/pila" % nid, json=dict(mapa=str(tmp_path)))
        assert r.status_code == 200 and r.json()["paketi"][0]["sheme"]
        png = r.json()["paketi"][0]["sheme"][0]["png"]
        r = c.get("/api/slika", params=dict(put=png))
        assert r.status_code == 200 and r.headers["content-type"] == "image/png" and r.content[:4] == b"\x89PNG"
        assert c.get("/api/slika", params=dict(put=str(tmp_path / "nema.png"))).status_code == 404
        mno = _mno(str(tmp_path / "x.mno"), [("H0000009", "POD", 800, 560, N.nalog(baza, nid)["naziv"])])
        r = c.post("/api/rezultat/nesting", json=dict(put=mno, tko="OPERATER"))
        assert r.status_code == 200 and r.json()["veze"][0]["ploca"] == 1.0
        r = c.get("/api/nalog/%d/rezultati" % nid)
        assert r.status_code == 200 and r.json()[0]["hub"]["broj_ploca"] == 1 and r.json()[0]["bnest"]["broj_ploca"] == 1 and r.json()[0]["razlika_ploca"] == 0
        assert c.post("/api/rezultat/nesting", json=dict(mapa=str(tmp_path))).status_code == 200
        assert c.post("/api/rezultat/nesting", json=dict()).status_code == 400
    finally:
        A._veza = None


@stvarni
def test_stvarni_corpus_mno(stvarna_baza):
    """Corpus uzorak: uvoz paketa + bNest .mno iz 04_export_nesting → 2 materijala, 3/3 i 8/10 dijelova (police su iz drugog Corpus izvoza)."""
    mapa = os.path.join(DATA, "_CORPUS_UZORAK")
    if not glob.glob(os.path.join(mapa, "04_export_nesting", "**", "*.mno"), recursive=True):
        pytest.skip("nema .mno u Corpus uzorku")
    nid, _ = UC.uvezi_paket(stvarna_baza, os.path.join(mapa, "01_ulaz_corpus"), "TEST", kupac_kratki="PROBA", izvor="provjera", broj="PROV-990", redni=990)
    rez = RN.upisi_mapu(stvarna_baza, os.path.join(mapa, "04_export_nesting"), "TEST")
    veze = {v["ident"]: v for r in rez for v in r["veze"]}
    assert veze["IV000027"]["ploca"] == 1.0 and veze["IV000027"]["dijelova"] == 3
    assert veze["IV000090"]["dijelova"] == 8 and 0.7 < veze["IV000090"]["ploca"] < 0.9 and "8 od 10" in veze["IV000090"]["napomena"]
    u = {x["ident"]: x for x in RN.usporedba(stvarna_baza, nid)}
    assert u["IV000027"]["bnest"]["broj_ploca"] == 1.0 and u["IV000054"]["bnest"] is None      # MDF leđa su išla na pilu
    PR.obrisi_provjere(stvarna_baza)
