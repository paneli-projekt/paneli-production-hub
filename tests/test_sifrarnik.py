# -*- coding: utf-8 -*-
"""Testovi šifrarnika (04 §4 korak 1, D-24, D-31).

Dio A — čiste funkcije (bez baze, uvijek se izvode): normalizacija, kodovi dekora, debljina, vrsta, oznake traka.
Dio B — mali sintetički šifrarnik u privremenoj bazi (uvijek): uvoz, prepoznavanje, aliasi, zadane trake, Winstore.
Dio C — prihvaćanje na stvarnim podacima (samo ako je HUB_TEST_DATA postavljen na Paneli_Production_Hub\\05_NALOZI_ZA_TEST):
        svih 50 CPO materijala mapirano osim zidnih obloga bez identa, 40/40 točno prema identu u ponudi, CPW 40/40, trake ≥ 44/51.
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


def test_debljina_iz_dimenzije():
    assert N.debljina("ZIDNA PLOČA H3303 ST10 4100X640X8MM") == 8          # debljina iz L x W x T
    assert N.debljina("COMPACT F1861 4100X650X12 JEZGRA U BOJI") == 12
    assert N.debljina("RADNA PLOČA QUARTZ - VEGA 30MM, 2070X600MM") == 30  # dvije mjere nisu debljina, '30MM' jest
    assert N.debljina("IVERAL HRAST SONOMA 517 18MM - 2840X1830") == 18
    assert N.debljina("COMPACT PRADO AGATE GREY 13 0027/NN/CF") == 13      # 13 mm = Fundermax compact
    assert N.zadana_debljina("RP", "radna") == 38 and N.zadana_debljina("RP", "stola") == 38
    assert N.zadana_debljina("ZO", "zidna") is None and N.zadana_debljina("CP", None) is None   # tu debljina varira — ured kaže (D-52)


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


def test_corpus_kod_u_nazivu_i_rod(baza):
    """Corpusov CPW u polje MATERIJAL piše Winstore kod, a dekore u ženskom rodu (D-57, D-58; dokument 14)."""
    winstore.uvezi_winstore(baza, str(baza.xml_p), "TEST")
    r = P.prepoznaj_materijal(baza, "W908ST2-18", debljina=18)              # kod u nazivu, bez zasebnog polja
    assert (r.razina, r.ident) == ("winstore", "IV000090")
    r = P.prepoznaj_materijal(baza, "VSM02-18", debljina=4)                 # kod je jači od deklarirane debljine (MDF nut, D-57)
    assert (r.razina, r.ident) == ("winstore", "IV000671")
    assert N.rijeci("SIVA_TAMNA") == N.rijeci("SIVI TAMNI") == ["SIVI", "TAMNI"]    # ženski rod = muški rod (D-58)
    assert N.rijeci("BIJELA NK") == N.rijeci("BIJELI NK")
    r = P.prepoznaj_traku(baza, "SIVA_TAMNA-1/22")                          # Corpusov ženski rod nađe Pantheonov muški
    assert (r.razina, r.ident) == ("naziv", "TR000103") and "SIVI TAMNI" in r.naziv


def test_traka_pod_rp_identom_nije_materijal(baza):
    """RP ident s nazivom 'TRAKA ZA R.P. …' je kriva klasifikacija u Pantheonu — nije ploča (D-52)."""
    assert pantheon.je_materijal({"acIdent": "RP000020", "acName": "TRAKA ZA R.P. NERO AFRIKA"}) is False
    assert pantheon.je_materijal({"acIdent": "RP000001", "acName": "RADNA PLOČA BIJELA MAT 1106 PE"}) is True
    assert baza.execute("SELECT COUNT(*) FROM materijal WHERE naziv_pantheon LIKE 'TRAKA%'").fetchone()[0] == 0


def test_prednost_izvora_debljine(baza):
    """Redoslijed prednosti (D-52): naziv > ručno > vrsta > Winstore; jedina iznimka je 'debljina_umjesto_naziva' (D-51)."""
    from hub.sifrarnici import ispravci
    ispravci.upisi(baza, "debljina", "RP000102", 25, "test", "IGOR")       # ploča stola bez debljine u nazivu: ured kaže 25
    ispravci.primijeni(baza, "TEST")
    assert baza.execute("SELECT debljina, debljina_izvor FROM materijal WHERE pantheon_ident = 'RP000102'").fetchone()[:] == (25.0, "rucno")
    pantheon.primijeni_zadane_debljine(baza, "TEST")                       # zadanih 38 mm NE gazi ručni upis
    assert baza.execute("SELECT debljina FROM materijal WHERE pantheon_ident = 'RP000102'").fetchone()[0] == 25.0

    ispravci.upisi(baza, "debljina", "IV000221", 25, "test", "IGOR")       # naziv 'IVERAL CRNI NK 18MM' je jači od običnog ručnog upisa
    ispravci.primijeni(baza, "TEST")
    assert baza.execute("SELECT debljina, debljina_izvor FROM materijal WHERE pantheon_ident = 'IV000221'").fetchone()[:] == (18.0, "naziv")

    assert baza.execute("SELECT debljina, debljina_izvor FROM materijal WHERE pantheon_ident = 'IV000090'").fetchone()[:] == (18.0, "naziv")
    ispravci.upisi(baza, "debljina_umjesto_naziva", "IV000090", 19, "naziv u Pantheonu je kriv", "IGOR")   # jedini ispravak jači od naziva
    ispravci.primijeni(baza, "TEST")
    assert baza.execute("SELECT debljina, debljina_izvor FROM materijal WHERE pantheon_ident = 'IV000090'").fetchone()[:] == (19.0, "rucno_umjesto_naziva")
    assert ispravci.naziv_ispravljen(baza) == []                           # naziv još kaže 18 MM — ispravak je i dalje potreban
    baza.execute("UPDATE materijal SET naziv_pantheon = 'IVERAL BIJELI NK W908 ST2 19 MM' WHERE pantheon_ident = 'IV000090'")
    assert [x["ident"] for x in ispravci.naziv_ispravljen(baza)] == ["IV000090"]        # Pantheon ispravljen → ispravak se može maknuti
    ispravci.makni(baza, "debljina_umjesto_naziva", "IV000090", "IGOR")                 # brisanje vraća debljinu iz naziva
    assert baza.execute("SELECT debljina, debljina_rucno, debljina_izvor FROM materijal WHERE pantheon_ident = 'IV000090'").fetchone()[:] == (19.0, None, "naziv")


def test_winstore(baza):
    st = winstore.uvezi_winstore(baza, str(baza.xml_p), "TEST")
    assert (st["stavke"], st["kodova"], st["povezano"]) == (5, 4, 3)
    assert st["po_razini"] == {"naziv": 2, "ident": 1}
    assert st["nepovezano"] == [] and st["ambalaza"] == 1                      # AMBALAZA-16 = podloga za slaganje (D-49): ne povezuje se
    assert "AMBALAZA-16" not in winstore.stanje_po_kodu(baza)                  # i ne ulazi u stanje skladišta
    assert winstore.je_ambalaza("AMABALAZA JANC 18MM") and winstore.je_ambalaza("AMB KRUNO") and not winstore.je_ambalaza("IVERAL BIJELI NK")
    m = baza.execute("SELECT winstore_kod, god, ploca_L, ploca_W FROM materijal WHERE pantheon_ident = 'IV000671'").fetchone()
    assert tuple(m) == ("VSM02-18", 1, 2800, 1220)
    assert baza.execute("SELECT winstore_kod FROM materijal WHERE pantheon_ident = 'IV000221'").fetchone()[0] == "IV000221A-18"
    r = P.prepoznaj_materijal(baza, "IV_BIJELI_NK_18_MM", winstore_kod="W908ST2_18")
    assert (r.razina, r.ident) == ("winstore", "IV000090")
    r = P.prepoznaj_materijal(baza, "XXX", winstore_kod="VSM2-18")
    assert (r.razina, r.ident) == ("winstore", "IV000671")
    assert winstore.stanje_po_kodu(baza)["W908ST2-18"][0] == 12          # ostatak (Drop) se ne broji
    st2 = winstore.uvezi_winstore(baza, str(baza.xml_p), "TEST")          # ponovni uvoz istog izvoza: zamjena, veze ostaju
    assert st2["vec_povezano"] == 3 and st2["povezano"] == 0 and baza.execute("SELECT COUNT(*) FROM winstore_ploca").fetchone()[0] == 5


def test_ispravci(baza):
    from hub.sifrarnici import ispravci
    ident = "IV000090"
    ispravci.upisi(baza, "debljina", "RP000001", 38, "test", "IGOR")           # naziv nema debljinu → upiše se ručna
    ispravci.upisi(baza, "ne_koristi_se", ident, "1", "test", "IGOR")
    ispravci.upisi(baza, "winstore_kod", "W908ST2-18", "IV000671", "test", "IGOR")
    st = ispravci.primijeni(baza, "TEST")
    assert (st["debljina"], st["ne_koristi_se"], st["winstore_kod"], st["nepoznati"]) == (1, 1, 1, [])
    m = baza.execute("SELECT debljina, debljina_rucno FROM materijal WHERE pantheon_ident = 'RP000001'").fetchone()
    assert tuple(m) == (38.0, 38.0)
    ispravci.upisi(baza, "debljina", "IV000090", 25, "test", "IGOR")           # naziv IMA debljinu (18) → Pantheon ostaje glavni
    ispravci.primijeni(baza, "TEST")
    assert baza.execute("SELECT debljina FROM materijal WHERE pantheon_ident = 'IV000090'").fetchone()[0] == 18.0
    assert P.prepoznaj_materijal(baza, "IV BIJELI NK 18 MM").ident != ident    # ident koji se ne koristi Hub više ne nudi
    assert ispravci.veze_winstore(baza) == {"W908ST2-18": _ident(baza, "materijal", "IV000671")}
    st = winstore.uvezi_winstore(baza, str(baza.xml_p), "TEST")                # ručna veza ima prednost pred prepoznavanjem po nazivu
    assert st["rucno"] == 1
    assert baza.execute("SELECT m.pantheon_ident FROM winstore_ploca w JOIN materijal m ON m.id = w.materijal_id WHERE w.materijal_kod = 'W908ST2-18'"
                        ).fetchone()[0] == "IV000671"
    obr = str(baza.csv_p.parent / "obrazac.csv")                            # obrazac iz Excela: zarez kao razdjelnik, višak stupaca, neispravan redak
    open(obr, "w", encoding="utf-8-sig").write(
        "vrsta,kljuc,vrijednost,napomena,,\n"
        "winstore_kod,VSM02-18,IV000090,prebaceno na bijeli,dodatni stupac,\n"
        "winstore_kod,XYZ-18,NIŠTA,roba bez identa,,\n"
        "debljina,RP000102,25,ploca stola,,\n"
        "debljina,RP000001,,jos nije odluceno,,\n")
    n, presk = ispravci.ucitaj_csv(baza, obr, "IVANA")
    assert n == 2 and [(x[1], x[3]) for x in presk] == [("XYZ-18", "nije postojeći ident materijala"), ("RP000001", "prazno — ured još nije odlučio")]
    vsm = [x for x in ispravci.popis(baza, "winstore_kod") if x["kljuc"] == "VSM02-18"][0]
    assert vsm["vrijednost"] == "IV000090" and vsm["napomena"] == "prebaceno na bijeli, dodatni stupac"   # višak stupaca ide u napomenu
    ispravci.primijeni(baza, "TEST")
    assert ispravci.makni(baza, "ne_koristi_se", ident, "IGOR") == 1
    P.ocisti_kes()
    assert baza.execute("SELECT ne_koristi_se FROM materijal WHERE pantheon_ident = ?", (ident,)).fetchone()[0] == 0
    assert P.prepoznaj_materijal(baza, "IV BIJELI NK 18 MM").ident == ident


def test_nalazi(baza):
    from hub.sifrarnici import nalazi
    winstore.uvezi_winstore(baza, str(baza.xml_p), "TEST")
    s = nalazi.sazetak(baza)
    assert s["ambalaza"]["kodova"] == 1                                   # ambalaža se broji odvojeno (D-49), ne kao nepovezani kod
    assert [x["kod"] for x in s["winstore_bez_identa"]] == []             # u testnom XML-u su svi kodovi povezani
    identi = {x["ident"]: x["prioritet"] for x in s["bez_debljine"]}
    assert "RP000102" in identi                                           # ploča stola još nema debljinu
    assert all(p in nalazi.REDOSLIJED for p in identi.values())
    assert pantheon.primijeni_zadane_debljine(baza, "TEST") == [("RP radna", 38.0, 1), ("RP stola", 38.0, 1)]   # D-52
    assert baza.execute("SELECT debljina, debljina_izvor FROM materijal WHERE pantheon_ident = 'RP000102'").fetchone()[:] == (38.0, "vrsta")
    assert "RP000102" not in {x["ident"] for x in nalazi.bez_debljine(baza)}
    md = nalazi.markdown(s)
    assert md.startswith("# Nalazi o šifrarniku") and "## 0." not in md          # bez ispravaka nema sekcije 0
    from hub.sifrarnici import ispravci
    ispravci.upisi(baza, "debljina", "RP000001", 38, "test", "IGOR")
    assert "## 0." in nalazi.markdown(nalazi.sazetak(baza))
    for naslov in ("### 1.1", "### 1.3", "### 2.1", "## 3."):
        assert naslov in md, naslov


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
    from hub.sifrarnici import ispravci                      # isti redoslijed kao hub.sifrarnici.uvoz: ispravci ureda prije Winstorea (D-51/D-52)
    ispravci.ucitaj_csv(b, ispravci.ZADANI_CSV, "TEST")
    ispravci.primijeni(b, "TEST")
    pantheon.primijeni_zadane_debljine(b, "TEST")
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
    assert s["cpw"]["sigurno"] == s["cpw"]["ukupno"] >= 40   # +3 Corpus materijala iz uzorka (dokument 14)
    assert s["csv"]["sigurno"] >= s["csv"]["ukupno"] - 2            # K2739DC-19: tipfeler u SIFRA MAT; AMBALAZA-19 (ROMIC_Kuhinja, Corpus) nije roba (D-49) — oba ispravno 'za potvrdu'
    assert s["trake"]["sigurno"] >= 44


@stvarni
def test_prihvacanje_winstore(stvarna_baza):
    if "st_winstore" not in stvarna_baza.__dict__:
        pytest.skip("nema Winstore XML")
    st = stvarna_baza.st_winstore
    assert st["kodova"] >= 500 and st["povezano"] + st["rucno"] >= 400        # + ručne veze ureda (D-51)
    assert all(kom >= 0 for _, _, _, kom in st["nepovezano"])   # popis je izvještaj, ne greška
    assert st["ambalaza"] >= 15                                  # ambalažne ploče se ne povezuju (D-49)
