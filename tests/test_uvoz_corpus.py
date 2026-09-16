# -*- coding: utf-8 -*-
"""Uvoz Corpusovog paketa (korak 3c, D-29 / D-55 / D-23) na sintetičkom paketu — CPW po materijalu + CSV + CIX (+ HORIZONTALNO_BUSENJE),
pa izvoz na nesting (kopija oba CIX-a) i pilu (leđa). Fixture `baza` iz tests/test_nalozi.py."""
import os
import json
import pytest

from hub.formati import cix_citaj, nalog_io
from hub.nalozi import nalozi as N, uvoz_corpus as UC, export_nesting as EX, export_pila as EP, provjera as PR
from tests.test_nalozi import baza  # noqa: F401

CPW_IV = ("FORMAT;CORPUS->PW; 012992;\r\nMATERIJAL; W908ST2-18; 18;\r\n"
          "ELEMENT;,; 800; 560; 1;A; M; M;M;BIJELA_NK-1/22;BIJELA_NK-MEL;BIJELA_NK-MEL;BIJELA_NK-MEL;EL1 - L_BOK; 1446A0000001.CIX; .CIX; ; W908ST2-18;\r\n"
          "ELEMENT;,; 864; 556; 1;A; ; ;;BIJELA_NK-1/22;;;;EL1 - POD; 1446A0000002.CIX; 2446A0000002.CIX; ; W908ST2-18;\r\n"
          "ELEMENT;,; 863; 536; 2;M; ; ;;BIJELA_NK-MEL;;;;EL1 - Polica; .CIX; .CIX; ; W908ST2-18;\r\n")
CPW_MDF = ("FORMAT;CORPUS->PW; 003068;\r\nMATERIJAL; IV001038-19; 19;\r\n"
           "ELEMENT;,; 796; 888; 1;; ; ;;;;;;EL1 - LEDJA; .CIX; .CIX; ; IV001038-19;\r\n")
CSV = ("RB;RN;NAZIV ELEMENTA;BROJ ELE;IME DASKE;KONACNADIMENZIJA;SIRINA;DUZINA;KOLICINA;SIFRA MAT;MAT DEB;MAT NAZIV;GOD;PROGRAM1;PROGRAM2;OBRADA;"
       "RUB1;TR1SIFRA;RUB2;TR2SIFRA;RUB3;TR3SIFRA;RUB4;TR4SIFRA;LJEPLJENJE;CIX;bSolid;GLODANJE;Primjedba;\n"
       "1;;EL1;0;L_BOK;560x800;560.00;800.00;1;W908ST2-18;18;IV BIJELI NK;0;1446A0000001;;;1.0;BIJELA_NK-1/22;0.5;BIJELA_NK-MEL;0.5;BIJELA_NK-MEL;0.5;BIJELA_NK-MEL;0;1446A0000001;;;;False\n"
       "2;;EL1;0;POD;556x864;556.00;864.00;1;W908ST2-18;18;IV BIJELI NK;0;1446A0000002;2446A0000002;;1.0;BIJELA_NK-1/22;0.0;;0.0;;0.0;;0;1446A0000002;;;;False\n"
       "3;;EL1;0;Polica;536x863;536.00;863.00;2;W908ST2-18;18;IV BIJELI NK;0;;;;0.5;BIJELA_NK-MEL;0.0;;0.0;;0.0;;0;1446A0000003;;;;False\n;\n")


def _cix(L, W, deb, busenja=0, kant=0, utor=0, tocaka=5):
    m = ["BEGIN ID CID3\n\tREL= 5.0\nEND ID\n\nBEGIN MAINDATA\n\tLPX=%g\n\tLPY=%g\n\tLPZ=%g\nEND MAINDATA\n" % (L, W, deb)]
    if tocaka:
        m.append("BEGIN MACRO\n\tNAME=GEO\n\tPARAM,NAME=LAY,VALUE=\"GEO\"\nEND MACRO\nBEGIN MACRO\n\tNAME=START_POINT\n\tPARAM,NAME=X,VALUE=0\n\tPARAM,NAME=Y,VALUE=0\nEND MACRO\n")
        m += ["BEGIN MACRO\n\tNAME=LINE_EP\n\tPARAM,NAME=XE,VALUE=%d\n\tPARAM,NAME=YE,VALUE=0\nEND MACRO\n" % i for i in range(tocaka)]
        m.append("BEGIN MACRO\n\tNAME=ROUTG\n\tPARAM,NAME=DP,VALUE=%g\n\tPARAM,NAME=DIA,VALUE=12\nEND MACRO\n" % (deb + 0.15))
    m += ["BEGIN MACRO\n\tNAME=BG\n\tPARAM,NAME=SIDE,VALUE=0\n\tPARAM,NAME=X,VALUE=9\n\tPARAM,NAME=DIA,VALUE=5\nEND MACRO\n"] * busenja
    m += ["BEGIN MACRO\n\tNAME=BG\n\tPARAM,NAME=SIDE,VALUE=1\n\tPARAM,NAME=X,VALUE=9\n\tPARAM,NAME=DIA,VALUE=8\nEND MACRO\n"] * kant
    m += ["BEGIN MACRO\n\tNAME=CUT_X\n\tPARAM,NAME=X,VALUE=0\n\tPARAM,NAME=DP,VALUE=8\nEND MACRO\n"] * utor
    return "".join(m)


def paket(mapa, **izmjene):
    """Corpusov raspored: <PROJEKT>/ (CSV + CIX + HORIZONTALNO_BUSENJE/) i sestrinska <PROJEKT_>/ s CPW-ovima."""
    p = os.path.join(mapa, "TEST PAKET")
    os.makedirs(os.path.join(p, "HORIZONTALNO_BUSENJE"))
    os.makedirs(os.path.join(mapa, "TEST_PAKET"))
    with open(os.path.join(mapa, "TEST_PAKET", "IV BIJELI NK_18.cpw"), "wb") as f:
        f.write(izmjene.get("cpw_iv", CPW_IV).encode("cp1250"))
    with open(os.path.join(mapa, "TEST_PAKET", "MDF CHAMPAGNE_19.cpw"), "wb") as f:
        f.write(CPW_MDF.encode("cp1250"))
    open(os.path.join(p, "TEST_PAKET.CSV"), "w", encoding="utf-8").write(izmjene.get("csv", CSV))
    cixi = izmjene.get("cix", {"1446A0000001": _cix(800, 560, 18, busenja=22, utor=2), "1446A0000002": _cix(864, 556, 18, busenja=4),
                              "1446A0000003": _cix(863, 536, 18), "1446A0000009": _cix(796, 888, 19),
                              "HORIZONTALNO_BUSENJE/2446A0000002": _cix(864, 556, 18, kant=12, tocaka=0)})
    for ime, txt in cixi.items():
        open(os.path.join(p, ime + ".cix"), "w").write(txt)
    return p


@pytest.fixture
def baza_c(baza):
    baza.execute("UPDATE materijal SET winstore_kod = 'IV001038-19' WHERE pantheon_ident = 'IV001038'")
    baza.commit()
    from hub.sifrarnici import prepoznaj as P
    P.ocisti_kes()
    return baza


def test_citac_cix(tmp_path):
    p = tmp_path / "a.cix"
    p.write_text(_cix(800, 560, 18, busenja=22, utor=2))
    d = cix_citaj.procitaj(str(p))
    assert (d["L"], d["W"], d["deb"], d["busenja"], d["busenja_h"], d["utora"], d["krivolinija"], d["ima_obradu"]) == (800, 560, 18, 22, 0, 2, False, True)
    assert d["opis"] == "22 bus, 2 utora" and cix_citaj.odgovara_elementu(d, 560, 800) and not cix_citaj.odgovara_elementu(d, 800, 561)
    p.write_text(_cix(864, 556, 18, kant=12, tocaka=0))
    assert cix_citaj.procitaj(str(p))["opis"] == "12 bus kant"
    p.write_text(_cix(796, 888, 4))
    assert cix_citaj.procitaj(str(p))["opis"] == "kontura" and not cix_citaj.procitaj(str(p))["ima_obradu"]
    p.write_text(_cix(796, 888, 4, tocaka=7))
    assert cix_citaj.procitaj(str(p))["krivolinija"]
    p.write_text("nista")
    with pytest.raises(ValueError):
        cix_citaj.procitaj(str(p))


def test_read_cpw_corpus_stupci(tmp_path):
    p = tmp_path / "x.cpw"
    p.write_bytes(CPW_IV.encode("cp1250"))
    els = nalog_io.read_cpw(str(p))
    assert els[1]["naziv"] == "EL1 - POD" and (els[1]["cjelina"], els[1]["pozicija"]) == ("EL1", "POD")
    assert (els[1]["program1"], els[1]["program2"], els[1]["cix"], els[1]["sifra_mat"]) == ("1446A0000002", "2446A0000002", "1446A0000002", "W908ST2-18")
    assert els[2]["program1"] == "" and els[2]["cix"] == "" and els[2]["corpus"]
    assert els[0]["traka"]["L"] == "BIJELA_NK-1/22" and els[0]["tip"]["O"] == "M"


def test_uvoz_paketa_i_izvoz(baza_c, tmp_path):
    p = paket(str(tmp_path / "corpus"))
    # suho: brojke bez upisa
    nid, izv = UC.uvezi_paket(baza_c, p, "TEST", kupac_kratki="PROBA", suho=True)
    assert nid is None and (izv["elemenata"], izv["komada"], izv["nesting"], izv["pila"], izv["cix"]) == (4, 5, 3, 1, 4)
    assert izv["projekt"] == "TEST_PAKET" and len(izv["cpw"]) == 2 and any("1446A0000009" in u for u in izv["upozorenja"])   # CIX bez elementa
    assert baza_c.execute("SELECT COUNT(*) FROM nalog").fetchone()[0] == 0
    # pravi uvoz — mapa zadana kao mapa projekta (CPW-ovi u sestrinskoj mapi)
    nid, izv = UC.uvezi_paket(baza_c, p, "TEST", kupac_kratki="PROBA")
    n = N.nalog(baza_c, nid)
    assert n["vrsta"] == "vlastita_proizvodnja" and n["izvor"] == "corpus" and n["corpus_projekt"] == "TEST_PAKET" and n["naziv"].startswith("PROBA_TEST_PAKET_")
    pr = N.pregled(baza_c, nid)
    assert pr["sazetak"]["elemenata"] == 4 and pr["sazetak"]["komada"] == 5 and pr["sazetak"]["za_potvrdu"] == 0
    putovi = {m["ident"]: (m["put"], m["put_prijedlog"]) for m in pr["materijali"]}
    assert putovi == {"IV000090": ("nesting", "nesting"), "IV001038": ("pila", "pila")}
    els = {e["naziv"]: e for m in pr["materijali"] for e in m["elementi"]}
    pod = N.element(baza_c, els["EL1 - POD"]["id"])
    assert (pod["cix_ime"], pod["cix_izvor"], pod["program1"], pod["program2"], pod["cjelina"], pod["pozicija"]) == ("1446A0000002", "corpus", "1446A0000002", "2446A0000002", "EL1", "POD")
    o = json.loads(pod["obrada_json"])
    assert o["ima_obradu"] and o["cix"]["put"].endswith("1446A0000002.cix") and o["cix2"]["put"].endswith(os.path.join("HORIZONTALNO_BUSENJE", "2446A0000002.cix"))
    assert pod["obrada"] == "4 bus, 12 bus kant"
    polica = N.element(baza_c, els["EL1 - Polica"]["id"])
    assert (polica["cix_ime"], polica["cix_izvor"], polica["program1"], polica["obrada"]) == ("1446A0000003", "corpus", None, "kontura")   # CIX iz CSV-a, bez programa
    ledja = N.element(baza_c, els["EL1 - LEDJA"]["id"])
    assert ledja["cix_ime"] is None and ledja["obrada_json"] is None
    assert {r[0] for r in baza_c.execute("SELECT ime FROM cix_registar")} == {"1446A0000001", "1446A0000002", "2446A0000002", "1446A0000003"}
    assert baza_c.execute("SELECT COUNT(*) FROM dokument WHERE nalog_id = ? AND vrsta = 'cix'", (nid,)).fetchone()[0] == 4
    # isti paket drugi put: Corpusova imena su zauzeta → stane prije upisa (D-23 / D-55)
    with pytest.raises(UC.CorpusGreska) as ex:
        UC.uvezi_paket(baza_c, p, "TEST", kupac_kratki="PROBA")
    assert "već pripada" in str(ex.value) and baza_c.execute("SELECT COUNT(*) FROM nalog").fetchone()[0] == 1 and not baza_c.conn.in_transaction
    # izvoz na nesting: Corpusovi CIX-ovi se kopiraju (oba), leđa idu na pilu
    r = EX.izvezi(baza_c, nid, str(tmp_path / "out"), "TEST", forsiraj=True)
    assert len(r["paketi"]) == 1 and r["paketi"][0]["cix_corpus"] == 4 and len(r["paketi"][0]["cix"]) == 4 and r["preskoceno"][0]["razlog"] == "ide na pilu"
    korijen = r["mapa"]
    assert open(os.path.join(korijen, "1446A0000001.cix")).read() == _cix(800, 560, 18, busenja=22, utor=2)
    assert os.path.exists(os.path.join(korijen, "HORIZONTALNO_BUSENJE", "2446A0000002.cix")) and os.path.exists(os.path.join(korijen, "1446A0000003.cix"))
    csv = nalog_io.read_ppnest_csv(r["paketi"][0]["csv"])
    assert [(e["cix"], e["program1"], e["program2"], e["cjelina"], e["pozicija"]) for e in csv][1] == ("1446A0000002", "1446A0000002", "2446A0000002", "EL1", "POD")
    rp = EP.izvezi(baza_c, nid, str(tmp_path / "out"), "TEST", forsiraj=True)
    assert len(rp["paketi"]) == 1 and rp["paketi"][0]["elemenata"] == 1 and rp["preskoceno"][0]["razlog"] == "ide na nesting"
    # izvorni CIX nestao s diska → izvoz stane s porukom, ne s pola paketa
    os.remove(o["cix2"]["put"])
    with pytest.raises(EX.ExportGreska) as ex:
        EX.izvezi(baza_c, nid, str(tmp_path / "out2"), "TEST", forsiraj=True)
    assert "ne postoji" in str(ex.value) and not os.path.exists(str(tmp_path / "out2"))


def test_paket_s_greskom_ne_otvara_nalog(baza_c, tmp_path):
    # nema CIX-a za program
    p = paket(str(tmp_path / "a"), cix={"1446A0000001": _cix(800, 560, 18), "1446A0000003": _cix(863, 536, 18), "HORIZONTALNO_BUSENJE/2446A0000002": _cix(864, 556, 18, kant=12, tocaka=0)})
    with pytest.raises(UC.CorpusGreska) as ex:
        UC.uvezi_paket(baza_c, p, "TEST")
    assert "nema CIX datoteke 1446A0000002" in str(ex.value)
    # CIX s krivim mjerama
    p = paket(str(tmp_path / "b"), cix={"1446A0000001": _cix(800, 500, 18), "1446A0000002": _cix(864, 556, 18), "1446A0000003": _cix(863, 536, 18),
                                        "HORIZONTALNO_BUSENJE/2446A0000002": _cix(864, 556, 18, kant=12, tocaka=0)})
    with pytest.raises(UC.CorpusGreska) as ex:
        UC.uvezi_paket(baza_c, p, "TEST")
    assert "mjere 800x500" in str(ex.value)
    # element s obradom u CIX-u koji nije u CSV listi (išao bi na pilu s bušenjem, D-29)
    csv2 = "\n".join(l for l in CSV.splitlines() if not l.startswith("1;")) + "\n"
    p = paket(str(tmp_path / "c"), csv=csv2)
    with pytest.raises(UC.CorpusGreska) as ex:
        UC.uvezi_paket(baza_c, p, "TEST")
    assert "ima CNC obradu" in str(ex.value) and "nije u CSV listi" in str(ex.value)
    # CSV redak bez elementa u CPW-u
    p = paket(str(tmp_path / "d"), csv=CSV.replace("3;;EL1;0;Polica;536x863;536.00;863.00;2", "3;;EL1;0;Polica;536x999;536.00;999.00;2"))
    with pytest.raises(UC.CorpusGreska) as ex:
        UC.uvezi_paket(baza_c, p, "TEST")
    assert "nema odgovarajući element u CPW-u" in str(ex.value)
    assert baza_c.execute("SELECT COUNT(*) FROM nalog").fetchone()[0] == 0 and not baza_c.execute("SELECT 1 FROM cix_registar").fetchone()
    with pytest.raises(UC.CorpusGreska):
        UC.uvezi_paket(baza_c, str(tmp_path / "nema"), "TEST")


def test_brisanje_naloga_odvezuje_imena(baza_c, tmp_path):
    p = paket(str(tmp_path / "corpus"))
    nid, _ = UC.uvezi_paket(baza_c, p, "TEST", kupac_kratki="PROBA")
    N.obrisi_nalog(baza_c, nid, "TEST")
    assert baza_c.execute("SELECT COUNT(*) FROM cix_registar WHERE element_id IS NULL").fetchone()[0] == 4      # imena ostaju zauzeta (D-23)
    nid2, _ = UC.uvezi_paket(baza_c, p, "TEST", kupac_kratki="PROBA")   # isti Corpus paket ponovno: ime bez elementa smije preuzeti (ista datoteka)
    assert nid2 and baza_c.execute("SELECT COUNT(*) FROM cix_registar WHERE element_id IS NOT NULL").fetchone()[0] == 4
    # Hubovo ime (H…) se nikad ne vraća: element s ručno upisanim Hub imenom drugog (obrisanog) elementa dobiva novo
    baza_c.execute("INSERT INTO cix_registar (ime, element_id, nalog_id, izvor, kada) VALUES ('H0000001', NULL, NULL, 'hub', '2026')")
    assert not EX.registriraj(baza_c, "H0000001", 999, nid2, "hub") and not EX.registriraj(baza_c, "H0000001", 999, nid2, "corpus")


def test_api_uvoz_corpus(baza_c, monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    from hub.sifrarnici import prepoznaj as P
    monkeypatch.setenv("HUB_DB", str(baza_c.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    p = paket(str(tmp_path / "corpus"))
    c = TestClient(A.app, raise_server_exceptions=False)
    try:
        r = c.post("/api/nalozi/uvoz-corpus", json=dict(mapa=p, kupac_kratki="PROBA", suho=True))
        assert r.status_code == 200 and r.json()["nesting"] == 3 and r.json().get("nalog_id") is None
        r = c.post("/api/nalozi/uvoz-corpus", json=dict(mapa=p, kupac_kratki="PROBA", tko="SINISA"))
        assert r.status_code == 200 and r.json()["nalog_id"] and r.json()["sazetak"]["elemenata"] == 4 and r.json()["za_potvrdu"] == []
        r = c.post("/api/nalozi/uvoz-corpus", json=dict(mapa=p, kupac_kratki="PROBA"))
        assert r.status_code == 400 and "već pripada" in r.text
        r = c.post("/api/nalozi/uvoz-corpus", json=dict(mapa=str(tmp_path / "nema")))
        assert r.status_code == 400 and not A.veza().in_transaction
    finally:
        A._veza = None
