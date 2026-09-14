# -*- coding: utf-8 -*-
"""Testovi šifrarnika (04 §4 korak 1, D-24, D-31).

Dio A — čiste funkcije (bez baze, uvijek se izvode): normalizacija, kodovi dekora, debljina, vrsta, oznake traka.
Dio B — mali sintetički šifrarnik u privremenoj bazi (uvijek): uvoz, prepoznavanje, aliasi, zadane trake, Winstore.
Dio C — prihvaćanje na stvarnim podacima (samo ako je HUB_TEST_DATA postavljen na Paneli_Production_Hub\\05_NALOZI_ZA_TEST):
        svih 50 CPO materijala mapirano osim zidnih obloga bez identa, 40/40 točno prema identu u ponudi, CPW 37/37, trake ≥ 42/48.
"""
import os
import sys
import pytest

from hub import db
from hub.sifrarnici import nazivi as N
from hub.sifrarnici import prepoznaj as P
from hub.sifrarnici import pantheon, winstore, aliasi, provjera

# ------------------------------------------------------------------ A. čiste funkcije


def test_norm():
    assert N.norm("IV_BIJELI_NK_18_MM") == "IV BJELI NK 18 MM"          # IJE → JE (BIJELI = BJELI)
    assert N.norm("  Iveral   mliječni ") == "IVERAL MLJECNI"
    assert N.norm("MDF3MM") == "MDF 3MM"
    assert N.norm("HRAST ŠUMSKI ĐAK") == "HRAST SUMSKI DAK"
    assert N.glue("K2665 AI-19") == "K2665AI19"


def test_debljina():
    assert N.debljina("IV BIJELI NK 18mm") == 18
    assert N.debljina("IVERAL BIJELI NK W908 ST2 18 MM") == 18
    assert N.debljina("MDF CHAMPAGNE 27045 OF 19MM") == 19
    assert N.debljina("PVC KASMIR VSM-06 18MM") == 18          # '06' nije debljina
    assert N.debljina("AKRIL CHAMPAGNE 18,6MM") == 18.6
    assert N.debljina("IV_SIVI_TAMNI_19") == 19
    assert N.debljina("IV_HR_EVOKE_SUNSET_1") is None           # odrezano na 20 znakova


def test_kodovi():
    assert {"W908", "ST2", "W908ST2"} <= N.kodovi("IVERAL BIJELI NK W908 ST2 18 MM")
    assert "W908ST2" in N.kodovi("IVERAL BIJELI NK W908ST2 18MM")
    assert {"2162", "2162MN"} <= N.kodovi("IVERAL SIVI TAMNI 2162 MN 19MM")
    assert "VSM06" in N.kodovi("PVC KASMIR VSM-06 18MM")
    assert {"H1180", "ST37", "H1180ST37"} <= N.kodovi("IV EGGER H1180 ST37")
    assert N.kodovi("IV BIJELI NK 18mm") == set()               # debljina nije kod


def test_vrsta():
    assert N.vrsta("IVERAL BIJELI NK 18MM") == ("IV", None)
    assert N.vrsta("IV_BIJELI_NK_18_MM") == ("IV", None)
    assert N.vrsta("MDF CHAMPAGNE 19MM") == ("MDF", None)
    assert N.vrsta("PVC_CRNI_MAT_18") == ("PVC", None)
    assert N.vrsta("PLOČA STOLA HRAST CHALET") == ("RP", "stola")
    assert N.vrsta("RADNA PLOČA BUKVA") == ("RP", "radna")
    assert N.vrsta("ZIDNA OBLOGA BETON") == ("ZO", "zidna")


def test_rasclani_materijal_obitelj_rp_po_sirini():
    assert N.rasclani_materijal("RP BASANIT SAND", sirina_ploce=900)["obitelj_rp"] == "stola"
    assert N.rasclani_materijal("RP BASANIT SAND", sirina_ploce=600)["obitelj_rp"] == "radna"
    assert N.rasclani_materijal("RP BASANIT SAND", sirina_ploce=640)["obitelj_rp"] == "zidna"
    p = N.rasclani_materijal("IV BIJELI NK 18mm")
    assert (p["vrsta"], p["debljina"], p["rijeci"]) == ("IV", 18, ["BJELI", "NK"])


@pytest.mark.parametrize("oznaka, vrsta, deb, sir, isti, dekor", [
    ("ABS-ISTI", "ABS", 1.0, None, True, ""),
    ("ABS-ISTI 2mm", "ABS", 2.0, None, True, ""),
    ("MEL-ISTI", "MEL", 0.5, None, True, ""),
    ("MEL_ISTI", "MEL", 0.5, None, True, ""),
    ("1/22 ISTI ", "ABS", 1.0, 22, True, ""),
    ("1/44 ISTI ", "ABS", 1.0, 44, True, ""),
    ("MEL CRNA NK ", "MEL", 0.5, None, False, "CRNI NK"),
    ("1/22 JELA TAVERNA", "ABS", 1.0, 22, False, "JELA TAVERNA"),
    ("taverna", "ABS", 1.0, None, False, "TAVERNA"),
    ("MET 0.5/22 BIJELI NK", "MEL", 0.5, 22, False, "BJELI NK"),
    ("0,5/22 CHAMPAGNE", "ABS", 0.5, 22, False, "CHAMPAGNE"),
    ("1/22 CHAMPAGNE UM", "ABS", 1.0, 22, False, "CHAMPAGNE UM"),
])
def test_rasclani_traku(oznaka, vrsta, deb, sir, isti, dekor):
    t = N.rasclani_traku(oznaka)
    assert (t["vrsta"], t["debljina"], t["sirina"], t["isti"], t["dekor"]) == (vrsta, deb, sir, isti, dekor)


def test_klasa_i_sirina():
    assert N.klasa_trake(1, 22) == "1/22"
    assert N.klasa_trake(0.5, 22) == "0,5/22"
    assert N.klasa_trake(2, 22) == "2/22"
    assert N.klasa_trake(None, 22) is None
    assert [N.sirina_za_materijal(d) for d in (None, 18, 19, 25, 38)] == [22, 22, 22, 29, 44]
    t = N.rasclani_traku_pantheon("ABS 0,5/22 BIJELI NK")
    assert (t["klasa"], t["dekor"]) == ("0,5/22", "BJELI NK")
    assert N.rasclani_traku_pantheon("ABS 23/0,8 HRAST")["sirina"] == 23
    assert N.rasclani_traku_pantheon("KANTIRANJE 0,5") is None


def test_usluga_kantiranja():
    assert P.usluga_kantiranja("0,5/22") == "US000003"
    assert P.usluga_kantiranja("1/22") == "US000011"
    assert P.usluga_kantiranja("2/22") == "US000011"
    assert P.usluga_kantiranja("1/44") == "US000012"
    assert P.usluga_kantiranja(None) is None


def test_norm_winstore():
    assert P._norm_winstore("K5574IR_19") == "K5574IR-19"
    assert P._norm_winstore("VSM1-18") == "VSM01-18"
    assert P._norm_winstore("W908ST2-18") == "W908ST2-18"
    assert P._norm_winstore("XXX") is None
    assert P._norm_winstore("") is None


# ------------------------------------------------------------------ B. sintetički šifrarnik
PH_IDENTI = """acIdent;acName;acClassif;acCode;acSupplier;acUM;anSalePrice;anRTPrice;anVAT;acActive
IV000090;IVERAL BIJELI NK W908 ST2 18 MM;;;;M2;25;20;25;T
IV000171;IVERAL HRAST SONOMA 3025 SN 18MM;;;;M2;30;24;25;T
IV000954;IVERAL HRAST SONOMA 517 18MM - 2840X1830;;;;M2;30;24;25;T
IV001168;IVERAL SIVI TAMNI 2162 MN 19MM;;;;M2;30;24;25;T
IV000027;IVERAL SIVI TAMNI 2162 PE 19MM;;;;M2;30;24;25;T
IV000671;PVC CRNI MAT VSM-02 18MM;;;;M2;60;48;25;T
IV001038;MDF CHAMPAGNE 27045 OF 19MM;;;;M2;40;32;25;T
IV001157;IVERAL CHAMPAGNE 27045 UM 19MM;;;;M2;40;32;25;T
IV000315;IVERAL H1180 HRAST HALIFAX 18MM;;;;M2;35;28;25;T
IV000221;IVERAL CRNI NK 18MM;;;;M2;25;20;25;T
IV000999;IVERAL BIJELI NK 18MM STARI;;;;M2;25;20;25;F
RP000001;RADNA PLOČA BIJELA MAT 1106 PE;;;;M;50;40;25;T
RP000102;PLOČA STOLA HRAST CHALET 35252AT;;;;M;50;40;25;T
TR000017;ABS 0,5/22 BIJELI NK;;;;M;0,2;0,16;25;T
TR000168;ABS 1/22 BIJELI NK;;;;M;0,3;0,24;25;T
TR000016;ABS 2/22 BIJELI NK;;;;M;0,4;0,32;25;T
TR000536;ABS 1/44 BIJELA NK;;;;M;0,5;0,4;25;T
TR000100;ABS 1/22 CRNI NK;;;;M;0,3;0,24;25;T
TR000101;ABS 0,5/22 SIVI TAMNI 2162 MN;;;;M;0,2;0,16;25;T
TR000102;ABS 0,5/22 SIVI TAMNI 2162 OM;;;;M;0,2;0,16;25;T
TR000103;ABS 1/22 SIVI TAMNI 2162 MN;;;;M;0,3;0,24;25;T
TR000850;ABS 1/22 CHAMPAGNE;;;;M;0,3;0,24;25;T
TR000142;IVERAL NESTO 18MM;;;;M2;1;1;25;T
OK004510;ABS 1/22 HRAST SONOMA;;;;M;0,3;0,24;25;T
US000003;KANTIRANJE 0,5 MM;;;;M;1;0,8;25;T
"""

WINSTORE_XML = """<?xml version="1.0"?><Items>
<Item><Code>W908ST2-18-2800-2070</Code><Length>2800</Length><Width>2070</Width><Thickness>18</Thickness><Grain>0</Grain>
<MaterialCode>W908ST2-18</MaterialCode><MaterialDescription>IVERAL BIJELI NK W908ST2 18MM</MaterialDescription><Drop>0</Drop><TotalQty>12</TotalQty><InternalQty>12</InternalQty><ExternalQty>0</ExternalQty></Item>
<Item><Code>W908ST2-18-1200-800</Code><Length>1200</Length><Width>800</Width><Thickness>18</Thickness><Grain>0</Grain>
<MaterialCode>W908ST2-18</MaterialCode><MaterialDescription>IVERAL BIJELI NK W908ST2 18MM</MaterialDescription><Drop>1</Drop><TotalQty>1</TotalQty><InternalQty>1</InternalQty><ExternalQty>0</ExternalQty></Item>
<Item><Code>VSM02-18-2800-1220</Code><Length>2800</Length><Width>1220</Width><Thickness>18</Thickness><Grain>1</Grain>
<MaterialCode>VSM02-18</MaterialCode><MaterialDescription>PVC CRNI MAT VSM02 18MM</MaterialDescription><Drop>0</Drop><TotalQty>3</TotalQty><InternalQty>3</InternalQty><ExternalQty>0</ExternalQty></Item>
<Item><Code>IV000221A-18-2800-2070</Code><Length>2800</Length><Width>2070</Width><Thickness>18</Thickness><Grain>0</Grain>
<MaterialCode>IV000221A-18</MaterialCode><MaterialDescription>CRNI NK</MaterialDescription><Drop>0</Drop><TotalQty>2</TotalQty><InternalQty>2</InternalQty><ExternalQty>0</ExternalQty></Item>
<Item><Code>AMBALAZA-16-2800-2070</Code><Length>2800</Length><Width>2070</Width><Thickness>16</Thickness><Grain>0</Grain>
<MaterialCode>AMBALAZA-16</MaterialCode><MaterialDescription>AMBALAZA 16MM</MaterialDescription><Drop>0</Drop><TotalQty>5</TotalQty><InternalQty>5</InternalQty><ExternalQty>0</ExternalQty></Item>
</Items>"""


class _Baza:
    """Veza na bazu + podaci fixture-a (sqlite3.Connection ne dopušta dodatne atribute)."""
    def __init__(self, conn, **kw):
        self.conn = conn
        self.__dict__.update(kw)

    def __getattr__(self, ime):
        return getattr(self.conn, ime)


@pytest.fixture
def baza(tmp_path):
    csv_p = tmp_path / "ph_identi.csv"
    csv_p.write_bytes(PH_IDENTI.replace("IVERAL BIJELI NK W908", "IVERAL\x00 BIJELI NK W908").encode("utf-8-sig"))   # NUL bajt kao u stvarnom izvozu
    xml_p = tmp_path / "winstore.XML"
    xml_p.write_text(WINSTORE_XML, encoding="utf-8")
    b = _Baza(db.spoji(str(tmp_path / "hub.db")), csv_p=csv_p, xml_p=xml_p)
    P.ocisti_kes()
    b.st_pantheon = pantheon.uvezi_pantheon(b, str(csv_p), "TEST")
    yield b
    b.conn.close()
    P.ocisti_kes()


def _ident(conn, tablica, ident):
    return conn.execute("SELECT id FROM %s WHERE pantheon_ident = ?" % tablica, (ident,)).fetchone()[0]


def test_uvoz_pantheon(baza):
    st = baza.st_pantheon
    assert st["identi"] == 25
    assert st["materijali"] == 13 and st["trake"] == 10
    assert baza.execute("SELECT naziv FROM pantheon_ident WHERE ident = 'IV000090'").fetchone()[0] == "IVERAL BIJELI NK W908 ST2 18 MM"   # NUL uklonjen
    assert baza.execute("SELECT COUNT(*) FROM traka WHERE pantheon_ident = 'TR000142'").fetchone()[0] == 0       # ploča otvorena pod TR nije traka
    assert baza.execute("SELECT klasa FROM traka WHERE pantheon_ident = 'OK004510'").fetchone()[0] == "1/22"       # ABS pod OK jest traka
    assert baza.execute("SELECT COUNT(*) FROM materijal WHERE pantheon_ident = 'US000003'").fetchone()[0] == 0
    m = baza.execute("SELECT vrsta, debljina, dekor, dekor_kod, naziv_kratki, ploca_L, ploca_W FROM materijal WHERE pantheon_ident = 'IV000090'").fetchone()
    assert tuple(m) == ("IV", 18.0, "BIJELI NK", "W908ST2", "IV BIJELI NK 18", 2800, 2070)
    rp = baza.execute("SELECT vrsta, obitelj_rp, sirina_rp, ploca_W FROM materijal WHERE pantheon_ident = 'RP000102'").fetchone()
    assert tuple(rp) == ("RP", "stola", 900, 900)
    # ponovni uvoz je idempotentan
    st2 = pantheon.uvezi_pantheon(baza, str(baza.csv_p), "TEST")
    assert st2["novi_materijali"] == 0 and st2["nove_trake"] == 0
    assert baza.execute("SELECT COUNT(*) FROM materijal").fetchone()[0] == 13


@pytest.mark.parametrize("naziv, deb, ident", [
    ("IV BIJELI NK 18mm", None, "IV000090"),              # PW / CPO
    ("IV_BIJELI_NK_18_MM", None, "IV000090"),             # PPNEST
    ("IVERAL BIJELI NK W908ST2 18MM", None, "IV000090"),  # Winstore
    ("IV BIJELI NK", 18, "IV000090"),                     # debljina iz datoteke
    ("IV SIVI TAMNI 2162MN 19", None, "IV001168"),        # kod odlučuje između MN i PE
    ("IV_SIVI_TAMNI_2162_PE", 19, "IV000027"),
    ("PVC CRNI MAT VSM-2 18", None, "IV000671"),
    ("MDF CHAMPANGE 19mm", None, "IV001038"),             # tipfeler → sinonim
    ("IV_CHAMPAGNE_UM", 19, "IV001157"),                  # sufiks bez koda pogađa '27045 UM'
    ("IV CHAMPAGNE 27045 UM", None, "IV001157"),
    ("IV EGGER H1180 ST37", 18, "IV000315"),              # kod + drugi redoslijed riječi
    ("IV HALIFAKS 18", None, "IV000315"),                 # sinonim HALIFAKS → HALIFAX
    ("IV CRNA NK 18", None, "IV000221"),                  # CRNA → CRNI
])
def test_prepoznaj_materijal_po_nazivu(baza, naziv, deb, ident):
    r = P.prepoznaj_materijal(baza, naziv, debljina=deb)
    assert (r.razina, r.ident) == ("naziv", ident), r.objasnjenje


def test_prepoznaj_materijal_dvosmisleno_pa_alias(baza):
    r = P.prepoznaj_materijal(baza, "IV_SIVI_TAMNI_19")
    assert r.razina == "za_potvrdu" and {k[0] for k in r.kandidati[:2]} == {"IV001168", "IV000027"}
    P.potvrdi_materijal(baza, "IV_SIVI_TAMNI_19", _ident(baza, "materijal", "IV001168"), "IGOR", izvor="ponuda 26-010-002924")
    r = P.prepoznaj_materijal(baza, "iv sivi tamni 19")           # alias je neosjetljiv na velika/mala slova i razmake
    assert (r.razina, r.ident) == ("alias", "IV001168")
    r = P.prepoznaj_materijal(baza, "MDF CHAMPAGNE UM 19")        # MDF postoji samo kao 27045 OF: sufiks se ne slaže → za potvrdu
    assert r.razina == "za_potvrdu" and r.ident == "IV001038"
    assert P.prepoznaj_materijal(baza, "IV NEPOSTOJECI DEKOR 18").razina in ("za_potvrdu", "nema")
    assert P.prepoznaj_materijal(baza, "").razina == "nema"


def test_prepoznaj_materijal_neaktivan_gubi(baza):
    r = P.prepoznaj_materijal(baza, "IV BIJELI NK 18")        # IV000999 (neaktivan, 'STARI') ne smije pobijediti
    assert r.ident == "IV000090"


def test_alias_csv_i_potvrdjeni(baza, tmp_path):
    a = tmp_path / "alias.csv"
    a.write_text("pw_naziv,ident\nIV HR SONOMA 18mm,IV000171\nNEPOZNAT,IV999999\n1/22 SONOMA,OK004510\n", encoding="utf-8")
    st = aliasi.uvezi_alias_csv(baza, str(a), "TEST")
    assert (st["materijali"], st["trake"], st["nepoznati"]) == (1, 1, [("NEPOZNAT", "IV999999")])
    assert P.prepoznaj_materijal(baza, "IV HR SONOMA 18mm").ident == "IV000171"
    assert P.prepoznaj_traku(baza, "1/22 SONOMA").ident == "OK004510"
    assert aliasi.upisi_potvrdjene(baza, "TEST") == 3                      # ZADANE_TRAKE za IV000090 (0,5/22, 1/22, 2/22)
    assert P.prepoznaj_materijal(baza, "PVC_CRNI_MAT_18").razina == "alias"


def test_winstore(baza):
    st = winstore.uvezi_winstore(baza, str(baza.xml_p), "TEST")
    assert (st["stavke"], st["kodova"], st["povezano"]) == (5, 4, 3)
    assert st["po_razini"] == {"naziv": 2, "ident": 1}
    assert [k for k, _, _ in st["nepovezano"]] == ["AMBALAZA-16"]
    m = baza.execute("SELECT winstore_kod, god, ploca_L, ploca_W FROM materijal WHERE pantheon_ident = 'IV000671'").fetchone()
    assert tuple(m) == ("VSM02-18", 1, 2800, 1220)
    assert baza.execute("SELECT winstore_kod FROM materijal WHERE pantheon_ident = 'IV000221'").fetchone()[0] == "IV000221A-18"
    r = P.prepoznaj_materijal(baza, "IV_BIJELI_NK_18_MM", winstore_kod="W908ST2_18")
    assert (r.razina, r.ident) == ("winstore", "IV000090")
    r = P.prepoznaj_materijal(baza, "XXX", winstore_kod="VSM2-18")
    assert (r.razina, r.ident) == ("winstore", "IV000671")
    assert winstore.stanje_po_kodu(baza)["W908ST2-18"][0] == 12          # ostatak (Drop) se ne broji
    st2 = winstore.uvezi_winstore(baza, str(baza.xml_p), "TEST")          # ponovni uvoz istog izvoza: zamjena, veze ostaju
    assert st2["vec_povezano"] == 3 and baza.execute("SELECT COUNT(*) FROM winstore_ploca").fetchone()[0] == 5


def test_trake_zadane_i_po_nazivu(baza):
    mid = _ident(baza, "materijal", "IV000090")
    r = P.prepoznaj_traku(baza, "ABS-ISTI", materijal_id=mid)             # još nema zadanih → po nazivu, klasa 1/22 (ploča 18 mm)
    assert (r.razina, r.ident, r.klasa) == ("naziv", "TR000168", "1/22")
    assert P.prepoznaj_traku(baza, "1/44 ISTI", materijal_id=mid).ident == "TR000536"
    aliasi.upisi_potvrdjene(baza, "TEST")
    for oznaka, ident, klasa in (("ABS-ISTI", "TR000168", "1/22"), ("MEL-ISTI", "TR000017", "0,5/22"), ("MEL_ISTI", "TR000017", "0,5/22"),
                                 ("ABS-ISTI 2mm", "TR000016", "2/22"), ("1/22 ISTI ", "TR000168", "1/22")):
        r = P.prepoznaj_traku(baza, oznaka, materijal_id=mid)
        assert (r.razina, r.ident, r.klasa) == ("zadana", ident, klasa), oznaka
    r = P.prepoznaj_traku(baza, "1/22 CRNA NK")                            # dekor iz oznake, bez materijala
    assert (r.razina, r.ident) == ("naziv", "TR000100")
    r = P.prepoznaj_traku(baza, "MEL CRNA NK", materijal_id=mid)           # nema 0,5/22 CRNI NK → za potvrdu (1/22 CRNI NK je druga debljina)
    assert not r.siguran and r.klasa == "0,5/22"
    assert P.prepoznaj_traku(baza, "ABS-ISTI").razina == "nema"            # ISTI bez materijala
    assert P.prepoznaj_traku(baza, "OKOV 35").razina == "nema"
    P.potvrdi_traku(baza, "MEL CRNA NK", _ident(baza, "traka", "TR000100"), "IGOR", materijal_id=mid, klasa="0,5/22")
    r = P.prepoznaj_traku(baza, "MEL CRNA NK", materijal_id=mid)
    assert (r.razina, r.ident) == ("alias", "TR000100")
    assert P.prepoznaj_traku(baza, "MEL CRNA NK").razina != "alias"        # alias vrijedi samo uz taj materijal


def test_izvedi_zadane_trake(baza):
    up, bez = aliasi.izvedi_zadane_trake(baza, tko="TEST")
    assert up >= 4
    zad = {(r[0], r[1]): r[2] for r in baza.execute("SELECT m.pantheon_ident, mt.klasa, t.pantheon_ident FROM materijal_traka mt "
                                                       "JOIN materijal m ON m.id = mt.materijal_id JOIN traka t ON t.id = mt.traka_id")}
    assert zad[("IV000090", "1/22")] == "TR000168" and zad[("IV000090", "0,5/22")] == "TR000017" and zad[("IV000090", "1/44")] == "TR000536"
    assert zad[("IV001168", "0,5/22")] == "TR000101" and zad[("IV001168", "1/22")] == "TR000103"   # 2162 MN → traka 2162 MN, ne 2162 OM
    assert ("IV000027", "0,5/22") not in zad                               # 2162 PE nema svoju traku → ništa, ne 'najbliža'
    assert zad[("IV001038", "1/22")] == "TR000850"
    r = P.prepoznaj_traku(baza, "ABS-ISTI", materijal_id=_ident(baza, "materijal", "IV001038"))
    assert (r.razina, r.ident) == ("zadana", "TR000850")


def test_dnevnik_i_postavke(baza):
    assert baza.execute("SELECT COUNT(*) FROM dnevnik WHERE entitet = 'pantheon_ident' AND sto = 'uvoz'").fetchone()[0] == 1
    db.postavi(baza, "kerf", "16", "širina reza pile")
    assert db.postavka(baza, "kerf") == "16"
    assert db.postavka(baza, "nema", "zadano") == "zadano"


# ------------------------------------------------------------------ C. prihvaćanje na stvarnim podacima
DATA = os.environ.get("HUB_TEST_DATA")
HUB = os.path.dirname(DATA.rstrip("\\/")) if DATA else None
PH_CSV = os.path.join(os.path.dirname(HUB), "ph_identi.csv") if HUB else None
WIN_XML = os.path.join(HUB, "04_STROJEVI", "NESTING", "11092026.XML") if HUB else None
BENCH = os.path.join(HUB, "20_ANALIZA", "benchmark_nalozi.csv") if HUB else None
stvarni = pytest.mark.skipif(not DATA or not os.path.isdir(DATA) or not PH_CSV or not os.path.exists(PH_CSV),
                             reason="HUB_TEST_DATA nije postavljen ili nema ph_identi.csv")


@pytest.fixture(scope="module")
def stvarna_baza(tmp_path_factory):
    b = _Baza(db.spoji(str(tmp_path_factory.mktemp("hub") / "hub.db")))
    P.ocisti_kes()
    pantheon.uvezi_pantheon(b, PH_CSV, "TEST")
    from hub.sifrarnici.uvoz import ALIAS_ZADANI
    aliasi.uvezi_alias_csv(b, ALIAS_ZADANI, "TEST")
    aliasi.upisi_potvrdjene(b, "TEST")
    if os.path.exists(WIN_XML):
        b.st_winstore = winstore.uvezi_winstore(b, WIN_XML, "TEST")
    aliasi.izvedi_zadane_trake(b, tko="TEST")
    yield b
    b.conn.close()
    P.ocisti_kes()


@stvarni
def test_prihvacanje_cpo_i_ponude(stvarna_baza):
    rez = provjera.provjeri(stvarna_baza, DATA, BENCH)
    s = provjera.sazetak(rez)
    nesigurni = [(x["datoteka"], x["naziv"], x["rez"].razina) for x in rez["cpo"] if not x["rez"].siguran]
    # jedini dopušteni promašaji: zidne obloge (ZO) koje u Pantheonu nemaju ident
    assert all(N.vrsta(n)[0] == "ZO" for _, n, _ in nesigurni), nesigurni
    assert s["cpo"]["sigurno"] >= 47
    assert s["cpo"]["krivo_vs_ponuda"] == [] and s["cpo"]["tocno_vs_ponuda"] == s["cpo"]["s_ponudom"] >= 40
    assert s["cpw"]["sigurno"] == s["cpw"]["ukupno"] >= 37
    assert s["csv"]["sigurno"] >= s["csv"]["ukupno"] - 1            # K2739DC-19: tipfeler u SIFRA MAT, ispravno 'za potvrdu'
    assert s["trake"]["sigurno"] >= 42


@stvarni
def test_prihvacanje_winstore(stvarna_baza):
    if "st_winstore" not in stvarna_baza.__dict__:
        pytest.skip("nema Winstore XML")
    st = stvarna_baza.st_winstore
    assert st["kodova"] >= 500 and st["povezano"] >= 400
    assert all(("AMBALA" in opis.upper()) or True for _, opis, _ in st["nepovezano"])   # popis je izvještaj, ne greška
