# -*- coding: utf-8 -*-
"""Ispravci šifrarnika koje ured upisuje u Hub, a Pantheon ih nema (D-51).

Tri vrste, sve preživljavaju ponovni uvoz iz Pantheona i Winstorea (kao i aliasi — što je čovjek rekao, Hub ne briše):

  debljina       IV001032 = 19      debljine nema u nazivu u Pantheonu, ured zna koja je
  debljina_umjesto_naziva  IV001290 = 19   debljina U NAZIVU je kriva; ured zna pravu dok se Pantheon ne ispravi
                                           (jedini ispravak koji pobjeđuje naziv — zato se posebno prijavljuje)
  ne_koristi_se  IV000633           ident postoji u Pantheonu, ali se više ne koristi → Hub ga ne nudi ni s čim ne povezuje
  winstore_kod   H3303ST10-18 = IV000941   Winstore kod ide na taj ident (Hub ga sam ne bi pogodio)

    py -m hub.sifrarnici.ispravci --db hub.db --popis
    py -m hub.sifrarnici.ispravci --db hub.db --debljina IV001032=19 --ne-koristi IV000633 --kod H3303ST10-18=IV000941 --tko IGOR

Zapisani su u tablici `sifrarnik_ispravak`; `primijeni()` ih upisuje u `materijal` pri svakom uvozu (hub.sifrarnici.uvoz radi to sam).
Kad ured ispravi i sam Pantheon (npr. doda 18 MM u naziv), ispravak više ništa ne mijenja i može se obrisati (`--makni`).
"""
import argparse
import csv
import io
import os
import sys

from .. import db
from ..db import sada, dnevnik
from . import prepoznaj as P

VRSTE = ("debljina", "debljina_umjesto_naziva", "ne_koristi_se", "winstore_kod")
ZADANI_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "podaci", "ispravci_sifrarnika.csv")


def upisi(conn, vrsta, kljuc, vrijednost=None, napomena=None, tko="ured"):
    """Upiši (ili promijeni) jedan ispravak. Ne primjenjuje ga — to radi primijeni()."""
    if vrsta not in VRSTE:
        raise ValueError("nepoznata vrsta ispravka: %s (dopušteno: %s)" % (vrsta, ", ".join(VRSTE)))
    kljuc = (kljuc or "").strip().upper()
    vrijednost = None if vrijednost is None else str(vrijednost).strip().upper()
    conn.execute("INSERT INTO sifrarnik_ispravak (vrsta, kljuc, vrijednost, napomena, tko, kada) VALUES (?, ?, ?, ?, ?, ?) "
                 "ON CONFLICT(vrsta, kljuc) DO UPDATE SET vrijednost = excluded.vrijednost, napomena = COALESCE(excluded.napomena, sifrarnik_ispravak.napomena), "
                 "tko = excluded.tko, kada = excluded.kada", (vrsta, kljuc, vrijednost, napomena, tko, sada()))
    dnevnik(conn, tko, "sifrarnik_ispravak", kljuc, vrsta, vrijednost)
    conn.commit()


def makni(conn, vrsta, kljuc, tko="ured"):
    n = conn.execute("DELETE FROM sifrarnik_ispravak WHERE vrsta = ? AND kljuc = ?", (vrsta, (kljuc or "").strip().upper())).rowcount
    if n:
        dnevnik(conn, tko, "sifrarnik_ispravak", kljuc, "makni", vrsta)
        k = (kljuc or "").strip().upper()
        if vrsta == "ne_koristi_se":
            conn.execute("UPDATE materijal SET ne_koristi_se = 0 WHERE pantheon_ident = ?", (k,))
        elif vrsta.startswith("debljina"):        # vrati debljinu na ono što kaže naziv u Pantheonu (ili natrag na nepoznato)
            from .nazivi import debljina as deb_iz_naziva
            r = conn.execute("SELECT naziv_pantheon FROM materijal WHERE pantheon_ident = ?", (k,)).fetchone()
            d = deb_iz_naziva(r["naziv_pantheon"]) if r else None
            conn.execute("UPDATE materijal SET debljina_rucno = NULL, debljina = ?, debljina_izvor = ? WHERE pantheon_ident = ?",
                         (d, "naziv" if d is not None else None, k))
    conn.commit()
    P.ocisti_kes()
    return n


def popis(conn, vrsta=None):
    q = "SELECT vrsta, kljuc, vrijednost, napomena, tko, kada FROM sifrarnik_ispravak"
    a = ()
    if vrsta:
        q, a = q + " WHERE vrsta = ?", (vrsta,)
    return [dict(r) for r in conn.execute(q + " ORDER BY vrsta, kljuc", a)]


def veze_winstore(conn):
    """{WINSTORE_KOD: materijal_id} — ručno povezani kodovi; koristi ih uvoz Winstorea prije svog prepoznavanja."""
    out = {}
    for r in conn.execute("SELECT i.kljuc, m.id FROM sifrarnik_ispravak i JOIN materijal m ON m.pantheon_ident = i.vrijednost WHERE i.vrsta = 'winstore_kod'"):
        out[r["kljuc"]] = r["id"]
    return out


def primijeni(conn, tko="uvoz"):
    """Upiši ispravke u materijal: ručna debljina (samo ako je naziv nema), oznaka 'ne koristi se', prvi ručni Winstore kod.
    Vraća statistiku; poziva se nakon uvoza Pantheona, a prije uvoza Winstorea."""
    st = dict(debljina=0, debljina_umjesto_naziva=0, ne_koristi_se=0, winstore_kod=0, nepoznati=[])
    for r in conn.execute("SELECT vrsta, kljuc, vrijednost FROM sifrarnik_ispravak ORDER BY vrsta, kljuc").fetchall():
        vrsta, kljuc, vrij = r["vrsta"], r["kljuc"], r["vrijednost"]
        if vrsta == "debljina_umjesto_naziva":                  # naziv u Pantheonu je kriv — ovo ga nadglasava dok se ne ispravi
            d = float((vrij or "").replace(",", "."))
            n = conn.execute("UPDATE materijal SET debljina_rucno = ?, debljina = ?, debljina_izvor = 'rucno_umjesto_naziva' "
                             "WHERE pantheon_ident = ?", (d, d, kljuc)).rowcount
        elif vrsta == "debljina":
            d = float((vrij or "").replace(",", "."))
            n = conn.execute("UPDATE materijal SET debljina_rucno = ?, "
                             "debljina = CASE WHEN debljina_izvor = 'naziv' THEN debljina ELSE ? END, "
                             "debljina_izvor = CASE WHEN debljina_izvor = 'naziv' THEN 'naziv' ELSE 'rucno' END "
                             "WHERE pantheon_ident = ?", (d, d, kljuc)).rowcount
        elif vrsta == "ne_koristi_se":
            n = conn.execute("UPDATE materijal SET ne_koristi_se = ? WHERE pantheon_ident = ?", (0 if vrij in ("0", "NE") else 1, kljuc)).rowcount
        else:                                  # winstore_kod: kod → ident; materijal pamti prvi kod, ostali ostaju na razini ploče
            m = conn.execute("SELECT id, winstore_kod FROM materijal WHERE pantheon_ident = ?", (vrij,)).fetchone()
            if not m:
                st["nepoznati"].append((vrsta, kljuc, vrij))
                continue
            conn.execute("UPDATE materijal SET winstore_kod = NULL WHERE UPPER(winstore_kod) = ? AND id <> ?", (kljuc, m["id"]))   # kod više ne pripada starom identu
            if not m["winstore_kod"]:
                conn.execute("UPDATE materijal SET winstore_kod = ?, trazi = COALESCE(trazi, '') || ' ' || ? WHERE id = ?", (kljuc, kljuc, m["id"]))
            n = 1
        if n:
            st[vrsta] += 1
        else:
            st["nepoznati"].append((vrsta, kljuc, vrij))
    conn.commit()
    P.ocisti_kes()
    return st


def ucitaj_csv(conn, putanja, tko="uvoz"):
    """Učitaj odluke ureda iz CSV-a (vrsta;kljuc;vrijednost;napomena). Obrazac se vraća iz Excela pa je izdržljiv:
    prihvaća i `;` i `,` kao razdjelnik, višak stupaca spaja u napomenu, prazne i neispravne retke preskače.

    Vraća (upisano, preskočeno) gdje je preskočeno popis (redak, kljuc, vrijednost, razlog) — prazno polje nije greška,
    ali vrijednost koja nije ident jest (npr. 'NIŠTA' za robu koja nema ident) i mora se vidjeti."""
    with open(putanja, encoding="utf-8-sig", newline="") as f:
        tekst = f.read()
    prvi = tekst.split("\n", 1)[0]
    raz = ";" if prvi.count(";") >= prvi.count(",") else ","
    red = list(csv.reader(io.StringIO(tekst), delimiter=raz))
    if not red:
        return 0, []
    zaglavlje = [(x or "").strip().lower() for x in red[0]]
    if zaglavlje[:2] != ["vrsta", "kljuc"]:
        raise ValueError("prvi redak mora biti zaglavlje 'vrsta%skljuc%svrijednost%snapomena'" % (raz, raz, raz))
    n, presk = 0, []
    for i, r in enumerate(red[1:], 2):
        r = [(x or "").strip() for x in r] + ["", "", "", ""]
        vrsta, kljuc, vrij = r[0], r[1], r[2]
        napomena = ", ".join(x for x in r[3:] if x) or None
        if not vrsta or vrsta.startswith("#"):
            continue
        if not vrij:
            presk.append((i, kljuc, "", "prazno — ured još nije odlučio"))
            continue
        if vrsta == "winstore_kod" and not conn.execute("SELECT 1 FROM materijal WHERE pantheon_ident = ?", (vrij.upper(),)).fetchone():
            presk.append((i, kljuc, vrij, "nije postojeći ident materijala"))
            continue
        if vrsta.startswith("debljina"):
            try:
                float(vrij.replace(",", "."))
            except ValueError:
                presk.append((i, kljuc, vrij, "nije broj"))
                continue
        upisi(conn, vrsta, kljuc, vrij, napomena, tko)
        n += 1
    return n, presk


def naziv_ispravljen(conn):
    """Ispravci vrste 'debljina_umjesto_naziva' kojima naziv u Pantheonu sada govori isto — ispravak je odradio svoje i može se maknuti."""
    from .nazivi import debljina as deb_iz_naziva
    out = []
    for r in conn.execute("SELECT i.kljuc, i.vrijednost, m.naziv_pantheon FROM sifrarnik_ispravak i "
                          "JOIN materijal m ON m.pantheon_ident = i.kljuc WHERE i.vrsta = 'debljina_umjesto_naziva'"):
        d = deb_iz_naziva(r["naziv_pantheon"])
        if d is not None and abs(d - float(str(r["vrijednost"]).replace(",", "."))) < 0.11:
            out.append(dict(ident=r["kljuc"], debljina=d, naziv=r["naziv_pantheon"]))
    return out


def neslaganje_debljine(conn, tolerancija=0.5):
    """Ručno povezani Winstore kodovi kojima se debljina ploče u Winstoreu razlikuje od debljine identa.
    Veza radi, ali skladište i šifrarnik govore različito — netko treba ispraviti jedno od dvoje."""
    return [dict(r) for r in conn.execute(
        "SELECT i.kljuc AS kod, m.pantheon_ident AS ident, m.naziv_pantheon AS naziv, m.debljina AS debljina_identa, "
        "       MAX(w.debljina) AS debljina_winstore, MAX(w.opis) AS opis "
        "FROM sifrarnik_ispravak i JOIN materijal m ON m.pantheon_ident = i.vrijednost "
        "JOIN winstore_ploca w ON UPPER(w.materijal_kod) = i.kljuc "
        "WHERE i.vrsta = 'winstore_kod' AND m.debljina IS NOT NULL AND w.debljina IS NOT NULL "
        "GROUP BY i.kljuc HAVING ABS(m.debljina - MAX(w.debljina)) > ?", (tolerancija,))]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ispravci šifrarnika u Hubu (debljina, ne koristi se, Winstore kod) — D-51")
    ap.add_argument("--db")
    ap.add_argument("--debljina", action="append", default=[], metavar="IDENT=MM", help="npr. IV001032=19")
    ap.add_argument("--ne-koristi", action="append", default=[], metavar="IDENT", help="ident koji se više ne koristi")
    ap.add_argument("--kod", action="append", default=[], metavar="KOD=IDENT", help="npr. H3303ST10-18=IV000941")
    ap.add_argument("--makni", action="append", default=[], metavar="VRSTA:KLJUC", help="npr. debljina:IV001032")
    ap.add_argument("--csv", nargs="?", const=ZADANI_CSV, help="učitaj ispravke iz CSV-a (zadano: podaci/ispravci_sifrarnika.csv)")
    ap.add_argument("--napomena")
    ap.add_argument("--popis", action="store_true")
    ap.add_argument("--tko", default="ured")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    for x in a.debljina:
        upisi(conn, "debljina", *x.split("=", 1), napomena=a.napomena, tko=a.tko)
    for x in a.ne_koristi:
        upisi(conn, "ne_koristi_se", x, "1", a.napomena, a.tko)
    for x in a.kod:
        upisi(conn, "winstore_kod", *x.split("=", 1), napomena=a.napomena, tko=a.tko)
    for x in a.makni:
        print("maknuto:" if makni(conn, *x.split(":", 1), tko=a.tko) else "nije bilo:", x)
    if a.csv:
        n, presk = ucitaj_csv(conn, a.csv, a.tko)
        print("Ucitano iz CSV-a: %d ispravaka (%s)" % (n, os.path.basename(a.csv)))
        for i, kljuc, vrij, zasto in presk:
            print("   redak %-3d %-16s %-12s preskoceno: %s" % (i, kljuc, vrij, zasto))
    st = primijeni(conn, a.tko)
    print("Primijenjeno: debljina %d, ne koristi se %d, Winstore kod %d" % (st["debljina"], st["ne_koristi_se"], st["winstore_kod"]))
    for x in neslaganje_debljine(conn):
        print("   PAZI: %-16s Winstore %s mm, %s %s mm — uskladiti" % (x["kod"], x["debljina_winstore"], x["ident"], x["debljina_identa"]))
    for vrsta, kljuc, vrij in st["nepoznati"]:
        print("   NEPOZNAT IDENT: %s %s -> %s" % (vrsta, kljuc, vrij))
    if a.popis or not (a.debljina or a.ne_koristi or a.kod or a.makni or a.csv):
        for x in popis(conn):
            print("   %-14s %-16s %-12s %s" % (x["vrsta"], x["kljuc"], x["vrijednost"] or "", x["napomena"] or ""))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
