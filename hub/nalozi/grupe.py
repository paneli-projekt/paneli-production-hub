# -*- coding: utf-8 -*-
"""Mjera za rezanje i „majka“ (kralježnica korak 6; D-70 niz goda, D-79 lijepljenje, D-80 kantiranje malih komada).

Element ima KONAČNU mjeru (L, W — po njoj idu trake, kantiranje i etiketa) i MJERU ZA REZANJE (rez_L, rez_W — po njoj se slaže ploča,
piše CPO / CSV / CIX i naplaćuje materijal). Kad su iste, rez_* je NULL. Tri razloga zašto se razlikuju, sva tri primjenjuje Hub sam:

  D-80 mali komadi   kanterica ne prima komad kraći od 150 mm uz traku ni uži od 60 mm → rub kraći od 150 se reže na 150, širina ispod 60 na 60,
                     etiketa „SUZITI NA <mjera>“; 4 i više ISTIH komada kantiranih po kraćoj strani (< 150) → MAJKA: jedan veći komad
                     L × (n·s + (n−1)·kerf) koji se prvo kantira po dugim rubovima pa reže na komade (jedna majka dok stane u ploču,
                     inače više s podjednakim brojem komada)
  D-79 lijepljenje   dva sloja (sufiks `_LA1` / `_LA2` u nazivu, ili Corpusov stupac LJEPLJENJE) režu se na sirovu mjeru = konačna + 10 mm,
                     bez kanta; kant je na SKLOPU (vidljivi sloj 1) s klasom trake po Σ debljina (≤ 20 → /22, 25 → /29, 36–42 → /44);
                     lijepljenje US000007 po m² sirove mjere jednog sloja, rez na konačnu mjeru se ne naplaćuje
  D-70 niz goda      fronte s oznakom niza (`FR1_A1`, `FR11_E1H`, `FR20_C1-2`) reže se kao JEDAN veći komad (Σ + kerf pile po rezu),
                     operater ga po skici reže na fronte; trake, CNC i etikete ostaju po frontama

Majka (tablica `majka`) je grupa; element-majka (`element.vrsta = 'majka'`) je ono što ide na stroj umjesto članova (`element.majka_id`).
Sklop lijepljenja nema element-majku — na stroj idu slojevi na sirovu mjeru. Sve je izvedeno iz podataka elementa (naziv / niz / ljepljenje /
rubovi / mjere), pa se `primijeni(conn, nalog_id)` smije pozvati koliko god puta: obriše automatske majke i složi ih iznova.

    py -m hub.nalozi.grupe --db hub.db --nalog 12            (ponovno primijeni pravila i ispiši majke)
    py -m hub.nalozi.grupe --db hub.db --nalog 12 --skice C:\\tmp   (nacrtaj skice majki)
"""
import argparse
import json
import math
import re
import sys

from .. import db
from ..db import sada, dnevnik, postavka

MIN_KANT = 150.0            # najkraći rub koji kanterica kantira (D-80)
MIN_SIRINA = 60.0           # najmanja širina komada koji ide kroz kantericu po dužoj strani (D-80, 3. krug)
MIN_ZA_MAJKU = 4            # od toliko istih komada Hub radi majku (D-80)
NADMJERA_SLOJA = 10.0       # sirova mjera sloja = konačna + 10 mm (D-79, uvijek)
TRIM = 10.0                 # obrez ploče — najveća dužina majke = ploča − 2 × obrez (Igor, D-80 3. krug)
ETIKETA = 14                # znakova na etiketi (D-38)

SUFIKS_NIZ = re.compile(r"_([A-Za-z])(\d+)(H|h|-\d+)?$")                 # FR1_A1, FR11_E1H, FR20_C1-2 (23 §5)
SUFIKS_SLOJ = re.compile(r"_L([A-Za-z])(\d)$")                            # POLICA_LA1, POLICA_LA2
KONACNA_U_NAZIVU = re.compile(r"=\s*(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)")   # '2DA 2KA =930x340' (HUMER)
CORPUS_SKLOP = re.compile(r"\(I\)\s*\((\d+(?:[.,]\d+)?)\)\s*#:\s*(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)")   # ',(I) (37)#: 1465.00 x 600.00'
KUPCEVA_SKICA = re.compile(r"^\s*(SKICA|SK)\s*\.?\s*(\d+)\s*$", re.I)     # kupčev PPW: 'skica 2' = veći komad koji već sadrži fronte
MJERA_U_NAZIVU = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)\s*$")   # kupčev PPW '114X560' uz upisanih 140 × 560 = ručna nadmjera


class GrupeGreska(ValueError):
    pass


# ---------------------------------------------------------------- čitanje oznaka iz naziva
def procitaj_naziv(naziv):
    """Naziv elementa → dict(osnova, niz, sloj, konacna, corpus_sklop). niz = ('A', 1, 'V'|'H'|'G', red, stupac); sloj = ('A', 1)."""
    s = (naziv or "").strip()
    out = dict(osnova=s, niz=None, sloj=None, konacna=None, corpus_sklop=None, kupceva_skica=None)
    m = CORPUS_SKLOP.search(s)
    if m:
        deb = float(m.group(1).replace(",", "."))
        out["corpus_sklop"] = dict(debljina=deb, L=float(m.group(2)), W=float(m.group(3)))
        out["konacna"] = (float(m.group(2)), float(m.group(3)))
    m = KONACNA_U_NAZIVU.search(s)
    if m and not out["konacna"]:
        out["konacna"] = (float(m.group(1).replace(",", ".")), float(m.group(2).replace(",", ".")))
    m = SUFIKS_SLOJ.search(s)
    if m:
        out["sloj"] = (m.group(1).upper(), int(m.group(2)))
        out["osnova"] = s[:m.start()]
        return out
    m = SUFIKS_NIZ.search(s)
    if m:
        slovo, br, dod = m.group(1).upper(), int(m.group(2)), (m.group(3) or "")
        if dod.upper() == "H":
            out["niz"] = dict(slovo=slovo, rb=br, smjer="H", red=1, stupac=br, oznaka="%s%dH" % (slovo, br))
        elif dod.startswith("-"):
            out["niz"] = dict(slovo=slovo, rb=br, smjer="G", red=br, stupac=int(dod[1:]), oznaka="%s%d-%d" % (slovo, br, int(dod[1:])))
        else:
            out["niz"] = dict(slovo=slovo, rb=br, smjer="V", red=br, stupac=1, oznaka="%s%d" % (slovo, br))
        out["osnova"] = s[:m.start()]
    if KUPCEVA_SKICA.match(s):
        out["kupceva_skica"] = int(KUPCEVA_SKICA.match(s).group(2))
    return out


def procitaj_niz(oznaka):
    """'A1' | 'E1H' | 'C1-2' (kako stoji u element.niz) → dict kao u procitaj_naziv()['niz'] ili None."""
    if not oznaka:
        return None
    return procitaj_naziv("_" + oznaka.strip())["niz"]


# ---------------------------------------------------------------- D-80: pravilo za jedan komad
def pravilo_malih(L, W, kant_L, kant_W):
    """Mjera za rezanje po D-80. L, W = konačna mjera; kant_L = ima traku na rubu duž L (dužina ruba = L), kant_W = na rubu duž W.
    Rub koji se kantira mora biti ≥ 150 mm, a širina komada koji prolazi kroz kantericu ≥ 60 mm. Vraća (rez_L, rez_W, napomena|None)."""
    rez_L, rez_W = float(L), float(W)
    if kant_L:
        rez_L = max(rez_L, MIN_KANT)
        rez_W = max(rez_W, MIN_SIRINA)
    if kant_W:
        rez_W = max(rez_W, MIN_KANT)
        rez_L = max(rez_L, MIN_SIRINA)
    if rez_L == L and rez_W == W:
        return None, None, None
    if rez_L != L and rez_W != W:
        nap = "SUZITI %gx%g" % (L, W)
    else:
        nap = "SUZITI NA %g" % (L if rez_L != L else W)
    return rez_L, rez_W, nap[:ETIKETA]


def _ima_kant(e, i):
    return bool(e["rub%d_traka_id" % i] or (e["rub%d_kod" % i] or "").strip())


def _kant_po_stranama(e):
    """(kant na rubovima duž L = rub1/rub3, kant na rubovima duž W = rub2/rub4)."""
    return (_ima_kant(e, 1) or _ima_kant(e, 3)), (_ima_kant(e, 2) or _ima_kant(e, 4))


# ---------------------------------------------------------------- pomoćno
def _kerf(conn):
    return float(postavka(conn, "kerf_pile", "5") or 5)


def _ploca(conn, nm_id):
    r = conn.execute("SELECT nm.ploca_L, nm.ploca_W, nm.god, m.ploca_L AS mL, m.ploca_W AS mW, m.debljina, nm.debljina_ulaz "
                     "FROM nalog_materijal nm LEFT JOIN materijal m ON m.id = nm.materijal_id WHERE nm.id = ?", (nm_id,)).fetchone()
    return (float(r["ploca_L"] or r["mL"] or 2800), float(r["ploca_W"] or r["mW"] or 2070), bool(r["god"]), r["debljina"] or r["debljina_ulaz"])


def _elementi(conn, nm_id, vrsta="element"):
    return [dict(r) for r in conn.execute("SELECT * FROM element WHERE nalog_materijal_id = ? AND vrsta = ? ORDER BY rb, id", (nm_id, vrsta)).fetchall()]


def _novi_element_majka(conn, nm_id, majka_id, L, W, kom, naziv, god, rubovi, napomena_rez, izvor="auto"):
    """Element-majka: ono što ide na stroj umjesto članova. rubovi = [(traka_id, kod)] × 4."""
    rb = (conn.execute("SELECT COALESCE(MAX(rb), 0) FROM element WHERE nalog_materijal_id = ?", (nm_id,)).fetchone()[0] or 0) + 1
    cur = conn.execute("INSERT INTO element (nalog_materijal_id, rb, naziv, L, W, kom, god, izvor, provjeri, vrsta, majka_id, napomena_rez, "
                       "rub1_traka_id, rub1_kod, rub2_traka_id, rub2_kod, rub3_traka_id, rub3_kod, rub4_traka_id, rub4_kod) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'majka', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (nm_id, rb, naziv, float(L), float(W), int(kom), god, izvor, majka_id, napomena_rez,
                        rubovi[0][0], rubovi[0][1], rubovi[1][0], rubovi[1][1], rubovi[2][0], rubovi[2][1], rubovi[3][0], rubovi[3][1]))
    return cur.lastrowid


def _obrisi_auto(conn, nalog_id):
    """Sve što je Hub sam složio: element-majke van, članovi odvezani, mjere za rezanje (osim sloja lijepljenja) resetirane."""
    nms = [r[0] for r in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ?", (nalog_id,)).fetchall()]
    if not nms:
        return
    q = ",".join("?" * len(nms))
    conn.execute("UPDATE cix_registar SET element_id = NULL WHERE element_id IN (SELECT id FROM element WHERE nalog_materijal_id IN (%s) AND vrsta = 'majka')" % q, nms)
    conn.execute("UPDATE majka SET element_id = NULL WHERE nalog_materijal_id IN (%s)" % q, nms)
    conn.execute("DELETE FROM element WHERE nalog_materijal_id IN (%s) AND vrsta = 'majka'" % q, nms)
    conn.execute("UPDATE element SET majka_id = NULL, majka_poz = NULL, napomena_rez = NULL WHERE nalog_materijal_id IN (%s)" % q, nms)
    conn.execute("UPDATE element SET rez_L = NULL, rez_W = NULL, rez_razlog = NULL WHERE nalog_materijal_id IN (%s) AND rez_razlog IS NOT 'sloj'" % q, nms)
    conn.execute("DELETE FROM majka WHERE nalog_materijal_id IN (%s) AND izvor = 'auto'" % q, nms)


# ---------------------------------------------------------------- D-79: sklop lijepljenja
def _sklopovi(conn, nalog_id, upoz):
    """Slojevi (element.ljepljenje = 'A1', 'A2' … slovo sklopa + sloj) → majka vrste 'lijepljenje' po sklopu:
    slojevi na sirovu mjeru (rez = konačna + 10), kant samo na sloju 1 s klasom po Σ debljina, etiketa `LA1/2>1465x600`."""
    from . import nalozi as N
    grupe = {}
    for r in conn.execute("SELECT e.*, nm.nalog_id FROM element e JOIN nalog_materijal nm ON nm.id = e.nalog_materijal_id "
                          "WHERE nm.nalog_id = ? AND e.vrsta = 'element' AND e.ljepljenje IS NOT NULL AND e.ljepljenje <> '' ORDER BY nm.rb, e.rb", (nalog_id,)).fetchall():
        m = re.fullmatch(r"\s*([A-Za-z])\s*(\d)\s*", r["ljepljenje"] or "")
        if not m:
            upoz.append("element %s: oznaka lijepljenja '%s' nije oblika A1 / A2 — preskočeno" % (r["naziv"] or r["id"], r["ljepljenje"]))
            continue
        grupe.setdefault(m.group(1).upper(), []).append((int(m.group(2)), dict(r)))
    majke = []
    for slovo, slojevi in sorted(grupe.items()):
        slojevi.sort(key=lambda x: x[0])
        if len(slojevi) < 2:
            upoz.append("sklop L%s ima samo jedan sloj (%s) — nema lijepljenja; oznaku sloja maknuti ili dodati drugi sloj" % (slovo, slojevi[0][1]["naziv"]))
            continue
        # 1. sirova mjera: ono što je upisano je sirova (kupčev PPW, ručno) dok rez_razlog nije 'sloj'; Corpus već daje konačnu + sirovu (uvoz)
        for _, e in slojevi:
            if e["rez_razlog"] != "sloj":
                naz = procitaj_naziv(e["naziv"])
                kon = naz["konacna"]
                if kon and abs(kon[0] - (e["L"] - NADMJERA_SLOJA)) + abs(kon[1] - (e["W"] - NADMJERA_SLOJA)) > 0.6 \
                        and abs(kon[1] - (e["L"] - NADMJERA_SLOJA)) + abs(kon[0] - (e["W"] - NADMJERA_SLOJA)) > 0.6:
                    upoz.append("sklop %s, %s: konačna mjera u nazivu %gx%g nije sirova − 10 (%gx%g) — uzeta je sirova − 10, provjeriti"
                                % (slovo, e["naziv"], kon[0], kon[1], e["L"] - NADMJERA_SLOJA, e["W"] - NADMJERA_SLOJA))
                conn.execute("UPDATE element SET rez_L = L, rez_W = W, L = L - ?, W = W - ?, rez_razlog = 'sloj' WHERE id = ?",
                             (NADMJERA_SLOJA, NADMJERA_SLOJA, e["id"]))
                e["rez_L"], e["rez_W"], e["L"], e["W"], e["rez_razlog"] = e["L"], e["W"], e["L"] - NADMJERA_SLOJA, e["W"] - NADMJERA_SLOJA, "sloj"
        prvi = slojevi[0][1]
        provjeri, nap = 0, []
        brojevi = [s for s, _ in slojevi]
        if brojevi != list(range(1, len(slojevi) + 1)):
            provjeri, nap = 1, nap + ["slojevi %s nisu 1..n" % brojevi]
        if any(abs(e["L"] - prvi["L"]) > 0.6 or abs(e["W"] - prvi["W"]) > 0.6 for _, e in slojevi):
            provjeri, nap = 1, nap + ["slojevi nemaju istu mjeru"]
        if any(int(e["kom"]) != int(prvi["kom"]) for _, e in slojevi):
            provjeri, nap = 1, nap + ["slojevi nemaju istu količinu"]
        debljine = [_ploca(conn, e["nalog_materijal_id"])[3] for _, e in slojevi]
        deb = round(sum(d for d in debljine if d), 1) if all(debljine) else None
        if deb is None:
            provjeri, nap = 1, nap + ["debljina sloja nepoznata — klasa trake nije određena"]
        cur = conn.execute("INSERT INTO majka (nalog_materijal_id, vrsta, oznaka, smjer, element_id, L, W, debljina, kerf, clanova, komada, skica_json, napomena, provjeri, izvor, kada) "
                           "VALUES (?, 'lijepljenje', ?, NULL, NULL, ?, ?, ?, NULL, ?, ?, ?, ?, ?, 'auto', ?)",
                           (prvi["nalog_materijal_id"], "L" + slovo, prvi["L"], prvi["W"], deb, len(slojevi), int(prvi["kom"]),
                            json.dumps(dict(slojevi=[dict(element_id=e["id"], sloj=s, L=e["L"], W=e["W"], rez_L=e["rez_L"], rez_W=e["rez_W"],
                                                          nalog_materijal_id=e["nalog_materijal_id"], debljina=d) for (s, e), d in zip(slojevi, debljine)])),
                            "; ".join(nap) or None, provjeri, sada()))
        mid = cur.lastrowid
        for s, e in slojevi:
            et = ("L%s%d/%d>%gx%g" % (slovo, s, len(slojevi), prvi["L"], prvi["W"]))[:ETIKETA]
            conn.execute("UPDATE element SET majka_id = ?, majka_poz = ?, napomena_rez = ? WHERE id = ?", (mid, str(s), et, e["id"]))
            if s > 1:                       # kant je na sklopu = vidljivi sloj; s donjih slojeva se skida (Corpus ga stavi na oba — D-79)
                conn.execute("UPDATE element SET rub1_traka_id = NULL, rub1_kod = NULL, rub2_traka_id = NULL, rub2_kod = NULL, rub3_traka_id = NULL, rub3_kod = NULL, "
                             "rub4_traka_id = NULL, rub4_kod = NULL, provjeri = 0 WHERE id = ?", (e["id"],))
        if deb:                             # klasa trake sloja 1 po debljini sklopa (≤ 20 → /22, 25 → /29, 36–42 → /44)
            mat = conn.execute("SELECT materijal_id FROM nalog_materijal WHERE id = ?", (prvi["nalog_materijal_id"],)).fetchone()[0]
            N._prepoznaj_rubove_elementa(conn, prvi["id"], mat, debljina=deb)
        majke.append(mid)
        if provjeri:
            upoz.append("sklop L%s: %s" % (slovo, "; ".join(nap)))
    return majke


# ---------------------------------------------------------------- D-70: niz goda
def _nizovi(conn, nm_id, kerf, upoz):
    """Elementi s oznakom niza (element.niz) → majka vrste 'niz' po slovu: veći komad Σ + kerf po rezu, članovi ostaju (trake, CNC, etiketa A2/3)."""
    grupe = {}
    for e in _elementi(conn, nm_id):
        if e["majka_id"] or not e["niz"]:
            continue
        n = procitaj_niz(e["niz"])
        if not n:
            upoz.append("element %s: oznaka niza '%s' nije oblika A1 / E1H / C1-2" % (e["naziv"] or e["id"], e["niz"]))
            continue
        grupe.setdefault(n["slovo"], []).append((n, e))
    pL, pW, god_mat, _ = _ploca(conn, nm_id)
    majke = []
    for slovo, clanovi in sorted(grupe.items()):
        if len(clanovi) < 2:
            upoz.append("niz %s ima samo jedan element (%s) — nema majke" % (slovo, clanovi[0][1]["naziv"]))
            continue
        smjerovi = {n["smjer"] for n, _ in clanovi}
        smjer = "G" if "G" in smjerovi else ("H" if "H" in smjerovi else "V")
        provjeri, nap = 0, []
        if len(smjerovi) > 1:
            provjeri, nap = 1, nap + ["miješani smjerovi u oznakama (%s)" % ", ".join(sorted(smjerovi))]
        kom = int(clanovi[0][1]["kom"])
        if any(int(e["kom"]) != kom for _, e in clanovi):
            provjeri, nap = 1, nap + ["fronte niza nemaju istu količinu"]
        # raspored: red = položaj uz god (L), stupac = položaj poprijeko (W); V: red = rb; H: stupac = rb; G: red-stupac
        polozaji = {}
        for n, e in clanovi:
            red, stupac = (n["rb"], 1) if smjer == "V" else ((1, n["rb"]) if smjer == "H" else (n["red"], n["stupac"]))
            if (red, stupac) in polozaji:
                provjeri, nap = 1, nap + ["dvije fronte na položaju %d-%d" % (red, stupac)]
            polozaji[(red, stupac)] = (n, e)
        redovi = sorted({r for r, _ in polozaji})
        stupci = sorted({s for _, s in polozaji})
        if redovi != list(range(1, len(redovi) + 1)) or stupci != list(range(1, len(stupci) + 1)):
            provjeri, nap = 1, nap + ["brojevi u nizu nisu 1..n bez rupa"]
        vis_reda = {r: max(e["L"] for (rr, _), (n, e) in polozaji.items() if rr == r) for r in redovi}
        sir_stupca = {s: max(e["W"] for (_, ss), (n, e) in polozaji.items() if ss == s) for s in stupci}
        L = sum(vis_reda.values()) + kerf * (len(redovi) - 1)
        W = sum(sir_stupca.values()) + kerf * (len(stupci) - 1)
        if smjer == "V" and len({round(e["W"], 1) for _, e in clanovi}) > 1:
            nap.append("fronte nemaju istu širinu — majka je najšira")
        if smjer == "H" and len({round(e["L"], 1) for _, e in clanovi}) > 1:
            nap.append("fronte nemaju istu visinu — majka je najviša")
        if L > pL - 2 * TRIM or W > pW - 2 * TRIM:
            provjeri, nap = 1, nap + ["majka %gx%g ne stane u ploču %gx%g (obrez %g) — podijeliti niz" % (L, W, pL, pW, TRIM)]
        clanovi_json, x = [], 0.0                       # x = uz L majke (redovi = visine fronti uz god), y = uz W majke (stupci = širine)
        for r in redovi:
            y = 0.0
            for s in stupci:
                if (r, s) in polozaji:
                    n, e = polozaji[(r, s)]
                    clanovi_json.append(dict(element_id=e["id"], poz=n["oznaka"], x=x, y=y, L=e["L"], W=e["W"], naziv=e["naziv"], kom=int(e["kom"])))
                y += sir_stupca[s] + kerf
            x += vis_reda[r] + kerf
        god = clanovi[0][1]["god"]
        cur = conn.execute("INSERT INTO majka (nalog_materijal_id, vrsta, oznaka, smjer, element_id, L, W, debljina, kerf, clanova, komada, skica_json, napomena, provjeri, izvor, kada) "
                           "VALUES (?, 'niz', ?, ?, NULL, ?, ?, NULL, ?, ?, ?, ?, ?, ?, 'auto', ?)",
                           (nm_id, slovo, smjer, L, W, kerf, len(clanovi), len(clanovi) * kom,
                            json.dumps(dict(L=L, W=W, kerf=kerf, smjer=smjer, clanovi=clanovi_json)), "; ".join(nap) or None, provjeri, sada()))
        mid = cur.lastrowid
        eid = _novi_element_majka(conn, nm_id, mid, L, W, kom, "NIZ %s (%d fronti)" % (slovo, len(clanovi)), god, [(None, None)] * 4,
                                  ("NIZ %s (%d)" % (slovo, len(clanovi)))[:ETIKETA])
        conn.execute("UPDATE majka SET element_id = ? WHERE id = ?", (eid, mid))
        for n, e in clanovi:
            conn.execute("UPDATE element SET majka_id = ?, majka_poz = ?, napomena_rez = ? WHERE id = ?",
                         (mid, n["oznaka"], ("%s/%d" % (n["oznaka"], len(clanovi)))[:ETIKETA], e["id"]))
        majke.append(mid)
        if nap:
            upoz.append("niz %s: %s" % (slovo, "; ".join(nap)))
    return majke


# ---------------------------------------------------------------- D-80: majka malih komada + pojedinačna nadmjera
def _kljuc_istih(e):
    return (round(e["L"], 1), round(e["W"], 1), e["god"] or "", tuple((e["rub%d_traka_id" % i], (e["rub%d_kod" % i] or "").strip().upper()) for i in range(1, 5)))


def _majke_malih(conn, nm_id, kerf, upoz):
    """4+ istih komada kantiranih po kraćoj strani < 150 → majka L × (n·s + (n−1)·kerf): dugi rubovi majke = kratki rubovi komada
    (kantiraju se na majci), komad se nakon rezanja kantira po svojim dugim rubovima kao dosad."""
    pL, pW, god_mat, _ = _ploca(conn, nm_id)
    kandidati = {}
    for e in _elementi(conn, nm_id):
        if e["majka_id"] or e["rez_razlog"] == "sloj":
            continue
        kant_L, kant_W = _kant_po_stranama(e)
        s, l = min(e["L"], e["W"]), max(e["L"], e["W"])
        kant_kratki = kant_W if e["L"] >= e["W"] else kant_L
        kant_dugi = kant_L if e["L"] >= e["W"] else kant_W
        if not (kant_kratki and s < MIN_KANT):
            continue
        if kant_dugi and s < MIN_SIRINA:
            continue                                     # komad uži od 60 kantiran i po dugoj strani: majka mu ne pomaže — ide pojedinačno
        kandidati.setdefault(_kljuc_istih(e), []).append(e)
    majke = []
    br = conn.execute("SELECT COUNT(*) FROM majka WHERE nalog_materijal_id = ? AND vrsta = 'mali'", (nm_id,)).fetchone()[0]
    for k, els in kandidati.items():
        n = sum(int(e["kom"]) for e in els)
        if n < MIN_ZA_MAJKU:
            continue
        e0 = els[0]
        s, l = min(e0["L"], e0["W"]), max(e0["L"], e0["W"])
        god = bool(e0["god"]) or god_mat
        kratki_uz_L = e0["L"] < e0["W"]                            # kraća strana je L (uz god) → komadi se slažu uz L ploče
        if god:
            granica = (pL if kratki_uz_L else pW) - 2 * TRIM       # stog uz god ide uz duljinu ploče (2780), poprijeko uz širinu (2050)
        else:
            granica = max(pL, pW) - 2 * TRIM
        po_majci = max(1, int((granica + kerf) // (s + kerf)))
        k_majki = int(math.ceil(n / po_majci))
        osnova, visak = divmod(n, k_majki)
        velicine = [osnova + (1 if i < visak else 0) for i in range(k_majki)]     # podjednak broj komada (7 → 4 + 3, 30 → 15 + 15)
        br += 1
        oznaka = "M%d" % br
        kratki = (2, 4) if e0["L"] >= e0["W"] else (1, 3)          # rubovi komada duž kraće strane → dugi rubovi majke
        rub_kratki = [(e0["rub%d_traka_id" % i], e0["rub%d_kod" % i]) for i in kratki]
        provjeri, nap = 0, []
        if any(e["cix_ime"] or e["program1"] for e in els):
            provjeri, nap = 1, nap + ["komadi imaju CNC program — obrada na komadu nakon rezanja iz majke, provjeriti"]
        cur = conn.execute("INSERT INTO majka (nalog_materijal_id, vrsta, oznaka, smjer, element_id, L, W, debljina, kerf, clanova, komada, skica_json, napomena, provjeri, izvor, kada) "
                           "VALUES (?, 'mali', ?, ?, NULL, NULL, NULL, NULL, ?, ?, ?, ?, ?, ?, 'auto', ?)",
                           (nm_id, oznaka, "L" if (god and kratki_uz_L) or (not god) else "W", kerf, len(els), n, None, "; ".join(nap) or None, provjeri, sada()))
        mid = cur.lastrowid
        majke_el, skice = [], []
        for vel, kom_majki in sorted(((v, velicine.count(v)) for v in set(velicine)), reverse=True):
            stog = vel * s + (vel - 1) * kerf
            if (god and not kratki_uz_L) or (not god and stog <= l):
                L, W, rub = l, stog, [(None, None), rub_kratki[0], (None, None), rub_kratki[1]]       # stog poprijeko: rubovi majke rub2 / rub4
            else:
                L, W, rub = stog, l, [rub_kratki[0], (None, None), rub_kratki[1], (None, None)]       # stog uz L: rubovi majke rub1 / rub3
            et = ("%s %dx%gx%g" % (oznaka, vel, l, s))[:ETIKETA]
            eid = _novi_element_majka(conn, nm_id, mid, L, W, kom_majki, "MAJKA %s (%d x %gx%g)" % (oznaka, vel, l, s), e0["god"], rub, et)
            majke_el.append(eid)
            clanovi = []
            for i in range(vel):
                off = i * (s + kerf)
                clanovi.append(dict(poz="%d" % (i + 1), x=0 if W == stog else off, y=off if W == stog else 0, L=l if W == stog else s, W=s if W == stog else l))
            skice.append(dict(element_id=eid, L=L, W=W, komada=vel, majki=kom_majki, clanovi=clanovi))
        conn.execute("UPDATE majka SET element_id = ?, L = ?, W = ?, skica_json = ? WHERE id = ?",
                     (majke_el[0], skice[0]["L"], skice[0]["W"],
                      json.dumps(dict(kerf=kerf, komad=dict(L=l, W=s), rub_kratki=[k for _, k in rub_kratki], majke=skice,
                                      clanovi_elementi=[e["id"] for e in els])), mid))
        for e in els:
            conn.execute("UPDATE element SET majka_id = ?, majka_poz = 'clan', napomena_rez = ? WHERE id = ?", (mid, ("IZ %s" % oznaka)[:ETIKETA], e["id"]))
        majke.append(mid)
        if nap:
            upoz.append("majka %s: %s" % (oznaka, "; ".join(nap)))
    return majke


def _pojedinacno(conn, nm_id, upoz):
    """D-80 za komade koji nisu u majci: rez na 150 / 60 + etiketa 'SUZITI NA'."""
    n = 0
    for e in _elementi(conn, nm_id):
        if e["majka_id"] and e["rez_razlog"] != "sloj":
            continue
        kant_L, kant_W = _kant_po_stranama(e)
        rez_L, rez_W, nap = pravilo_malih(e["L"], e["W"], kant_L, kant_W)
        if rez_L is None:
            continue
        if e["rez_razlog"] == "sloj":
            # sloj lijepljenja: sirova mjera je već konačna + 10; ako ni to nije dovoljno za kantericu, sirova raste, etiketa ostaje sloja
            if rez_L > e["rez_L"] or rez_W > e["rez_W"]:
                conn.execute("UPDATE element SET rez_L = ?, rez_W = ? WHERE id = ?", (max(rez_L, e["rez_L"]), max(rez_W, e["rez_W"]), e["id"]))
                upoz.append("sloj %s (%gx%g): kraći od 150 uz traku — sirova mjera povećana, nakon lijepljenja suziti na %gx%g" % (e["naziv"], e["L"], e["W"], e["L"], e["W"]))
            continue
        conn.execute("UPDATE element SET rez_L = ?, rez_W = ?, rez_razlog = 'suziti', napomena_rez = ? WHERE id = ?", (rez_L, rez_W, nap, e["id"]))
        n += 1
    return n


# ---------------------------------------------------------------- glavno
def primijeni(conn, nalog_id, tko="sustav", commit=True):
    """Ponovno izvedi sve majke i mjere za rezanje naloga iz podataka elemenata (idempotentno). Vraća izvještaj."""
    from . import nalozi as N
    n = N.nalog(conn, nalog_id)
    if n["status"] not in ("unos", "ponuda"):
        return dict(nalog_id=nalog_id, preskoceno="nalog u statusu '%s' — elementi se ne mijenjaju" % n["status"], majke=pregled(conn, nalog_id), upozorenja=[])
    upoz = []
    _obrisi_auto(conn, nalog_id)
    kerf = _kerf(conn)
    majke = _sklopovi(conn, nalog_id, upoz)
    suzeno = 0
    for (nm_id,) in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? ORDER BY rb, id", (nalog_id,)).fetchall():
        majke += _nizovi(conn, nm_id, kerf, upoz)
        majke += _majke_malih(conn, nm_id, kerf, upoz)
        suzeno += _pojedinacno(conn, nm_id, upoz)
    for e in conn.execute("SELECT e.id, e.naziv, e.L, e.W, e.rez_razlog FROM element e JOIN nalog_materijal nm ON nm.id = e.nalog_materijal_id WHERE nm.nalog_id = ? AND e.vrsta = 'element'", (nalog_id,)).fetchall():
        sk = procitaj_naziv(e["naziv"])["kupceva_skica"]
        if sk:
            upoz.append("element '%s' je kupčev veći komad s frontama na skici — fronte se upisuju kroz 'niz iz kupčeve majke' (D-70)" % e["naziv"])
        m = MJERA_U_NAZIVU.match(e["naziv"] or "")
        if m and e["rez_razlog"] == "suziti":
            a, b = float(m.group(1)), float(m.group(2))
            if {a, b} != {e["L"], e["W"]} and ((a < e["L"] and b == e["W"]) or (a == e["L"] and b < e["W"]) or (b < e["L"] and a == e["W"]) or (b == e["L"] and a < e["W"])):
                upoz.append("element '%s' upisan %gx%g: naziv izgleda kao KONAČNA mjera — nadmjera za kantericu je već dodana ručno? Upisati konačnu mjeru, Hub sam dodaje nadmjeru (D-80)"
                            % (e["naziv"], e["L"], e["W"]))
    if majke or suzeno:
        dnevnik(conn, tko, "nalog", nalog_id, "grupe", "%d majki / sklopova, %d komada s nadmjerom za kantericu" % (len(majke), suzeno))
    if commit:
        conn.commit()
    return dict(nalog_id=nalog_id, majke=pregled(conn, nalog_id), suzeno=suzeno, upozorenja=list(dict.fromkeys(upoz)))


def pregled(conn, nalog_id):
    """Majke i sklopovi naloga s članovima (za ekran, ispis i testove)."""
    out = []
    for m in conn.execute("SELECT mk.*, nm.nalog_id FROM majka mk JOIN nalog_materijal nm ON nm.id = mk.nalog_materijal_id WHERE nm.nalog_id = ? ORDER BY mk.id", (nalog_id,)).fetchall():
        d = dict(m)
        d["skica"] = json.loads(d.pop("skica_json") or "{}")
        d["clanovi"] = [dict(r) for r in conn.execute("SELECT id, naziv, L, W, kom, rez_L, rez_W, rez_razlog, majka_poz, napomena_rez, cix_ime, nalog_materijal_id "
                                                       "FROM element WHERE majka_id = ? AND vrsta = 'element' ORDER BY rb, id", (m["id"],)).fetchall()]
        d["elementi_majke"] = [dict(r) for r in conn.execute("SELECT id, naziv, L, W, kom, napomena_rez, rub1_kod, rub2_kod, rub3_kod, rub4_kod FROM element "
                                                              "WHERE majka_id = ? AND vrsta = 'majka' ORDER BY rb, id", (m["id"],)).fetchall()]
        out.append(d)
    return out


def majka(conn, majka_id):
    m = conn.execute("SELECT mk.*, nm.nalog_id FROM majka mk JOIN nalog_materijal nm ON nm.id = mk.nalog_materijal_id WHERE mk.id = ?", (majka_id,)).fetchone()
    if not m:
        raise GrupeGreska("majka %s ne postoji" % majka_id)
    for d in pregled(conn, m["nalog_id"]):
        if d["id"] == majka_id:
            return d
    return None


def clanovi_s_cix(conn, nm_id):
    """Elementi-članovi majki (niz / mali) tog materijala koji imaju Corpusov CIX — ne nestaju se, program ide na Rover na izrezanom komadu."""
    return [dict(r) for r in conn.execute("SELECT e.*, mk.vrsta AS majka_vrsta, mk.oznaka AS majka_oznaka FROM element e JOIN majka mk ON mk.id = e.majka_id "
                                          "WHERE e.nalog_materijal_id = ? AND e.vrsta = 'element' AND mk.vrsta IN ('niz', 'mali') AND e.cix_izvor = 'corpus' AND e.obrada_json IS NOT NULL "
                                          "ORDER BY e.rb", (nm_id,)).fetchall()]


# ---------------------------------------------------------------- niz iz kupčeve majke (kupčev PPW 'skica N')
def niz_iz_kupceve_majke(conn, element_id, fronte, tko="web", smjer="V"):
    """Kupčev PPW već nosi VEĆI komad ('skica 2', 817 × 497 × 3): ured upiše fronte [(L, W, rubovi{L,O,D,G}, naziv?)…] uz god redom,
    Hub ih otvori kao članove niza, kupčev element postane element-majka i usporedi mjeru s izračunatom (Σ + kerf)."""
    from . import nalozi as N
    e = N.element(conn, element_id)
    nm = N.materijal_naloga(conn, e["nalog_materijal_id"])
    if N.nalog(conn, nm["nalog_id"])["status"] not in ("unos", "ponuda"):
        raise GrupeGreska("elementi se mijenjaju samo u statusu unos / ponuda")
    if e["vrsta"] != "element" or e["majka_id"]:
        raise GrupeGreska("element %s je već majka ili član" % element_id)
    if len(fronte) < 2:
        raise GrupeGreska("niz treba barem dvije fronte")
    kerf = _kerf(conn)
    slova = {r[0] for r in conn.execute("SELECT oznaka FROM majka WHERE nalog_materijal_id = ? AND vrsta = 'niz'", (nm["id"],)).fetchall()}
    slovo = next(c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in slova)
    ids = []
    for i, f in enumerate(fronte, 1):
        oz = "%s%d%s" % (slovo, i, "H" if smjr(smjer) == "H" else "")
        el = N.dodaj_element(conn, nm["id"], tko, f["L"], f["W"], e["kom"], naziv=(f.get("naziv") or "%s_%s" % (procitaj_naziv(e["naziv"])["osnova"] or "FRONTA", oz)),
                             rubovi=f.get("rubovi") or {}, god=e["god"], napomena=f.get("napomena"), izvor="rucno", grupe=False)
        conn.execute("UPDATE element SET niz = ? WHERE id = ?", (oz, el["id"]))
        ids.append(el["id"])
    if smjr(smjer) == "V":
        L, W = sum(f["L"] for f in fronte) + kerf * (len(fronte) - 1), max(f["W"] for f in fronte)
    else:
        L, W = max(f["L"] for f in fronte), sum(f["W"] for f in fronte) + kerf * (len(fronte) - 1)
    razlika = None
    if abs(L - e["L"]) > 0.6 or abs(W - e["W"]) > 0.6:
        razlika = "kupčev komad %gx%g, Hub računa %gx%g (Σ fronti + %g mm po rezu) — provjeriti skicu" % (e["L"], e["W"], L, W, kerf)
    # kupčev veći komad više nije samostalan element: obriše se, majku Hub složi iz fronti (mjera po Hubu; razlika se javi)
    conn.execute("UPDATE cix_registar SET element_id = NULL WHERE element_id = ?", (element_id,))
    conn.execute("DELETE FROM element WHERE id = ?", (element_id,))
    dnevnik(conn, tko, "element", element_id, "niz_iz_kupceve_majke", "%s → niz %s (%d fronti)%s" % (e["naziv"], slovo, len(fronte), (": " + razlika) if razlika else ""))
    r = primijeni(conn, nm["nalog_id"], tko)
    if razlika:
        r["upozorenja"].append(razlika)
    r["niz"] = slovo
    r["element_ids"] = ids
    return r


def smjr(s):
    return "H" if (s or "V").upper().startswith("H") else "V"


# ---------------------------------------------------------------- CIX s povećanom mjerom (D-80: Corpus daje točnu mjeru, nadmjeru dodaje Hub)
_LP = re.compile(r"^(\s*LP([XY])\s*=\s*)([0-9.]+)", re.M)


def kopiraj_cix_prosiren(put, cilj, L_kon, W_kon, rez_L, rez_W):
    """Corpusov CIX kopiraj s LPX / LPY povećanim na mjeru za rezanje — ishodište ostaje, obrade ostaju na mjestu, višak je na strani
    suprotnoj od ishodišta i suzi se nakon kantiranja. Vraća (promijenjeno: bool, upozorenje | None)."""
    import shutil
    txt = open(put, "rb").read().decode("utf-8", "replace")
    vr = {m.group(2): float(m.group(3)) for m in _LP.finditer(txt)}
    if "X" not in vr or "Y" not in vr:
        shutil.copyfile(put, cilj)
        return False, "%s: nema LPX/LPY — kopiran nepromijenjen" % put
    if abs(vr["X"] - L_kon) < 0.6 and abs(vr["Y"] - W_kon) < 0.6:
        novo = dict(X=rez_L, Y=rez_W)
    elif abs(vr["X"] - W_kon) < 0.6 and abs(vr["Y"] - L_kon) < 0.6:
        novo = dict(X=rez_W, Y=rez_L)
    else:
        shutil.copyfile(put, cilj)
        return False, "%s: LPX/LPY %gx%g nisu mjere elementa %gx%g — kopiran nepromijenjen" % (put, vr["X"], vr["Y"], L_kon, W_kon)
    txt = _LP.sub(lambda m: "%s%g" % (m.group(1), novo[m.group(2)]), txt)
    open(cilj, "wb").write(txt.encode("utf-8"))
    return True, None


def skice_materijala(conn, nm_id, mapa, osnova):
    """Nacrtaj skice svih majki materijala uz CPO / CSV: `<osnova>_MAJKA_<oznaka>.png`. Vraća [dict(majka_id, oznaka, vrsta, png)]."""
    import os
    out = []
    for m in conn.execute("SELECT id, oznaka, vrsta FROM majka WHERE nalog_materijal_id = ? AND vrsta IN ('niz', 'mali') ORDER BY id", (nm_id,)).fetchall():
        png = skica_png(conn, m["id"], os.path.join(mapa, "%s_MAJKA_%s.png" % (osnova, m["oznaka"])))
        if png:
            out.append(dict(majka_id=m["id"], oznaka=m["oznaka"], vrsta=m["vrsta"], png=png))
    return out


# ---------------------------------------------------------------- skica majke (PNG, kao sheme.py)
def skica_png(conn, majka_id, put, dpi=90):
    """Nacrtaj majku s članovima (rezovi, mjere, oznake) — za operatera uz CPO / CSV i za ekran. Vraća put ili None bez matplotliba."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except ImportError:
        return None
    m = majka(conn, majka_id)
    sk = m["skica"]
    ploce = []
    if m["vrsta"] == "niz":
        ploce.append(dict(L=sk["L"], W=sk["W"], clanovi=sk["clanovi"], naslov="NIZ %s — %d fronti, kerf %g mm, smjer %s" % (m["oznaka"], m["clanova"], sk["kerf"], sk["smjer"])))
    elif m["vrsta"] == "mali":
        for mj in sk["majke"]:
            ploce.append(dict(L=mj["L"], W=mj["W"], clanovi=mj["clanovi"], naslov="MAJKA %s — %d komada %gx%g, %d× (kerf %g mm); kant dugih rubova na majci: %s"
                              % (m["oznaka"], mj["komada"], sk["komad"]["L"], sk["komad"]["W"], mj["majki"], sk["kerf"], " / ".join(k for k in sk["rub_kratki"] if k) or "—")))
    else:
        ploce.append(dict(L=m["L"], W=m["W"], clanovi=[dict(poz="sloj %d" % s["sloj"], x=0, y=0, L=s["L"], W=s["W"]) for s in sk["slojevi"]],
                          naslov="SKLOP %s — %d slojeva, konačna %gx%g, %s mm" % (m["oznaka"], m["clanova"], m["L"], m["W"], m["debljina"] or "?")))
    fig, axes = plt.subplots(len(ploce), 1, figsize=(11, 4 * len(ploce)))
    if len(ploce) == 1:
        axes = [axes]
    for ax, p in zip(axes, ploce):
        ax.add_patch(Rectangle((0, 0), p["L"], p["W"], fill=False, lw=2, ec="#333"))
        for c in p["clanovi"]:
            ax.add_patch(Rectangle((c["x"], c["y"]), c["L"], c["W"], fc="#eef2f6", ec="#1f3a5f", lw=1))
            ax.text(c["x"] + c["L"] / 2, c["y"] + c["W"] / 2, "%s\n%g x %g%s" % (c["poz"], c["L"], c["W"], ("\n" + (c.get("naziv") or "")[:16]) if c.get("naziv") else ""),
                    ha="center", va="center", fontsize=8 if min(c["L"], c["W"]) > 100 else 6)
        ax.set_xlim(-40, p["L"] + 40)
        ax.set_ylim(-40, p["W"] + 40)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title("%s   majka %g x %g" % (p["naslov"], p["L"], p["W"]), fontsize=9)
    fig.tight_layout()
    fig.savefig(put, dpi=dpi)
    plt.close(fig)
    return put


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mjera za rezanje i majke (korak 6: D-70 / D-79 / D-80)")
    ap.add_argument("--db")
    ap.add_argument("--nalog", type=int, required=True)
    ap.add_argument("--skice", help="mapa u koju se nacrtaju skice majki (PNG)")
    ap.add_argument("--tko", default="cli")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    try:
        r = primijeni(conn, a.nalog, a.tko)
    except GrupeGreska as e:
        print("GRESKA:", e)
        return 1
    if r.get("preskoceno"):
        print("PAZI:", r["preskoceno"])
    for m in r["majke"]:
        print("%-12s %-4s %-3s %8s x %-8s clanova %d  komada %d%s" % (m["vrsta"], m["oznaka"], m["smjer"] or "", m["L"], m["W"], m["clanova"], m["komada"],
                                                                     "  PROVJERI: " + (m["napomena"] or "") if m["provjeri"] else ""))
        for c in m["clanovi"]:
            print("      %-6s %-28s %gx%g x%d%s  [%s]" % (c["majka_poz"] or "", (c["naziv"] or "")[:28], c["L"], c["W"], c["kom"],
                                                        ("  rez %gx%g" % (c["rez_L"], c["rez_W"])) if c["rez_L"] else "", c["napomena_rez"] or ""))
        if a.skice:
            import os
            p = skica_png(conn, m["id"], os.path.join(a.skice, "majka_%s_%d.png" % (m["oznaka"], m["id"])))
            print("      skica:", p or "(nema matplotliba)")
    print("komada s nadmjerom za kantericu (SUZITI NA): %d" % r.get("suzeno", 0))
    for u in r["upozorenja"]:
        print("PAZI:", u)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
