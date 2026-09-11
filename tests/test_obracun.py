"""Testovi pravila obračuna (PW-metoda) — brojke potvrđene na PW PDF-ovima 11. 9. 2026."""
from hub.optimizacija import obracun

def test_naplata_blago_jasa_bijeli_S():
    # I_01970: shema S, trake 380/900/380/370 → ostatak 696 × 2070, naplata 4,36
    r = obracun.naplata([('S', [380, 900, 380, 370])], (2800, 2070))
    assert r['ostaci'][0][:2] == (696, 2070)
    assert r['m2_naplata'] == 4.36

def test_naplata_blago_jasa_aviva_L():
    # I_01971: shema L, trake 566/446 → ostatak 2800 × 1016, naplata 2,95
    r = obracun.naplata([('L', [566, 446])], (2800, 2070))
    assert r['ostaci'][0][:2] == (2800, 1016)
    assert r['m2_naplata'] == 2.95

def test_naplata_bez_ostatka():
    # HUMER I_01913: 10 ploča bez korisnog ostatka → 57,96
    sheme = [('L', [1830, 190])] + [('L', [550, 550, 557, 340])] * 9
    assert obracun.naplata(sheme, (2800, 2070))['m2_naplata'] == 57.96

def test_ostatak_ispod_kriterija():
    assert obracun.ostatak_ploce("L", [1917], (2800, 2070)) is None   # 2070-10-1917-16 = 127 < 400
    assert obracun.ostatak_ploce('L', [1900, 90], (2800, 2070)) is None

def test_kant_metri():
    els = [dict(L=1000, W=380, kom=2, traka={'L': 'ABS', 'D': 'ABS', 'G': 'ABS', 'O': 'ABS'})]
    # 2 × (1000+1000+380+380) mm = 5,52 m × 1,10 = 6,072
    assert obracun.kant_metri(els) == {'ABS': 6.072}
