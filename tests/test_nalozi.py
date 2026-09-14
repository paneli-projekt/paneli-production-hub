# -*- coding: utf-8 -*-
"""Testovi koraka 2 — kupci, nalog, materijali, elementi, statusi, uvoz CPW / CSV kroz šifrarnik, API.
Dio A: sintetički šifrarnik (iz test_sifrarnik.py) + mali ph_subjekti.csv + CPW/CSV datoteke u tmp — uvijek.
Dio B: stvarni testni nalozi (HUB_TEST_DATA) — CPW ↔ CSV uvoz istog naloga daje iste elemente; materijali prepoznati."""
import os
import pytest

from hub import db
from hub.sifrarnici import pantheon, aliasi, prepoznaj as P
from hub.nalozi import nalozi as N, kupci as K, uvoz_datoteka as U, provjera as PR
from tests.test_sifrarnik import PH_IDENTI, _Baza

SUBJEKTI = ('"acSubject";"acBuyer";"acSupplier";"acName2";"acAddress";"acPost";"acCountry";"acPIN";"anDaysForPayment";"anRebate";"acActive";"acNaturalPerson"\n'
            '"NAMJEŠTAJ MARIO vl.Mario Humer";"T";"F";"NAMJEŠTAJ MARIO, obrt za usluge";"Zavojane 235";"HR-21275";"Hrvatska";"48435685062";"0";"0.0000";"T";"F"\n'
            '"BOJAN ROMIĆ";"T";"F";"BOJAN ROMIĆ";"MLJETSKA 40";"HR-31000";"Hrvatska";"";"15";"0.0000";"T";"T"\n'
            '"IVERPAN d.o.o.";"F";"T";"IVERPAN d.o.o.";"";"HR-10000";"Hrvatska";"11111111111";"0";"0.0000";"T";"F"\n'
            '"STARI KUPAC";"T";"F";"";"";"";"";"";"0";"0.0000";"F";"F"\n')
POSTE = '"acPost";"acName"\n"HR-21275";"DRAGLJANE"\n"HR-31000";"OSIJEK"\n'

CPW_BIJELI = ("FORMAT;CORPUS->PW;002600;\r\nMATERIJAL;IV BIJELI NK 18MM;18;\r\n"
              "ELEMENT;;820;550;16;A;A;;A;taverna;taverna;;taverna;\r\n"
              "ELEMENT;bok;700;400;2;M;;M;;;;;;\r\n"
              "ELEMENT;polica;600;300;3;;;;;;;;;\r\n")
CPW_BIJELI_2 = "FORMAT;CORPUS->PW;002600;\r\nMATERIJAL;IV BIJELI NK 18MM;18;\r\nELEMENT;;500;500;1;A;A;A;A;;;;;\r\n"
CPW_SIVI = "FORMAT;CORPUS->PW;002600;\r\nMATERIJAL;IV SIVI TAMNI 19mm;19;\r\nELEMENT;;900;450;2;A;A;A;A;;;;;\r\nELEMENT;;300;200;4;;;;;;;;;\r\n"
CSV = ("RB;RN;NAZIV ELEMENTA;BROJ ELE;IME DASKE;KONACNA DIMENZIJA;SIRINA;DUZINA;KOLICINA;SIFRA MAT;MAT DEB;MAT NAZIV;GOD;PROGRAM1;PROGRAM2;OBRADA;"
       "RUB1;TR1SIFRA;RUB2;TRS2IFRA;RUB3;TR3SIFRA;RUB4;TR4SIFRA;LJEPLJENJE;CIX;NAPOMENA;GLODANJE\r\n"
       "1;TEST;;;1_ELEMENT;;550;820;16;W908ST2-18;18;IV_BIJELI_NK_18_MM;0;;;;;1/22 CRNA NK;;;;;;1/22 CRNA NK;;100926_080618;lijevi bok gornji;1\r\n"
       "2;TEST;;;2_ELEMENT;;400;700;2;W908ST2-18;18;IV_BIJELI_NK_18_MM;0;;;;;ABS 0,5/22 BIJELI NK;;;;;;;;100926_080619;;1\r\n"
       "3;TEST;;;3_ELEMENT;;450;900;2;VSM2-18;18;PVC_CRNI_MAT_18;1;;;;;ABS-ISTI;;ABS-ISTI;;;;;;100926_080620;;1\r\n")


@pytest.fixture
def baza(tmp_path):
    (tmp_path / "ph_identi.csv").write_text(PH_IDENTI, encoding="utf-8")
    (tmp_path / "ph_subjekti.csv").write_text(SUBJEKTI, encoding="utf-8")
    (tmp_path / "ph_poste.csv").write_text(POSTE, encoding="utf-8")
    for ime, txt in (("a_bijeli.CPW", CPW_BIJELI), ("b_bijeli2.CPW", CPW_BIJELI_2), ("c_sivi.CPW", CPW_SIVI)):
        (tmp_path / ime).write_bytes(txt.encode("cp1250"))
    (tmp_path / "TEST.CSV").write_text(CSV, encoding="utf-8")
    b = _Baza(db.spoji(str(tmp_path / "hub.db")), dir=tmp_path)
    P.ocisti_kes()
    pantheon.uvezi_pantheon(b, str(tmp_path / "ph_identi.csv"), "TEST")
    aliasi.upisi_potvrdjene(b, "TEST")
    b.execute("UPDATE materijal SET winstore_kod = 'W908ST2-18' WHERE pantheon_ident = 'IV000090'")
    b.execute("UPDATE materijal SET winstore_kod = 'VSM02-18', god = 1 WHERE pantheon_ident = 'IV000671'")
    b.commit()
    P.ocisti_kes()
    K.uvezi_kupce(b, str(tmp_path / "ph_subjekti.csv"), str(tmp_path / "ph_poste.csv"), "TEST")
    yield b
    b.conn.close()
    P.ocisti_kes()


# ------------------------------------------------------------------ kupci
def test_kupci(baza):
    assert baza.execute("SELECT COUNT(*) FROM kupac").fetchone()[0] == 3            # dobavljač (acBuyer = F) preskočen
    k = K.trazi_kupce(baza, "humer")[0]
    assert (k["naziv"], k["mjesto"], k["oib"], k["posta"]) == ("NAMJEŠTAJ MARIO vl.Mario Humer", "DRAGLJANE", "48435685062", "HR-21275")
    assert K.trazi_kupce(baza, "romic")[0]["naziv"] == "BOJAN ROMIĆ"                # bez dijakritike
    assert K.trazi_kupce(baza, "ROMIĆ osijek")[0]["dani_placanja"] == 15
    assert K.trazi_kupce(baza, "stari") == [] and len(K.trazi_kupce(baza, "stari", aktivni=False)) == 1
    K.uredi_kupca(baza, k["id"], "IVANA", email="mario@example.com", rabat_materijal=12, rabat_usluge=18)
    K.uvezi_kupce(baza, str(baza.dir / "ph_subjekti.csv"), None, "TEST")             # ponovni uvoz ne dira Hub-polja
    k2 = K.kupac(baza, k["id"])
    assert (k2["email"], k2["rabat_materijal"], k2["rabat_usluge"]) == ("mario@example.com", 12, 18)
    assert K.kratki_naziv("NAMJEŠTAJ MARIO vl.Mario Humer") == "HUMER" and K.kratki_naziv("BOJAN ROMIĆ") == "ROMIC"
    assert K.kratki_naziv("KL - MONT, vl. Ivan Bogdanić") == "BOGDANIC" and K.kratki_naziv("ADRIA GRUPA d.o.o.") == "ADRIA_GRUPA"


def test_krajnji_kupci(baza):
    """D-48: vrsta kupca i subjekt za Pantheon; kupac otvoren u Hubu; ponavljači."""
    humer, romic = K.trazi_kupce(baza, "humer")[0], K.trazi_kupce(baza, "romic")[0]
    assert (humer["vrsta"], humer["pantheon_subjekt_racun"]) == ("obrt", humer["naziv"])
    assert (romic["vrsta"], romic["oib"], romic["pantheon_subjekt_racun"]) == ("krajnji", None, "Krajnji kupac")   # fizička osoba bez OIB-a
    assert K.vrsta_iz_naziva("KONČAR - KUĆANSKI APARATI d.o.") == "tvrtka" and K.vrsta_iz_naziva("Nenad Pacek", "12345678901") == "krajnji"
    k = K.novi_hub_kupac(baza, "IVANA", "Blago Perković", mjesto="Osijek", telefon="+385 91 234 5678", email="Blago@Example.com")
    assert (k["izvor"], k["vrsta"], k["pantheon_subjekt_racun"], k["rabat_materijal"], k["rabat_usluge"], k["pantheon_subjekt"]) == ("hub", "krajnji", "Krajnji kupac", 0, 0, None)
    assert [r for _, r in K.slicni_kupci(baza, telefon="091/234-5678")] == ["isti telefon"]
    assert [r for _, r in K.slicni_kupci(baza, email="blago@example.com")] == ["isti e-mail"]
    assert [x["naziv"] for x, _ in K.slicni_kupci(baza, ime="Perković Blago")] == ["Blago Perković"]
    assert K.slicni_kupci(baza, ime="Pero Perić", telefon="099 000 0000") == []
    assert K.trazi_kupce(baza, "0912345678")[0]["id"] == k["id"]
    n = N.novi_nalog(baza, "IVANA", kupac_id=k["id"], projekt="kuhinja")
    assert (n["naziv"], n["rabat_materijal"], n["rabat_usluge"], n["kupac_vrsta"], n["kupac_pantheon_subjekt"]) == ("PERKOVIC_KUHINJA_1", 0, 0, "krajnji", "Krajnji kupac")
    k2 = K.uredi_kupca(baza, k["id"], "IVANA", vrsta="obrt", pantheon_subjekt_racun="PERKOVIĆ, vl. Blago Perković", naziv="Blago Perković, obrt")
    assert (k2["vrsta"], k2["pantheon_subjekt_racun"], k2["naziv"]) == ("obrt", "PERKOVIĆ, vl. Blago Perković", "Blago Perković, obrt")
    K.uvezi_kupce(baza, str(baza.dir / "ph_subjekti.csv"), None, "TEST")          # ponovni uvoz ne dira vrstu / subjekt za račun
    assert K.kupac(baza, romic["id"])["pantheon_subjekt_racun"] == "Krajnji kupac" and K.kupac(baza, k["id"])["vrsta"] == "obrt"
    assert K.uredi_kupca(baza, romic["id"], "IVANA", vrsta="krajnji")["pantheon_subjekt_racun"] == "Krajnji kupac"
    with pytest.raises(ValueError):
        K.novi_hub_kupac(baza, "IVANA", "AB")
    # interna baza pod ključem 'Krajnji kupac' + automatsko punjenje kartice kupca na nalogu
    pod = K.trazi_kupce(baza, "", subjekt="Krajnji kupac")
    assert {x["naziv"] for x in pod} == {"BOJAN ROMIĆ"} and {x["naziv"] for x in K.trazi_kupce(baza, "", vrsta="obrt")} == {humer["naziv"], "Blago Perković, obrt"}
    assert K.subjekti_za_pantheon(baza)["krajnji_kupac"] == dict(subjekt="Krajnji kupac", osoba=1)
    n2 = N.nalog(baza, n["id"])
    assert n2["kupac"]["naziv"] == "Blago Perković, obrt" and n2["kupac"]["telefon"] == "+385 91 234 5678" and n2["kupac"]["email"] == "Blago@Example.com"


# ------------------------------------------------------------------ nalog
def test_novi_nalog_broj_i_naziv(baza):
    k = K.trazi_kupce(baza, "humer")[0]
    n1 = N.novi_nalog(baza, "IVANA", kupac_id=k["id"], projekt="Omiš", izvor="kupac_ppw")
    n2 = N.novi_nalog(baza, "GORAN", kupac_kratki="Bratek", projekt="kupac 1")
    assert n1["broj"].endswith("-00001") and n2["broj"].endswith("-00002")
    assert n1["naziv"].endswith("HUMER_OMIS_1") and n2["naziv"] == "BRATEK_KUPAC_1_2"
    assert (n1["status"], n1["izradio"], n1["kerf"], n1["rabat_materijal"], n1["rabat_usluge"]) == ("unos", "IVANA", 16, 15, 20)
    assert n1["kupac_naziv"] == k["naziv"]
    db.postavi(baza, "brojac_naloga_pocetak", "3300")
    n3 = N.novi_nalog(baza, "IVANA", kupac_kratki="X")                             # brojač već postoji → nastavlja se
    assert n3["broj"].endswith("-00003")
    assert [d["u_status"] for d in N.dogadjaji(baza, n1["id"])] == ["unos"]
    with pytest.raises(N.NalogGreska):
        N.novi_nalog(baza, "IVANA", kupac_id=9999)
    assert N.po_nazivu(baza, n2["naziv"]) == n2["id"]


def test_materijali_i_elementi_rucno(baza):
    n = N.novi_nalog(baza, "IVANA", kupac_kratki="TEST")
    mid = baza.execute("SELECT id FROM materijal WHERE pantheon_ident = 'IV000090'").fetchone()[0]
    nm, rez = N.dodaj_materijal(baza, n["id"], "IVANA", materijal_id=mid)
    assert rez is None and nm["ident"] == "IV000090" and nm["traka_zadana"] == "ABS-ISTI" and set(nm["trake"]) == {"0,5/22", "1/22", "2/22"}
    e = N.dodaj_element(baza, nm["id"], "IVANA", 800, 400, 3, rubovi={"L": "ABS-ISTI", "O": "MEL-ISTI", "D": "", "G": "1/22 CRNA NK"}, napomena="lijevi bok gornji dio")
    assert (e["rub1_traka"], e["rub2_traka"], e["rub3_traka"], e["rub4_traka"]) == ("TR000168", "TR000017", None, "TR000100")
    assert e["provjeri"] == 0 and e["napomena_etiketa"] == "lijevi bok gor" and e["m2"] == 0.96
    nm2 = N.uredi_materijal(baza, nm["id"], "IVANA", traka_zadana="ABS-ISTI 2mm")
    e2 = N.dodaj_element(baza, nm["id"], "IVANA", 500, 300, 1, tipovi={"L": "A", "O": "M"})   # CPW: tip bez naziva → zadana oznaka
    assert (e2["rub1_kod"], e2["rub1_traka"], e2["rub2_kod"], e2["rub2_traka"]) == ("ABS-ISTI 2mm", "TR000016", "MEL-ISTI", "TR000017")
    e3 = N.uredi_element(baza, e2["id"], "IVANA", kom=5, rubovi={"L": "MEL CRNA NK"})       # nema 0,5/22 CRNI NK → za potvrdu
    assert e3["kom"] == 5 and e3["provjeri"] == 1 and e3["rub1_traka"] is None
    zp = N.za_potvrdu(baza, n["id"])
    assert [(z["vrsta"], z["tekst"]) for z in zp] == [("traka", "MEL CRNA NK")]
    with pytest.raises(N.NalogGreska):
        N.postavi_status(baza, n["id"], "ponuda", "IVANA")                                      # ima stavke za potvrdu
    tr = baza.execute("SELECT id FROM traka WHERE pantheon_ident = 'TR000100'").fetchone()[0]
    N.potvrdi_traku_naloga(baza, nm["id"], "MEL CRNA NK", tr, "IVANA")
    assert N.element(baza, e2["id"])["rub1_traka"] == "TR000100" and N.broj_za_potvrdu(baza, n["id"]) == 0
    assert baza.execute("SELECT materijal_id FROM traka_alias WHERE alias = 'MEL CRNA NK'").fetchone()[0] is None   # vlastiti dekor → opći alias
    p = N.pregled(baza, n["id"])
    assert p["sazetak"] == dict(materijala=1, elemenata=2, komada=8, m2=round(0.96 + 0.75, 3), za_potvrdu=0)
    N.obrisi_element(baza, e["id"], "IVANA")
    assert N.pregled(baza, n["id"])["sazetak"]["elemenata"] == 1
    with pytest.raises(N.NalogGreska):
        N.dodaj_element(baza, nm["id"], "IVANA", 0, 300, 1)


def test_tok_statusa(baza):
    n = N.novi_nalog(baza, "IVANA", kupac_kratki="TEST")
    N.postavi_status(baza, n["id"], "ponuda", "IVANA", razlog="ponuda v1")
    n = N.postavi_status(baza, n["id"], "potvrdjeno", "GORAN", nacin="telefon", rok_obecan="2026-09-30", prioritet="hitno")
    assert (n["status"], n["potvrda_kupca_nacin"], n["rok_obecan"], n["prioritet"], n["potvrdio"]) == ("potvrdjeno", "telefon", "2026-09-30", "hitno", "GORAN")
    assert n["potvrda_kupca_datum"]
    for s in ("skladiste", "pila_nesting", "proizvodnja", "zatvoren"):
        n = N.postavi_status(baza, n["id"], s, "VP")
    assert n["status"] == "zatvoren"
    with pytest.raises(N.NalogGreska):
        N.postavi_status(baza, n["id"], "unos", "VP")
    d = N.dogadjaji(baza, n["id"])
    assert [(x["iz_statusa"], x["u_status"]) for x in d] == [(None, "unos"), ("unos", "ponuda"), ("ponuda", "potvrdjeno"), ("potvrdjeno", "skladiste"),
                                                             ("skladiste", "pila_nesting"), ("pila_nesting", "proizvodnja"), ("proizvodnja", "zatvoren")]
    assert d[1]["tko"] == "IVANA" and d[1]["razlog"] == "ponuda v1"
    with pytest.raises(N.NalogGreska):
        N.dodaj_materijal(baza, n["id"], "IVANA", naziv_ulaz="IV BIJELI NK 18")         # zatvoren nalog se ne mijenja
    assert N.popis(baza, status="zatvoren")[0]["id"] == n["id"] and N.popis(baza, q="test")[0]["id"] == n["id"]


# ------------------------------------------------------------------ uvoz datoteka
def test_uvoz_cpw(baza):
    n = N.novi_nalog(baza, "IVANA", kupac_kratki="HUMER", projekt="OMIS", izvor="kupac_ppw")
    st = U.uvezi_mapu(baza, n["id"], str(baza.dir), "IVANA", uzorak="*.CPW", izvor="kupac_ppw")
    assert (st["datoteke"], st["materijali_novi"], st["materijali_spojeni"], st["elementi"], st["komada"]) == (3, 2, 1, 6, 28)
    assert st["za_potvrdu_materijal"] == 1                                             # IV SIVI TAMNI 19: MN ili PE
    p = N.pregled(baza, n["id"])
    bij = [m for m in p["materijali"] if m["ident"] == "IV000090"][0]
    assert bij["elemenata"] == 4 and bij["komada"] == 22                              # dvije CPW datoteke istog materijala spojene
    e = bij["elementi"][0]
    assert (e["rub1_kod"], e["rub1_traka"], e["rub3_kod"]) == ("taverna", None, None) and e["provjeri"] == 1   # 'taverna' bez aliasa u sint. bazi
    assert bij["elementi"][1]["rub1_kod"] == "MEL-ISTI" and bij["elementi"][1]["rub1_traka"] == "TR000017"   # tip M bez naziva
    assert bij["elementi"][1]["naziv"] == "bok"
    siv = [m for m in p["materijali"] if m["naziv_ulaz"] == "IV SIVI TAMNI 19mm"][0]
    assert siv["ident"] is None and siv["provjeri"] == 1 and siv["elementi"][0]["provjeri"] == 1
    z = p["za_potvrdu"]
    assert [x["vrsta"] for x in z] == ["materijal", "traka"] and {c["ident"] for c in z[0]["kandidati"]} >= {"IV001168", "IV000027"}
    # potvrda materijala → alias + rubovi elemenata prepoznati
    mid = baza.execute("SELECT id FROM materijal WHERE pantheon_ident = 'IV001168'").fetchone()[0]
    N.potvrdi_materijal_naloga(baza, siv["id"], mid, "IVANA")
    siv2 = N.materijal_naloga(baza, siv["id"])
    assert siv2["ident"] == "IV001168" and siv2["provjeri"] == 0
    assert baza.execute("SELECT izvor FROM materijal_alias WHERE alias = 'IV SIVI TAMNI 19mm'").fetchone()[0] == "nalog"
    e_siv = N.pregled(baza, n["id"])["materijali"][-1]["elementi"][0]
    assert e_siv["rub1_traka"] == "TR000103" and e_siv["provjeri"] == 0                # ABS-ISTI → ABS 1/22 SIVI TAMNI 2162 MN po nazivu
    # potvrda 'taverna' → JELA (u sintetičkoj bazi nema JELA CLAY → koristimo CRNI NK kao primjer)
    tr = baza.execute("SELECT id FROM traka WHERE pantheon_ident = 'TR000100'").fetchone()[0]
    N.potvrdi_traku_naloga(baza, bij["id"], "taverna", tr, "IVANA")
    assert N.broj_za_potvrdu(baza, n["id"]) == 0
    # ista datoteka drugi put se preskače
    st2 = U.uvezi_cpw(baza, n["id"], str(baza.dir / "a_bijeli.CPW"), "IVANA", izvor="kupac_ppw")
    assert st2["preskoceno"] == 1 and N.pregled(baza, n["id"])["sazetak"]["elemenata"] == 6
    assert baza.execute("SELECT COUNT(*) FROM dokument WHERE nalog_id = ?", (n["id"],)).fetchone()[0] == 3
    # export zapis
    ex = N.elementi_za_export(baza, n["id"])
    assert len(ex) == 6 and ex[0]["sifra_mat"] == "W908ST2-18" and ex[0]["mat"] == "IV BIJELI NK 18" and ex[0]["traka"]["L"] == "ABS 1/22 CRNI NK" and ex[0]["tip"]["L"] == "A"
    assert ex[1]["tip"] == {"L": "M", "O": "", "D": "M", "G": ""} and ex[1]["napomena"] == ""


def test_uvoz_ppnest_csv(baza):
    n = N.novi_nalog(baza, "GORAN", kupac_kratki="TEST", izvor="csv")
    st = U.uvezi_ppnest_csv(baza, n["id"], str(baza.dir / "TEST.CSV"), "GORAN")
    assert (st["materijali_novi"], st["elementi"], st["komada"], st["za_potvrdu_materijal"]) == (2, 3, 20, 0)
    p = N.pregled(baza, n["id"])
    m1, m2 = p["materijali"]
    assert m1["ident"] == "IV000090" and m1["winstore_kod_ulaz"] == "W908ST2-18"
    assert m2["ident"] == "IV000671" and m2["god"] == 1 and m2["elementi"][0]["god"] == "H"   # VSM2-18 → VSM02-18 preko Winstore koda; god iz CSV-a
    e1 = m1["elementi"][0]
    assert (e1["L"], e1["W"], e1["kom"], e1["cix_ime"], e1["napomena"]) == (820, 550, 16, "100926_080618", "lijevi bok gornji")
    assert (e1["rub1_kod"], e1["rub1_traka"], e1["rub2_kod"], e1["rub2_traka"], e1["rub4_kod"]) == ("1/22 CRNA NK", "TR000100", "1/22 CRNA NK", "TR000100", None)   # TR1 = lijevo (rub1), TR4 = dolje (rub2)
    assert m1["elementi"][1]["rub1_traka"] == "TR000017"                              # puni naziv trake iz CSV-a
    assert m2["elementi"][0]["provjeri"] == 1                                          # PVC CRNI MAT nema svoju traku u sintetičkom skupu


# ------------------------------------------------------------------ API
def test_api_nalozi(baza, monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    monkeypatch.setenv("HUB_DB", str(baza.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    c = TestClient(A.app)
    try:
        k = c.get("/api/kupci", params=dict(q="humer")).json()["kupci"][0]
        n = c.post("/api/nalozi", json=dict(kupac_id=k["id"], projekt="Omiš", izvor="kupac_ppw", tko="IVANA")).json()
        assert n["naziv"].startswith("HUMER_OMIS_") and n["status"] == "unos"
        with open(baza.dir / "a_bijeli.CPW", "rb") as f:
            r = c.post("/api/nalog/%d/uvoz" % n["id"], params=dict(izvor="kupac_ppw", tko="IVANA"), files={"datoteka": ("a_bijeli.CPW", f, "application/octet-stream")}).json()
        assert r["elementi"] == 3 and r["sazetak"]["komada"] == 21 and [z["tekst"] for z in r["za_potvrdu"]] == ["taverna"]
        assert os.path.exists(os.path.join(str(baza.dir), "ulaz", n["naziv"], "a_bijeli.CPW"))
        p = c.get("/api/nalog/%d" % n["id"]).json()
        nm = p["materijali"][0]
        assert nm["ident"] == "IV000090" and len(nm["elementi"]) == 3
        r = c.post("/api/nalog/materijal/%d/potvrdi-traku" % nm["id"], json=dict(oznaka="taverna", traka="TR000100", tko="IVANA")).json()
        assert r["ok"] and r["za_potvrdu"] == []
        e = c.post("/api/nalog/materijal/%d/elementi" % nm["id"], json=dict(L=600, W=300, kom=2, rubovi={"L": "ABS-ISTI"}, napomena="x", tko="IVANA")).json()
        assert e["rub1_traka"] == "TR000168" and e["rb"] == 4
        assert c.put("/api/nalog/element/%d" % e["id"], json=dict(kom=7, tko="IVANA")).json()["kom"] == 7
        assert c.delete("/api/nalog/element/%d" % e["id"], params=dict(tko="IVANA")).json()["ok"]
        m2 = c.post("/api/nalog/%d/materijali" % n["id"], json=dict(naziv_ulaz="IV SIVI TAMNI 19mm", tko="IVANA")).json()
        assert m2["provjeri"] == 1 and m2["prepoznavanje"]["razina"] == "za_potvrdu"
        assert c.post("/api/nalog/materijal/%d/potvrdi" % m2["id"], json=dict(ident="IV001168", tko="IVANA")).json()["ident"] == "IV001168"
        assert c.post("/api/nalog/%d/status" % n["id"], json=dict(status="ponuda", tko="IVANA")).json()["status"] == "ponuda"
        r = c.post("/api/nalog/%d/status" % n["id"], json=dict(status="potvrdjeno", tko="GORAN", nacin="mail", rok_obecan="2026-10-01")).json()
        assert r["rok_obecan"] == "2026-10-01" and r["potvrdio"] == "GORAN"
        assert c.post("/api/nalog/%d/status" % n["id"], json=dict(status="zatvoren", tko="GORAN")).status_code == 400
        lst = c.get("/api/nalozi", params=dict(status="potvrdjeno")).json()
        assert lst["nalozi"][0]["id"] == n["id"] and lst["nalozi"][0]["elemenata"] == 3 and len(lst["statusi"]) == 7
        assert c.get("/api/kupci/%d" % k["id"]).json()["nalozi"][0]["id"] == n["id"]
        assert c.put("/api/kupci/%d" % k["id"], json=dict(email="a@b.hr", tko="IVANA")).json()["email"] == "a@b.hr"
        r = c.post("/api/kupci", json=dict(ime="Ana Anić", telefon="098 111 222", mjesto="Đakovo", tko="IVANA"))
        assert r.status_code == 200 and r.json()["pantheon_subjekt_racun"] == "Krajnji kupac"
        r2 = c.post("/api/kupci", json=dict(ime="Anić Ana", telefon="+385 98 111 222", tko="IVANA"))
        assert r2.status_code == 409 and r2.json()["detail"]["slicni"][0]["razlog"] == "isti telefon"
        assert c.get("/api/kupci/slicni", params=dict(ime="ana anić")).json()["slicni"][0]["id"] == r.json()["id"]
        assert [x["naziv"] for x in c.get("/api/kupci", params=dict(q="anic djakovo")).json()["kupci"]] == ["Ana Anić"]
        assert {x["naziv"] for x in c.get("/api/kupci", params=dict(subjekt="Krajnji kupac")).json()["kupci"]} == {"BOJAN ROMIĆ", "Ana Anić"}
        assert c.get("/api/kupci/kljucevi").json()["krajnji_kupac"]["osoba"] == 2
        assert c.get("/api/nalog/%d" % n["id"]).json()["kupac"]["mjesto"] == "DRAGLJANE"
        assert len(c.get("/api/nalog/%d/elementi-export" % n["id"]).json()) == 3
        assert c.get("/api/nalog/9999").status_code == 400
        z = c.get("/api/zdravlje").json()
        assert z["kupaca"] == 4 and z["naloga"] == 1              # 3 iz Pantheona + Ana Anić otvorena u Hubu
    finally:
        c.close()
        A._veza = None
        P.ocisti_kes()


# ------------------------------------------------------------------ B. stvarni testni nalozi
from tests.test_sifrarnik import DATA, PH_CSV, WIN_XML, stvarni, stvarna_baza   # noqa: E402,F401


@stvarni
def test_prihvacanje_uvoz_naloga(stvarna_baza):
    rez = PR.provjeri(stvarna_baza, DATA)
    s = PR.sazetak(rez)
    assert s["naloga"] == 9 and s["usporedivo"] == 8 and s["slaze_se"] >= 7    # MAZUR: CSV materijal za potvrdu zbog tipfelera 'K2739DC-19'
    assert s["materijala_sigurno"] >= s["materijala"] - 1                   # jedini nesigurni: isti MAZUR CSV materijal
    assert s["elemenata"] >= 990 and s["komada"] >= 2200
    bratek = [r for r in rez if r["mapa"] == "_BRATEK_KUPAC1"][0]
    assert bratek["cpw"]["sazetak"]["komada"] == 108 and bratek["cpw"]["uvoz"]["preskocene_starije"]   # stariji izvoz istog materijala preskočen (65 kom kao u CPO-u)
    humer = [r for r in rez if r["mapa"] == "_HUMER_OMIS"][0]
    assert humer["kupac"]["sazetak"] == dict(materijala=5, elemenata=121, komada=278, m2=98.534, za_potvrdu=0)
    assert all(z["vrsta"] == "traka" or z["tekst"] == "IV_HR_CREMONA_CANNOLO_19" for r in rez for k in ("cpw", "csv", "kupac") if r[k] for z in r[k]["za_potvrdu"])
    PR.obrisi_provjere(stvarna_baza)
