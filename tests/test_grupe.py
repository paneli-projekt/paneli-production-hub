# -*- coding: utf-8 -*-
"""Korak 6 — mjera za rezanje i majka (D-70 niz goda, D-79 lijepljenje, D-80 mali komadi).
Sintetički dio: fixture `baza` iz tests/test_nalozi.py (IV BIJELI NK 18 s trakama 0,5/22, 1/22, 2/22, 1/44).
Stvarni dio (HUB_TEST_DATA): Corpus uzorak `_CORPUS_UZORAK\\LIJEPLJENJE` (TEST LJEPLJENJE NK: sloj 1 CHAMPAGNE 19 + sloj 2 BIJELI NK 18 → 37 mm)."""
import os
import pytest

from hub.nalozi import nalozi as N, grupe as G, obracun as OC, export_pila as EP, export_nesting as EN, uvoz_corpus as UC, provjera as PR
from hub.formati import cpo_rw, nalog_io
from tests.test_nalozi import baza  # noqa: F401
from tests.test_sifrarnik import DATA, stvarni, stvarna_baza  # noqa: F401

SVI = {"L": "ABS-ISTI", "O": "ABS-ISTI", "D": "ABS-ISTI", "G": "ABS-ISTI"}
KRATKI = {"O": "ABS-ISTI", "G": "ABS-ISTI"}          # rubovi duž W (kraća strana kad je L > W)
DUGI = {"L": "ABS-ISTI", "D": "ABS-ISTI"}            # rubovi duž L


def _nalog(baza, ident="IV000090"):
    k = baza.execute("SELECT id FROM kupac WHERE naziv LIKE '%Humer%'").fetchone()[0]
    n = N.novi_nalog(baza, "IVANA", kupac_id=k, projekt="GRUPE")
    mid = baza.execute("SELECT id FROM materijal WHERE pantheon_ident = ?", (ident,)).fetchone()[0]
    nm, _ = N.dodaj_materijal(baza, n["id"], "IVANA", materijal_id=mid)
    return n, nm


def _us000007(baza):
    baza.execute("INSERT OR IGNORE INTO pantheon_ident (ident, naziv, jm, cijena_neto, cijena_prodajna, aktivan) VALUES ('US000007', 'USLUGA LJEPLJENJA PLOČA', 'M2', 7.0, 8.75, 1)")
    baza.commit()


# ------------------------------------------------------------------ čitanje oznaka i pravilo
def test_procitaj_naziv():
    assert G.procitaj_naziv("FR1_A1")["niz"]["oznaka"] == "A1" and G.procitaj_naziv("FR1_A1")["osnova"] == "FR1"
    n = G.procitaj_naziv("FR11_E1H")["niz"]
    assert (n["slovo"], n["rb"], n["smjer"], n["oznaka"]) == ("E", 1, "H", "E1H")
    n = G.procitaj_naziv("FR20_c1-2")["niz"]
    assert (n["slovo"], n["smjer"], n["red"], n["stupac"], n["oznaka"]) == ("C", "G", 1, 2, "C1-2")
    assert G.procitaj_naziv("FR3")["niz"] is None and G.procitaj_naziv("bok_lijevi")["niz"] is None
    assert G.procitaj_naziv("POLICA_LA2")["sloj"] == ("A", 2) and G.procitaj_naziv("POLICA_LA2")["osnova"] == "POLICA"
    assert G.procitaj_naziv("2DA 2KA =930x340")["konacna"] == (930.0, 340.0)
    c = G.procitaj_naziv(",(I) (37)#: 1465.00 x 600.00")
    assert c["corpus_sklop"] == dict(debljina=37.0, L=1465.0, W=600.0)
    assert G.procitaj_naziv("skica 2")["kupceva_skica"] == 2 and G.procitaj_naziv("SK 5")["kupceva_skica"] == 5
    assert G.procitaj_niz("A1")["rb"] == 1 and G.procitaj_niz("") is None


def test_pravilo_malih():
    assert G.pravilo_malih(600, 120, True, True) == (600.0, 150.0, "SUZITI NA 120")
    assert G.pravilo_malih(600, 120, True, False) == (None, None, None)              # kant samo po dugoj strani, širina 120 ≥ 60
    assert G.pravilo_malih(300, 50, True, False) == (300.0, 60.0, "SUZITI NA 50")     # uži od 60 kroz kantericu
    assert G.pravilo_malih(100, 40, True, True) == (150.0, 150.0, "SUZITI 100x40")
    assert G.pravilo_malih(800, 400, True, True) == (None, None, None)
    assert G.pravilo_malih(120, 600, True, False) == (150.0, 600.0, "SUZITI NA 120")   # kraća strana je L (rub duž L = 120)


# ------------------------------------------------------------------ D-80: pojedinačna nadmjera + majka malih komada
def test_suziti_i_majka_malih(baza, tmp_path):
    n, nm = _nalog(baza)
    e1 = N.dodaj_element(baza, nm["id"], "IVANA", 600, 120, 2, naziv="letvica", rubovi=KRATKI)       # < 4 komada (drukčiji kant) → pojedinačno
    e2 = N.dodaj_element(baza, nm["id"], "IVANA", 600, 120, 9, naziv="letvica", rubovi=SVI)          # 9 + 6 istih → majka
    e3 = N.dodaj_element(baza, nm["id"], "IVANA", 600, 120, 6, naziv="letvica2", rubovi=SVI)
    e4 = N.dodaj_element(baza, nm["id"], "IVANA", 300, 50, 6, naziv="uska", rubovi=DUGI)             # uža od 60 → pojedinačno (majka ne pomaže)
    e5 = N.dodaj_element(baza, nm["id"], "IVANA", 800, 400, 1, naziv="polica", rubovi=SVI)
    r = G.primijeni(baza, n["id"], "IVANA")
    assert not r["upozorenja"], r["upozorenja"]
    # e1: pojedinačno na 150, etiketa; e2 + e3 (isti ključ) su ČLANOVI majke M1
    e1 = N.element(baza, e1["id"])
    assert (e1["rez_L"], e1["rez_W"], e1["rez_razlog"], e1["napomena_etiketa"]) == (600.0, 150.0, "suziti", "SUZITI NA 120")
    assert (e1["L"], e1["W"]) == (600.0, 120.0)
    e4 = N.element(baza, e4["id"])
    assert (e4["rez_L"], e4["rez_W"], e4["napomena_etiketa"]) == (300.0, 60.0, "SUZITI NA 50")
    assert N.element(baza, e5["id"])["rez_razlog"] is None
    majke = r["majke"]
    assert len(majke) == 1 and majke[0]["vrsta"] == "mali" and majke[0]["oznaka"] == "M1" and majke[0]["komada"] == 15
    assert {c["id"] for c in majke[0]["clanovi"]} == {e2["id"], e3["id"]}
    # 15 × 120 + 14 × 5 = 1870 ≤ 2780 (bez goda) → jedna majka 1870 × 600, kom 1; kant kratkih rubova komada na dugim rubovima majke (rub1 / rub3)
    em = majke[0]["elementi_majke"]
    assert len(em) == 1 and (em[0]["L"], em[0]["W"], em[0]["kom"]) == (1870.0, 600.0, 1)
    assert em[0]["rub1_kod"] == "ABS-ISTI" and em[0]["rub3_kod"] == "ABS-ISTI" and not em[0]["rub2_kod"] and not em[0]["rub4_kod"]
    assert em[0]["napomena_rez"] == "M1 15x600x120"
    assert N.element(baza, e2["id"])["napomena_etiketa"] == "IZ M1"
    # na stroj: e1 (600 × 150), majka, e4 (300 × 60), e5 — bez članova
    ex = N.elementi_za_export(baza, n["id"])
    assert [(x["L"], x["W"], x["kom"], x["vrsta"]) for x in ex] == [(600.0, 150.0, 2, "element"), (300.0, 60.0, 6, "element"), (800.0, 400.0, 1, "element"), (1870.0, 600.0, 1, "majka")]
    assert ex[0]["napomena"] == "SUZITI NA 120" and ex[0]["L_kon"] == 600 and ex[0]["W_kon"] == 120
    assert len(N.elementi_konacni(baza, nm["id"])) == 5
    # idempotentno: drugi put isto, bez duplih majki
    r2 = G.primijeni(baza, n["id"], "IVANA")
    assert len(r2["majke"]) == 1 and baza.execute("SELECT COUNT(*) FROM element WHERE vrsta = 'majka'").fetchone()[0] == 1
    # obračun: trake po KONAČNOJ mjeri članova (2 × 240 + 15 letvica 600 × 120 sve četiri + uska 2 × 300 × 6 + polica) → (480 + 21 600 + 3 600 + 2 400) × 1,10 = 30 888 → 31 m
    o = OC.izracunaj(baza, n["id"], pravila=False)
    tr = [s for s in o["stavke"] if s["grupa"] == "traka"]
    assert len(tr) == 1 and tr[0]["pantheon_ident"] == "TR000168" and tr[0]["kolicina"] == 31
    # izvoz na pilu (forsiraj): CPO nosi majku i napomenu SUZITI
    N.postavi_status(baza, n["id"], "ponuda", "IVANA")
    r = EP.izvezi(baza, n["id"], str(tmp_path), "IVANA", forsiraj=True)
    p = r["paketi"][0]
    d = cpo_rw.parse(open(p["cpo"], "rb").read())
    assert sorted((o["L"], o["W"]) for o in d["ord"]) == [(300.0, 60.0), (600.0, 150.0), (800.0, 400.0), (1870.0, 600.0)]
    assert any(o["note"].startswith("SUZITI NA 120") for o in d["ord"]) and any(o["note"].startswith("M1 15x600x120") for o in d["ord"])
    assert len(p["majke"]) == 1 and len(p["suzeno"]) == 2
    assert p.get("skice_majki") and os.path.exists(p["skice_majki"][0]["png"])
    # promjena člana (nakon vraćanja u unos) → majka se preslaže sama; brisanje člana ispod 4 → majke nema
    N.postavi_status(baza, n["id"], "unos", "IVANA")
    N.uredi_element(baza, e3["id"], "IVANA", kom=1)
    assert G.pregled(baza, n["id"])[0]["komada"] == 10
    N.obrisi_element(baza, e2["id"], "IVANA")
    assert G.pregled(baza, n["id"]) == [] and N.element(baza, e3["id"])["rez_W"] == 150.0
    with pytest.raises(N.NalogGreska):
        N.obrisi_element(baza, ex[3]["element_id"], "IVANA") if baza.execute("SELECT 1 FROM element WHERE id = ?", (ex[3]["element_id"],)).fetchone() else (_ for _ in ()).throw(N.NalogGreska("obrisana"))


def test_majka_s_godom_i_vise_majki(baza):
    """Materijal s godom (VSM02): stog ide poprijeko uz širinu ploče 1220 − 20 = 1200 → 30 × 120 = 3730 → 4 majke po 8 / 8 / 7 / 7."""
    n, nm = _nalog(baza, "IV000671")
    N.dodaj_element(baza, nm["id"], "IVANA", 500, 120, 30, naziv="letvica", rubovi=KRATKI)
    r = G.primijeni(baza, n["id"], "IVANA")
    m = r["majke"][0]
    assert m["vrsta"] == "mali" and m["komada"] == 30 and m["smjer"] == "W"
    em = sorted(((x["L"], x["W"], x["kom"]) for x in m["elementi_majke"]), reverse=True)
    assert em == [(500.0, 995.0, 2), (500.0, 870.0, 2)]          # 8 × 120 + 7 × 5 = 995; 7 × 120 + 6 × 5 = 870
    assert all(x["rub2_kod"] == "ABS-ISTI" and x["rub4_kod"] == "ABS-ISTI" and not x["rub1_kod"] for x in m["elementi_majke"])
    assert sum(x["kom"] for x in N.elementi_za_export(baza, n["id"])) == 4


# ------------------------------------------------------------------ D-79: sklop lijepljenja iz kupčevog PPW-a / ručnog unosa
def test_sklop_lijepljenja_sufiks(baza):
    _us000007(baza)
    n, nm = _nalog(baza)
    a1 = N.dodaj_element(baza, nm["id"], "IVANA", 940, 350, 2, naziv="POLICA_LA1", rubovi=SVI)
    a2 = N.dodaj_element(baza, nm["id"], "IVANA", 940, 350, 2, naziv="POLICA_LA2", rubovi=SVI)
    r = G.primijeni(baza, n["id"], "IVANA")
    assert not r["upozorenja"], r["upozorenja"]
    m = r["majke"][0]
    assert (m["vrsta"], m["oznaka"], m["L"], m["W"], m["debljina"], m["clanova"], m["komada"]) == ("lijepljenje", "LA", 930.0, 340.0, 36.0, 2, 2)
    a1, a2 = N.element(baza, a1["id"]), N.element(baza, a2["id"])
    assert (a1["L"], a1["W"], a1["rez_L"], a1["rez_W"], a1["rez_razlog"], a1["ljepljenje"]) == (930.0, 340.0, 940.0, 350.0, "sloj", "A1")
    assert a1["napomena_etiketa"] == "LA1/2>930x340" and a2["napomena_etiketa"] == "LA2/2>930x340"
    assert a1["rub1_traka"] == "TR000536" and a1["rub1_klasa"] == "1/44"          # klasa po Σ debljina 36 → /44
    assert not any(a2["rub%d_kod" % i] for i in range(1, 5)) and a2["provjeri"] == 0    # kant samo na sklopu (vidljivi sloj)
    ex = N.elementi_za_export(baza, n["id"])
    assert [(x["L"], x["W"], x["kom"]) for x in ex] == [(940.0, 350.0, 2), (940.0, 350.0, 2)]
    o = OC.izracunaj(baza, n["id"], pravila=False)
    lj = [s for s in o["stavke"] if s["pantheon_ident"] == "US000007"]
    assert len(lj) == 1 and lj[0]["kolicina"] == 0.658 and lj[0]["grupa"] == "usluga"       # 0,94 × 0,35 × 2 kom (sirova mjera jednog sloja)
    tr = [s for s in o["stavke"] if s["grupa"] == "traka"]
    assert tr[0]["pantheon_ident"] == "TR000536" and tr[0]["kolicina"] == 6              # (930 + 340) × 2 × 2 × 1,10 = 5,588 → 6 m po konačnoj mjeri
    kant = [s for s in o["stavke"] if s["grupa"] == "kantiranje"]
    assert kant[0]["pantheon_ident"] == "US000012"                                       # usluga kantiranja /44
    # sloj 1 više nije sloj → natrag na upisanu (sirovu) mjeru; sklop nestaje
    N.uredi_element(baza, a1["id"], "IVANA", ljepljenje="")
    a1 = N.element(baza, a1["id"])
    assert (a1["L"], a1["W"], a1["rez_razlog"]) == (940.0, 350.0, None)
    assert G.pregled(baza, n["id"]) == [] and "samo jedan sloj" in str(G.primijeni(baza, n["id"])["upozorenja"])


# ------------------------------------------------------------------ D-70: niz goda iz sufiksa
def test_niz_goda(baza, tmp_path):
    n, nm = _nalog(baza)
    f1 = N.dodaj_element(baza, nm["id"], "IVANA", 406, 497, 1, naziv="FR1_A1", rubovi=SVI)
    f2 = N.dodaj_element(baza, nm["id"], "IVANA", 406, 497, 1, naziv="FR2_A2", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 700, 300, 1, naziv="FR11_E1H", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 700, 400, 1, naziv="FR12_E2H", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 500, 200, 1, naziv="FR20_C1-1", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 500, 300, 1, naziv="FR21_C1-2", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 400, 200, 1, naziv="FR22_C2-1", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 400, 300, 1, naziv="FR23_C2-2", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 800, 500, 1, naziv="BOK", rubovi=SVI)
    r = G.primijeni(baza, n["id"], "IVANA")
    assert not r["upozorenja"], r["upozorenja"]
    m = {x["oznaka"]: x for x in r["majke"]}
    assert (m["A"]["smjer"], m["A"]["L"], m["A"]["W"], m["A"]["clanova"]) == ("V", 817.0, 497.0, 2)          # 406 + 406 + 5 (HUMER skica 2)
    assert (m["E"]["smjer"], m["E"]["L"], m["E"]["W"]) == ("H", 700.0, 705.0)                                 # 300 + 400 + 5
    assert (m["C"]["smjer"], m["C"]["L"], m["C"]["W"]) == ("G", 905.0, 505.0)                                 # redovi 500 + 400 + 5, stupci 200 + 300 + 5
    f1 = N.element(baza, f1["id"])
    assert f1["niz"] == "A1" and f1["majka_poz"] == "A1" and f1["napomena_etiketa"] == "A1/2" and f1["rez_razlog"] is None
    assert [c["poz"] for c in m["C"]["skica"]["clanovi"]] == ["C1-1", "C1-2", "C2-1", "C2-2"]
    ex = N.elementi_za_export(baza, n["id"])
    assert sorted((x["L"], x["W"]) for x in ex) == [(700.0, 705.0), (800.0, 500.0), (817.0, 497.0), (905.0, 505.0)]
    assert [x["napomena"] for x in ex if x["vrsta"] == "majka" and x["L"] == 817] == ["NIZ A (2)"]
    # skica niza
    png = G.skica_png(baza, m["A"]["id"], str(tmp_path / "niz_A.png"))
    assert png and os.path.getsize(png) > 1000
    # trake po frontama (konačna mjera), ne po majci: 2 × (406 + 497) × 2 + (700 + 300) × 2 + (700 + 400) × 2 + 4 fronti mreže + bok
    o = OC.izracunaj(baza, n["id"], pravila=False)
    tr = [s for s in o["stavke"] if s["grupa"] == "traka"]
    ocek = (2 * 2 * (406 + 497) + 2 * (700 + 300) + 2 * (700 + 400) + 2 * (500 + 200) + 2 * (500 + 300) + 2 * (400 + 200) + 2 * (400 + 300) + 2 * (800 + 500)) * 1.1 / 1000
    assert sum(s["kolicina"] for s in tr) == __import__("math").ceil(ocek - 1e-9), (o["upozorenja"], o["stavke"])


def test_niz_iz_kupceve_majke(baza):
    """Kupčev PPW 'skica 2' 817 × 497 × 3: ured upiše fronte 406 + 406 → Hub napravi niz, izračuna 817 i usporedi s kupčevim."""
    n, nm = _nalog(baza)
    e = N.dodaj_element(baza, nm["id"], "IVANA", 817, 497, 3, naziv="skica 2", rubovi={})
    r = G.primijeni(baza, n["id"])
    assert any("kupčev veći komad" in u for u in r["upozorenja"])
    r = G.niz_iz_kupceve_majke(baza, e["id"], [dict(L=406, W=497, rubovi=SVI), dict(L=406, W=497, rubovi=SVI)], "IVANA")
    assert r["niz"] == "A" and not any("provjeriti skicu" in u for u in r["upozorenja"])
    m = r["majke"][0]
    assert (m["L"], m["W"], m["komada"]) == (817.0, 497.0, 6) and m["elementi_majke"][0]["kom"] == 3
    assert not baza.execute("SELECT 1 FROM element WHERE id = ?", (e["id"],)).fetchone()
    # kupčeva mjera koja se ne slaže → upozorenje
    e2 = N.dodaj_element(baza, nm["id"], "IVANA", 2050, 597, 1, naziv="skica 5", rubovi={})
    r = G.niz_iz_kupceve_majke(baza, e2["id"], [dict(L=1227, W=597), dict(L=406, W=597), dict(L=406, W=597)], "IVANA")
    assert any("2049" in u and "provjeriti skicu" in u for u in r["upozorenja"])


# ------------------------------------------------------------------ Corpus: sloj iz CSV-a (LJEPLJENJE), CIX s povećanom mjerom
def test_kopiraj_cix_prosiren(tmp_path):
    src = tmp_path / "a.cix"
    src.write_text("BEGIN MAINDATA\n\tLPX=600\n\tLPY=120\n\tLPZ=18\nEND MAINDATA\n")
    ok, upoz = G.kopiraj_cix_prosiren(str(src), str(tmp_path / "b.cix"), 600, 120, 600, 150)
    assert ok and upoz is None and "LPY=150" in (tmp_path / "b.cix").read_text() and "LPX=600" in (tmp_path / "b.cix").read_text()
    ok, upoz = G.kopiraj_cix_prosiren(str(src), str(tmp_path / "c.cix"), 120, 600, 150, 600)       # obrnuta orijentacija
    assert ok and "LPY=150" in (tmp_path / "c.cix").read_text()
    ok, upoz = G.kopiraj_cix_prosiren(str(src), str(tmp_path / "d.cix"), 700, 120, 700, 150)
    assert not ok and "nisu mjere elementa" in upoz


@stvarni
def test_stvarni_corpus_lijepljenje(stvarna_baza, tmp_path):
    """Corpus uzorak TEST LJEPLJENJE NK: sloj 1 CHAMPAGNE 19 (27045BS-19) + sloj 2 BIJELI NK 18 → sklop 37 mm, konačna 1465 × 600, sirova 1475 × 610."""
    mapa = os.path.join(DATA, "_CORPUS_UZORAK", "LIJEPLJENJE", "NESTING", "TEST LJEPLJENJE NK")
    if not os.path.isdir(mapa):
        pytest.skip("nema Corpus uzorka LIJEPLJENJE")
    _us000007(stvarna_baza)
    nid, izv = UC.uvezi_paket(stvarna_baza, mapa, "TEST", kupac_kratki="PROBA", izvor="provjera", broj="PROV-991", redni=991)
    try:
        g = izv["grupe"]
        assert len(g) == 1 and g[0]["vrsta"] == "lijepljenje" and g[0]["debljina"] == 37 and (g[0]["L"], g[0]["W"]) == (1465.0, 600.0)
        s1, s2 = sorted(g[0]["clanovi"], key=lambda c: c["majka_poz"])
        assert (s1["L"], s1["W"], s1["rez_L"], s1["rez_W"]) == (1465.0, 600.0, 1475.0, 610.0) and s2["rez_razlog"] == "sloj"
        e1, e2 = N.element(stvarna_baza, s1["id"]), N.element(stvarna_baza, s2["id"])
        assert e1["rub1_traka"] == "TR000850" and e1["rub1_klasa"] == "1/44" and e1["provjeri"] == 0        # ABS 1/44 CHAMPAGNE, sloj 1
        assert not any(e2["rub%d_kod" % i] for i in range(1, 5))                                             # sloj 2 bez kanta (D-79)
        assert e1["napomena_etiketa"] == "LA1/2>1465x600"
        m1 = N.materijal_naloga(stvarna_baza, e1["nalog_materijal_id"])
        m2 = N.materijal_naloga(stvarna_baza, e2["nalog_materijal_id"])
        assert (m1["ident"], m2["ident"]) == ("IV000017", "IV000090")
        o = OC.izracunaj(stvarna_baza, nid, pravila=False)
        lj = [s for s in o["stavke"] if s["pantheon_ident"] == "US000007"]
        assert len(lj) == 1 and lj[0]["kolicina"] == 0.9                                                    # 1,475 × 0,61 = 0,89975 → 0,9 m²
        tr = {s["pantheon_ident"]: s["kolicina"] for s in o["stavke"] if s["grupa"] == "traka"}
        assert tr == {"TR000850": 5}                                                                          # (1465 + 600) × 2 × 1,10 = 4,54 → 5 m, samo na sklopu
        r = EN.izvezi(stvarna_baza, nid, str(tmp_path), "TEST", suho=True, forsiraj=True)
        assert sum(p["komada"] for p in r["paketi"]) == 2 and all(p["m2"] == round(1.475 * 0.61, 3) for p in r["paketi"])
    finally:
        PR.obrisi_provjere(stvarna_baza)


# ------------------------------------------------------------------ krojni nacrt sa stranicom majki + API
def test_krojni_i_api(baza, monkeypatch, tmp_path):
    from hub.ispis import krojni as KR
    n, nm = _nalog(baza)
    N.dodaj_element(baza, nm["id"], "IVANA", 600, 120, 12, naziv="letvica", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 940, 350, 2, naziv="POLICA_LA1", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 940, 350, 2, naziv="POLICA_LA2", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 800, 400, 1, naziv="bok", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 406, 497, 1, naziv="FR1_A1", rubovi=SVI)
    N.dodaj_element(baza, nm["id"], "IVANA", 406, 497, 1, naziv="FR2_A2", rubovi=SVI)
    r = KR.pdf(baza, [nm["id"]], str(tmp_path / "krojni.pdf"))
    assert r["stranica"] >= 3 and os.path.getsize(r["put"]) > 5000          # listovi + statistika + majke
    if os.environ.get("HUB_PROBA_MAPA"):                                     # probni ispis za pregled (docs/sheme_proba)
        import shutil
        shutil.copyfile(r["put"], os.path.join(os.environ["HUB_PROBA_MAPA"], "krojni_proba_majke.pdf"))
        for mk in G.pregled(baza, n["id"]):
            G.skica_png(baza, mk["id"], os.path.join(os.environ["HUB_PROBA_MAPA"], "majka_proba_%s.png" % mk["oznaka"]))
    d = KR.podaci(baza, nm["id"])
    assert len(d["majke"]) == 3 and {m["vrsta"] for m in d["majke"]} == {"mali", "lijepljenje", "niz"}
    assert any(e["vrsta"] == "majka" for e in d["elementi"]) and any("sirova mjera sloja" in e["napomena"] for e in d["elementi"])
    assert {t["klasa"]: round(t["metri_tocno"], 3) for t in d["trake"]} == {"1/22": 23.292, "1/44": 5.08}    # članovi po konačnoj mjeri (+ 2 fronte niza 1,806 × 2); sklop /44 po 930 × 340
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    from hub.sifrarnici import prepoznaj as P
    monkeypatch.setenv("HUB_DB", str(baza.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    c = TestClient(A.app)
    try:
        g = c.get("/api/nalog/%d/grupe" % n["id"]).json()["majke"]
        assert len(g) == 3 and g[0]["clanovi"]
        assert c.post("/api/nalog/%d/grupe" % n["id"], json=dict(tko="IVANA")).json()["suzeno"] == 0
        assert c.get("/api/majka/%d/skica.png" % g[0]["id"]).status_code == 200
        e = c.post("/api/nalog/materijal/%d/elementi" % nm["id"], json=dict(L=817, W=497, kom=1, naziv="skica 2", tko="IVANA")).json()
        r = c.post("/api/nalog/element/%d/niz" % e["id"], json=dict(fronte=[dict(L=406, W=497, rubovi=SVI), dict(L=406, W=497, rubovi=SVI)], tko="IVANA")).json()
        assert r["niz"] == "B" and len(r["majke"]) == 4
        p = c.get("/api/nalog/%d" % n["id"]).json()
        assert len(p["grupe"]) == 4 and p["materijali"][0]["majke"]
        assert c.get("/api/nalog/%d/ispis/krojni.pdf" % n["id"], params=dict(mapa=str(tmp_path))).status_code == 200
    finally:
        c.close()
        A._veza = None
