from hub.optimizacija import pila_optimizator as po
from hub.formati import cpo_rw

def _cpo_valid(dijelovi, god):
    sh, oc, nacin, _ = po.najbolje(dijelovi, (2800, 2070), 10, 16.0, god)
    d = dict(ctl1=dict(grain='Y' if god else 'N'), ctl2=[16.0], inv=[dict(L=2800, W=2070, trim=[10] * 4)],
             ord=[dict(idx=i, W=W, L=L, qty=k) for i, W, L, k in dijelovi],
             pat=[dict(no=i + 1, dir=s['dir'], qty=1, cuts=po.sheme_u_cuts(s)) for i, s in enumerate(sh)])
    return cpo_rw.validate(d), oc

def test_sheme_valjane_s_godom():
    err, oc = _cpo_valid([(1, 496, 996, 1), (2, 496, 796, 1), (3, 566, 680, 1), (4, 195, 412, 4), (5, 218, 300, 2)], True)
    assert err == [] and oc['ploca'] == 1

def test_sheme_valjane_bez_goda():
    err, oc = _cpo_valid([(1, 380, 1000, 2), (2, 380, 900, 2), (3, 380, 464, 4), (4, 100, 464, 4), (5, 412, 694, 2)], False)
    assert err == [] and oc['ploca'] == 1

def test_d19_s_godom_samo_uzduzno():
    _, _, nacin, kand = po.najbolje([(1, 400, 1200, 6)], (2800, 2070), 10, 16.0, True)
    assert all(k[3] in po.NACINI_S_GODOM for k in kand)

def test_pw_trik_kombinacija_sirina():
    # EGGER H1180 (SA_016182): 760×140 + 2× 376×2256 s godom → PW traka 768 = 376+16+376, naplata 2,22
    sh, oc, nacin, _ = po.najbolje([(1, 760, 140, 1), (2, 376, 2256, 2)], (2800, 2070), 10, 16.0, True)
    assert oc['ploca'] == 1 and oc['m2_naplata'] <= 2.22
