"""Bočni izbornik i raspored radnji (Igor, 18. 9. 2026.)

Skladište i Restlovi su dvije stavke bočnog izbornika sa svojim podizborima;
zasebnog ekrana „Skladištar“ više nema (stara poveznica samo preusmjerava).
Svi gumbi, podizbori i pretraživanja stoje LIJEVO.
"""
import os

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hub", "web")


def _txt(ime):
    return open(os.path.join(WEB, ime), encoding="utf-8").read()


def test_bocni_izbornik_ima_restlove():
    js = _txt("app.js")
    assert '["sklad", "Skladište", "#/skladiste"], ["restl", "Restlovi", "#/restlovi"]' in js
    assert "restl:" in js.split("function ico(")[1].split("}[name]")[0]      # ikona za bočni izbornik


def test_podizbori_skladista_i_restlova():
    js = _txt("ekrani.js")
    assert "E.restlovi = async function" in js
    assert 'podizbor("skladiste", pod, [["stanje", "Stanje"], ["izdavanje", "Izdavanje"]])' in js
    assert 'podizbor("restlovi", pod, [["popis", "Popis"], ["potvrda", "Za potvrdu"], ["dekori", "Dekori za potvrdu"]])' in js
    assert "#/skladiste/potvrde" not in js                                   # dekori za potvrdu su prešli pod Restlove
    assert 'E.skladistar = function () { idi("#/restlovi/potvrda"); };' in js  # stara poveznica i dalje radi


def test_radnje_su_lijevo():
    css = _txt("app.css")
    assert "justify-content:flex-start" in css.split(".alatna{")[1].split("}")[0]
    assert ".alatna .grow{flex:0 0 0" in css
    assert ".pane .hd .grow{flex:0 0 0" in css


def test_trake_imaju_vlastitu_tablicu_na_skladistu_naloga():
    """Ekran Skladište naloga: trake su odvojena tablica (naziv / potrebno / raspoloživo / pozicija), a ne stupac uz ploče."""
    js = _txt("ekrani.js")
    assert '<th>Traka</th><th class="r">Potrebno</th><th class="r">Raspoloživo</th><th>Pozicija</th>' in js
    assert "trake-c" not in js                                               # stari zbijeni stupac uz ploče
    assert "nalog nema traka" in js
