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

SHEMA_VERZIJA = 3

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
