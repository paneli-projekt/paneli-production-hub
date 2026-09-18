# -*- coding: utf-8 -*-
"""Katalozi dobavljača i slike dekora (dokument 36): uvoz CSV-a i slika, vezanje na naše identе po kodu dekora i po nazivu,
potvrda ureda. Slike se koriste samo na internim ekranima."""
import os

import pytest

from hub.sifrarnici import dekori as DEK
from tests.test_nalozi import baza  # noqa: F401

ZAGLAVLJE = ("jedinstveni_id;dobavljac;kategorija;naziv;sifra;proizvodac;debljina;dostupne_debljine;duzina;sirina;"
             "datoteka_slike;putanja_slike_u_paketu;url_proizvoda;status_slike;kljuc_pretrage;datum_prikupljanja;"
             "blazic_oznaka_ploce;blazic_sifra_artikla;blazic_naziv_trake;blazic_debljine;blazic_ocjena_podudaranja;blazic_datoteka_slike_trake")
REDOVI = [
    # isti kod i ista obrada kao IV000090 (W908 ST2) → slika se upisuje sama
    "IVERPAN-IV-0001;Iverpan;Iverali;Platinasto bijela W908 ST2 - 18 mm;;EGGER;18;;2800;2070;a.jpg;kat/a.jpg;https://iverpan.hr/a;preuzeto;platinasto bijela;2026-09-18;W908;A100;100;1 mm;odlično ujemanje;slike_traka/A100.jpg",
    # isti dekor, druga obrada od IV001157 (27045 UM) → ide na potvrdu
    "IVERPAN-IV-0002;Iverpan;Iverali;Champagne 27045 GR - 19 mm;;KAINDL;19;;2800;2070;b.jpg;kat/b.jpg;https://iverpan.hr/b;preuzeto;champagne;2026-09-18;27045;;;;;",
    # bez koda, ali naziv se poklapa s IV000171 (HRAST SONOMA) → kandidat po nazivu
    "ELGRAD-OI-0003;Elgrad;Oplemenjena iverica;Hrast Sonoma prirodni;;KRONOSPAN;18;;2800;2070;c.jpg;kat/c.jpg;https://elgrad.hr/c;preuzeto;hrast sonoma;2026-09-18;;;;;;",
]


def _mapa(tmp_path, redovi=REDOVI):
    from PIL import Image
    d = tmp_path / "katalog_dobavljaca"
    (d / "kat").mkdir(parents=True)
    for ime in ("a.jpg", "b.jpg", "c.jpg"):
        Image.new("RGB", (1200, 900), (200, 180, 160)).save(str(d / "kat" / ime), "JPEG")
    (d / "Svi_dekori_s_BLAZIC_rubnim_trakama_2026-09-18.csv").write_text("﻿" + ZAGLAVLJE + "\n" + "\n".join(redovi) + "\n", encoding="utf-8")
    return str(d)


def test_kodovi_i_rijeci():
    assert DEK.kodovi("Acai 25727 MN - 19 mm") == ["25727MN", "25727"]
    assert DEK.kodovi("Platinasto bijela W908 ST2 - 18 mm")[0] == "W908ST2"
    assert DEK.kodovi("Hrast Bardolino natur", "H1145 ST10")[0] == "H1145ST10"
    assert DEK.kodovi("Bookmatch hrast") == []
    assert DEK.rijeci("IVERAL HRAST SONOMA 3025 SN 18MM") >= {"HRAST", "SONOMA"}
    assert "MM" not in DEK.rijeci("Hrast Sonoma 18 mm") and "IVERAL" not in DEK.rijeci("IVERAL HRAST")


def test_uvoz_i_vezanje(baza, tmp_path):
    c = baza.conn if hasattr(baza, "conn") else baza
    mapa = _mapa(tmp_path)
    iz = DEK.uvezi_katalog(c, mapa, "TEST")
    assert iz["redaka"] == 3 and iz["novo"] == 3 and iz["slika"] == 3
    assert os.path.isfile(os.path.join(iz["mapa_slika"], "IVERPAN-IV-0001.jpg"))
    k = c.execute("SELECT * FROM dekor_katalog WHERE katalog_id = 'IVERPAN-IV-0001'").fetchone()
    assert k["proizvodac"] == "EGGER" and k["traka_sifra"] == "A100" and k["kod_dekora"] == "W908"
    sp = DEK.spoji(c, "TEST")
    assert sp["po_kodu"] >= 1
    s = DEK.slika(c, "IV000090")                                   # W908 ST2 → točan pogodak, upisuje se sam
    assert s and s["razina"] == "kod" and s["dobavljac"] == "Iverpan" and s["url_proizvoda"].endswith("/a")
    assert DEK.slika(c, "IV001157") is None                        # 27045 UM ≠ 27045 GR → čeka ured
    kand = DEK.kandidati(c, "IV001157")
    assert [x["katalog_id"] for x in kand] == ["IVERPAN-IV-0002"]
    assert any(x["pantheon_ident"] == "IV000171" for x in DEK.za_potvrdu(c))     # HRAST SONOMA po nazivu
    # ponovni uvoz ništa ne kvari
    iz2 = DEK.uvezi_katalog(c, mapa, "TEST")
    assert iz2["novo"] == 0 and iz2["osvjezeno"] == 3


def test_potvrda_ureda(baza, tmp_path):
    c = baza.conn if hasattr(baza, "conn") else baza
    DEK.uvezi_katalog(c, _mapa(tmp_path), "TEST")
    DEK.spoji(c, "TEST")
    s = DEK.potvrdi(c, "IV001157", "IVERPAN-IV-0002", "IVANA")
    assert s["razina"] == "potvrda" and s["potvrdio"] == "IVANA"
    assert DEK.kandidati(c, "IV001157") == []
    assert not any(x["pantheon_ident"] == "IV001157" for x in DEK.za_potvrdu(c))
    DEK.odbij(c, "IV000171", None, "IVANA")                        # nijedna ponuđena ne odgovara
    assert DEK.kandidati(c, "IV000171") == [] and DEK.slika(c, "IV000171") is None
    DEK.spoji(c, "TEST")                                           # ponovno vezanje ne vraća odbijeno
    assert DEK.kandidati(c, "IV000171") == []
    with pytest.raises(ValueError):
        DEK.potvrdi(c, "IV999999", "IVERPAN-IV-0002", "IVANA")
    assert DEK.sazetak(c)["katalog"] == 3


def test_api_dekori(baza, tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    c = baza.conn if hasattr(baza, "conn") else baza
    DEK.uvezi_katalog(c, _mapa(tmp_path), "TEST")
    DEK.spoji(c, "TEST")
    monkeypatch.setenv("HUB_DB", str(baza.dir / "hub.db"))
    A._veza = None
    kl = TestClient(A.app, raise_server_exceptions=False)
    try:
        r = kl.get("/api/dekori/za-potvrdu").json()
        assert r["broj"] >= 1 and r["sazetak"]["katalog"] == 3 and r["materijali"][0]["kandidati"]
        assert kl.get("/api/dekor/slika/IV000090").status_code == 200
        assert kl.get("/api/dekor/slika/IV001157").status_code == 404
        assert kl.post("/api/dekor/potvrdi", json=dict(ident="IV001157", katalog_id="IVERPAN-IV-0002", tko="IVANA")).json()["razina"] == "potvrda"
        assert kl.get("/api/dekor/slika/IV001157").status_code == 200
        assert kl.get("/api/dekor/IV001157").json()["slika"]["dobavljac"] == "Iverpan"
        assert kl.post("/api/dekor/odbij", json=dict(ident="IV000171", tko="IVANA")).json()["ok"]
        assert kl.get("/api/dekori/katalog", params=dict(q="champagne")).json()["dekori"][0]["katalog_id"] == "IVERPAN-IV-0002"
        assert kl.post("/api/dekori/uvoz", json=dict(mapa=str(tmp_path / "nema"), tko="TEST")).status_code == 400
    finally:
        A._veza = None


def test_ekran_slika_dekora():
    web = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hub", "web")
    js = open(os.path.join(web, "ekrani.js"), encoding="utf-8").read()
    for x in ("E.dekori", "/api/dekor/slika/", "/api/dekori/za-potvrdu", "Nijedna ne odgovara", "dslika("):
        assert x in js, x
