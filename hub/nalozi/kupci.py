# -*- coding: utf-8 -*-
"""Šifrarnik kupaca iz Pantheona (D-12): ph_subjekti.csv = tHE_SetSubj (IzvozPantheon_v2.ps1), ph_poste.csv = pošte (naziv mjesta).

Uvoz uzima subjekte s acBuyer = T i acActive = T (3 612 od 4 750 subjekata, 9. 9. 2026.). Iz Pantheona: naziv (acSubject = ključ),
puni naziv (acName2), adresa, pošta (acPost 'HR-31000') + mjesto iz ph_poste, država, OIB (acPIN), fizička osoba.
U Pantheonu NISU održavani (ostaju Hubu): rabat po kupcu (D-40, anRebate je 0 kod 3 605 od 3 612), dani plaćanja (anDaysForPayment 0),
e-mail (kontakti su u tHE_SetSubjContact — nije u izvozu; do proširenja izvoza ured upisuje u Hub). Uvoz nikad ne prepisuje ta polja.

Krajnji kupci (D-48): fizičke osobe Hub vodi SAM (ime, mjesto, telefon, e-mail), a u Pantheon njihove ponude / računi idu na zajednički subjekt
'Krajnji kupac' (postavka `krajnji_kupac_subjekt`). Pri uvozu: subjekt s OIB-om ili pravnim oblikom u nazivu → tvrtka / obrt (vlastiti subjekt),
bez pravnog oblika → krajnji (fizička osoba): s OIB-om zadržava svoj subjekt, bez OIB-a subjekt za račun = Krajnji kupac; vrsta i subjekt za račun se pri ponovnom uvozu ne prepisuju
(ured ih može promijeniti). Novi krajnji kupac otvara se u Hubu (`novi_hub_kupac`) uz provjeru duplikata po telefonu / e-mailu / imenu.
"""
import csv
import io
import os

from ..db import sada, dnevnik
from ..sifrarnici.nazivi import norm


def _ucitaj(putanja):
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


def ucitaj_poste(putanja):
    """{'HR-31000': 'OSIJEK'} iz ph_poste.csv (acPost, acName)."""
    if not putanja or not os.path.exists(putanja):
        return {}
    return {r["acPost"].strip(): r["acName"].strip() for r in _ucitaj(putanja) if r.get("acPost") and r.get("acName")}


def _cist(x):
    return (x or "").strip() or None


_PRAVNI = None


def vrsta_iz_naziva(naziv, oib=None):
    """tvrtka | obrt | krajnji po nazivu: pravni oblik → tvrtka (obrt ako 'vl.' / 'obrt' / 'OPG'), inače fizička osoba (krajnji).
    OIB ne mijenja vrstu, ali odlučuje kamo ide račun: krajnji S OIB-om zadržava svoj Pantheon subjekt, BEZ OIB-a ide na 'Krajnji kupac' (D-48)."""
    import re
    global _PRAVNI
    if _PRAVNI is None:
        _PRAVNI = re.compile(r"(?<![A-Z0-9])(D\.?O\.?O\.?|D\.O\.|J\.?D\.?O\.?O\.?|JDOO|DOO|OBRT|OPG|D\.?D\.?|J\.?T\.?D\.?|VL\.?|UDRUGA|USTANOVA|SKOLA|VRTIC|OPCINA|GRAD|ZUPANIJA|ZADRUGA|"
                             r"BOLNICA|CENTAR|KLUB|ZUPA|CRKVA|AGENCIJA|B\.?V\.?|GMBH|S\.?R\.?O\.?|LTD|LLC|SP\.? Z|KFT|AG)(?![A-Z0-9])")
    n = norm(naziv)
    if re.search(r"\b(OBRT|OPG|VL\.?)\b", n):
        return "obrt"
    if _PRAVNI.search(n):
        return "tvrtka"
    return "krajnji"


def _smece(naziv):
    """Pantheon ima probne subjekte ('prazno', '00002', 'fi', 'ha') — u Hubu neaktivni."""
    n = norm(naziv)
    return len(n.replace(" ", "")) < 3 or n.replace(" ", "").isdigit() or n.startswith("PRAZNO")


def _telefon_norm(t):
    """Samo znamenke, hrvatski predbroj sveden na 0: '+385 98 111 222' = '098111222' = '00385981112 22'."""
    import re
    d = re.sub(r"\D", "", t or "")
    if d.startswith("00385"):
        d = "0" + d[5:]
    elif d.startswith("385") and len(d) >= 11:
        d = "0" + d[3:]
    return d or None


def uvezi_kupce(conn, putanja, poste=None, tko="uvoz", samo_kupci=True):
    """Upiše / osvježi kupce iz ph_subjekti.csv; vraća statistiku. Idempotentno: Hub-polja (rabat, e-mail, dani plaćanja, vrsta, subjekt za račun) se ne diraju."""
    from ..db import postavka
    poste = ucitaj_poste(poste) if isinstance(poste, str) else (poste or {})
    kada = sada()
    zajednicki = postavka(conn, "krajnji_kupac_subjekt", "Krajnji kupac")
    st = dict(redova=0, kupaca=0, novih=0, neaktivnih=0, tvrtka=0, obrt=0, krajnji=0, zajednicki=0)
    cur = conn.cursor()
    for r in _ucitaj(putanja):
        st["redova"] += 1
        subjekt = _cist(r.get("acSubject"))
        if not subjekt:
            continue
        if samo_kupci and (r.get("acBuyer") or "F") != "T":
            continue
        aktivan = 1 if (r.get("acActive") or "T") == "T" else 0
        if _smece(subjekt):
            aktivan = 0
        if not aktivan:
            st["neaktivnih"] += 1
        posta = _cist(r.get("acPost"))
        oib = _cist(r.get("acPIN"))
        if norm(subjekt) == norm(zajednicki):
            vrsta = "zajednicki"
        else:
            vrsta = vrsta_iz_naziva(subjekt, oib)
        st[vrsta] += 1
        racun = zajednicki if (vrsta == "krajnji" and not oib) else subjekt
        vals = dict(naziv=subjekt, naziv_puni=_cist(r.get("acName2")), adresa=_cist(r.get("acAddress")), posta=posta,
                    mjesto=poste.get(posta or "", None), drzava=_cist(r.get("acCountry")), oib=oib,
                    fizicka_osoba=1 if (r.get("acNaturalPerson") or "F") == "T" or vrsta == "krajnji" else 0, aktivan=aktivan, pantheon_azurirano=kada)
        vals["trazi"] = norm(" ".join(x for x in (vals["naziv"], vals["naziv_puni"], vals["adresa"], vals["posta"], vals["mjesto"], vals["oib"]) if x))
        dani = _cist(r.get("anDaysForPayment"))
        dani = int(float(dani)) if dani and float(dani) > 0 else None
        postoji = cur.execute("SELECT id FROM kupac WHERE pantheon_subjekt = ?", (subjekt,)).fetchone()
        if postoji:
            cur.execute("UPDATE kupac SET naziv = :naziv, naziv_puni = :naziv_puni, adresa = :adresa, posta = :posta, mjesto = :mjesto, drzava = :drzava, "
                        "oib = :oib, fizicka_osoba = :fizicka_osoba, aktivan = :aktivan, pantheon_azurirano = :pantheon_azurirano, trazi = :trazi, "
                        "dani_placanja = COALESCE(dani_placanja, :dani), vrsta = COALESCE(vrsta, :vrsta), "
                        "pantheon_subjekt_racun = COALESCE(pantheon_subjekt_racun, :racun) WHERE id = :id", dict(vals, dani=dani, vrsta=vrsta, racun=racun, id=postoji[0]))
        else:
            cur.execute("INSERT INTO kupac (pantheon_subjekt, izvor, vrsta, pantheon_subjekt_racun, naziv, naziv_puni, adresa, posta, mjesto, drzava, oib, fizicka_osoba, "
                        "aktivan, pantheon_azurirano, trazi, dani_placanja) VALUES (:subjekt, 'pantheon', :vrsta, :racun, :naziv, :naziv_puni, :adresa, :posta, :mjesto, "
                        ":drzava, :oib, :fizicka_osoba, :aktivan, :pantheon_azurirano, :trazi, :dani)", dict(vals, subjekt=subjekt, vrsta=vrsta, racun=racun, dani=dani))
            st["novih"] += 1
        st["kupaca"] += 1
    dnevnik(conn, tko, "kupac", None, "uvoz", "%s: %d redova, %d kupaca (%d novih, %d neaktivnih; tvrtki %d, obrta %d, krajnjih %d)"
            % (os.path.basename(putanja), st["redova"], st["kupaca"], st["novih"], st["neaktivnih"], st["tvrtka"], st["obrt"], st["krajnji"]))
    conn.commit()
    return st


def slicni_kupci(conn, ime=None, telefon=None, email=None, limit=5):
    """Ponavljači (D-48): isti telefon ili e-mail = sigurno isti kupac; isto ime (bez dijakritike) = vjerojatno. Vraća [(kupac, razlog)]."""
    out, vidjeno = [], set()
    tel = _telefon_norm(telefon)
    if tel:
        for r in conn.execute("SELECT * FROM kupac WHERE aktivan = 1 AND telefon IS NOT NULL"):
            if _telefon_norm(r["telefon"]) == tel and r["id"] not in vidjeno:
                out.append((dict(r), "isti telefon")); vidjeno.add(r["id"])
    if email and email.strip():
        for r in conn.execute("SELECT * FROM kupac WHERE aktivan = 1 AND LOWER(email) = ?", (email.strip().lower(),)):
            if r["id"] not in vidjeno:
                out.append((dict(r), "isti e-mail")); vidjeno.add(r["id"])
    if ime and ime.strip():
        n = norm(ime)
        obrnuto = " ".join(reversed(n.split()))
        for r in conn.execute("SELECT * FROM kupac WHERE aktivan = 1 AND vrsta != 'zajednicki'"):
            nn = norm(r["naziv"])
            if (nn == n or nn == obrnuto) and r["id"] not in vidjeno:
                out.append((dict(r), "isto ime")); vidjeno.add(r["id"])
    return out[:limit]


def novi_hub_kupac(conn, tko, ime, mjesto=None, telefon=None, email=None, adresa=None, posta=None, napomena=None, vrsta="krajnji",
                   rabat_materijal=None, rabat_usluge=None, oib=None):
    """Kupac otvoren u Hubu (fizička osoba koja nema svoj subjekt u Pantheonu): ponuda / račun idu na 'Krajnji kupac' (D-48).
    Duplikate provjeri prije poziva sa slicni_kupci()."""
    from ..db import postavka
    ime = (ime or "").strip()
    if len(ime) < 3:
        raise ValueError("ime kupca je prekratko")
    if vrsta not in ("krajnji", "tvrtka", "obrt"):
        raise ValueError("vrsta mora biti krajnji, tvrtka ili obrt")
    racun = postavka(conn, "krajnji_kupac_subjekt", "Krajnji kupac") if vrsta == "krajnji" else None
    if rabat_materijal is None and vrsta == "krajnji":
        rabat_materijal = float(postavka(conn, "rabat_krajnji_materijal", "0") or 0)
    if rabat_usluge is None and vrsta == "krajnji":
        rabat_usluge = float(postavka(conn, "rabat_krajnji_usluge", "0") or 0)
    trazi = norm(" ".join(x for x in (ime, adresa, posta, mjesto, oib, _telefon_norm(telefon), email) if x))
    cur = conn.execute("INSERT INTO kupac (pantheon_subjekt, izvor, vrsta, pantheon_subjekt_racun, naziv, adresa, posta, mjesto, drzava, oib, fizicka_osoba, email, telefon, "
                       "rabat_materijal, rabat_usluge, napomena, aktivan, trazi) VALUES (NULL, 'hub', ?, ?, ?, ?, ?, ?, 'Hrvatska', ?, ?, ?, ?, ?, ?, ?, 1, ?)",
                       (vrsta, racun, ime, _cist(adresa), _cist(posta), _cist(mjesto), _cist(oib), 1 if vrsta == "krajnji" else 0, _cist(email), _cist(telefon),
                        rabat_materijal, rabat_usluge, _cist(napomena), trazi))
    dnevnik(conn, tko, "kupac", cur.lastrowid, "novi", "%s (%s)" % (ime, vrsta))
    conn.commit()
    return kupac(conn, cur.lastrowid)


def trazi_kupce(conn, q="", aktivni=True, limit=30, subjekt=None, vrsta=None):
    """Pretraga: svaka riječ upita u nazivu, punom nazivu, mjestu, OIB-u, telefonu; točan naziv prvi.
    subjekt = ključ za Pantheon (npr. 'Krajnji kupac' → interna baza fizičkih osoba pod tim ključem, D-48); vrsta = tvrtka | obrt | krajnji."""
    n = norm(q)
    uvjeti, par = [], []
    if subjekt:
        uvjeti.append("pantheon_subjekt_racun = ?")
        par.append(subjekt)
    if vrsta:
        uvjeti.append("vrsta = ?")
        par.append(vrsta)
    for w in n.split():
        w2 = w.replace("DJ", "D")                            # 'Djakovo' = Đakovo (norm: DAKOVO)
        uvjeti.append("(trazi LIKE ? OR trazi LIKE ?)")      # trazi = normalizirani naziv + puni naziv + adresa + pošta + mjesto + OIB + telefon + e-mail
        par += ["%" + w + "%", "%" + w2 + "%"]
    if aktivni:
        uvjeti.append("aktivan = 1")
    uvjeti.append("(vrsta IS NULL OR vrsta != 'zajednicki')")        # subjekt 'Krajnji kupac' nije kupac za biranje
    sql = ("SELECT id, pantheon_subjekt, izvor, vrsta, pantheon_subjekt_racun, naziv, naziv_puni, adresa, posta, mjesto, drzava, oib, fizicka_osoba, email, telefon, rabat_materijal, "
           "rabat_usluge, dani_placanja, aktivan FROM kupac " + ("WHERE " + " AND ".join(uvjeti) if uvjeti else "")
           + " ORDER BY (trazi LIKE ?) DESC, naziv LIMIT ?")
    return [dict(r) for r in conn.execute(sql, par + [n + " %", limit])]


def kupac(conn, kupac_id):
    r = conn.execute("SELECT * FROM kupac WHERE id = ?", (kupac_id,)).fetchone()
    return dict(r) if r else None


def subjekti_za_pantheon(conn):
    """Ključevi po kojima se biraju kupci na ekranu: zajednički 'Krajnji kupac' (s brojem osoba pod njim) + vlastiti subjekti (tvrtke, obrti, osobe s OIB-om)."""
    from ..db import postavka
    zaj = postavka(conn, "krajnji_kupac_subjekt", "Krajnji kupac")
    n = conn.execute("SELECT COUNT(*) FROM kupac WHERE aktivan = 1 AND pantheon_subjekt_racun = ? AND vrsta != 'zajednicki'", (zaj,)).fetchone()[0]
    return dict(krajnji_kupac=dict(subjekt=zaj, osoba=n), vlastitih=conn.execute(
        "SELECT COUNT(*) FROM kupac WHERE aktivan = 1 AND pantheon_subjekt_racun != ? AND vrsta != 'zajednicki'", (zaj,)).fetchone()[0])


def uredi_kupca(conn, kupac_id, tko, **polja):
    """Hub-polja kupca: email, telefon, rabat_materijal, rabat_usluge, dani_placanja, napomena, vrsta, pantheon_subjekt_racun (prijelaz krajnji ↔ vlastiti
    subjekt, D-48); za kupce otvorene u Hubu i naziv / adresa / mjesto / OIB (ostalo dolazi iz Pantheona)."""
    k = kupac(conn, kupac_id)
    if not k:
        return None
    dopusteno = {"email", "telefon", "rabat_materijal", "rabat_usluge", "dani_placanja", "napomena", "vrsta", "pantheon_subjekt_racun", "aktivan"}
    if k["izvor"] == "hub":
        dopusteno |= {"naziv", "adresa", "posta", "mjesto", "oib"}
    p = {kk: v for kk, v in polja.items() if kk in dopusteno}
    if "vrsta" in p and p["vrsta"] not in ("krajnji", "tvrtka", "obrt"):
        raise ValueError("vrsta mora biti krajnji, tvrtka ili obrt")
    if p.get("vrsta") == "krajnji" and "pantheon_subjekt_racun" not in p:
        from ..db import postavka
        p["pantheon_subjekt_racun"] = postavka(conn, "krajnji_kupac_subjekt", "Krajnji kupac")
    if p.get("vrsta") in ("tvrtka", "obrt") and "pantheon_subjekt_racun" not in p and k["pantheon_subjekt"]:
        p["pantheon_subjekt_racun"] = k["pantheon_subjekt"]
    if not p:
        return k
    conn.execute("UPDATE kupac SET " + ", ".join("%s = :%s" % (kk, kk) for kk in p) + " WHERE id = :id", dict(p, id=kupac_id))
    if k["izvor"] == "hub" or "telefon" in p or "email" in p:
        k2 = kupac(conn, kupac_id)
        trazi = norm(" ".join(x for x in (k2["naziv"], k2["naziv_puni"], k2["adresa"], k2["posta"], k2["mjesto"], k2["oib"], _telefon_norm(k2["telefon"]), k2["email"]) if x))
        conn.execute("UPDATE kupac SET trazi = ? WHERE id = ?", (trazi, kupac_id))
    dnevnik(conn, tko, "kupac", kupac_id, "uredi", ", ".join("%s=%s" % kv for kv in p.items()))
    conn.commit()
    return kupac(conn, kupac_id)


def kratki_naziv(naziv):
    """Prijedlog prvog dijela naziva naloga (D-33) — ured ga može promijeniti: prezime vlasnika obrta / osobe, ili prve dvije riječi tvrtke;
    bez dijakritike i razmaka. 'NAMJEŠTAJ MARIO vl.Mario Humer' → HUMER; 'KL - MONT, vl. Ivan Bogdanić' → BOGDANIC; 'BOJAN ROMIĆ' → ROMIC;
    'PROMISSIO d.o.o.' → PROMISSIO; 'ADRIA GRUPA d.o.o.' → ADRIA_GRUPA; 'OPG KUSIĆ BLAGOJE' → KUSIC_BLAGOJE."""
    import re
    n = norm(naziv)
    m = re.search(r"\bVL\.?\s*(.+)$", n)                    # obrt: 'vl. Ime Prezime' → prezime
    if m:
        rijeci = [w for w in re.split(r"[\s,.]+", m.group(1)) if w]
        return rijeci[-1] if rijeci else "KUPAC"
    pravni = re.compile(r"\b(D\.?O\.?O\.?|J\.?D\.?O\.?O\.?|OBRT|OPG|D\.?D\.?|J\.?T\.?D\.?|UDRUGA|USTANOVA)\b")
    tvrtka = bool(pravni.search(n))
    ostatak = pravni.sub(" ", n)
    ostatak = re.split(r"\bZA\b", ostatak)[0]                # 'PROMISSIO društvo s ograničenom … za trgovinu' → do 'ZA'
    ostatak = re.sub(r"\bDRUSTVO S OGRANICENOM ODGOVORNOSCU\b", " ", ostatak)
    rijeci = [w for w in re.split(r"[\s,.\-]+", ostatak) if w and len(w) > 1]
    if not rijeci:
        return "KUPAC"
    if not tvrtka and 2 <= len(rijeci) <= 3 and all(w.isalpha() for w in rijeci):
        return rijeci[-1]                                    # fizička osoba 'IME PREZIME' → PREZIME
    return "_".join(rijeci[:2])
