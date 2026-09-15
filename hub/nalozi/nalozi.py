# -*- coding: utf-8 -*-
"""Nalog i elementi (kralježnica korak 2, 04 §4): otvaranje naloga, materijali s zadanim trakama, elementi s rubovima, tok statusa (D-35),
događaji (D-42), popis „za potvrdu“ (D-32) i pretvorba u element-zapis za exporte (hub.formati.nalog_io).

Naziv naloga = KUPAC_NAZIV_BROJ (D-33): kratki naziv kupca, kupčev naziv projekta, Hub broj (brojač po godini u `postavke`).
Rubovi elementa: rub1..rub4 = lijevo, dolje, desno, gore (duža1, kraća1, duža2, kraća2 — isti redoslijed kao CPW, 04 §5.1);
u svakom rubu se čuva tekst iz naloga (rubX_kod: 'ABS-ISTI', 'MEL-ISTI', '1/22 JELA TAVERNA'…) i prepoznata traka (rubX_traka_id).
Materijal ili rub koji šifrarnik nije siguran → provjeri = 1 → na ekranu „za potvrdu“; potvrda upisuje alias (D-32) i ponavlja prepoznavanje.
"""
import re
from datetime import date

from ..db import sada, dnevnik, postavka, postavi
from ..sifrarnici import prepoznaj as P
from ..sifrarnici.nazivi import norm

STATUSI = ["unos", "ponuda", "potvrdjeno", "skladiste", "pila_nesting", "proizvodnja", "zatvoren"]
PRIJELAZI = {                                    # D-35; natrag samo dok kupac nije potvrdio (ispravak ponude)
    "unos": ["ponuda", "zatvoren"],
    "ponuda": ["potvrdjeno", "unos", "zatvoren"],
    "potvrdjeno": ["skladiste", "ponuda"],
    "skladiste": ["pila_nesting", "potvrdjeno"],
    "pila_nesting": ["proizvodnja", "skladiste"],
    "proizvodnja": ["zatvoren", "pila_nesting"],
    "zatvoren": [],
}
STATUS_NAZIV = {"unos": "Unos", "ponuda": "Ponuda — čeka kupca", "potvrdjeno": "Potvrđeno", "skladiste": "Skladište",
                "pila_nesting": "Pila / nesting", "proizvodnja": "Proizvodnja", "zatvoren": "Zatvoren"}
RUBOVI = ("L", "O", "D", "G")                    # rub1..rub4
TRAKE_ZADANE = ("MEL-ISTI", "ABS-ISTI", "ABS-ISTI 2mm")   # izbornik iznad daske (D-31, D-36)
NAPOMENA_ETIKETA = 14                            # znakova napomene koji stanu na etiketu (D-38)


class NalogGreska(ValueError):
    pass


# ---------------------------------------------------------------- pomoćno
def korisnik_id(conn, oznaka):
    """id korisnika po oznaci (IVANA, GORAN…); nepoznata oznaka → WEB (dnevnik ipak pamti tekst)."""
    r = conn.execute("SELECT id FROM korisnik WHERE oznaka = ?", ((oznaka or "WEB").upper(),)).fetchone()
    if not r:
        r = conn.execute("SELECT id FROM korisnik WHERE oznaka = 'WEB'").fetchone()
    return r[0] if r else None


def sljedeci_broj(conn, godina=None):
    """Hub broj naloga: brojač po godini u postavkama (D-33/D-40) → (2026, 123, '2026-00123')."""
    godina = godina or date.today().year
    kljuc = "brojac_naloga_%d" % godina
    zadnji = postavka(conn, kljuc)
    n = int(zadnji) + 1 if zadnji else int(postavka(conn, "brojac_naloga_pocetak", "1") or 1)
    postavi(conn, kljuc, str(n), "zadnji dodijeljeni broj naloga u %d" % godina)
    return godina, n, "%d-%05d" % (godina, n)


def _cisti_dio(s):
    s = norm(s or "")
    s = re.sub(r"[^A-Z0-9]+", "_", s).strip("_")
    return re.sub(r"_+", "_", s)


def naziv_naloga(kupac_kratki, projekt, n):
    """KUPAC_NAZIV_BROJ bez dijakritike i razmaka (ide u imena datoteka i na naljepnice, D-33): HUMER + OMIS + 2823 → HUMER_OMIS_2823."""
    dijelovi = [d for d in (_cisti_dio(kupac_kratki) or "KUPAC", _cisti_dio(projekt)) if d]
    return "_".join(dijelovi + [str(n)])


# ---------------------------------------------------------------- nalog
def novi_nalog(conn, tko, kupac_id=None, kupac_kratki=None, projekt="", vrsta="usluga", izvor="rucno", kerf=None, napomena=None,
               rok_kupca=None, corpus_projekt=None, broj=None, redni=None):
    """Otvori nalog u statusu 'unos'. Rabat se kopira s kupca (ili zadani), broj i naziv dodjeljuje Hub.
    broj / redni: samo za probne naloge (provjera) — vlastiti broj koji NE troši godišnji brojač naloga."""
    from .kupci import kratki_naziv
    if vrsta not in ("usluga", "vlastita_proizvodnja"):
        raise NalogGreska("vrsta mora biti usluga ili vlastita_proizvodnja")
    k = conn.execute("SELECT * FROM kupac WHERE id = ?", (kupac_id,)).fetchone() if kupac_id else None
    if kupac_id and not k:
        raise NalogGreska("nema kupca %s" % kupac_id)
    if not kupac_kratki:
        kupac_kratki = kratki_naziv(k["naziv"]) if k else "KUPAC"
    if broj:
        n = redni if redni is not None else 0
    else:
        godina, n, broj = sljedeci_broj(conn)
    naziv = naziv_naloga(kupac_kratki, projekt, n)
    krajnji = bool(k) and k["vrsta"] == "krajnji"
    rab_m = (k["rabat_materijal"] if k and k["rabat_materijal"] is not None else float(postavka(conn, "rabat_krajnji_materijal" if krajnji else "rabat_materijal_zadano", "0" if krajnji else "15") or 0))
    rab_u = (k["rabat_usluge"] if k and k["rabat_usluge"] is not None else float(postavka(conn, "rabat_krajnji_usluge" if krajnji else "rabat_usluge_zadano", "0" if krajnji else "20") or 0))
    kerf = kerf if kerf is not None else float(postavka(conn, "kerf", "16") or 16)
    tko_id = korisnik_id(conn, tko)
    cur = conn.execute("INSERT INTO nalog (broj, naziv, kupac_id, vrsta, izvor, corpus_projekt, status, datum, izradio_id, kerf, rabat_materijal, "
                       "rabat_usluge, rok_kupca, napomena) VALUES (?, ?, ?, ?, ?, ?, 'unos', ?, ?, ?, ?, ?, ?, ?)",
                       (broj, naziv, kupac_id, vrsta, izvor, corpus_projekt, sada(), tko_id, kerf, rab_m, rab_u, rok_kupca, napomena))
    nid = cur.lastrowid
    conn.execute("INSERT INTO dogadjaj (nalog_id, kada, tko_id, iz_statusa, u_status, razlog) VALUES (?, ?, ?, NULL, 'unos', ?)",
                 (nid, sada(), tko_id, "nalog otvoren (%s)" % izvor))
    dnevnik(conn, tko, "nalog", nid, "novi", "%s %s" % (broj, naziv))
    conn.commit()
    return nalog(conn, nid)


def nalog(conn, nalog_id):
    r = conn.execute("SELECT n.*, k.naziv AS kupac_naziv, k.mjesto AS kupac_mjesto, k.email AS kupac_email, k.telefon AS kupac_telefon, k.vrsta AS kupac_vrsta, "
                     "k.pantheon_subjekt_racun AS kupac_pantheon_subjekt, ki.oznaka AS izradio, kp.oznaka AS potvrdio "
                     "FROM nalog n LEFT JOIN kupac k ON k.id = n.kupac_id LEFT JOIN korisnik ki ON ki.id = n.izradio_id "
                     "LEFT JOIN korisnik kp ON kp.id = n.potvrdio_id WHERE n.id = ?", (nalog_id,)).fetchone()
    if not r:
        raise NalogGreska("nema naloga %s" % nalog_id)
    d = dict(r)
    d["status_naziv"] = STATUS_NAZIV.get(d["status"], d["status"])
    if d["kupac_id"]:                                                        # cijela kartica kupca: ekran je puni sam kad se kupac izabere (D-48)
        k = conn.execute("SELECT id, naziv, naziv_puni, vrsta, izvor, pantheon_subjekt, pantheon_subjekt_racun, adresa, posta, mjesto, oib, email, telefon, "
                         "rabat_materijal, rabat_usluge, dani_placanja, napomena FROM kupac WHERE id = ?", (d["kupac_id"],)).fetchone()
        d["kupac"] = dict(k) if k else None
    else:
        d["kupac"] = None
    return d


def po_nazivu(conn, naziv):
    r = conn.execute("SELECT id FROM nalog WHERE naziv = ? OR broj = ?", (naziv, naziv)).fetchone()
    return r[0] if r else None


def uredi_nalog(conn, nalog_id, tko, **polja):
    dopusteno = {"naziv", "kupac_id", "vrsta", "kerf", "rabat_materijal", "rabat_usluge", "rok_kupca", "rok_obecan", "prioritet", "napomena", "corpus_projekt", "izvor"}
    p = {k: v for k, v in polja.items() if k in dopusteno}
    if p:
        if "naziv" in p:
            p["naziv"] = _cisti_dio(p["naziv"]) or nalog(conn, nalog_id)["naziv"]
        conn.execute("UPDATE nalog SET " + ", ".join("%s = :%s" % (k, k) for k in p) + " WHERE id = :id", dict(p, id=nalog_id))
        dnevnik(conn, tko, "nalog", nalog_id, "uredi", ", ".join("%s=%s" % kv for kv in p.items()))
        conn.commit()
    return nalog(conn, nalog_id)


def popis(conn, status=None, q=None, limit=200, kupac_id=None):
    """Popis naloga za ekran 1 (svi korisnici isti popis, filter po statusu — D-34)."""
    uvjeti, par = [], []
    if status:
        uvjeti.append("n.status = ?")
        par.append(status)
    if kupac_id:
        uvjeti.append("n.kupac_id = ?")
        par.append(kupac_id)
    if q:
        uvjeti.append("(UPPER(n.naziv) LIKE ? OR n.broj LIKE ? OR UPPER(k.naziv) LIKE ?)")
        par += ["%" + norm(q).replace(" ", "_") + "%", "%" + q + "%", "%" + norm(q) + "%"]
    sql = ("SELECT n.id, n.broj, n.naziv, n.status, n.vrsta, n.izvor, n.datum, n.rok_obecan, n.rok_kupca, n.prioritet, n.ponuda_pantheon, "
           "k.naziv AS kupac_naziv, ki.oznaka AS izradio, "
           "(SELECT COUNT(*) FROM nalog_materijal m WHERE m.nalog_id = n.id) AS materijala, "
           "(SELECT COUNT(*) FROM element e JOIN nalog_materijal m ON m.id = e.nalog_materijal_id WHERE m.nalog_id = n.id) AS elemenata, "
           "(SELECT COALESCE(SUM(e.kom), 0) FROM element e JOIN nalog_materijal m ON m.id = e.nalog_materijal_id WHERE m.nalog_id = n.id) AS komada, "
           "(SELECT COUNT(*) FROM nalog_materijal m WHERE m.nalog_id = n.id AND (m.provjeri = 1 OR m.materijal_id IS NULL)) "
           " + (SELECT COUNT(*) FROM element e JOIN nalog_materijal m ON m.id = e.nalog_materijal_id WHERE m.nalog_id = n.id AND e.provjeri = 1) AS za_potvrdu "
           "FROM nalog n LEFT JOIN kupac k ON k.id = n.kupac_id LEFT JOIN korisnik ki ON ki.id = n.izradio_id "
           + ("WHERE " + " AND ".join(uvjeti) if uvjeti else "") + " ORDER BY n.id DESC LIMIT ?")
    out = []
    for r in conn.execute(sql, par + [limit]):
        d = dict(r)
        d["status_naziv"] = STATUS_NAZIV.get(d["status"], d["status"])
        out.append(d)
    return out


# ---------------------------------------------------------------- statusi i događaji
def postavi_status(conn, nalog_id, novi, tko, razlog=None, veza=None, **potvrda):
    """Prijelaz po D-35; svaki prijelaz = događaj (D-42). Za 'potvrdjeno' se upisuju datum/način potvrde, rok_obecan, prioritet (dijalog 3b)."""
    n = nalog(conn, nalog_id)
    if novi not in STATUSI:
        raise NalogGreska("nepoznat status %s" % novi)
    if novi not in PRIJELAZI[n["status"]]:
        raise NalogGreska("iz statusa '%s' ne može u '%s' (dopušteno: %s)" % (n["status"], novi, ", ".join(PRIJELAZI[n["status"]]) or "ništa"))
    tko_id = korisnik_id(conn, tko)
    if novi == "potvrdjeno":
        conn.execute("UPDATE nalog SET potvrda_kupca_datum = COALESCE(?, potvrda_kupca_datum, ?), potvrda_kupca_nacin = COALESCE(?, potvrda_kupca_nacin), "
                     "rok_obecan = COALESCE(?, rok_obecan), prioritet = COALESCE(?, prioritet), potvrdio_id = ? WHERE id = ?",
                     (potvrda.get("datum"), sada()[:10], potvrda.get("nacin"), potvrda.get("rok_obecan"), potvrda.get("prioritet"), tko_id, nalog_id))
    if novi == "ponuda" and n["status"] == "unos" and broj_za_potvrdu(conn, nalog_id):
        raise NalogGreska("nalog ima stavke za potvrdu — prvo potvrditi materijale i trake")
    conn.execute("UPDATE nalog SET status = ? WHERE id = ?", (novi, nalog_id))
    conn.execute("INSERT INTO dogadjaj (nalog_id, kada, tko_id, iz_statusa, u_status, razlog, veza) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (nalog_id, sada(), tko_id, n["status"], novi, razlog, veza))
    dnevnik(conn, tko, "nalog", nalog_id, "status", "%s → %s%s" % (n["status"], novi, (" (" + razlog + ")") if razlog else ""))
    conn.commit()
    return nalog(conn, nalog_id)


def dogadjaji(conn, nalog_id):
    return [dict(r) for r in conn.execute("SELECT d.id, d.kada, k.oznaka AS tko, d.iz_statusa, d.u_status, d.razlog, d.veza FROM dogadjaj d "
                                          "LEFT JOIN korisnik k ON k.id = d.tko_id WHERE d.nalog_id = ? ORDER BY d.id", (nalog_id,))]


def broj_za_potvrdu(conn, nalog_id):
    m = conn.execute("SELECT COUNT(*) FROM nalog_materijal WHERE nalog_id = ? AND (provjeri = 1 OR materijal_id IS NULL)", (nalog_id,)).fetchone()[0]
    e = conn.execute("SELECT COUNT(*) FROM element e JOIN nalog_materijal m ON m.id = e.nalog_materijal_id WHERE m.nalog_id = ? AND e.provjeri = 1", (nalog_id,)).fetchone()[0]
    return m + e


# ---------------------------------------------------------------- materijali naloga
def dodaj_materijal(conn, nalog_id, tko, materijal_id=None, naziv_ulaz=None, debljina_ulaz=None, winstore_kod_ulaz=None, god=None,
                    traka_zadana="ABS-ISTI", napomena=None, sirina_ploce=None):
    """Materijal u nalog: po identu (ručni unos) ili po tekstu iz datoteke (prepoznavanje). Vraća (nalog_materijal dict, Rezultat|None)."""
    n = nalog(conn, nalog_id)
    if n["status"] not in ("unos", "ponuda"):
        raise NalogGreska("materijali se mijenjaju samo u statusu unos / ponuda")
    if traka_zadana not in TRAKE_ZADANE:
        raise NalogGreska("traka_zadana mora biti jedna od: %s" % ", ".join(TRAKE_ZADANE))
    rez = None
    provjeri = 0
    if materijal_id is None and naziv_ulaz:
        rez = P.prepoznaj_materijal(conn, naziv_ulaz, debljina=debljina_ulaz, winstore_kod=winstore_kod_ulaz, sirina_ploce=sirina_ploce)
        materijal_id = rez.id if rez.siguran else None
        provjeri = 0 if rez.siguran else 1
    if materijal_id is None and not naziv_ulaz:
        raise NalogGreska("treba materijal_id ili naziv_ulaz")
    m = conn.execute("SELECT id, god, pantheon_ident FROM materijal WHERE id = ?", (materijal_id,)).fetchone() if materijal_id else None
    if materijal_id and not m:
        raise NalogGreska("nema materijala id %s" % materijal_id)
    if god is None and m is not None:
        god = m["god"]
    rb = (conn.execute("SELECT COALESCE(MAX(rb), 0) FROM nalog_materijal WHERE nalog_id = ?", (nalog_id,)).fetchone()[0] or 0) + 1
    cur = conn.execute("INSERT INTO nalog_materijal (nalog_id, materijal_id, naziv_ulaz, debljina_ulaz, winstore_kod_ulaz, provjeri, god, traka_zadana, napomena, rb) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (nalog_id, materijal_id, naziv_ulaz, debljina_ulaz, winstore_kod_ulaz, provjeri, god, traka_zadana, napomena, rb))
    nm_id = cur.lastrowid
    dnevnik(conn, tko, "nalog_materijal", nm_id, "dodaj", "%s: %s → %s%s" % (n["naziv"], naziv_ulaz or "", m["pantheon_ident"] if m else "?", " (za potvrdu)" if provjeri else ""))
    conn.commit()
    return materijal_naloga(conn, nm_id), rez


def materijal_naloga(conn, nm_id):
    r = conn.execute("SELECT nm.*, m.pantheon_ident AS ident, m.naziv_pantheon AS naziv, m.naziv_kratki, m.vrsta, m.debljina, m.winstore_kod, m.ploca_L AS m_ploca_L, "
                     "m.ploca_W AS m_ploca_W, m.god AS m_god FROM nalog_materijal nm LEFT JOIN materijal m ON m.id = nm.materijal_id WHERE nm.id = ?", (nm_id,)).fetchone()
    if not r:
        raise NalogGreska("nema materijala naloga %s" % nm_id)
    d = dict(r)
    d["trake"] = {}
    if d["materijal_id"]:
        for t in conn.execute("SELECT mt.klasa, tr.pantheon_ident, tr.naziv, mt.izvor FROM materijal_traka mt JOIN traka tr ON tr.id = mt.traka_id WHERE mt.materijal_id = ?", (d["materijal_id"],)):
            d["trake"][t["klasa"]] = dict(ident=t["pantheon_ident"], naziv=t["naziv"], izvor=t["izvor"])
    return d


def uredi_materijal(conn, nm_id, tko, **polja):
    dopusteno = {"put", "put_prijedlog", "god", "ploca_L", "ploca_W", "traka_zadana", "napomena", "rb"}
    p = {k: v for k, v in polja.items() if k in dopusteno}
    if "traka_zadana" in p and p["traka_zadana"] not in TRAKE_ZADANE:
        raise NalogGreska("traka_zadana mora biti jedna od: %s" % ", ".join(TRAKE_ZADANE))
    if p:
        conn.execute("UPDATE nalog_materijal SET " + ", ".join("%s = :%s" % (k, k) for k in p) + " WHERE id = :id", dict(p, id=nm_id))
        dnevnik(conn, tko, "nalog_materijal", nm_id, "uredi", ", ".join("%s=%s" % kv for kv in p.items()))
        conn.commit()
    return materijal_naloga(conn, nm_id)


def potvrdi_materijal_naloga(conn, nm_id, materijal_id, tko, zapamti=True):
    """Čovjek je izabrao materijal za tekst iz datoteke → upiši, zapamti alias (D-32) i ponovno prepoznaj rubove elemenata."""
    nm = materijal_naloga(conn, nm_id)
    m = conn.execute("SELECT id, god, pantheon_ident FROM materijal WHERE id = ?", (materijal_id,)).fetchone()
    if not m:
        raise NalogGreska("nema materijala id %s" % materijal_id)
    conn.execute("UPDATE nalog_materijal SET materijal_id = ?, provjeri = 0, god = COALESCE(god, ?) WHERE id = ?", (materijal_id, m["god"], nm_id))
    if zapamti and nm["naziv_ulaz"]:
        P.potvrdi_materijal(conn, nm["naziv_ulaz"], materijal_id, tko, izvor="nalog")
    dnevnik(conn, tko, "nalog_materijal", nm_id, "potvrda", "%s → %s" % (nm["naziv_ulaz"], m["pantheon_ident"]))
    conn.commit()
    _prepoznaj_rubove(conn, nm_id, samo_provjeri=False)
    return materijal_naloga(conn, nm_id)


def obrisi_materijal(conn, nm_id, tko):
    nm = materijal_naloga(conn, nm_id)
    n = nalog(conn, nm["nalog_id"])
    if n["status"] not in ("unos", "ponuda"):
        raise NalogGreska("materijali se mijenjaju samo u statusu unos / ponuda")
    conn.execute("DELETE FROM element WHERE nalog_materijal_id = ?", (nm_id,))
    conn.execute("DELETE FROM nalog_materijal WHERE id = ?", (nm_id,))
    dnevnik(conn, tko, "nalog_materijal", nm_id, "obrisi", nm["naziv_ulaz"] or nm["ident"] or "")
    conn.commit()


# ---------------------------------------------------------------- elementi
def _oznaka_ruba(tekst, tip, traka_zadana):
    """Tekst ruba iz datoteke → oznaka za prepoznavanje: prazno + tip 'M' → MEL-ISTI, 'A' → zadana ABS oznaka materijala (D-31)."""
    t = (tekst or "").strip()
    if t:
        return t
    tip = (tip or "").strip().upper()
    if tip == "M":
        return "MEL-ISTI"
    if tip == "A":
        return traka_zadana or "ABS-ISTI"
    return ""


def tip_ruba(klasa, kod):
    """Oznaka vrste ruba za CPW / obračun: 'M' tanka melaminska traka, 'A' ABS, prazno bez ruba.

    Odlučuje klasa prepoznate trake (0,5 mm = M), a kad trake nema ili je klasa nepoznata — tekst oznake iz naloga
    (`MEL-ISTI`, `MEL CRNA NK`). Bez toga bi rub koji je operater naručio kao melamin, a šifrarnik ga nije prepoznao,
    otišao u PanelWizard kao ABS i bio skuplje naplaćen."""
    klasa = (klasa or "").strip()
    kod = (kod or "").strip().upper()
    if not (klasa or kod):
        return ""
    if klasa.startswith("0,5"):
        return "M"
    if not klasa and (kod.startswith("MEL") or kod.startswith("0,5")):
        return "M"
    return "A"


def dodaj_element(conn, nm_id, tko, L, W, kom, naziv=None, rubovi=None, tipovi=None, god=None, napomena=None, izvor="rucno",
                  cix_ime=None, cix_izvor=None, obrada=None, program1=None, program2=None, ljepljenje=None, cjelina=None, pozicija=None, gotova_mjera=None):
    """rubovi = {'L':tekst,'O':tekst,'D':tekst,'G':tekst} (lijevo, dolje, desno, gore); tipovi = {'L':'M'|'A'|''…} kad tekst nedostaje.
    Rub s tekstom prolazi prepoznavanje trake uz materijal; nesiguran rub → element.provjeri = 1."""
    nm = materijal_naloga(conn, nm_id)
    n = nalog(conn, nm["nalog_id"])
    if n["status"] not in ("unos", "ponuda"):
        raise NalogGreska("elementi se mijenjaju samo u statusu unos / ponuda")
    L, W, kom = float(L), float(W), int(kom)
    if L <= 0 or W <= 0 or kom <= 0:
        raise NalogGreska("mjere i količina moraju biti veće od 0")
    rubovi = rubovi or {}
    tipovi = tipovi or {}
    rb = (conn.execute("SELECT COALESCE(MAX(rb), 0) FROM element WHERE nalog_materijal_id = ?", (nm_id,)).fetchone()[0] or 0) + 1
    if god is None:
        god = "H" if nm.get("god") else None
    cur = conn.execute("INSERT INTO element (nalog_materijal_id, rb, naziv, L, W, kom, god, gotova_mjera, obrada, program1, program2, ljepljenje, napomena, "
                       "cix_ime, cix_izvor, cjelina, pozicija, izvor, provjeri) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                       (nm_id, rb, naziv, L, W, kom, god, gotova_mjera, obrada, program1, program2, ljepljenje, napomena, cix_ime, cix_izvor, cjelina, pozicija, izvor))
    eid = cur.lastrowid
    kodovi = {r: _oznaka_ruba(rubovi.get(r), tipovi.get(r), nm["traka_zadana"]) for r in RUBOVI}
    conn.execute("UPDATE element SET rub1_kod = ?, rub2_kod = ?, rub3_kod = ?, rub4_kod = ? WHERE id = ?", (kodovi["L"] or None, kodovi["O"] or None, kodovi["D"] or None, kodovi["G"] or None, eid))
    _prepoznaj_rubove_elementa(conn, eid, nm["materijal_id"])
    conn.commit()
    return element(conn, eid)


def element(conn, eid):
    r = conn.execute("SELECT e.*, t1.pantheon_ident AS rub1_traka, t1.naziv AS rub1_naziv, t1.klasa AS rub1_klasa, "
                     "t2.pantheon_ident AS rub2_traka, t2.naziv AS rub2_naziv, t2.klasa AS rub2_klasa, "
                     "t3.pantheon_ident AS rub3_traka, t3.naziv AS rub3_naziv, t3.klasa AS rub3_klasa, "
                     "t4.pantheon_ident AS rub4_traka, t4.naziv AS rub4_naziv, t4.klasa AS rub4_klasa FROM element e "
                     "LEFT JOIN traka t1 ON t1.id = e.rub1_traka_id LEFT JOIN traka t2 ON t2.id = e.rub2_traka_id "
                     "LEFT JOIN traka t3 ON t3.id = e.rub3_traka_id LEFT JOIN traka t4 ON t4.id = e.rub4_traka_id WHERE e.id = ?", (eid,)).fetchone()
    if not r:
        raise NalogGreska("nema elementa %s" % eid)
    d = dict(r)
    d["napomena_etiketa"] = (d["napomena"] or "")[:NAPOMENA_ETIKETA]
    d["m2"] = round(d["L"] * d["W"] * d["kom"] / 1e6, 4)
    return d


def _prepoznaj_rubove_elementa(conn, eid, materijal_id):
    e = conn.execute("SELECT rub1_kod, rub2_kod, rub3_kod, rub4_kod FROM element WHERE id = ?", (eid,)).fetchone()
    ids, provjeri = [], 0
    for i, kod in enumerate(e):
        if not kod:
            ids.append(None)
            continue
        r = P.prepoznaj_traku(conn, kod, materijal_id=materijal_id) if materijal_id else None
        if r is not None and r.siguran:
            ids.append(r.id)
        else:
            ids.append(None)                 # nesigurno ostaje prazno (kandidati su u za_potvrdu) — ništa nepotvrđeno ne ide dalje
            provjeri = 1
    conn.execute("UPDATE element SET rub1_traka_id = ?, rub2_traka_id = ?, rub3_traka_id = ?, rub4_traka_id = ?, provjeri = ? WHERE id = ?", (*ids, provjeri, eid))


def _prepoznaj_rubove(conn, nm_id, samo_provjeri=True):
    nm = conn.execute("SELECT materijal_id FROM nalog_materijal WHERE id = ?", (nm_id,)).fetchone()
    sql = "SELECT id FROM element WHERE nalog_materijal_id = ?" + (" AND provjeri = 1" if samo_provjeri else "")
    for (eid,) in conn.execute(sql, (nm_id,)).fetchall():
        _prepoznaj_rubove_elementa(conn, eid, nm["materijal_id"])
    conn.commit()


def uredi_element(conn, eid, tko, **polja):
    """Mjere, količina, god, napomena, rubovi (rubovi={'L':…}) — ponovno prepoznaje rubove."""
    e = element(conn, eid)
    nm = materijal_naloga(conn, e["nalog_materijal_id"])
    dopusteno = {"naziv", "L", "W", "kom", "god", "gotova_mjera", "obrada", "program1", "program2", "ljepljenje", "napomena", "cjelina", "pozicija", "rb"}
    p = {k: v for k, v in polja.items() if k in dopusteno}
    rubovi = polja.get("rubovi")
    if rubovi:
        for i, r in enumerate(RUBOVI, 1):
            if r in rubovi:
                p["rub%d_kod" % i] = (rubovi[r] or "").strip() or None
    if p:
        conn.execute("UPDATE element SET " + ", ".join("%s = :%s" % (k, k) for k in p) + " WHERE id = :id", dict(p, id=eid))
    if rubovi or "rubovi" in polja:
        _prepoznaj_rubove_elementa(conn, eid, nm["materijal_id"])
    dnevnik(conn, tko, "element", eid, "uredi", ", ".join("%s=%s" % kv for kv in p.items()))
    conn.commit()
    return element(conn, eid)


def obrisi_element(conn, eid, tko):
    e = element(conn, eid)
    conn.execute("DELETE FROM element WHERE id = ?", (eid,))
    dnevnik(conn, tko, "element", eid, "obrisi", "%gx%g x%d" % (e["L"], e["W"], e["kom"]))
    conn.commit()


def oznaka_ovisi_o_materijalu(oznaka):
    """'ABS-ISTI', 'MEL-ISTI', '1/22 ISTI' ovise o materijalu (ista boja); '1/22 JELA TAVERNA', 'MEL CRNA NK' imaju svoj dekor → vrijede za sve materijale."""
    from ..sifrarnici.nazivi import rasclani_traku
    t = rasclani_traku(oznaka)
    return bool(t["isti"] or not t["dekor"])


def potvrdi_traku_naloga(conn, nm_id, oznaka, traka_id, tko, zapamti=True):
    """Čovjek je za oznaku ruba uz materijal naloga izabrao traku → alias (D-32) + ponovno prepoznavanje u cijelom nalogu.
    ISTI-oznake se pamte uz materijal (i kao zadana traka te klase), oznake s vlastitim dekorom ('1/22 CHAMPAGNE UM') općenito."""
    nm = materijal_naloga(conn, nm_id)
    if not nm["materijal_id"]:
        raise NalogGreska("prvo potvrditi materijal")
    if zapamti:
        P.potvrdi_traku(conn, oznaka, traka_id, tko, materijal_id=nm["materijal_id"] if oznaka_ovisi_o_materijalu(oznaka) else None, izvor="nalog")
    else:
        n = norm(oznaka)
        for i in range(1, 5):
            conn.execute("UPDATE element SET rub%d_traka_id = ? WHERE nalog_materijal_id = ? AND rub%d_kod IS NOT NULL AND UPPER(rub%d_kod) = ?" % (i, i, i), (traka_id, nm_id, n))
    dnevnik(conn, tko, "nalog_materijal", nm_id, "potvrda_trake", "%s → traka %s" % (oznaka, traka_id))
    conn.commit()
    for (x,) in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? AND materijal_id IS NOT NULL", (nm["nalog_id"],)).fetchall():
        _prepoznaj_rubove(conn, x, samo_provjeri=True)


def ponovi_prepoznavanje(conn, nalog_id, tko="sustav"):
    """Nakon potvrda / novih aliasa: ponovno prepoznaj sve nesigurne materijale i rubove naloga. Vraća broj preostalih za potvrdu."""
    for nm in conn.execute("SELECT id, naziv_ulaz, debljina_ulaz, winstore_kod_ulaz FROM nalog_materijal WHERE nalog_id = ? AND (provjeri = 1 OR materijal_id IS NULL)", (nalog_id,)).fetchall():
        if not nm["naziv_ulaz"]:
            continue
        rez = P.prepoznaj_materijal(conn, nm["naziv_ulaz"], debljina=nm["debljina_ulaz"], winstore_kod=nm["winstore_kod_ulaz"])
        if rez.siguran:
            m = conn.execute("SELECT god FROM materijal WHERE id = ?", (rez.id,)).fetchone()
            conn.execute("UPDATE nalog_materijal SET materijal_id = ?, provjeri = 0, god = COALESCE(god, ?) WHERE id = ?", (rez.id, m["god"], nm["id"]))
            _prepoznaj_rubove(conn, nm["id"], samo_provjeri=False)
    for (nm_id,) in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? AND materijal_id IS NOT NULL", (nalog_id,)).fetchall():
        _prepoznaj_rubove(conn, nm_id, samo_provjeri=True)
    conn.commit()
    return broj_za_potvrdu(conn, nalog_id)


# ---------------------------------------------------------------- pregled naloga (ekran 2)
def za_potvrdu(conn, nalog_id):
    """Popis stavki koje čovjek mora potvrditi, s kandidatima (desni stupac „Provjere“ na ekranu 2)."""
    out = []
    for nm in conn.execute("SELECT * FROM nalog_materijal WHERE nalog_id = ? AND (provjeri = 1 OR materijal_id IS NULL) ORDER BY rb", (nalog_id,)):
        rez = P.prepoznaj_materijal(conn, nm["naziv_ulaz"] or "", debljina=nm["debljina_ulaz"], winstore_kod=nm["winstore_kod_ulaz"])
        out.append(dict(vrsta="materijal", nalog_materijal_id=nm["id"], tekst=nm["naziv_ulaz"], debljina=nm["debljina_ulaz"], razina=rez.razina,
                        objasnjenje=rez.objasnjenje, kandidati=[dict(ident=i, naziv=n, score=round(s, 2)) for i, n, s in rez.kandidati[:5]]))
    vidjeno = set()
    for e in conn.execute("SELECT e.id, e.nalog_materijal_id, e.rub1_kod, e.rub2_kod, e.rub3_kod, e.rub4_kod, nm.materijal_id FROM element e "
                          "JOIN nalog_materijal nm ON nm.id = e.nalog_materijal_id WHERE nm.nalog_id = ? AND e.provjeri = 1 ORDER BY nm.rb, e.rb", (nalog_id,)):
        if not e["materijal_id"]:
            continue                       # rubovi se rješavaju kad se potvrdi materijal
        for kod in (e["rub1_kod"], e["rub2_kod"], e["rub3_kod"], e["rub4_kod"]):
            kljuc = (e["nalog_materijal_id"] if oznaka_ovisi_o_materijalu(kod or "") else None, norm(kod or ""))
            if not kod or kljuc in vidjeno:
                continue
            r = P.prepoznaj_traku(conn, kod, materijal_id=e["materijal_id"])
            if r.siguran:
                continue
            vidjeno.add(kljuc)
            out.append(dict(vrsta="traka", nalog_materijal_id=e["nalog_materijal_id"], tekst=kod, klasa=r.klasa, razina=r.razina, objasnjenje=r.objasnjenje,
                            kandidati=[dict(ident=i, naziv=n, score=round(s, 2)) for i, n, s in r.kandidati[:5]]))
    return out


def pregled(conn, nalog_id):
    """Cijeli nalog za ekran 2: zaglavlje, kupac, materijali s elementima i zadanim trakama, događaji, stavke za potvrdu, sažetak."""
    d = nalog(conn, nalog_id)
    d["materijali"] = []
    uk_el = uk_kom = 0
    uk_m2 = 0.0
    for nm in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? ORDER BY rb, id", (nalog_id,)).fetchall():
        m = materijal_naloga(conn, nm["id"])
        m["elementi"] = [element(conn, e["id"]) for e in conn.execute("SELECT id FROM element WHERE nalog_materijal_id = ? ORDER BY rb, id", (nm["id"],))]
        m["elemenata"] = len(m["elementi"])
        m["komada"] = sum(e["kom"] for e in m["elementi"])
        m["m2"] = round(sum(e["m2"] for e in m["elementi"]), 3)
        uk_el += m["elemenata"]
        uk_kom += m["komada"]
        uk_m2 += m["m2"]
        d["materijali"].append(m)
    d["dogadjaji"] = dogadjaji(conn, nalog_id)
    d["za_potvrdu"] = za_potvrdu(conn, nalog_id)
    d["sazetak"] = dict(materijala=len(d["materijali"]), elemenata=uk_el, komada=uk_kom, m2=round(uk_m2, 3), za_potvrdu=len(d["za_potvrdu"]))
    return d


# ---------------------------------------------------------------- za exporte (korak 3): element-zapis kakav čitaju hub.formati.nalog_io
def elementi_za_export(conn, nalog_id):
    """Lista element-dictova (rb, nalog, kupac, L, W, kom, sifra_mat, deb, mat, god, traka{L,D,G,O}, tip{…}, cix, napomena, prolaza, glodalo)."""
    n = nalog(conn, nalog_id)
    out = []
    rb = 0
    for nm in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? ORDER BY rb, id", (nalog_id,)).fetchall():
        m = materijal_naloga(conn, nm["id"])
        deb = m["debljina"] or m["debljina_ulaz"] or 0
        for e in conn.execute("SELECT id FROM element WHERE nalog_materijal_id = ? ORDER BY rb, id", (nm["id"],)).fetchall():
            el = element(conn, e["id"])
            rb += 1
            traka, tip = {}, {}
            for i, r in enumerate(RUBOVI, 1):
                naziv_t = el["rub%d_naziv" % i]
                klasa = el["rub%d_klasa" % i] or ""
                traka[r] = naziv_t or (el["rub%d_kod" % i] or "")
                tip[r] = tip_ruba(klasa, el["rub%d_kod" % i])
            out.append(dict(rb=rb, nalog=n["naziv"], kupac=n["kupac_naziv"] or "", L=el["L"], W=el["W"], kom=el["kom"],
                            sifra_mat=m["winstore_kod"] or "", deb=deb, mat=m["naziv_kratki"] or m["naziv_ulaz"] or "",
                            god=1 if el["god"] else 0, traka=traka, tip=tip, cix=el["cix_ime"] or "", napomena=el["napomena_etiketa"],
                            prolaza=2 if (el["L"] < 200 or el["W"] < 200) else 1, glodalo=14 if deb > 20 else 12,
                            element_id=el["id"], materijal_ident=m["ident"], nalog_materijal_id=nm["id"]))
    return out
