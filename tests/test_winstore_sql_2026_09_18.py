"""Hub čita stanje ploča izravno iz baze Winstorea (dokument 38, D-98).

Prava baza Winstorea ovdje nije dostupna, pa se `procitaj` zamjenjuje lažnim redcima pogleda
`vBoardsDropsStatus` — uvoz, povezivanje s Pantheon identima i ambalaža idu istim putem kao kod XML-a.
"""
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hub import db as D                                    # noqa: E402
from hub.sifrarnici import winstore_sql as WSQ             # noqa: E402

# Code, MaterialCode, MaterialDescription, L, W, T, Grain, IsDrop, Stored, StoredInternal, StoredExternal, Booked
REDCI = [
    ("W908ST2-18-2800-2070", "W908ST2-18", "IVERAL BIJELI NK W908ST2 18MM", 2800.0, 2070.0, 18.0, 0, False, 20, 0, 20, 3),
    ("3025SN-18-2800X2070", "3025SN-18", "IVERAL HRAST SONOMA 3025 SN 18MM", 2800.0, 2070.0, 18.0, 1, False, 20, 20, 0, 0),
    ("111IVAN-18-2800X2070", "111IVAN-18", "AMBALAZA 18MM IVAN", 2800.0, 2070.0, 18.0, 0, False, 8, 8, 0, 0),
    ("R-KOMAD-1", "W908ST2-18", "IVERAL BIJELI NK W908ST2 18MM", 1200.0, 600.0, 18.0, 0, True, 1, 1, 0, 0),
]


@pytest.fixture()
def baza(tmp_path):
    c = sqlite3.connect(str(tmp_path / "hub.db"))
    c.row_factory = sqlite3.Row
    D.init(c)
    c.execute("INSERT INTO pantheon_ident (ident, naziv, azurirano) VALUES ('IV000090', 'IVERAL BIJELI NK W908 ST2 18MM', '2026-09-18 00:00:00')")
    c.execute("INSERT INTO materijal (pantheon_ident, naziv_pantheon, vrsta, winstore_kod, debljina, aktivan) "
              "VALUES ('IV000090', 'IVERAL BIJELI NK W908 ST2 18MM', 'IV', 'W908ST2-18', 18.0, 1)")
    c.commit()
    return c


def test_redci_pogleda_daju_iste_stavke_kao_xml():
    st = WSQ.stavke_iz_redaka(REDCI)
    assert [x["kod"] for x in st] == [r[0] for r in REDCI]
    p = st[0]
    assert (p["materijal_kod"], p["L"], p["W"], p["debljina"], p["god"]) == ("W908ST2-18", 2800.0, 2070.0, 18.0, 0)
    assert (p["kom_ukupno"], p["kom_interno"], p["kom_eksterno"], p["drop"], p["rezervirano"]) == (20, 0, 20, 0, 3)
    assert st[1]["god"] == 1 and st[3]["drop"] == 1          # IsDrop = restl u Winstoreu


def test_osvjezavanje_puni_winstore_plocu(baza, monkeypatch):
    monkeypatch.setattr(WSQ, "procitaj", lambda p: WSQ.stavke_iz_redaka(REDCI))
    st = WSQ.osvjezi(baza, tko="test")
    assert st["stavke"] == 4 and st["izvor"] == "sql"
    r = baza.execute("SELECT kod, rezervirano, ambalaza, drop_ploca, materijal_id FROM winstore_ploca ORDER BY kod").fetchall()
    assert len(r) == 4
    d = {x["kod"]: x for x in r}
    assert d["W908ST2-18-2800-2070"]["rezervirano"] == 3            # Booked — u XML-u ga nije bilo
    assert d["111IVAN-18-2800X2070"]["ambalaza"] == 1               # ambalaža se ne vodi na stanju (D-49)
    assert d["R-KOMAD-1"]["drop_ploca"] == 1
    assert d["W908ST2-18-2800-2070"]["materijal_id"] is not None    # povezano s Pantheon identom preko winstore_kod
    assert (D.postavka(baza, "winstore_izvoz") or "").startswith("baza Winstorea @ ")


def test_ponovno_citanje_zamjenjuje_prethodno_stanje(baza, monkeypatch):
    monkeypatch.setattr(WSQ, "procitaj", lambda p: WSQ.stavke_iz_redaka(REDCI))
    WSQ.osvjezi(baza, tko="test")
    monkeypatch.setattr(WSQ, "procitaj", lambda p: WSQ.stavke_iz_redaka(REDCI[:1]))
    WSQ.osvjezi(baza, tko="test")
    assert baza.execute("SELECT COUNT(*) FROM winstore_ploca").fetchone()[0] == 1


def test_osvjezi_ako_treba_postuje_prekidac_i_starost(baza, monkeypatch):
    zvano = []
    monkeypatch.setattr(WSQ, "procitaj", lambda p: (zvano.append(1), WSQ.stavke_iz_redaka(REDCI))[1])
    assert WSQ.osvjezi_ako_treba(baza) is None and not zvano          # isključeno
    D.postavi(baza, "winstore_sql_ukljucen", "1"); baza.commit()
    assert WSQ.osvjezi_ako_treba(baza) is not None and len(zvano) == 1
    assert WSQ.osvjezi_ako_treba(baza) is None and len(zvano) == 1    # svježe — ne dira Winstore
    assert 0 <= WSQ.starost_minuta(baza) < 5


def test_neuspjeh_ne_rusi_ekran(baza, monkeypatch):
    D.postavi(baza, "winstore_sql_ukljucen", "1"); baza.commit()

    def pukni(p):
        raise WSQ.NemaVeze("poslužitelj ne odgovara")

    monkeypatch.setattr(WSQ, "procitaj", pukni)
    assert WSQ.osvjezi_ako_treba(baza) is None
    assert baza.execute("SELECT COUNT(*) FROM dnevnik WHERE sto = 'greska'").fetchone()[0] == 1
    r = WSQ.provjeri(baza)
    assert r["ok"] is False and "ne odgovara" in r["poruka"]


def test_ekran_postavki_ima_karticu_winstore():
    web = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hub", "web")
    js = open(os.path.join(web, "ekrani.js"), encoding="utf-8").read()
    for x in ('karta("Winstore"', "btnWsProvjeri", "btnWsOsvjezi", "winstore_sql_ukljucen", "winstore_sql_lozinka", "/api/postavke/winstore"):
        assert x in js, x
    assert "winstore_sql_lozinka_upisana" in js          # sama lozinka se ne prikazuje na ekranu
