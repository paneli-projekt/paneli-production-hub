# -*- coding: utf-8 -*-
"""Uvoz Winstore inventara (ručni XML izvoz operatera nestinga, npr. 04_STROJEVI\\NESTING\\11092026.XML; I-12) u winstore_ploca
i povezivanje MaterialCode ↔ Pantheon materijal (D-24: Hub u pozadini piše Winstore kod u SIFRA MAT za bNest).

<Item><Code>W908ST2-18-2800-2070</Code><Length>2800</Length><Width>2070</Width><Thickness>18</Thickness><Grain>0</Grain>
      <MaterialCode>W908ST2-18</MaterialCode><MaterialDescription>IVERAL BIJELI NK W908ST2 18MM</MaterialDescription>
      <Drop>0</Drop><TotalQty>2</TotalQty><InternalQty>2</InternalQty><ExternalQty>0</ExternalQty></Item>
Više Item-a može imati isti MaterialCode (više skladišnih linija / ostataka) — zbrajaju se po kodu u pogledu stanja.
Povezivanje: (0) ručna veza kod → ident koju je upisao ured (D-51, hub.sifrarnici.ispravci); (1) materijal.winstore_kod već postavljen → veza; (2) kod je Pantheon ident (IV000065-19, IV000160A-18) → taj materijal;
(3) inače prepoznavanje po MaterialDescription (vrsta + debljina + dekor + kod) → siguran pogodak upisuje winstore_kod, god i dimenziju
ploče u materijal; nesiguran ostaje nepovezan (izvještaj). Više kodova istog materijala (varijante A/B/C, druga dimenzija) vežu se
na razini winstore_ploca; materijal pamti prvi kod. Ambalažne ploče (podloge za slaganje, D-49) se ne povezuju i ne ulaze u stanje.
"""
import os
import re
import xml.etree.ElementTree as ET

from ..db import sada, dnevnik
from .nazivi import norm
from . import prepoznaj as P
from . import ispravci


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


_AMBALAZA = re.compile(r"AM+A?B+A?LAZ|(?:^| )AMB(?= |$)")   # AMBALAZA, AMABALAZA (tipfeler), ABIJELA AMBALAZA, AMB KRUNO


def je_ambalaza(opis, kod=""):
    """Podloga na koju se slažu ploče (D-49): u Winstoreu ima svoj kod (često po osobi — 111IVAN-18, STEF-19, GABI000-18),
    ali se ne kupuje ni ne naplaćuje pa se ne vodi na stanju. Hvata i tipfeler 'AMABALAZA'."""
    n = norm(opis) + " " + norm(kod)
    return bool(_AMBALAZA.search(n))


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
    st = dict(stavke=len(stavke), kodova=len({s["materijal_kod"] for s in stavke}), povezano=0, vec_povezano=0, nepovezano=[], dodatni=[], po_razini={},
              ambalaza=0, rucno=0, debljina_iz_winstorea=[])
    ambalaza = {s["materijal_kod"] for s in stavke if je_ambalaza(s["opis"], s["materijal_kod"])}
    st["ambalaza"] = len(ambalaza)
    svi = {s["materijal_kod"] for s in stavke} - ambalaza
    veze = {k: v for k, v in ispravci.veze_winstore(conn).items() if k in svi}    # ručno povezano u Hubu (D-51) — ima prednost pred prepoznavanjem
    st["rucno"] = len(veze)
    for kod, mid in veze.items():                      # ručno povezanom identu dopuni god i dimenziju ploče iz Winstorea
        s = next(x for x in stavke if x["materijal_kod"] == kod)
        cur.execute("UPDATE materijal SET god = COALESCE(god, ?), ploca_L = COALESCE(?, ploca_L), ploca_W = COALESCE(?, ploca_W) WHERE id = ?",
                    (s["god"], s["L"], s["W"], mid))
    for kod in sorted(svi - set(veze)):
        r = cur.execute("SELECT id FROM materijal WHERE UPPER(winstore_kod) = ?", (kod,)).fetchone()
        if r:
            veze[kod] = r[0]
            st["vec_povezano"] += 1
    if povezi:
        for kod in sorted(svi - set(veze)):
            s = next(x for x in stavke if x["materijal_kod"] == kod)
            mid, razina = _po_identu(cur, kod, s["debljina"]), "ident"
            if not mid:
                rez = P.prepoznaj_materijal(conn, s["opis"], debljina=s["debljina"], sirina_ploce=s["W"], winstore_kod=kod, winstore_prednost=False)
                if rez.razina in ("alias", "naziv"):
                    mid, razina = rez.id, rez.razina
                else:
                    kom = sum(x["kom_ukupno"] for x in stavke if x["materijal_kod"] == kod and not x["drop"])
                    st["nepovezano"].append((kod, s["opis"], "%s: %s" % (rez.razina, (rez.kandidati[0][0] + " " + rez.kandidati[0][1]) if rez.kandidati else "—"), kom))
                    continue
            zauzet = cur.execute("SELECT pantheon_ident, winstore_kod FROM materijal WHERE id = ?", (mid,)).fetchone()
            if zauzet["winstore_kod"] and zauzet["winstore_kod"].upper() != kod:
                st["dodatni"].append((kod, zauzet["pantheon_ident"], zauzet["winstore_kod"]))   # varijanta A/B/C ili druga dimenzija istog identa
                veze[kod] = mid
                continue
            if not zauzet["winstore_kod"]:
                cur.execute("UPDATE materijal SET winstore_kod = ?, god = COALESCE(god, ?), ploca_L = COALESCE(?, ploca_L), ploca_W = COALESCE(?, ploca_W), "
                            "trazi = trazi || ' ' || ? WHERE id = ?", (kod, s["god"], s["L"], s["W"], kod, mid))
                for m in P._materijali(conn)[0]:          # osvježi keš bez ponovnog učitavanja (1609 materijala × 400 kodova)
                    if m["id"] == mid:
                        m["winstore"] = kod
            veze[kod] = mid
            st["povezano"] += 1
            st["po_razini"][razina] = st["po_razini"].get(razina, 0) + 1
    for s in stavke:
        cur.execute("INSERT INTO winstore_ploca (kod, materijal_kod, opis, L, W, debljina, god, kom_ukupno, kom_interno, kom_eksterno, drop_ploca, izvoz, materijal_id, ambalaza) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (s["kod"], s["materijal_kod"], s["opis"], s["L"], s["W"], s["debljina"], s["god"], s["kom_ukupno"], s["kom_interno"],
                     s["kom_eksterno"], s["drop"], izvoz, veze.get(s["materijal_kod"]), 1 if s["materijal_kod"] in ambalaza else 0))
    # debljina iz Winstorea za materijale kojima je nema u Pantheon nazivu (samo ako Winstore za taj materijal zna jednu jedinu debljinu)
    for r in cur.execute("SELECT m.id, m.pantheon_ident, COUNT(DISTINCT w.debljina) n, MIN(w.debljina) d FROM materijal m JOIN winstore_ploca w ON w.materijal_id = m.id "
                         "WHERE m.debljina IS NULL AND m.ne_koristi_se = 0 AND w.debljina IS NOT NULL AND w.ambalaza = 0 GROUP BY m.id HAVING n = 1").fetchall():
        cur.execute("UPDATE materijal SET debljina = ?, debljina_izvor = 'winstore' WHERE id = ?", (r["d"], r["id"]))
        st["debljina_iz_winstorea"].append((r["pantheon_ident"], r["d"]))
    conn.execute("INSERT INTO postavke (kljuc, vrijednost, opis) VALUES ('winstore_izvoz', ?, 'zadnji uvezeni Winstore XML') "
                 "ON CONFLICT(kljuc) DO UPDATE SET vrijednost = excluded.vrijednost", (izvoz + " @ " + sada(),))
    dnevnik(conn, tko, "winstore_ploca", None, "uvoz", "%s: %d stavki, %d kodova, povezano %d + %d već + %d dodatnih, nepovezano %d, ambalaža %d, debljina iz Winstorea %d"
            % (izvoz, st["stavke"], st["kodova"], st["povezano"], st["vec_povezano"], len(st["dodatni"]), len(st["nepovezano"]), st["ambalaza"], len(st["debljina_iz_winstorea"])))
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
    """{materijal_kod: (kom_ukupno, materijal_id)} iz zadnjeg izvoza — za ekran skladišta / nabave (D-42). Ambalaža se ne vodi na stanju (D-49)."""
    out = {}
    for r in conn.execute("SELECT materijal_kod, SUM(kom_ukupno) kom, MAX(materijal_id) mid FROM winstore_ploca WHERE drop_ploca = 0 AND ambalaza = 0 GROUP BY materijal_kod"):
        out[r["materijal_kod"]] = (r["kom"], r["mid"])
    return out
