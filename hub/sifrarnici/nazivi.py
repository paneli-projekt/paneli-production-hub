# -*- coding: utf-8 -*-
"""Normalizacija i raščlamba naziva materijala i traka (D-24, D-31).

Isti materijal se u praksi piše na najmanje četiri načina:
  Pantheon  "IVERAL BIJELI NK W908 ST2 18 MM"      (ident IV000090)
  Winstore  "IVERAL BIJELI NK W908ST2 18MM"         (MaterialCode W908ST2-18)
  PPNEST    "IV_BIJELI_NK_18_MM"                    (SIFRA MAT W908ST2-18)
  PW / CPO  "IV BIJELI NK 18mm" / "IV BIJELI NK 18MM" (ručni unos, do 20 znakova)
  kupac     "IV BIJELI NK 18MM", "taverna", "CHAMPANGE UM"…
Ovdje su čiste funkcije bez baze: norm(), tokens(), kodovi(), rasclani_materijal(), rasclani_traku().
Logika je preuzeta iz skilla krojna-ponuda (scripts/krojna2ponuda.py, D-07) i proširena kodovima dekora i Winstore kodom.
"""
import re
import unicodedata

# riječi koje ne nose značenje dekora (vrsta, jedinice, česti sufiksi kodova)
STOP = {"IV", "IVERAL", "IVERICA", "MDF", "HDF", "LESONIT", "PVC", "AK", "AKRIL", "HPL", "CP", "COMPACT", "SP", "SPERPLOCA",
        "RP", "ZO", "RADNA", "ZIDNA", "PLOCA", "STOLA", "OBLOGA", "MM", "M", "ABS", "MEL", "MELAMIN", "TRAKA", "ISTI",
        "KOM", "M2", "X", "PLOCE", "EGGER", "KAINDL", "FUNDERMAX", "KRONOSPAN"}

# sinonimi / kratice / tipfeleri koji se stalno ponavljaju (norm → kanonski oblik)
SINONIMI = {
    "HR": "HRAST", "GL": "GLATKI", "GLATKA": "GLATKI", "BIJELA": "BIJELI", "CRNA": "CRNI", "SIVA": "SIVI", "TAMNA": "TAMNI",
    "CASHMIR": "KASMIR", "CASHMERE": "KASMIR", "KASMIR": "KASMIR",
    "CHAMPAGE": "CHAMPAGNE", "CHAMPANGE": "CHAMPAGNE", "SAMPANJAC": "CHAMPAGNE",
    "TRESNJA": "TRESNJA", "SVJETLI": "SVIJETLI", "SVJETLA": "SVIJETLI", "SVIJETLA": "SVIJETLI",
    "NATURAL": "NATUR", "HALIFAKS": "HALIFAX", "GRAY": "GREY", "GRAFIT": "GRAPHITE", "TEXTIL": "TEKSTIL", "TEXTILE": "TEKSTIL",
    "LIGHT": "SVIJETLI", "DARK": "TAMNI", "WHITE": "BIJELI", "BLACK": "CRNI", "OAK": "HRAST", "WALNUT": "ORAH", "BEZ": "BEIGE", "BEŽ": "BEIGE",
    "MODERNA": "MODERNO", "CANNOL": "CANNOLO",
}

DEBLJINE_PLOCA = {3, 4, 5, 6, 8, 10, 12, 13, 15, 16, 18, 19, 22, 25, 28, 30, 36, 38, 40}   # 13 = Fundermax compact

# Debljina koja se podrazumijeva po vrsti kad je u nazivu nema (Igor, 14.9.2026.): radne ploče i ploče stola su 38 mm.
# Zidne obloge i compact nisu ovdje — kod njih debljina varira (compact 6/8/12/13), pa ih ured potvrđuje po identu (D-51).
ZADANA_DEBLJINA = {("RP", "radna"): 38.0, ("RP", "stola"): 38.0}
PREFIKSI_KODA = {"VSM", "VHG", "VA", "FP", "TM", "ST"}  # prefiksi kodova dobavljača (VSM-06, VA-103), ne riječi dekora
_SINONIMI_NORM = None   # ključevi i vrijednosti provučeni kroz norm() (BIJELA → BJELA → BJELI); puni se pri prvom pozivu

VRSTE = [  # (prefiks u nazivu → vrsta, obitelj_rp); redoslijed je bitan (dulji prvi)
    (("PLOCA STOLA",), "RP", "stola"), (("RADNA PLOCA", "COMPACT RADNA"), "RP", "radna"),
    (("ZIDNA PLOCA", "ZIDNA OBLOGA"), "ZO", "zidna"),
    (("IVERAL", "IVERICA", "IV"), "IV", None), (("MDF", "HDF", "LESONIT"), "MDF", None), (("PVC",), "PVC", None),
    (("AKRIL", "AK"), "AK", None), (("HPL",), "HPL", None), (("COMPACT", "CP"), "CP", None),
    (("SPERPLOCA", "SPEROLCA", "SP"), "SP", None), (("RP",), "RP", None), (("ZO",), "ZO", None),
]


def norm(s):
    """Velika slova, bez dijakritike, '_' i višestruki razmaci → jedan razmak, IJE → JE (MLIJEČNI = MLJEČNI), 'MDF3MM' → 'MDF 3MM'."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("_", " ").replace("Đ", "D").replace("đ", "d")
    s = re.sub(r"\s+", " ", s).strip().upper()
    s = re.sub(r"^(MDF|IV|PVC|AK|HDF|RP|ZO)(\d)", r"\1 \2", s)
    return s.replace("IJE", "JE")


def norm_prikaz(s):
    """Kao norm(), ali bez IJE → JE i bez sinonima — za nazive koji idu ljudima na ekran / etiketu (BIJELI ostaje BIJELI)."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("_", " ").replace("Đ", "D").replace("đ", "d")
    s = re.sub(r"\s+", " ", s).strip().upper()
    return re.sub(r"^(MDF|IV|PVC|AK|HDF|RP|ZO)(\d)", r"\1 \2", s)


def rijeci_prikaz(s):
    """Riječi dekora u izvornom pisanju (za naziv_kratki i etikete): 'IVERAL BIJELI NK W908 ST2 18 MM' → ['BIJELI', 'NK']."""
    out = []
    for t in [t for t in re.split(r"[ /()\[\],;+*\-]+", norm_prikaz(s)) if t]:
        if norm(t) in STOP or len(t) < 2 or re.search(r"\d", t) or t in PREFIKSI_KODA or re.fullmatch(r"\d{1,2}MM", t):
            continue
        out.append(t)
    return out


def glue(s):
    """Sve alfanumeričko slijepljeno: 'K2665 AI-19' → 'K2665AI19'. Za usporedbu kodova neovisno o razmacima i crticama."""
    return re.sub(r"[^A-Z0-9]+", "", norm(s))


def _split(s):
    return [t for t in re.split(r"[ /()\[\],;+*\-]+", norm(s)) if t]


def tokens(s):
    """Riječi dekora: bez stop-riječi, sa sinonimima, bez čistih brojeva ≤ 2 znamenke (debljine)."""
    global _SINONIMI_NORM
    if _SINONIMI_NORM is None:
        _SINONIMI_NORM = {norm(k): norm(v) for k, v in SINONIMI.items()}
    out = []
    for t in _split(s):
        t = _SINONIMI_NORM.get(t, t)
        if t in STOP or len(t) < 2:
            continue
        if re.fullmatch(r"\d{1,2}(?:[,.]\d)?", t):
            continue
        if re.fullmatch(r"\d{1,2}MM", t):
            continue
        out.append(t)
    return out


def rijeci(s):
    """Samo alfabetske riječi dekora (bez kodova s brojkama i bez prefiksa kodova kao VSM, VA)."""
    return [t for t in tokens(s) if not re.search(r"\d", t) and t not in PREFIKSI_KODA]


def sufiksi(s):
    """Dvoslovni tokeni koji slijede iza koda s brojkama (2162 PE, K2751 AE, 27045 UM): sufiks koda dobavljača, ne riječ dekora."""
    toks = _split(s)
    out = set()
    for i in range(1, len(toks)):
        if re.fullmatch(r"[A-Z]{2}", toks[i]) and re.search(r"\d", toks[i - 1]) and not re.fullmatch(r"\d{1,2}(?:MM)?", toks[i - 1]):
            out.add(toks[i])
    return out


def kodovi(s):
    """Kodovi dekora u više varijanti, slijepljeno: 'BIJELI NK W908 ST2 18 MM' → {'W908', 'ST2', 'W908ST2'};
    'SIVI TAMNI 2162 MN 19MM' → {'2162', '2162MN'}; 'PVC KASMIR VSM-06 18MM' → {'VSM06'}; 'H1180 ST37' → {'H1180','ST37','H1180ST37'}.
    Kod počinje tokenom koji sadrži znamenku (a nije debljina) i nastavlja se dok slijede kratki tokeni (≤ 2 slova ili znamenke)."""
    toks = _split(s)
    # ukloni tokene debljine ("18", "18MM") — nisu kodovi
    def je_debljina(t):
        return bool(re.fullmatch(r"\d{1,2}(?:[,.]\d)?M{0,2}", t)) and float(t.rstrip("M").replace(",", ".")) in DEBLJINE_PLOCA | {0.5, 1.0, 2.0, 1.3, 0.8, 18.6}
    out = set()
    i = 0
    while i < len(toks):
        t = toks[i]
        prefiks = bool(re.fullmatch(r"(VSM|VHG|VA|FP|TM|ST|K|U|W|H|F)", t)) and i + 1 < len(toks) and bool(re.fullmatch(r"\d{2,5}[A-Z]{0,2}", toks[i + 1]))
        if (re.search(r"\d", t) and not je_debljina(t) and len(t) >= 3) or prefiks:
            run = [t]
            j = i + 1
            while j < len(toks) and (re.fullmatch(r"[A-Z]{1,2}", toks[j]) or re.fullmatch(r"[A-Z]{1,2}\d{1,3}", toks[j])
                                     or re.fullmatch(r"\d{2,5}[A-Z]{0,2}", toks[j]) and (prefiks and j == i + 1 or not je_debljina(toks[j]))):
                run.append(toks[j])
                j += 1
            for k in range(len(run)):
                for m in range(k + 1, len(run) + 1):
                    v = "".join(run[k:m])
                    if re.search(r"\d", v) and len(v) >= 3:
                        out.add(v)
            i = j
        else:
            i += 1
    return out


def zadana_debljina(vrsta_, obitelj_rp=None):
    """Debljina po vrsti za materijale kojima je u nazivu nema (nazivi.ZADANA_DEBLJINA) ili None."""
    return ZADANA_DEBLJINA.get((vrsta_, obitelj_rp))


_DIM3 = re.compile(r"(?<!\d)(\d{3,4})\s*X\s*(\d{2,4})\s*X\s*(\d{1,2}(?:[,.]\d)?)(?![\dA-LN-Z])")   # 4100X640X8MM → 8 (M smije slijediti)


def debljina(s):
    """Debljina ploče iz naziva (mm) ili None: '18MM', '18 MM', '_18_', ' 18' (samo vjerojatne debljine), '18,6MM',
    i iz dimenzije '4100X640X8MM'; 'VHG-19' / 'VSM-06' su kodovi."""
    n = norm(s)
    m = _DIM3.search(n)
    if m and float(m.group(3).replace(",", ".")) in DEBLJINE_PLOCA:
        return float(m.group(3).replace(",", "."))
    m = re.search(r"(?<![\dA-Z])(\d{1,2}(?:[,.]\d)?)\s*M{1,2}\b", n)
    if m:
        return float(m.group(1).replace(",", "."))
    kand = [float(t) for t in re.findall(r"(?<![\dA-Z/,.-])(\d{1,2})(?![\dA-Z/,.])", n) if float(t) in DEBLJINE_PLOCA]   # 'VHG-19' nije debljina
    return kand[-1] if kand else None


def vrsta(s):
    """(vrsta, obitelj_rp) iz početka naziva: 'IVERAL …' → ('IV', None), 'PLOČA STOLA …' → ('RP', 'stola'), 'ZO HR …' → ('ZO', 'zidna')."""
    n = norm(s)
    toks = _split(n)
    if not toks:
        return "OST", None
    for prefiksi, v, ob in VRSTE:
        for p in prefiksi:
            pt = p.split()
            if toks[:len(pt)] == pt:
                if v in ("RP", "ZO") and ob is None:
                    ob = "zidna" if v == "ZO" else None
                return v, ob
    return "OST", None


def rasclani_materijal(naziv, debljina_datoteke=None, sirina_ploce=None):
    """Sve što o materijalu znamo iz naziva (i, ako je dano, iz datoteke): vrsta, obitelj_rp, debljina, riječi dekora, kodovi.
    sirina_ploce (mm) iz CPO/Winstorea odlučuje obitelj radne ploče: 600 → radna, 900 → stola, 640 → zidna (D-37)."""
    v, ob = vrsta(naziv)
    deb = debljina(naziv)
    if deb is None:
        deb = debljina_datoteke
    if v in ("RP", "ZO") and sirina_ploce:
        if abs(sirina_ploce - 900) <= 60:
            ob = "stola"
        elif abs(sirina_ploce - 640) <= 30:
            ob = "zidna"
        elif abs(sirina_ploce - 600) <= 30:
            ob = "radna"
    if v == "ZO" and ob is None:
        ob = "zidna"
    return dict(vrsta=v, obitelj_rp=ob, debljina=deb, rijeci=rijeci(naziv), rijeci_prikaz=rijeci_prikaz(naziv), kodovi=kodovi(naziv), norm=norm(naziv), glue=glue(naziv))


def naziv_kratki(vrsta_, dekor, deb, obitelj_rp=None):
    """Kratki naziv kakav ljudi pišu u nalogu: 'IV BIJELI NK 18', 'MDF BIJELI 3', 'RP BASANIT SAND (stola)'."""
    d = ("%g" % deb) if deb else ""
    if vrsta_ in ("RP", "ZO"):
        return " ".join(x for x in (vrsta_, dekor, ("(%s)" % obitelj_rp) if obitelj_rp else "") if x)
    return " ".join(x for x in (vrsta_, dekor, d) if x)


# ---------------------------------------------------------------- trake
_KLASA = re.compile(r"(?<![\d,])(\d+(?:[,.]\d+)?)\s*/\s*(\d{2,3})")


def rasclani_traku(oznaka):
    """Oznaka trake iz naloga → dict(vrsta, debljina, sirina, isti, dekor, kodovi).
    'ABS-ISTI' → ABS, 1 mm (zadano), širina po materijalu, isti dekor (D-31)
    'ABS-ISTI 2mm' → 2 mm; 'MEL-ISTI' / 'MEL_ISTI' / 'MEL' → 0,5/22 isti
    '1/22 ISTI', '1/44 ISTI' → 1 mm, širina 22 / 44, isti
    'MEL CRNA NK' → 0,5/22 dekor CRNA NK; '1/22 JELA TAVERNA' → 1/22 dekor JELA TAVERNA; 'taverna' → dekor TAVERNA
    'MET 0.5/22 BIJELI NK' (tipfeler) = 'MEL 0,5/22 BIJELI NK'."""
    n = norm(oznaka)
    vr = None
    if re.search(r"\b(MEL|MET|MELAMIN)\b", n):
        vr = "MEL"
    elif re.search(r"\bABS\b", n):
        vr = "ABS"
    elif re.search(r"\bPVC\b", n):
        vr = "PVC"
    deb = sir = None
    m = _KLASA.search(n)
    if m:
        deb = float(m.group(1).replace(",", "."))
        sir = int(m.group(2))
        n = n[:m.start()] + " " + n[m.end():]
    m2 = re.search(r"\b(\d(?:[,.]\d)?)\s*MM\b", n)
    if m2 and deb is None:
        deb = float(m2.group(1).replace(",", "."))
        n = n[:m2.start()] + " " + n[m2.end():]
    isti = bool(re.search(r"\bISTI\b", n)) or (vr == "MEL" and not tokens(n))
    rest = re.sub(r"\b(ABS|MEL|MET|MELAMIN|PVC|ISTI)\b", " ", n)
    dekor = " ".join(t for t in tokens(rest))
    if vr == "MEL" and deb is None:
        deb = 0.5
    if vr is None and (isti or dekor):
        vr = "ABS"
    if deb is None and vr == "ABS":
        deb = 1.0
    return dict(vrsta=vr, debljina=deb, sirina=sir, isti=isti, dekor=dekor, kodovi=kodovi(rest), norm=norm(oznaka))


def klasa_trake(deb, sir):
    """'1/22', '0,5/22', '2/44' — isti zapis kao u Pantheon nazivima traka i pravilima usluga (D-20)."""
    if deb is None or sir is None:
        return None
    d = ("%g" % deb).replace(".", ",")
    return "%s/%d" % (d, sir)


def sirina_za_materijal(deb_materijala):
    """Zadana širina trake po debljini ploče: ≤ 19 → 22, 20–30 → 29, > 30 (radne ploče 38) → 44."""
    if deb_materijala is None:
        return 22
    if deb_materijala <= 19.5:
        return 22
    if deb_materijala <= 30:
        return 29
    return 44


def rasclani_traku_pantheon(naziv):
    """Pantheon naziv trake 'ABS 0,5/22 BIJELI NK' → (vrsta, debljina, sirina, klasa, dekor); None ako nije oblika ABS d/š …"""
    n = norm(naziv)
    m = re.match(r"^(ABS|PVC|MEL|MELAMIN|PP)\s+(\d+(?:[,.]\d+)?)\s*/\s*(\d{2,3})\s*(.*)$", n)
    if not m:
        m2 = re.match(r"^(ABS|PVC)\s+(\d{2,3})\s*/\s*(\d+(?:[,.]\d+)?)\s*(.*)$", n)  # 'ABS 23/0,8 …' (obrnuto)
        if not m2:
            return None
        vr, sir, deb, rest = m2.group(1), int(m2.group(2)), float(m2.group(3).replace(",", ".")), m2.group(4)
    else:
        vr, deb, sir, rest = m.group(1), float(m.group(2).replace(",", ".")), int(m.group(3)), m.group(4)
    if vr == "MELAMIN":
        vr = "MEL"
    return dict(vrsta=vr, debljina=deb, sirina=sir, klasa=klasa_trake(deb, sir), dekor=" ".join(tokens(rest)), kodovi=kodovi(rest))
