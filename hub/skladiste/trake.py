"""skladiste/trake.py — prilagodnik za Regal traku (D-63 / D-64 / D-77): Hub samo ČITA stanje traka po Pantheon identu.

Regal traka (server/server.py): `GET /api/stanje` → {rev, stanje: {lok: {IDENT: "R3-05-B"}, q: {IDENT: {m: metri, mt: 'YYYY-MM-DD HH:MM'}}}}.
Adresa poslužitelja je postavka `regal_traka_url` (zadano http://192.168.5.201:8080). Kad Regal traka nije dostupna, sve vraća None
i ništa ne staje — pretinac na ispisu ostaje prazan.
"""
import json
import time
import urllib.request

from ..db import postavka

ZADANI_URL = "http://192.168.5.201:8080"
_kes = {"t": 0.0, "url": None, "stanje": None}
KES_SEK = 60


def url(conn):
    return (postavka(conn, "regal_traka_url", ZADANI_URL) or ZADANI_URL).rstrip("/")


def stanje_sve(conn, timeout=2.0):
    """Cijelo stanje Regal trake (dict lok/q) ili None. Keš 60 s."""
    u = url(conn)
    if _kes["url"] == u and time.time() - _kes["t"] < KES_SEK and (_kes["stanje"] is not None or _kes.get("neuspjeh")):
        return _kes["stanje"]                     # i neuspjeh se pamti 60 s — inače svaki ident čeka svoj timeout (ekran skladišta 12 s)
    try:
        with urllib.request.urlopen(u + "/api/stanje", timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8"))
        s = d.get("stanje") or {}
        _kes.update(t=time.time(), url=u, stanje=s, neuspjeh=False)
        return s
    except Exception:
        _kes.update(t=time.time(), url=u, stanje=None, neuspjeh=True)
        return None


def pretinac(conn, ident):
    """Adresa pretinca trake (npr. 'R3-05-B') ili None."""
    s = stanje_sve(conn)
    if not s or not ident:
        return None
    return (s.get("lok") or {}).get(ident) or None


def metri(conn, ident):
    """Preostali metri na roli po zadnjem upisu ili None."""
    s = stanje_sve(conn)
    if not s or not ident:
        return None
    q = (s.get("q") or {}).get(ident)
    if isinstance(q, dict) and q.get("m") is not None:
        try:
            return float(q["m"])
        except (TypeError, ValueError):
            return None
    return None


def ocisti_kes():
    _kes.update(t=0.0, url=None, stanje=None, neuspjeh=False)


def stanje(conn, ident):
    """Isto sučelje kao ploče / restlovi: {ident, metri, pretinac, dostupno} — dostupno=False kad Regal traka ne odgovara."""
    s = stanje_sve(conn)
    return dict(ident=ident, metri=metri(conn, ident), pretinac=pretinac(conn, ident), dostupno=s is not None)
