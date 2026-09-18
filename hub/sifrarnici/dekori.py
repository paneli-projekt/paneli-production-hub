# -*- coding: utf-8 -*-
"""dekori.py — katalozi dobavljača (Iverpan, Elgrad, Frischeis; Blažićeve rubne trake) i SLIKE DEKORA uz naše identе (dokument 36).

Izvor je mapa `CLAUDE_COWORK\\dekori\\` koju je pripremio ured: po dobavljaču CSV i slike, plus zbirni CSV sa svim dekorima i
Blažićevim prijedlogom ABS trake. Uvoz puni `dekor_katalog` (podaci kojih u Pantheonu nema: proizvođač ploče, dostupne debljine,
dimenzije, poveznica na proizvod, predložena traka) i kopira slike u mapu Huba, umanjene na najviše 640 px.

Vezanje na naš materijal ide u dva koraka, kao kod restlova (D-64/2, D-95):
  * KOD DEKORA (25727, K2737, U504 ST9) — siguran pogodak, slika se upisuje sama (razina 'kod');
  * NAZIV — preklapanje riječi dekora daje kandidate koje ured potvrđuje na ekranu (razina 'naziv' → 'potvrda').
Potvrda ureda se pamti i ponovni uvoz je ne dira. Slike dobavljača koriste se samo na internim ekranima (D-95 §8).

    py -m hub.sifrarnici.dekori --db hub.db --uvoz "C:\\...\\CLAUDE_COWORK\\dekori"      uvoz kataloga i slika + vezanje
    py -m hub.sifrarnici.dekori --db hub.db --spoji                                      samo ponovno vezanje
    py -m hub.sifrarnici.dekori --db hub.db --stanje                                     koliko materijala ima sliku
"""
import argparse
import csv
import os
import re
import shutil
import sys

from ..db import sada, dnevnik, postavka
from .nazivi import norm

CSV_ZBIRNI = ("Svi_dekori_s_BLAZIC_rubnim_trakama", "Svi_dekori_Iverpan_Elgrad_Frischeis")
MAKS_PX = 640                                   # slike se spremaju umanjene — u popisu se ionako gledaju kao sličice
KOD = re.compile(r"\b([A-Z]{0,2}\d{3,6}\s?[A-Z]{0,3}\d{0,2})\b")      # W908 ST2, K2665 AI, H1145 ST10, 25727 MN, 0080 LI
STOP = {"MM", "PLOCA", "PLOCE", "IVERAL", "IVERICA", "MDF", "HDF", "ABS", "CP", "OM", "UM", "DEKOR", "OPTIMATT", "SIROVI", "KRONOSPAN", "EGGER", "KAINDL"}


def _kod(x):
    return re.sub(r"[^A-Z0-9]", "", (x or "").upper())


def kodovi(naziv, dodatni=None):
    """Kodovi dekora iz naziva kataloga ('Acai 25727 MN - 19 mm' → 25727MN, 25727) i iz Blažićeve oznake ploče."""
    out = []
    if dodatni:
        out.append(_kod(dodatni))
    for m in KOD.finditer((naziv or "").upper()):
        k = _kod(m.group(1))
        if len(k) >= 3 and not re.fullmatch(r"\d{1,2}", k):
            out.append(k)
    out += [re.sub(r"[A-Z]+$", "", k) for k in list(out)]
    return [k for k in dict.fromkeys(out) if len(k) >= 3]


def rijeci(naziv):
    """Riječi dekora za usporedbu naziva — bez vrste, debljine i marketinških dodataka."""
    n = norm(re.sub(r"\d+([,.]\d+)?\s*mm", " ", naziv or "", flags=re.I))
    r = {w for w in re.split(r"[^A-ZŠĐČĆŽ0-9]+", n) if len(w) > 2 and w not in STOP and not re.fullmatch(r"\d+", w)}
    return r


def mapa_slika(conn, zadano=None):
    """Gdje Hub drži slike dekora: postavka `mapa_dekori` (na VM-u C:\\Paneli\\Hub\\dekori), inače mapa 'dekori' pokraj same baze.
    Slike su izvan koda i izvan Gita, a u noćnoj kopiji su zajedno s bazom."""
    p = (postavka(conn, "mapa_dekori") or "").strip() or zadano
    if not p:
        baza = None
        for _, ime, datoteka in conn.execute("PRAGMA database_list"):
            if ime == "main" and datoteka:
                baza = datoteka
                break
        if not baza:
            from .. import db as D
            baza = D.putanja_baze()
        p = os.path.join(os.path.dirname(os.path.abspath(baza)), "dekori")
    return p


# ---------------------------------------------------------------- uvoz kataloga
def _zbirni_csv(mapa):
    for ime in sorted(os.listdir(mapa)):
        if ime.lower().endswith(".csv") and any(ime.startswith(p) for p in CSV_ZBIRNI):
            return os.path.join(mapa, ime)
    raise ValueError("u mapi %s nema zbirnog CSV-a (%s…)" % (mapa, CSV_ZBIRNI[0]))


def ucitaj_csv(putanja):
    with open(putanja, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _f(x):
    try:
        return float(str(x).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def _kopiraj_sliku(izvor, cilj, maks_px=MAKS_PX):
    """Slika iz paketa → mapa Huba, umanjena na najviše maks_px i spremljena kao .jpg. Vraća True kad je datoteka nastala."""
    if not os.path.isfile(izvor):
        return False
    if os.path.isfile(cilj) and os.path.getmtime(cilj) >= os.path.getmtime(izvor):
        return True                                            # već kopirana i nije se mijenjala
    try:
        from PIL import Image
        im = Image.open(izvor)
        im.thumbnail((maks_px, maks_px))
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        im.save(cilj, "JPEG", quality=82)
        return True
    except Exception:
        try:
            shutil.copyfile(izvor, cilj)                        # bez Pillowa: barem kopija
            return True
        except OSError:
            return False


def uvezi_katalog(conn, mapa, tko="uvoz", sa_slikama=True):
    """Zbirni CSV + slike iz mape dobavljača → `dekor_katalog` i mapa slika Huba. Idempotentno po katalog_id."""
    put = _zbirni_csv(mapa)
    redovi = ucitaj_csv(put)
    cilj_mapa = mapa_slika(conn)
    os.makedirs(cilj_mapa, exist_ok=True)
    novo = osvjezeno = slika_ok = bez_slike = 0
    for r in redovi:
        kid = (r.get("jedinstveni_id") or "").strip()
        if not kid:
            continue
        dat = None
        if sa_slikama and (r.get("putanja_slike_u_paketu") or "").strip():
            izvor = os.path.join(mapa, r["putanja_slike_u_paketu"].replace("\\", os.sep).replace("/", os.sep))
            ime = kid + ".jpg"
            if _kopiraj_sliku(izvor, os.path.join(cilj_mapa, ime)):
                dat = ime; slika_ok += 1
            else:
                bez_slike += 1
        tdat = None
        if sa_slikama and (r.get("blazic_datoteka_slike_trake") or "").strip():
            izvor = os.path.join(mapa, "Blazic_trake_2026-09-18", r["blazic_datoteka_slike_trake"].replace("/", os.sep))
            if not os.path.isfile(izvor):                       # mapa Blažića nosi datum u imenu — nađi je
                for d in os.listdir(mapa):
                    p2 = os.path.join(mapa, d, r["blazic_datoteka_slike_trake"].replace("/", os.sep))
                    if os.path.isfile(p2):
                        izvor = p2; break
            ime = "traka_" + _kod(r.get("blazic_sifra_artikla") or kid) + ".jpg"
            if _kopiraj_sliku(izvor, os.path.join(cilj_mapa, ime)):
                tdat = ime
        kod = (kodovi(r.get("naziv"), r.get("blazic_oznaka_ploce")) or [None])[0]
        v = dict(katalog_id=kid, dobavljac=(r.get("dobavljac") or "").strip(), kategorija=(r.get("kategorija") or "").strip(),
                 naziv=(r.get("naziv") or "").strip(), sifra=(r.get("sifra") or "").strip(), kod_dekora=kod,
                 proizvodac=(r.get("proizvodac") or r.get("blazic_proizvodac_ploce") or "").strip(), debljina=_f(r.get("debljina")),
                 dostupne_debljine=(r.get("dostupne_debljine") or "").strip(), duzina=_f(r.get("duzina")), sirina=_f(r.get("sirina")),
                 url_proizvoda=(r.get("url_proizvoda") or "").strip(), datoteka=dat,
                 izvor_slike=(r.get("putanja_slike_u_paketu") or "").strip(),
                 traka_sifra=(r.get("blazic_sifra_artikla") or "").strip(), traka_naziv=(r.get("blazic_naziv_trake") or "").strip(),
                 traka_debljine=(r.get("blazic_debljine") or "").strip(), traka_ocjena=(r.get("blazic_ocjena_podudaranja") or "").strip(),
                 traka_datoteka=tdat, kljuc_pretrage=(r.get("kljuc_pretrage") or "").strip(), datum=(r.get("datum_prikupljanja") or "").strip())
        # upiši
        st = conn.execute("SELECT id FROM dekor_katalog WHERE katalog_id = ?", (kid,)).fetchone()
        if st:
            conn.execute("UPDATE dekor_katalog SET dobavljac=:dobavljac, kategorija=:kategorija, naziv=:naziv, sifra=:sifra, kod_dekora=:kod_dekora, "
                         "proizvodac=:proizvodac, debljina=:debljina, dostupne_debljine=:dostupne_debljine, duzina=:duzina, sirina=:sirina, "
                         "url_proizvoda=:url_proizvoda, datoteka=COALESCE(:datoteka, datoteka), izvor_slike=:izvor_slike, traka_sifra=:traka_sifra, "
                         "traka_naziv=:traka_naziv, traka_debljine=:traka_debljine, traka_ocjena=:traka_ocjena, "
                         "traka_datoteka=COALESCE(:traka_datoteka, traka_datoteka), kljuc_pretrage=:kljuc_pretrage, datum=:datum "
                         "WHERE katalog_id = :katalog_id", v)
            osvjezeno += 1
        else:
            v["kada"] = sada()
            conn.execute("INSERT INTO dekor_katalog (katalog_id, dobavljac, kategorija, naziv, sifra, kod_dekora, proizvodac, debljina, dostupne_debljine, "
                         "duzina, sirina, url_proizvoda, datoteka, izvor_slike, traka_sifra, traka_naziv, traka_debljine, traka_ocjena, traka_datoteka, "
                         "kljuc_pretrage, datum, kada) VALUES (:katalog_id, :dobavljac, :kategorija, :naziv, :sifra, :kod_dekora, :proizvodac, :debljina, "
                         ":dostupne_debljine, :duzina, :sirina, :url_proizvoda, :datoteka, :izvor_slike, :traka_sifra, :traka_naziv, :traka_debljine, "
                         ":traka_ocjena, :traka_datoteka, :kljuc_pretrage, :datum, :kada)", v)
            novo += 1
    conn.commit()
    dnevnik(conn, tko, "dekori", 0, "uvoz kataloga", "%d novih, %d osvježenih, %d slika" % (novo, osvjezeno, slika_ok))
    conn.commit()
    return dict(redaka=len(redovi), novo=novo, osvjezeno=osvjezeno, slika=slika_ok, bez_slike=bez_slike, mapa_slika=cilj_mapa, csv=os.path.basename(put))


# ---------------------------------------------------------------- vezanje kataloga na naše materijale
def _katalog(conn):
    return [dict(r) for r in conn.execute("SELECT katalog_id, naziv, kod_dekora, dobavljac, kategorija, debljina, datoteka FROM dekor_katalog WHERE datoteka IS NOT NULL")]


def _indeks_kodova(kat):
    """Dva kazala: po PUNOM kodu (27045BS — ista završna obrada) i po OSNOVNOM (27045 — isti dekor, druga obrada)."""
    puni, osnovni = {}, {}
    for k in kat:
        for kod in kodovi(k["naziv"], k["kod_dekora"]):
            baza = re.sub(r"[A-Z]+$", "", kod)
            if k not in osnovni.setdefault(baza, []):
                osnovni[baza].append(k)
            if re.search(r"\d[A-Z]+$", kod) and k not in puni.setdefault(kod, []):
                puni[kod].append(k)
    return puni, osnovni


def spoji(conn, tko="uvoz", prag=0.6, commit=True):
    """Poveži katalog s materijalima: siguran pogodak po KODU dekora upisuje sliku sam (razina 'kod'), inače se po NAZIVU ponudi
    najviše 3 kandidata koje ured potvrđuje. Ne dira ono što je ured već potvrdio ili odbio."""
    kat = _katalog(conn)
    puni, osnovni = _indeks_kodova(kat)
    rijec_kat = [(k, rijeci(k["naziv"])) for k in kat]
    ima = {r[0] for r in conn.execute("SELECT materijal_id FROM dekor_slika WHERE status = 'aktivna'")}
    odbijeno = {(r[0], r[1]) for r in conn.execute("SELECT materijal_id, katalog_id FROM dekor_slika WHERE status = 'odbijena'")}
    n_kod = n_kand = 0
    for m in conn.execute("SELECT id, pantheon_ident, naziv_pantheon, dekor, dekor_kod, debljina FROM materijal WHERE ne_koristi_se = 0").fetchall():
        if m["id"] in ima:
            continue
        mk = _kod(m["dekor_kod"]) if m["dekor_kod"] else None
        def _bolji(lst):
            lst = [x for x in lst if (m["id"], x["katalog_id"]) not in odbijeno]
            lst.sort(key=lambda x: (0 if (m["debljina"] and x["debljina"] and abs(x["debljina"] - m["debljina"]) < 0.6) else 1, x["katalog_id"]))
            return lst
        baza = re.sub(r"[A-Z]+$", "", mk) if mk else None
        tocno = _bolji(puni.get(mk, [])) if mk and re.search(r"\d[A-Z]+$", mk) else []
        if not tocno and mk and not re.search(r"\d[A-Z]+$", mk):
            jedini = _bolji(osnovni.get(baza, []))           # naš kod nema završnu obradu: jedan pogodak je siguran
            tocno = jedini if len(jedini) == 1 else []
        if tocno:                                            # isti kod i ista završna obrada — slika se upisuje sama
            _upisi(conn, m["id"], tocno[0], "aktivna", "kod", 1.0)
            n_kod += 1
            continue
        blizu = _bolji(osnovni.get(baza, [])) if baza else []
        if blizu:                                            # isti dekor, druga obrada (27045 BS ↔ 27045 GR) — ured potvrdi
            for k in blizu[:3]:
                _upisi(conn, m["id"], k, "kandidat", "kod-osnovni", 0.9)
            n_kand += 1
            continue
        rm = rijeci(m["dekor"] or m["naziv_pantheon"])
        if len(rm) < 2:
            continue                                        # jedna riječ dekora (BIJELI, CRNI) ne razlikuje dekore — bolje ništa nego nagađanje
        bodovi = []
        for k, rk in rijec_kat:
            if (m["id"], k["katalog_id"]) in odbijeno or not rk:
                continue
            zajedno = rm & rk
            if len(zajedno) < 2:
                continue                                    # traži se barem dvije zajedničke riječi (HRAST + SANREMO)
            p = len(zajedno) / float(len(rm | rk))           # Jaccard: kažnjava i kataloške nazive s puno viška
            if p >= prag:
                bodovi.append((p + (0.05 if m["debljina"] and k["debljina"] and abs(k["debljina"] - m["debljina"]) < 0.6 else 0), k))
        if not bodovi:
            continue
        bodovi.sort(key=lambda x: -x[0])
        for p, k in bodovi[:3]:
            _upisi(conn, m["id"], k, "kandidat", "naziv", round(min(p, 1.0), 3))
        n_kand += 1
    if commit:
        conn.commit()
    dnevnik(conn, tko, "dekori", 0, "vezanje", "%d po kodu, %d materijala s kandidatima" % (n_kod, n_kand))
    conn.commit()
    return dict(po_kodu=n_kod, s_kandidatima=n_kand, katalog=len(kat))


def _upisi(conn, materijal_id, k, status, razina, bodovi):
    conn.execute("INSERT OR IGNORE INTO dekor_slika (materijal_id, katalog_id, datoteka, status, razina, bodovi, kada) VALUES (?,?,?,?,?,?,?)",
                 (materijal_id, k["katalog_id"], k["datoteka"], status, razina, bodovi, sada()))


def _mat(conn, ident_ili_id):
    r = conn.execute("SELECT * FROM materijal WHERE id = ? OR pantheon_ident = ?", (ident_ili_id, str(ident_ili_id).upper())).fetchone()
    return dict(r) if r else None


def slika(conn, ident_ili_id):
    """Aktivna slika materijala → dict(datoteka, putanja, katalog_id, dobavljac, url_proizvoda, razina) ili None."""
    m = _mat(conn, ident_ili_id)
    if not m:
        return None
    r = conn.execute("SELECT s.datoteka, s.katalog_id, s.razina, s.potvrdio, k.dobavljac, k.naziv AS naziv_kataloga, k.url_proizvoda, k.proizvodac, "
                     "k.dostupne_debljine, k.traka_sifra, k.traka_naziv, k.traka_datoteka, k.traka_ocjena "
                     "FROM dekor_slika s LEFT JOIN dekor_katalog k ON k.katalog_id = s.katalog_id "
                     "WHERE s.materijal_id = ? AND s.status = 'aktivna' LIMIT 1", (m["id"],)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["putanja"] = os.path.join(mapa_slika(conn), d["datoteka"])
    d["ident"] = m["pantheon_ident"]
    return d


def kandidati(conn, ident_ili_id):
    """Ponuđene slike koje ured još nije potvrdio (najbolje prve)."""
    m = _mat(conn, ident_ili_id)
    if not m:
        return []
    return [dict(r) for r in conn.execute(
        "SELECT s.katalog_id, s.datoteka, s.bodovi, k.naziv, k.dobavljac, k.kategorija, k.proizvodac, k.url_proizvoda "
        "FROM dekor_slika s JOIN dekor_katalog k ON k.katalog_id = s.katalog_id WHERE s.materijal_id = ? AND s.status = 'kandidat' "
        "ORDER BY s.bodovi DESC, k.katalog_id", (m["id"],))]


def za_potvrdu(conn, limit=200, q=None):
    """Materijali bez slike koji imaju kandidate — ekran ureda. [{ident, naziv, dekor, debljina, kandidati:[…]}]"""
    a = []
    sql = ("SELECT m.id, m.pantheon_ident, m.naziv_pantheon, m.dekor, m.debljina, m.vrsta FROM materijal m "
           "WHERE m.ne_koristi_se = 0 AND EXISTS (SELECT 1 FROM dekor_slika s WHERE s.materijal_id = m.id AND s.status = 'kandidat') "
           "AND NOT EXISTS (SELECT 1 FROM dekor_slika s WHERE s.materijal_id = m.id AND s.status = 'aktivna')")
    if q:
        sql += " AND m.trazi LIKE ?"; a.append("%" + norm(q) + "%")
    sql += " ORDER BY m.pantheon_ident LIMIT ?"; a.append(limit)
    out = []
    for m in conn.execute(sql, a):
        d = dict(m); d["kandidati"] = kandidati(conn, m["id"]); out.append(d)
    return out


def potvrdi(conn, ident_ili_id, katalog_id, tko, commit=True):
    """Ured je odabrao sliku: ona postaje aktivna, ostali kandidati tog materijala se odbijaju."""
    m = _mat(conn, ident_ili_id)
    if not m:
        raise ValueError("nema materijala %s" % ident_ili_id)
    k = conn.execute("SELECT katalog_id, datoteka FROM dekor_katalog WHERE katalog_id = ?", (katalog_id,)).fetchone()
    if not k or not k["datoteka"]:
        raise ValueError("nema slike u katalogu za %s" % katalog_id)
    conn.execute("UPDATE dekor_slika SET status = 'odbijena' WHERE materijal_id = ? AND status IN ('kandidat', 'aktivna')", (m["id"],))
    conn.execute("INSERT OR IGNORE INTO dekor_slika (materijal_id, katalog_id, datoteka, status, razina, kada) VALUES (?,?,?,'aktivna','potvrda',?)",
                 (m["id"], katalog_id, k["datoteka"], sada()))
    conn.execute("UPDATE dekor_slika SET status = 'aktivna', razina = 'potvrda', datoteka = ?, potvrdio = ?, potvrdjeno = ? "
                 "WHERE materijal_id = ? AND katalog_id = ?", (k["datoteka"], tko, sada(), m["id"], katalog_id))
    dnevnik(conn, tko, "materijal", m["id"], "slika dekora", "potvrđena %s" % katalog_id)
    if commit:
        conn.commit()
    return slika(conn, m["id"])


def odbij(conn, ident_ili_id, katalog_id, tko, commit=True):
    """Ni jedna ponuđena slika ne valja (ili ova ne valja) — miče se iz ponude i više se ne nudi."""
    m = _mat(conn, ident_ili_id)
    if not m:
        raise ValueError("nema materijala %s" % ident_ili_id)
    if katalog_id:
        conn.execute("UPDATE dekor_slika SET status = 'odbijena', potvrdio = ?, potvrdjeno = ? WHERE materijal_id = ? AND katalog_id = ?",
                     (tko, sada(), m["id"], katalog_id))
    else:
        conn.execute("UPDATE dekor_slika SET status = 'odbijena', potvrdio = ?, potvrdjeno = ? WHERE materijal_id = ? AND status = 'kandidat'",
                     (tko, sada(), m["id"]))
    if commit:
        conn.commit()
    return True


def sazetak(conn):
    """Brojke za ekran: koliko materijala ima sliku, koliko čeka potvrdu, koliko je u katalogu."""
    q = lambda sql, *a: conn.execute(sql, a).fetchone()[0]
    return dict(katalog=q("SELECT COUNT(*) FROM dekor_katalog"), sa_slikom=q("SELECT COUNT(DISTINCT materijal_id) FROM dekor_slika WHERE status = 'aktivna'"),
                za_potvrdu=q("SELECT COUNT(DISTINCT materijal_id) FROM dekor_slika WHERE status = 'kandidat' AND materijal_id NOT IN "
                             "(SELECT materijal_id FROM dekor_slika WHERE status = 'aktivna')"),
                materijala=q("SELECT COUNT(*) FROM materijal WHERE ne_koristi_se = 0"),
                dobavljaci=[dict(r) for r in conn.execute("SELECT dobavljac, COUNT(*) AS n FROM dekor_katalog GROUP BY dobavljac ORDER BY n DESC")])


# ---------------------------------------------------------------- CLI
def main(argv=None):
    from .. import db as D
    p = argparse.ArgumentParser(description="Katalozi dobavljača i slike dekora (dokument 36)")
    p.add_argument("--db", default=None)
    p.add_argument("--uvoz", metavar="MAPA", help="mapa CLAUDE_COWORK\\dekori")
    p.add_argument("--spoji", action="store_true")
    p.add_argument("--stanje", action="store_true")
    p.add_argument("--bez-slika", action="store_true", help="uvezi samo podatke, bez kopiranja slika")
    p.add_argument("--tko", default="uvoz")
    a = p.parse_args(argv)
    conn = D.spoji(a.db)
    D.init(conn)
    if a.uvoz:
        iz = uvezi_katalog(conn, a.uvoz, a.tko, sa_slikama=not a.bez_slika)
        print("Katalog: %(redaka)d redaka — %(novo)d novih, %(osvjezeno)d osvježenih, %(slika)d slika u %(mapa_slika)s" % iz)
        sp = spoji(conn, a.tko)
        print("Vezanje: %(po_kodu)d po kodu dekora, %(s_kandidatima)d materijala čeka potvrdu ureda" % sp)
    elif a.spoji:
        print("Vezanje: %(po_kodu)d po kodu dekora, %(s_kandidatima)d materijala čeka potvrdu ureda" % spoji(conn, a.tko))
    if a.stanje or not (a.uvoz or a.spoji):
        s = sazetak(conn)
        print("Katalog %(katalog)d dekora · materijala %(materijala)d · sa slikom %(sa_slikom)d · čeka potvrdu %(za_potvrdu)d" % s)
        for d in s["dobavljaci"]:
            print("   %-12s %d" % (d["dobavljac"], d["n"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
