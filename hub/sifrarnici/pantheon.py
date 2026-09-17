# -*- coding: utf-8 -*-
"""Uvoz Pantheon šifrarnika identa (ph_identi.csv iz IzvozPantheon_v2.ps1, D-06) u tablice pantheon_ident, materijal i traka.

Pravila (CLAUDE.md + 04 §2):
- ph_identi.csv zna sadržavati NUL bajtove → očistiti prije csv modula; kodiranje utf-8-sig ili cp1250; separator ';'.
- Materijali = identi IV* (iveral, MDF, PVC, akril, HPL, compact, šperploča…) i RP* (radne ploče, ploče stola, zidne ploče).
- Trake = identi TR* + identi drugih prefiksa čiji naziv počinje s 'ABS' (OK004510, US000558, OK002749 — poznate iznimke).
- Cijena: anSalePrice (s PDV-om) i anRTPrice (neto = / 1,25) — u Hubu se ne mijenjaju (D-40).
Uvoz je idempotentan: ponovni uvoz osvježava nazive/cijene/aktivnost, ne briše veze (aliasi, winstore_kod, materijal_traka).
Ident koji više nije ploča / traka (D-53: 'TRAKA ZA R.P.' pod RP identom; preimenovan ili obrisan u Pantheonu) izlazi iz
šifrarnika: briše se ako ga ništa ne koristi, inače se označi 'ne koristi se' + neaktivan pa ga Hub više ne nudi.
"""
import csv
import io
import os

from ..db import sada, dnevnik
from .nazivi import rasclani_materijal, rasclani_traku_pantheon, naziv_kratki, norm, norm_prikaz

PLOCA_ZADANO = {  # zadane dimenzije ploče po vrsti (mm) dok Winstore ne kaže drukčije (skill krojna-ponuda STANDARD_DIMS)
    "IV": (2800, 2070), "MDF": (2800, 2070), "PVC": (2800, 1220), "AK": (2800, 1220), "HPL": (2800, 2070),
    "CP": (4200, 1300), "SP": (2500, 1250), "RP": (4100, 600), "ZO": (4100, 640), "OST": (None, None),
}
SIRINA_RP = {"radna": 600, "stola": 900, "zidna": 640}


def ucitaj_ph_identi(putanja):
    """Redovi ph_identi.csv kao dict-ovi (NUL bajtovi uklonjeni, kodiranje prepoznato)."""
    raw = open(putanja, "rb").read().replace(b"\x00", b"")
    for enc in ("utf-8-sig", "cp1250"):
        try:
            txt = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        txt = raw.decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(txt), delimiter=";"))


def _broj(x):
    try:
        return float(str(x).replace(",", ".")) if x not in (None, "") else None
    except ValueError:
        return None


def je_materijal(r):
    """IV* i RP* identi su ploče — osim onih koji su u Pantheonu krivo klasificirani: 'TRAKA ZA R.P. …' pod RP identom nije ploča (D-53)."""
    ident, n = r["acIdent"], norm(r["acName"])
    return (ident.startswith("IV") or ident.startswith("RP")) and n not in ("", "PRAZNO") and not n.startswith("TRAKA")


def je_traka(r):
    ident = r["acIdent"]
    n = norm(r["acName"])
    if ident.startswith("TR"):
        return n not in ("", "PRAZNO") and not n.startswith("IVERAL")   # TR000142 / TR001255 / TR001315 su ploče otvorene pod TR
    return n.startswith("ABS ")


def uvezi_pantheon(conn, putanja, tko="uvoz"):
    """Upiše/osvježi sve idente, izvede materijale i trake. Vraća statistiku."""
    rows = ucitaj_ph_identi(putanja)
    kada = sada()
    st = dict(identi=0, materijali=0, trake=0, novi_materijali=0, nove_trake=0, izbaceni_materijali=0, izbacene_trake=0)
    cur = conn.cursor()
    identi_materijala, identi_traka = set(), set()
    for r in rows:
        ident = (r.get("acIdent") or "").strip()
        if not ident:
            continue
        cur.execute(
            "INSERT INTO pantheon_ident (ident, naziv, klasif, kod, dobavljac, jm, cijena_prodajna, cijena_neto, pdv, aktivan, azurirano) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(ident) DO UPDATE SET naziv = excluded.naziv, klasif = excluded.klasif, "
            "kod = excluded.kod, dobavljac = excluded.dobavljac, jm = excluded.jm, cijena_prodajna = excluded.cijena_prodajna, "
            "cijena_neto = excluded.cijena_neto, pdv = excluded.pdv, aktivan = excluded.aktivan, azurirano = excluded.azurirano",
            (ident, r.get("acName", "").strip(), (r.get("acClassif") or "").strip(), (r.get("acCode") or "").strip(),
             (r.get("acSupplier") or "").strip(), (r.get("acUM") or "").strip(), _broj(r.get("anSalePrice")),
             _broj(r.get("anRTPrice")), _broj(r.get("anVAT")), 1 if (r.get("acActive") or "T") == "T" else 0, kada))
        st["identi"] += 1
        if je_materijal(r):
            st["materijali"] += 1
            st["novi_materijali"] += _upisi_materijal(cur, r)
            identi_materijala.add(ident)
        elif je_traka(r):
            st["trake"] += 1
            st["nove_trake"] += _upisi_traku(cur, r)
            identi_traka.add(ident)
    if st["identi"]:
        st["izbaceni_materijali"], st["izbacene_trake"] = _izbaci_sto_vise_nije(cur, identi_materijala, identi_traka)
    dnevnik(conn, tko, "pantheon_ident", None, "uvoz", "%s: %d identa, %d materijala (%d novih, %d izbačenih), %d traka (%d novih, %d izbačenih)"
            % (os.path.basename(putanja), st["identi"], st["materijali"], st["novi_materijali"], st["izbaceni_materijali"],
               st["trake"], st["nove_trake"], st["izbacene_trake"]))
    conn.commit()
    return st


def _izbaci_sto_vise_nije(cur, identi_materijala, identi_traka):
    """Materijali / trake u Hubu čiji ident u ovom uvozu više nije ploča / traka (D-53) ili ga u Pantheonu više nema:
    obriši ako ih ništa ne koristi (nalog, potvrđeni alias, Winstore, restl), inače označi 'ne koristi se' + neaktivan."""
    m_out = t_out = 0
    for r in cur.execute("SELECT id, pantheon_ident FROM materijal").fetchall():
        if r["pantheon_ident"] in identi_materijala:
            continue
        mid = r["id"]
        koristi = any(cur.execute(q, (mid,)).fetchone() for q in (
            "SELECT 1 FROM nalog_materijal WHERE materijal_id = ? LIMIT 1", "SELECT 1 FROM materijal_alias WHERE materijal_id = ? AND potvrdio IS NOT NULL LIMIT 1",
            "SELECT 1 FROM winstore_ploca WHERE materijal_id = ? LIMIT 1", "SELECT 1 FROM restl WHERE materijal_id = ? LIMIT 1",
            "SELECT 1 FROM materijal_traka WHERE materijal_id = ? AND potvrdio IS NOT NULL LIMIT 1",
            "SELECT 1 FROM traka_alias WHERE materijal_id = ? LIMIT 1"))
        if koristi:
            cur.execute("UPDATE materijal SET aktivan = 0, ne_koristi_se = 1 WHERE id = ? AND (aktivan = 1 OR ne_koristi_se = 0)", (mid,))
        else:
            cur.execute("DELETE FROM materijal_traka WHERE materijal_id = ?", (mid,))
            cur.execute("DELETE FROM materijal_alias WHERE materijal_id = ?", (mid,))
            cur.execute("DELETE FROM materijal WHERE id = ?", (mid,))
        m_out += 1
    for r in cur.execute("SELECT id, pantheon_ident FROM traka").fetchall():
        if r["pantheon_ident"] in identi_traka:
            continue
        tid = r["id"]
        koristi = any(cur.execute(q, (tid,)).fetchone() for q in (
            "SELECT 1 FROM element WHERE ? IN (rub1_traka_id, rub2_traka_id, rub3_traka_id, rub4_traka_id) LIMIT 1",
            "SELECT 1 FROM traka_alias WHERE traka_id = ? AND potvrdio IS NOT NULL LIMIT 1",
            "SELECT 1 FROM materijal_traka WHERE traka_id = ? AND potvrdio IS NOT NULL LIMIT 1"))
        if koristi:
            cur.execute("UPDATE traka SET aktivan = 0 WHERE id = ?", (tid,))
        else:
            cur.execute("DELETE FROM materijal_traka WHERE traka_id = ?", (tid,))
            cur.execute("DELETE FROM traka_alias WHERE traka_id = ?", (tid,))
            cur.execute("DELETE FROM traka WHERE id = ?", (tid,))
        t_out += 1
    return m_out, t_out


def primijeni_zadane_debljine(conn, tko="uvoz"):
    """Upiši debljinu po vrsti (nazivi.ZADANA_DEBLJINA — radne ploče i ploče stola 38 mm) svima kojima je Hub još ne zna.
    Zove se NAKON ispravaka ureda, pa naziv iz Pantheona i ručni upis uvijek imaju prednost (D-52)."""
    from .nazivi import ZADANA_DEBLJINA
    st = []
    for (vrsta_, ob), d in sorted(ZADANA_DEBLJINA.items()):
        n = conn.execute("UPDATE materijal SET debljina = ?, debljina_izvor = 'vrsta' WHERE vrsta = ? AND obitelj_rp IS ? "
                         "AND debljina IS NULL AND ne_koristi_se = 0", (d, vrsta_, ob)).rowcount
        if n:
            st.append(("%s %s" % (vrsta_, ob or ""), d, n))
    conn.commit()
    return st


def tekst_za_pretragu(*dijelovi):
    """Oba pisanja (BIJELI i BJELI, KAŠMIR → KASMIR) + ident + kod, da pretraga radi kako god čovjek utipka."""
    t = " ".join(x for x in dijelovi if x)
    return (norm_prikaz(t) + " " + norm(t)).strip()


def _upisi_materijal(cur, r):
    ident, naziv = r["acIdent"].strip(), r["acName"].strip()
    p = rasclani_materijal(naziv)
    vrsta_, ob = p["vrsta"], p["obitelj_rp"]
    if ident.startswith("RP") and vrsta_ not in ("RP", "ZO"):
        vrsta_, ob = "RP", ob or "radna"      # RP identi koji ne počinju s 'RADNA PLOČA' (npr. 'RP F206', 'KAMENA PLOČA')
    if vrsta_ == "OST" and ident.startswith("IV"):
        vrsta_ = "IV" if norm(naziv).startswith("IVER") else "OST"
    dekor = " ".join(p["rijeci_prikaz"])            # izvorno pisanje (BIJELI, ne BJELI) — za ekran i etikete; prepoznavanje ga opet normalizira
    kod = " ".join(sorted(k for k in p["kodovi"] if not any(k != o and k in o for o in p["kodovi"])))  # samo najdulje varijante
    L, W = PLOCA_ZADANO.get(vrsta_, (None, None))
    if vrsta_ in ("RP", "ZO") and ob in SIRINA_RP:
        W = SIRINA_RP[ob]
    aktivan = 1 if (r.get("acActive") or "T") == "T" else 0
    kratki = naziv_kratki(vrsta_, dekor, p["debljina"], ob)
    postoji = cur.execute("SELECT id, winstore_kod FROM materijal WHERE pantheon_ident = ?", (ident,)).fetchone()
    if postoji:
        # debljina iz naziva uvijek pobjeđuje (kad ured ispravi naziv u Pantheonu, Hub to odmah preuzme); inače ostaje što je bilo
        cur.execute("UPDATE materijal SET naziv_pantheon = ?, vrsta = ?, obitelj_rp = COALESCE(obitelj_rp, ?), "
                    "debljina = COALESCE(?, CASE WHEN debljina_izvor = 'naziv' THEN NULL ELSE debljina END), "
                    "debljina_izvor = CASE WHEN ? IS NOT NULL THEN 'naziv' WHEN debljina_izvor = 'naziv' THEN NULL ELSE debljina_izvor END, "
                    "dekor = ?, dekor_kod = ?, aktivan = ?, naziv_kratki = COALESCE(naziv_kratki, ?), trazi = ? WHERE id = ?",
                    (naziv, vrsta_, ob, p["debljina"], p["debljina"], dekor, kod, aktivan, kratki,
                     tekst_za_pretragu(ident, naziv, kratki, postoji["winstore_kod"]), postoji[0]))
        return 0
    cur.execute("INSERT INTO materijal (pantheon_ident, naziv_pantheon, naziv_kratki, vrsta, obitelj_rp, debljina, debljina_izvor, dekor, dekor_kod, "
                "ploca_L, ploca_W, sirina_rp, aktivan, trazi) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ident, naziv, kratki, vrsta_, ob, p["debljina"], "naziv" if p["debljina"] else None, dekor, kod, L, W,
                 SIRINA_RP.get(ob) if ob else None, aktivan, tekst_za_pretragu(ident, naziv, kratki)))
    return 1


def _upisi_traku(cur, r):
    ident, naziv = r["acIdent"].strip(), r["acName"].strip()
    p = rasclani_traku_pantheon(naziv)
    if p is None:
        p = dict(vrsta="OST", debljina=None, sirina=None, klasa=None, dekor=" ".join(norm(naziv).split()[:6]), kodovi=set())
    aktivan = 1 if (r.get("acActive") or "T") == "T" else 0
    kod = (r.get("acCode") or "").strip()
    postoji = cur.execute("SELECT id FROM traka WHERE pantheon_ident = ?", (ident,)).fetchone()
    trazi = tekst_za_pretragu(ident, naziv, kod)
    if postoji:
        cur.execute("UPDATE traka SET naziv = ?, vrsta = ?, debljina = ?, sirina = ?, klasa = ?, dekor = ?, kod = ?, dobavljac = ?, aktivan = ?, trazi = ? WHERE id = ?",
                    (naziv, p["vrsta"], p["debljina"], p["sirina"], p["klasa"], p["dekor"], kod, (r.get("acSupplier") or "").strip(), aktivan, trazi, postoji[0]))
        return 0
    cur.execute("INSERT INTO traka (pantheon_ident, naziv, vrsta, debljina, sirina, klasa, dekor, kod, dobavljac, regal_traka_ident, aktivan, trazi) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ident, naziv, p["vrsta"], p["debljina"], p["sirina"], p["klasa"], p["dekor"], kod, (r.get("acSupplier") or "").strip(), ident, aktivan, trazi))
    return 1
