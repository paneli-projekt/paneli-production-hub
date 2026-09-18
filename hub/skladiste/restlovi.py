# -*- coding: utf-8 -*-
"""skladiste/restlovi.py — prilagodnik za restlove (D-64): vlasnik broja je modul RESTLOVI u Hubu (tablica `restl`, vode je skladištari).

Početno stanje dolazi iz dosadašnje evidencije skladišta `20_ANALIZA\\RESTLOVI_V7.xlsm` (Igor, 16. 9.): list RESTLOVI
(ID, Grupa, Ident, Naziv artikla, Duljina, Širina, Kom, Lokacija, Status, M2, Nalog (izlaz), Datum, Napomena, STARI OPIS …) —
jedan redak = jedan restl, dekor je u stupcu STARI OPIS (naziv kao u PanelWizardu), debljine u tablici NEMA (zna se tek preko identa).
List MAPIRANJE DEKORA nosi ručno provjereno mapiranje dekor → ident (TOČNO / PROVJERI / NEMA U CJENIKU) i služi kao usporedba.

Vezanje dekora na ident ide KROZ ŠIFRARNIK (prepoznaj_materijal: alias → Winstore kod → naziv); što nije sigurno ide na potvrdu s
kandidatima (D-46/4) i nikad se ne popunjava najboljim kandidatom. Excelov ident se koristi samo kad je ondje označen TOČNO, a šifrarnik
nema siguran pogodak (razina 'excel'); kad se šifrarnik i Excel ne slažu, restl ide na potvrdu s oba kandidata. Potvrda skladištara /
ureda postaje alias (D-32) i primjenjuje se na sve restlove istog dekora.

Uvoz je idempotentan: ključ je oznaka restla (R0001…); ponovni uvoz osvježava mjere, lokaciju, status i napomenu iz Excela, ali ne dira
restlove koje je skladištar u Hubu već potvrdio (potvrdio IS NOT NULL) ni one koji nisu iz Excela. Statusi: NA SKLADIŠTU → slobodan,
REZERVIRAN → rezerviran, PROVJERI → provjeri (fizički provjeriti — izgrebano, više mjera), PRODAN → potrosen, OTPISAN → otpisan.
Restl koji Hub PREDLOŽI iz potvrđene sheme (D-64/3) ima status 'prijedlog' i na stanje ulazi tek kad ga skladištar potvrdi i zalijepi QR.

    py -m hub.skladiste.restlovi --db hub.db --uvoz ..\\20_ANALIZA\\RESTLOVI_V7.xlsm [--md izvjestaj.md]
    py -m hub.skladiste.restlovi --db hub.db --stanje [--ident IV000090]
    py -m hub.skladiste.restlovi --db hub.db --potvrdi "IV JAVOR (KRONO)" IV000013 --tko IVANA
    py -m hub.skladiste.restlovi --db hub.db --prijedlozi [--nalog N]      restlovi predloženi iz potvrđenih shema (D-64/3), čekaju skladištara
    py -m hub.skladiste.restlovi --db hub.db --potvrdi-restl R1364 --lokacija B004 --tko SKLADISTAR

Rezervacija (D-42/4): `rezerviraj(nm_id, restl_id)` veže restl na materijal naloga (status restla → rezerviran), `oslobodi` ga vraća,
`izdaj` ga troši (nalog otišao na stroj: status potrošen + nalog izlaz). Restl kao PRIJEDLOG (D-64/3): `predlozi_iz_sheme(nm_id)` iz
potvrđenog slaganja otvori restlove sa statusom `prijedlog` i oznakom R…; skladištar ih `potvrdi_restl` (zalijepi QR, upiše lokaciju) →
`slobodan`, ili `odbaci_restl` → `otpisan`.

PRAG ČUVANJA (D-95, Igor 18. 9., mjereno na 1 363 restla iz evidencije): restl je ostatak **≥ 0,35 m²**, ili traka **duža od 2 000 mm**,
uz kraću stranicu najmanje 150 mm — postavke `restl_min_m2`, `restl_traka_mm`, `restl_min_mm`. Pravilo NAPLATE se ne mijenja (≥ 400 mm i
≥ 1 m², D-19): komad između ta dva praga kupac plaća, a mi ga ipak zadržimo u regalu. Restl koji kupac ostavi nama upisuje se ručno
(`novi_restl(..., izvor='kupac')`).
"""
import argparse
import hashlib
import json
import os
import sys

from ..db import sada, dnevnik, postavi, postavka
from ..optimizacija import obracun as OBR
from ..sifrarnici import prepoznaj as P

STATUSI_EXCEL = {"NA SKLADIŠTU": "slobodan", "NA SKLADISTU": "slobodan", "REZERVIRAN": "rezerviran", "PROVJERI": "provjeri",
                 "PRODAN": "potrosen", "OTPISAN": "otpisan"}
NA_STANJU = ("slobodan", "rezerviran", "provjeri")          # fizički u regalu; 'provjeri' = treba pogledati (izgrebano…), ali postoji
STATUSI = NA_STANJU + ("prijedlog", "potrosen", "otpisan")
IZVOR_EXCEL = "excel_v7"


# ---------------------------------------------------------------- čitanje Excela
def _s(x):
    return str(x).strip() if x is not None else ""


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def ucitaj_xlsm(putanja):
    """Pročitaj RESTLOVI_V7.xlsm → dict(restlovi=[…], mapiranje={dekor: (ident, status)}, datoteka, hash, upozorenja)."""
    import openpyxl
    wb = openpyxl.load_workbook(putanja, data_only=True, read_only=True)
    if "RESTLOVI" not in wb.sheetnames:
        raise ValueError("u %s nema lista RESTLOVI" % putanja)
    ws = wb["RESTLOVI"]
    redovi = ws.iter_rows(min_row=1, values_only=True)
    zaglavlje = [_s(c).upper() for c in next(redovi)]
    ix = {k: (zaglavlje.index(v) if v in zaglavlje else None) for k, v in dict(
        oznaka="ID", grupa="GRUPA", ident="IDENT", L="DULJINA", W="ŠIRINA", kom="KOM", lokacija="LOKACIJA", status="STATUS",
        m2="M2", nalog="NALOG (IZLAZ)", datum="DATUM", napomena="NAPOMENA", dekor="STARI OPIS").items()}
    if ix["oznaka"] is None or ix["dekor"] is None or ix["L"] is None or ix["W"] is None:
        raise ValueError("list RESTLOVI nema očekivane stupce (ID, STARI OPIS, Duljina, Širina); zaglavlje: %s" % zaglavlje)

    def g(r, k):
        i = ix[k]
        return r[i] if i is not None and i < len(r) else None

    out, upoz = [], []
    for r in redovi:
        oz = _s(g(r, "oznaka"))
        if not oz:
            continue
        L, W = _f(g(r, "L")), _f(g(r, "W"))
        if not L or not W:
            upoz.append("%s: nema mjere (%s × %s) — preskočeno" % (oz, g(r, "L"), g(r, "W")))
            continue
        st_excel = _s(g(r, "status")).upper()
        d = _s(g(r, "datum"))
        out.append(dict(oznaka=oz, grupa=_s(g(r, "grupa")) or None, ident_ulaz=_s(g(r, "ident")).upper() or None,
                        dekor=_s(g(r, "dekor")), L=L, W=W, kom=int(_f(g(r, "kom")) or 1), lokacija=_s(g(r, "lokacija")) or None,
                        status_excel=st_excel, status=STATUSI_EXCEL.get(st_excel, "provjeri"), m2_excel=_f(g(r, "m2")),
                        nalog_izlaz=_s(g(r, "nalog")) or None, datum=d[:10] if d else None, napomena=_s(g(r, "napomena")) or None))
        if st_excel and st_excel not in STATUSI_EXCEL:
            upoz.append("%s: nepoznat status '%s' → provjeri" % (oz, st_excel))
    mapiranje = {}
    if "MAPIRANJE DEKORA" in wb.sheetnames:
        for r in wb["MAPIRANJE DEKORA"].iter_rows(min_row=2, values_only=True):
            if r and _s(r[0]):
                mapiranje[_s(r[0])] = (_s(r[2]).upper() or None, _s(r[5]) if len(r) > 5 else "")
    wb.close()
    return dict(restlovi=out, mapiranje=mapiranje, datoteka=os.path.basename(putanja),
                hash=hashlib.sha1(open(putanja, "rb").read()).hexdigest(), upozorenja=upoz)


# ---------------------------------------------------------------- vezanje dekora na ident
def _materijal_po_identu(conn, ident):
    if not ident:
        return None
    return conn.execute("SELECT id, pantheon_ident, naziv_pantheon FROM materijal WHERE pantheon_ident = ? AND ne_koristi_se = 0", (ident,)).fetchone()


def prepoznaj_dekor(conn, dekor, excel_ident=None, excel_status=None):
    """Dekor iz evidencije → materijal kroz šifrarnik; Excelov ident samo kao potvrđena rezerva ili kao drugi kandidat.
    Vraća dict(materijal_id, ident, naziv, razina, provjeri, kandidati, objasnjenje)."""
    rz = P.prepoznaj_materijal(conn, dekor)
    ex = _materijal_po_identu(conn, excel_ident) if excel_ident else None
    ex_tocno = bool(ex) and str(excel_status or "").upper().startswith("TOČNO")
    kand = [(i, n, s) for i, n, s in rz.kandidati]

    def za_potvrdu(razlog, prvi=None):
        k = list(kand)
        if prvi:
            k = [prvi] + [x for x in k if x[0] != prvi[0]]
        if ex and all(x[0] != ex["pantheon_ident"] for x in k):
            k.append((ex["pantheon_ident"], ex["naziv_pantheon"], 0.0))
        return dict(materijal_id=None, ident=None, naziv=None, razina="za_potvrdu" if k else "nema", provjeri=1, kandidati=k[:6],
                    objasnjenje=razlog)

    if rz.siguran:
        if ex and ex["pantheon_ident"] != rz.ident:
            if ex_tocno:
                return za_potvrdu("šifrarnik %s (%s) ≠ Excel TOČNO %s" % (rz.ident, rz.razina, ex["pantheon_ident"]), (rz.ident, rz.naziv, rz.score))
            if rz.razina == "naziv":                      # dekor bez debljine, Hub pogodio po nazivu, Excel nagađa drugo → čovjek
                return za_potvrdu("šifrarnik po nazivu %s, Excel PROVJERI %s" % (rz.ident, ex["pantheon_ident"]), (rz.ident, rz.naziv, rz.score))
        return dict(materijal_id=rz.id, ident=rz.ident, naziv=rz.naziv, razina=rz.razina, provjeri=0, kandidati=[], objasnjenje=rz.objasnjenje)
    if ex_tocno:
        return dict(materijal_id=ex["id"], ident=ex["pantheon_ident"], naziv=ex["naziv_pantheon"], razina="excel", provjeri=0, kandidati=[],
                    objasnjenje="Excel MAPIRANJE DEKORA: TOČNO (šifrarnik: %s)" % rz.razina)
    return za_potvrdu("šifrarnik: %s — %s" % (rz.razina, rz.objasnjenje))


# ---------------------------------------------------------------- uvoz
def uvezi_excel(conn, putanja, tko="uvoz"):
    """Uvezi evidenciju restlova; vraća izvještaj (brojke po dekorima i restlovima, popis za potvrdu, upozorenja)."""
    x = ucitaj_xlsm(putanja)
    P.ocisti_kes()
    dekori = {}
    for r in x["restlovi"]:
        d = r["dekor"]
        if d not in dekori:
            ex_ident, ex_status = x["mapiranje"].get(d, (None, None))
            if ex_ident is None and r["ident_ulaz"]:
                ex_ident, ex_status = r["ident_ulaz"], ""
            dekori[d] = prepoznaj_dekor(conn, d, ex_ident, ex_status)
            dekori[d]["excel_ident"] = ex_ident
            dekori[d]["excel_status"] = ex_status
    novo = osvjezeno = zadrzano = 0
    m2_razlika = []
    cur = conn.cursor()
    sada_ = sada()
    for r in x["restlovi"]:
        p = dekori[r["dekor"]]
        m2 = r["L"] * r["W"] * r["kom"] / 1e6
        if r["m2_excel"] is not None and abs(m2 - r["m2_excel"]) > 0.02:
            m2_razlika.append((r["oznaka"], round(m2, 3), r["m2_excel"]))
        st = conn.execute("SELECT id, izvor, potvrdio FROM restl WHERE oznaka = ?", (r["oznaka"],)).fetchone()
        if st and (st["potvrdio"] or st["izvor"] != IZVOR_EXCEL):
            zadrzano += 1
            continue
        vals = dict(materijal_id=p["materijal_id"], dekor_ulaz=r["dekor"], ident_ulaz=p["excel_ident"], grupa=r["grupa"], L=r["L"], W=r["W"],
                    kom=r["kom"], lokacija=r["lokacija"], status=r["status"], provjeri=p["provjeri"], razina=p["razina"],
                    kandidati_json=json.dumps(p["kandidati"], ensure_ascii=False) if p["kandidati"] else None,
                    nalog_izlaz=r["nalog_izlaz"], napomena=r["napomena"], datum=r["datum"])
        if st:
            cur.execute("UPDATE restl SET %s WHERE id = ?" % ", ".join("%s = ?" % k for k in vals), (*vals.values(), st["id"]))
            osvjezeno += 1
        else:
            cur.execute("INSERT INTO restl (oznaka, qr, izvor, kada, %s) VALUES (?, ?, ?, ?, %s)" % (", ".join(vals), ", ".join("?" * len(vals))),
                        (r["oznaka"], r["oznaka"], IZVOR_EXCEL, sada_, *vals.values()))
            novo += 1
    postavi(conn, "restlovi_uvoz", "%s %s %s" % (x["datoteka"], x["hash"][:12], sada_), "zadnji uvoz evidencije restlova")
    dnevnik(conn, tko, "restl", None, "uvoz", "%s: %d novo, %d osvježeno, %d zadržano (potvrđeno u Hubu)" % (x["datoteka"], novo, osvjezeno, zadrzano))
    conn.commit()
    return _izvjestaj(x, dekori, novo, osvjezeno, zadrzano, m2_razlika)


def _izvjestaj(x, dekori, novo, osvjezeno, zadrzano, m2_razlika):
    po_dekoru = {"sigurno": 0, "za_potvrdu": 0, "nema": 0}
    po_restlu = {"sigurno": 0, "za_potvrdu": 0, "nema": 0}
    razine, excel_slaganje = {}, {"isti": 0, "razlicit": 0, "excel_nema": 0, "hub_nema": 0}
    n_dek = {}
    for r in x["restlovi"]:
        n_dek[r["dekor"]] = n_dek.get(r["dekor"], 0) + 1
    za_potvrdu = []
    for d, p in dekori.items():
        kl = "sigurno" if not p["provjeri"] else p["razina"]
        po_dekoru[kl] += 1
        po_restlu[kl] += n_dek[d]
        razine[p["razina"]] = razine.get(p["razina"], 0) + 1
        if p["ident"] and p["excel_ident"]:
            excel_slaganje["isti" if p["ident"] == p["excel_ident"] else "razlicit"] += 1
        elif p["ident"]:
            excel_slaganje["excel_nema"] += 1
        elif p["excel_ident"]:
            excel_slaganje["hub_nema"] += 1
        if p["provjeri"]:
            za_potvrdu.append(dict(dekor=d, restlova=n_dek[d], razina=p["razina"], kandidati=p["kandidati"], excel=p["excel_ident"],
                                   excel_status=p["excel_status"], objasnjenje=p["objasnjenje"]))
    za_potvrdu.sort(key=lambda z: -z["restlova"])
    return dict(datoteka=x["datoteka"], restlova=len(x["restlovi"]), dekora=len(dekori), novo=novo, osvjezeno=osvjezeno, zadrzano=zadrzano,
                po_dekoru=po_dekoru, po_restlu=po_restlu, razine=razine, excel_slaganje=excel_slaganje, za_potvrdu=za_potvrdu,
                m2_razlika=m2_razlika, upozorenja=x["upozorenja"])


def izvjestaj_md(iz):
    d, r = iz["po_dekoru"], iz["po_restlu"]
    nd, nr = iz["dekora"], iz["restlova"]
    L = ["# Uvoz evidencije restlova — %s" % iz["datoteka"], "",
         "Restlova **%d**, dekora **%d** (novo %d, osvježeno %d, zadržano %d)." % (nr, nd, iz["novo"], iz["osvjezeno"], iz["zadrzano"]), "",
         "| | dekora | restlova |", "|---|---|---|"]
    for k, ime in (("sigurno", "vezano na ident (sigurno)"), ("za_potvrdu", "za potvrdu (kandidati)"), ("nema", "nema kandidata")):
        L.append("| %s | %d (%.0f %%) | %d (%.0f %%) |" % (ime, d[k], 100.0 * d[k] / (nd or 1), r[k], 100.0 * r[k] / (nr or 1)))
    L += ["", "Razine: " + ", ".join("%s %d" % kv for kv in sorted(iz["razine"].items())),
          "Usporedba s Excelovim mapiranjem: isti ident %d, različit %d, Hub veže a Excel nema %d, Excel ima a Hub ne %d." % tuple(
              iz["excel_slaganje"][k] for k in ("isti", "razlicit", "excel_nema", "hub_nema")), ""]
    if iz["za_potvrdu"]:
        L += ["## Za potvrdu (%d dekora)" % len(iz["za_potvrdu"]), "", "| Dekor | restlova | kandidati (Hub) | Excel | zašto |", "|---|---|---|---|---|"]
        for z in iz["za_potvrdu"]:
            L.append("| %s | %d | %s | %s | %s |" % (z["dekor"], z["restlova"], "; ".join("%s %s" % (i, n) for i, n, _ in z["kandidati"][:3]) or "—",
                                                    ("%s (%s)" % (z["excel"], z["excel_status"])) if z["excel"] else (z["excel_status"] or "—"),
                                                    z["objasnjenje"].replace("|", "/")))
        L.append("")
    if iz["m2_razlika"]:
        L += ["M² iz mjera ≠ Excelov M2 (%d): %s" % (len(iz["m2_razlika"]), ", ".join("%s %g≠%g" % t for t in iz["m2_razlika"][:10])), ""]
    if iz["upozorenja"]:
        L += ["Upozorenja: " + "; ".join(iz["upozorenja"][:20]), ""]
    return "\n".join(L)


# ---------------------------------------------------------------- potvrda dekora (postaje alias, D-32)
def potvrdi_dekor(conn, dekor, materijal_id, tko):
    """Ured / skladištar potvrdi dekor → ident: svi restlovi tog dekora bez identa dobiju materijal, par ide u alias-tablicu. Vraća broj restlova."""
    m = conn.execute("SELECT id, pantheon_ident FROM materijal WHERE id = ? OR pantheon_ident = ?", (materijal_id, materijal_id)).fetchone()
    if not m:
        raise ValueError("nema materijala %s" % materijal_id)
    cur = conn.execute("UPDATE restl SET materijal_id = ?, provjeri = 0, razina = 'potvrda', kandidati_json = NULL WHERE dekor_ulaz = ? AND provjeri = 1",
                       (m["id"], dekor))
    P.potvrdi_materijal(conn, dekor, m["id"], tko, izvor="restlovi")
    dnevnik(conn, tko, "restl", None, "potvrda dekora", "%s → %s (%d restlova)" % (dekor, m["pantheon_ident"], cur.rowcount))
    conn.commit()
    return cur.rowcount


# ---------------------------------------------------------------- pogled (isto sučelje kao ploce / trake: stanje, lokacija)
def stanje(conn, materijal_id=None, ident=None, samo_slobodni=False):
    """Restlovi na stanju po materijalu: [{materijal_id, ident, naziv, debljina, kom, m2, restlovi:[{oznaka, L, W, kom, lokacija, status}]}].
    Na stanju su statusi slobodan / rezerviran / provjeri; 'prijedlog' (D-64/3) i nevezani dekori (provjeri = 1) se NE broje kao stanje."""
    st = "'slobodan'" if samo_slobodni else ", ".join("'%s'" % s for s in NA_STANJU)
    sql = ("SELECT r.id, r.oznaka, r.L, r.W, r.kom, r.lokacija, r.status, r.napomena, m.id AS mid, m.pantheon_ident, m.naziv_pantheon, m.debljina "
           "FROM restl r JOIN materijal m ON m.id = r.materijal_id WHERE r.status IN (%s) AND r.provjeri = 0" % st)
    args = []
    if materijal_id:
        sql += " AND m.id = ?"; args.append(materijal_id)
    if ident:
        sql += " AND m.pantheon_ident = ?"; args.append(ident)
    sql += " ORDER BY m.pantheon_ident, r.L * r.W DESC"
    out = {}
    for r in conn.execute(sql, args):
        o = out.setdefault(r["mid"], dict(materijal_id=r["mid"], ident=r["pantheon_ident"], naziv=r["naziv_pantheon"], debljina=r["debljina"],
                                          kom=0, m2=0.0, restlovi=[]))
        m2 = r["L"] * r["W"] * r["kom"] / 1e6
        o["kom"] += r["kom"]; o["m2"] += m2
        o["restlovi"].append(dict(id=r["id"], oznaka=r["oznaka"], L=r["L"], W=r["W"], kom=r["kom"], m2=round(m2, 3), lokacija=r["lokacija"],
                                  status=r["status"], napomena=r["napomena"]))
    for o in out.values():
        o["m2"] = round(o["m2"], 3)
    return list(out.values())


def lokacija(conn, oznaka):
    """Gdje je restl (A001, SATOR B 2.1) ili None."""
    r = conn.execute("SELECT lokacija FROM restl WHERE oznaka = ?", (oznaka,)).fetchone()
    return r["lokacija"] if r else None


def sazetak(conn):
    """Brojke za ekran / STANJE: restlova po statusu, za potvrdu, m² na stanju."""
    s = {r["status"]: r["n"] for r in conn.execute("SELECT status, COUNT(*) AS n FROM restl GROUP BY status")}
    zp = conn.execute("SELECT COUNT(*) AS n, COUNT(DISTINCT dekor_ulaz) AS d FROM restl WHERE provjeri = 1").fetchone()
    m2 = conn.execute("SELECT COALESCE(SUM(L * W * kom) / 1e6, 0) FROM restl WHERE provjeri = 0 AND status IN (%s)" % ", ".join("'%s'" % x for x in NA_STANJU)).fetchone()[0]
    return dict(po_statusu=s, ukupno=sum(s.values()), za_potvrdu=zp["n"], dekora_za_potvrdu=zp["d"], m2_na_stanju=round(m2, 1),
                zadnji_uvoz=postavka(conn, "restlovi_uvoz"))



# ---------------------------------------------------------------- oznake, ručni restl
def prag(conn):
    """Prag čuvanja restla iz Postavki (D-95) → (min_m2, min_mm, traka_mm)."""
    def f(k, zadano):
        try:
            return float(str(postavka(conn, k, zadano)).replace(",", "."))
        except (TypeError, ValueError):
            return float(zadano)
    return (f("restl_min_m2", OBR.RESTL_MIN_M2), f("restl_min_mm", OBR.RESTL_MIN_MM), f("restl_traka_mm", OBR.RESTL_TRAKA_MM))


def je_restl(conn, L, W):
    """Čuva li se ostatak mjere L × W kao restl (prag iz Postavki)."""
    m2, mm, tr = prag(conn)
    return OBR.je_restl(L, W, m2, mm, tr)


def nova_oznaka(conn):
    """Sljedeća oznaka u nizu R0001… (nastavlja Excelov niz; oznaka se nikad ne vraća)."""
    r = conn.execute("SELECT MAX(CAST(SUBSTR(oznaka, 2) AS INTEGER)) FROM restl WHERE oznaka GLOB 'R[0-9]*'").fetchone()[0]
    return "R%04d" % ((r or 0) + 1)


def novi_restl(conn, materijal_id, L, W, tko, kom=1, lokacija=None, napomena=None, status="slobodan", izvor="rucno", nalog_materijal_id=None,
               potvrdio=None, commit=True):
    """Ručno otvoren restl (skladištar) ili prijedlog Huba. Vraća dict restla."""
    m = conn.execute("SELECT id, pantheon_ident, naziv_kratki, naziv_pantheon FROM materijal WHERE id = ? OR pantheon_ident = ?", (materijal_id, materijal_id)).fetchone()
    if not m:
        raise ValueError("nema materijala %s" % materijal_id)
    if status not in STATUSI:
        raise ValueError("nepoznat status restla %s" % status)
    if not L or not W or L <= 0 or W <= 0:
        raise ValueError("restl treba mjere L × W")
    oz = nova_oznaka(conn)
    t = sada()
    cur = conn.execute("INSERT INTO restl (oznaka, materijal_id, dekor_ulaz, L, W, kom, lokacija, qr, status, provjeri, razina, izvor, nalog_materijal_id, "
                       "napomena, datum, potvrdio, potvrdjeno, kada) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'ident', ?, ?, ?, ?, ?, ?, ?)",
                       (oz, m["id"], m["naziv_kratki"] or m["naziv_pantheon"], float(L), float(W), int(kom or 1), lokacija, oz, status, izvor,
                        nalog_materijal_id, napomena, t[:10], potvrdio, t if potvrdio else None, t))
    dnevnik(conn, tko, "restl", cur.lastrowid, "novi", "%s %s %g×%g×%d %s (%s)" % (oz, m["pantheon_ident"], L, W, kom or 1, lokacija or "", status))
    if commit:
        conn.commit()
    return restl(conn, cur.lastrowid)


def restl(conn, restl_id):
    r = conn.execute("SELECT r.*, m.pantheon_ident AS ident, m.naziv_pantheon AS naziv, m.naziv_kratki, m.debljina FROM restl r "
                     "LEFT JOIN materijal m ON m.id = r.materijal_id WHERE r.id = ? OR r.oznaka = ?", (restl_id, restl_id)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["m2"] = round(d["L"] * d["W"] * d["kom"] / 1e6, 3)
    d["kandidati"] = json.loads(d["kandidati_json"]) if d.get("kandidati_json") else []
    return d


def popis(conn, ident=None, status=None, za_potvrdu=None, q=None, limit=500):
    """Popis restlova za ekran: filtri ident / status / za_potvrdu (dekor bez identa) / q (oznaka, dekor, lokacija)."""
    sql = ("SELECT r.*, m.pantheon_ident AS ident, m.naziv_pantheon AS naziv, m.naziv_kratki, m.debljina FROM restl r "
           "LEFT JOIN materijal m ON m.id = r.materijal_id WHERE 1 = 1")
    a = []
    if ident:
        sql += " AND m.pantheon_ident = ?"; a.append(ident)
    if status:
        st = [x.strip() for x in status.split(",") if x.strip()]
        sql += " AND r.status IN (%s)" % ", ".join("?" * len(st)); a += st
    if za_potvrdu is not None:
        sql += " AND r.provjeri = ?"; a.append(1 if za_potvrdu else 0)
    if q:
        sql += " AND (r.oznaka LIKE ? OR UPPER(r.dekor_ulaz) LIKE UPPER(?) OR UPPER(r.lokacija) LIKE UPPER(?) OR UPPER(m.naziv_pantheon) LIKE UPPER(?))"
        a += ["%" + q + "%"] * 4
    sql += " ORDER BY r.provjeri DESC, r.status, m.pantheon_ident, r.L * r.W DESC LIMIT ?"; a.append(limit)
    out = []
    for r in conn.execute(sql, a):
        d = dict(r); d["m2"] = round(d["L"] * d["W"] * d["kom"] / 1e6, 3)
        d["kandidati"] = json.loads(d["kandidati_json"]) if d.get("kandidati_json") else []
        out.append(d)
    return out


# ---------------------------------------------------------------- prijedlog iz potvrđene sheme (D-64/3) + potvrda skladištara
def kandidati_iz_sheme(conn, snimka):
    """Ostaci potvrđene sheme koji prolaze prag čuvanja (D-95) → [(L, W, m2, naplacen_kupcu)].
    Za radne ploče / zidne obloge ostatak dolazi iz `rp` (uz duljinu ploče), inače je to traka koja preostane na ploči."""
    ploca = snimka.get("ploca") or []
    trim = float(snimka.get("trim") or OBR.OBRUB)
    kerf = float(snimka.get("kerf") or OBR.KERF_OBRACUN)
    naplata = {(round(float(o[0])), round(float(o[1]))) for o in (snimka.get("ostaci") or [])}      # ostaci koje kupac NE plaća (D-19)
    sirovi = []
    rp = snimka.get("rp")
    if rp:
        for li in rp.get("listovi", []):
            o = li.get("ostatak")
            if o:
                sirovi.append((float(o[0]), float(o[1])))
    else:
        for sh in (snimka.get("sheets") or []):
            l1 = [st["w"] for st in sh.get("strips", [])]
            d1, d2, _ = OBR.ostatak_dims(sh.get("dir", "L"), l1, (float(ploca[0]), float(ploca[1])), trim, kerf)
            sirovi.append((float(d1), float(d2)))
    out = []
    for d1, d2 in sirovi:
        if d1 <= 0 or d2 <= 0 or not je_restl(conn, d1, d2):
            continue
        L, W = max(d1, d2), min(d1, d2)
        out.append((round(L), round(W), round(L * W / 1e6, 3), (round(d1), round(d2)) not in naplata and (round(d2), round(d1)) not in naplata))
    return out


def predlozi_iz_sheme(conn, nm_id, tko="hub", commit=True):
    """Iz POTVRĐENOG slaganja materijala naloga (D-75) otvori restlove-prijedloge za ostatke koji prolaze prag čuvanja (D-95:
    ≥ 0,35 m² ili traka ≥ 2 000 mm, kraća stranica ≥ 150 mm — postavke). Komad koji je ispod praga naplate kupac je platio, a mi ga
    ipak zadržimo — to piše u napomeni. Idempotentno: raniji prijedlozi istog materijala naloga koji još nisu potvrđeni se otpišu i
    naprave iznova. Samo za materijal koji ide na PILU (nesting ostatke vodi Winstore kao Drop). Vraća popis restlova (dict)."""
    from ..nalozi import optimiziraj as OP
    m = conn.execute("SELECT nm.*, m.pantheon_ident AS ident FROM nalog_materijal nm LEFT JOIN materijal m ON m.id = nm.materijal_id WHERE nm.id = ?", (nm_id,)).fetchone()
    if not m or not m["materijal_id"]:
        return []
    if (m["put"] or m["put_prijedlog"] or "pila") != "pila":
        return []
    r = OP.potvrdjena(conn, nm_id)
    if not r or not r["slaganje_json"]:
        return []
    kand = kandidati_iz_sheme(conn, json.loads(r["slaganje_json"]))
    mjere = sorted((float(k[0]), float(k[1])) for k in kand)
    postojeci = conn.execute("SELECT id, L, W FROM restl WHERE nalog_materijal_id = ? AND status = 'prijedlog' ORDER BY id", (nm_id,)).fetchall()
    if postojeci and sorted((x["L"], x["W"]) for x in postojeci) == mjere:
        return [restl(conn, x["id"]) for x in postojeci]                   # isto slaganje, isti prijedlozi — ništa ne diraj
    conn.execute("UPDATE restl SET status = 'otpisan', napomena = COALESCE(napomena || '; ', '') || 'prijedlog zamijenjen novom optimizacijom' "
                 "WHERE nalog_materijal_id = ? AND status = 'prijedlog'", (nm_id,))
    out = []
    n = conn.execute("SELECT naziv FROM nalog WHERE id = ?", (m["nalog_id"],)).fetchone()
    for i, (L, W, _m2, placen) in enumerate(kand, 1):
        nap = "ostatak %d/%d iz sheme %s (opt. %d)" % (i, len(kand), n["naziv"] if n else m["nalog_id"], r["id"])
        if placen:
            nap += "; kupac ga je platio (ispod praga naplate)"
        out.append(novi_restl(conn, m["materijal_id"], L, W, tko, status="prijedlog", izvor="prijedlog", nalog_materijal_id=nm_id,
                              napomena=nap, commit=False))
    if commit:
        conn.commit()
    return out


def prijedlozi(conn, nalog_id=None):
    sql = ("SELECT r.*, m.pantheon_ident AS ident, m.naziv_pantheon AS naziv, m.naziv_kratki, n.naziv AS nalog FROM restl r JOIN materijal m ON m.id = r.materijal_id "
           "LEFT JOIN nalog_materijal nm ON nm.id = r.nalog_materijal_id LEFT JOIN nalog n ON n.id = nm.nalog_id WHERE r.status = 'prijedlog'")
    a = []
    if nalog_id:
        sql += " AND nm.nalog_id = ?"; a.append(nalog_id)
    return [dict(r, m2=round(r["L"] * r["W"] * r["kom"] / 1e6, 3)) for r in conn.execute(sql + " ORDER BY r.id", a)]


def potvrdi_restl(conn, restl_id, tko, lokacija=None, L=None, W=None, commit=True):
    """Skladištar fizički potvrdio restl (zalijepio QR): prijedlog → slobodan, uz lokaciju i po potrebi ispravljenu mjeru;
    uvezeni restl (Excel) dobiva potvrdu pri prvom obilasku (inventura, D-64/3)."""
    r = restl(conn, restl_id)
    if not r:
        raise ValueError("nema restla %s" % restl_id)
    if r["status"] in ("potrosen", "otpisan"):
        raise ValueError("restl %s je %s" % (r["oznaka"], r["status"]))
    st = "slobodan" if r["status"] in ("prijedlog", "provjeri") else r["status"]
    conn.execute("UPDATE restl SET status = ?, lokacija = COALESCE(?, lokacija), L = COALESCE(?, L), W = COALESCE(?, W), potvrdio = ?, potvrdjeno = ?, datum = ? WHERE id = ?",
                 (st, lokacija, L, W, tko, sada(), sada()[:10], r["id"]))
    dnevnik(conn, tko, "restl", r["id"], "potvrda", "%s → %s%s" % (r["oznaka"], st, (" @ " + lokacija) if lokacija else ""))
    if commit:
        conn.commit()
    return restl(conn, r["id"])


def odbaci_restl(conn, restl_id, tko, razlog=None, commit=True):
    """Prijedlog kojeg fizički nema (ili restl koji je bačen) → otpisan."""
    r = restl(conn, restl_id)
    if not r:
        raise ValueError("nema restla %s" % restl_id)
    if r["status"] == "rezerviran":
        raise ValueError("restl %s je rezerviran — prvo osloboditi" % r["oznaka"])
    conn.execute("UPDATE restl SET status = 'otpisan', napomena = ?, datum = ? WHERE id = ?",
                 ((r["napomena"] + "; " if r["napomena"] else "") + (razlog or "otpisan"), sada()[:10], r["id"]))
    dnevnik(conn, tko, "restl", r["id"], "otpis", "%s: %s" % (r["oznaka"], razlog or ""))
    if commit:
        conn.commit()
    return restl(conn, r["id"])


# ---------------------------------------------------------------- rezervacija restla za nalog (D-42/4)
def kandidati(conn, materijal_id, L=None, W=None, samo_slobodni=True):
    """Restlovi materijala u koje stane komad L × W (u bilo kojoj orijentaciji); bez mjera = svi na stanju."""
    out = []
    for o in stanje(conn, materijal_id=materijal_id, samo_slobodni=samo_slobodni):
        for r in o["restlovi"]:
            if L and W and not ((r["L"] >= L and r["W"] >= W) or (r["L"] >= W and r["W"] >= L)):
                continue
            out.append(dict(r, ident=o["ident"]))
    return out


def rezerviraj(conn, nm_id, restl_id, tko, commit=True):
    """Veži restl na materijal naloga: rezervacija (restl_id) + status restla 'rezerviran'. Restl mora biti slobodan i istog materijala."""
    from ..nalozi.nalozi import korisnik_id
    r = restl(conn, restl_id)
    nm = conn.execute("SELECT id, materijal_id FROM nalog_materijal WHERE id = ?", (nm_id,)).fetchone()
    if not r or not nm:
        raise ValueError("nema restla %s ili materijala naloga %s" % (restl_id, nm_id))
    if r["status"] != "slobodan" or r["provjeri"]:
        raise ValueError("restl %s nije slobodan (%s)" % (r["oznaka"], "dekor nije potvrđen" if r["provjeri"] else r["status"]))
    if r["materijal_id"] != nm["materijal_id"]:
        raise ValueError("restl %s je %s, materijal naloga je drugi ident" % (r["oznaka"], r["ident"]))
    cur = conn.execute("INSERT INTO rezervacija (nalog_materijal_id, restl_id, kom, status, datum, korisnik_id) VALUES (?, ?, ?, 'rezervirano', ?, ?)",
                       (nm_id, r["id"], r["kom"], sada(), korisnik_id(conn, tko)))
    conn.execute("UPDATE restl SET status = 'rezerviran', datum = ? WHERE id = ?", (sada()[:10], r["id"]))
    dnevnik(conn, tko, "rezervacija", cur.lastrowid, "rezerviraj restl", "nm %d ← %s" % (nm_id, r["oznaka"]))
    if commit:
        conn.commit()
    return cur.lastrowid


def rezervirani(conn, nm_id):
    """Restlovi aktivno rezervirani za materijal naloga."""
    return [restl(conn, x["restl_id"]) for x in conn.execute(
        "SELECT restl_id FROM rezervacija WHERE nalog_materijal_id = ? AND restl_id IS NOT NULL AND status IN ('rezervirano', 'izdano')", (nm_id,))]


def oslobodi(conn, nm_id, tko, commit=True):
    n = 0
    for x in conn.execute("SELECT id, restl_id FROM rezervacija WHERE nalog_materijal_id = ? AND restl_id IS NOT NULL AND status = 'rezervirano'", (nm_id,)).fetchall():
        conn.execute("UPDATE rezervacija SET status = 'oslobodjeno' WHERE id = ?", (x["id"],))
        conn.execute("UPDATE restl SET status = 'slobodan', datum = ? WHERE id = ? AND status = 'rezerviran'", (sada()[:10], x["restl_id"]))
        n += 1
    if n:
        dnevnik(conn, tko, "rezervacija", None, "oslobodi restl", "nm %d: %d" % (nm_id, n))
    if commit:
        conn.commit()
    return n


def izdaj(conn, nm_id, tko, nalog_naziv=None, commit=True):
    """Materijal naloga otišao na stroj: rezervirani restl je potrošen (nalog izlaz), rezervacija → izdano."""
    n = 0
    for x in conn.execute("SELECT id, restl_id FROM rezervacija WHERE nalog_materijal_id = ? AND restl_id IS NOT NULL AND status = 'rezervirano'", (nm_id,)).fetchall():
        conn.execute("UPDATE rezervacija SET status = 'izdano', izdano_kada = ? WHERE id = ?", (sada(), x["id"]))
        conn.execute("UPDATE restl SET status = 'potrosen', nalog_izlaz = ?, datum = ? WHERE id = ?", (nalog_naziv, sada()[:10], x["restl_id"]))
        n += 1
    if commit:
        conn.commit()
    return n


# ---------------------------------------------------------------- CLI
def main(argv=None):
    from .. import db
    ap = argparse.ArgumentParser(description="Restlovi (D-64): uvoz evidencije, stanje, potvrda dekora")
    ap.add_argument("--db", default=None)
    ap.add_argument("--uvoz", metavar="XLSM", help="uvezi RESTLOVI_V7.xlsm")
    ap.add_argument("--md", metavar="DATOTEKA", help="izvještaj uvoza u Markdown")
    ap.add_argument("--stanje", action="store_true")
    ap.add_argument("--ident")
    ap.add_argument("--potvrdi", nargs=2, metavar=("DEKOR", "IDENT"))
    ap.add_argument("--tko", default="cli")
    ap.add_argument("--prijedlozi", action="store_true", help="restlovi predloženi iz potvrđenih shema, čekaju skladištara")
    ap.add_argument("--nalog", type=int)
    ap.add_argument("--potvrdi-restl", metavar="OZNAKA")
    ap.add_argument("--lokacija")
    a = ap.parse_args(argv)
    conn = db.spoji(a.db)
    if a.prijedlozi:
        for r in prijedlozi(conn, a.nalog):
            print("%s %s %g × %g  %.2f m²  %s  (%s)" % (r["oznaka"], r["ident"], r["L"], r["W"], r["m2"], r["nalog"] or "", r["napomena"] or ""))
    if a.potvrdi_restl:
        r = potvrdi_restl(conn, a.potvrdi_restl, a.tko, a.lokacija)
        print("potvrđeno:", r["oznaka"], r["status"], r["lokacija"])
    if a.uvoz:
        iz = uvezi_excel(conn, a.uvoz, a.tko)
        md = izvjestaj_md(iz)
        print(md)
        if a.md:
            open(a.md, "w", encoding="utf-8").write(md)
    if a.potvrdi:
        print("potvrđeno restlova:", potvrdi_dekor(conn, a.potvrdi[0], a.potvrdi[1], a.tko))
    if a.stanje:
        for o in stanje(conn, ident=a.ident):
            print("%s %s (%s mm): %d kom, %.2f m²" % (o["ident"], o["naziv"], o["debljina"], o["kom"], o["m2"]))
            for r in o["restlovi"]:
                print("   %s %g × %g × %d  %s  %s" % (r["oznaka"], r["L"], r["W"], r["kom"], r["lokacija"] or "-", r["status"]))
        print(sazetak(conn))
    return 0


if __name__ == "__main__":
    sys.exit(main())
