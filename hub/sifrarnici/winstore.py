# -*- coding: utf-8 -*-
"""Uvoz Winstore inventara (ručni XML izvoz operatera nestinga, npr. 04_STROJEVI\\NESTING\\11092026.XML; I-12) u winstore_ploca
i povezivanje MaterialCode ↔ Pantheon materijal (D-24: Hub u pozadini piše Winstore kod u SIFRA MAT za bNest).

<Item><Code>W908ST2-18-2800-2070</Code><Length>2800</Length><Width>2070</Width><Thickness>18</Thickness><Grain>0</Grain>
      <MaterialCode>W908ST2-18</MaterialCode><MaterialDescription>IVERAL BIJELI NK W908ST2 18MM</MaterialDescription>
      <Drop>0</Drop><TotalQty>2</TotalQty><InternalQty>2</InternalQty><ExternalQty>0</ExternalQty></Item>
Više Item-a može imati isti MaterialCode (više skladišnih linija / ostataka) — zbrajaju se po kodu u pogledu stanja.
Povezivanje: (1) materijal.winstore_kod već postavljen → veza; (2) kod je Pantheon ident (IV000065-19, IV000160A-18) → taj materijal;
(3) inače prepoznavanje po MaterialDescription (vrsta + debljina + dekor + kod) → siguran pogodak upisuje winstore_kod, god i dimenziju
ploče u materijal; nesiguran ostaje nepovezan (izvještaj). Više kodova istog materijala (varijante A/B/C, druga dimenzija) vežu se
na razini winstore_ploca; materijal pamti prvi kod.
"""
import os
import re
import xml.etree.ElementTree as ET

from ..db import sada, dnevnik
from .nazivi import norm
from . import prepoznaj as P


def ucitaj_xml(putanja):
    root = ET.parse(putanja).getroot()
    out = []
    for it in root.findall("Item"):
        d = {c.tag: (c.text or "").strip() for c in it}
        out.append(dict(kod=d.get("Code", ""), materijal_kod=d.get("MaterialCode", "").upper(), opis=d.get("MaterialDescription", ""),
                        L=_f(d.get("Length")), W=_f(d.get("Width")), debljina=_f(d.get("Thickness")), god=int(_f(d.get("Grain")) or 0),
                        kom_ukupno=int(_f(d.get("TotalQty")) or 0), kom_interno=int(_f(d.get("InternalQty")) or 0),
                        kom_eksterno=int(_f(d.get("ExternalQty")) or 0), drop=int(_f(d.get("Drop")) or 0)))
    return out


def _f(x):
    try:
        return float(x) if x not in (None, "") else None
    except ValueError:
        return None


def uvezi_winstore(conn, putanja, tko="uvoz", povezi=True):
    """Zamijeni prethodni izvoz istog imena, upiši ploče, poveži s materijalima. Vraća statistiku i popis nepovezanih kodova."""
    stavke = ucitaj_xml(putanja)
    izvoz = os.path.basename(putanja)
    cur = conn.cursor()
    cur.execute("DELETE FROM winstore_ploca WHERE izvoz = ?", (izvoz,))
    st = dict(stavke=len(stavke), kodova=len({s["materijal_kod"] for s in stavke}), povezano=0, vec_povezano=0, nepovezano=[], dodatni=[], po_razini={})
    veze = {}
    for kod in sorted({s["materijal_kod"] for s in stavke}):
        r = cur.execute("SELECT id FROM materijal WHERE UPPER(winstore_kod) = ?", (kod,)).fetchone()
        if r:
            veze[kod] = r[0]
            st["vec_povezano"] += 1
    if povezi:
        for kod in sorted({s["materijal_kod"] for s in stavke} - set(veze)):
            s = next(x for x in stavke if x["materijal_kod"] == kod)
            mid, razina = _po_identu(cur, kod, s["debljina"]), "ident"
            if not mid:
                rez = P.prepoznaj_materijal(conn, s["opis"], debljina=s["debljina"], sirina_ploce=s["W"], winstore_kod=kod)
                if rez.razina in ("alias", "naziv"):
                    mid, razina = rez.id, rez.razina
                else:
                    st["nepovezano"].append((kod, s["opis"], "%s: %s" % (rez.razina, (rez.kandidati[0][0] + " " + rez.kandidati[0][1]) if rez.kandidati else "—")))
                    continue
            zauzet = cur.execute("SELECT pantheon_ident, winstore_kod FROM materijal WHERE id = ?", (mid,)).fetchone()
            if not zauzet["winstore_kod"]:
                cur.execute("UPDATE materijal SET winstore_kod = ?, god = COALESCE(god, ?), ploca_L = COALESCE(?, ploca_L), ploca_W = COALESCE(?, ploca_W), "
                            "trazi = trazi || ' ' || ? WHERE id = ?", (kod, s["god"], s["L"], s["W"], kod, mid))
                for m in P._materijali(conn)[0]:          # osvježi keš bez ponovnog učitavanja (1609 materijala × 400 kodova)
                    if m["id"] == mid:
                        m["winstore"] = kod
            elif zauzet["winstore_kod"].upper() != kod:
                st["dodatni"].append((kod, zauzet["pantheon_ident"], zauzet["winstore_kod"]))   # varijanta A/B/C ili druga dimenzija istog identa
            veze[kod] = mid
            st["povezano"] += 1
            st["po_razini"][razina] = st["po_razini"].get(razina, 0) + 1
    for s in stavke:
        cur.execute("INSERT INTO winstore_ploca (kod, materijal_kod, opis, L, W, debljina, god, kom_ukupno, kom_interno, kom_eksterno, drop_ploca, izvoz, materijal_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (s["kod"], s["materijal_kod"], s["opis"], s["L"], s["W"], s["debljina"], s["god"], s["kom_ukupno"], s["kom_interno"],
                     s["kom_eksterno"], s["drop"], izvoz, veze.get(s["materijal_kod"])))
    conn.execute("INSERT INTO postavke (kljuc, vrijednost, opis) VALUES ('winstore_izvoz', ?, 'zadnji uvezeni Winstore XML') "
                 "ON CONFLICT(kljuc) DO UPDATE SET vrijednost = excluded.vrijednost", (izvoz + " @ " + sada(),))
    dnevnik(conn, tko, "winstore_ploca", None, "uvoz", "%s: %d stavki, %d kodova, povezano %d + %d već, nepovezano %d"
            % (izvoz, st["stavke"], st["kodova"], st["povezano"], st["vec_povezano"], len(st["nepovezano"])))
    conn.commit()
    P.ocisti_kes()
    return st


def _po_identu(cur, kod, debljina):
    """Operater nestinga dio kodova piše kao Pantheon ident: IV000065-19, IV000065B-19, IV000160A-18 → materijal s tim identom,
    ako se debljina slaže (IV000065-25 nije IV000065 od 19 mm)."""
    m = re.match(r"^((?:IV|RP)\d{6})[A-Z]?(?:-(\d{1,2}(?:[,.]\d)?))?$", kod)
    if not m:
        return None
    r = cur.execute("SELECT id, debljina FROM materijal WHERE pantheon_ident = ?", (m.group(1),)).fetchone()
    if not r:
        return None
    if r["debljina"] and debljina and abs(r["debljina"] - debljina) > 0.11:
        return None
    return r["id"]


def stanje_po_kodu(conn):
    """{materijal_kod: (kom_ukupno, materijal_id)} iz zadnjeg izvoza — za ekran skladišta / nabave (D-42)."""
    out = {}
    for r in conn.execute("SELECT materijal_kod, SUM(kom_ukupno) kom, MAX(materijal_id) mid FROM winstore_ploca WHERE drop_ploca = 0 GROUP BY materijal_kod"):
        out[r["materijal_kod"]] = (r["kom"], r["mid"])
    return out
