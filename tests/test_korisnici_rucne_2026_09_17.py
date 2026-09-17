# -*- coding: utf-8 -*-
"""Igorove napomene 17. 9.: prijava s lozinkom (D-88), potpis u mailu, ručne stavke ponude (D-87), sličica slaganja na ekranu, PDF inline."""
import pytest

from hub import korisnici as KO
from hub.nalozi import obracun as OC, optimiziraj as OP
from hub.ispis import sheme_png as SPNG
from tests.test_nalozi import baza  # noqa: F401
from tests.test_api import klijent  # noqa: F401
from tests.test_obracun_ponuda import baza_o  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog


def test_lozinka_prijava_i_potpis(baza_o):
    c = baza_o
    assert not KO.prijava_obavezna(c)
    r = KO.prijava(c, "ivana")                                   # bez lozinke: ulazi, ali je mora postaviti
    assert r["treba_lozinka"] and r["token"] and KO.iz_tokena(c, r["token"])["oznaka"] == "IVANA"
    with pytest.raises(KO.KorisnikGreska):
        KO.postavi_lozinku(c, "IVANA", "abc")                    # prekratko
    p = KO.postavi_lozinku(c, "IVANA", "tajna1", "IVANA", zadrzi_token=r["token"])
    assert p["prijava_ukljucena"] and KO.prijava_obavezna(c)     # prva lozinka uključi obaveznu prijavu
    assert KO.iz_tokena(c, r["token"])["oznaka"] == "IVANA"      # vlastita sesija ostaje
    with pytest.raises(KO.KorisnikGreska, match="pogrešna"):
        KO.prijava(c, "IVANA", "kriva")
    r2 = KO.prijava(c, "IVANA", "tajna1")
    assert not r2["treba_lozinka"]
    KO.odjava(c, r2["token"])
    assert KO.iz_tokena(c, r2["token"]) is None
    with pytest.raises(KO.KorisnikGreska):
        KO.prijava(c, "WEB")                                      # sustavski račun se ne prijavljuje
    assert c.execute("SELECT lozinka_hash FROM korisnik WHERE oznaka = 'IVANA'").fetchone()[0].startswith("pbkdf2$")
    # potpis: ime / funkcija / tvrtka / kontakt; vlastiti tekst ima prednost
    KO.upisi(c, "IVANA", ime="Ivana Ivić", funkcija="prodaja", email="ivana@paneliprojekt.hr", telefon="031 123 456", tko="IGOR")
    pot = KO.potpis(c, "IVANA")
    assert pot.splitlines() == ["Ivana Ivić", "prodaja", "Paneli projekt d.o.o.", "031 123 456 · ivana@paneliprojekt.hr"]
    KO.upisi(c, "IVANA", potpis="Ivana\nPaneli", tko="IGOR")
    assert KO.potpis(c, "IVANA") == "Ivana\nPaneli"
    assert KO.potpis(c, "WEB") == "Paneli projekt d.o.o." and KO.potpis(c, "NEMA") == "Paneli projekt d.o.o."
    k = KO.upisi(c, "MARKO", ime="Marko", uloga="ured", tko="IGOR")
    assert k["oznaka"] == "MARKO" and not k["ima_lozinku"]


def test_mail_tekst_nosi_potpis_posiljatelja(baza_o, monkeypatch):
    from hub.nalozi import ponuda as PO, mail as M
    c = baza_o
    OP.AUTO_POTVRDA = True
    nid, nm, e1, e2 = _nalog(c, status="ponuda")
    v = PO.nova_verzija(c, nid, "IVANA", potvrdi_opt=True)
    KO.upisi(c, "IVANA", ime="Ivana Ivić", funkcija="prodaja", email="ivana@paneliprojekt.hr", tko="IGOR")
    uhvaceno = {}
    def lazni(conn, na, predmet, tekst, html=None, prilozi=(), cc=None, tko="web", nalog_id=None, suho=False):
        uhvaceno.update(tekst=tekst, tko=tko, msg=M.poruka(M.postavke_smtp(conn), na, predmet, tekst, html, prilozi, cc, "Ivana Ivić <ivana@paneliprojekt.hr>"))
        return dict(poslano=False, na=na, cc=None, predmet=predmet, prilozi=[], message_id="x", kada="")
    monkeypatch.setattr(M, "posalji", lazni)
    PO.posalji(c, v["id"], "IVANA", na="kupac@example.com", suho=True)
    assert uhvaceno["tekst"].rstrip().endswith("Lijep pozdrav,\nIvana Ivić\nprodaja\nPaneli projekt d.o.o.\nivana@paneliprojekt.hr")
    assert uhvaceno["msg"]["Reply-To"] == "Ivana Ivić <ivana@paneliprojekt.hr>"


def test_rucna_stavka_u_obracunu(baza_o):
    c = baza_o
    OP.AUTO_POTVRDA = True
    nid, nm, e1, e2 = _nalog(c, status="ponuda")
    ident = c.execute("SELECT ident FROM pantheon_ident WHERE ident LIKE 'US%' ORDER BY ident LIMIT 1").fetchone()[0]
    with pytest.raises(OC.ObracunGreska, match="šifrarniku"):
        OC.dodaj_rucnu(c, nid, "NEMA_TOGA", 1, cijena=10)          # ponuda ide u Pantheon samo s pravim identom
    with pytest.raises(OC.ObracunGreska):
        OC.dodaj_rucnu(c, nid, ident, 0)
    r1 = OC.dodaj_rucnu(c, nid, ident, 2, grupa="usluga", napomena="dodatno", tko="IVANA")
    r2 = OC.dodaj_rucnu(c, nid, ident, 3, grupa="okov", naziv="Montaža na objektu", jm="H", cijena=35, rabat=0, tko="IVANA")
    ob = OC.izracunaj(c, nid)
    rucne = [s for s in ob["stavke"] if s.get("rucna_id")]
    assert [s["rucna_id"] for s in rucne] == [r1["id"], r2["id"]]
    assert rucne[0]["pravilo"] == "ručno: dodatno" and rucne[0]["kolicina"] == 2
    assert rucne[1]["naziv"] == "Montaža na objektu" and rucne[1]["jm"] == "H" and rucne[1]["cijena"] == 35 and rucne[1]["iznos"] == 105 and rucne[1]["grupa"] == "okov"
    OC.upisi(c, nid, "IVANA")                                       # upis u obracun_stavka prolazi (FK na ident)
    assert c.execute("SELECT COUNT(*) FROM obracun_stavka WHERE nalog_id = ? AND pravilo LIKE 'ručno%'", (nid,)).fetchone()[0] == 2
    assert len(OC.rucne(c, nid)) == 2 and OC.rucne(c, nid)[0]["u_sifrarniku"]
    r3 = OC.promijeni_rucnu(c, r2["id"], "IVANA", kolicina=4, cijena=None, rabat=10)      # korekcija u tablici: količina, cijena natrag na Pantheon, rabat 10 %
    assert r3["kolicina"] == 4 and r3["cijena"] is None and r3["rabat"] == 10
    s3 = [s for s in OC.izracunaj(c, nid)["stavke"] if s.get("rucna_id") == r2["id"]][0]
    assert s3["kolicina"] == 4 and s3["rabat"] == 10 and s3["cijena"] is not None
    with pytest.raises(OC.ObracunGreska):
        OC.promijeni_rucnu(c, r2["id"], "IVANA", kolicina=0)
    OC.obrisi_rucnu(c, r1["id"], "IVANA")
    assert len(OC.rucne(c, nid)) == 1
    with pytest.raises(OC.ObracunGreska):
        OC.obrisi_rucnu(c, r1["id"])


def test_slicica_slaganja_i_pregled(baza_o, tmp_path):
    pytest.importorskip("matplotlib")
    c = baza_o
    OP.AUTO_POTVRDA = False
    nid, nm, e1, e2 = _nalog(c, status="ponuda")
    p = OP.predlozi(c, nm, "auto", "najbolje", "IVANA")
    put = SPNG.png(c, p["id"], str(tmp_path / "sve.png"))
    assert put and open(put, "rb").read(8) == b"\x89PNG\r\n\x1a\n"
    put1 = SPNG.png(c, p["id"], str(tmp_path / "l1.png"), visina_px=600, list_br=1)
    assert put1 and (tmp_path / "l1.png").stat().st_size > 1000
    assert SPNG.png(c, p["id"], str(tmp_path / "l9.png"), list_br=99) is None
    pr = SPNG.pregled(c, p["id"])
    assert pr["listovi"][0]["br"] == 1 and pr["elementi"] and pr["statistika"]["ploca"] == p["broj_ploca"]
    assert SPNG.png(c, 999999) is None


def test_api_prijava_i_rucne(klijent):
    """API: bez lozinke sve prolazi; prva lozinka → 401 bez kolačića; s kolačićem radi; sheme.png i PDF inline."""
    ja = klijent.get("/api/ja").json()
    assert ja["korisnik"] is None and not ja["prijava_obavezna"] and any(x["oznaka"] == "IGOR" for x in ja["oznake"])
    assert klijent.get("/api/korisnici").status_code == 200                       # bootstrap: bez lozinke i bez prijave
    r = klijent.post("/api/korisnici", json={"oznaka": "IGOR", "lozinka": "test1234", "email": "igor@paneliprojekt.hr", "funkcija": "direktor"}).json()
    assert r["ima_lozinku"] and r["email"] == "igor@paneliprojekt.hr"
    assert klijent.get("/api/ja").json()["prijava_obavezna"]
    klijent.cookies.clear()
    assert klijent.get("/api/nalozi").status_code == 401 and klijent.get("/api/nalozi").json()["detail"] == "prijava"
    assert klijent.get("/api/zdravlje").status_code == 200                        # slobodno
    assert klijent.post("/api/prijava", json={"oznaka": "IGOR", "lozinka": "kriva"}).status_code == 401
    r = klijent.post("/api/prijava", json={"oznaka": "igor", "lozinka": "test1234"})
    assert r.status_code == 200 and not r.json()["treba_lozinka"] and "hub_sesija" in r.cookies
    assert klijent.get("/api/nalozi").status_code == 200
    ja = klijent.get("/api/ja").json()
    assert ja["korisnik"]["oznaka"] == "IGOR" and "direktor" in ja["potpis"]
    assert klijent.get("/api/korisnici/IGOR/potpis").json()["potpis"].startswith("Igor")
    # prva prijava korisnika bez lozinke: prazna lozinka ulazi, treba_lozinka
    k2 = klijent.__class__(klijent.app)
    r = k2.post("/api/prijava", json={"oznaka": "IVANA", "lozinka": ""})
    assert r.status_code == 200 and r.json()["treba_lozinka"]
    assert k2.post("/api/ja/lozinka", json={"nova": "ivana1"}).status_code == 200
    assert k2.get("/api/ja").json()["korisnik"]["oznaka"] == "IVANA"             # vlastita sesija ostaje
    assert k2.get("/api/korisnici").status_code == 403                            # nije admin
    assert k2.post("/api/ja/lozinka", json={"nova": "ivana2", "stara": "kriva"}).status_code == 400
    assert k2.post("/api/odjava").status_code == 200 and k2.get("/api/nalozi").status_code == 401
    # ručne stavke i pretraga identa
    assert klijent.get("/api/sifrarnik/identi?q=US").json()
    assert klijent.get("/api/optimizacija/999999/sheme.png").status_code == 404


def test_korekcija_izracunate_stavke_i_napomena(baza_o):
    """D-90: ured smije za tu ponudu ispraviti količinu / cijenu / rabat izračunate stavke; napomena ponude ide na dokument."""
    from hub.nalozi import nalozi as N, ponuda as PO
    c = baza_o
    OP.AUTO_POTVRDA = True
    nid, nm, e1, e2 = _nalog(c, status="ponuda")
    ob = OC.izracunaj(c, nid)
    traka = [s for s in ob["stavke"] if s["grupa"] == "traka"][0]
    kant = [s for s in ob["stavke"] if s["grupa"] == "kantiranje"][0]
    assert traka["pravilo"] == "" and kant["pravilo"] == "" and kant["kolicina"] == traka["kolicina"]     # bez napomene o nadmjeri; kantiranje = traka
    assert traka["kljuc"].startswith("traka|") and "korekcija" not in traka
    r = OC.korigiraj_stavku(c, nid, traka["kljuc"], "IVANA", kolicina=5, rabat=12)
    assert r["kolicina"] == 5 and r["rabat"] == 12 and r["cijena"] is None
    t2 = [s for s in OC.izracunaj(c, nid)["stavke"] if s["grupa"] == "traka"][0]
    assert t2["kolicina"] == 5 and t2["rabat"] == 12 and t2["korekcija"] == {"kolicina": 5.0, "rabat": 12.0} and abs(t2["iznos"] - round(5 * t2["cijena"] * 0.88, 2)) < 0.011
    OC.korigiraj_stavku(c, nid, traka["kljuc"], "IVANA", rabat="")                                  # rabat natrag na nalog, količina ostaje
    t3 = [s for s in OC.izracunaj(c, nid)["stavke"] if s["grupa"] == "traka"][0]
    assert t3["kolicina"] == 5 and t3["rabat"] != 12
    with pytest.raises(OC.ObracunGreska):
        OC.korigiraj_stavku(c, nid, traka["kljuc"], "IVANA", kolicina=0)
    OC.korigiraj_stavku(c, nid, traka["kljuc"], "IVANA")                                            # ukloni korekciju
    assert "korekcija" not in [s for s in OC.izracunaj(c, nid)["stavke"] if s["grupa"] == "traka"][0]
    # zbroji iste idente (opcija naloga): drugi materijal s istom uslugom rezanja → jedan redak
    mid2 = c.execute("SELECT id FROM materijal WHERE pantheon_ident != 'IV000090' AND vrsta = 'IV' LIMIT 1").fetchone()
    if mid2:
        nm2 = N.dodaj_materijal(c, nid, "TEST", materijal_id=mid2[0])[0]["id"]
        N.dodaj_element(c, nm2, "TEST", L=500, W=400, kom=2, naziv="X")
        OP.AUTO_POTVRDA = True
        rez = [s for s in OC.izracunaj(c, nid)["stavke"] if s["pantheon_ident"] == "US000002"]
        assert len(rez) == 2
        N.uredi_nalog(c, nid, "IVANA", zbroji_idente=1)
        rez2 = [s for s in OC.izracunaj(c, nid)["stavke"] if s["pantheon_ident"] == "US000002"]
        assert len(rez2) == 1 and abs(rez2[0]["kolicina"] - (rez[0]["kolicina"] + rez[1]["kolicina"])) < 0.001 and rez2[0]["zbrojeno"] == 2
        N.uredi_nalog(c, nid, "IVANA", zbroji_idente=0)
    N.uredi_nalog(c, nid, "IVANA", napomena_ponude="Isporuka franco Osijek.")
    v = PO.nova_verzija(c, nid, "IVANA", potvrdi_opt=True)
    from hub.nalozi import ponuda_pdf as PP
    d = PP.podaci(c, v["id"])
    assert d["napomena"] == "Isporuka franco Osijek." and d["bruto"] >= d["neto"] - 0.02 and "10 %" not in PP.html(c, v["id"])   # bruto/neto: zaokruživanje po stavci


# ---------------------------------------------------------------- PanelWizard .pnl (Igor, 17. 9.: „uvoz ne da .pnl iz PW-a“)
import os

DATA = os.environ.get("HUB_TEST_DATA")
PNL_MAPA = os.path.join(DATA or "", "_BLAGO_ADRIJANA", "02_panelwizard")


@pytest.mark.skipif(not DATA or not os.path.isdir(PNL_MAPA), reason="HUB_TEST_DATA nije postavljen")
def test_read_pnl_stvarni():
    from hub.formati import nalog_io as IO
    import glob
    dat = sorted(glob.glob(os.path.join(PNL_MAPA, "*.pnl")))
    assert len(dat) >= 5
    po = {os.path.basename(f): IO.read_pnl(f) for f in dat}
    nk18 = [v for k, v in po.items() if "NK_18" in k][0]
    assert nk18[0]["mat"] == "IV BIJELI NK 18 MM" and nk18[0]["deb"] == 18 and len(nk18) == 35 and sum(e["kom"] for e in nk18) == 93
    assert (nk18[0]["L"], nk18[0]["W"], nk18[0]["kom"], nk18[0]["naziv"]) == (777, 560, 4, "GOLA L I C IPN")
    assert nk18[0]["traka"] == {"L": "1/22 ISTI", "O": "1/22 ISTI", "D": "", "G": "1/22 ISTI"} and nk18[0]["tip"] == {"L": "A", "O": "A", "D": "", "G": "A"}
    assert nk18[0]["program"] == "I_01840"
    mel = [e for e in nk18 if e["traka"]["L"] == "MEL CRNA NK"]
    assert mel and mel[0]["tip"]["L"] == "M"                       # MEL zastavice su u prvom bloku, ABS u drugom
    for k, v in po.items():                                        # materijal iz polja u repu datoteke, ne iz imena datoteke
        assert v and v[0]["mat"] and "_" not in v[0]["mat"], (k, v[0]["mat"])
    assert [v for k, v in po.items() if "VULCANO" in k][0][0]["mat"] == "RP SLATE VULCANO K2877"
    assert [v for k, v in po.items() if "EVOKE_SUNSET_1" in k][0][0]["deb"] == 19


@pytest.mark.skipif(not DATA or not os.path.isdir(PNL_MAPA), reason="HUB_TEST_DATA nije postavljen")
def test_uvoz_pnl_u_nalog(baza_o):
    from hub.nalozi import uvoz_datoteka as U, nalozi as N
    import glob
    c = baza_o
    nid, nm, e1, e2 = _nalog(c)
    f = [x for x in glob.glob(os.path.join(PNL_MAPA, "*.pnl")) if "NK_18" in x][0]
    st = U.uvezi_pnl(c, nid, f, "IVANA")
    assert st["elementi"] == 35 and st["komada"] == 93
    assert U.uvezi_pnl(c, nid, f, "IVANA")["preskoceno"] == 1           # isti hash = ne dvaput
    assert c.execute("SELECT vrsta FROM dokument WHERE nalog_id = ? AND vrsta = 'pnl'", (nid,)).fetchone()
    d = N.pregled(c, nid)
    assert d["sazetak"]["elemenata"] == 35 + 2
