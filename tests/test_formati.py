"""Round-trip testovi formata na stvarnim datotekama (trebaju mapu 05_NALOZI_ZA_TEST; preskaču se ako je nema).
HUB_TEST_DATA = putanja do Paneli_Production_Hub\\05_NALOZI_ZA_TEST"""
import os, glob, pytest
from hub.formati import cpo_rw, nalog_io

DATA = os.environ.get('HUB_TEST_DATA')
pytestmark = pytest.mark.skipif(not DATA or not os.path.isdir(DATA), reason='HUB_TEST_DATA nije postavljen')

def test_cpo_roundtrip_identican():
    files = glob.glob(os.path.join(DATA, '*', '03_export_pila', '*.cpo'))
    assert files
    for f in files:
        raw = open(f, 'rb').read()
        assert cpo_rw.write(cpo_rw.parse(raw)) == raw, f

def test_ppnest_csv_iz_txt_identican():
    n = 0
    for t in glob.glob(os.path.join(DATA, '*', '04_export_nesting', '*', '*.txt')):
        c = os.path.join(os.path.dirname(t), 'NESTING', os.path.basename(t)[:-4] + '.CSV')
        if not os.path.exists(c):
            continue
        els = nalog_io.read_ppnest_txt(t)
        out = os.path.join(os.path.dirname(t), '_hub_test.csv')
        nalog_io.write_ppnest_csv(els, out)
        try:
            assert open(out, 'rb').read() == open(c, 'rb').read(), t
        finally:
            os.remove(out)
        n += 1
    assert n > 0
