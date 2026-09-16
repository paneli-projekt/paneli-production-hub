# -*- coding: utf-8 -*-
"""Korak 4: obračun naloga → stavke ponude (D-18/D-19/D-20, pravila skilla krojna-ponuda), verzije ponude, eSlog 220, potvrda kupca (D-40),
korekcija po stvarnom stanju za vlastitu proizvodnju (D-56). Stvarni dio: HUMER kupčev PPW vs Pantheon ponuda 26-010-002823."""
import glob
import os
import xml.etree.ElementTree as ET
import pytest

from hub.nalozi import nalozi as N, obracun as OC, ponuda as PO, provjera as PR, rezultat_nesting as RN
from hub.alati import benchmark_ponuda as BP
from tests.test_nalozi import baza  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog
from tests.test_sifrarnik import DATA, stvarni, stvarna_baza  # noqa: F401

USLUGE = [("US000002", "USLUGA REZANJA", "M2", 2.04), ("US000011", "USLUGA KANTIRANJA 2/22", "M", 1.04), ("US000013", "USLUGA REZANJA MDF", "M2", 1.0),
          ("US000016", "USLUGA NUT", "M", 1.4), ("US000149", "USLUGA P-BUSENJA 35", "KOM", 0.88), ("OK000218", "PVC NOGA 100", "KOM", 0.32)]


@pytest.fixture
def baza_o(baza):
    for ident, naziv, jm, cij in USLUGE:
        baza.execute("INSERT OR IGNORE INTO pantheon_ident (ident, naziv, klasif, jm, cijena_prodajna, cijena_neto, pdv, aktivan, azurirano) VALUES (?,?,?,?,?,?,25,1,'t')",
                     (ident, naziv, ident[:2], jm, round(cij * 1.25, 4), cij))
    baza.commit()
    return baza


def test_pravilo_nacete_ploce():
    pl = 2800 * 2070 / 1e6                                         # 5.796
    assert OC.pravilo_nacete_ploce(5.0, 1, pl)[0] == 5.8 and "cijela" in OC.pravilo_nacete_ploce(5.0, 1, pl)[1]        # 86 % > 2/3
    assert OC.pravilo_nacete_ploce(8.5, 2, pl) == (8.75, "načeta ploča 47 % (1/3–2/3) → +0,25 m²", False)
    m2, opis, provjeri = OC.pravilo_nacete_ploce(7.54, 2, pl)      # Blago basanit: 30 % → +0,25 i PROVJERI
    assert m2 == 7.79 and provjeri
    m2, opis, _ = OC.pravilo_nacete_ploce(6.0, 2, pl)              # 3,5 % → minimum 1/3
    assert abs(m2 - (5.796 + 5.796 / 3)) < 0.01 and "minimum 1/3" in opis
    assert OC.pravilo_nacete_ploce(11.59, 2, pl)[1] is None        # pune ploče: bez pravila


def test_obracun_stavke(baza_o):
    nid, nm, e1, e2 = _nalog(baza_o, status="ponuda")              # IV000090, POD 800×560 ×2 + BOK 400×300, rub L = ABS-ISTI (TR000168 1/22)
    N.uredi_element(baza_o, e2["id"], "TEST", napomena="NUT DUZA")
    baza_o.execute("INSERT INTO okov_stavka (nalog_id, pantheon_ident, naziv, kom, jm, status) VALUES (?, 'OK000218', 'PVC NOGA', 8, 'KOM', 'potvrdjeno')", (nid,))
    baza_o.execute("INSERT INTO okov_stavka (nalog_id, naziv, kom, jm, status) VALUES (?, 'SARKA', 4, 'KOM', 'za_potvrdu')", (nid,))
    baza_o.commit()
    r = OC.izracunaj(baza_o, nid)
    po = {s["pantheon_ident"]: s for s in r["stavke"]}
    assert [s["grupa"] for s in r["stavke"]] == ["materijal", "rezanje", "usluga", "traka", "kantiranje", "okov"]   # redoslijed kao u ponudama ureda
    # 1 ploča 2800×2070: PW-metoda daje korisni ostatak, pravilo načete ploče → cijela / +0,25 / min 1/3 — količina je iz PW m² + pravilo
    assert po["IV000090"]["jm"] == "M2" and 1.93 <= po["IV000090"]["kolicina"] <= 5.8 and "PW-metoda" in po["IV000090"]["pravilo"]
    assert po["US000002"]["kolicina"] == po["IV000090"]["kolicina"]
    # traka: (800×2 + 400) mm × 1,10 = 2,20 m → 3 m naviše; kantiranje = točno 2,20 m (D-20)
    assert po["TR000168"]["kolicina"] == 3 and po["US000011"]["kolicina"] == 2.2
    assert po["US000016"]["kolicina"] == 0.4 and "NUT" in po["US000016"]["pravilo"]
    assert po["OK000218"]["kolicina"] == 8 and any("SARKA" in u for u in r["upozorenja"])
    # cijene iz šifrarnika, rabat: materijal / usluge s naloga (zadano 15 / 20)
    n = N.nalog(baza_o, nid)
    assert po["IV000090"]["cijena"] == 20 and po["IV000090"]["rabat"] == r["rabat_materijal"] == n["rabat_materijal"] and po["US000002"]["rabat"] == r["rabat_usluge"] == n["rabat_usluge"]
    assert po["TR000168"]["cijena"] == 0.24 and po["OK000218"]["rabat"] == n["rabat_materijal"]
    assert r["neto"] == round(sum(s["iznos"] for s in r["stavke"]), 2) and r["ukupno"] == round(r["neto"] * 1.25, 2)
    # bez pravila načete ploče = čisti PW m²
    r2 = OC.izracunaj(baza_o, nid, pravila=False)
    assert {s["pantheon_ident"]: s for s in r2["stavke"]}["IV000090"]["kolicina"] <= po["IV000090"]["kolicina"]
    # upis radnih stavki, ponovni upis zamjenjuje
    OC.upisi(baza_o, nid, "TEST")
    OC.upisi(baza_o, nid, "TEST")
    assert len(OC.stavke(baza_o, nid)) == 6 and baza_o.execute("SELECT COUNT(*) FROM obracun_stavka WHERE nalog_id = ?", (nid,)).fetchone()[0] == 6


def test_ponuda_verzije_eslog_potvrda(baza_o, tmp_path):
    nid, nm, e1, e2 = _nalog(baza_o)                               # status unos
    n = N.nalog(baza_o, nid)
    v1 = PO.nova_verzija(baza_o, nid, "IVANA")
    assert v1["verzija"] == 1 and v1["status"] == "nacrt" and len(v1["stavke"]) == 4 and v1["iznos_pdv"] == round(v1["iznos_neto"] * 0.25, 2)
    assert N.nalog(baza_o, nid)["status"] == "ponuda"               # unos → ponuda
    v2 = PO.nova_verzija(baza_o, nid, "IVANA", pravila=False)
    assert v2["verzija"] == 2 and {v["verzija"]: v["status"] for v in PO.verzije(baza_o, nid)} == {1: "zamijenjena", 2: "nacrt"}
    assert baza_o.execute("SELECT COUNT(*) FROM obracun_stavka WHERE ponuda_verzija_id = ?", (v1["id"],)).fetchone()[0] == 4   # snimka ostaje
    # eSlog XML
    xml, broj = PO.eslog_xml(baza_o, v2["id"])
    t = ET.fromstring(xml)
    assert t.tag == "NarociloEnostavno" and t.findtext("Dokument/GlavaDokumenta/VrstaDokumenta") == "220" and broj.startswith("HUB-")
    post = t.findall("Dokument/PostavkeDokumenta")
    assert len(post) == 4 and t.findtext("Dokument/KontrolnaSekcija/VrednostKontrole") == "4"
    assert post[0].findtext("DodatnaIdentifikacijaArtikla/StevilkaArtiklaDodatna") == "IV000090" and post[0].findtext("KolicinaArtikla/EnotaMere") == "MTK"
    assert post[0].findtext("OdstotkiPostavk/OdstotekPostavke") == "%.6f" % n["rabat_materijal"] and post[1].findtext("OdstotkiPostavk/OdstotekPostavke") == "%.6f" % n["rabat_usluge"]
    partneri = [p.findtext("NazivNaslovPodjetja/VrstaPartnerja") for p in t.findall("Dokument/PodatkiPodjetja")]
    assert partneri == ["BY", "DP", "SU", "OB"] and t.findall("Dokument/PodatkiPodjetja")[2].findtext("NazivNaslovPodjetja/NazivPartnerja/NazivPartnerja1") == (n["kupac"]["pantheon_subjekt_racun"] or n["kupac"]["naziv"])
    # poslana (kupac bez e-maila → upozorenje), pa potvrda → nalog potvrđen, XML na disku, Pantheon broj
    p = PO.oznaci_poslanu(baza_o, v2["id"], "IVANA")
    assert p["status"] == "poslana" and ("upozorenje" in p) == (not n["kupac_email"])
    r = PO.potvrdi(baza_o, v2["id"], "IVANA", ponuda_pantheon="26-010-009999", mapa_eslog=str(tmp_path), nacin="telefon", rok_obecan="2026-09-30")
    assert r["status"] == "potvrdjena" and r["nalog"]["status"] == "potvrdjeno" and r["nalog"]["ponuda_pantheon"] == "26-010-009999" and r["nalog"]["rok_obecan"] == "2026-09-30"
    assert os.path.isfile(r["eslog"]) and r["eslog"].endswith("eSlog_220_26-010-009999.xml") and "26-010-009999" in open(r["eslog"], encoding="utf-8").read()
    assert baza_o.execute("SELECT COUNT(*) FROM dokument WHERE nalog_id = ? AND vrsta = 'eslog'", (nid,)).fetchone()[0] == 1
    with pytest.raises(PO.PonudaGreska):
        PO.potvrdi(baza_o, v2["id"], "IVANA")                      # već potvrđena
    with pytest.raises(PO.PonudaGreska):
        PO.nova_verzija(baza_o, nid, "IVANA")                      # nakon potvrde nema nove verzije
    with pytest.raises(PO.PonudaGreska):
        PO.korekcija_po_stvarnom(baza_o, nid, "IVANA")             # usluga nije vlastita proizvodnja


def test_izdatnica_vlastita_proizvodnja(baza_o, tmp_path):
    k = N.kupci_kljuc = None
    from hub.nalozi import kupci as K
    kid = K.trazi_kupce(baza_o, "", limit=1)[0]["id"]
    mid = baza_o.execute("SELECT id FROM materijal WHERE pantheon_ident = 'IV000090'").fetchone()[0]
    nid = N.novi_nalog(baza_o, "TEST", kupac_id=kid, projekt="KUHINJA", vrsta="vlastita_proizvodnja", izvor="corpus")["id"]
    nm = N.dodaj_materijal(baza_o, nid, "TEST", materijal_id=mid)[0]["id"]
    N.dodaj_element(baza_o, nm, "TEST", L=800, W=560, kom=4, naziv="POD")
    v = PO.nova_verzija(baza_o, nid, "TEST")
    PO.potvrdi(baza_o, v["id"], "TEST", mapa_eslog=str(tmp_path))
    for st in ("skladiste", "pila_nesting", "proizvodnja"):
        N.postavi_status(baza_o, nid, st, "TEST")
    # bez bNest rezultata: izdatnica = obračun + upozorenje
    r0 = PO.korekcija_po_stvarnom(baza_o, nid, "TEST", upisi=False)
    assert any("nema bNest" in u for u in r0["upozorenja"])
    baza_o.execute("INSERT INTO optimizacija (nalog_materijal_id, engine, nacin, datum, broj_ploca, iskoristenje, m2_dijelova, m2_ploca) VALUES (?, 'bNest', 'nesting', 't', 1, 0.31, 1.79, 5.796)", (nm,))
    baza_o.commit()
    r = PO.korekcija_po_stvarnom(baza_o, nid, "TEST", mapa_eslog=str(tmp_path))
    po = {s["pantheon_ident"]: s for s in r["stavke"]}
    assert r["status"] == "izdatnica" and po["IV000090"]["kolicina"] == 5.8 and "stvarno potrošeno" in po["IV000090"]["pravilo"] and po["US000002"]["kolicina"] == 5.8
    assert os.path.basename(r["eslog"]).startswith("eSlog_220_IZD-") and N.nalog(baza_o, nid)["status"] == "izdatnica"
    assert {x["verzija"]: x["status"] for x in PO.verzije(baza_o, nid)} == {1: "potvrdjena", 2: "izdatnica"}
    N.postavi_status(baza_o, nid, "zatvoren", "TEST")
    # usluga ne može u 'izdatnica'
    nid2, _, _, _ = _nalog(baza_o, status="potvrdjeno")
    for st in ("skladiste", "pila_nesting", "proizvodnja"):
        N.postavi_status(baza_o, nid2, st, "TEST")
    with pytest.raises(N.NalogGreska):
        N.postavi_status(baza_o, nid2, "izdatnica", "TEST")


def test_api_obracun_ponuda(baza_o, monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    from hub.sifrarnici import prepoznaj as P
    monkeypatch.setenv("HUB_DB", str(baza_o.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    nid, nm, e1, e2 = _nalog(baza_o)
    c = TestClient(A.app, raise_server_exceptions=False)
    try:
        r = c.get("/api/nalog/%d/obracun" % nid)
        assert r.status_code == 200 and len(r.json()["stavke"]) == 4 and r.json()["neto"] > 0
        r = c.post("/api/nalog/%d/ponude" % nid, json=dict(tko="IVANA"))
        assert r.status_code == 200 and r.json()["verzija"] == 1
        vid = r.json()["id"]
        assert c.get("/api/nalog/%d/ponude" % nid).json()[0]["stavki"] == 4 and c.get("/api/ponuda/%d" % vid).json()["stavke"][0]["pantheon_ident"] == "IV000090"
        r = c.post("/api/ponuda/%d/eslog" % vid, json=dict(mapa=str(tmp_path)))
        assert r.status_code == 200 and os.path.isfile(r.json()["eslog"])
        r = c.post("/api/ponuda/%d/potvrdi" % vid, json=dict(ponuda_pantheon="26-010-000001", nacin="mail", mapa=str(tmp_path), tko="IVANA"))
        assert r.status_code == 200 and r.json()["nalog"]["status"] == "potvrdjeno"
        assert c.post("/api/ponuda/%d/potvrdi" % vid, json=dict()).status_code == 400 and not A.veza().in_transaction
        assert c.get("/api/ponuda/9999").status_code == 400
    finally:
        A._veza = None


@stvarni
def test_stvarni_humer_vs_ponuda(stvarna_baza):
    """HUMER kupčev PPW → Hub obračun vs Pantheon ponuda 26-010-002823: iste cijene za sve zajedničke idente, m² ploča unutar +5 %."""
    pdf = glob.glob(os.path.join(DATA, "_HUMER_OMIS", "05_pantheon", "*.pdf"))
    if not pdf:
        pytest.skip("nema ponude")
    pon = BP.ponuda_iz_pdf(pdf[0])
    assert pon and pon["broj"] == "26-010-002823" and len(pon["stavke"]) >= 70
    nid, _ = PR._uvezi(stvarna_baza, "HUMER_OMIS", sorted(glob.glob(os.path.join(DATA, "_HUMER_OMIS", "01_ulaz_kupca", "*.[cC][pP][wW]"))), "kupac_ppw")
    hub = OC.izracunaj(stvarna_baza, nid)
    u = BP.usporedi(hub, pon)
    assert u["zajednickih"] >= 12 and u["cijena_ista"] == u["zajednickih"]                    # sve cijene iz Pantheona
    po = {r["ident"]: r for r in u["redovi"]}
    assert po["IV001210"]["ponuda"] == 30.97 and 30.0 <= po["IV001210"]["hub"] <= 30.97   # JELA TAVERNA: isto ili malo bolje od PW-a (korak 5)
    assert po["IV000002"]["hub"] == po["IV000002"]["ponuda"] == 5.8
    assert -8 <= po["IV000090"]["razlika_pct"] <= 5 and abs(po["US000002"]["razlika_pct"]) <= 8
    assert abs(u["neto_hub_zajednicki"] - u["neto_ponuda_zajednicki"]) / u["neto_ponuda_zajednicki"] < 0.05   # zajednički identi: unutar 5 % (Hub sada troši manje ploča od PW-a)
    assert not [i for i in u["samo_ponuda"] if i.startswith("IV")]                            # nijedan materijal ne fali
    PR.obrisi_provjere(stvarna_baza)
