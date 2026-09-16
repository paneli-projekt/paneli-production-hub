"""optimiziraj.py — optimizacija materijala naloga S POTVRDOM (D-75, korak 5b).

Ponuda i izvoz na pilu uvijek koriste ISTO slaganje, jer se iz tog dokumenta naručuje materijal (Igor, 16. 9. 2026.).
Hub po D-19 PREDLOŽI slaganje s najmanje materijala; korisnik ga provjeri (sheme) i POTVRDI; tek potvrđeno slaganje ide u
ponudu (obracun), CPO (export_pila) i nabavu. Alternative: način (auto | uzduzno | poprecno | trake) × dubina (brzo | najbolje).

    py -m hub.nalozi.optimiziraj --db hub.db --nalog 12                       (prijedlog auto/najbolje za sve materijale, bez potvrde)
    py -m hub.nalozi.optimiziraj --db hub.db --nalog 12 --materijal 40 --nacin poprecno --dubina brzo
    py -m hub.nalozi.optimiziraj --db hub.db --potvrdi 17 --tko IVANA
    py -m hub.nalozi.optimiziraj --db hub.db --nalog 12 --potvrdi-sve --tko IVANA   (potvrdi auto/najbolje prijedlog za sve — probe, CLI)

    GET  /api/nalog/{id}/optimizacija                       potvrđeno + prijedlozi po materijalu
    POST /api/nalog/{id}/materijal/{nm}/optimizacija        {nacin, dubina, tko} → novi prijedlog
    POST /api/optimizacija/{oid}/potvrdi                    {tko}
"""
import argparse
import hashlib
import json
import sys

from .. import db
from ..db import sada, dnevnik, postavka
from ..optimizacija import pila_optimizator as OPT
from . import nalozi as N

NACINI = ("auto", "uzduzno", "poprecno", "trake")
DUBINE = ("brzo", "najbolje")
TRIM = 10
AUTO_POTVRDA = False            # True samo za probe / testove: ponuda i izvoz sami potvrde auto/najbolje prijedlog (CLI --potvrdi-opt)


class OptimizacijaGreska(Exception):
    pass


def kerf_pile(conn):
    return float(postavka(conn, "kerf_pile", "5") or 5)


def _ploca(m):
    return float(m["ploca_L"] or m["m_ploca_L"] or 2800), float(m["ploca_W"] or m["m_ploca_W"] or 2070)


def ulaz_materijala(conn, nm_id):
    """Sve što optimizator treba za jedan materijal naloga: (m, els, dijelovi, ploca, trim, god, hash).
    els su u istom redoslijedu kao u export_pila / obracun (elementi_za_export), pa je idx = redni broj u toj listi."""
    m = N.materijal_naloga(conn, nm_id)
    els = [e for e in N.elementi_za_export(conn, m["nalog_id"]) if e["nalog_materijal_id"] == nm_id]
    dijelovi = [(k + 1, float(e["W"]), float(e["L"]), int(e["kom"])) for k, e in enumerate(els)]
    pL, pW = _ploca(m)
    trim = TRIM
    if any(e["L"] > pL - 2 * TRIM or e["W"] > pW - 2 * TRIM for e in els):
        trim = 0                                            # element na punu mjeru ploče: bez obreza (D-65/10)
    god = bool(m["god"]) or any(int(e.get("god", 0)) for e in els)
    h = hashlib.sha1(json.dumps([(e["element_id"], e["L"], e["W"], e["kom"]) for e in els] + [pL, pW, trim, god]).encode()).hexdigest()[:16]
    return m, els, dijelovi, (pL, pW), trim, god, h


def izracunaj(conn, nm_id, nacin="auto", dubina="najbolje"):
    """Složi materijal bez upisa. Vraća dict(sheets, oc, nacin, ploca, trim, kerf, god, hash, komada, elemenata, st)."""
    if nacin not in NACINI:
        raise OptimizacijaGreska("nepoznat način '%s' (auto | uzduzno | poprecno | trake)" % nacin)
    if dubina not in DUBINE:
        raise OptimizacijaGreska("nepoznata dubina '%s' (brzo | najbolje)" % dubina)
    m, els, dijelovi, ploca, trim, god, h = ulaz_materijala(conn, nm_id)
    if not els:
        raise OptimizacijaGreska("materijal %s nema elemenata" % (m["naziv_kratki"] or m["naziv_ulaz"] or nm_id))
    kerf = kerf_pile(conn)
    nacini = None if nacin == "auto" else (nacin,)
    try:
        sheets, oc, pobjednik, _ = OPT.najbolje(dijelovi, ploca, trim, kerf, god, nacini, brzo=(dubina == "brzo"))
    except ValueError as e:
        raise OptimizacijaGreska("%s: ne može se složiti (%s)" % (m["naziv_kratki"] or m["naziv_ulaz"], e))
    st = OPT.statistika(sheets, dijelovi, ploca)
    return dict(nalog_materijal_id=nm_id, sheets=sheets, oc=oc, nacin=pobjednik, nacin_trazen=nacin, dubina=dubina, ploca=ploca, trim=trim,
                kerf=kerf, god=god, hash=h, elemenata=len(els), komada=sum(int(e["kom"]) for e in els), st=st,
                element_ids=[e["element_id"] for e in els])


def _snimka(r):
    return json.dumps(dict(sheets=r["sheets"], element_ids=r["element_ids"], ploca=list(r["ploca"]), trim=r["trim"], kerf=r["kerf"], god=r["god"],
                           ostaci=r["oc"].get("ostaci")))


def predlozi(conn, nm_id, nacin="auto", dubina="najbolje", tko="web", commit=True):
    """Izračunaj i upiši PRIJEDLOG (status 'prijedlog'); stariji prijedlog istog načina i dubine postaje 'zamijenjeno'.
    Vraća red optimizacije (dict) s razlikom prema auto/najbolje prijedlogu ako postoji."""
    r = izracunaj(conn, nm_id, nacin, dubina)
    conn.execute("UPDATE optimizacija SET status = 'zamijenjeno' WHERE nalog_materijal_id = ? AND status = 'prijedlog' AND nacin_trazen = ? AND dubina = ?",
                 (nm_id, nacin, dubina))
    cur = conn.execute("INSERT INTO optimizacija (nalog_materijal_id, engine, nacin, datum, broj_ploca, iskoristenje, m2_dijelova, m2_ploca, m2_za_naplatu, "
                       "rezova, status, nacin_trazen, dubina, slaganje_json, elementi_hash, kerf, obrez) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (nm_id, "hub", r["nacin"], sada(), r["st"]["ploca"], r["st"]["iskoristenje"], r["st"]["m2_dijelova"], r["st"]["m2_bruto"],
                        r["oc"]["m2_naplata"], r["oc"]["rezova"], "prijedlog", nacin, dubina, _snimka(r), r["hash"], r["kerf"], r["trim"]))
    oid = cur.lastrowid
    dnevnik(conn, tko, "optimizacija", oid, "prijedlog", "nm %d %s/%s: %s, %d ploča, %.2f m²" % (nm_id, nacin, dubina, r["nacin"], r["st"]["ploca"], r["oc"]["m2_naplata"]))
    if commit:
        conn.commit()
    return red(conn, oid)


def red(conn, oid):
    r = conn.execute("SELECT * FROM optimizacija WHERE id = ?", (oid,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d.pop("slaganje_json", None)
    d.pop("sheme_json", None)
    auto = conn.execute("SELECT m2_za_naplatu, broj_ploca FROM optimizacija WHERE nalog_materijal_id = ? AND status IN ('prijedlog', 'potvrdjeno') "
                        "AND nacin_trazen = 'auto' AND dubina = 'najbolje' ORDER BY id DESC LIMIT 1", (r["nalog_materijal_id"],)).fetchone()
    if auto and r["m2_za_naplatu"] is not None and auto["m2_za_naplatu"] is not None and not (r["nacin_trazen"] == "auto" and r["dubina"] == "najbolje"):
        d["razlika_m2_prema_auto"] = round(r["m2_za_naplatu"] - auto["m2_za_naplatu"], 2)
        d["razlika_ploca_prema_auto"] = (r["broj_ploca"] or 0) - (auto["broj_ploca"] or 0)
    return d


def snimka(conn, oid):
    r = conn.execute("SELECT slaganje_json FROM optimizacija WHERE id = ?", (oid,)).fetchone()
    return json.loads(r["slaganje_json"]) if r and r["slaganje_json"] else None


def potvrdi(conn, oid, tko="web", commit=True):
    """Prijedlog → POTVRĐENO (jedino slaganje materijala). Dosadašnje potvrđeno postaje 'zamijenjeno'. Elementi promijenjeni u
    međuvremenu → greška (treba novi prijedlog). Vraća red + `ponuda_poslana` (True kad nalog već ima poslanu / potvrđenu ponudu — treba nova verzija)."""
    r = conn.execute("SELECT * FROM optimizacija WHERE id = ?", (oid,)).fetchone()
    if not r:
        raise OptimizacijaGreska("optimizacija %s ne postoji" % oid)
    if r["status"] not in ("prijedlog", "potvrdjeno"):
        raise OptimizacijaGreska("optimizacija %s nije prijedlog (status %s)" % (oid, r["status"]))
    nm_id = r["nalog_materijal_id"]
    m, els, dijelovi, ploca, trim, god, h = ulaz_materijala(conn, nm_id)
    if h != r["elementi_hash"]:
        conn.execute("UPDATE optimizacija SET status = 'zastarjelo' WHERE id = ?", (oid,))
        if commit:
            conn.commit()
        raise OptimizacijaGreska("elementi materijala su promijenjeni nakon prijedloga — napraviti novi prijedlog")
    n = N.nalog(conn, m["nalog_id"])
    if n["status"] not in ("unos", "ponuda", "potvrdjeno", "skladiste", "pila_nesting"):
        raise OptimizacijaGreska("optimizacija se ne može mijenjati u statusu '%s'" % n["status"])
    prije = conn.execute("SELECT id, m2_za_naplatu, broj_ploca FROM optimizacija WHERE nalog_materijal_id = ? AND status = 'potvrdjeno' AND id != ?",
                         (nm_id, oid)).fetchall()
    conn.execute("UPDATE optimizacija SET status = 'zamijenjeno' WHERE nalog_materijal_id = ? AND status = 'potvrdjeno' AND id != ?", (nm_id, oid))
    conn.execute("UPDATE optimizacija SET status = 'potvrdjeno', potvrdio_id = ?, potvrdjeno = ? WHERE id = ?", (N.korisnik_id(conn, tko), sada(), oid))
    ime = m["naziv_kratki"] or m["naziv_ulaz"] or str(nm_id)
    opis = "optimizacija potvrđena: %s %s/%s → %s, %d ploča, %.2f m²" % (ime, r["nacin_trazen"], r["dubina"], r["nacin"], r["broj_ploca"] or 0, r["m2_za_naplatu"] or 0)
    ponuda_poslana = bool(conn.execute("SELECT 1 FROM ponuda_verzija WHERE nalog_id = ? AND status IN ('poslana', 'potvrdjena') LIMIT 1", (m["nalog_id"],)).fetchone())
    if prije:
        p = prije[0]
        opis += " (zamjenjuje %d ploča / %.2f m²)" % (p["broj_ploca"] or 0, p["m2_za_naplatu"] or 0)
        if ponuda_poslana:
            opis += " — PONUDA JE VEĆ POSLANA, treba nova verzija"
    dnevnik(conn, tko, "optimizacija", oid, "potvrda", opis)
    conn.execute("INSERT INTO dogadjaj (nalog_id, kada, tko_id, iz_statusa, u_status, razlog) VALUES (?, ?, ?, ?, ?, ?)",
                 (m["nalog_id"], sada(), N.korisnik_id(conn, tko), n["status"], n["status"], opis))
    if commit:
        conn.commit()
    d = red(conn, oid)
    d["ponuda_poslana"] = ponuda_poslana and bool(prije)
    return d


def potvrdjena(conn, nm_id, provjeri=True):
    """Potvrđeno slaganje materijala (dict reda) ili None. Uz provjeri=True: ako su elementi promijenjeni, red postaje 'zastarjelo' i vraća se None."""
    r = conn.execute("SELECT * FROM optimizacija WHERE nalog_materijal_id = ? AND status = 'potvrdjeno' ORDER BY id DESC LIMIT 1", (nm_id,)).fetchone()
    if not r:
        return None
    if provjeri:
        _, _, _, _, _, _, h = ulaz_materijala(conn, nm_id)
        if h != r["elementi_hash"]:
            conn.execute("UPDATE optimizacija SET status = 'zastarjelo' WHERE id = ?", (r["id"],))
            conn.commit()
            return None
    return dict(r)


def slaganje(conn, nm_id):
    """(sheets, ploca, trim, kerf, god, red) potvrđenog slaganja ili None."""
    r = potvrdjena(conn, nm_id)
    if not r:
        return None
    s = json.loads(r["slaganje_json"])
    return s["sheets"], tuple(s["ploca"]), s["trim"], s["kerf"], s["god"], r


def prijedlog_auto(conn, nm_id):
    """Živi auto/najbolje prijedlog s istim elementima (sheets, ploca, trim, kerf, god, red) ili None — da obračun ne računa dvaput."""
    r = conn.execute("SELECT * FROM optimizacija WHERE nalog_materijal_id = ? AND status = 'prijedlog' AND nacin_trazen = 'auto' AND dubina = 'najbolje' "
                     "ORDER BY id DESC LIMIT 1", (nm_id,)).fetchone()
    if not r:
        return None
    _, _, _, _, _, _, h = ulaz_materijala(conn, nm_id)
    if h != r["elementi_hash"]:
        return None
    s = json.loads(r["slaganje_json"])
    return s["sheets"], tuple(s["ploca"]), s["trim"], s["kerf"], s["god"], dict(r)


def pripremi_prijedloge(conn, nalog_id, tko="web"):
    """Za svaki materijal naloga bez potvrđenog slaganja i bez živog auto prijedloga napravi auto/najbolje prijedlog (ekran obračuna, D-75)."""
    novi = []
    for nm in conn.execute("SELECT nm.id FROM nalog_materijal nm WHERE nm.nalog_id = ? AND EXISTS (SELECT 1 FROM element e WHERE e.nalog_materijal_id = nm.id) "
                           "ORDER BY nm.rb, nm.id", (nalog_id,)).fetchall():
        if not treba_optimizaciju(conn, nm["id"]) or potvrdjena(conn, nm["id"]) or prijedlog_auto(conn, nm["id"]):
            continue
        try:
            novi.append(predlozi(conn, nm["id"], "auto", "najbolje", tko, commit=False))
        except OptimizacijaGreska:
            continue
    return novi


def osiguraj_potvrdu(conn, nm_id, tko="web", auto=None):
    """Za ponudu / izvoz: vrati potvrđeno slaganje; ako ga nema i dopuštena je automatska potvrda (probe, CLI --potvrdi-opt),
    napravi auto/najbolje prijedlog i potvrdi ga; inače None."""
    s = slaganje(conn, nm_id)
    if s:
        return s
    auto = AUTO_POTVRDA if auto is None else auto
    if not auto:
        return None
    p = conn.execute("SELECT id FROM optimizacija WHERE nalog_materijal_id = ? AND status = 'prijedlog' AND nacin_trazen = 'auto' AND dubina = 'najbolje' "
                     "ORDER BY id DESC LIMIT 1", (nm_id,)).fetchone()
    oid = p["id"] if p else predlozi(conn, nm_id, "auto", "najbolje", tko, commit=False)["id"]
    try:
        potvrdi(conn, oid, tko, commit=False)
    except OptimizacijaGreska:
        oid = predlozi(conn, nm_id, "auto", "najbolje", tko, commit=False)["id"]
        potvrdi(conn, oid, tko, commit=False)
    conn.execute("UPDATE optimizacija SET napomena = 'potvrđeno automatski (proba / CLI)' WHERE id = ?", (oid,))
    return slaganje(conn, nm_id)


def treba_optimizaciju(conn, nm_id):
    """Materijal koji se slaže na ploču (ne RP/ZO po dužnom metru)."""
    m = N.materijal_naloga(conn, nm_id)
    if not m["materijal_id"]:
        return False
    v = conn.execute("SELECT vrsta FROM materijal WHERE id = ?", (m["materijal_id"],)).fetchone()
    return not (v and v["vrsta"] in ("RP", "ZO"))


def pregled(conn, nalog_id):
    """Po materijalu naloga: potvrđeno slaganje + živi prijedlozi (za ekran)."""
    out = []
    for nm in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? ORDER BY rb, id", (nalog_id,)).fetchall():
        m = N.materijal_naloga(conn, nm["id"])
        p = potvrdjena(conn, nm["id"])
        prijedlozi = [red(conn, r["id"]) for r in conn.execute("SELECT id FROM optimizacija WHERE nalog_materijal_id = ? AND status = 'prijedlog' ORDER BY id", (nm["id"],)).fetchall()]
        out.append(dict(nalog_materijal_id=nm["id"], materijal=m["naziv_kratki"] or m["naziv_ulaz"], ident=m["ident"], put=m["put"],
                        treba=treba_optimizaciju(conn, nm["id"]), potvrdjeno=red(conn, p["id"]) if p else None, prijedlozi=prijedlozi))
    return out


def nepotvrdjeni(conn, nalog_id):
    """Materijali naloga (s elementima) koji se slažu na ploču, a nemaju potvrđeno slaganje — imena."""
    out = []
    for nm in conn.execute("SELECT nm.id FROM nalog_materijal nm WHERE nm.nalog_id = ? AND EXISTS (SELECT 1 FROM element e WHERE e.nalog_materijal_id = nm.id) "
                           "ORDER BY nm.rb, nm.id", (nalog_id,)).fetchall():
        if treba_optimizaciju(conn, nm["id"]) and not potvrdjena(conn, nm["id"]):
            m = N.materijal_naloga(conn, nm["id"])
            out.append(m["naziv_kratki"] or m["naziv_ulaz"] or str(nm["id"]))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Optimizacija materijala naloga s potvrdom (D-75)")
    ap.add_argument("--db")
    ap.add_argument("--nalog", type=int)
    ap.add_argument("--materijal", type=int, help="nalog_materijal id (zadano: svi materijali naloga)")
    ap.add_argument("--nacin", default="auto", choices=NACINI)
    ap.add_argument("--dubina", default="najbolje", choices=DUBINE)
    ap.add_argument("--potvrdi", type=int, help="id prijedloga koji se potvrđuje")
    ap.add_argument("--potvrdi-sve", action="store_true", help="potvrdi auto/najbolje prijedlog za sve materijale naloga (probe)")
    ap.add_argument("--tko", default="cli")
    a = ap.parse_args(argv)
    conn = db.spoji(a.db)
    try:
        if a.potvrdi:
            r = potvrdi(conn, a.potvrdi, a.tko)
            print("potvrđeno #%d: %s, %d ploča, %.2f m²%s" % (r["id"], r["nacin"], r["broj_ploca"] or 0, r["m2_za_naplatu"] or 0,
                                                            " — ponuda je već poslana, treba nova verzija" if r.get("ponuda_poslana") else ""))
            return 0
        if not a.nalog:
            ap.error("--nalog ili --potvrdi")
        nms = [a.materijal] if a.materijal else [r["id"] for r in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? ORDER BY rb, id", (a.nalog,))]
        for nm_id in nms:
            if not treba_optimizaciju(conn, nm_id):
                continue
            if a.potvrdi_sve:
                s = osiguraj_potvrdu(conn, nm_id, a.tko, auto=True)
                conn.commit()
                print("%s: potvrđeno %s, %d ploča, %.2f m²" % (nm_id, s[5]["nacin"], s[5]["broj_ploca"] or 0, s[5]["m2_za_naplatu"] or 0))
                continue
            try:
                r = predlozi(conn, nm_id, a.nacin, a.dubina, a.tko)
            except OptimizacijaGreska as e:
                print("%s: %s" % (nm_id, e))
                continue
            print("prijedlog #%d nm %d %s/%s → %s: %d ploča, isk. %.1f %%, %.2f m² za naplatu%s" % (
                r["id"], nm_id, a.nacin, a.dubina, r["nacin"], r["broj_ploca"] or 0, 100 * (r["iskoristenje"] or 0), r["m2_za_naplatu"] or 0,
                (" (%+.2f m² prema auto)" % r["razlika_m2_prema_auto"]) if "razlika_m2_prema_auto" in r else ""))
        return 0
    except OptimizacijaGreska as e:
        print("GREŠKA:", e)
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
