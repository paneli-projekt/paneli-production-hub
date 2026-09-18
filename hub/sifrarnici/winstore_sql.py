# -*- coding: utf-8 -*-
"""Čitanje stanja ploča izravno iz Winstorea (dokument 38, D-98) — zamjena za ručni XML izvoz.

Winstore (SPV - Winstore 1.0.4) ima dokumentirano sučelje za vanjski softver: zasebnu SQL Server bazu
`WINSTORE_EXCHANGE` s vlastitom prijavom. Hub iz nje ČITA pogled `vBoardsDropsStatus`:

    Code | MaterialCode | MaterialDescription | L | W | T | Grain | IsDrop | Stored | StoredInternal | StoredExternal | Booked

Stupci se poklapaju sa starim XML izvozom (`Stored` ↔ TotalQty, `StoredInternal` ↔ InternalQty,
`StoredExternal` ↔ ExternalQty, `IsDrop` ↔ Drop), uz `Booked` — koliko je ploča Winstore sam rezervirao
za svoje picking liste; toga u XML-u nije bilo.

Hub u Winstore NIŠTA NE PIŠE. Upis (rezervacije, vanjski restlovi) je moguć preko istih tablica,
ali dira sustav koji upravlja strojem i ide tek uz dogovor s proizvođačem (dokument 38 §5).

Podaci za spajanje su u postavkama (`winstore_sql_*`); lozinka se čuva u bazi Huba i ne prikazuje se na ekranu.
Upravljački program: `pymssql` ili `pyodbc` — koji je god instaliran.
"""
from ..db import postavka, sada, dnevnik
from . import winstore as W

POGLED = "vBoardsDropsStatus"
STUPCI = "Code, MaterialCode, MaterialDescription, L, W, T, Grain, IsDrop, Stored, StoredInternal, StoredExternal, Booked"


class NemaVeze(RuntimeError):
    """Spajanje nije moguće: nije uključeno, nema upravljačkog programa ili poslužitelj ne odgovara."""


def postavke(conn):
    return dict(ukljucen=(postavka(conn, "winstore_sql_ukljucen", "0") or "0") == "1",
                server=postavka(conn, "winstore_sql_server", "") or "",
                baza=postavka(conn, "winstore_sql_baza", "WINSTORE_EXCHANGE") or "WINSTORE_EXCHANGE",
                korisnik=postavka(conn, "winstore_sql_korisnik", "") or "",
                lozinka=postavka(conn, "winstore_sql_lozinka", "") or "",
                minuta=int(float(postavka(conn, "winstore_sql_minuta", "30") or 30)))


def veza(p):
    """Otvori vezu na SQL Server. `p` je rječnik iz `postavke`. Diže NemaVeze s razumljivom porukom."""
    if not p["server"] or not p["korisnik"]:
        raise NemaVeze("nisu upisani poslužitelj i korisnik (Postavke → Winstore)")
    try:
        import pymssql
    except ImportError:
        pymssql = None
    if pymssql is not None:
        host, _, inst = p["server"].partition("\\")
        try:
            return pymssql.connect(server=host, database=p["baza"], user=p["korisnik"], password=p["lozinka"],
                                   login_timeout=10, timeout=30, **({"instance": inst} if inst else {}))
        except Exception as e:                                  # noqa: BLE001 — poruka ide korisniku
            raise NemaVeze("pymssql: %s" % e)
    try:
        import pyodbc
    except ImportError:
        raise NemaVeze("nema upravljačkog programa za SQL Server — instaliraj `pymssql` (pip install pymssql)")
    for drv in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"):
        try:
            return pyodbc.connect("DRIVER={%s};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s;TrustServerCertificate=yes;Connect Timeout=10"
                                  % (drv, p["server"], p["baza"], p["korisnik"], p["lozinka"]))
        except Exception:                                       # noqa: BLE001 — probaj sljedeći upravljački program
            continue
    raise NemaVeze("pyodbc: nijedan ODBC upravljački program za SQL Server nije uspio otvoriti vezu")


def _f(x):
    try:
        return float(x) if x not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _i(x):
    try:
        return int(float(x)) if x not in (None, "") else 0
    except (TypeError, ValueError):
        return 0


def stavke_iz_redaka(redovi):
    """Redci pogleda → stavke u istom obliku kao `winstore.ucitaj_xml` (+ `rezervirano`), pa uvoz ide zajedničkim putem."""
    out = []
    for r in redovi:
        kod, mat, opis, L, W_, T, god, drop, uk, unut, van, rez = (list(r) + [None] * 12)[:12]
        out.append(dict(kod=(kod or "").strip(), materijal_kod=(mat or "").strip().upper(), opis=(opis or "").strip(),
                        L=_f(L), W=_f(W_), debljina=_f(T), god=_i(god),
                        kom_ukupno=_i(uk), kom_interno=_i(unut), kom_eksterno=_i(van),
                        drop=1 if _i(drop) else 0, rezervirano=_i(rez)))
    return out


def procitaj(p):
    """Otvori vezu, pročitaj pogled i zatvori vezu. Vraća popis stavki."""
    v = veza(p)
    try:
        cur = v.cursor()
        cur.execute("SELECT %s FROM %s" % (STUPCI, POGLED))
        return stavke_iz_redaka(cur.fetchall())
    finally:
        try:
            v.close()
        except Exception:                                        # noqa: BLE001 — zatvaranje ne smije srušiti uvoz
            pass


def provjeri(conn):
    """Proba veze za ekran Postavki: vraća {ok, poruka, stavki, ploca, restlova}. Ne dira bazu Huba."""
    p = postavke(conn)
    try:
        st = procitaj(p)
    except NemaVeze as e:
        return dict(ok=False, poruka=str(e), stavki=0, ploca=0, restlova=0)
    except Exception as e:                                       # noqa: BLE001 — poruka ide korisniku
        return dict(ok=False, poruka="%s: %s" % (type(e).__name__, e), stavki=0, ploca=0, restlova=0)
    return dict(ok=True, poruka="veza radi", stavki=len(st),
                ploca=sum(1 for x in st if not x["drop"]), restlova=sum(1 for x in st if x["drop"]))


def osvjezi(conn, tko="winstore", povezi=True):
    """Pročitaj stanje iz Winstorea i upiši ga u `winstore_ploca` (zamjenjuje prethodno stanje, kao i XML uvoz)."""
    p = postavke(conn)
    st = W.uvezi_stavke(conn, procitaj(p), "baza Winstorea", tko=tko, povezi=povezi)
    st["izvor"] = "sql"
    return st


def zadnje_stanje(conn):
    """Kad je stanje zadnji put preuzeto i odakle — za prikaz starosti na ekranu."""
    v = postavka(conn, "winstore_izvoz", "") or ""
    izvor, _, kada = v.partition(" @ ")
    return dict(izvor=izvor or None, kada=kada or None)


def starost_minuta(conn):
    """Koliko je minuta prošlo od zadnjeg preuzimanja (None ako se nikad nije preuzelo ili je zapis neuporabljiv)."""
    import datetime
    kada = zadnje_stanje(conn)["kada"]
    if not kada:
        return None
    for oblik in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            t = datetime.datetime.strptime(kada[:19], oblik)
            break
        except ValueError:
            t = None
    if t is None:
        return None
    return max(0.0, (datetime.datetime.now() - t).total_seconds() / 60.0)


def osvjezi_ako_treba(conn, tko="winstore"):
    """Poziva se s ekrana skladišta: ako je čitanje uključeno i stanje starije od zadanog broja minuta, preuzmi novo.

    Nikad ne ruši ekran — neuspjeh se zapiše u dnevnik i stanje ostaje ono zadnje poznato."""
    p = postavke(conn)
    if not p["ukljucen"]:
        return None
    s = starost_minuta(conn)
    if s is not None and s < p["minuta"]:
        return None
    try:
        return osvjezi(conn, tko=tko)
    except Exception as e:                                       # noqa: BLE001 — stanje ostaje staro, ekran radi dalje
        dnevnik(conn, tko, "winstore_ploca", None, "greska", "čitanje stanja iz Winstorea nije uspjelo: %s" % e)
        conn.commit()
        return None


def main(argv=None):
    """py -m hub.sifrarnici.winstore_sql --db hub.db [--provjeri]"""
    import argparse
    from .. import db
    ap = argparse.ArgumentParser(description="Preuzmi stanje ploča iz baze Winstorea (samo čitanje)")
    ap.add_argument("--db", default=None)
    ap.add_argument("--provjeri", action="store_true", help="samo proba veze, bez upisa")
    a = ap.parse_args(argv)
    conn = db.spoji(a.db)
    db.init(conn)
    if a.provjeri:
        r = provjeri(conn)
        print("%s — %d stavki (%d ploča, %d restlova)" % (r["poruka"], r["stavki"], r["ploca"], r["restlova"]))
        return 0 if r["ok"] else 1
    st = osvjezi(conn)
    print("%d stavki, %d kodova, povezano %d + %d već, nepovezano %d, ambalaža %d (%s)"
          % (st["stavke"], st["kodova"], st["povezano"], st["vec_povezano"], len(st["nepovezano"]), st["ambalaza"], sada()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
