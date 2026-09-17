# -*- coding: utf-8 -*-
"""radne_ploce.py — radne ploče, ploče stola i zidne obloge (4100 × 600 / 900 / 640) na pili: slaganje i naplata PO PLOČI.

Pravila (D-37, 12. 9. 2026., dopunjeno Igorovim odgovorima 17. 9. 2026. → D-92):
  * radna ploča 600 (RP, obitelj 'radna' ili bez obitelji): KOMAD IZA KOMADA — prva mjera elementa (L) uvijek uz duljinu ploče (4100),
    druga (W) je dubina preko širine ploče, jedan komad u širini (profilirani prednji rub ostaje; Igor 17. 9.: element 500 × 600 je
    dužina 500 i dubina 600, NE smije se okrenuti); naplata po ploči: zbroj duljina komada na ploči ≤ 2,7 m → točni metri, najmanje 1,4 m;
    > 2,7 m → cijela ploča (4,1 m).
  * ploča stola 900 (RP 'stola'): smiju se rezati i uži komadi jedan uz drugi (trake uz duljinu ploče — obični optimizator, samo uzdužno /
    trake); naplata po ploči: iskorištena duljina (najdulja traka) ≤ pola ploče (2,05 m) → pola, inače cijela; ident DEKORA (M) × 2,05 / 4,1 m.
  * zidna obloga 640 (ZO): komad iza komada kao radna ploča; prodaje se ISKLJUČIVO cijela (4,1 m po ploči); rezanje 4 reza po komadu
    (krajca se sa svih strana).
  * rezanje radne ploče i ploče stola: US000303 = 2 reza po komadu (kao dosad).
Korisni ostatak (naš restl) postoji samo kad ploča NIJE naplaćena cijela: ostatak uz duljinu ploče (fizički: ploča − obrez − iskorišteno − rez).

Oblik shema je isti kao u pila_optimizator (dir, strips → blocks → subs → parts), pa CPO, sličice, krojni nacrt i potvrda rade bez izmjena.
"""
import math

from hub.optimizacija import pila_optimizator as OPT

RADNA_CIJELA_IZNAD_MM = 2700.0
RADNA_MIN_MM = 1400.0
OSTATAK_MIN_MM = 400.0
REZOVA_PO_KOMADU = {"radna": 2, "stola": 2, "zidna": 4}
OPIS_OBITELJI = {"radna": "radna ploča", "stola": "ploča stola", "zidna": "zidna obloga"}


def obitelj(vrsta, obitelj_rp=None):
    """'radna' | 'stola' | 'zidna' za RP / ZO materijal, inače None."""
    if vrsta == "ZO" or obitelj_rp == "zidna":
        return "zidna"
    if vrsta == "RP":
        return "stola" if obitelj_rp == "stola" else "radna"
    return None


def slozi_niz(dijelovi, ploca=(4100, 600), trim=0, kerf=5.0):
    """Komad iza komada: dijelovi (idx, W, L, kom) → ploče s JEDNOM trakom uz duljinu. Orijentacija je FIKSNA: L elementa uz duljinu
    ploče, W (dubina) preko širine — komad se nikad ne okreće, jer bi pila tada odrezala profilirani (zaobljeni) rub (Igor, 17. 9.).
    Best-fit decreasing po duljini (najmanje ploča), ploče poredane od najpunije. ValueError kad komad ne stane."""
    PL, PW = float(ploca[0]), float(ploca[1])
    LIM_L, LIM_W = PL - 2 * trim, PW - 2 * trim
    komadi = []
    for idx, W, L, kom in dijelovi:
        duz, sir = float(L), float(W)
        if sir > LIM_W + 1e-6:
            raise ValueError("dio %d (L %g × W %g): dubina W je veća od širine ploče %g — prva mjera (L) je dužina uz ploču, druga (W) dubina"
                             % (idx, L, W, PW - 2 * trim))
        if duz > LIM_L + 1e-6:
            raise ValueError("dio %d (L %g × W %g) dulji je od ploče %g — spoj ploča se radi ručno" % (idx, L, W, PL - 2 * trim))
        komadi += [(duz, sir, idx)] * int(kom)
    komadi.sort(key=lambda k: (-k[0], -k[1], k[2]))
    ploce = []                                   # [dict(used, items)]
    for duz, sir, idx in komadi:
        naj = None
        for p in ploce:
            treba = p["used"] + kerf + duz
            if treba <= LIM_L + 1e-6 and (naj is None or LIM_L - treba < naj[0]):
                naj = (LIM_L - treba, p)
        if naj:
            naj[1]["used"] += kerf + duz
            naj[1]["items"].append((duz, sir, idx))
        else:
            ploce.append(dict(used=duz, items=[(duz, sir, idx)]))
    ploce.sort(key=lambda p: -p["used"])
    sheets = []
    for p in ploce:
        w = max(s for _, s, _ in p["items"])
        blocks = [dict(l=duz, used_w=sir, subs=[dict(w3=sir, parts=[(duz, idx)])]) for duz, sir, idx in p["items"]]
        sheets.append(dict(dir="L", used_w=w, strips=[dict(w=w, used_l=p["used"], blocks=blocks)]))
    return sheets


def _duljine(sheet):
    """(zbroj duljina komada u najduljoj traci, iskorištena duljina s rezovima) — mjera za pravilo naplate i za ostatak."""
    zbroj = max((sum(b["l"] for b in st["blocks"]) for st in sheet["strips"]), default=0.0)
    used = max((st["used_l"] for st in sheet["strips"]), default=0.0)
    return zbroj, used


def naplata_ploce(ob, zbroj_mm, ploca_L=4100.0):
    """Pravilo naplate jedne ploče → (metri za naplatu, opis) — opis: 'cijela' | 'pola' | 'najmanje 1,4 m' | 'metri'."""
    L = float(ploca_L)
    if ob == "zidna":
        return L / 1000.0, "cijela"
    if ob == "stola":
        return (L / 2000.0, "pola") if zbroj_mm <= L / 2 + 1e-6 else (L / 1000.0, "cijela")
    if zbroj_mm > RADNA_CIJELA_IZNAD_MM + 1e-6:
        return L / 1000.0, "cijela"
    if zbroj_mm < RADNA_MIN_MM - 1e-6:
        return RADNA_MIN_MM / 1000.0, "najmanje 1,4 m"
    return math.ceil(zbroj_mm / 10.0 - 1e-9) / 100.0, "metri"                # točni metri, naviše na cijeli cm (2265 mm → 2,27 m)


def ocijeni(sheets, ploca, trim, kerf, ob):
    """Kao pila_optimizator.ocijeni, ali naplata po pravilu obitelji: dict(ploca, m2_sve, m2_naplata, ostaci, rezova, rp{…})."""
    L, W = float(ploca[0]), float(ploca[1])
    listovi, ostaci = [], []
    for i, s in enumerate(sheets, 1):
        zbroj, used = _duljine(s)
        metri, opis = naplata_ploce(ob, zbroj, L)
        ostatak = None
        if opis != "cijela":
            rest = L - trim - used - kerf
            if rest >= OSTATAK_MIN_MM:
                ostatak = (round(rest), round(W), rest * W / 1e6)
                ostaci.append(ostatak)
        listovi.append(dict(br=i, duljina_mm=round(zbroj), naplata_m=round(metri, 3), opis=opis, ostatak=ostatak))
    ukupno = round(sum(li["naplata_m"] for li in listovi), 3)
    return dict(ploca=len(sheets), m2_sve=round(len(sheets) * L * W / 1e6, 2), m2_naplata=round(ukupno * W / 1000.0, 2), ostaci=ostaci,
                rezova=sum(len(OPT.sheme_u_cuts(s)) for s in sheets),
                rp=dict(obitelj=ob, naziv=OPIS_OBITELJI.get(ob, ob), listovi=listovi, ukupno_m=ukupno, ploca_L=L, ploca_W=W,
                        rezova_po_komadu=REZOVA_PO_KOMADU.get(ob, 2)))


def _m(x):
    s = ("%.2f" % x).rstrip("0").rstrip(".")
    return s.replace(".", ",")


def opis(rp):
    """Kratko, za stavku ponude i ekran: 'ploča 1: 3,12 m → cijela 4,1 m; ploča 2: 0,9 m → najmanje 1,4 m'."""
    dijelovi = []
    for li in rp["listovi"]:
        d = li["duljina_mm"] / 1000.0
        if li["opis"] == "metri":
            dijelovi.append("ploča %d: %s m" % (li["br"], _m(li["naplata_m"])))
        else:
            dijelovi.append("ploča %d: %s m → %s %s m" % (li["br"], _m(d), li["opis"].replace(" 1,4 m", ""), _m(li["naplata_m"])))
    return "; ".join(dijelovi)


def kolicina_za_jm(rp, jm):
    """Količina stavke u jedinici identa: M → metri, M2 → metri × širina ploče, KOM → broj ploča (uz upozorenje). Vraća (količina, upozorenje)."""
    jm = (jm or "M").upper()
    if jm == "M2":
        return round(rp["ukupno_m"] * rp["ploca_W"] / 1000.0, 3), None
    if jm == "KOM":
        return float(len(rp["listovi"])), "jedinica identa je KOM — naplaćeno po započetoj ploči, provjeriti"
    return round(rp["ukupno_m"], 3), None
