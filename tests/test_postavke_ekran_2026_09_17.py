# -*- coding: utf-8 -*-
"""Ekran Postavke u stilu 1A + 2A + 3A (Igor, 17. 9.): podaci tvrtke preko API-ja (samo dopušteni ključevi, OIB 11 znamenki, IBAN bez razmaka),
postavke optimizacije i dalje s istim značenjem (0/1, 2|3|4, m2|rezova|m_reza), a ekran nosi cjeline, prekidač i gumb Spremi postavke."""
import os

from hub.sifrarnici import prepoznaj as P
from tests.test_nalozi import baza  # noqa: F401

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hub", "web")


def _klijent(baza, monkeypatch):
    from fastapi.testclient import TestClient
    import hub.api.app as A
    monkeypatch.setenv("HUB_DB", str(baza.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    return TestClient(A.app)


def test_api_podaci_tvrtke(baza, monkeypatch):
    c = _klijent(baza, monkeypatch)
    t = c.get("/api/postavke/tvrtka").json()
    assert set(t) == {"tvrtka_naziv", "tvrtka_adresa", "tvrtka_oib", "tvrtka_iban", "tvrtka_tel", "tvrtka_mail", "tvrtka_web"}
    assert t["tvrtka_naziv"] and t["tvrtka_oib"] == ""                          # zadani naziv s dokumenata, OIB prazan dok se ne upiše
    assert c.post("/api/postavke/tvrtka", json=dict(tvrtka_oib="123", tko="IGOR")).status_code == 400
    assert c.post("/api/postavke/tvrtka", json=dict(kerf="3", tko="IGOR")).status_code == 400   # samo podaci tvrtke
    r = c.post("/api/postavke/tvrtka", json=dict(tvrtka_oib=" 12345678901 ", tvrtka_iban="hr12 3456 7890 1234 5678 9", tvrtka_tel="031 000 000", tko="IGOR"))
    assert r.status_code == 200
    t = r.json()
    assert t["tvrtka_oib"] == "12345678901" and t["tvrtka_iban"] == "HR1234567890123456789" and t["tvrtka_tel"] == "031 000 000"
    assert c.get("/api/postavke/tvrtka").json()["tvrtka_iban"] == "HR1234567890123456789"
    assert c.post("/api/postavke/tvrtka", json=dict(tvrtka_oib="", tko="IGOR")).json()["tvrtka_oib"] == ""   # brisanje dopušteno


def test_api_postavke_optimizacije_isto_znacenje(baza, monkeypatch):
    c = _klijent(baza, monkeypatch)
    p = {x["kljuc"]: x["vrijednost"] for x in c.get("/api/postavke/optimizacija").json()}
    assert p["pila_mijesana_orijentacija"] in ("0", "1") and p["pila_max_razina"] in ("2", "3", "4") and p["obracun_rezanja"] in ("m2", "rezova", "m_reza")
    assert c.post("/api/postavke/optimizacija", json=dict(pila_mijesana_orijentacija="2")).status_code == 400
    r = c.post("/api/postavke/optimizacija", json=dict(pila_mijesana_orijentacija="1", kerf="17", tko="IGOR")).json()
    assert {x["kljuc"]: x["vrijednost"] for x in r}["pila_mijesana_orijentacija"] == "1"


def test_ekran_postavke_cjeline():
    js = open(os.path.join(WEB, "ekrani.js"), encoding="utf-8").read()
    css = open(os.path.join(WEB, "app.css"), encoding="utf-8").read()
    i = js.index("E.postavke = async function"); dio = js[i:js.index("H.optBlok = optBlok", i)]
    for naslov in ("Obračun", "Pravila pile", "Mape izvoza", "E-pošta", "Korisnici i prijava", "Napredni podaci", "Spremi postavke", "Nije postavljena", "Postavi lozinku", "Oznaka", "E-mail / telefon"):
        assert naslov in dio, naslov
    for kljuc in ("kerf", "kerf_pile", "nadmjera_trake", "obracun_rezanja", "ident_rezanje_rez", "ident_rezanje_m", "mapa_nesting", "mapa_pila",
                  "pila_max_razina", "pila_max_sirina_u_traci", "pila_min_komad_4", "pila_mijesana_orijentacija"):
        assert 'polje("%s"' % kljuc in dio, kljuc                                # nijedno postojeće polje nije izgubljeno
    assert '"prekidac"' in dio and '"izbor"' in dio and "/api/postavke/tvrtka" in dio
    assert "--btn:#78B84A" in css and "--btn-ink:#173510" in css and "--paper:#F6F5F1" in css and ".prek" in css
