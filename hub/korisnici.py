# -*- coding: utf-8 -*-
"""Korisnici Huba: prijava s lozinkom, sesije, potpis u mailu (D-88, Igor 17. 9.).

Lozinka se čuva samo kao PBKDF2-SHA256 hash (sol + 200 000 iteracija), nikad u čistom obliku. Sesija = nasumični token u
kolačiću `hub_sesija` (tablica `sesija`), traje SESIJA_DANA od zadnjeg korištenja. Prijava postaje obavezna (postavka
`prijava_obavezna` = 1) čim prvi korisnik dobije lozinku — do tada Hub radi kao dosad (oznaka bez lozinke), pa testovi i
prvi start ne traže ništa. Korisnik bez lozinke prijavi se praznom lozinkom i odmah je mora postaviti (`treba_lozinka`).
Potpis u mailu: ime + funkcija + tvrtka + telefon + e-mail prijavljenog korisnika (ili njegov vlastiti tekst `potpis`)."""
import argparse
import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta

from . import db
from .db import sada, dnevnik, postavka

ITERACIJE = 200_000
SESIJA_DANA = 30
ULOGE = ("ured", "nabava", "voditelj", "admin", "sustav")
TVRTKA = "Paneli projekt d.o.o."


class KorisnikGreska(ValueError):
    pass


def hash_lozinke(lozinka, sol=None):
    sol = sol or secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", lozinka.encode("utf-8"), sol, ITERACIJE)
    return "pbkdf2$%d$%s$%s" % (ITERACIJE, base64.b64encode(sol).decode(), base64.b64encode(h).decode())


def lozinka_odgovara(lozinka, zapis):
    try:
        _, it, sol, h = zapis.split("$")
        n = hashlib.pbkdf2_hmac("sha256", lozinka.encode("utf-8"), base64.b64decode(sol), int(it))
        return secrets.compare_digest(base64.b64encode(n).decode(), h)
    except (ValueError, AttributeError):
        return False


def _red(r):
    if not r:
        return None
    d = dict(r)
    d["ima_lozinku"] = bool(d.pop("lozinka_hash", None))
    return d


def korisnik(conn, oznaka):
    return _red(conn.execute("SELECT * FROM korisnik WHERE oznaka = ?", ((oznaka or "").strip().upper(),)).fetchone())


def popis(conn, i_sustav=False):
    sql = "SELECT * FROM korisnik" + ("" if i_sustav else " WHERE uloga != 'sustav'") + " ORDER BY aktivan DESC, oznaka"
    return [_red(r) for r in conn.execute(sql).fetchall()]


def prijava_obavezna(conn):
    return (postavka(conn, "prijava_obavezna", "0") or "0").strip() == "1"


def upisi(conn, oznaka, ime=None, uloga=None, email=None, telefon=None, funkcija=None, potpis=None, aktivan=None, tko="web"):
    """Novi korisnik ili izmjena postojećeg (samo polja koja su dana)."""
    oznaka = (oznaka or "").strip().upper()
    if not oznaka or not oznaka.replace("_", "").isalnum():
        raise KorisnikGreska("oznaka korisnika: slova/brojke bez razmaka (IVANA, GORAN…)")
    if uloga is not None and uloga not in ULOGE:
        raise KorisnikGreska("uloga %s (ured | nabava | voditelj | admin)" % uloga)
    k = conn.execute("SELECT id FROM korisnik WHERE oznaka = ?", (oznaka,)).fetchone()
    polja = dict(ime=ime, uloga=uloga, email=email, telefon=telefon, funkcija=funkcija, potpis=potpis, aktivan=aktivan)
    polja = {a: (v.strip() if isinstance(v, str) else v) for a, v in polja.items() if v is not None}
    if k:
        if polja:
            conn.execute("UPDATE korisnik SET %s WHERE id = ?" % ", ".join("%s = ?" % a for a in polja), list(polja.values()) + [k["id"]])
        dnevnik(conn, tko, "korisnik", k["id"], "izmjena", ", ".join(polja) or "-")
    else:
        polja.setdefault("ime", oznaka.title())
        polja.setdefault("uloga", "ured")
        cur = conn.execute("INSERT INTO korisnik (oznaka, %s) VALUES (?, %s)" % (", ".join(polja), ", ".join("?" * len(polja))), [oznaka] + list(polja.values()))
        dnevnik(conn, tko, "korisnik", cur.lastrowid, "novi", oznaka)
    conn.commit()
    return korisnik(conn, oznaka)


def postavi_lozinku(conn, oznaka, nova, tko="web", zadrzi_token=None):
    """Nova lozinka (min. 4 znaka). Ostale sesije korisnika padaju (osim `zadrzi_token` — vlastita trenutna). Prva lozinka u Hubu uključi obaveznu prijavu."""
    k = korisnik(conn, oznaka)
    if not k:
        raise KorisnikGreska("korisnik %s ne postoji" % oznaka)
    if not nova or len(nova) < 4:
        raise KorisnikGreska("lozinka mora imati barem 4 znaka")
    conn.execute("UPDATE korisnik SET lozinka_hash = ? WHERE id = ?", (hash_lozinke(nova), k["id"]))
    conn.execute("DELETE FROM sesija WHERE korisnik_id = ? AND token != ?", (k["id"], zadrzi_token or ""))   # stare sesije padaju
    ukljucena = False
    if not prijava_obavezna(conn):
        conn.execute("INSERT OR REPLACE INTO postavke (kljuc, vrijednost, opis) VALUES ('prijava_obavezna', '1', 'prijava s lozinkom obavezna (uključeno prvom lozinkom)')")
        ukljucena = True
    dnevnik(conn, tko, "korisnik", k["id"], "lozinka", "postavljena" + (" — prijava uključena" if ukljucena else ""))
    conn.commit()
    return dict(oznaka=k["oznaka"], prijava_ukljucena=ukljucena)


def prijava(conn, oznaka, lozinka=""):
    """Provjeri korisnika i otvori sesiju. Vraća dict(korisnik, token, treba_lozinka)."""
    r = conn.execute("SELECT * FROM korisnik WHERE oznaka = ?", ((oznaka or "").strip().upper(),)).fetchone()
    if not r or not r["aktivan"] or r["uloga"] == "sustav":
        raise KorisnikGreska("nepoznat ili neaktivan korisnik")
    treba = not r["lozinka_hash"]
    if not treba and not lozinka_odgovara(lozinka or "", r["lozinka_hash"]):
        dnevnik(conn, r["oznaka"], "korisnik", r["id"], "prijava_neuspjela", "")
        conn.commit()
        raise KorisnikGreska("pogrešna lozinka")
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO sesija (token, korisnik_id, stvoreno, zadnje) VALUES (?, ?, ?, ?)", (token, r["id"], sada(), sada()))
    conn.execute("DELETE FROM sesija WHERE zadnje < ?", ((datetime.now() - timedelta(days=SESIJA_DANA)).strftime("%Y-%m-%dT%H:%M:%S"),))
    dnevnik(conn, r["oznaka"], "korisnik", r["id"], "prijava", "bez lozinke — treba je postaviti" if treba else "")
    conn.commit()
    return dict(korisnik=_red(r), token=token, treba_lozinka=treba)


def iz_tokena(conn, token):
    """Korisnik iz kolačića sesije (None kad nema / istekla). Osvježi `zadnje` najviše jednom u sat."""
    if not token:
        return None
    s = conn.execute("SELECT s.token, s.zadnje, k.* FROM sesija s JOIN korisnik k ON k.id = s.korisnik_id WHERE s.token = ?", (token,)).fetchone()
    if not s or not s["aktivan"]:
        return None
    if s["zadnje"] < (datetime.now() - timedelta(days=SESIJA_DANA)).strftime("%Y-%m-%dT%H:%M:%S"):
        conn.execute("DELETE FROM sesija WHERE token = ?", (token,))
        conn.commit()
        return None
    if s["zadnje"] < (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"):
        conn.execute("UPDATE sesija SET zadnje = ? WHERE token = ?", (sada(), token))
        conn.commit()
    d = {k: s[k] for k in s.keys() if k not in ("token", "zadnje")}
    return _red(d)


def odjava(conn, token):
    conn.execute("DELETE FROM sesija WHERE token = ?", (token or "",))
    conn.commit()


def potpis(conn, oznaka):
    """Potpis za mail: vlastiti tekst korisnika ili ime / funkcija / tvrtka / telefon / e-mail. Nepoznat korisnik → samo tvrtka."""
    k = korisnik(conn, oznaka)
    tvrtka = postavka(conn, "tvrtka_naziv", TVRTKA) or TVRTKA
    if not k or k["uloga"] == "sustav":
        return tvrtka
    if k.get("potpis"):
        return k["potpis"].strip()
    redci = [k.get("ime") or k["oznaka"].title()]
    if k.get("funkcija"):
        redci.append(k["funkcija"])
    redci.append(tvrtka)
    kontakt = " · ".join(x for x in (k.get("telefon"), k.get("email")) if x)
    if kontakt:
        redci.append(kontakt)
    return "\n".join(redci)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Korisnici Huba (D-88): popis, nova lozinka")
    ap.add_argument("--db")
    ap.add_argument("--popis", action="store_true")
    ap.add_argument("--lozinka", metavar="OZNAKA", help="postavi lozinku korisniku (upis s tipkovnice)")
    ap.add_argument("--iskljuci-prijavu", action="store_true", help="prijava opet nije obavezna (npr. zaboravljene sve lozinke)")
    a = ap.parse_args(argv)
    conn = db.spoji(a.db)
    try:
        if a.lozinka:
            import getpass
            r = postavi_lozinku(conn, a.lozinka, getpass.getpass("Nova lozinka za %s: " % a.lozinka.upper()), tko="cli")
            print("lozinka postavljena za %s%s" % (r["oznaka"], " — prijava s lozinkom je sada obavezna" if r["prijava_ukljucena"] else ""))
        if a.iskljuci_prijavu:
            conn.execute("INSERT OR REPLACE INTO postavke (kljuc, vrijednost, opis) VALUES ('prijava_obavezna', '0', 'prijava s lozinkom obavezna')")
            conn.commit()
            print("prijava više nije obavezna")
        if a.popis or not (a.lozinka or a.iskljuci_prijavu):
            print("prijava obavezna: %s" % ("DA" if prijava_obavezna(conn) else "NE"))
            for k in popis(conn):
                print("%-8s %-22s %-9s %s %s" % (k["oznaka"], k["ime"] or "", k["uloga"] or "", "lozinka" if k["ima_lozinku"] else "bez lozinke", "" if k["aktivan"] else "(neaktivan)"))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
