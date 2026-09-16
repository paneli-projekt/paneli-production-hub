# -*- coding: utf-8 -*-
"""Stvarno spajanje malih naloga u jedan nesting posao (D-54/B): jedan CSV + CIX paket iz više naloga istog materijala,
RN = naziv naloga po elementu, .mno natrag → razdioba po nalozima i posao označen gotovim."""
import os
import pytest

from hub.nalozi import nalozi as N, spajanje as SP, rezultat_nesting as RN, export_nesting as EX
from hub.formati import nalog_io
from tests.test_nalozi import baza  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog
from tests.test_rezultati import _mno


def test_spojeni_posao(baza, tmp_path):
    nid1, nm1, a1, a2 = _nalog(baza, projekt="PRVI", status="potvrdjeno")
    nid2, nm2, b1, b2 = _nalog(baza, projekt="DRUGI", status="potvrdjeno")
    nid3, nm3, c1, c2 = _nalog(baza, projekt="TRECI")                       # još u 'unos' — bez forsiraj ne ide
    n1, n2 = N.nalog(baza, nid1)["naziv"], N.nalog(baza, nid2)["naziv"]
    # greške: jedan materijal, dvaput isti, nepotvrđen nalog
    for ids, tekst in (([nm1], "barem dva"), ([nm1, nm1], "barem dva"), ([nm1, nm3], "statusu")):
        with pytest.raises((SP.SpajanjeGreska, EX.ExportGreska)) as ex:
            SP.izvezi_spojeno(baza, ids, str(tmp_path), "TEST")
        assert tekst in str(ex.value)
    # suho: ništa na disku ni u bazi
    r = SP.izvezi_spojeno(baza, [nm1, nm2], str(tmp_path), "TEST", suho=True)
    assert r["suho"] and r["naloga"] == 2 and r["elemenata"] == 4 and r["komada"] == 6 and not os.path.exists(r["mapa"])
    assert baza.execute("SELECT COUNT(*) FROM spojeni_posao").fetchone()[0] == 0
    # pravi izvoz
    r = SP.izvezi_spojeno(baza, [nm1, nm2], str(tmp_path), "TEST")
    assert r["naziv"].startswith("SPOJ_IV_BIJELI_NK_18_") and os.path.isfile(r["csv"]) and len(r["cix"]) == 4 and all(os.path.isfile(x) for x in r["cix"])
    rows = nalog_io.read_ppnest_csv(r["csv"])
    assert [x["nalog"] for x in rows] == [n1, n1, n2, n2] and [x["rb"] for x in rows] == [1, 2, 3, 4]      # RN = naziv naloga po elementu
    assert all(x["sifra_mat"] == "W908ST2-18" for x in rows) and {x["cix"] for x in rows} == {"H0000001", "H0000002", "H0000003", "H0000004"}
    p = SP.poslovi(baza)[0]
    assert p["naziv"] == r["naziv"] and p["ident"] == "IV000090" and [s["nalog"] for s in p["stavke"]] == [n1, n2] and not p["rezultat_stigao"]
    assert {baza.execute("SELECT put, status_opt FROM nalog_materijal WHERE id = ?", (x,)).fetchone()[:] for x in (nm1, nm2)} == {("nesting", "spojeno:" + r["naziv"])}
    assert baza.execute("SELECT COUNT(*) FROM dokument WHERE nalog_id = ? AND vrsta = 'cix'", (nid1,)).fetchone()[0] == 2
    assert "spojenom poslu" in N.dogadjaji(baza, nid2)[-1]["razlog"]
    # ponovni izvoz istih naloga → ista CIX imena (registar), novi posao
    r2 = SP.izvezi_spojeno(baza, [nm1, nm2], str(tmp_path), "TEST", vrijeme=__import__("datetime").datetime(2026, 9, 15, 12, 0, 0))
    assert r2["naziv"] == "SPOJ_IV_BIJELI_NK_18_150926_120000" and {os.path.basename(x) for x in r2["cix"]} == {os.path.basename(x) for x in r["cix"]}
    # .mno se vraća pod imenom bNest projekta = naš CSV + _<šifra>_<deb>
    mno = _mno(str(tmp_path / (r2["naziv"] + "_W908ST2-18_18.mno")),
               [("H0000001", "POD", 800, 560, n1), ("H0000001", "POD", 800, 560, n1), ("H0000002", "BOK", 400, 300, n1), ("H0000003", "POD", 800, 560, n2), ("H0000004", "BOK", 400, 300, n2)])
    open(mno).read()
    txt = open(mno, encoding="utf-8").read().replace("<DESCR>PROBA_W908 ;", "<DESCR>%s_W908ST2-18_18 ;" % r2["naziv"])
    open(mno, "w", encoding="utf-8").write(txt)
    izv = RN.upisi(baza, mno, "TEST")
    v = {x["nalog"]: x for x in izv["veze"]}
    assert v[n1]["spojeno"] and v[n1]["spojeni_posao"] == r2["naziv"] and v[n2]["spojeni_posao"] == r2["naziv"]
    assert abs(v[n1]["ploca"] + v[n2]["ploca"] - 1.0) < 1e-6 and v[n1]["ploca"] > v[n2]["ploca"]
    p = SP.poslovi(baza)[0]
    assert p["naziv"] == r2["naziv"] and p["rezultat_stigao"] and not SP.poslovi(baza)[1]["rezultat_stigao"]
    u = RN.usporedba(baza, nid1)[0]
    assert u["spojeni_posao"] == dict(naziv=r2["naziv"], rezultat_stigao=True) and u["bnest"]["nacin"] == "spojeno"
    # brisanje probnog naloga briše i stavku posla
    N.obrisi_nalog(baza, nid1, "TEST", forsiraj=True)
    assert baza.execute("SELECT COUNT(*) FROM spojeni_posao_stavka WHERE nalog_id = ?", (nid1,)).fetchone()[0] == 0


def test_api_spajanje_izvezi(baza, monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    from hub.sifrarnici import prepoznaj as P
    monkeypatch.setenv("HUB_DB", str(baza.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    nid1, nm1, _, _ = _nalog(baza, projekt="PRVI", status="potvrdjeno")
    nid2, nm2, _, _ = _nalog(baza, projekt="DRUGI", status="potvrdjeno")
    c = TestClient(A.app, raise_server_exceptions=False)
    try:
        r = c.post("/api/spajanje/izvezi", json=dict(nm_ids=[nm1, nm2], mapa=str(tmp_path), suho=True))
        assert r.status_code == 200 and r.json()["naloga"] == 2
        r = c.post("/api/spajanje/izvezi", json=dict(nm_ids=[nm1], mapa=str(tmp_path)))
        assert r.status_code == 400 and "barem dva" in r.text and not A.veza().in_transaction
        r = c.post("/api/spajanje/izvezi", json=dict(nm_ids=[nm1, nm2], mapa=str(tmp_path), tko="VODITELJ"))
        assert r.status_code == 200 and os.path.isfile(r.json()["csv"])
        r = c.get("/api/spajanje/poslovi")
        assert r.status_code == 200 and len(r.json()) == 1 and len(r.json()[0]["stavke"]) == 2
    finally:
        A._veza = None
