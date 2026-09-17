"""optimiziraj.py — optimizacija materijala naloga S POTVRDOM (D-75, korak 5b).

Ponuda i izvoz na pilu uvijek koriste ISTO slaganje, jer se iz tog dokumenta naručuje materijal (Igor, 16. 9. 2026.).
Hub PREDLOŽI slaganje; korisnik ga provjeri (sheme) i POTVRDI; tek potvrđeno slaganje ide u ponudu (obracun), CPO (export_pila) i nabavu.
D-91 (Igor, 17. 9. 2026., opcija B): zadani prijedlog „auto“ = najmanje materijala koje PILA REALNO MOŽE IZREZATI uz ograničenja iz
postavki (pila_max_razina, pila_max_sirina_u_traci, pila_min_komad_4, pila_mijesana_orijentacija); način „hub“ = Hubov minimum bez
ograničenja (rezerva, prikazuje se razlika m²). Alternative: način (auto | hub | uzduzno | poprecno | trake) × dubina (brzo | najbolje).

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
from ..optimizacija import pila_optimizator as OPT, radne_ploce as RPP
from . import nalozi as N

NACINI = ("auto", "hub", "uzduzno", "poprecno", "trake")
DUBINE = ("brzo", "najbolje")
TRIM = 10
OGRANICENJA_ZADANO = dict(pila_max_razina=3, pila_max_sirina_u_traci=2, pila_min_komad_4=0, pila_mijesana_orijentacija=0)   # D-91, početno (Igor)
_KAND_CACHE = {}                # (hash, kerf, nacini, brzo, ogr) → kandidati iz OPT.najbolje — auto i hub prijedlog iz istog računa
_KAND_CACHE_MAX = 12
AUTO_POTVRDA = False            # True samo za probe / testove: ponuda i izvoz sami potvrde auto/najbolje prijedlog (CLI --potvrdi-opt)


class OptimizacijaGreska(Exception):
    pass


def kerf_pile(conn):
    return float(postavka(conn, "kerf_pile", "5") or 5)


def ogranicenja_pile(conn):
    """D-91: dict(max_razina, max_sirina, min_komad_4, mijesana) iz postavki (pila_*). max_razina 2|3|4; max_sirina 0 = bez ograničenja."""
    def broj(k):
        v = postavka(conn, k, str(OGRANICENJA_ZADANO[k]))
        try:
            return float(str(v).replace(",", "."))
        except (TypeError, ValueError):
            return float(OGRANICENJA_ZADANO[k])
    mr = int(broj("pila_max_razina") or 4)
    return dict(max_razina=min(4, max(2, mr)), max_sirina=int(broj("pila_max_sirina_u_traci") or 0), min_komad_4=broj("pila_min_komad_4") or 0,
                mijesana=1 if broj("pila_mijesana_orijentacija") else 0)


def _kandidati(dijelovi, ploca, trim, kerf, god, nacini, brzo, ogr, h):
    """OPT.najbolje s malim cacheom (isti elementi + iste postavke → isti kandidati, pa auto i hub ne računaju dvaput)."""
    kljuc = (h, kerf, nacini, brzo, tuple(sorted((ogr or {}).items())))
    r = _KAND_CACHE.get(kljuc)
    if r is None:
        r = OPT.najbolje(dijelovi, ploca, trim, kerf, god, nacini, brzo=brzo, ogr=ogr)
        if len(_KAND_CACHE) >= _KAND_CACHE_MAX:
            _KAND_CACHE.pop(next(iter(_KAND_CACHE)))
        _KAND_CACHE[kljuc] = r
    return r


def _ploca(m):
    return float(m["ploca_L"] or m["m_ploca_L"] or 2800), float(m["ploca_W"] or m["m_ploca_W"] or 2070)


def obrub(m, els, ploca):
    """Obrub (rubljenje) ploče za optimizaciju → (mm, auto_0). Upisan na materijalu naloga vrijedi kakav jest; inače zadano
    (10 mm, radne ploče / ploče stola / zidne obloge 0) — a kad element ne stane uz zadani obrub (puna mjera ploče), 0 (D-65/10)."""
    def cijeli(x):                                  # 10 a ne 10.0: isti hash elemenata kao prije (potvrđene optimizacije ne zastare)
        x = float(x)
        return int(x) if x.is_integer() else x
    if m.get("obrub") is not None:
        return cijeli(m["obrub"]), False
    t = cijeli(N.obrub_zadani(m.get("vrsta")))
    pL, pW = ploca
    if t and any(e["L"] > pL - 2 * t or e["W"] > pW - 2 * t for e in els):
        return 0, True
    return t, False


def ulaz_materijala(conn, nm_id):
    """Sve što optimizator treba za jedan materijal naloga: (m, els, dijelovi, ploca, trim, god, hash).
    els su u istom redoslijedu kao u export_pila / obracun (elementi_za_export), pa je idx = redni broj u toj listi."""
    m = N.materijal_naloga(conn, nm_id)
    els = [e for e in N.elementi_za_export(conn, m["nalog_id"]) if e["nalog_materijal_id"] == nm_id]
    dijelovi = [(k + 1, float(e["W"]), float(e["L"]), int(e["kom"])) for k, e in enumerate(els)]
    pL, pW = _ploca(m)
    trim = obrub(m, els, (pL, pW))[0]                       # obrub s materijala naloga ili zadani (radne ploče 0; puna mjera ploče → 0, D-65/10)
    god = bool(m["god"]) or any(int(e.get("god", 0)) for e in els)
    h = hashlib.sha1(json.dumps([(e["element_id"], e["L"], e["W"], e["kom"]) for e in els] + [pL, pW, trim, god]).encode()).hexdigest()[:16]
    return m, els, dijelovi, (pL, pW), trim, god, h


def obitelj_rp(conn, nm_id=None, m=None):
    """'radna' | 'stola' | 'zidna' za radnu ploču, ploču stola ili zidnu oblogu (D-37 / D-92), inače None."""
    m = m or N.materijal_naloga(conn, nm_id)
    if not m["materijal_id"]:
        return None
    v = conn.execute("SELECT vrsta, obitelj_rp FROM materijal WHERE id = ?", (m["materijal_id"],)).fetchone()
    return RPP.obitelj(v["vrsta"], v["obitelj_rp"]) if v else None


def izracunaj(conn, nm_id, nacin="auto", dubina="najbolje"):
    """Složi materijal bez upisa. Vraća dict(sheets, oc, nacin, ploca, trim, kerf, god, hash, komada, elemenata, st, napomena, dopusteno).
    D-91: auto / uzduzno / poprecno / trake = najbolje slaganje koje pila realno može izrezati (ograničenja iz postavki); ako takvog nema,
    uzima se najbolje bez ograničenja uz napomenu. hub = Hubov minimum bez ograničenja (rezerva)."""
    if nacin not in NACINI:
        raise OptimizacijaGreska("nepoznat način '%s' (auto | hub | uzduzno | poprecno | trake)" % nacin)
    if dubina not in DUBINE:
        raise OptimizacijaGreska("nepoznata dubina '%s' (brzo | najbolje)" % dubina)
    m, els, dijelovi, ploca, trim, god, h = ulaz_materijala(conn, nm_id)
    if not els:
        raise OptimizacijaGreska("materijal %s nema elemenata" % (m["naziv_kratki"] or m["naziv_ulaz"] or nm_id))
    kerf = kerf_pile(conn)
    ogr = ogranicenja_pile(conn)
    ob = obitelj_rp(conn, m=m)
    if ob in ("radna", "zidna"):                                        # D-92: komad iza komada, naplata po ploči — nema varijanti ni rezerve
        try:
            sheets = RPP.slozi_niz(dijelovi, ploca, trim, kerf)
        except ValueError as e:
            raise OptimizacijaGreska("%s: ne može se složiti (%s)%s" % (m["naziv_kratki"] or m["naziv_ulaz"], e,
                                     " — obrub ploče %g mm, smanji ga u materijalu" % trim if trim and m.get("obrub") is not None else ""))
        oc = RPP.ocijeni(sheets, ploca, trim, kerf, ob)
        return dict(nalog_materijal_id=nm_id, sheets=sheets, oc=oc, nacin="komad iza komada", nacin_trazen=nacin, dubina=dubina, ploca=ploca, trim=trim,
                    kerf=kerf, god=god, hash=h, elemenata=len(els), komada=sum(int(e["kom"]) for e in els), st=OPT.statistika(sheets, dijelovi, ploca),
                    element_ids=[e["element_id"] for e in els], napomena=None, dopusteno=True, ogranicenja=ogr, obitelj=ob)
    nacini = None if nacin in ("auto", "hub") else (nacin,)
    if ob == "stola" and nacini is None:
        nacini = ("uzduzno", "trake")                                   # ploča stola: trake uz duljinu, smiju i uži komadi jedan uz drugi (D-92)
    god_opt = True if ob == "stola" else god                            # ploča stola: L elementa uvijek uz duljinu ploče (profil ruba, Igor 17. 9.)
    try:
        sheets, oc, pobjednik, kand = _kandidati(dijelovi, ploca, trim, kerf, god_opt, nacini, dubina == "brzo", ogr, h)
    except ValueError as e:
        raise OptimizacijaGreska("%s: ne može se složiti (%s)%s" % (m["naziv_kratki"] or m["naziv_ulaz"], e,
                                     " — obrub ploče %g mm, smanji ga u materijalu" % trim if trim and m.get("obrub") is not None else ""))
    napomena = None
    dop = True
    if nacin == "hub":                                                  # rezerva: najbolji kandidat bez obzira na ograničenja
        b = min(kand, key=lambda k: (k[0], k[1], k[2]))
        sheets, oc = b[6], b[7]
        pobjednik = "%s/%s%s" % (b[3], b[4], "" if b[5] else "/poprijeko")
        dop, razlozi = OPT.dopusteno(sheets, dijelovi, ogr)
        if not dop:
            napomena = "Hub rezerva — pila ovako ne reže: " + "; ".join(razlozi)
    elif pobjednik.endswith("/izvan-ogranicenja"):
        pobjednik = pobjednik[:-len("/izvan-ogranicenja")]
        dop, razlozi = OPT.dopusteno(sheets, dijelovi, ogr)
        napomena = "nijedna optimizacija ne zadovoljava ograničenja pile (%s) — uzeto najbolje bez ograničenja" % "; ".join(razlozi)
    st = OPT.statistika(sheets, dijelovi, ploca)
    if ob == "stola":
        oc = RPP.ocijeni(sheets, ploca, trim, kerf, ob)                 # naplata pola / cijela po ploči umjesto m² PW-metodom
    return dict(nalog_materijal_id=nm_id, sheets=sheets, oc=oc, nacin=pobjednik, obitelj=ob, nacin_trazen=nacin, dubina=dubina, ploca=ploca, trim=trim,
                kerf=kerf, god=god, hash=h, elemenata=len(els), komada=sum(int(e["kom"]) for e in els), st=st,
                element_ids=[e["element_id"] for e in els], napomena=napomena, dopusteno=dop, ogranicenja=ogr)


def _snimka(r):
    return json.dumps(dict(sheets=r["sheets"], element_ids=r["element_ids"], ploca=list(r["ploca"]), trim=r["trim"], kerf=r["kerf"], god=r["god"],
                           ostaci=r["oc"].get("ostaci"), rp=r["oc"].get("rp")))


def predlozi(conn, nm_id, nacin="auto", dubina="najbolje", tko="web", commit=True):
    """Izračunaj i upiši PRIJEDLOG (status 'prijedlog'); stariji prijedlog istog načina i dubine postaje 'zamijenjeno'.
    Vraća red optimizacije (dict) s razlikom prema auto/najbolje prijedlogu ako postoji."""
    r = izracunaj(conn, nm_id, nacin, dubina)
    conn.execute("UPDATE optimizacija SET status = 'zamijenjeno' WHERE nalog_materijal_id = ? AND status = 'prijedlog' AND nacin_trazen = ? AND dubina = ?",
                 (nm_id, nacin, dubina))
    cur = conn.execute("INSERT INTO optimizacija (nalog_materijal_id, engine, nacin, datum, broj_ploca, iskoristenje, m2_dijelova, m2_ploca, m2_za_naplatu, "
                       "rezova, status, nacin_trazen, dubina, slaganje_json, elementi_hash, kerf, obrez, napomena) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (nm_id, "hub", r["nacin"], sada(), r["st"]["ploca"], r["st"]["iskoristenje"], r["st"]["m2_dijelova"], r["st"]["m2_bruto"],
                        r["oc"]["m2_naplata"], r["oc"]["rezova"], "prijedlog", nacin, dubina, _snimka(r), r["hash"], r["kerf"], r["trim"], r.get("napomena")))
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
    if r["slaganje_json"]:
        try:
            rp = json.loads(r["slaganje_json"]).get("rp")
        except ValueError:
            rp = None
        if rp:                                                          # radna ploča / ploča stola / zidna obloga: naplata po ploči u metrima (D-92)
            d["naplata_rp"] = dict(rp, opis_kratko=RPP.opis(rp))
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


def prijedlog_zivi(conn, nm_id, nacin, dubina="najbolje"):
    """Živi prijedlog (isti elementi) traženog načina i dubine — red (dict) ili None."""
    r = conn.execute("SELECT * FROM optimizacija WHERE nalog_materijal_id = ? AND status = 'prijedlog' AND nacin_trazen = ? AND dubina = ? "
                     "ORDER BY id DESC LIMIT 1", (nm_id, nacin, dubina)).fetchone()
    if not r:
        return None
    _, _, _, _, _, _, h = ulaz_materijala(conn, nm_id)
    return dict(r) if h == r["elementi_hash"] else None


def pripremi_prijedloge(conn, nalog_id, tko="web", nm_id=None, svjeze=False):
    """Za svaki materijal naloga (ili samo nm_id) bez potvrđenog slaganja i bez živog auto prijedloga napravi auto/najbolje prijedlog (ekran slaganja, D-75).
    D-91: uz njega i „hub“ rezervu (bez ograničenja pile) kad ona štedi materijal — da se razlika m² vidi odmah.
    svjeze=True: računa iznova i kad živi prijedlozi postoje (gumb Optimiziraj — npr. nakon promjene ograničenja pile u postavkama)."""
    novi = []
    for nm in conn.execute("SELECT nm.id FROM nalog_materijal nm WHERE nm.nalog_id = ? AND EXISTS (SELECT 1 FROM element e WHERE e.nalog_materijal_id = nm.id) "
                           "ORDER BY nm.rb, nm.id", (nalog_id,)).fetchall():
        if nm_id and nm["id"] != nm_id:
            continue
        if not treba_optimizaciju(conn, nm["id"]) or potvrdjena(conn, nm["id"]):
            continue
        auto = None if svjeze else prijedlog_auto(conn, nm["id"])
        if svjeze:                                                      # stara rezerva ne smije ostati uz novo zadano slaganje
            conn.execute("UPDATE optimizacija SET status = 'zamijenjeno' WHERE nalog_materijal_id = ? AND status = 'prijedlog' AND nacin_trazen = 'hub'", (nm["id"],))
        try:
            if not auto:
                a = predlozi(conn, nm["id"], "auto", "najbolje", tko, commit=False)
                novi.append(a)
                m2_auto = a["m2_za_naplatu"]
            else:
                m2_auto = auto[5]["m2_za_naplatu"]
            if svjeze or not prijedlog_zivi(conn, nm["id"], "hub"):
                r = izracunaj(conn, nm["id"], "hub", "najbolje")
                if m2_auto is not None and r["oc"]["m2_naplata"] < m2_auto - 0.005:
                    novi.append(predlozi(conn, nm["id"], "hub", "najbolje", tko, commit=False))
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
    """Materijal koji se slaže na ploču — svaki potvrđeni materijal. Od D-92 (Igor, 17. 9.) i radne ploče, ploče stola i zidne obloge:
    režu se uvijek na pili iz ploče 4100 × 600 / 900 / 640, a naplata se računa po ploči iz potvrđenog slaganja (radne_ploce.py)."""
    m = N.materijal_naloga(conn, nm_id)
    return bool(m["materijal_id"])


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
