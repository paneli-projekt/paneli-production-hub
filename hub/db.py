# -*- coding: utf-8 -*-
"""Baza Huba: SQLite (04 §3), jedna datoteka, shema iz hub/schema.sql.

    from hub import db
    conn = db.spoji("hub.db")      # otvori (ili stvori) bazu i primijeni shemu
    db.dnevnik(conn, "IGOR", "materijal", "12", "uvoz")

Putanja baze: argument, inače varijabla okoline HUB_DB, inače ./hub.db.
"""
import os
import sqlite3
from datetime import datetime

SHEMA_VERZIJA = 17

# Migracije starijih baza (verzija → popis SQL naredbi); 'duplicate column' se preskače (svježa baza već ima stupce iz schema.sql).
MIGRACIJE = {
    2: [
        "ALTER TABLE kupac ADD COLUMN naziv_puni TEXT", "ALTER TABLE kupac ADD COLUMN adresa TEXT", "ALTER TABLE kupac ADD COLUMN posta TEXT",
        "ALTER TABLE kupac ADD COLUMN mjesto TEXT", "ALTER TABLE kupac ADD COLUMN drzava TEXT", "ALTER TABLE kupac ADD COLUMN oib TEXT",
        "ALTER TABLE kupac ADD COLUMN fizicka_osoba INTEGER NOT NULL DEFAULT 0", "ALTER TABLE kupac ADD COLUMN pantheon_azurirano TEXT",
        "ALTER TABLE kupac ADD COLUMN trazi TEXT",
        "ALTER TABLE materijal ADD COLUMN trazi TEXT", "ALTER TABLE traka ADD COLUMN trazi TEXT",
        "REBUILD nalog_materijal",     # materijal_id postaje NULL-abilan + naziv_ulaz, debljina_ulaz, winstore_kod_ulaz, provjeri, traka_zadana, rb
    ],
    3: [
        "ALTER TABLE kupac ADD COLUMN izvor TEXT NOT NULL DEFAULT 'pantheon'", "ALTER TABLE kupac ADD COLUMN vrsta TEXT",
        "ALTER TABLE kupac ADD COLUMN pantheon_subjekt_racun TEXT",
    ],
    4: [
        "ALTER TABLE winstore_ploca ADD COLUMN ambalaza INTEGER NOT NULL DEFAULT 0",
    ],
    5: [                                # sifrarnik_ispravak nastaje iz schema.sql (CREATE IF NOT EXISTS)
        "ALTER TABLE materijal ADD COLUMN debljina_rucno REAL",
        "ALTER TABLE materijal ADD COLUMN ne_koristi_se INTEGER NOT NULL DEFAULT 0",
    ],
    6: [
        "ALTER TABLE materijal ADD COLUMN debljina_izvor TEXT",
        "UPDATE materijal SET debljina_izvor = 'naziv' WHERE debljina IS NOT NULL AND debljina_izvor IS NULL",
    ],
    7: [                                # cix_registar nastaje iz schema.sql; postojeća imena elemenata se upisuju u njega
        "INSERT OR IGNORE INTO cix_registar (ime, element_id, nalog_id, izvor, kada) "
        "SELECT e.cix_ime, e.id, nm.nalog_id, COALESCE(e.cix_izvor, 'hub'), datetime('now') "
        "FROM element e JOIN nalog_materijal nm ON nm.id = e.nalog_materijal_id WHERE e.cix_ime IS NOT NULL AND e.cix_ime <> ''",
    ],
    8: [                                # prolaza iz PPNEST CSV-a; brojač naloga koji su potrošile probe se briše dok nema stvarnih naloga (D-47)
        "ALTER TABLE element ADD COLUMN prolaza INTEGER",
        "DELETE FROM postavke WHERE kljuc GLOB 'brojac_naloga_[0-9]*' AND NOT EXISTS (SELECT 1 FROM nalog WHERE broj NOT LIKE 'PROV-%')",
    ],
    9: [],                              # spojeni_posao + spojeni_posao_stavka nastaju iz schema.sql (CREATE IF NOT EXISTS), D-54/B
    10: ["ALTER TABLE optimizacija ADD COLUMN %s" % c for c in           # potvrda i snimka slaganja, D-75
         ("status TEXT", "nacin_trazen TEXT", "dubina TEXT", "slaganje_json TEXT", "elementi_hash TEXT", "kerf REAL", "obrez REAL",
          "potvrdio_id INTEGER REFERENCES korisnik (id)", "potvrdjeno TEXT", "napomena TEXT")],
    11: ["ALTER TABLE element ADD COLUMN %s" % c for c in            # mjera za rezanje + majka (korak 6: D-70, D-79, D-80); tablica majka iz schema.sql
         ("rez_L REAL", "rez_W REAL", "rez_razlog TEXT", "vrsta TEXT NOT NULL DEFAULT 'element'", "majka_id INTEGER REFERENCES majka (id)",
          "majka_poz TEXT", "niz TEXT", "napomena_rez TEXT")],
    12: [                               # Warehouse (D-64): restl po RESTLOVI_V7.xlsm (oznaka, dekor, razina, kandidati…), rezervacija bez ploca_stanje_id
        "REBUILD rezervacija", "REBUILD restl", "DROP TABLE IF EXISTS ploca_stanje",
    ],
    13: [                               # nabava (D-42/5): tablica dobavljac iz schema.sql; narudžbenica pamti adresu i PDF
        "ALTER TABLE narudzbenica ADD COLUMN poslano_na TEXT", "ALTER TABLE narudzbenica ADD COLUMN put_pdf TEXT",
    ],
    14: [                               # ručne stavke ponude (D-87) i korisnici s lozinkom (D-88): tablice rucna_stavka, sesija iz schema.sql
        "ALTER TABLE korisnik ADD COLUMN lozinka_hash TEXT", "ALTER TABLE korisnik ADD COLUMN email TEXT", "ALTER TABLE korisnik ADD COLUMN telefon TEXT",
        "ALTER TABLE korisnik ADD COLUMN funkcija TEXT", "ALTER TABLE korisnik ADD COLUMN potpis TEXT",
    ],
    15: [                               # ponuda kao Pantheon (D-90): napomena na dokumentu, korekcije izračunatih stavki (tablica iz schema.sql)
        "ALTER TABLE nalog ADD COLUMN napomena_ponude TEXT",
    ],
    16: [                               # D-90: zbroji iste idente u ponudi; mape izvoza kao postavke (seed iz schema.sql)
        "ALTER TABLE nalog ADD COLUMN zbroji_idente INTEGER NOT NULL DEFAULT 0",
    ],
    17: [                               # obrub (rubljenje) ploče po materijalu naloga (Igor, 17. 9.); NULL = zadano
        "ALTER TABLE nalog_materijal ADD COLUMN obrub REAL",
    ],
}
OVDJE = os.path.dirname(os.path.abspath(__file__))


def sada():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def putanja_baze(putanja=None):
    return putanja or os.environ.get("HUB_DB") or os.path.join(os.getcwd(), "hub.db")


def spoji(putanja=None):
    """Otvori bazu, uključi foreign keys, primijeni shemu ako treba. Redovi se vraćaju kao sqlite3.Row."""
    conn = sqlite3.connect(putanja_baze(putanja))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    init(conn)
    return conn


def init(conn):
    """Primijeni schema.sql (CREATE IF NOT EXISTS) i migracije za baze starije verzije."""
    with open(os.path.join(OVDJE, "schema.sql"), encoding="utf-8") as f:
        shema = f.read()
    postojala = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'shema_verzija'").fetchone()[0]
    v = conn.execute("SELECT MAX(verzija) FROM shema_verzija").fetchone()[0] if postojala else None
    conn.executescript(shema)
    if v is None:
        v = 0 if postojala else SHEMA_VERZIJA      # svježa baza = već zadnja verzija; stara baza bez zapisa = verzija 0
    for nova in range(v + 1, SHEMA_VERZIJA + 1):
        for sql in MIGRACIJE.get(nova, []):
            if sql.startswith("REBUILD "):
                _rebuild(conn, sql.split()[1], shema)
                continue
            try:
                conn.execute(sql)
            except sqlite3.OperationalError as e:
                if "duplicate column" not in str(e):
                    raise
        conn.execute("INSERT OR IGNORE INTO shema_verzija (verzija, primijenjeno) VALUES (?, ?)", (nova, sada()))
    conn.execute("INSERT OR IGNORE INTO shema_verzija (verzija, primijenjeno) VALUES (?, ?)", (SHEMA_VERZIJA, sada()))
    conn.commit()


def _rebuild(conn, tablica, shema):
    """Ponovno stvori tablicu po aktualnoj definiciji iz schema.sql i prenese zajedničke stupce (SQLite ne mijenja NOT NULL)."""
    import re
    m = re.search(r"CREATE TABLE IF NOT EXISTS %s \(.*?\n\);" % tablica, shema, re.S)
    if not m:
        raise RuntimeError("nema definicije tablice %s u schema.sql" % tablica)
    stari = [r[1] for r in conn.execute("PRAGMA table_info(%s)" % tablica)]
    conn.commit()
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("PRAGMA legacy_alter_table = ON")     # da RENAME ne prepiše reference u drugim tablicama (element → nalog_materijal)
    try:
        conn.execute("ALTER TABLE %s RENAME TO %s__staro" % (tablica, tablica))
        conn.executescript(m.group(0))
        novi = [r[1] for r in conn.execute("PRAGMA table_info(%s)" % tablica)]
        zajednicki = ", ".join(c for c in novi if c in stari)
        conn.execute("INSERT INTO %s (%s) SELECT %s FROM %s__staro" % (tablica, zajednicki, zajednicki, tablica))
        conn.execute("DROP TABLE %s__staro" % tablica)
        conn.commit()
    finally:
        conn.execute("PRAGMA legacy_alter_table = OFF")
        conn.execute("PRAGMA foreign_keys = ON")


def dnevnik(conn, tko, entitet, id_entiteta, sto, detalji=None):
    conn.execute("INSERT INTO dnevnik (kada, tko, entitet, id_entiteta, sto, detalji) VALUES (?, ?, ?, ?, ?, ?)",
                 (sada(), tko, entitet, str(id_entiteta) if id_entiteta is not None else None, sto, detalji))


def postavka(conn, kljuc, zadano=None):
    r = conn.execute("SELECT vrijednost FROM postavke WHERE kljuc = ?", (kljuc,)).fetchone()
    return r[0] if r else zadano


def postavi(conn, kljuc, vrijednost, opis=None):
    conn.execute("INSERT INTO postavke (kljuc, vrijednost, opis) VALUES (?, ?, ?) "
                 "ON CONFLICT(kljuc) DO UPDATE SET vrijednost = excluded.vrijednost, opis = COALESCE(excluded.opis, postavke.opis)",
                 (kljuc, vrijednost, opis))
