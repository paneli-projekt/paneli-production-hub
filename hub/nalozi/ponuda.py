# -*- coding: utf-8 -*-
"""Ponuda iz Huba (D-40) i završni korak vlastite proizvodnje (D-56) — kralježnica korak 4.

Tok: obračun (obracun.py) → VERZIJA ponude (snimka stavki s cijenom i rabatom, neto + PDV) → poslana kupcu mailom s PDF-om (D-41: SMTP
hostinga, mail.py; bez lozinke ured šalje sam i označi poslanu) → ured upiše potvrdu kupca (dijalog 3b) → eSlog 220 XML u Pantheon (ponuda → račun), s Pantheon brojem
ponude u nalogu. Svaka nova verzija zamjenjuje prethodnu (status `zamijenjena`), potvrđena se više ne mijenja.

Vlastita proizvodnja (D-56): ponuda je RADNI dokument — po završetku posla `korekcija_po_stvarnom` iz bNestovog rezultata (.mno,
dokument 19) uzme STVARNO potrošene ploče (umjesto PW-metode) i napravi verziju `izdatnica` s vlastitim eSlog-om za internu izdatnicu.

eSlog: isti kalup kao `skripte\\12_ponuda_eslog.py` (klon Pantheon izvoza 26-010-003175, uvoz potvrđen 29. 8. 2026.):
`NarociloEnostavno/Dokument` → glava 220 → datum 137 → PUR napomena → BY / DP / SU / OB → `PostavkeDokumenta` po stavci → kontrola.
Rabat po stavci ide u `OdstotkiPostavk` (postotak + iznos) — TREBA PROBNI UVOZ da se potvrdi da ga Pantheon preuzme (STANJE, otvoreno 6).
"""
import argparse
import datetime
import os
import sys
from xml.sax.saxutils import escape

from .. import db
from ..db import sada, dnevnik, postavka
from . import nalozi as N, obracun as OC, optimiziraj as OP

MJ = {"KOM": "H87", "KPT": "H87", "PAR": "PAI", "M": "MTR", "M2": "MTK", "M3": "MTQ", "KG": "KGM", "L": "LTR", "SAT": "HUR"}
NASA = dict(naziv="PANELI PROJEKT d.o.o.", ulica="Svilajska Ulica 30A", kraj="OSIJEK", posta="HR-31000", vat="3842622")
STATUSI_VERZIJE = ("nacrt", "poslana", "potvrdjena", "zamijenjena", "izdatnica")


class PonudaGreska(ValueError):
    pass


def verzije(conn, nalog_id):
    out, pret = [], None
    for v in conn.execute("SELECT v.*, k.oznaka AS poslao FROM ponuda_verzija v LEFT JOIN korisnik k ON k.id = v.poslao_id WHERE v.nalog_id = ? ORDER BY v.verzija",
                          (nalog_id,)).fetchall():
        d = dict(v)
        d["stavki"] = conn.execute("SELECT COUNT(*) FROM obracun_stavka WHERE ponuda_verzija_id = ?", (v["id"],)).fetchone()[0]
        d["promjene"] = promjene(conn, pret, v) if pret is not None else None     # sažetak ispod novije verzije (Igor, 17. 9.)
        pret = v
        out.append(d)
    return out


def _kljuc_stavke(s):
    """Ista stavka u dvije verzije: isti ident na istom materijalu naloga; stavke bez materijala (usluge, ručne) i po nazivu."""
    return (s["pantheon_ident"] or "", s.get("nalog_materijal_id") or 0, "" if s.get("nalog_materijal_id") else (s["naziv"] or "").strip().upper())


def _skupi(stavke):
    g = {}
    for s in stavke:
        k = _kljuc_stavke(s)
        if k not in g:
            g[k] = dict(ident=s["pantheon_ident"], naziv=s["naziv"], jm=s["jm"], kolicina=0.0, iznos=0.0, cijena=s["cijena"], rabat=s["rabat"] or 0, redaka=0)
        x = g[k]
        x["kolicina"] += s["kolicina"] or 0
        x["iznos"] += s["iznos"] or 0
        x["redaka"] += 1
    return g


def promjene(conn, stara, nova):
    """Što se promijenilo od verzije `stara` do `nova` (redak ponuda_verzija ili id): razlika neto / s PDV-om, dodane i uklonjene stavke,
    promjene količine, cijene i rabata. Redoslijed: najveća razlika iznosa prva."""
    def red(v):
        return v if not isinstance(v, int) else conn.execute("SELECT * FROM ponuda_verzija WHERE id = ?", (v,)).fetchone()
    stara, nova = red(stara), red(nova)
    a = _skupi(OC.stavke(conn, stara["nalog_id"], stara["id"]))
    b = _skupi(OC.stavke(conn, nova["nalog_id"], nova["id"]))
    dodano, uklonjeno, promijenjeno = [], [], []
    for k, x in b.items():
        if k not in a:
            dodano.append(dict(ident=x["ident"], naziv=x["naziv"], kolicina=round(x["kolicina"], 3), jm=x["jm"], razlika=round(x["iznos"], 2)))
    for k, x in a.items():
        if k not in b:
            uklonjeno.append(dict(ident=x["ident"], naziv=x["naziv"], kolicina=round(x["kolicina"], 3), jm=x["jm"], razlika=round(-x["iznos"], 2)))
    for k, y in b.items():
        x = a.get(k)
        if not x:
            continue
        polja = []
        if abs(x["kolicina"] - y["kolicina"]) > 0.0005:
            polja.append(dict(polje="kolicina", staro=round(x["kolicina"], 3), novo=round(y["kolicina"], 3)))
        if x["redaka"] == 1 and y["redaka"] == 1:
            if (x["cijena"] is None) != (y["cijena"] is None) or (x["cijena"] is not None and abs(x["cijena"] - y["cijena"]) > 0.00005):
                polja.append(dict(polje="cijena", staro=x["cijena"], novo=y["cijena"]))
            if abs((x["rabat"] or 0) - (y["rabat"] or 0)) > 0.0005:
                polja.append(dict(polje="rabat", staro=x["rabat"], novo=y["rabat"]))
        raz = round(y["iznos"] - x["iznos"], 2)
        if polja or abs(raz) >= 0.01:
            promijenjeno.append(dict(ident=y["ident"], naziv=y["naziv"], jm=y["jm"], polja=polja, razlika=raz))
    po_iznosu = lambda z: -abs(z["razlika"])
    neto = round((nova["iznos_neto"] or 0) - (stara["iznos_neto"] or 0), 2)
    ukupno = round(((nova["iznos_neto"] or 0) + (nova["iznos_pdv"] or 0)) - ((stara["iznos_neto"] or 0) + (stara["iznos_pdv"] or 0)), 2)
    return dict(prema=stara["verzija"], neto_razlika=neto, ukupno_razlika=ukupno,
                dodano=sorted(dodano, key=po_iznosu), uklonjeno=sorted(uklonjeno, key=po_iznosu), promijenjeno=sorted(promijenjeno, key=po_iznosu),
                bez_promjene=not (dodano or uklonjeno or promijenjeno) and abs(neto) < 0.01)


def verzija(conn, verzija_id):
    v = conn.execute("SELECT * FROM ponuda_verzija WHERE id = ?", (verzija_id,)).fetchone()
    if not v:
        raise PonudaGreska("nema verzije ponude %s" % verzija_id)
    d = dict(v)
    d["stavke"] = OC.stavke(conn, v["nalog_id"], verzija_id)
    return d


def nova_verzija(conn, nalog_id, tko="web", pravila=True, status="nacrt", stavke=None, napomena=None, potvrdi_opt=None):
    """Obračun → nova verzija ponude (snimka stavki). Prethodne verzije u nacrtu / poslane postaju `zamijenjena`; potvrđena se ne dira.
    stavke: gotov popis (npr. iz korekcije po stvarnom stanju) umjesto obračuna.
    D-75: svaki materijal koji se slaže na ploču mora imati POTVRĐENO slaganje; potvrdi_opt=True (probe, CLI --potvrdi-opt) sam potvrdi Hubov prijedlog."""
    n = N.nalog(conn, nalog_id)
    if n["status"] not in ("unos", "ponuda") and status != "izdatnica":
        raise PonudaGreska("nova verzija ponude samo u statusu unos / ponuda (nalog je u '%s')" % n["status"])
    if n["status"] == "unos" and N.broj_za_potvrdu(conn, nalog_id):
        raise PonudaGreska("nalog ima stavke za potvrdu — prvo potvrditi materijale i trake")
    if stavke is None:
        auto = OP.AUTO_POTVRDA if potvrdi_opt is None else potvrdi_opt
        if auto:
            for nm in conn.execute("SELECT id FROM nalog_materijal WHERE nalog_id = ? ORDER BY rb, id", (nalog_id,)).fetchall():
                if OP.treba_optimizaciju(conn, nm["id"]) and conn.execute("SELECT 1 FROM element WHERE nalog_materijal_id = ? LIMIT 1", (nm["id"],)).fetchone():
                    OP.osiguraj_potvrdu(conn, nm["id"], tko, auto=True)
        nep = OP.nepotvrdjeni(conn, nalog_id)
        if nep:
            raise PonudaGreska("optimizacija nije potvrđena za: %s — ponuda i pila koriste istu optimizaciju (D-75), prvo je potvrditi" % ", ".join(nep))
    r = dict(stavke=stavke, upozorenja=[]) if stavke is not None else OC.izracunaj(conn, nalog_id, pravila)
    if not r["stavke"]:
        raise PonudaGreska("obračun nema nijednu stavku")
    neto = round(sum(s["iznos"] for s in r["stavke"]), 2)
    try:
        conn.execute("UPDATE ponuda_verzija SET status = 'zamijenjena' WHERE nalog_id = ? AND status IN ('nacrt', 'poslana')", (nalog_id,))
        br = (conn.execute("SELECT COALESCE(MAX(verzija), 0) FROM ponuda_verzija WHERE nalog_id = ?", (nalog_id,)).fetchone()[0] or 0) + 1
        cur = conn.execute("INSERT INTO ponuda_verzija (nalog_id, verzija, status, iznos_neto, iznos_pdv, mail_tekst) VALUES (?, ?, ?, ?, ?, ?)",
                           (nalog_id, br, status, neto, round(neto * OC.PDV, 2), napomena))
        vid = cur.lastrowid
        for s in r["stavke"]:
            conn.execute("INSERT INTO obracun_stavka (nalog_id, ponuda_verzija_id, rb, pantheon_ident, naziv, kolicina, jm, cijena, rabat, grupa, pravilo, nalog_materijal_id) "
                         "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (nalog_id, vid, s["rb"], s["pantheon_ident"], s["naziv"], s["kolicina"], s["jm"], s["cijena"], s["rabat"],
                                                              s["grupa"], s["pravilo"], s.get("nalog_materijal_id")))
        dnevnik(conn, tko, "nalog", nalog_id, "ponuda_verzija", "v%d (%s): %d stavki, neto %.2f EUR" % (br, status, len(r["stavke"]), neto))
        conn.execute("INSERT INTO dogadjaj (nalog_id, kada, tko_id, iz_statusa, u_status, razlog) VALUES (?, ?, ?, ?, ?, ?)",
                     (nalog_id, sada(), N.korisnik_id(conn, tko), n["status"], n["status"], "ponuda v%d %s: %d stavki, neto %.2f EUR" % (br, status, len(r["stavke"]), neto)))
        if n["status"] == "unos" and status == "nacrt":
            conn.execute("UPDATE nalog SET status = 'ponuda' WHERE id = ?", (nalog_id,))
            conn.execute("INSERT INTO dogadjaj (nalog_id, kada, tko_id, iz_statusa, u_status, razlog) VALUES (?, ?, ?, 'unos', 'ponuda', ?)",
                         (nalog_id, sada(), N.korisnik_id(conn, tko), "ponuda v%d napravljena" % br))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    d = verzija(conn, vid)
    d["upozorenja"] = r["upozorenja"]
    return d


def _podjetje(vrsta, naziv, ulica=None, kraj="", posta="", vat=""):
    u = "<Ulica><Ulica1>%s</Ulica1></Ulica>" % escape(ulica) if ulica else ""
    return ("<PodatkiPodjetja><NazivNaslovPodjetja><VrstaPartnerja>%s</VrstaPartnerja><NazivPartnerja><NazivPartnerja1>%s</NazivPartnerja1></NazivPartnerja>"
            "%s<Kraj>%s</Kraj><NazivDrzave>Hrvatska</NazivDrzave><PostnaStevilka>%s</PostnaStevilka><KodaDrzave>HR</KodaDrzave></NazivNaslovPodjetja>"
            "<ReferencniPodatkiPodjetja><VrstaPodatkaPodjetja>VA</VrstaPodatkaPodjetja><PodatekPodjetja>%s</PodatekPodjetja></ReferencniPodatkiPodjetja>"
            "<ReferencniPodatkiPodjetja><VrstaPodatkaPodjetja>GN</VrstaPodatkaPodjetja><PodatekPodjetja></PodatekPodjetja></ReferencniPodatkiPodjetja></PodatkiPodjetja>"
            % (vrsta, escape(naziv or ""), u, escape(kraj or ""), escape(posta or ""), escape(vat or "")))


def _postavka(i, s):
    em = MJ.get((s["jm"] or "KOM").strip().upper(), "H87")
    cij = float(s["cijena"] or 0)
    rab = float(s["rabat"] or 0)
    iznos_rab = round(float(s["kolicina"]) * cij * rab / 100, 6)
    return ("<PostavkeDokumenta><Postavka><StevilkaVrstice>%d</StevilkaVrstice></Postavka>"
            "<DodatnaIdentifikacijaArtikla><VrstaPodatkaArtikla>5</VrstaPodatkaArtikla><StevilkaArtiklaDodatna>%s</StevilkaArtiklaDodatna>"
            "<VrstaKodeArtiklaDodatna>SA</VrstaKodeArtiklaDodatna></DodatnaIdentifikacijaArtikla>"
            "<OpisiArtiklov><KodaOpisaArtikla>F</KodaOpisaArtikla><OpisArtikla><VrstaArtikla>CU</VrstaArtikla><OpisArtikla1>%s</OpisArtikla1><OpisArtikla2></OpisArtikla2></OpisArtikla></OpisiArtiklov>"
            "<KolicinaArtikla><VrstaKolicine>21</VrstaKolicine><Kolicina>%.6f</Kolicina><EnotaMere>%s</EnotaMere></KolicinaArtikla>"
            "<CenaPostavke><VrstaCene>AAA</VrstaCene><Cena>%.6f</Cena></CenaPostavke><CenaPostavke><VrstaCene>AAB</VrstaCene><Cena>%.6f</Cena></CenaPostavke>"
            "<OdstotkiPostavk><Identifikator>A</Identifikator><VrstaOdstotkaPostavke>3</VrstaOdstotkaPostavke><OdstotekPostavke>%.6f</OdstotekPostavke>"
            "<VrstaZneskaOdstotka>204</VrstaZneskaOdstotka><ZnesekOdstotka>%.6f</ZnesekOdstotka></OdstotkiPostavk></PostavkeDokumenta>"
            % (i, escape(s["pantheon_ident"]), escape((s["naziv"] or s["pantheon_ident"])[:70]), float(s["kolicina"]), em, cij, cij, rab, iznos_rab))


def eslog_xml(conn, verzija_id, broj=None, datum=None, napomena=None):
    """eSlog 1.1 EnostavnoNarocilo (220) za uvoz ponude u Pantheon. Kupac = Pantheon subjekt za račun (D-48: Krajnji kupac ili vlastiti);
    ime osobe krajnjeg kupca ide u napomenu (PUR)."""
    v = verzija(conn, verzija_id)
    n = N.nalog(conn, v["nalog_id"])
    k = n.get("kupac") or {}
    subjekt = k.get("pantheon_subjekt_racun") or k.get("naziv") or "Krajnji kupac"
    broj = broj or n["ponuda_pantheon"] or ("HUB-%s-v%d" % (n["broj"], v["verzija"]))
    datum = datum or sada()[:10]
    nap = napomena or v.get("mail_tekst") or ("Nalog %s%s" % (n["naziv"], (" — %s" % k["naziv"]) if k.get("naziv") and k.get("naziv") != subjekt else ""))
    x = ['<?xml version="1.0" encoding="UTF-8" ?>',
         '<NarociloEnostavno xmlns:b="urn:schemas-microsoft-com:BizTalkServer" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
         'xsi:noNamespaceSchemaLocation="http://www.gzs.si/e-poslovanje/sheme/\\eSLOG_1-1_EnostavnoNarocilo.xsd">', "<Dokument>",
         "<GlavaDokumenta><VrstaDokumenta>220</VrstaDokumenta><StevilkaDokumenta>%s</StevilkaDokumenta><FunkcijaDokumenta>9</FunkcijaDokumenta></GlavaDokumenta>" % escape(broj),
         "<DatumiDokumenta><VrstaDatuma>137</VrstaDatuma><DatumDokumenta>%sT00:00:00</DatumDokumenta></DatumiDokumenta>" % datum,
         "<PoljubnoBesedilo><VrstaBesedila>PUR</VrstaBesedila><Besedilo> <Tekst1>%s</Tekst1><Tekst2></Tekst2><Tekst3></Tekst3><Tekst4></Tekst4><Tekst5></Tekst5></Besedilo></PoljubnoBesedilo>" % escape(nap[:70]),
         _podjetje("BY", NASA["naziv"], NASA["ulica"], NASA["kraj"], NASA["posta"], NASA["vat"]),
         _podjetje("DP", NASA["naziv"], NASA["ulica"], NASA["kraj"], NASA["posta"], NASA["vat"]),
         _podjetje("SU", subjekt, k.get("adresa"), k.get("mjesto") or "", k.get("posta") or "", k.get("oib") or ""),
         _podjetje("OB", NASA["naziv"], NASA["ulica"], NASA["kraj"], NASA["posta"], NASA["vat"])]
    for i, s in enumerate(v["stavke"], 1):
        x.append(_postavka(i, s))
    x.append("<KontrolnaSekcija><VrstaKontrole>2</VrstaKontrole><VrednostKontrole>%d</VrednostKontrole></KontrolnaSekcija>" % len(v["stavke"]))
    x.append("</Dokument></NarociloEnostavno>")
    return "".join(x), broj


def napisi_eslog(conn, verzija_id, mapa=None, tko="web", broj=None):
    """Napiši XML u mapu (postavka `mapa_eslog_ponude` ili zadana uz bazu) i zabilježi u verziju + dokument naloga."""
    v = verzija(conn, verzija_id)
    xml, broj = eslog_xml(conn, verzija_id, broj)
    mapa = mapa or postavka(conn, "mapa_eslog_ponude") or os.path.join(os.path.dirname(os.path.abspath(db.putanja_baze())), "eslog_uvoz_ponude")
    os.makedirs(mapa, exist_ok=True)
    put = os.path.join(mapa, "eSlog_220_%s.xml" % broj.replace("/", "-"))
    open(put, "w", encoding="utf-8").write(xml)
    conn.execute("UPDATE ponuda_verzija SET eslog_putanja = ? WHERE id = ?", (put, verzija_id))
    conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, datum) VALUES (?, 'eslog', ?, ?)", (v["nalog_id"], put, sada()))
    dnevnik(conn, tko, "nalog", v["nalog_id"], "eslog", "v%d → %s" % (v["verzija"], os.path.basename(put)))
    conn.commit()
    return put


def oznaci_poslanu(conn, verzija_id, tko="web", na=None, mail_tekst=None):
    """Ponuda poslana kupcu (za sada ručno / vlastitim mailom — D-41 čeka pružatelja)."""
    v = verzija(conn, verzija_id)
    if v["status"] not in ("nacrt", "poslana"):
        raise PonudaGreska("verzija v%d je '%s' — ne može se slati" % (v["verzija"], v["status"]))
    n = N.nalog(conn, v["nalog_id"])
    na = na or n.get("kupac_email")
    conn.execute("UPDATE ponuda_verzija SET status = 'poslana', poslano_kada = ?, poslao_id = ?, poslano_na = ?, mail_tekst = COALESCE(?, mail_tekst) WHERE id = ?",
                 (sada(), N.korisnik_id(conn, tko), na, mail_tekst, verzija_id))
    conn.execute("INSERT INTO dogadjaj (nalog_id, kada, tko_id, iz_statusa, u_status, razlog) VALUES (?, ?, ?, ?, ?, ?)",
                 (v["nalog_id"], sada(), N.korisnik_id(conn, tko), n["status"], n["status"], "ponuda v%d poslana%s" % (v["verzija"], (" na " + na) if na else "")))
    conn.commit()
    if not na:
        return dict(verzija(conn, verzija_id), upozorenje="kupac nema e-mail u Hubu (D-50) — upisati na kartici kupca")
    return verzija(conn, verzija_id)


def posalji(conn, verzija_id, tko="web", na=None, tekst=None, cc=None, mapa=None, suho=False):
    """Ponuda kupcu mailom (D-41): PDF (ili HTML) u prilogu + HTML tijelo; verzija → poslana s adresom i tekstom. Bez SMTP lozinke → MailGreska,
    ured može poslati ručno i označiti s `oznaci_poslanu`."""
    from . import mail as M, ponuda_pdf as PP
    v = verzija(conn, verzija_id)
    if v["status"] not in ("nacrt", "poslana"):
        raise PonudaGreska("verzija v%d je '%s' — ne može se slati" % (v["verzija"], v["status"]))
    n = N.nalog(conn, v["nalog_id"])
    na = na or n.get("kupac_email")
    if not na:
        raise PonudaGreska("kupac %s nema e-mail u Hubu — upisati na kartici kupca (D-50)" % (n.get("kupac_naziv") or "?"))
    mapa = mapa or postavka(conn, "mapa_ponude") or os.path.join(os.path.dirname(os.path.abspath(db.putanja_baze())), "ponude")
    dok = PP.napravi(conn, verzija_id, mapa, tko=tko)
    from .. import korisnici as KO
    tekst = tekst or ("Poštovani,\n\nu prilogu je ponuda %s (nalog %s), ukupno %.2f EUR s PDV-om.\n\nMolimo potvrdu odgovorom na ovaj mail ili telefonom.\n\nLijep pozdrav,\n%s"
                      % (dok["naslov"], n["naziv"], dok["ukupno"], KO.potpis(conn, tko)))      # D-88: potpis osobe koja šalje
    r = M.posalji(conn, na, "%s — %s" % (dok["naslov"], PP.TVRTKA["naziv"]), tekst, html=PP.html(conn, verzija_id),
                  prilozi=[dok["pdf"] or dok["html"]], cc=cc, tko=tko, nalog_id=v["nalog_id"], suho=suho)
    conn.execute("UPDATE ponuda_verzija SET pdf_putanja = ? WHERE id = ?", (dok["pdf"] or dok["html"], verzija_id))
    conn.execute("INSERT INTO dokument (nalog_id, vrsta, putanja, datum) VALUES (?, 'ponuda_pdf', ?, ?)", (v["nalog_id"], dok["pdf"] or dok["html"], sada()))
    conn.commit()
    if suho:
        return dict(verzija(conn, verzija_id), mail=r, dokument=dok)
    d = oznaci_poslanu(conn, verzija_id, tko, na, tekst)
    d["mail"] = r
    d["dokument"] = dok
    return d


def potvrdi(conn, verzija_id, tko="web", ponuda_pantheon=None, mapa_eslog=None, **potvrda):
    """Kupac potvrdio (dijalog 3b): verzija → potvrđena, nalog → potvrdjeno (D-35, s datumom / načinom / rokom), eSlog XML za Pantheon,
    Pantheon broj ponude u nalog (D-40) — ako još nije poznat, XML nosi Hubov broj, a ured broj upiše nakon uvoza."""
    v = verzija(conn, verzija_id)
    if v["status"] not in ("nacrt", "poslana"):
        raise PonudaGreska("verzija v%d je '%s' — ne može se potvrditi" % (v["verzija"], v["status"]))
    n = N.nalog(conn, v["nalog_id"])
    if n["status"] == "unos":
        N.postavi_status(conn, v["nalog_id"], "ponuda", tko, razlog="ponuda v%d" % v["verzija"])
    N.postavi_status(conn, v["nalog_id"], "potvrdjeno", tko, razlog="kupac potvrdio ponudu v%d" % v["verzija"], **potvrda)
    conn.execute("UPDATE ponuda_verzija SET status = 'potvrdjena' WHERE id = ?", (verzija_id,))
    conn.execute("UPDATE ponuda_verzija SET status = 'zamijenjena' WHERE nalog_id = ? AND id != ? AND status IN ('nacrt', 'poslana')", (v["nalog_id"], verzija_id))
    if ponuda_pantheon:
        conn.execute("UPDATE nalog SET ponuda_pantheon = ? WHERE id = ?", (ponuda_pantheon, v["nalog_id"]))
    conn.commit()
    put = napisi_eslog(conn, verzija_id, mapa_eslog, tko, ponuda_pantheon)
    return dict(verzija(conn, verzija_id), eslog=put, nalog=N.nalog(conn, v["nalog_id"]))


def upisi_pantheon_broj(conn, nalog_id, broj, tko="web"):
    conn.execute("UPDATE nalog SET ponuda_pantheon = ? WHERE id = ?", (broj, nalog_id))
    dnevnik(conn, tko, "nalog", nalog_id, "ponuda_pantheon", broj)
    conn.commit()


def korekcija_po_stvarnom(conn, nalog_id, tko="web", mapa_eslog=None, upisi=True):
    """D-56 (vlastita proizvodnja): ploče iz bNest rezultata (.mno) umjesto PW-metode → stavke izdatnice. Materijal bez bNest rezultata
    ostaje po obračunu (i to se javi). Vraća verziju `izdatnica` (ili samo stavke ako upisi=False)."""
    n = N.nalog(conn, nalog_id)
    if n["vrsta"] != "vlastita_proizvodnja":
        raise PonudaGreska("korekcija po stvarnom stanju je samo za vlastitu proizvodnju (D-56); nalog je '%s'" % n["vrsta"])
    r = OC.izracunaj(conn, nalog_id)
    upoz = list(r["upozorenja"])
    stavke = []
    for s in r["stavke"]:
        s = dict(s)
        if s["grupa"] in ("materijal", "rezanje") and s["nalog_materijal_id"]:
            b = conn.execute("SELECT broj_ploca, m2_ploca, m2_dijelova, iskoristenje FROM optimizacija WHERE nalog_materijal_id = ? AND engine = 'bNest' "
                             "ORDER BY id DESC LIMIT 1", (s["nalog_materijal_id"],)).fetchone()
            if b and b["m2_ploca"] and s["jm"] == "M2":
                s["kolicina"] = round(float(b["m2_ploca"]), 2)
                s["pravilo"] = "stvarno potrošeno (bNest .mno): %s ploča, %.2f m²" % (b["broj_ploca"], b["m2_ploca"])
                s["iznos"] = round(s["kolicina"] * (s["cijena"] or 0) * (1 - (s["rabat"] or 0) / 100), 2)
            elif s["grupa"] == "materijal":
                upoz.append("%s: nema bNest rezultata — ostaje obračun PW-metodom" % s["naziv"])
        stavke.append(s)
    if not upisi:
        return dict(stavke=stavke, upozorenja=upoz, neto=round(sum(s["iznos"] for s in stavke), 2))
    d = nova_verzija(conn, nalog_id, tko, status="izdatnica", stavke=stavke, napomena="Interna izdatnica po stvarnom stanju — nalog %s" % n["naziv"])
    d["upozorenja"] = upoz
    if n["status"] == "proizvodnja":
        N.postavi_status(conn, nalog_id, "izdatnica", tko, razlog="korekcija po stvarnom stanju (izdatnica v%d)" % d["verzija"])
    d["eslog"] = napisi_eslog(conn, d["id"], mapa_eslog, tko, "IZD-%s" % n["broj"])
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description="Ponuda iz Huba (korak 4): verzija, eSlog, potvrda, izdatnica")
    ap.add_argument("--db")
    ap.add_argument("--nalog", type=int, required=True)
    ap.add_argument("--nova", action="store_true", help="nova verzija ponude iz obračuna")
    ap.add_argument("--potvrdi-opt", action="store_true", help="uz --nova: sam potvrdi Hubov prijedlog slaganja za nepotvrđene materijale (probe, D-75)")
    ap.add_argument("--eslog", type=int, metavar="VERZIJA_ID", help="napiši eSlog XML za verziju")
    ap.add_argument("--potvrdi", type=int, metavar="VERZIJA_ID", help="kupac potvrdio verziju → nalog potvrđen + eSlog")
    ap.add_argument("--pantheon", help="Pantheon broj ponude (uz --potvrdi)")
    ap.add_argument("--posalji", type=int, metavar="VERZIJA_ID", help="pošalji verziju kupcu mailom (PDF u prilogu), D-41")
    ap.add_argument("--na", help="adresa primatelja (zadano e-mail kupca iz Huba)")
    ap.add_argument("--izdatnica", action="store_true", help="vlastita proizvodnja: korekcija po stvarnom stanju (.mno) → izdatnica")
    ap.add_argument("--mapa", help="mapa za eSlog XML")
    ap.add_argument("--tko", default="web")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    try:
        if a.nova:
            v = nova_verzija(conn, a.nalog, a.tko, potvrdi_opt=True if a.potvrdi_opt else None)
            print("ponuda v%d (%s): %d stavki, neto %.2f, PDV %.2f" % (v["verzija"], v["status"], len(v["stavke"]), v["iznos_neto"], v["iznos_pdv"]))
            for u in v["upozorenja"]:
                print("   PAZI:", u)
        if a.eslog:
            print("eSlog:", napisi_eslog(conn, a.eslog, a.mapa, a.tko))
        if a.potvrdi:
            r = potvrdi(conn, a.potvrdi, a.tko, a.pantheon, a.mapa)
            print("potvrđeno: nalog %s → %s, eSlog %s" % (r["nalog"]["naziv"], r["nalog"]["status"], r["eslog"]))
        if a.posalji:
            r = posalji(conn, a.posalji, a.tko, a.na, mapa=a.mapa)
            print("poslano na %s: %s (%s)" % (r["mail"]["na"], r["mail"]["predmet"], ", ".join(r["mail"]["prilozi"])))
        if a.izdatnica:
            r = korekcija_po_stvarnom(conn, a.nalog, a.tko, a.mapa)
            print("izdatnica v%d: %d stavki, neto %.2f, eSlog %s" % (r["verzija"], len(r["stavke"]), r["iznos_neto"], r["eslog"]))
            for u in r["upozorenja"]:
                print("   PAZI:", u)
        for v in verzije(conn, a.nalog):
            print("   v%d %-11s %3d stavki  neto %9.2f  %s" % (v["verzija"], v["status"], v["stavki"], v["iznos_neto"] or 0, v["eslog_putanja"] or ""))
    except (PonudaGreska, N.NalogGreska, OC.ObracunGreska) as e:
        print("GRESKA:", e)
        return 1
    except RuntimeError as e:                                       # MailGreska
        print("GRESKA:", e)
        return 1
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
