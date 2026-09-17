# -*- coding: utf-8 -*-
"""Izvoz naloga na nesting: CSV + CIX za bNest (kralježnica korak 3, 04 §4).

Zamjenjuje ono što danas radi PPNEST: iz naloga po MATERIJALU nastaje jedna CSV lista elemenata (28 stupaca, isti profil
koji bNest već čita) i jedna CIX datoteka po elementu. Mape su kao dosad — `<mapa>/<NALOG>/NESTING/`.

    py -m hub.nalozi.export_nesting --db hub.db --nalog 12 --mapa C:\\PPNESTING
    py -m hub.nalozi.export_nesting --db hub.db --nalog 12 --mapa . --stil ppnest --suho

Dvije stvari koje Hub radi, a PPNEST nije:
  * **ime CIX datoteke je jedinstveno zauvijek** (D-23) — bNest datoteku s istim imenom pregazi bez pitanja, a to se već
    dogodilo. Hub imena dijeli iz brojača i upisuje ih u `cix_registar`; ime se ne oslobađa ni kad se element obriše.
  * **SIFRA MAT je Winstore kod** iz šifrarnika (D-24), ne prepisani tekst — pa bNest nađe ploču bez ručnog mapiranja.

Element koji već ima CIX ime (npr. iz Corpusa, D-55) zadržava svoje — Hub ga samo registrira i proslijedi.
"""
import argparse
import json
import os
import shutil
import sys

from .. import db
from ..db import sada, dnevnik, postavka, postavi
from ..formati import nalog_io
from . import nalozi as N, grupe as G

PODMAPA_KANT = "HORIZONTALNO_BUSENJE"   # Corpusov drugi CIX (bušenje u kant) ide u podmapu, kako operater već ima (D-55/3)
PODMAPA_CLANOVA = {"niz": "NIZ", "mali": "MAJKA"}   # korak 6: CIX-ovi fronti / komada koji se režu IZ majke — nisu u CSV-u, program ide na Rover na izrezanom komadu
PREFIKS = "H"          # Hubova imena: H0000001 — razlikuju se od PPNEST-ovih (ddmmyy_HHmmss) i Corpusovih (14 hex znamenki)
STATUSI_ZA_STROJ = ("potvrdjeno", "skladiste", "pila_nesting")   # D-35: na stroj tek nakon potvrde kupca (Igor, 15. 9. 2026.)


class ExportGreska(Exception):
    pass


def provjeri_spremnost(conn, n, forsiraj=False, suho=False):
    """Zajednički uvjeti za izvoz na stroj (nesting, pila): nikad s otvorenim stavkama za potvrdu; iz statusa unos / ponuda
    samo uz forsiraj (probe) ili u suhom načinu (ekran pokazuje što bi nastalo). Vraća popis upozorenja."""
    otvoreno = N.broj_za_potvrdu(conn, n["id"])
    if otvoreno:
        raise ExportGreska("nalog %s ima %d stavki za potvrdu — prvo potvrditi materijale i trake" % (n["naziv"], otvoreno))
    upozorenja = []
    if n["status"] not in STATUSI_ZA_STROJ:
        poruka = "nalog %s je u statusu '%s' — na stroj ide tek iz statusa %s" % (n["naziv"], n["status"], " / ".join(STATUSI_ZA_STROJ))
        if not (forsiraj or suho):
            raise ExportGreska(poruka + " (za probu: --forsiraj)")
        upozorenja.append(poruka)
    return upozorenja


def _dogadjaj_izvoza(conn, n, tko, razlog, veza):
    conn.execute("INSERT INTO dogadjaj (nalog_id, kada, tko_id, iz_statusa, u_status, razlog, veza) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (n["id"], sada(), N.korisnik_id(conn, tko), n["status"], n["status"], razlog, veza))


def uz_rollback(fn):
    """Izvoz koji padne (disk, shema, greška u kodu) ne smije ostaviti pola upisa u otvorenoj transakciji."""
    def omot(conn, *a, **kw):
        try:
            return fn(conn, *a, **kw)
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
    omot.__name__, omot.__doc__ = fn.__name__, fn.__doc__
    return omot


def _bez_dij(s):
    return nalog_io.bez_dijakritika(s or "").upper().replace(" ", "_").replace("/", "_")


def registriraj(conn, ime, element_id=None, nalog_id=None, izvor="hub"):
    """Upiši ime u registar. Vraća False ako je ime već zauzeto DRUGIM elementom (D-23)."""
    r = conn.execute("SELECT element_id, izvor FROM cix_registar WHERE ime = ?", (ime,)).fetchone()
    if r:
        if r["element_id"] is None and izvor == "corpus" and r["izvor"] == "corpus" and element_id is not None:
            # Corpusovo ime čiji je element obrisan (probni ili krivo otvoren nalog): isti program iz istog Corpus projekta smije ga
            # ponovno preuzeti — datoteka je ista, pa pregaženja nema. Hubova (H…) i PPNEST-ova imena se nikad ne vraćaju (D-23).
            conn.execute("UPDATE cix_registar SET element_id = ?, nalog_id = ?, kada = ? WHERE ime = ?", (element_id, nalog_id, sada(), ime))
            return True
        return r["element_id"] == element_id
    conn.execute("INSERT INTO cix_registar (ime, element_id, nalog_id, izvor, kada) VALUES (?, ?, ?, ?, ?)",
                 (ime, element_id, nalog_id, izvor, sada()))
    return True


def novo_ime(conn, element_id=None, nalog_id=None):
    """Sljedeće slobodno Hub ime iz brojača (`postavke.brojac_cix`), preskačući sve što je registar već vidio."""
    n = int(postavka(conn, "brojac_cix", "0") or 0)
    for _ in range(1000000):
        n += 1
        ime = "%s%07d" % (PREFIKS, n)
        if registriraj(conn, ime, element_id, nalog_id, "hub"):
            postavi(conn, "brojac_cix", str(n), "zadnje dodijeljeno ime CIX datoteke (D-23)")
            return ime
    raise ExportGreska("brojač CIX imena je pun")


def dodijeli_imena(conn, nalog_id, tko="web"):
    """Svakom elementu naloga bez CIX imena dodijeli novo i registriraj ga; postojeća imena samo registrira.
    Ime koje već pripada drugom elementu: Corpusovo je nedodirljivo (D-55) → greška; PPNEST-ovo ime po vremenu se ponavlja
    (D-60) → element dobiva novo Hub ime, staro ostaje zauzeto. Vraća (novih, registriranih_otprije)."""
    novo, staro = 0, 0
    for r in conn.execute(
            "SELECT e.id, e.cix_ime, e.cix_izvor FROM element e JOIN nalog_materijal nm ON nm.id = e.nalog_materijal_id "
            "WHERE nm.nalog_id = ? ORDER BY nm.rb, nm.id, e.rb, e.id", (nalog_id,)).fetchall():
        if r["cix_ime"]:
            if registriraj(conn, r["cix_ime"], r["id"], nalog_id, r["cix_izvor"] or "corpus"):
                staro += 1
                continue
            if (r["cix_izvor"] or "corpus") == "corpus":
                raise ExportGreska("ime CIX datoteke '%s' već pripada drugom elementu — preimenovati u Corpusu prije izvoza (D-23)" % r["cix_ime"])
            dnevnik(conn, tko, "element", r["id"], "cix_preimenovan", "%s zauzeto (%s) → novo Hub ime" % (r["cix_ime"], r["cix_izvor"]))
        conn.execute("UPDATE element SET cix_ime = ?, cix_izvor = 'hub' WHERE id = ?", (novo_ime(conn, r["id"], nalog_id), r["id"]))
        novo += 1
    conn.commit()
    return novo, staro


def _corpus_cix(e):
    """Za element iz Corpusa (cix_izvor = corpus) izvorne CIX datoteke iz obrada_json: [(ime, izvorna_putanja, podmapa)] — D-55/3 oba."""
    if (e.get("cix_izvor") or "") != "corpus" or not e.get("obrada_json"):
        return []
    try:
        o = json.loads(e["obrada_json"])
    except ValueError:
        return []
    out = []
    if o.get("cix", {}).get("put"):
        out.append((o["cix"]["ime"], o["cix"]["put"], ""))
    if o.get("cix2", {}).get("put"):
        out.append((o["cix2"]["ime"], o["cix2"]["put"], PODMAPA_KANT))
    return out


def _prenesi_corpus_cix(grupa, korijen, suho, upozorenja=None):
    """Corpusove CIX-ove Hub ne generira nego kopira nepromijenjene (D-29); uz CIX za kant ide i .wmf slika ako postoji.
    Korak 6 (D-80): element čija je mjera za rezanje veća od konačne dobiva KOPIJU s povećanim LPX / LPY (obrade ostaju na mjestu);
    ima li i bušenje u kant (drugi CIX), rub koji se produžuje može ga pomaknuti → upozorenje „provjeri“.
    Vraća (popis odredišnih putanja, popis elemenata koje Hub sam mora napisati)."""
    kopije, hub_pise, plan = [], [], []
    for e in grupa:                                     # prvo sve provjeri, pa tek onda kopiraj — da ne ostane pola paketa
        izvorni = _corpus_cix(e)
        if not izvorni:
            hub_pise.append(e)
            continue
        prosiri = bool(e.get("rez_razlog")) and (abs(e["L"] - e.get("L_kon", e["L"])) > 0.01 or abs(e["W"] - e.get("W_kon", e["W"])) > 0.01)
        if prosiri and len(izvorni) > 1 and upozorenja is not None:
            upozorenja.append("%s: mjera za rezanje %gx%g (konačna %gx%g) i bušenje u kant — PROVJERITI program %s na produženom rubu"
                              % (e.get("naziv") or e["cix"], e["L"], e["W"], e["L_kon"], e["W_kon"], izvorni[1][0]))
        for ime, put, podmapa in izvorni:
            if not os.path.isfile(put):
                raise ExportGreska("izvorna CIX datoteka iz Corpusa ne postoji: %s (element %s)" % (put, e.get("naziv") or e["cix"]))
            cilj = os.path.join(os.path.join(korijen, podmapa) if podmapa else korijen, ime + ".cix")
            kopije.append(cilj)
            plan.append((put, cilj, e if (prosiri and not podmapa) else None))
    if not suho:
        for put, cilj, e in plan:
            os.makedirs(os.path.dirname(cilj), exist_ok=True)
            if e is not None:
                ok, upoz = G.kopiraj_cix_prosiren(put, cilj, e["L_kon"], e["W_kon"], e["L"], e["W"])
                if upoz and upozorenja is not None:
                    upozorenja.append(upoz)
            else:
                shutil.copyfile(put, cilj)
            wmf = os.path.splitext(put)[0] + ".wmf"
            if os.path.isfile(wmf):
                shutil.copyfile(wmf, os.path.splitext(cilj)[0] + ".wmf")
    return kopije, hub_pise


def _prenesi_cix_clanova(conn, nm_id, korijen, suho):
    """CIX-ovi članova majki (fronte niza, komadi iz majke) — nisu u CSV-u za nesting (režu se iz majke), program ide na Rover na
    izrezanom komadu; kopiraju se u podmapu NIZ / MAJKA da operater ima sve na jednom mjestu. Vraća popis odredišnih putanja."""
    out = []
    for e in G.clanovi_s_cix(conn, nm_id):
        for ime, put, podmapa in _corpus_cix(dict(cix_izvor=e["cix_izvor"], obrada_json=e["obrada_json"])):
            if not os.path.isfile(put):
                raise ExportGreska("izvorna CIX datoteka iz Corpusa ne postoji: %s (član %s)" % (put, e.get("naziv") or ime))
            cilj = os.path.join(korijen, PODMAPA_CLANOVA[e["majka_vrsta"]], podmapa, ime + ".cix") if podmapa else os.path.join(korijen, PODMAPA_CLANOVA[e["majka_vrsta"]], ime + ".cix")
            out.append(cilj)
            if not suho:
                os.makedirs(os.path.dirname(cilj), exist_ok=True)
                shutil.copyfile(put, cilj)
    return out


def _po_materijalu(els):
    red = []
    for e in els:
        if not red or red[-1][0] != e["nalog_materijal_id"]:
            red.append((e["nalog_materijal_id"], []))
        red[-1][1].append(e)
    return red


@uz_rollback
def izvezi(conn, nalog_id, mapa, tko="web", stil="bsolid", samo_nesting=True, suho=False, vrijeme=None, forsiraj=False):
    """Napiši CSV + CIX po materijalu u `<mapa>/<NAZIV NALOGA>/NESTING/`. Vraća popis paketa (jedan po materijalu).

    samo_nesting: preskoči materijale koje je voditelj poslao na pilu (`nalog_materijal.put = 'pila'`).
    suho: samo izračunaj što bi nastalo, ne diraj disk ni bazu (za provjeru i za ekran prije izvoza).
    forsiraj: dopusti izvoz i iz statusa unos / ponuda (probe); stavke za potvrdu blokiraju uvijek.
    """
    n = N.nalog(conn, nalog_id)
    upozorenja = provjeri_spremnost(conn, n, forsiraj, suho)
    if not suho:
        dodijeli_imena(conn, nalog_id, tko)
    els = N.elementi_za_export(conn, nalog_id)
    if not els:
        raise ExportGreska("nalog %s nema elemenata" % n["naziv"])
    zig = (vrijeme or __import__("datetime").datetime.now()).strftime("%d%m%y_%H%M%S")
    korijen = os.path.join(mapa, n["naziv"], "NESTING")
    paketi, preskoceno = [], []
    for nm_id, grupa in _po_materijalu(els):
        m = N.materijal_naloga(conn, nm_id)
        if samo_nesting and (m["put"] or "") == "pila":
            preskoceno.append(dict(materijal=m["naziv_kratki"] or m["naziv_ulaz"], razlog="ide na pilu", elemenata=len(grupa)))
            continue
        if not m["materijal_id"]:
            preskoceno.append(dict(materijal=m["naziv_ulaz"], razlog="materijal nije potvrđen", elemenata=len(grupa)))
            continue
        deb = grupa[0]["deb"]
        if not deb:
            preskoceno.append(dict(materijal=m["naziv_kratki"], razlog="nepoznata debljina", elemenata=len(grupa)))
            continue
        try:
            nalog_io.alat_za_debljinu(deb)                      # nesting ne reže deblje od 26 mm
        except ValueError as e:
            preskoceno.append(dict(materijal=m["naziv_kratki"], razlog=str(e), elemenata=len(grupa)))
            continue
        for i, e in enumerate(grupa, 1):                        # rb unutar paketa kreće od 1, kao kod PPNEST-a
            e["rb"] = i
            e["mat"] = _bez_dij(e["mat"])
        baza_ime = "%s_%s_%s" % (_bez_dij(n["naziv"]), _bez_dij(grupa[0]["mat"]), zig)
        csv_put = os.path.join(korijen, baza_ime + ".CSV")
        kopije, hub_pise = _prenesi_corpus_cix(grupa, korijen, suho, upozorenja)      # Corpusovi CIX-ovi se kopiraju (oba), ostale piše Hub
        cix_clanova = _prenesi_cix_clanova(conn, nm_id, korijen, suho)             # korak 6: fronte / komadi iz majke → podmapa NIZ / MAJKA
        p = dict(nalog_materijal_id=nm_id, materijal=grupa[0]["mat"], ident=m["ident"], winstore_kod=m["winstore_kod"] or "",
                 debljina=deb, elemenata=len(grupa), komada=sum(x["kom"] for x in grupa),
                 m2=round(sum(x["L"] * x["W"] * x["kom"] for x in grupa) / 1e6, 3),
                 csv=csv_put, cix=[os.path.join(korijen, (x["cix"] or "") + ".cix") for x in hub_pise] + kopije,
                 cix_corpus=len(kopije), bez_winstore_koda=not (m["winstore_kod"] or ""), cix_clanova=cix_clanova,
                 majke=[x for x in grupa if x.get("vrsta") == "majka"], suzeno=[x for x in grupa if x.get("rez_razlog") == "suziti"])
        if not suho:
            os.makedirs(korijen, exist_ok=True)
            nalog_io.write_ppnest_csv(grupa, csv_put)
            nalog_io.write_cix(hub_pise, korijen, stil=stil)
            p["skice"] = G.skice_materijala(conn, nm_id, korijen, baza_ime)         # skica majke za operatera (rezovi, oznake)
            for vrsta, put in [("csv", csv_put)] + [("cix", x) for x in p["cix"] + cix_clanova] + [("png", x["png"]) for x in p["skice"]]:
                conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, datum) VALUES (?, ?, ?, ?)", (nalog_id, vrsta, put, sada()))
        paketi.append(p)
    if not paketi:
        raise ExportGreska("nema nijednog materijala za nesting (%s)" % ("; ".join("%s: %s" % (x["materijal"], x["razlog"]) for x in preskoceno) or "nalog je prazan"))
    if not suho:
        dnevnik(conn, tko, "nalog", nalog_id, "izvoz_nesting",
                "%s: %d paketa, %d elemenata, %d CIX" % (n["naziv"], len(paketi), sum(x["elemenata"] for x in paketi),
                                                         sum(len(x["cix"]) for x in paketi)))
        _dogadjaj_izvoza(conn, n, tko, "izvoz na nesting: %d paketa, %d CIX" % (len(paketi), sum(len(x["cix"]) for x in paketi)), "mapa:" + korijen)
        conn.commit()
    return dict(nalog=n["naziv"], mapa=korijen, paketi=paketi, preskoceno=preskoceno, stil=stil, suho=suho, upozorenja=upozorenja)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Izvoz naloga na nesting: CSV + CIX za bNest (korak 3)")
    ap.add_argument("--db")
    ap.add_argument("--nalog", type=int, required=True, help="id naloga")
    ap.add_argument("--mapa", default=".", help="korijen izvoza (nastaje <mapa>\\<NALOG>\\NESTING\\)")
    ap.add_argument("--stil", choices=("bsolid", "ppnest"), default="bsolid", help="postavke CIX-a: bsolid (operater) ili ppnest")
    ap.add_argument("--sve", action="store_true", help="izvezi i materijale koje je voditelj poslao na pilu")
    ap.add_argument("--suho", action="store_true", help="samo pokaži što bi nastalo, ne piši ništa")
    ap.add_argument("--forsiraj", action="store_true", help="izvezi i nalog koji još nije potvrđen (status unos / ponuda) — samo za probe")
    ap.add_argument("--tko", default="web")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    try:
        r = izvezi(conn, a.nalog, a.mapa, a.tko, a.stil, samo_nesting=not a.sve, suho=a.suho, forsiraj=a.forsiraj)
    except ExportGreska as e:
        print("GRESKA:", e)
        return 1
    print("%s%s -> %s" % ("[suho] " if a.suho else "", r["nalog"], r["mapa"]))
    for p in r["paketi"]:
        print("   %-28s %-12s %4s mm  %3d el / %3d kom  %7.2f m2  %d CIX%s%s"
              % (p["materijal"][:28], p["winstore_kod"] or "-", p["debljina"], p["elemenata"], p["komada"], p["m2"], len(p["cix"]),
                 " (%d iz Corpusa)" % p["cix_corpus"] if p.get("cix_corpus") else "",
                 "   PAZI: nema Winstore koda" if p["bez_winstore_koda"] else ""))
        print("      %s" % os.path.basename(p["csv"]))
        for x in p.get("majke", []):
            print("      MAJKA %-30s %gx%g x%d  [%s]" % (x["naziv"][:30], x["L"], x["W"], x["kom"], x["napomena"]))
        for x in p.get("suzeno", []):
            print("      SUZITI %-28s reze se %gx%g, konacna %gx%g  [%s]" % ((x["naziv"] or "")[:28], x["L"], x["W"], x["L_kon"], x["W_kon"], x["napomena"]))
        if p.get("cix_clanova"):
            print("      CIX clanova majki (Rover na izrezanom komadu): %d" % len(p["cix_clanova"]))
    for x in r["preskoceno"]:
        print("   preskoceno: %-28s %s (%d el.)" % ((x["materijal"] or "?")[:28], x["razlog"], x["elemenata"]))
    for x in r["upozorenja"]:
        print("   PAZI:", x)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
