# -*- coding: utf-8 -*-
"""Početno punjenje alias-tablica i zadanih traka.

- alias.csv iz skilla krojna-ponuda (pw_naziv,ident — 369 ručno provjerenih parova, kolovoz 2026, D-07): IV/RP identi → materijal_alias,
  TR identi → traka_alias (opći, bez materijala).
- ZADANE_TRAKE: parovi (materijal, klasa → traka) potvrđeni na stvarnim ponudama (06 §5, D-31) koje se po nazivu ne mogu naći
  (npr. JELA TAVERNA → ABS 1/22 JELA CLAY: dobavljač traku zove drukčije nego ploču).
- izvedi_zadane_trake(): za svaki materijal pokuša po nazivu naći trake 0,5/22, 1/22 i 2/22 istog dekora i upiše ih kao zadane
  (izvor 'naziv'); ne prepisuje one koje je čovjek potvrdio.
"""
import csv

from ..db import sada, dnevnik
from .nazivi import norm, rijeci, kodovi
from . import prepoznaj as P

# (Pantheon ident materijala, klasa, ident trake, izvor) — potvrđeno u ponudama (06 §5: HUMER 26-010-002823)
ZADANE_TRAKE = [
    ("IV001210", "1/22", "TR001254", "ponuda 26-010-002823"),   # IVERAL JELA TAVERNA K2665 AI 19MM → ABS 1/22 JELA CLAY
    ("IV001210", "1/44", "TR001258", "ponuda 26-010-002823"),   # → ABS 1/44 JELA CLAY
    ("IV001219", "1/22", "TR001213", "ponuda 26-010-002823"),   # IVERAL HRAST RELIEF CARDAMOM K2776 GR → ABS 1/22 HRAST RELIEF PIMENTO
    ("IV000090", "0,5/22", "TR000017", "ponuda 26-010-002823"), # IVERAL BIJELI NK W908 ST2 18 MM → ABS 0,5/22 BIJELI NK (MEL-ISTI)
    ("IV000090", "1/22", "TR000168", "D-31"),                   # → ABS 1/22 BIJELI NK (ABS-ISTI)
    ("IV000090", "2/22", "TR000016", "D-31"),                   # → ABS 2/22 BIJELI NK (ABS-ISTI 2mm)
]

# aliasi materijala potvrđeni u ponudama testnih naloga (06 §5, benchmark_nalozi.csv) — nazivi koji su po imenu dvosmisleni
ALIASI_MATERIJALA = [
    ("IV HR SONOMA 18mm", "IV000171", "ponuda 26-010-002423"),      # dva 'HRAST SONOMA 18': 3025 SN (ova) i 517 (2840×1830)
    ("PVC_CRNI_MAT_18", "IV000671", "ponuda 26-010-002929"),        # PVC CRNI MAT VSM-02 (Winstore VSM02-18)
    ("IV EGGER H1180 ST37", "IV000315", "ponuda 26-010-002924"),    # IVERAL H1180 HRAST HALIFAX 18MM
    ("MDF_CHAMPAGNE_19", "IV001038", "ponuda 26-010-003213"),       # MDF CHAMPAGNE 27045 OF 19MM (Winstore 27045OF-19)
    ("IV_SIVI_TAMNI_19", "IV001168", "ponuda 26-010-002924"),       # IVERAL SIVI TAMNI 2162 MN (ne 2162 PE) — Winstore 2162MN-19
]

# opći aliasi traka (oznaka u nalogu → traka), neovisno o materijalu — potvrđeno u ponudama
ALIASI_TRAKA = [
    ("1/22 JELA TAVERNA", "TR001254", "ponuda 26-010-002823"),
    ("taverna", "TR001254", "ponuda 26-010-002823"),
]


def uvezi_alias_csv(conn, putanja, tko="uvoz", izvor="skill krojna-ponuda"):
    """pw_naziv,ident → materijal_alias / traka_alias. Preskače idente kojih nema u šifrarniku (vraća ih u statistici)."""
    st = dict(materijali=0, trake=0, nepoznati=[], preskoceno=0)
    cur = conn.cursor()
    with open(putanja, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            alias, ident = (row.get("pw_naziv") or "").strip(), (row.get("ident") or "").strip()
            if not alias or not ident:
                continue
            m = cur.execute("SELECT id FROM materijal WHERE pantheon_ident = ?", (ident,)).fetchone()
            if m:
                cur.execute("INSERT INTO materijal_alias (alias, alias_norm, materijal_id, izvor, potvrdio, kada) VALUES (?, ?, ?, ?, NULL, ?) "
                            "ON CONFLICT(alias_norm) DO NOTHING", (alias, norm(alias), m[0], izvor, sada()))
                st["materijali"] += cur.rowcount
                continue
            t = cur.execute("SELECT id FROM traka WHERE pantheon_ident = ?", (ident,)).fetchone()
            if t:
                cur.execute("INSERT INTO traka_alias (alias, alias_norm, materijal_id, traka_id, izvor, potvrdio, kada) VALUES (?, ?, NULL, ?, ?, NULL, ?) "
                            "ON CONFLICT(alias_norm, materijal_id) DO NOTHING", (alias, norm(alias), t[0], izvor, sada()))
                st["trake"] += cur.rowcount
                continue
            st["nepoznati"].append((alias, ident))
    dnevnik(conn, tko, "materijal_alias", None, "uvoz", "%s: %d aliasa materijala, %d traka, %d nepoznatih identa" % (putanja, st["materijali"], st["trake"], len(st["nepoznati"])))
    conn.commit()
    P.ocisti_kes()
    return st


def upisi_potvrdjene(conn, tko="uvoz"):
    """Zadane trake i aliasi iz ponuda (ZADANE_TRAKE, ALIASI_TRAKA)."""
    cur = conn.cursor()
    n = 0
    for mid_ident, klasa, tr_ident, izvor in ZADANE_TRAKE:
        m = cur.execute("SELECT id FROM materijal WHERE pantheon_ident = ?", (mid_ident,)).fetchone()
        t = cur.execute("SELECT id FROM traka WHERE pantheon_ident = ?", (tr_ident,)).fetchone()
        if m and t:
            cur.execute("INSERT INTO materijal_traka (materijal_id, klasa, traka_id, izvor, potvrdio, kada) VALUES (?, ?, ?, ?, ?, ?) "
                        "ON CONFLICT(materijal_id, klasa) DO UPDATE SET traka_id = excluded.traka_id, izvor = excluded.izvor, potvrdio = excluded.potvrdio, kada = excluded.kada",
                        (m[0], klasa, t[0], izvor, tko, sada()))
            n += 1
    for alias, m_ident, izvor in ALIASI_MATERIJALA:
        m = cur.execute("SELECT id FROM materijal WHERE pantheon_ident = ?", (m_ident,)).fetchone()
        if m:
            cur.execute("INSERT INTO materijal_alias (alias, alias_norm, materijal_id, izvor, potvrdio, kada) VALUES (?, ?, ?, ?, ?, ?) "
                        "ON CONFLICT(alias_norm) DO NOTHING", (alias, norm(alias), m[0], izvor, tko, sada()))
    for alias, tr_ident, izvor in ALIASI_TRAKA:
        t = cur.execute("SELECT id FROM traka WHERE pantheon_ident = ?", (tr_ident,)).fetchone()
        if t:
            cur.execute("INSERT INTO traka_alias (alias, alias_norm, materijal_id, traka_id, izvor, potvrdio, kada) VALUES (?, ?, NULL, ?, ?, ?, ?) "
                        "ON CONFLICT(alias_norm, materijal_id) DO NOTHING", (alias, norm(alias), t[0], izvor, tko, sada()))
    conn.commit()
    P.ocisti_kes()
    return n


def izvedi_zadane_trake(conn, klase=("0,5/22", "1/22", "2/22", "1/44"), samo_aktivni=True, tko="uvoz"):
    """Za svaki materijal (IV/MDF/PVC/AK…) nađi po nazivu traku istog dekora za svaku klasu i upiši je kao zadanu (izvor 'naziv').
    Vraća (upisano, bez_pogotka)."""
    cur = conn.cursor()
    mats = cur.execute("SELECT id, pantheon_ident, naziv_pantheon, dekor, dekor_kod FROM materijal WHERE vrsta IN ('IV','MDF','PVC','AK','HPL') AND (aktivan = 1 OR ? = 0)",
                       (1 if samo_aktivni else 0,)).fetchall()
    upisano = 0
    bez = 0
    for m in mats:
        if not m["dekor"]:
            continue
        for klasa in klase:
            vec = cur.execute("SELECT izvor FROM materijal_traka WHERE materijal_id = ? AND klasa = ?", (m["id"], klasa)).fetchone()
            if vec and vec[0] != "naziv":
                continue
            rez = _traka_po_dekoru(conn, m["dekor"], klasa, m["dekor_kod"], m["naziv_pantheon"])   # bodovanje po dekoru + kodu materijala
            if rez.razina == "naziv":
                cur.execute("INSERT INTO materijal_traka (materijal_id, klasa, traka_id, izvor, potvrdio, kada) VALUES (?, ?, ?, 'naziv', NULL, ?) "
                            "ON CONFLICT(materijal_id, klasa) DO UPDATE SET traka_id = excluded.traka_id, izvor = 'naziv', kada = excluded.kada",
                            (m["id"], klasa, rez.id, sada()))
                upisano += 1
            else:
                bez += 1
    conn.commit()
    P.ocisti_kes()
    return upisano, bez


def _traka_po_dekoru(conn, dekor, klasa, dekor_kod=None, naziv_materijala=None):
    """Traka zadane klase s istim dekorom (riječi + kod dekora: 'SIVI TAMNI 2162 MN' ne dobiva traku '2162 OM')."""
    trs, df = P._trake(conn)
    q_rijeci = rijeci(dekor)
    q_kodovi = kodovi(dekor_kod or "")
    q_sufiksi = P.sufiksi(naziv_materijala or "")
    kand = []
    for tr in trs:
        if tr["vrsta"] not in ("ABS", "PVC") or tr["klasa"] != klasa or not P.moguc(q_rijeci, q_kodovi, tr):
            continue
        s, promasaji = P._bodovi(q_rijeci, q_kodovi, tr, df, len(trs), q_sufiksi)
        if s > -0.5:
            kand.append((s, tr, promasaji))
    kand.sort(key=lambda x: -x[0])
    rez = P._odluka(dekor, kand, potpuni=True, objasnjenje="dekor materijala, klasa %s" % klasa, q_rijeci=q_rijeci)
    if rez.razina == "naziv":
        # zadana traka se poslije primjenjuje bez pitanja (razina 'zadana'), pa traži strože: traka nema riječi viška
        # ('MASLINA' ≠ 'MASLINA SJAJ', 'BEŽ' ≠ 'LANENO BEŽ') osim ako se kod dekora poklapa
        k1 = kand[0][1]
        visak = k1["rijeci"] - set(q_rijeci) - k1.get("sufiksi", set())
        if visak and not any(k in k1["glue"] for k in q_kodovi):
            rez.razina = "za_potvrdu"
            rez.objasnjenje += "; traka ima riječi viška: " + " ".join(sorted(visak))
    return rez
