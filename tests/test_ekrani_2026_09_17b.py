# -*- coding: utf-8 -*-
"""Igorove napomene 17. 9. (drugi prolaz): uvoz više datoteka kupca odjednom, sažetak promjena između verzija ponude,
gumbi verzije u jednom redu, ekran pile / nestinga preimenovan u Proizvodnja (materijali u punoj visini)."""
import os

import pytest

from hub.nalozi import nalozi as N, obracun as OC, optimiziraj as OP, ponuda as PO
from hub.sifrarnici import prepoznaj as P
from tests.test_nalozi import baza  # noqa: F401
from tests.test_obracun_ponuda import baza_o  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog


def test_promjene_izmedju_verzija(baza_o):
    c = baza_o
    OP.AUTO_POTVRDA = True
    nid, nm, e1, e2 = _nalog(c, status="ponuda")
    v1 = PO.nova_verzija(c, nid, "IVANA")
    assert PO.verzije(c, nid)[0]["promjene"] is None                            # prva verzija nema s čime se uspoređivati
    traka = [s for s in OC.izracunaj(c, nid)["stavke"] if s["grupa"] == "traka"][0]
    OC.korigiraj_stavku(c, nid, traka["kljuc"], "IVANA", kolicina=5, rabat=12)
    ident = c.execute("SELECT ident FROM pantheon_ident WHERE ident LIKE 'US%' ORDER BY ident LIMIT 1").fetchone()[0]
    r = OC.dodaj_rucnu(c, nid, ident, 3, grupa="okov", naziv="Montaža na objektu", jm="H", cijena=35, rabat=0, tko="IVANA")
    v2 = PO.nova_verzija(c, nid, "IVANA")
    pr = PO.verzije(c, nid)[1]["promjene"]
    assert pr["prema"] == 1 and not pr["bez_promjene"]
    assert pr["neto_razlika"] == round(v2["iznos_neto"] - v1["iznos_neto"], 2)
    assert pr["ukupno_razlika"] == round((v2["iznos_neto"] + v2["iznos_pdv"]) - (v1["iznos_neto"] + v1["iznos_pdv"]), 2)
    assert [(x["naziv"], x["kolicina"], x["razlika"]) for x in pr["dodano"]] == [("Montaža na objektu", 3, 105)]
    tr = [x for x in pr["promijenjeno"] if x["ident"] == traka["pantheon_ident"]][0]
    polja = {f["polje"]: (f["staro"], f["novo"]) for f in tr["polja"]}
    assert polja["kolicina"] == (traka["kolicina"], 5) and polja["rabat"] == (traka["rabat"], 12)
    assert not pr["uklonjeno"]
    # ista ponuda još jednom → bez promjena
    PO.nova_verzija(c, nid, "IVANA")
    assert PO.verzije(c, nid)[2]["promjene"]["bez_promjene"]
    # uklonjena ručna stavka
    OC.obrisi_rucnu(c, r["id"], "IVANA")
    PO.nova_verzija(c, nid, "IVANA")
    pr4 = PO.verzije(c, nid)[3]["promjene"]
    assert pr4["prema"] == 3 and [(x["naziv"], x["razlika"]) for x in pr4["uklonjeno"]] == [("Montaža na objektu", -105)] and not pr4["dodano"]
    # zbroj razlika stavki = razlika neto (zaokruživanje po stavci)
    zbroj = sum(x["razlika"] for x in pr["dodano"] + pr["uklonjeno"] + pr["promijenjeno"])
    assert abs(zbroj - pr["neto_razlika"]) < 0.05


def test_api_uvoz_vise_datoteka_redom(baza, monkeypatch):
    """Ekran šalje datoteke jednu za drugom na isti endpoint: svaka ulazi u isti nalog, ponovljena se preskače (hash), krivi tip javi grešku."""
    from fastapi.testclient import TestClient
    import hub.api.app as A
    monkeypatch.setenv("HUB_DB", str(baza.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    c = TestClient(A.app)
    k = c.get("/api/kupci", params=dict(q="humer")).json()["kupci"][0]
    n = c.post("/api/nalozi", json=dict(kupac_id=k["id"], projekt="Omiš", izvor="kupac_ppw", tko="IVANA")).json()
    el = 0
    for ime in ("a_bijeli.CPW", "b_bijeli2.CPW", "c_sivi.CPW"):
        with open(baza.dir / ime, "rb") as f:
            r = c.post("/api/nalog/%d/uvoz" % n["id"], params=dict(izvor="kupac_ppw", tko="IVANA"), files={"datoteka": (ime, f, "application/octet-stream")})
        assert r.status_code == 200 and not r.json()["preskoceno"]
        el += r.json()["elementi"]
    assert r.json()["sazetak"]["elemenata"] == el and os.path.exists(os.path.join(str(baza.dir), "ulaz", n["naziv"], "c_sivi.CPW"))
    with open(baza.dir / "a_bijeli.CPW", "rb") as f:                            # ista datoteka drugi put
        r = c.post("/api/nalog/%d/uvoz" % n["id"], params=dict(izvor="kupac_ppw", tko="IVANA"), files={"datoteka": ("a_bijeli (1).CPW", f, "application/octet-stream")}).json()
    assert r["preskoceno"] == 1 and r["elementi"] == 0 and r["sazetak"]["elemenata"] == el
    r = c.post("/api/nalog/%d/uvoz" % n["id"], params=dict(tko="IVANA"), files={"datoteka": ("nacrt.pdf", b"%PDF", "application/pdf")})
    assert r.status_code == 400
    # ekran: višestruki odabir, sažetak promjena, gumbi u boji, korak „5 Proizvodnja“
    js = c.get("/static/app.js").text + c.get("/static/ekrani.js").text
    css = c.get("/static/app.css").text
    assert 'id="dat" multiple' in js and "5 Proizvodnja" in js and "E.nalog_proizvodnja = E.nalog_pila" in js and "promjeneHtml" in js
    assert ".btn.zuti" in css and ".btn.plavi" in css and ".content.proizv" in css
