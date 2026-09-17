# -*- coding: utf-8 -*-
"""Prepoznavanje materijala i traka iz teksta kako ga pišu PW / PPNEST / kupci / Corpus → Pantheon ident (D-24, D-31, D-32).

Redoslijed (deterministički, bez LLM-a — modul `ai` nije potreban za šifrarnik, D-15):
  1. alias-tablica (točan normalizirani tekst)                → razina 'alias'
  2. Winstore kod (SIFRA MAT iz PPNEST CSV-a, MaterialCode)   → razina 'winstore'
  3. usporedba naziva: vrsta + debljina + riječi dekora + kodovi dekora
        jedinstven i potpun pogodak                           → razina 'naziv'
        više kandidata ili djelomičan pogodak                 → razina 'za_potvrdu' (kandidati za čovjeka)
  4. ništa                                                    → razina 'nema'
Na ekranu se razine 'za_potvrdu' / 'nema' prikazuju kao „za potvrdu“; potvrđeni par ide u alias-tablicu (potvrdi_materijal / potvrdi_traku).
"""
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from functools import lru_cache

from ..db import sada
from .nazivi import (rasclani_materijal, rasclani_traku, rasclani_traku_pantheon, norm, glue, rijeci, kodovi, sufiksi,
                     klasa_trake, sirina_za_materijal)

RAZINE_SIGURNE = ("alias", "winstore", "zadana", "naziv")


@dataclass
class Rezultat:
    upit: str
    razina: str                       # alias | winstore | zadana | naziv | za_potvrdu | nema
    ident: str = None
    id: int = None                    # materijal.id ili traka.id
    naziv: str = None                 # Pantheon naziv
    score: float = 0.0
    kandidati: list = field(default_factory=list)   # [(ident, naziv, score), …] najbolji prvi
    objasnjenje: str = ""
    klasa: str = None                 # samo trake: "1/22", "0,5/22"…

    @property
    def siguran(self):
        return self.razina in RAZINE_SIGURNE

    def kao_dict(self):
        return dict(upit=self.upit, razina=self.razina, ident=self.ident, id=self.id, naziv=self.naziv, score=round(self.score, 2),
                    kandidati=[dict(ident=i, naziv=n, score=round(s, 2)) for i, n, s in self.kandidati[:6]],
                    objasnjenje=self.objasnjenje, klasa=self.klasa, siguran=self.siguran)


# ---------------------------------------------------------------- keš šifrarnika (invalidira se pri svakoj promjeni)
_KES = {}


def ocisti_kes():
    _KES.clear()


def _materijali(conn):
    k = ("materijali", id(conn))
    if k not in _KES:
        rows = conn.execute("SELECT id, pantheon_ident, naziv_pantheon, vrsta, obitelj_rp, debljina, dekor, dekor_kod, winstore_kod, aktivan "
                            "FROM materijal WHERE ne_koristi_se = 0").fetchall()     # ured je rekao da se ident ne koristi (D-51) → Hub ga ne nudi
        mats = []
        for r in rows:
            mats.append(dict(id=r["id"], ident=r["pantheon_ident"], naziv=r["naziv_pantheon"], vrsta=r["vrsta"], ob=r["obitelj_rp"],
                             deb=r["debljina"], rijeci=set(rijeci(r["naziv_pantheon"])), sufiksi=sufiksi(r["naziv_pantheon"]), kodovi=kodovi(r["naziv_pantheon"]),
                             glue=glue(r["naziv_pantheon"]), winstore=(r["winstore_kod"] or "").upper(), aktivan=r["aktivan"]))
            mats[-1]["pref3"] = {w[:3] for w in mats[-1]["rijeci"]}
        df = {}
        for m in mats:
            for w in m["rijeci"]:
                df[w] = df.get(w, 0) + 1
        _KES[k] = (mats, df)
    return _KES[k]


def _trake(conn):
    k = ("trake", id(conn))
    if k not in _KES:
        rows = conn.execute("SELECT id, pantheon_ident, naziv, vrsta, debljina, sirina, klasa, dekor, kod, aktivan FROM traka").fetchall()
        trs = []
        for r in rows:
            p = rasclani_traku_pantheon(r["naziv"]) or {}
            trs.append(dict(id=r["id"], ident=r["pantheon_ident"], naziv=r["naziv"], vrsta=r["vrsta"], deb=r["debljina"], sir=r["sirina"],
                            klasa=r["klasa"], rijeci=set(rijeci(p.get("dekor", "") or r["dekor"] or "")), sufiksi=sufiksi(r["naziv"]),
                            kodovi=kodovi(r["naziv"]) | ({r["kod"].upper()} if r["kod"] else set()),
                            glue=glue(r["naziv"]) + glue(r["kod"] or ""), aktivan=r["aktivan"]))
            trs[-1]["pref3"] = {w[:3] for w in trs[-1]["rijeci"]}
        df = {}
        for t in trs:
            for w in t["rijeci"]:
                df[w] = df.get(w, 0) + 1
        _KES[k] = (trs, df)
    return _KES[k]


# ---------------------------------------------------------------- bodovanje
@lru_cache(maxsize=500000)
def _slicno(a, b):
    """Ista riječ, prefiks (≥ 4 slova) ili tipfeler (sličnost ≥ 0,84). Keširano: iste se riječi uspoređuju tisuće puta."""
    return a == b or (len(a) >= 4 and (b.startswith(a) or a.startswith(b))) or SequenceMatcher(None, a, b).ratio() >= 0.84


def moguc(q_rijeci, q_kodovi, kand):
    """Brzi predfilter prije bodovanja: kandidat mora dijeliti bar jednu riječ (ili početak riječi — tipfeleri) ili kod;
    inače ne može biti ni pogodak ni koristan prijedlog. Štedi ~90 % vremena uvoza (Winstore, zadane trake)."""
    if q_rijeci:
        p3 = kand.get("pref3") or {w[:3] for w in kand["rijeci"]}
        for w in q_rijeci:
            if w in kand["rijeci"] or w[:3] in p3 or (len(w) == 2 and w in kand["glue"]):
                return True
    for k in q_kodovi:
        if k in kand["glue"] or (len(k) >= 4 and k[:4] in kand["glue"]):
            return True
    return not q_rijeci and not q_kodovi


def _bodovi(q_rijeci, q_kodovi, kand, df, n_ukupno, q_sufiksi=(), winstore_prednost=True):
    """Vrati (score, promasaji): riječi upita koje kandidat nema su promašaji (svaki −0,6); kodovi dekora nose najviše.
    Dvoslovni sufiksi kodova (PE, MN, AE, UM) su slab dokaz: u upitu iza koda (q_sufiksi) ne rade promašaj; 'UM' bez koda u upitu
    pogađa kandidata koji ima '27045 UM' u nazivu (sufiks u slijepljenom nazivu)."""
    score = 0.0
    promasaji = []
    for w in q_rijeci:
        if w in kand["rijeci"]:
            score += (0.5 if df.get(w, 0) > 0.03 * n_ukupno else 1.0) if len(w) > 2 else 0.6
        elif len(w) == 2 and re.search(r"\d" + w + r"(?![A-Z])", kand["glue"]):
            score += 0.8                                          # sufiks koda u nazivu kandidata (CHAMPANGE UM → 27045 UM)
        elif w in q_sufiksi:
            score -= 0.3                                          # sufiks koda iz upita koji kandidat nema — slab dokaz, nije promašaj
        elif len(w) > 2 and any(_slicno(w, c) for c in kand["rijeci"]):
            score += 0.4 if df.get(w, 0) > 0.03 * n_ukupno else 0.8
        else:
            promasaji.append(w)
            score -= 0.6
    pogodjeni = [k for k in q_kodovi if k in kand["glue"]]
    jak_kod = False
    for k in {k for k in pogodjeni if not any(k != o and k in o for o in pogodjeni)}:   # samo najdulje pogođene varijante
        score += min(3.0, 0.5 + 0.25 * len(k))                    # W908ST2 → 2,25; ST9 → 1,25 (kratki sufiksi malo vrijede)
        if len(k) >= 5 and re.search(r"[A-Z]", k) and re.search(r"\d", k):
            jak_kod = True                                        # potpun kod dekora (K2665AI, W908ST2, VSM06) = odlučujuće
    for k in q_kodovi:
        m = re.match(r"^([A-Z]{0,3}\d{3,5})([A-Z]{1,2})$", k)   # 2162MN: jezgra 2162 + sufiks MN
        if m and k not in kand["glue"] and m.group(1) in kand["glue"]:
            score -= 1.0                                        # isti kod, drugi sufiks (2162 PE ≠ 2162 MN)
            promasaji.append(k)
    score -= 0.1 * max(0, len(kand["rijeci"] - set(q_rijeci) - kand.get("sufiksi", set())))
    if kand.get("aktivan"):
        score += 0.2
    if winstore_prednost and kand.get("winstore"):
        score += 0.3                                              # materijal koji postoji u Winstoreu se stvarno koristi — prednost pri izjednačenju
    if jak_kod and promasaji and not any(re.search(r"\d", x) for x in promasaji):
        promasaji = []                                            # riječi se razlikuju (EVOKE LIGHT vs EVOKE SVIJETLI), ali kod je isti
        score += 0.5
    return score, promasaji


def _jaki(kodovi):
    """Najdulje varijante kodova sa znamenkom (W908ST2, ne W908 i ST2 zasebno)."""
    return {k for k in kodovi if re.search(r"\d", k) and not any(k != o and k in o for o in kodovi)}


def _odluka(upit, kandidati, potpuni, objasnjenje, q_rijeci=()):
    """kandidati: [(score, kand, promasaji)] sortirani silazno. Siguran ('naziv') = bez promašaja i jasna prednost (≥ 0,5),
    ili savršen pogodak (kandidat nema ni jednu riječ viška) dok drugi kandidat ima višak ili promašaj."""
    if not kandidati:
        return Rezultat(upit=upit, razina="nema", objasnjenje=objasnjenje or "nema kandidata")
    lista = [(k["ident"], k["naziv"], s) for s, k, _ in kandidati[:8]]
    s1, k1, p1 = kandidati[0]
    s2 = kandidati[1][0] if len(kandidati) > 1 else None
    q = set(q_rijeci)
    savrsen1 = not p1 and not (k1["rijeci"] - q - k1.get("sufiksi", set()))
    savrsen2 = len(kandidati) > 1 and not kandidati[1][2] and not (kandidati[1][1]["rijeci"] - q - kandidati[1][1].get("sufiksi", set()))
    if not p1 and potpuni and s1 > 0 and (s2 is None or s1 - s2 >= 0.5 or (savrsen1 and not savrsen2 and s1 - s2 > 0)):
        return Rezultat(upit=upit, razina="naziv", ident=k1["ident"], id=k1["id"], naziv=k1["naziv"], score=s1, kandidati=lista,
                        objasnjenje=objasnjenje + "; jedinstven pogodak po nazivu")
    razlog = ("bez pogotka: %s" % ", ".join(p1)) if p1 else ("više kandidata (%.1f vs %.1f)" % (s1, s2) if s2 is not None else "slab pogodak")
    return Rezultat(upit=upit, razina="za_potvrdu", ident=k1["ident"], id=k1["id"], naziv=k1["naziv"], score=s1, kandidati=lista,
                    objasnjenje=objasnjenje + "; " + razlog)


# ---------------------------------------------------------------- materijali
def prepoznaj_materijal(conn, naziv, debljina=None, winstore_kod=None, sirina_ploce=None, winstore_prednost=True):
    """naziv = kako piše u CPW/CPO/CSV/nalogu; debljina i sirina_ploce iz datoteke (CPO THK1/INV1, CPW MATERIJAL) ako naziv nema.
    winstore_prednost=False koristi sam uvoz Winstorea: dok se veze tek grade, „postoji u Winstoreu“ ne smije utjecati na poredak
    kandidata — inače bi isti izvoz dao drukčije prijedloge u prvom i u drugom prolazu."""
    upit = (naziv or "").strip()
    n = norm(upit)
    # 1. alias
    r = conn.execute("SELECT a.materijal_id, m.pantheon_ident, m.naziv_pantheon, a.izvor FROM materijal_alias a JOIN materijal m ON m.id = a.materijal_id "
                     "WHERE a.alias_norm = ?", (n,)).fetchone()
    if r:
        return Rezultat(upit=upit, razina="alias", ident=r[1], id=r[0], naziv=r[2], score=9.0, objasnjenje="alias (%s)" % (r[3] or "—"))
    # 2. Winstore kod — iz zasebnog polja (PPNEST SIFRA MAT) ili iz samog naziva: Corpusov CPW u polje MATERIJAL
    #    piše upravo Winstore kod (W908ST2-18, IV000054-3), a ne tekstualni naziv (dokument 14 §3.5).
    wk = _norm_winstore(winstore_kod)                     # samo ovaj ulazi u bodovanje naziva (korak 3)
    for k in [x for x in (wk, (winstore_kod or "").strip().upper() or None,
                          _norm_winstore(upit), (upit or "").strip().upper()) if x]:
        r = conn.execute("SELECT id, pantheon_ident, naziv_pantheon FROM materijal WHERE UPPER(winstore_kod) = ? AND ne_koristi_se = 0", (k,)).fetchone()
        if not r:   # dodatni kod istog materijala (varijanta A/B/C) — veza je na razini ploče u zadnjem Winstore izvozu
            r = conn.execute("SELECT m.id, m.pantheon_ident, m.naziv_pantheon FROM winstore_ploca w JOIN materijal m ON m.id = w.materijal_id "
                             "WHERE UPPER(w.materijal_kod) = ? AND m.ne_koristi_se = 0 LIMIT 1", (k,)).fetchone()
        if r:
            return Rezultat(upit=upit, razina="winstore", ident=r[1], id=r[0], naziv=r[2], score=8.0, objasnjenje="Winstore kod %s" % k)
    # 3. naziv
    p = rasclani_materijal(upit, debljina, sirina_ploce)
    mats, df = _materijali(conn)
    q_rijeci, q_kodovi = list(dict.fromkeys(p["rijeci"])), set(p["kodovi"])
    if wk:
        q_kodovi.add(wk.split("-")[0])
    if not q_rijeci and not q_kodovi:
        return Rezultat(upit=upit, razina="nema", objasnjenje="naziv bez riječi dekora i bez koda")
    q_sufiksi = sufiksi(upit)
    q_jaki = _jaki(q_kodovi)
    kand = []
    for m in mats:
        if p["vrsta"] != "OST" and m["vrsta"] != p["vrsta"]:
            continue
        if p["vrsta"] in ("RP", "ZO") and p["obitelj_rp"] and m["ob"] and m["ob"] != p["obitelj_rp"]:
            continue
        if p["vrsta"] not in ("RP", "ZO") and p["debljina"] and m["deb"] and abs(m["deb"] - p["debljina"]) > 0.11:
            continue
        if p["vrsta"] == "OST" and sirina_ploce and sirina_ploce > 1000 and m["vrsta"] in ("RP", "ZO"):
            continue                                                  # ploča šira od 1 m nije radna/zidna ploča (600/640/900)
        if not moguc(q_rijeci, q_kodovi, m):
            continue
        s, promasaji = _bodovi(q_rijeci, q_kodovi, m, df, len(mats), q_sufiksi, winstore_prednost)
        if q_jaki and not any(k in m["glue"] for k in q_jaki):
            m_jaki = _jaki(m["kodovi"])
            if m_jaki and not any(k in p["glue"] for k in m_jaki):
                s -= 1.0                                              # oba imaju kod dekora, a različit je (FA41 ≠ FA42, W960 ST7 ≠ U999 ST7)
                promasaji = promasaji + ["kod " + "/".join(sorted(m_jaki))]
        if p["vrsta"] in ("RP", "ZO") and p["obitelj_rp"] and m["ob"] == p["obitelj_rp"]:
            s += 0.3
        if wk and m["winstore"] == wk:
            s += 3.0
        if s > -0.5:
            kand.append((s, m, promasaji))
    kand.sort(key=lambda x: -x[0])
    obj = "vrsta %s%s, debljina %s, riječi %s, kodovi %s" % (p["vrsta"], (" (%s)" % p["obitelj_rp"]) if p["obitelj_rp"] else "",
                                                          ("%g" % p["debljina"]) if p["debljina"] else "?", " ".join(q_rijeci) or "—", " ".join(sorted(q_kodovi)) or "—")
    return _odluka(upit, kand, potpuni=True, objasnjenje=obj, q_rijeci=q_rijeci)


def _norm_winstore(kod):
    """PPNEST zna napisati K5574IR_19 ili VSM1-18: ujednači na K5574IR-19 / VSM01-18; 'XXX' i prazno = nema koda."""
    if not kod:
        return None
    k = norm(kod).replace(" ", "-")
    if k in ("XXX", "-", "0"):
        return None
    m = re.match(r"^([A-Z0-9]+)-(\d{1,2}(?:[,.]\d)?)$", k)
    if not m:
        return k
    osnova, deb = m.group(1), m.group(2)
    m2 = re.match(r"^(VSM|VHG|VA|FP|TM)(\d{1,2})$", osnova)
    if m2:
        osnova = "%s%02d" % (m2.group(1), int(m2.group(2)))
    return "%s-%s" % (osnova, deb)


def potvrdi_materijal(conn, alias, materijal_id, tko, izvor="rucno"):
    """Potvrđeni par (tekst → materijal) ulazi u alias-tablicu: idući put bez pitanja (D-32)."""
    conn.execute("INSERT INTO materijal_alias (alias, alias_norm, materijal_id, izvor, potvrdio, kada) VALUES (?, ?, ?, ?, ?, ?) "
                 "ON CONFLICT(alias_norm) DO UPDATE SET materijal_id = excluded.materijal_id, izvor = excluded.izvor, potvrdio = excluded.potvrdio, kada = excluded.kada",
                 (alias.strip(), norm(alias), materijal_id, izvor, tko, sada()))
    conn.commit()


# ---------------------------------------------------------------- trake
def prepoznaj_traku(conn, oznaka, materijal_id=None, debljina=None):
    """oznaka = tekst iz naloga ('ABS-ISTI', 'MEL-ISTI', '1/22 JELA TAVERNA', 'taverna'…); materijal_id = ploča na kojoj je rub (za ISTI i širinu);
    debljina = debljina za širinu trake kad nije debljina ploče (sklop lijepljenja 36–42 mm → /44, D-79)."""
    upit = (oznaka or "").strip()
    n = norm(upit)
    mat = None
    if materijal_id:
        mat = conn.execute("SELECT id, pantheon_ident, naziv_pantheon, debljina, dekor, dekor_kod FROM materijal WHERE id = ?", (materijal_id,)).fetchone()
    # 1. alias uz materijal, pa opći
    for mid in ([materijal_id] if materijal_id else []) + [None]:
        r = conn.execute("SELECT a.traka_id, t.pantheon_ident, t.naziv, t.klasa, a.izvor FROM traka_alias a JOIN traka t ON t.id = a.traka_id "
                         "WHERE a.alias_norm = ? AND a.materijal_id IS ?", (n, mid)).fetchone()
        if r:
            return Rezultat(upit=upit, razina="alias", ident=r[1], id=r[0], naziv=r[2], score=9.0, klasa=r[3], objasnjenje="alias (%s)" % (r[4] or "—"))
    t = rasclani_traku(upit)
    if t["vrsta"] is None and not t["dekor"]:
        return Rezultat(upit=upit, razina="nema", objasnjenje="oznaka nije traka")
    sir = t["sirina"] or sirina_za_materijal(debljina if debljina is not None else (mat["debljina"] if mat else None))
    klasa = klasa_trake(t["debljina"], sir)
    # 2. zadana traka materijala (D-31): ISTI ili samo klasa
    if (t["isti"] or not t["dekor"]) and mat:
        r = conn.execute("SELECT mt.traka_id, tr.pantheon_ident, tr.naziv, mt.izvor FROM materijal_traka mt JOIN traka tr ON tr.id = mt.traka_id "
                         "WHERE mt.materijal_id = ? AND mt.klasa = ?", (materijal_id, klasa)).fetchone()
        if r:
            return Rezultat(upit=upit, razina="zadana", ident=r[1], id=r[0], naziv=r[2], score=8.5, klasa=klasa,
                            objasnjenje="zadana traka materijala za klasu %s (%s)" % (klasa, r[3] or "—"))
    # 3. po nazivu: ciljni dekor = dekor materijala (ISTI) ili dekor iz oznake
    if t["isti"] or not t["dekor"]:
        if not mat:
            return Rezultat(upit=upit, razina="nema", klasa=klasa, objasnjenje="ISTI bez materijala")
        q_rijeci, q_kodovi = rijeci(mat["dekor"] or ""), kodovi(mat["dekor_kod"] or "")
        q_sufiksi = sufiksi(mat["naziv_pantheon"])
        cilj = "isti dekor kao %s" % mat["pantheon_ident"]
    else:
        q_rijeci, q_kodovi = rijeci(t["dekor"]), set(t["kodovi"])
        q_sufiksi = sufiksi(upit)
        cilj = "dekor iz oznake"
    trs, df = _trake(conn)
    obj = "%s, klasa %s, riječi %s, kodovi %s" % (cilj, klasa or "?", " ".join(q_rijeci) or "—", " ".join(sorted(q_kodovi)) or "—")
    rez = _trake_kandidati(upit, trs, df, q_rijeci, q_kodovi, klasa, obj, q_sufiksi=q_sufiksi)
    if rez.razina != "naziv" and klasa and t["debljina"] is not None:
        # druga širina iste debljine (npr. nema 0,5/22 CRNA NK, ali postoji 0,5/29) — samo kao kandidati za potvrdu
        rez2 = _trake_kandidati(upit, trs, df, q_rijeci, q_kodovi, None, obj + "; druga širina", debljina=t["debljina"], q_sufiksi=q_sufiksi)
        if rez2.kandidati and (not rez.kandidati or rez2.kandidati[0][2] > rez.kandidati[0][2] + 0.5):
            rez2.razina = "za_potvrdu"
            rez = rez2
    rez.klasa = klasa
    return rez


def _trake_kandidati(upit, trs, df, q_rijeci, q_kodovi, klasa, obj, debljina=None, q_sufiksi=()):
    kand = []
    for tr in trs:
        if tr["vrsta"] not in ("ABS", "PVC"):
            continue
        if klasa and tr["klasa"] != klasa:
            continue
        if debljina is not None and (tr["deb"] is None or abs(tr["deb"] - debljina) > 0.01):
            continue
        if not moguc(q_rijeci, q_kodovi, tr):
            continue
        s, promasaji = _bodovi(q_rijeci, q_kodovi, tr, df, len(trs), q_sufiksi)
        if s > -0.5:
            kand.append((s, tr, promasaji))
    kand.sort(key=lambda x: -x[0])
    return _odluka(upit, kand, potpuni=True, objasnjenje=obj, q_rijeci=q_rijeci)


def potvrdi_traku(conn, alias, traka_id, tko, materijal_id=None, izvor="rucno", klasa=None):
    """Potvrđeni par oznaka → traka; uz materijal (ISTI-oznake) upisuje i zadanu traku materijala za tu klasu (D-31)."""
    conn.execute("INSERT INTO traka_alias (alias, alias_norm, materijal_id, traka_id, izvor, potvrdio, kada) VALUES (?, ?, ?, ?, ?, ?, ?) "
                 "ON CONFLICT(alias_norm, materijal_id) DO UPDATE SET traka_id = excluded.traka_id, izvor = excluded.izvor, potvrdio = excluded.potvrdio, kada = excluded.kada",
                 (alias.strip(), norm(alias), materijal_id, traka_id, izvor, tko, sada()))
    if materijal_id:
        k = klasa or conn.execute("SELECT klasa FROM traka WHERE id = ?", (traka_id,)).fetchone()[0]
        if k:
            conn.execute("INSERT INTO materijal_traka (materijal_id, klasa, traka_id, izvor, potvrdio, kada) VALUES (?, ?, ?, ?, ?, ?) "
                         "ON CONFLICT(materijal_id, klasa) DO UPDATE SET traka_id = excluded.traka_id, izvor = excluded.izvor, potvrdio = excluded.potvrdio, kada = excluded.kada",
                         (materijal_id, k, traka_id, izvor, tko, sada()))
    conn.commit()


def usluga_kantiranja(klasa):
    """Ident usluge kantiranja po klasi trake (D-20 / skill krojna-ponuda): 0,5 mm → US000003, 1 i 2 mm /22 → US000011, /44 → US000012."""
    if not klasa:
        return None
    deb, sir = klasa.split("/")
    if sir == "44":
        return "US000012"
    if deb == "0,5":
        return "US000003"
    return "US000011"
