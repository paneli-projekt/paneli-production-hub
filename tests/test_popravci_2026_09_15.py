# -*- coding: utf-8 -*-
"""Testovi za greške nađene u pregledu 15. 9. 2026. (20_ANALIZA/17_pregled_izmjena_13-15_09_2026.md) — svaka točka jedan test,
da se ne vrate. Fixture `baza` (sintetički šifrarnik + kupci + CPW/CSV datoteke) je iz tests/test_nalozi.py."""
import os
import sqlite3
import pytest

from hub import db
from hub.sifrarnici import pantheon, winstore, prepoznaj as P
from hub.nalozi import nalozi as N, kupci as K, uvoz_datoteka as U, provjera as PR, export_nesting as EX, export_pw as EW, export_pila as EP
from hub.formati import nalog_io, cpo_rw
from tests.test_nalozi import baza, CPW_BIJELI  # noqa: F401  (fixture)
from tests.test_sifrarnik import PH_IDENTI, WINSTORE_XML


def _nalog(baza, projekt="PROBA", status=None):
    k = K.trazi_kupce(baza, "", limit=1)
    mid = baza.execute("SELECT id FROM materijal WHERE pantheon_ident = 'IV000090'").fetchone()[0]
    nid = N.novi_nalog(baza, "TEST", kupac_id=k[0]["id"], projekt=projekt)["id"]
    nm = N.dodaj_materijal(baza, nid, "TEST", materijal_id=mid)[0]["id"]
    e1 = N.dodaj_element(baza, nm, "TEST", L=800, W=560, kom=2, naziv="POD", rubovi={"L": "ABS-ISTI"})
    e2 = N.dodaj_element(baza, nm, "TEST", L=400, W=300, kom=1, naziv="BOK", rubovi={"L": "ABS-ISTI"})
    for s in ("ponuda", "potvrdjeno", "skladiste", "pila_nesting")[: {"ponuda": 1, "potvrdjeno": 2, "skladiste": 3, "pila_nesting": 4}.get(status, 0)]:
        N.postavi_status(baza, nid, s, "TEST")
    baza.commit()
    return nid, nm, e1, e2


def test_1_api_izvoz_pw_i_pila(baza, monkeypatch, tmp_path):
    """Točka 1: rute /izvoz/pw i /izvoz/pila su vraćale 500 (NameError EW / EP)."""
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    monkeypatch.setenv("HUB_DB", str(baza.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    nid, nm, e1, e2 = _nalog(baza, status="potvrdjeno")
    c = TestClient(A.app, raise_server_exceptions=False)
    try:
        for ruta in ("pw", "pila", "nesting"):
            r = c.post("/api/nalog/%d/izvoz/%s" % (nid, ruta), json=dict(mapa=str(tmp_path), suho=True, tko="IVANA"))
            assert r.status_code == 200, (ruta, r.text)
            assert r.json()["suho"] and r.json()["paketi"]
        r = c.post("/api/nalog/%d/izvoz/nesting" % nid, json=dict(mapa=str(tmp_path), tko="IVANA"))
        assert r.status_code == 200 and os.path.exists(r.json()["paketi"][0]["csv"])
        # točka 3 kroz API: brisanje elementa nakon izvoza je 400 (status), ne 500 (FOREIGN KEY)
        r = c.delete("/api/nalog/element/%d" % e2["id"], params=dict(tko="IVANA"))
        assert r.status_code == 400 and "status" in r.text
        # točka 14: nalog u 'unos' s otvorenim potvrdama → 400 s razlogom, ne 500
        nid2, nm2, _, _ = _nalog(baza, projekt="UNOS")
        N.dodaj_element(baza, nm2, "TEST", L=500, W=300, kom=1, rubovi={"L": "taverna"})
        r = c.post("/api/nalog/%d/izvoz/nesting" % nid2, json=dict(mapa=str(tmp_path), suho=True))
        assert r.status_code == 400 and "za potvrdu" in r.text
        assert not A.veza().in_transaction                                     # točka 7: nema otvorene transakcije nakon greške
    finally:
        A._veza = None


def test_3_brisanje_nakon_izvoza(baza, tmp_path):
    """Točka 3: cix_registar.element_id i optimizacija su blokirali brisanje; ime CIX-a ostaje zauzeto (D-23)."""
    nid, nm, e1, e2 = _nalog(baza, status="potvrdjeno")
    EX.izvezi(baza, nid, str(tmp_path), "TEST")
    EP.izvezi(baza, nid, str(tmp_path), "TEST", samo_pila=False)
    N.postavi_status(baza, nid, "ponuda", "TEST")
    N.obrisi_element(baza, e1["id"], "TEST")
    N.obrisi_materijal(baza, nm, "TEST")
    assert baza.execute("SELECT COUNT(*) FROM cix_registar").fetchone()[0] == 2
    assert baza.execute("SELECT COUNT(*) FROM cix_registar WHERE element_id IS NOT NULL").fetchone()[0] == 0
    assert baza.execute("SELECT COUNT(*) FROM optimizacija").fetchone()[0] == 0
    # probni nalog nakon izvoza: obrisi_provjere ga briše bez greške
    nidp = N.novi_nalog(baza, "PROVJERA", kupac_kratki="X", projekt="P", izvor="provjera", broj="PROV-001", redni=1)["id"]
    mid = baza.execute("SELECT id FROM materijal WHERE pantheon_ident = 'IV000090'").fetchone()[0]
    nmp = N.dodaj_materijal(baza, nidp, "TEST", materijal_id=mid)[0]["id"]
    N.dodaj_element(baza, nmp, "TEST", L=800, W=560, kom=1)
    EX.izvezi(baza, nidp, str(tmp_path), "TEST", forsiraj=True)
    assert PR.obrisi_provjere(baza) == 1 and baza.execute("SELECT COUNT(*) FROM nalog WHERE id = ?", (nidp,)).fetchone()[0] == 0
    with pytest.raises(N.NalogGreska):                                        # stvarni nalog koji je krenuo dalje se ne briše
        N.obrisi_nalog(baza, nid, "TEST")


def test_4_potvrda_trake_samo_za_nalog(baza):
    """Točka 4: potvrda trake sa zapamti=False nije radila ništa."""
    nid, nm, e1, e2 = _nalog(baza)
    e = N.dodaj_element(baza, nm, "TEST", L=800, W=560, kom=2, rubovi={"L": "taverna", "G": "taverna"})
    assert e["provjeri"] == 1 and e["rub1_traka_id"] is None
    tid = baza.execute("SELECT id FROM traka WHERE pantheon_ident = 'TR000168'").fetchone()[0]
    N.potvrdi_traku_naloga(baza, nm, "taverna", tid, "TEST", zapamti=False)
    e = N.element(baza, e["id"])
    assert (e["rub1_traka_id"], e["rub4_traka_id"], e["provjeri"]) == (tid, tid, 0)
    assert baza.execute("SELECT COUNT(*) FROM traka_alias WHERE alias_norm = 'TAVERNA'").fetchone()[0] == 0   # bez aliasa
    assert N.broj_za_potvrdu(baza, nid) == 0
    assert P.prepoznaj_traku(baza, "taverna", materijal_id=baza.execute("SELECT materijal_id FROM nalog_materijal WHERE id = ?", (nm,)).fetchone()[0]).siguran is False


def test_5_naziv_elementa_u_cpw_i_csv(baza, tmp_path):
    """Točka 5: naziv elementa iz CPW-a se gubio u izvozu; Corpusovi stupci i GLODANJE se nisu vraćali u CSV."""
    k = K.trazi_kupce(baza, "", limit=1)
    nid = N.novi_nalog(baza, "TEST", kupac_id=k[0]["id"], projekt="CPW")["id"]
    U.uvezi_cpw(baza, nid, str(baza.dir / "a_bijeli.CPW"), "TEST", "kupac_ppw")
    assert [r[0] for r in baza.execute("SELECT naziv FROM element ORDER BY id")] == [None, "bok", "polica"]
    r = EW.izvezi(baza, nid, str(tmp_path), "TEST")
    redci = [l for l in open(r["paketi"][0]["cpw"], "rb").read().decode("cp1250").splitlines() if l.startswith("ELEMENT")]
    assert redci[1].startswith("ELEMENT;bok;700;400;2;M;;M;") and redci[2].startswith("ELEMENT;polica;600;300;3;")
    # CSV: Corpusovi stupci, PROGRAM1/2 i GLODANJE
    csv = (baza.dir / "TEST.CSV").read_bytes().decode("utf-8").replace(";;;1_ELEMENT;", ";Kuhinja;;Polica2;", 1).replace(";0;;;;;1/22 CRNA NK", ";0;P1.cix;P2.cix;;;1/22 CRNA NK", 1)
    csv = csv.replace("lijevi bok gornji;1\r\n", "lijevi bok gornji;2\r\n", 1)
    for t in ("1/22 CRNA NK", "ABS 0,5/22 BIJELI NK", "ABS-ISTI"):                 # bez traka, da nalog nema stavki za potvrdu
        csv = csv.replace(t, "")
    assert "gornji;2" in csv
    (baza.dir / "TEST2.CSV").write_bytes(csv.encode("utf-8"))
    nid2 = N.novi_nalog(baza, "TEST", kupac_id=k[0]["id"], projekt="CSV")["id"]
    U.uvezi_ppnest_csv(baza, nid2, str(baza.dir / "TEST2.CSV"), "TEST")
    e = baza.execute("SELECT cjelina, pozicija, program1, program2, prolaza FROM element WHERE nalog_materijal_id IN "
                     "(SELECT id FROM nalog_materijal WHERE nalog_id = ?) ORDER BY id LIMIT 1", (nid2,)).fetchone()
    assert tuple(e) == ("Kuhinja", "Polica2", "P1.cix", "P2.cix", 2)
    assert N.za_potvrdu(baza, nid2) == []
    N.postavi_status(baza, nid2, "ponuda", "TEST")
    N.postavi_status(baza, nid2, "potvrdjeno", "TEST")
    out = EX.izvezi(baza, nid2, str(tmp_path), "TEST")
    els = nalog_io.read_ppnest_csv([p["csv"] for p in out["paketi"] if p["winstore_kod"] == "W908ST2-18"][0])
    assert (els[0]["cjelina"], els[0]["pozicija"], els[0]["program1"], els[0]["program2"], els[0]["prolaza"]) == ("Kuhinja", "Polica2", "P1.cix", "P2.cix", 2)
    assert els[1]["pozicija"] == "2_ELEMENT" and els[1]["prolaza"] == 1                 # PPNEST-ov oblik kad podatka nema


def test_6_element_se_ne_mijenja_nakon_potvrde(baza):
    """Točka 6: uredi_element / obrisi_element su radili u svakom statusu."""
    nid, nm, e1, e2 = _nalog(baza, status="potvrdjeno")
    with pytest.raises(N.NalogGreska):
        N.uredi_element(baza, e1["id"], "TEST", L=1234)
    with pytest.raises(N.NalogGreska):
        N.obrisi_element(baza, e2["id"], "TEST")
    assert N.element(baza, e1["id"])["L"] == 800
    N.postavi_status(baza, nid, "ponuda", "TEST")
    assert N.uredi_element(baza, e1["id"], "TEST", L=1234)["L"] == 1234
    with pytest.raises(N.NalogGreska):
        N.uredi_element(baza, e1["id"], "TEST", kom=0)


def test_10_cpo_ord2_oznaka():
    """Točka 10: Corpusov CPO ima oznaku elementa u 3. polju ORD2 zapisa — čitanje/pisanje je gubilo."""
    d = dict(prog="X", ord=[dict(qty=1, qty2=1, W=100.0, L=200.0, grain="H", flag="Y", price=5.995, note="n", oznaka="EL_BU", a=1, idx=1)])
    for r in cpo_rw.parse(cpo_rw.write(cpo_rw.parse(cpo_rw.write(_cpo_min(d)))))["ord"]:
        assert r["oznaka"] == "EL_BU"


def _cpo_min(d):
    """Minimalan CPO zapis oko jednog ORD bloka (ostali blokovi kakve piše pila_optimizator)."""
    from hub.optimizacija import pila_optimizator as OPT
    e = [dict(rb=1, nalog="N", kupac="K", L=200.0, W=100.0, kom=1, sifra_mat="", deb=18, mat="M", god=0,
              traka={"L": "", "O": "", "D": "", "G": ""}, tip={"L": "", "O": "", "D": "", "G": ""}, cix="", napomena="n", prolaza=1, glodalo=12)]
    bajtovi = OPT.napravi_cpo(e, "HUB_00001", "K", material="M", ploca=(2800, 2070), trim=10, kerf=5.0, kerf_slaganja=16)[0]
    p = cpo_rw.parse(bajtovi)
    p["ord"][0]["oznaka"] = d["ord"][0]["oznaka"]
    return p


def test_11_winstore_novi_dan_zamjenjuje_stari(baza):
    """Točka 11: dnevni XML s novim imenom se zbrajao na stari — stanje se udvostručavalo."""
    (baza.dir / "11092026.XML").write_text(WINSTORE_XML, encoding="utf-8")
    (baza.dir / "12092026.XML").write_text(WINSTORE_XML, encoding="utf-8")
    winstore.uvezi_winstore(baza, str(baza.dir / "11092026.XML"), "TEST")
    prije = winstore.stanje_po_kodu(baza)
    winstore.uvezi_winstore(baza, str(baza.dir / "12092026.XML"), "TEST")
    assert winstore.stanje_po_kodu(baza) == prije
    assert [r[0] for r in baza.execute("SELECT DISTINCT izvoz FROM winstore_ploca")] == ["12092026.XML"]


def test_12_ident_koji_vise_nije_ploca_izlazi(baza):
    """Točka 12 (D-53): postojeći materijal čiji ident više nije ploča (TRAKA ZA R.P. pod RP) nestaje iz šifrarnika."""
    csv = baza.dir / "ph2.csv"
    csv.write_text(PH_IDENTI + "RP000020;TRAKA ZA R.P. NERO AFRIKA;;;;M;5;4;25;T\n", encoding="utf-8")
    baza.execute("INSERT INTO pantheon_ident (ident, naziv, aktivan, azurirano) VALUES ('RP000020', 'TRAKA ZA R.P. NERO AFRIKA', 1, 'x')")
    baza.execute("INSERT INTO materijal (pantheon_ident, naziv_pantheon, vrsta, obitelj_rp, debljina) VALUES ('RP000020', 'TRAKA ZA R.P. NERO AFRIKA', 'RP', 'radna', 38)")
    baza.commit()
    P.ocisti_kes()
    st = pantheon.uvezi_pantheon(baza, str(csv), "TEST")
    assert st["izbaceni_materijali"] == 1
    assert baza.execute("SELECT COUNT(*) FROM materijal WHERE pantheon_ident = 'RP000020'").fetchone()[0] == 0
    # ident koji se koristi u nalogu se ne briše nego označi
    nid, nm, e1, e2 = _nalog(baza)
    csv.write_text(PH_IDENTI.replace("IV000090;IVERAL BIJELI NK W908 ST2 18 MM", "IV000090;TRAKA BIJELA"), encoding="utf-8")
    P.ocisti_kes()
    st = pantheon.uvezi_pantheon(baza, str(csv), "TEST")
    r = baza.execute("SELECT aktivan, ne_koristi_se FROM materijal WHERE pantheon_ident = 'IV000090'").fetchone()
    assert st["izbaceni_materijali"] == 1 and tuple(r) == (0, 1)


def test_13_migracija_v8_brise_brojac_bez_stvarnih_naloga(tmp_path):
    """Točka 13 (D-47): probe su potrošile brojač u bazi bez stvarnih naloga — migracija ga vraća na početak."""
    c = db.spoji(str(tmp_path / "hub.db"))
    c.execute("DELETE FROM shema_verzija WHERE verzija >= 8")
    c.execute("INSERT INTO postavke (kljuc, vrijednost) VALUES ('brojac_naloga_2026', '34')")
    c.commit()
    c.close()
    c = db.spoji(str(tmp_path / "hub.db"))
    assert db.postavka(c, "brojac_naloga_2026") is None and db.postavka(c, "brojac_naloga_pocetak") == "1"
    assert N.sljedeci_broj(c, 2026)[2] == "2026-00001"
    # a sa stvarnim nalogom brojač ostaje
    c.execute("INSERT INTO nalog (broj, naziv, datum) VALUES ('2026-00001', 'X_1', 'd')")
    c.execute("DELETE FROM shema_verzija WHERE verzija >= 8")
    c.commit()
    c.close()
    c = db.spoji(str(tmp_path / "hub.db"))
    assert db.postavka(c, "brojac_naloga_2026") == "1"
    c.close()


def test_18_ppnest_ime_u_sukobu_dobiva_hub_ime(baza, tmp_path):
    """Točka 18 (D-60): PPNEST-ovo ime po vremenu se ponavlja — drugi element s istim imenom dobiva Hub ime, Corpusovo staje."""
    nid, nm, e1, e2 = _nalog(baza, status="potvrdjeno")
    baza.execute("UPDATE element SET cix_ime = '100926_080618', cix_izvor = 'ppnest' WHERE id IN (?, ?)", (e1["id"], e2["id"]))
    baza.commit()
    r = EX.izvezi(baza, nid, str(tmp_path), "TEST")
    imena = sorted(e["cix"] for e in nalog_io.read_ppnest_csv(r["paketi"][0]["csv"]))
    assert imena == ["100926_080618", "H0000001"]
    baza.execute("UPDATE element SET cix_ime = '100926_080618', cix_izvor = 'corpus' WHERE id = ?", (e2["id"],))
    baza.commit()
    with pytest.raises(EX.ExportGreska):
        EX.izvezi(baza, nid, str(tmp_path), "TEST")
    assert not baza.conn.in_transaction


def test_pila_element_na_punu_plocu_bez_obreza(baza, tmp_path):
    """Element na punu mjeru ploče (kupčev PPW HUMER: 2800×1190) rušio je izvoz s ValueError; PW ga reže bez obreza ruba (Igor, 15. 9.)
    — Hub isto: obrez 0 za taj materijal + upozorenje. Element veći od same ploče daje ExportGreska s popisom."""
    nid, nm, e1, e2 = _nalog(baza, status="potvrdjeno")
    N.postavi_status(baza, nid, "ponuda", "TEST")
    N.uredi_element(baza, e1["id"], "TEST", L=2800, W=1190)
    N.postavi_status(baza, nid, "potvrdjeno", "TEST")
    r = EP.izvezi(baza, nid, str(tmp_path), "TEST", samo_pila=False)
    assert r["paketi"][0]["obrez"] == 0 and any("2800x1190" in u and "bez obruba" in u for u in r["upozorenja"])
    assert cpo_rw.parse(r["paketi"][0]["cpo"])["inv"][0]["trim"] == [0.0, 0.0, 0.0, 0.0]
    N.postavi_status(baza, nid, "ponuda", "TEST")
    N.uredi_element(baza, e1["id"], "TEST", L=2900, W=1190)
    N.postavi_status(baza, nid, "potvrdjeno", "TEST")
    with pytest.raises(EX.ExportGreska) as ex:
        EP.izvezi(baza, nid, str(tmp_path), "TEST", samo_pila=False, suho=True)
    assert "2900x1190" in str(ex.value) and not baza.conn.in_transaction
