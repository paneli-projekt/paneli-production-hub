# -*- coding: utf-8 -*-
"""Restlovi (Warehouse, D-64): uvoz evidencije RESTLOVI_V7.xlsm, vezanje dekora na ident kroz šifrarnik, potvrda, stanje, migracija v12.

Dio A — sintetički Excel + mali šifrarnik (uvijek). Dio B — stvarna evidencija `20_ANALIZA\\RESTLOVI_V7.xlsm` (HUB_TEST_DATA):
1 363 restla / 429 dekora — najmanje 85 % dekora vezano sigurno, sve što Excel ima kao TOČNO Hub veže na ISTI ident."""
import os
import sqlite3
import pytest

from hub import db
from hub.sifrarnici import prepoznaj as P
from hub.sifrarnici import pantheon, aliasi, ispravci
from hub.skladiste import restlovi as R

openpyxl = pytest.importorskip("openpyxl")

PH = """acIdent;acName;acClassif;acCode;acSupplier;acUM;anSalePrice;anRTPrice;anVAT;acActive
IV000090;IVERAL BIJELI NK W908 ST2 18 MM;;;;M2;25;20;25;T
IV000872;IVERAL ORAH STRIPE EARTH K2341 AN 19 mm;;;;M2;30;24;25;T
IV000171;IVERAL HRAST SONOMA 3025 SN 18MM;;;;M2;30;24;25;T
IV000351;IVERAL HRAST SONOMA 3025 SN 25MM;;;;M2;30;24;25;T
IV000187;IVERAL RIGOLETO BRONZA 18MM;;;;M2;30;24;25;T
IV000013;IVERAL JAVOR MURNAU 19MM 3306 BS;;;;M2;30;24;25;T
IV000276;IVERAL JAVOR 0375 BS 18MM;;;;M2;30;24;25;T
TR000017;ABS 0,5/22 BIJELI NK;;;;M;0,2;0,16;25;T
"""

REDOVI = [  # ID, Grupa, Ident, Naziv, Duljina, Širina, Kom, Lokacija, Status, M2, Nalog, Datum, Napomena, STARI OPIS
    ("R0001", "DRVNI DEKOR", None, None, 2800, 1340, 1, "A003", "NA SKLADIŠTU", 3.752, None, None, None, "IV RIGOLETO BRONZA"),
    ("R0002", "DRVNI DEKOR", "IV000872", "IVERAL ORAH…", 2800, 515, 1, "A003", "NA SKLADIŠTU", 1.442, None, None, None, "IV ORAH STRIPE EARTH K2341AN"),
    ("R0003", "DRVNI DEKOR", "IV000872", "IVERAL ORAH…", 2195, 1200, 1, "B004", "PROVJERI", 2.634, None, None, "IZGREBANO PROVJERITI", "IV ORAH STRIPE EARTH K2341AN"),
    ("R0004", "IV BIJELI", "IV000090", "IVERAL BIJELI…", 1000, 500, 2, "SATOR C 3.1", "NA SKLADIŠTU", 1.0, None, None, "VISE MJERA", "IV BIJELI NK 18MM"),
    ("R0005", "DRVNI DEKOR", "IV000171", None, 600, 400, 1, "B001", "NA SKLADIŠTU", 0.24, None, None, None, "IV HR SONOMA GOMOLJASTI"),
    ("R0006", "DRVNI DEKOR", None, None, 700, 300, 1, "B001", "NA SKLADIŠTU", 0.21, None, None, None, "IV JAVOR (KRONO)"),
    ("R0007", "DEKORI RAZNI", None, None, 500, 300, 1, None, "NA SKLADIŠTU", 0.15, None, None, None, "(FRANJIC)"),
    ("R0008", "DRVNI DEKOR", "IV000276", None, 800, 300, 1, "B002", "PRODAN", 0.24, "HUMER_OMIS_3", None, None, "IV JAVOR (KRONO)"),
    ("R0009", "DRVNI DEKOR", None, None, None, 300, 1, "B002", "NA SKLADIŠTU", None, None, None, None, "IV BIJELI NK 18MM"),   # bez mjere → preskočeno
]
MAPIRANJE = [  # Dekor, Grupa, Ident, Naziv, Cijena, Status
    ("IV ORAH STRIPE EARTH K2341AN", "DRVNI DEKOR", "IV000872", "IVERAL ORAH…", 30, "TOČNO ✓✓"),
    ("IV BIJELI NK 18MM", "IV BIJELI", "IV000090", "IVERAL BIJELI…", 25, "TOČNO ✓✓ (ispravljeno)"),
    ("IV HR SONOMA GOMOLJASTI", "DRVNI DEKOR", "IV000171", "IVERAL HRAST SONOMA", 30, "PROVJERI"),
    ("IV JAVOR (KRONO)", "DRVNI DEKOR", "IV000013", "IVERAL JAVOR MURNAU", 30, "PROVJERI"),
    ("(FRANJIC)", "DEKORI RAZNI", None, "artikl ne postoji", None, "NEMA U CJENIKU"),
]


def _xlsm(putanja, redovi=REDOVI, mapiranje=MAPIRANJE):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RESTLOVI"
    ws.append(["ID", "Grupa", "Ident", "Naziv artikla (auto)", "Duljina", "Širina", "Kom", "Lokacija", "Status", "M2", "Nalog (izlaz)", "Datum",
               "Napomena", "STARI OPIS", "Odabir po nazivu (pomoćno)", "Kontrola", "Auto-map (info)"])
    for r in redovi:
        ws.append(list(r))
    m = wb.create_sheet("MAPIRANJE DEKORA")
    m.append(["Dekor (iz tablice)", "Grupa", "Ident Pantheon", "Naziv u Pantheonu", "Cijena (EUR)", "Status", "Ispravak", "ili upiši ident", "Ident konačni"])
    for r in mapiranje:
        m.append(list(r))
    wb.save(putanja)
    return str(putanja)


@pytest.fixture
def baza(tmp_path):
    csv_p = tmp_path / "ph_identi.csv"
    csv_p.write_text(PH, encoding="utf-8-sig")
    conn = db.spoji(str(tmp_path / "hub.db"))
    P.ocisti_kes()
    pantheon.uvezi_pantheon(conn, str(csv_p), "TEST")
    yield conn
    conn.close()
    P.ocisti_kes()


# ------------------------------------------------------------------ A. sintetički
def test_ucitaj_xlsm(tmp_path):
    x = R.ucitaj_xlsm(_xlsm(tmp_path / "r.xlsx"))
    assert len(x["restlovi"]) == 8 and x["upozorenja"] and "R0009" in x["upozorenja"][0]
    r = x["restlovi"][2]
    assert r["oznaka"] == "R0003" and r["status"] == "provjeri" and r["napomena"] == "IZGREBANO PROVJERITI" and r["dekor"] == "IV ORAH STRIPE EARTH K2341AN"
    assert x["restlovi"][7]["status"] == "potrosen" and x["restlovi"][7]["nalog_izlaz"] == "HUMER_OMIS_3"
    assert x["mapiranje"]["IV BIJELI NK 18MM"] == ("IV000090", "TOČNO ✓✓ (ispravljeno)")


def test_uvoz_veze_dekore_kroz_sifrarnik(baza, tmp_path):
    iz = R.uvezi_excel(baza, _xlsm(tmp_path / "r.xlsx"), "TEST")
    assert iz["restlova"] == 8 and iz["dekora"] == 6 and iz["novo"] == 8
    po = {r["oznaka"]: dict(r) for r in baza.execute("SELECT * FROM restl")}
    # šifrarnik po nazivu (jedini RIGOLETO BRONZA) — Excel nema ident → sigurno
    assert po["R0001"]["razina"] == "naziv" and po["R0001"]["provjeri"] == 0 and po["R0001"]["materijal_id"]
    # kod dekora K2341AN → sigurno, isti kao Excel TOČNO
    assert po["R0002"]["razina"] == "naziv" and po["R0002"]["ident_ulaz"] == "IV000872"
    assert po["R0003"]["status"] == "provjeri" and po["R0004"]["kom"] == 2 and po["R0004"]["lokacija"] == "SATOR C 3.1"
    # dva identa iste riječi (SONOMA 18 / 25), debljine nema → za potvrdu; Excelov PROVJERI ident je među kandidatima
    assert po["R0005"]["provjeri"] == 1 and po["R0005"]["razina"] == "za_potvrdu" and po["R0005"]["materijal_id"] is None
    assert "IV000171" in po["R0005"]["kandidati_json"]
    # JAVOR (KRONO): dva javora → za potvrdu, oba retka (i prodani)
    assert po["R0006"]["provjeri"] == 1 and po["R0008"]["provjeri"] == 1 and po["R0008"]["status"] == "potrosen"
    # (FRANJIC): ništa
    assert po["R0007"]["razina"] == "nema" and po["R0007"]["provjeri"] == 1
    assert iz["po_dekoru"] == {"sigurno": 3, "za_potvrdu": 2, "nema": 1}
    assert iz["po_restlu"] == {"sigurno": 4, "za_potvrdu": 3, "nema": 1}
    assert iz["excel_slaganje"]["isti"] == 2 and iz["excel_slaganje"]["razlicit"] == 0
    md = R.izvjestaj_md(iz)
    assert "IV JAVOR (KRONO)" in md and "Za potvrdu (3 dekora)" in md
    # stanje: samo vezani i na stanju (R0003 'provjeri' se broji, R0008 prodan ne, R0005/6/7 nevezani ne)
    st = {o["ident"]: o for o in R.stanje(baza)}
    assert set(st) == {"IV000187", "IV000872", "IV000090"}
    assert st["IV000872"]["kom"] == 2 and st["IV000872"]["m2"] == round(2800 * 515 / 1e6 + 2195 * 1200 / 1e6, 3)
    assert st["IV000090"]["kom"] == 2 and st["IV000090"]["m2"] == 1.0
    assert [o["ident"] for o in R.stanje(baza, samo_slobodni=True, ident="IV000872")][0] == "IV000872"
    assert R.stanje(baza, samo_slobodni=True, ident="IV000872")[0]["kom"] == 1
    assert R.lokacija(baza, "R0004") == "SATOR C 3.1" and R.lokacija(baza, "R0099") is None
    s = R.sazetak(baza)
    assert s["ukupno"] == 8 and s["za_potvrdu"] == 4 and s["dekora_za_potvrdu"] == 3 and s["po_statusu"]["potrosen"] == 1


def test_potvrda_dekora_postaje_alias(baza, tmp_path):
    p = _xlsm(tmp_path / "r.xlsx")
    R.uvezi_excel(baza, p, "TEST")
    n = R.potvrdi_dekor(baza, "IV JAVOR (KRONO)", "IV000013", "IVANA")
    assert n == 2
    assert baza.execute("SELECT COUNT(*) FROM restl WHERE dekor_ulaz = 'IV JAVOR (KRONO)' AND provjeri = 0 AND razina = 'potvrda'").fetchone()[0] == 2
    assert P.prepoznaj_materijal(baza, "IV JAVOR (KRONO)").razina == "alias"
    # ponovni uvoz: potvrđeno ostaje (alias sada veže sigurno), ostalo se osvježi bez dupliciranja
    iz = R.uvezi_excel(baza, p, "TEST")
    assert iz["novo"] == 0 and iz["osvjezeno"] == 8 and baza.execute("SELECT COUNT(*) FROM restl").fetchone()[0] == 8
    assert baza.execute("SELECT razina FROM restl WHERE oznaka = 'R0006'").fetchone()[0] == "alias"
    with pytest.raises(ValueError):
        R.potvrdi_dekor(baza, "(FRANJIC)", "IV999999", "IVANA")


def test_ponovni_uvoz_ne_dira_potvrdjene_u_hubu(baza, tmp_path):
    p = _xlsm(tmp_path / "r.xlsx")
    R.uvezi_excel(baza, p, "TEST")
    baza.execute("UPDATE restl SET lokacija = 'C009', potvrdio = 'SKLADISTAR', potvrdjeno = '2026-09-17' WHERE oznaka = 'R0002'")
    baza.execute("INSERT INTO restl (oznaka, materijal_id, L, W, kom, status, izvor, kada) VALUES ('R9001', 1, 500, 500, 1, 'prijedlog', 'prijedlog', 'x')")
    baza.commit()
    iz = R.uvezi_excel(baza, p, "TEST")
    assert iz["zadrzano"] == 1 and iz["osvjezeno"] == 7
    assert baza.execute("SELECT lokacija FROM restl WHERE oznaka = 'R0002'").fetchone()[0] == "C009"
    assert baza.execute("SELECT COUNT(*) FROM restl WHERE oznaka = 'R9001' AND status = 'prijedlog'").fetchone()[0] == 1
    assert all(o["ident"] != "x" for o in R.stanje(baza))       # prijedlog nije na stanju


def test_migracija_v12_stara_baza(tmp_path):
    """Baza v11 (stari restl bez oznake, ploca_stanje, rezervacija.ploca_stanje_id) → v12 bez greške i bez ploca_stanje."""
    p = str(tmp_path / "stara.db")
    db.spoji(p).close()
    c = sqlite3.connect(p)
    c.executescript("""
        DELETE FROM shema_verzija WHERE verzija >= 12;
        DROP TABLE rezervacija; DROP TABLE restl;
        CREATE TABLE ploca_stanje (id INTEGER PRIMARY KEY, materijal_id INTEGER NOT NULL REFERENCES materijal (id), lokacija TEXT, kom INTEGER NOT NULL DEFAULT 0, zadnja_inventura TEXT);
        CREATE TABLE restl (id INTEGER PRIMARY KEY, materijal_id INTEGER NOT NULL REFERENCES materijal (id), L REAL NOT NULL, W REAL NOT NULL,
            lokacija TEXT, qr TEXT, izvor TEXT, status TEXT NOT NULL DEFAULT 'slobodan', datum TEXT);
        CREATE TABLE rezervacija (id INTEGER PRIMARY KEY, nalog_materijal_id INTEGER NOT NULL REFERENCES nalog_materijal (id),
            restl_id INTEGER REFERENCES restl (id), ploca_stanje_id INTEGER REFERENCES ploca_stanje (id), winstore_kod TEXT, kom REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'rezervirano', datum TEXT NOT NULL, korisnik_id INTEGER REFERENCES korisnik (id),
            izdao_id INTEGER REFERENCES korisnik (id), izdano_kada TEXT);
    """)
    c.commit(); c.close()
    conn = db.spoji(p)
    tablice = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert "ploca_stanje" not in tablice and "restl__staro" not in tablice and "rezervacija__staro" not in tablice
    stupci = {r[1] for r in conn.execute("PRAGMA table_info(restl)")}
    assert {"oznaka", "dekor_ulaz", "razina", "kandidati_json", "provjeri", "potvrdio"} <= stupci
    assert "ploca_stanje_id" not in {r[1] for r in conn.execute("PRAGMA table_info(rezervacija)")}
    assert conn.execute("SELECT MAX(verzija) FROM shema_verzija").fetchone()[0] == db.SHEMA_VERZIJA
    conn.execute("INSERT INTO restl (oznaka, L, W, kom, status, izvor, kada) VALUES ('R0001', 1, 1, 1, 'slobodan', 'excel_v7', 'x')")
    conn.close()


# ------------------------------------------------------------------ B. stvarna evidencija
DATA = os.environ.get("HUB_TEST_DATA")
HUB = os.path.dirname(DATA.rstrip("\\/")) if DATA else None
PH_CSV = os.path.join(os.path.dirname(HUB), "ph_identi.csv") if HUB else None
XLSM = os.path.join(HUB, "20_ANALIZA", "RESTLOVI_V7.xlsm") if HUB else None
stvarni = pytest.mark.skipif(not DATA or not PH_CSV or not os.path.exists(PH_CSV) or not XLSM or not os.path.exists(XLSM),
                             reason="HUB_TEST_DATA nije postavljen ili nema ph_identi.csv / RESTLOVI_V7.xlsm")


@stvarni
def test_stvarna_evidencija_restlova(tmp_path):
    conn = db.spoji(str(tmp_path / "hub.db"))
    P.ocisti_kes()
    pantheon.uvezi_pantheon(conn, PH_CSV, "TEST")
    from hub.sifrarnici.uvoz import ALIAS_ZADANI
    aliasi.uvezi_alias_csv(conn, ALIAS_ZADANI, "TEST")
    ispravci.ucitaj_csv(conn, ispravci.ZADANI_CSV, "TEST")
    ispravci.primijeni(conn, "TEST")
    pantheon.primijeni_zadane_debljine(conn, "TEST")
    aliasi.upisi_potvrdjene(conn, "TEST")
    iz = R.uvezi_excel(conn, XLSM, "TEST")
    assert iz["restlova"] >= 1300 and iz["dekora"] >= 400
    d = iz["po_dekoru"]
    assert d["sigurno"] >= 0.85 * iz["dekora"], d                       # 372 / 429 (16. 9.)
    assert iz["po_restlu"]["sigurno"] >= 0.88 * iz["restlova"]          # 1 223 / 1 363
    assert iz["excel_slaganje"]["razlicit"] == 0                        # nijedan Excelov TOČNO ident nije vezan drukčije
    assert iz["excel_slaganje"]["isti"] >= 360
    assert not iz["m2_razlika"]                                         # m² iz mjera = Excelov M2
    assert conn.execute("SELECT COUNT(*) FROM restl WHERE provjeri = 0 AND materijal_id IS NULL").fetchone()[0] == 0
    st = R.stanje(conn)
    assert sum(o["m2"] for o in st) > 1300                              # 1 226 restlova NA SKLADIŠTU ≈ 1 540 m²
    # ponovni uvoz iste datoteke: ništa novo, ništa duplo
    iz2 = R.uvezi_excel(conn, XLSM, "TEST")
    assert iz2["novo"] == 0 and conn.execute("SELECT COUNT(*) FROM restl").fetchone()[0] == iz["restlova"]
    conn.close()
    P.ocisti_kes()
