"""obracun.py — kalkulator količina "PW-metodom" (D-17 korak 1, D-18, D-19).

Pravila potvrđena 11. 9. 2026. usporedbom PW krojnih PDF-ova, CPO datoteka i ekrana PanelWizarda (05 §5.3):
  * ploča nominalno L×W (2800×2070), optimirana dimenzija = L−2·obrub × W−2·obrub (2780×2050), obrub 10 mm
  * kerf ZA OBRAČUN = 16 mm ("Podesi alat", globalno u PW-u), iako CPO za pilu nosi 5,00
  * KORISNI OSTATAK = jedna traka po ploči, okomita na trake razine 1, koja preostane nakon zadnje trake:
        ostatak = dim_okomita − obrub − Σ(širine traka razine 1) − kerf · n_traka
    (ostatak zadržava daleki obrub i puni nominalni drugi dim: npr. "Ostatak 2800 × 1016"), i računa se samo ako su
    OBJE mjere ≥ 400 mm i površina ≥ 1 m² (Konfiguracija → Generalno).
  * POVRŠINA ZA NAPLATU = n_ploča · L·W − Σ korisnih ostataka        (I_01970: 5,796 − 0,696·2,07 = 4,36 ✓; I_01971: 2,95 ✓; I_01915: 30,16 ✓)
  * METRI KANTIRANJA (PW "Kantiranje sortirano po dekorima") = Σ (duljina stranice · kom) · 1,10   (4 PDF-a: omjer točno 1,1000)
  * D-19: materijal s godom → samo uzdužni načini; bez goda → i poprečni; vrijedi rezultat s NAJMANJOM površinom za naplatu.
"""
from hub.formati import cpo_rw

OBRUB = 10.0
KERF_OBRACUN = 16.0
OSTATAK_MIN_MM = 400.0            # pravilo NAPLATE (PW): ostatak koji se ne naplaćuje kupcu — obje mjere
OSTATAK_MIN_M2 = 1.0              # … i površina (D-19); D-95 ovo NE mijenja
RESTL_MIN_M2 = 0.35               # pravilo ČUVANJA restla u regalu (D-95, Igor 18. 9.) — niže od naplate
RESTL_MIN_MM = 150.0              # kraća stranica ispod koje se komad ne čuva
RESTL_TRAKA_MM = 2000.0           # traka duža od ovoga čuva se i kad je ispod RESTL_MIN_M2
KANT_FAKTOR_PW = 1.10

def ostatak_dims(dir_, l1, ploca, trim=OBRUB, kerf=KERF_OBRACUN):
    """Geometrijski ostatak ploče, bez ikakvog praga: (dim1, dim2, m2). dir_ 'L' (trake uz duljinu, ostatak = L × preostala širina)
    ili 'S' (trake poprijeko, ostatak = preostala duljina × W); l1 = širine traka razine 1."""
    L, W = ploca
    n = len(l1)
    if dir_ == 'L':
        rest = W - trim - sum(l1) - kerf * n
        dims = (L, rest)
    else:
        rest = L - trim - sum(l1) - kerf * n
        dims = (rest, W)
    return (round(dims[0]), round(dims[1]), dims[0] * dims[1] / 1e6)

def je_restl(L, W, min_m2=RESTL_MIN_M2, min_mm=RESTL_MIN_MM, traka_mm=RESTL_TRAKA_MM):
    """Čuva li se ostatak kao restl (D-95): kraća stranica ≥ min_mm i (površina ≥ min_m2 ILI duža stranica ≥ traka_mm).
    Pravilo naplate je zasebno i ostaje ≥ 400 mm i ≥ 1 m² — komad između ta dva praga kupac plaća, a mi ga zadržimo."""
    d, k = max(float(L), float(W)), min(float(L), float(W))
    return k >= min_mm - 1e-6 and (d * k / 1e6 >= min_m2 - 1e-9 or d >= traka_mm - 1e-6)

def ostatak_ploce(dir_, l1, ploca, trim=OBRUB, kerf=KERF_OBRACUN):
    """Ostatak koji se NE NAPLAĆUJE kupcu (PW pravilo): (dim1, dim2, m2) ili None."""
    d1, d2, m2 = ostatak_dims(dir_, l1, ploca, trim, kerf)
    if min(d1, d2) >= OSTATAK_MIN_MM and m2 >= OSTATAK_MIN_M2:
        return (d1, d2, m2)
    return None

def naplata(sheme, ploca, trim=OBRUB, kerf=KERF_OBRACUN):
    """sheme = lista (dir, [širine traka razine 1]) po ploči. Vraća dict(ploca, m2_sve, m2_naplata, ostaci)."""
    L, W = ploca
    m2_ploce = L * W / 1e6
    ostaci = []
    for dir_, l1 in sheme:
        o = ostatak_ploce(dir_, l1, ploca, trim, kerf)
        if o:
            ostaci.append(o)
    n = len(sheme)
    sve = n * m2_ploce
    return dict(ploca=n, m2_sve=round(sve, 2), m2_naplata=round(sve - sum(o[2] for o in ostaci), 2), ostaci=ostaci)

def naplata_iz_cpo(d, kerf=KERF_OBRACUN):
    """Površina za naplatu rekonstruirana iz PW CPO datoteke (stablo rezova) — služi kao PW referenca za benchmark."""
    s = d['inv'][0]
    ploca = (s['L'], s['W'])
    sheme = []
    for q in d['pat']:
        l1 = [c[1] for c in q['cuts'] if c[0] == 1]
        # PW kuriozitet: puna širina radne ploče zapisana kao dvostruki rez razine 1 → računaj kao jednu traku
        if len(l1) == 2 and l1[0] == l1[1] and l1[0] >= (s['W'] if q['dir'] == 'L' else s['L']) - 2 * s['trim'][0]:
            l1 = l1[:1]
        for _ in range(q['qty']):
            sheme.append((q['dir'], l1))
    return naplata(sheme, ploca, s['trim'][0], kerf)

def kant_metri(els, faktor=KANT_FAKTOR_PW):
    """Metri trake po nazivu trake kako ih PW ispisuje (Σ stranica · kom · 1,10). L/D = duža stranica (L), G/O = kraća (W)."""
    tot = {}
    for e in els:
        for side, name in e.get('traka', {}).items():
            name = (name or '').strip()
            if not name:
                continue
            ln = float(e['L']) if side in ('L', 'D') else float(e['W'])
            tot[name] = tot.get(name, 0.0) + ln * int(e['kom']) / 1000.0
    return {k: round(v * faktor, 3) for k, v in tot.items()}

def kant_metri_iz_cpo(d, faktor=KANT_FAKTOR_PW):
    """Isto iz PW CPO datoteke (PRT3: [dolje, desno, gore, lijevo]; lijevo/desno = L, dolje/gore = W). Potvrđeno na 4 PDF-a."""
    tot = {}
    for p in d['prt']:
        for i, (_, name, _) in enumerate(p['edges']):
            if not name:
                continue
            ln = p['L'] if i in (1, 3) else p['W']
            tot[name] = tot.get(name, 0.0) + ln * p['qty'] / 1000.0
    return {k: round(v * faktor, 3) for k, v in tot.items()}

if __name__ == '__main__':
    import sys, glob, os
    for f in sorted(glob.glob(os.path.join(sys.argv[1], '**', '*.cpo'), recursive=True)):
        d = cpo_rw.parse(f)
        r = naplata_iz_cpo(d)
        print('%-14s %-24s ploča %2d  sve %6.2f  naplata %6.2f  ostaci %s' % (os.path.basename(f), d['material'][:24], r['ploca'], r['m2_sve'], r['m2_naplata'], [(o[0], o[1]) for o in r['ostaci']]))
