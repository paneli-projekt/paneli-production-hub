# -*- coding: utf-8 -*-
"""D-92 (Igor, 17. 9.): radne ploče, ploče stola i zidne obloge se slažu i režu na pili, naplata po ploči iz potvrđenog slaganja (D-37).
Radna 600: komad iza komada, ≤ 2,7 m točni metri (najmanje 1,4 m), > 2,7 m cijela 4,1 m. Stol 900: i uži komadi jedan uz drugi,
pola (≤ 2,05 m) / cijela; ident dekora. Zidna 640: komad iza komada, samo cijela, 4 reza po komadu."""
import os

import pytest

from hub.nalozi import nalozi as N, obracun as OC, optimiziraj as OP, export_pila as EP, spajanje as SP
from hub.optimizacija import pila_optimizator as OPT, radne_ploce as RPP
from hub.ispis import krojni as KR, sheme_png as SPNG
from hub.skladiste import restlovi as RS
from tests.test_nalozi import baza  # noqa: F401
from tests.test_obracun_ponuda import baza_o  # noqa: F401


def _els(dijelovi, deb=38):
    return [dict(mat="RP TEST", deb=deb, W=W, L=L, kom=kom, god=0, napomena="", traka={}) for _, W, L, kom in dijelovi]


def test_radna_komad_iza_komada_i_naplata():
    pl = (4100, 600)
    # 2,0 + 0,9 m na istoj ploči = 2,9 m > 2,7 → cijela 4,1 m; nema našeg ostatka
    d = [(1, 600, 2000, 1), (2, 600, 900, 1)]
    sh = RPP.slozi_niz(d, pl, 0, 5)
    assert len(sh) == 1 and len(sh[0]["strips"]) == 1 and [b["l"] for b in sh[0]["strips"][0]["blocks"]] == [2000, 900]
    oc = RPP.ocijeni(sh, pl, 0, 5, "radna")
    assert oc["rp"]["ukupno_m"] == 4.1 and oc["rp"]["listovi"][0]["opis"] == "cijela" and not oc["ostaci"]
    assert not OPT.napravi_cpo(_els(d), "HUB_T", "K", ploca=pl, trim=0, kerf=5, sheets=sh)[2]        # CPO valjan (stablo rezova)
    # 2,0 + 0,6 = 2,6 m → točni metri, ostatak 1490 mm je naš
    oc = RPP.ocijeni(RPP.slozi_niz([(1, 600, 2000, 1), (2, 580, 600, 1)], pl, 0, 5), pl, 0, 5, "radna")
    assert oc["rp"]["ukupno_m"] == 2.6 and oc["rp"]["listovi"][0]["opis"] == "metri" and oc["ostaci"][0][:2] == (1490, 600)
    # 0,9 m → najmanje 1,4 m
    oc = RPP.ocijeni(RPP.slozi_niz([(1, 600, 900, 1)], pl, 0, 5), pl, 0, 5, "radna")
    assert oc["rp"]["ukupno_m"] == 1.4 and oc["rp"]["listovi"][0]["opis"] == "najmanje 1,4 m"
    assert RPP.opis(oc["rp"]) == "ploča 1: 0,9 m → najmanje 1,4 m"
    # 3,0 + 2,5 ne stanu zajedno → dvije ploče: cijela 4,1 + 2,5 m; najpunija prva
    sh = RPP.slozi_niz([(1, 600, 2500, 1), (2, 600, 3000, 1)], pl, 0, 5)
    oc = RPP.ocijeni(sh, pl, 0, 5, "radna")
    assert len(sh) == 2 and oc["rp"]["ukupno_m"] == 6.6 and [li["opis"] for li in oc["rp"]["listovi"]] == ["cijela", "metri"]
    # komad upisan poprijeko (W > L) leži duljinom uz ploču; dulji od ploče → greška (spoj se radi ručno)
    sh = RPP.slozi_niz([(1, 2000, 600, 2)], pl, 0, 5)
    assert len(sh) == 1 and not OPT.napravi_cpo(_els([(1, 2000, 600, 2)]), "HUB_T", "K", ploca=pl, trim=0, kerf=5, sheets=sh)[2]
    with pytest.raises(ValueError, match="spoj"):
        RPP.slozi_niz([(1, 600, 4200, 1)], pl, 0, 5)
    # jedinica identa
    rp = RPP.ocijeni(RPP.slozi_niz([(1, 600, 2000, 1)], pl, 0, 5), pl, 0, 5, "radna")["rp"]
    assert RPP.kolicina_za_jm(rp, "M") == (2.0, None) and RPP.kolicina_za_jm(rp, "M2") == (1.2, None) and RPP.kolicina_za_jm(rp, "KOM")[0] == 1


def test_stol_pola_cijela_i_zidna():
    assert RPP.naplata_ploce("stola", 1800) == (2.05, "pola") and RPP.naplata_ploce("stola", 2050) == (2.05, "pola")
    assert RPP.naplata_ploce("stola", 2110) == (4.1, "cijela") and RPP.naplata_ploce("zidna", 500) == (4.1, "cijela")
    pl = (4100, 900)
    # HUMER (D-37): 2880 i 2110 → dvije cijele ploče
    sh, oc, _, _ = OPT.najbolje([(1, 900, 2880, 1), (2, 900, 2110, 1)], pl, 0, 5, False, ("uzduzno", "trake"))
    rp = RPP.ocijeni(sh, pl, 0, 5, "stola")["rp"]
    assert len(sh) == 2 and rp["ukupno_m"] == 8.2
    # dva uža komada jedan uz drugi na istoj ploči → iskorišteno 1,0 m → pola
    sh, oc, _, _ = OPT.najbolje([(1, 440, 1000, 2)], pl, 10, 5, False, ("uzduzno", "trake"))
    o = RPP.ocijeni(sh, pl, 10, 5, "stola")
    assert len(sh) == 1 and o["rp"]["listovi"][0]["opis"] == "pola" and o["ostaci"] and o["ostaci"][0][1] == 900
    # zidna: uvijek cijela, 4 reza po komadu
    o = RPP.ocijeni(RPP.slozi_niz([(1, 640, 1200, 1)], (4100, 640), 0, 5), (4100, 640), 0, 5, "zidna")
    assert o["rp"]["ukupno_m"] == 4.1 and not o["ostaci"] and RPP.REZOVA_PO_KOMADU["zidna"] == 4
    assert RPP.obitelj("RP", None) == "radna" and RPP.obitelj("RP", "stola") == "stola" and RPP.obitelj("ZO", "zidna") == "zidna" and RPP.obitelj("IV") is None


def _nalog_rp(c):
    c.execute("INSERT OR IGNORE INTO pantheon_ident (ident, naziv, klasif, jm, cijena_prodajna, cijena_neto, pdv, aktivan, azurirano) "
              "VALUES ('RP000900', 'ZIDNA PLOČA PROBA 4100X640X8MM', 'RP', 'M', 30, 24, 25, 1, 't')")
    c.execute("INSERT OR IGNORE INTO pantheon_ident (ident, naziv, klasif, jm, cijena_prodajna, cijena_neto, pdv, aktivan, azurirano) "
              "VALUES ('US000303', 'USLUGA REZANJA RADNE PLOČE', 'US', 'KOM', 3, 2.4, 25, 1, 't')")
    c.execute("INSERT OR IGNORE INTO materijal (pantheon_ident, naziv_pantheon, naziv_kratki, vrsta, obitelj_rp, debljina, ploca_L, ploca_W, sirina_rp, aktivan) "
              "VALUES ('RP000900', 'ZIDNA PLOČA PROBA 4100X640X8MM', 'ZO PROBA 8', 'ZO', 'zidna', 8, 4100, 640, 640, 1)")
    c.execute("UPDATE materijal SET debljina = 38 WHERE pantheon_ident IN ('RP000001', 'RP000102') AND debljina IS NULL")   # u pravom šifrarniku 38 mm (D-52)
    mid = {r["pantheon_ident"]: r["id"] for r in c.execute("SELECT id, pantheon_ident FROM materijal WHERE pantheon_ident IN ('RP000001', 'RP000102', 'RP000900')")}
    k = c.execute("SELECT id FROM kupac LIMIT 1").fetchone()[0]
    nid = N.novi_nalog(c, "TEST", kupac_id=k, projekt="RP")["id"]
    radna = N.dodaj_materijal(c, nid, "TEST", materijal_id=mid["RP000001"])[0]["id"]
    N.dodaj_element(c, radna, "TEST", L=2000, W=600, kom=1, naziv="RADNA 1")
    N.dodaj_element(c, radna, "TEST", L=600, W=580, kom=1, naziv="RADNA 2")
    stol = N.dodaj_materijal(c, nid, "TEST", materijal_id=mid["RP000102"])[0]["id"]
    N.dodaj_element(c, stol, "TEST", L=1800, W=900, kom=1, naziv="STOL")
    zid = N.dodaj_materijal(c, nid, "TEST", materijal_id=mid["RP000900"])[0]["id"]
    N.dodaj_element(c, zid, "TEST", L=1200, W=640, kom=2, naziv="OBLOGA")
    c.commit()
    return nid, radna, stol, zid


def test_nalog_s_radnom_plocom_od_slaganja_do_pile(baza_o, tmp_path):
    c = baza_o
    nid, radna, stol, zid = _nalog_rp(c)
    assert all(OP.treba_optimizaciju(c, x) for x in (radna, stol, zid))                    # više nema „po dužnom metru — bez slaganja“
    assert len(OP.nepotvrdjeni(c, nid)) == 3
    novi = OP.pripremi_prijedloge(c, nid, "IVANA")
    c.commit()
    assert {x["nalog_materijal_id"] for x in novi} == {radna, stol, zid} and all(x["nacin_trazen"] == "auto" for x in novi)   # nema „rezerve“
    pr = {x["nalog_materijal_id"]: x for x in novi}
    assert pr[radna]["nacin"] == "komad iza komada" and pr[radna]["naplata_rp"]["ukupno_m"] == 2.6 and pr[radna]["broj_ploca"] == 1
    assert pr[stol]["naplata_rp"]["listovi"][0]["opis"] == "pola" and pr[zid]["naplata_rp"]["ukupno_m"] == 4.1
    # bez potvrde: ponuda upozori, količine su prijedlog
    ob = OC.izracunaj(c, nid)
    assert any("nije potvrđena" in u for u in ob["upozorenja"])
    for x in novi:
        OP.potvrdi(c, x["id"], "IVANA")
    ob = OC.izracunaj(c, nid)
    st = {(s["pantheon_ident"], s["nalog_materijal_id"]): s for s in ob["stavke"]}
    assert st[("RP000001", radna)]["kolicina"] == 2.6 and "radna ploča: ploča 1: 2,6 m (potvrđeno)" == st[("RP000001", radna)]["pravilo"]
    assert st[("RP000102", stol)]["kolicina"] == 2.05 and "pola 2,05 m" in st[("RP000102", stol)]["pravilo"]
    assert st[("RP000900", zid)]["kolicina"] == 4.1 and "cijela 4,1 m" in st[("RP000900", zid)]["pravilo"]
    assert st[("US000303", radna)]["kolicina"] == 4 and st[("US000303", stol)]["kolicina"] == 2 and st[("US000303", zid)]["kolicina"] == 8   # 2 / 2 / 4 reza po komadu
    assert not any("nije potvrđena" in u for u in ob["upozorenja"])
    # krojni nacrt, sličica i pregled: naplata po ploči, ostatak uz duljinu
    d = KR.podaci(c, radna)
    assert d["statistika"]["rp"]["ukupno_m"] == 2.6 and d["listovi"][0]["ostatak_duz"] and d["listovi"][0]["ostatak"][:2] == (1490, 600)
    oid = OP.potvrdjena(c, radna)["id"]
    assert SPNG.pregled(c, oid)["naplata_rp"]["ukupno_m"] == 2.6 and os.path.exists(SPNG.png(c, oid, str(tmp_path / "rp.png")))
    assert KR.pdf(c, [radna, stol, zid], str(tmp_path / "krojni_rp.pdf"))["listova"] == 3
    # restl prijedlog iz sheme radne ploče (naš ostatak 1490 × 600)
    r = RS.predlozi_iz_sheme(c, radna, "IVANA")
    assert [(x["L"], x["W"]) for x in r] == [(1490, 600)]
    # pila: CPO za sva tri materijala iz potvrđenog slaganja; spajanje za nesting ih ne nudi
    rez = EP.izvezi(c, nid, str(tmp_path), "IVANA", forsiraj=True)
    assert {p["nalog_materijal_id"] for p in rez["paketi"]} == {radna, stol, zid} and all(os.path.exists(p["cpo"]) for p in rez["paketi"])
    assert not any("punu mjeru" in u for u in rez["upozorenja"])
    nid2, radna2, stol2, zid2 = _nalog_rp(c)                                                  # drugi nalog istih materijala: spajanje za nesting ne nudi ništa
    assert any(r_["vrsta"] in ("RP", "ZO") for r_ in SP._redovi(c, ("unos",)))
    assert not [k for k in SP.kandidati(c, ("unos",), prag_ploca=0.0) if k["ident"] in ("RP000001", "RP000102", "RP000900")]


def test_obrub_ploce_po_materijalu(baza_o, monkeypatch):
    """Igor 17. 9.: obrub (rubljenje) ploče u dijalogu materijala — zadano 10 mm, radne ploče / stol / zidne 0; upisani obrub vrijedi
    za optimizaciju, CPO i obračun; promjena obruba poništi potvrđenu optimizaciju (novi hash)."""
    from fastapi.testclient import TestClient
    import hub.api.app as A
    from tests.test_popravci_2026_09_15 import _nalog
    c = baza_o
    nid, nm, e1, e2 = _nalog(c, status="ponuda")                        # IV000090 800×560 + 400×300 na 2800×2070
    m = N.materijal_naloga(c, nm)
    assert m["obrub"] is None and m["obrub_zadano"] == 10
    assert OP.ulaz_materijala(c, nm)[4] == 10
    nid2, radna, stol, zid = _nalog_rp(c)
    assert N.materijal_naloga(c, radna)["obrub_zadano"] == 0 and OP.ulaz_materijala(c, radna)[4] == 0 and OP.ulaz_materijala(c, zid)[4] == 0
    p = OP.predlozi(c, nm, tko="IVANA")
    OP.potvrdi(c, p["id"], "IVANA")
    assert p["obrez"] == 10
    N.uredi_materijal(c, nm, "IVANA", obrub=25)
    assert OP.ulaz_materijala(c, nm)[4] == 25 and OP.potvrdjena(c, nm) is None               # potvrda zastarjela — treba nova optimizacija
    assert OP.predlozi(c, nm, tko="IVANA")["obrez"] == 25
    N.uredi_materijal(c, radna, "IVANA", obrub=10)                                         # i radnoj ploči se smije upisati
    assert OP.ulaz_materijala(c, radna)[4] == 10
    with pytest.raises(N.NalogGreska):
        N.uredi_materijal(c, nm, "IVANA", obrub=80)
    # API: izostavljen obrub ne mijenja ništa, null vraća na zadano
    monkeypatch.setenv("HUB_DB", str(c.dir / "hub.db"))
    A._veza = None
    k = TestClient(A.app)
    r = k.put("/api/nalog/materijal/%d" % nm, json=dict(napomena="x", tko="IVANA")).json()
    assert r["obrub"] == 25 and r["napomena"] == "x"
    r = k.put("/api/nalog/materijal/%d" % nm, json=dict(obrub=None, tko="IVANA")).json()
    assert r["obrub"] is None and r["obrub_zadano"] == 10
    r = k.put("/api/nalog/materijal/%d" % nm, json=dict(obrub=0, tko="IVANA")).json()
    assert r["obrub"] == 0
