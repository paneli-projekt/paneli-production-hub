# -*- coding: utf-8 -*-
"""Prag čuvanja restla (D-95, Igor 18. 9.): restl je ostatak ≥ 0,35 m² ili traka ≥ 2 000 mm, kraća stranica ≥ 150 mm.
Pravilo NAPLATE (≥ 400 mm i ≥ 1 m², D-19) se ne mijenja — komad između dva praga kupac plaća, a mi ga zadržimo u regalu."""
from hub.optimizacija import obracun as OBR
from hub.skladiste import restlovi as RS
from tests.test_nalozi import baza  # noqa: F401


def test_pravilo_praga():
    assert OBR.je_restl(600, 600) and OBR.je_restl(2000, 500)                      # 0,36 m² i 1,0 m²
    assert OBR.je_restl(2800, 195) and OBR.je_restl(2000, 150)                     # traka pune duljine (17 takvih je u evidenciji)
    assert not OBR.je_restl(500, 600)                                              # 0,30 m² — ispod praga
    assert not OBR.je_restl(2800, 120)                                             # preuska traka
    assert not OBR.je_restl(430, 100)                                              # najmanji komad iz evidencije
    assert OBR.je_restl(500, 600, min_m2=0.25)                                      # prag je podesiv


def test_naplata_ostaje_na_starom_pragu():
    """Isti geometrijski ostatak: naplata ga priznaje tek od 400 mm i 1 m², restl se čuva i ranije."""
    ploca = (2800, 2070)
    o = OBR.ostatak_dims("L", [700, 700], ploca)                                   # 2800 × 630 = 1,76 m²
    assert OBR.ostatak_ploce("L", [700, 700], ploca) == o                          # prolazi i naplatu
    uski = OBR.ostatak_dims("L", [900, 900], ploca)                                # 2800 × 228 = 0,64 m²
    assert OBR.ostatak_ploce("L", [900, 900], ploca) is None                       # kupac ga plaća
    assert OBR.je_restl(uski[0], uski[1])                                          # ali ga zadržimo (traka pune duljine)


def test_prag_iz_postavki(baza):
    c = baza.conn
    assert RS.prag(c) == (0.35, 150.0, 2000.0)
    assert RS.je_restl(c, 600, 600) and not RS.je_restl(c, 500, 600)
    c.execute("UPDATE postavke SET vrijednost = '0.6' WHERE kljuc = 'restl_min_m2'"); c.commit()
    assert not RS.je_restl(c, 600, 600)                                            # 0,36 m² sad je ispod praga
    assert RS.je_restl(c, 2500, 200)                                               # traka prolazi bez obzira na površinu


def test_kandidati_iz_sheme(baza):
    """Iz snimke sheme nastaju prijedlozi; onaj ispod praga naplate nosi oznaku da ga je kupac platio."""
    c = baza.conn
    snimka = dict(ploca=[2800, 2070], trim=10, kerf=16,
                  sheets=[dict(dir="L", strips=[dict(w=700), dict(w=700)]), dict(dir="L", strips=[dict(w=900), dict(w=900)])],
                  ostaci=[[2800, 628, 1.758]])                                     # naplata priznaje samo prvu ploču
    k = RS.kandidati_iz_sheme(c, snimka)
    assert len(k) == 2
    assert k[0][3] is False and k[1][3] is True                                    # druga je ispod praga naplate → kupac ju je platio
    assert k[1][0] == 2800 and 200 <= k[1][1] <= 240
    snimka["sheets"].append(dict(dir="L", strips=[dict(w=1000), dict(w=1000)]))     # 2800 × 28 — ispod svakog praga
    assert len(RS.kandidati_iz_sheme(c, snimka)) == 2


def test_kandidati_radne_ploce(baza):
    """Radna ploča: ostatak ide uz duljinu ploče (rp.listovi), prag je isti."""
    c = baza.conn
    snimka = dict(ploca=[4100, 600], trim=0, kerf=5,
                  rp=dict(obitelj="radna", listovi=[dict(br=1, ostatak=[1200, 600, 0.72]), dict(br=2, ostatak=[400, 600, 0.24]), dict(br=3, ostatak=None)]))
    k = RS.kandidati_iz_sheme(c, snimka)
    assert [(x[0], x[1]) for x in k] == [(1200, 600)]                              # 400 × 600 = 0,24 m² je ispod praga
