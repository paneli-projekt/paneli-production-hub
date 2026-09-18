# -*- coding: utf-8 -*-
"""skladiste/pogled.py — Warehouse kao POGLED nad izvorima (D-64) + ono što izvori nemaju: rezervacija po nalogu i računica (D-42/4, D-42/5).

Izvori (jedan prilagodnik po izvoru, isto sučelje): pune ploče = Winstore (`ploce.py`), restlovi = Hub (`restlovi.py`), trake = Regal traka (`trake.py`).
Hub nigdje ne vodi paralelni fizički broj. Iznad izvora:
  * `potrebe_naloga(nalog_id)`   — što nalog treba po materijalu: ploče iz POTVRĐENOG slaganja (D-75; bez potvrde = nepoznato, upozorenje),
                                   restl ako je materijal vezan na restl, metri traka po TR identu (Σ konačna stranica × kom × nadmjera, naviše na metar — D-20/D-77)
  * `stanje_materijala(mid)`     — fizičko (Winstore) + restlovi + rezervirano (drugi nalozi) + naručeno (otvorene narudžbenice) → raspoloživo
  * `provjera_naloga(nalog_id)`  — status „Skladište" (D-35): po materijalu potrebno / raspoloživo / manjak, restlovi koji mogu poslužiti,
                                   trake: metri na roli i pretinac iz Regal trake; UPOZORENJA i POPIS ZA NABAVU
  * `rezerviraj_nalog(nalog_id)` — rezervacija punih ploča (i restla ako je zadan) po materijalu; `oslobodi_nalog`, `izdaj_nalog`
  * `potrebe_ukupno()`           — potreba preko SVIH potvrđenih naloga za Nabavu (D-42/5): Σ potrebno − fizičko − rezervirano + naručeno
Trake Hub ne rezervira ni ne oduzima (D-63): samo uspoređuje potrebu s metrima na roli.
"""
import math

from ..db import postavka, dnevnik, sada
from . import ploce as PL, restlovi as RS, trake as TR

STATUSI_POTREBE = ("potvrdjeno", "skladiste", "pila_nesting")     # nalozi koji troše skladište, a još nisu rezani


# ---------------------------------------------------------------- potrebe jednog naloga
def trake_materijala(conn, nm_id):
    """{traka_id: {ident, naziv, klasa, metri_tocno, metri}} po KONAČNOJ mjeri elemenata (kao obračun, D-20; nadmjera iz postavki, D-77)."""
    from ..nalozi import nalozi as N
    faktor = 1 + float(postavka(conn, "nadmjera_trake", "10") or 0) / 100
    out = {}
    for el in N.elementi_konacni(conn, nm_id):
        for i, strana in enumerate(("L", "O", "D", "G"), 1):
            tid = el["rub%d_traka_id" % i]
            if not tid:
                continue
            t = out.setdefault(tid, dict(traka_id=tid, ident=el["rub%d_traka" % i], naziv=el["rub%d_naziv" % i], klasa=el["rub%d_klasa" % i], metri_tocno=0.0))
            ln = float(el["L"]) if strana in ("L", "D") else float(el["W"])
            t["metri_tocno"] += ln * int(el["kom"]) / 1000.0 * faktor
    for t in out.values():
        t["metri_tocno"] = round(t["metri_tocno"], 2)
        t["metri"] = int(math.ceil(t["metri_tocno"] - 1e-9))
    return out


def potrebe_naloga(conn, nalog_id):
    """[{nalog_materijal_id, materijal_id, ident, naziv, winstore_kod, put, na_restlu, ploce, optimizacija_id, potvrdjena, trake:{…}, upozorenje}]"""
    from ..nalozi import nalozi as N, optimiziraj as OP
    out = []
    for nm in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? ORDER BY rb, id", (nalog_id,)).fetchall():
        m = N.materijal_naloga(conn, nm["id"])
        d = dict(nalog_materijal_id=nm["id"], materijal_id=m["materijal_id"], ident=m["ident"], naziv=m["naziv_kratki"] or m["naziv"] or m["naziv_ulaz"],
                 vrsta=m["vrsta"], winstore_kod=m["winstore_kod"], put=m["put"] or m["put_prijedlog"], na_restlu=bool(m["ploca_L"] or m["ploca_W"]),
                 restl_mjera=(m["ploca_L"], m["ploca_W"]) if (m["ploca_L"] or m["ploca_W"]) else None,
                 ploce=None, optimizacija_id=None, potvrdjena=False, trake={}, upozorenje=None)
        if not m["materijal_id"]:
            d["upozorenje"] = "materijal nije potvrđen"
            out.append(d); continue
        els = [e for e in N.elementi_za_export(conn, nalog_id) if e["nalog_materijal_id"] == nm["id"]]
        if not els:
            d["upozorenje"] = "materijal bez elemenata"
            out.append(d); continue
        d["trake"] = trake_materijala(conn, nm["id"])
        d["najveci"] = (max(max(e["L"], e["W"]) for e in els), max(min(e["L"], e["W"]) for e in els))
        if m["vrsta"] in ("RP", "ZO"):
            d["metara"] = round(sum(max(e["L"], e["W"]) * e["kom"] for e in els) / 1000, 2)
            d["upozorenje"] = "radna / zidna ploča po dužnom metru — Winstore je ne vodi"
            out.append(d); continue
        r = OP.potvrdjena(conn, nm["id"])
        if r:
            d.update(ploce=int(r["broj_ploca"] or 0), optimizacija_id=r["id"], potvrdjena=True)
        else:
            d["upozorenje"] = "optimizacija nije potvrđena (D-75) — broj ploča nepoznat"
        out.append(d)
    return out


# ---------------------------------------------------------------- stanje jednog materijala preko svih izvora
def naruceno(conn, ident):
    """Otvoreno naručeno (poslane / djelomično zaprimljene narudžbenice) za ident: Σ (kom − zaprimljeno)."""
    r = conn.execute("SELECT COALESCE(SUM(s.kom - s.zaprimljeno_kom), 0) FROM narudzbenica_st s JOIN narudzbenica n ON n.id = s.narudzbenica_id "
                     "WHERE s.pantheon_ident = ? AND n.status IN ('poslana', 'djelomicno')", (ident,)).fetchone()
    return float(r[0] or 0)


def stanje_materijala(conn, materijal_id, bez_nm=None):
    """{ident, naziv, ploce: {fizicko, rezervirano, naruceno, raspolozivo, lokacija, drop}, restlovi: {kom, m2, popis}}"""
    m = conn.execute("SELECT id, pantheon_ident, naziv_pantheon, naziv_kratki, winstore_kod, debljina FROM materijal WHERE id = ?", (materijal_id,)).fetchone()
    if not m:
        return None
    fiz = PL.kom(conn, materijal_id)
    rez = PL.rezervirano(conn, materijal_id, bez_nm=bez_nm)
    nar = naruceno(conn, m["pantheon_ident"])
    w = PL.stanje(conn, materijal_id=materijal_id, samo_sa_stanjem=False)
    rs = RS.stanje(conn, materijal_id=materijal_id, samo_slobodni=True)
    return dict(materijal_id=m["id"], ident=m["pantheon_ident"], naziv=m["naziv_kratki"] or m["naziv_pantheon"], debljina=m["debljina"],
                ploce=dict(fizicko=fiz, rezervirano=rez, naruceno=nar, raspolozivo=fiz - rez + nar, lokacija=PL.lokacija(conn, materijal_id),
                           drop=w[0]["drop_kom"] if w else 0, izvoz=w[0]["izvoz"] if w else None),
                restlovi=dict(kom=rs[0]["kom"] if rs else 0, m2=rs[0]["m2"] if rs else 0.0, popis=rs[0]["restlovi"] if rs else []))


# ---------------------------------------------------------------- provjera naloga u statusu Skladište (D-35)
def provjera_naloga(conn, nalog_id):
    """Po materijalu: potrebno, fizičko, rezervirano (drugi nalozi), naručeno, raspoloživo, manjak, restlovi koji mogu poslužiti,
    trake s metrima na roli; + upozorenja i popis za nabavu."""
    from ..nalozi import nalozi as N
    n = N.nalog(conn, nalog_id)
    mats, upoz, nabava = [], [], []
    for p in potrebe_naloga(conn, nalog_id):
        d = dict(p)
        if p["upozorenje"]:
            upoz.append("%s: %s" % (p["naziv"], p["upozorenje"]))
        if p["materijal_id"]:
            st = stanje_materijala(conn, p["materijal_id"], bez_nm=p["nalog_materijal_id"])
            d["stanje"] = st
            d["rezervirano_ovaj"] = sum(r["kom"] for r in conn.execute(
                "SELECT kom FROM rezervacija WHERE nalog_materijal_id = ? AND restl_id IS NULL AND status IN ('rezervirano', 'izdano')", (p["nalog_materijal_id"],)))
            d["restl_rezerviran"] = RS.rezervirani(conn, p["nalog_materijal_id"])
            if p["na_restlu"]:
                L, W = p["restl_mjera"]
                d["restl_kandidati"] = RS.kandidati(conn, p["materijal_id"], L or 0, W or 0)
                d["manjak"] = 0 if (d["restl_rezerviran"] or d["restl_kandidati"]) else 1
                if d["manjak"]:
                    upoz.append("%s: nalog je na restlu %g × %g, a takvog restla nema na stanju" % (p["naziv"], L or 0, W or 0))
            else:
                naj = p.get("najveci")
                d["restl_kandidati"] = RS.kandidati(conn, p["materijal_id"], naj[0], naj[1]) if naj else []
                if p["ploce"] is not None:
                    d["manjak"] = max(0, p["ploce"] - st["ploce"]["raspolozivo"])
                    if d["manjak"]:
                        upoz.append("%s: treba %d ploča, raspoloživo %g (fizičko %d − rezervirano %g + naručeno %g)" % (
                            p["naziv"], p["ploce"], st["ploce"]["raspolozivo"], st["ploce"]["fizicko"], st["ploce"]["rezervirano"], st["ploce"]["naruceno"]))
                        nabava.append(dict(ident=p["ident"], naziv=p["naziv"], kom=d["manjak"], jm="PLOČA", winstore_kod=p["winstore_kod"], nalog_materijal_id=p["nalog_materijal_id"]))
                else:
                    d["manjak"] = None
        # trake: potreba vs Regal traka (Hub ne oduzima, D-63)
        for t in d["trake"].values():
            s = TR.stanje(conn, t["ident"])
            t.update(pretinac=s["pretinac"], na_roli=s["metri"], regal_traka=s["dostupno"])
            if s["metri"] is not None and s["metri"] < t["metri"]:
                t["manjak"] = round(t["metri"] - s["metri"], 1)
                upoz.append("traka %s %s: treba %d m, na roli %g m" % (t["ident"], t["naziv"] or "", t["metri"], s["metri"]))
                nabava.append(dict(ident=t["ident"], naziv=t["naziv"], kom=t["manjak"], jm="M", nalog_materijal_id=p["nalog_materijal_id"]))
        mats.append(d)
    return dict(nalog_id=nalog_id, naziv=n["naziv"], status=n["status"], materijali=mats, upozorenja=upoz, za_nabavu=nabava,
                ok=not any(x.get("manjak") for x in mats) and not any(t.get("manjak") for x in mats for t in x["trake"].values()))


def rezerviraj_nalog(conn, nalog_id, tko, restlovi=None, tko_potvrda=None):
    """Rezervacija po materijalu (D-42/4): pune ploče iz potvrđenog slaganja (Winstore kod), restl za materijal na restlu ako je zadan
    ({nm_id: restl_id}); uz to Hub PREDLOŽI restlove iz potvrđenih shema (D-64/3). Vraća provjeru naloga."""
    restlovi = restlovi or {}
    from ..nalozi import nalozi as N
    for p in potrebe_naloga(conn, nalog_id):
        nm = p["nalog_materijal_id"]
        if restlovi.get(nm) or restlovi.get(str(nm)):
            RS.oslobodi(conn, nm, tko, commit=False)
            RS.rezerviraj(conn, nm, restlovi.get(nm) or restlovi.get(str(nm)), tko, commit=False)
        if p["ploce"] and not p["na_restlu"]:
            PL.rezerviraj(conn, nm, p["ploce"], tko, winstore_kod=p["winstore_kod"], commit=False)
            RS.predlozi_iz_sheme(conn, nm, tko, commit=False)
    conn.commit()
    pr = provjera_naloga(conn, nalog_id)
    dnevnik(conn, tko, "nalog", nalog_id, "skladiste", "rezervirano; %d upozorenja, za nabavu %d" % (len(pr["upozorenja"]), len(pr["za_nabavu"])))
    conn.commit()
    return pr


def oslobodi_nalog(conn, nalog_id, tko):
    n = 0
    for nm in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ?", (nalog_id,)).fetchall():
        n += PL.oslobodi(conn, nm["id"], tko, commit=False) + RS.oslobodi(conn, nm["id"], tko, commit=False)
    conn.commit()
    return n


def u_winstoreu(conn, materijal_id, vrsta=None):
    """Drži li materijal automatsko skladište Winstore (D-95). Winstore ga poslužuje sam, pa Hub za njega ne vodi izdavanje.
    Radne ploče, ploče stola i zidne obloge nikad nisu u Winstoreu; za ostalo odlučuje zadnji izvoz (materijal se u njemu pojavljuje,
    makar s količinom 0)."""
    if (vrsta or "") in ("RP", "ZO"):
        return False
    if not materijal_id:
        return False
    r = conn.execute("SELECT COUNT(*) FROM winstore_ploca WHERE materijal_id = ? AND ambalaza = 0", (materijal_id,)).fetchone()
    return bool(r[0])


def izdaj_nalog(conn, nalog_id, tko):
    """Nalog otišao na stroj. Ploče koje drži Winstore izdaje sam automat, pa im rezervacija odmah ide u 'izdano' (stanje se ionako
    ispravlja idućim Winstore izvozom). Restlovi i materijali kojih Winstore nema ČEKAJU skladištara (D-95) — on ih izdaje na svom
    ekranu (`izdaj_materijal`). Vraća broj automatski izdanih rezervacija."""
    k = 0
    for nm in conn.execute("SELECT nm.id, nm.materijal_id, m.vrsta FROM nalog_materijal nm LEFT JOIN materijal m ON m.id = nm.materijal_id "
                           "WHERE nm.nalog_id = ?", (nalog_id,)).fetchall():
        if not u_winstoreu(conn, nm["materijal_id"], nm["vrsta"]):
            continue
        cur = conn.execute("UPDATE rezervacija SET status = 'izdano', izdano_kada = ? WHERE nalog_materijal_id = ? AND restl_id IS NULL AND status = 'rezervirano'",
                           (sada(), nm["id"]))
        k += cur.rowcount
    conn.commit()
    return k


def izdaj_materijal(conn, nm_id, tko, commit=True):
    """Skladištar je iznio materijal iz regala (D-95): rezervacije ploča → izdano, rezervirani restl → potrošen (s nazivom naloga).
    Vraća broj zatvorenih rezervacija."""
    from ..nalozi import nalozi as N
    r = conn.execute("SELECT nm.nalog_id, n.naziv FROM nalog_materijal nm JOIN nalog n ON n.id = nm.nalog_id WHERE nm.id = ?", (nm_id,)).fetchone()
    k = conn.execute("UPDATE rezervacija SET status = 'izdano', izdano_kada = ? WHERE nalog_materijal_id = ? AND restl_id IS NULL AND status = 'rezervirano'",
                     (sada(), nm_id)).rowcount
    k += RS.izdaj(conn, nm_id, tko, r["naziv"] if r else None, commit=False)
    if k:
        dnevnik(conn, tko, "nalog_materijal", nm_id, "izdano", "skladištar izdao materijal")
    if commit:
        conn.commit()
    return k


def ceka_izdavanje(conn, nalog_id=None, statusi=("skladiste", "pila_nesting", "proizvodnja")):
    """Što skladištar treba iznijeti iz regala (D-95): rezervirani restlovi i materijali kojih Winstore ne drži, po nalozima u radu.
    [{nalog_id, nalog, status, nalog_materijal_id, ident, naziv, vrsta, kom, restlovi:[{oznaka, L, W, lokacija}], dana}]"""
    st = ", ".join("'%s'" % x for x in statusi)
    sql = ("SELECT r.id AS rid, r.nalog_materijal_id AS nm, r.restl_id, r.kom, r.datum, nm.materijal_id, n.id AS nalog_id, n.naziv AS nalog, n.status, "
           "m.pantheon_ident AS ident, m.naziv_pantheon AS naziv, m.naziv_kratki, m.vrsta, x.oznaka, x.L AS rL, x.W AS rW, x.lokacija "
           "FROM rezervacija r JOIN nalog_materijal nm ON nm.id = r.nalog_materijal_id JOIN nalog n ON n.id = nm.nalog_id "
           "LEFT JOIN materijal m ON m.id = nm.materijal_id LEFT JOIN restl x ON x.id = r.restl_id "
           "WHERE r.status = 'rezervirano' AND n.status IN (%s)" % st)
    a = []
    if nalog_id:
        sql += " AND n.id = ?"; a.append(nalog_id)
    out = {}
    for r in conn.execute(sql + " ORDER BY n.id, m.pantheon_ident", a):
        if not r["restl_id"] and u_winstoreu(conn, r["materijal_id"], r["vrsta"]):
            continue                                                       # ploče iz Winstorea poslužuje automat
        o = out.setdefault(r["nm"], dict(nalog_id=r["nalog_id"], nalog=r["nalog"], status=r["status"], nalog_materijal_id=r["nm"],
                                         ident=r["ident"], naziv=r["naziv_kratki"] or r["naziv"], vrsta=r["vrsta"], kom=0, restlovi=[],
                                         datum=r["datum"], u_winstoreu=False))
        if r["restl_id"]:
            o["restlovi"].append(dict(oznaka=r["oznaka"], L=r["rL"], W=r["rW"], lokacija=r["lokacija"]))
        else:
            o["kom"] += r["kom"]
        if r["datum"] and (not o["datum"] or r["datum"] < o["datum"]):
            o["datum"] = r["datum"]
    return sorted(out.values(), key=lambda x: (x["nalog_id"], x["ident"] or ""))


def zatvori_nalog(conn, nalog_id, tko):
    """Zatvoren nalog: izdano → potrošeno, ostale aktivne rezervacije → oslobođeno (i restlovi natrag)."""
    oslobodi_nalog(conn, nalog_id, tko)
    conn.execute("UPDATE rezervacija SET status = 'potroseno' WHERE status = 'izdano' AND nalog_materijal_id IN (SELECT id FROM nalog_materijal WHERE nalog_id = ?)", (nalog_id,))
    conn.commit()


# ---------------------------------------------------------------- potreba preko svih potvrđenih naloga (D-42/5, ekran Nabava)
def potrebe_ukupno(conn, statusi=STATUSI_POTREBE):
    """Po materijalu: Σ ploča preko naloga (potvrđena slaganja), fizičko, rezervirano, naručeno, manjak; po traci: Σ metara vs rola.
    Nalozi bez potvrđenog slaganja se navode kao nepoznata potreba."""
    from ..nalozi import optimiziraj as OP
    mats, trake, nepoznato = {}, {}, []
    st = ", ".join("'%s'" % s for s in statusi)
    for n in conn.execute("SELECT id, naziv, status, rok_obecan FROM nalog WHERE status IN (%s) ORDER BY rok_obecan, id" % st).fetchall():
        for p in potrebe_naloga(conn, n["id"]):
            if not p["materijal_id"]:
                continue
            if p["ploce"] is None and not p["na_restlu"] and p["vrsta"] not in ("RP", "ZO"):
                nepoznato.append(dict(nalog=n["naziv"], materijal=p["naziv"], razlog=p["upozorenje"]))
            m = mats.setdefault(p["materijal_id"], dict(materijal_id=p["materijal_id"], ident=p["ident"], naziv=p["naziv"], winstore_kod=p["winstore_kod"],
                                                        potrebno=0, nalozi=[], na_restlu=0))
            if p["na_restlu"]:
                m["na_restlu"] += 1
            elif p["ploce"]:
                m["potrebno"] += p["ploce"]
            m["nalozi"].append(dict(nalog=n["naziv"], status=n["status"], rok=n["rok_obecan"], ploce=p["ploce"], na_restlu=p["na_restlu"]))
            for tid, t in p["trake"].items():
                x = trake.setdefault(tid, dict(traka_id=tid, ident=t["ident"], naziv=t["naziv"], klasa=t["klasa"], potrebno=0, nalozi=[]))
                x["potrebno"] += t["metri"]
                x["nalozi"].append(dict(nalog=n["naziv"], metri=t["metri"]))
    for m in mats.values():
        s = stanje_materijala(conn, m["materijal_id"])
        m.update(fizicko=s["ploce"]["fizicko"], rezervirano=s["ploce"]["rezervirano"], naruceno=s["ploce"]["naruceno"],
                 restlovi_kom=s["restlovi"]["kom"], restlovi_m2=s["restlovi"]["m2"])
        # Σ potrebno − fizičko − naručeno: rezervacije su rezervacije upravo ovih naloga, pa su već unutar Σ potrebno (ne oduzimaju se dvaput)
        m["manjak"] = max(0, m["potrebno"] - s["ploce"]["fizicko"] - s["ploce"]["naruceno"])
    for t in trake.values():
        s = TR.stanje(conn, t["ident"])
        t.update(na_roli=s["metri"], pretinac=s["pretinac"], manjak=round(max(0.0, t["potrebno"] - s["metri"]), 1) if s["metri"] is not None else None)
    return dict(materijali=sorted(mats.values(), key=lambda x: (-x["manjak"], x["ident"])),
                trake=sorted(trake.values(), key=lambda x: (-(x["manjak"] or 0), x["ident"])), nepoznato=nepoznato,
                za_nabavu=[dict(ident=m["ident"], naziv=m["naziv"], kom=m["manjak"], jm="PLOČA") for m in mats.values() if m["manjak"]] +
                          [dict(ident=t["ident"], naziv=t["naziv"], kom=t["manjak"], jm="M") for t in trake.values() if t["manjak"]])
