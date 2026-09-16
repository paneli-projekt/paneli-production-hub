"""pila_optimizator.py — giljotinski optimizator za pilu (D-16/D-17) + izbor načina po pravilu D-19.

Daje stablo rezova u obliku koji Selco OSI čita (CUT1 razine 1..4) i CPO datoteku preko cpo_rw; površina za
naplatu računa se PW-metodom (obracun.py). Potvrđeno na 50 PW datoteka: dio na razini n ima točno dimenzije
(pozicija roditelja, pozicija reza); shema 'L' = trake uz duljinu ploče (rez razine 1 paralelan s dužom stranicom),
'S' = trake poprijeko.

Načini (kao u PanelWizardu, desni klik na žarulju):
  'uzduzno'  → shema L, trake razine 1 uz duljinu (2800); u traci blokovi (razina 2), pod-trake (3), komadi (4)
  'poprecno' → shema S, trake razine 1 poprijeko (uz širinu 2070)
  'trake'    → shema L, ali u traci samo komadi ISTE širine (bez pod-traka razine 3/4) — jednostavnije rezanje
Svaki način se vrti u više varijanta (redoslijed komada, orijentacija bez goda, kolone, best-fit, dotjerivanje zadnje ploče — korak 5)
i uzima se varijanta s najmanjom površinom za naplatu, pa manje ploča, pa manje rezova.  D-19: s godom orijentacija komada je fiksna
(duljina uz god); 'poprecno' je dopušteno i s godom jer god ostaje uz duljinu ploče (PW ga sam koristi, I_01843).
Slaganje ide s FIZIČKIM kerfom pile (5 mm, kao PW — provjereno na 45 CPO-a: zbrojevi razine 2 dodiruju granicu točno s 5), a korisni
ostatak / naplata računa se s 16 (obracun.KERF_OBRACUN) — D-72.

Orijentacija komada: (w, l) = (mjera uz os širine trake, mjera uz traku). S godom duljina dijela (L) mora ležati uz
duljinu ploče: u L-shemi (w,l)=(W,L), u S-shemi (w,l)=(L,W). Bez goda obje orijentacije su dopuštene.
"""
from hub.formati import cpo_rw
from hub.optimizacija import obracun
from datetime import datetime

NACINI_S_GODOM = ('uzduzno', 'trake', 'poprecno')   # poprečno i s godom: god ostaje uz duljinu ploče (orijentacija fiksna), PW ga sam koristi (I_01843)
NACINI_BEZ_GODA = ('uzduzno', 'trake', 'poprecno')

def _os_ploce(ploca, trim, dir_):
    """(granica zbroja širina traka, duljina trake) za shemu L ili S."""
    PL, PW_ = ploca
    UL, UW = PL - 2 * trim, PW_ - 2 * trim
    return (UW, UL) if dir_ == 'L' else (UL, UW)

def _orijentiraj(W, L, god, dir_, dulja_uz_traku):
    """Vrati (w, l) za komad W×L u shemi dir_. Kod goda orijentacija je fiksna."""
    if god:
        return (W, L) if dir_ == 'L' else (L, W)
    a, b = (max(W, L), min(W, L))
    return (b, a) if dulja_uz_traku else (a, b)

def slozi(dijelovi, ploca=(2800, 2070), trim=10, kerf=16.0, god=True, nacin='uzduzno', sort='w', dulja_uz_traku=True):
    """dijelovi: lista (idx, W, L, kom). Vraća listu ploča: dict(dir, strips=[dict(w, used_l, blocks=[dict(l, used_w, subs=[dict(w3, parts=[(l4, idx)])])])])."""
    dir_ = 'S' if nacin == 'poprecno' else 'L'
    LIM_W, LIM_L = _os_ploce(ploca, trim, dir_)
    pieces = []
    for idx, W, L, kom in dijelovi:
        w, l = _orijentiraj(W, L, god, dir_, dulja_uz_traku)
        if w > LIM_W or l > LIM_L:
            if not god and l <= LIM_W and w <= LIM_L:
                w, l = l, w
            else:
                raise ValueError('dio %d (%sx%s) ne stane na ploču %sx%s u shemi %s' % (idx, W, L, ploca[0], ploca[1], dir_))
        pieces += [(w, l, idx)] * kom
    if sort == 'w':
        pieces.sort(key=lambda p: (-p[0], -p[1]))
    elif sort == 'l':
        pieces.sort(key=lambda p: (-p[1], -p[0]))
    else:  # 'area'
        pieces.sort(key=lambda p: (-p[0] * p[1], -p[0]))
    sheets = []
    samo_trake = nacin == 'trake'

    def try_place(sheet, w, l, idx):
        # 1) pod-traka u postojećem bloku (razina 3/4) — ne u načinu 'trake'
        if not samo_trake:
            for st in sheet['strips']:
                for b in st['blocks']:
                    if l <= b['l'] and b['used_w'] + kerf + w <= st['w']:
                        b['subs'].append(dict(w3=w, parts=[(l, idx)]))
                        b['used_w'] += kerf + w
                        return True
        # 2) novi blok u postojećoj traci (razina 2): ista širina (trake) ili ≤ (uzduzno/poprecno)
        for st in sheet['strips']:
            if (w == st['w'] if samo_trake else w <= st['w']) and st['used_l'] + kerf + l <= LIM_L:
                st['blocks'].append(dict(l=l, used_w=w, subs=[dict(w3=w, parts=[(l, idx)])]))
                st['used_l'] += kerf + l
                return True
        # 3) nova traka (razina 1)
        if sheet['used_w'] + (kerf if sheet['strips'] else 0) + w <= LIM_W:
            sheet['strips'].append(dict(w=w, used_l=l, blocks=[dict(l=l, used_w=w, subs=[dict(w3=w, parts=[(l, idx)])])]))
            sheet['used_w'] += (kerf if len(sheet['strips']) > 1 else 0) + w
            return True
        return False

    for w, l, idx in pieces:
        if not any(try_place(s, w, l, idx) for s in sheets):
            s = dict(dir=dir_, strips=[], used_w=0)
            sheets.append(s)
            if not try_place(s, w, l, idx):
                raise ValueError('dio %d ne stane ni na praznu ploču' % idx)
    return sheets

def sheme_u_cuts(sheet):
    """CUT1 zapisi (razina, pozicija, je_dio, idx) po PW pravilima."""
    cuts = []
    for st in sheet['strips']:
        cuts.append((1, st['w'], False, 0))
        for b in st['blocks']:
            sb0 = b['subs'][0]
            single = len(b['subs']) == 1 and sb0['w3'] == st['w'] and len(sb0['parts']) == 1 and sb0['parts'][0][0] == b['l']
            if single:
                cuts.append((2, b['l'], True, sb0['parts'][0][1]))
                continue
            cuts.append((2, b['l'], False, 0))
            for sb in b['subs']:
                p = sb['parts']
                if len(p) == 1 and p[0][0] == b['l']:
                    cuts.append((3, sb['w3'], True, p[0][1]))
                else:
                    cuts.append((3, sb['w3'], False, 0))
                    for l4, idx in p:
                        cuts.append((4, l4, True, idx))
    return cuts

def ocijeni(sheets, ploca, trim, kerf_obracun=obracun.KERF_OBRACUN):
    sheme = [(s['dir'], [st['w'] for st in s['strips']]) for s in sheets]
    r = obracun.naplata(sheme, ploca, trim, kerf_obracun)
    r['rezova'] = sum(len(sheme_u_cuts(s)) for s in sheets)
    return r

def _dijelovi_ploce(sheet, dijelovi):
    """Komadi jedne ploče kao lista (idx, W, L, kom) — iz idx-a natrag na izvorne mjere."""
    mjere = {idx: (W, L) for idx, W, L, _ in dijelovi}
    br = {}
    for st in sheet['strips']:
        for b in st['blocks']:
            for sb in b['subs']:
                for _, idx in sb['parts']:
                    br[idx] = br.get(idx, 0) + 1
    return [(idx, mjere[idx][0], mjere[idx][1], n) for idx, n in br.items()]

def _premjesti_u_prethodne(sheets, dijelovi, ploca, trim, kerf, god):
    """Komade zadnje ploče pokušaj ugurati u rupe prethodnih ploča (pod-traka / blok / nova traka, best-fit); zadrži samo ako se
    ukupna površina za naplatu smanji (zadnja ploča se prazni → veći ostatak, ili nestane)."""
    import copy
    if len(sheets) < 2:
        return sheets
    best_m2 = ocijeni(sheets, ploca, trim)['m2_naplata']
    rad = copy.deepcopy(sheets)
    mjere = {idx: (W, L) for idx, W, L, _ in dijelovi}
    zadnja = rad[-1]
    dir_ = zadnja['dir']
    LIM_W, LIM_L = _os_ploce(ploca, trim, dir_)
    # komadi zadnje ploče, veći prvo
    komadi = []
    for st in zadnja['strips']:
        for b in st['blocks']:
            for sb in b['subs']:
                for l, idx in sb['parts']:
                    komadi.append((mjere[idx][0] * mjere[idx][1], idx))
    komadi.sort(reverse=True)
    premjesteno = False
    for _, idx in komadi:
        W, L = mjere[idx]
        ors = _orijentacije(W, L, god, dir_, LIM_W, LIM_L)
        best = None
        for si, sheet in enumerate(rad[:-1]):
            if sheet['dir'] != dir_:
                continue
            for (w, l) in ors:
                for st in sheet['strips']:
                    for b in st['blocks']:
                        if l <= b['l'] and b['used_w'] + kerf + w <= st['w']:
                            k = ((b['l'] - l) * w, 0)
                            if best is None or k < best[0]: best = (k, sheet, w, l, (st, b))
                    if w <= st['w'] and st['used_l'] + kerf + l <= LIM_L:
                        k = ((st['w'] - w) * l, 1)
                        if best is None or k < best[0]: best = (k, sheet, w, l, st)
                if sheet['used_w'] + (kerf if sheet['strips'] else 0) + w <= LIM_W:      # nova traka u prethodnoj ploči (skuplje)
                    k = (w * (LIM_L - l) + 5e5, 2)
                    if best is None or k < best[0]: best = (k, sheet, w, l, None)
        if best is None:
            continue
        (otpad, vrsta), sheet, w, l, ref = best
        if vrsta == 0:
            st, b = ref
            b['subs'].append(dict(w3=w, parts=[(l, idx)])); b['used_w'] += kerf + w
        elif vrsta == 1:
            ref['blocks'].append(dict(l=l, used_w=w, subs=[dict(w3=w, parts=[(l, idx)])])); ref['used_l'] += kerf + l
        else:
            sheet['strips'].append(dict(w=w, used_l=l, blocks=[dict(l=l, used_w=w, subs=[dict(w3=w, parts=[(l, idx)])])]))
            sheet['used_w'] += (kerf if len(sheet['strips']) > 1 else 0) + w
        # makni iz zadnje
        for st in zadnja['strips']:
            for b in st['blocks']:
                for sb in b['subs']:
                    for i, (l_, idx_) in enumerate(sb['parts']):
                        if idx_ == idx:
                            del sb['parts'][i]
                            premjesteno = True
                            break
                    else:
                        continue
                    break
                else:
                    continue
                break
            else:
                continue
            break
    if not premjesteno:
        return sheets
    # zadnju ploču presloži iz preostalih komada (bez praznih pod-traka)
    ostatak = _dijelovi_ploce(_ocisti(zadnja), dijelovi)
    nove = rad[:-1]
    if ostatak:
        kand = []
        for nacin in (NACINI_S_GODOM if god else NACINI_BEZ_GODA):
            for fn in (lambda: slozi(ostatak, ploca, trim, kerf, god, nacin, 'w', True), lambda: slozi_bf(ostatak, ploca, trim, kerf, god, nacin, 'w', None),
                       lambda: slozi_kolone(ostatak, ploca, trim, kerf, god, nacin, None, 3, 'fill')):
                try:
                    sh = fn()
                except ValueError:
                    continue
                kand.append((ocijeni(sh, ploca, trim)['m2_naplata'], len(sh), sh))
        if not kand:
            return sheets
        kand.sort(key=lambda k: (k[0], k[1]))
        nove = nove + kand[0][2]
    m2 = ocijeni(nove, ploca, trim)['m2_naplata']
    return nove if m2 < best_m2 - 1e-9 else sheets

def _ocisti(sheet):
    """Ukloni prazne pod-trake / blokove / trake nakon premještanja komada."""
    strips = []
    for st in sheet['strips']:
        blocks = []
        for b in st['blocks']:
            subs = [sb for sb in b['subs'] if sb['parts']]
            if subs:
                b = dict(b, subs=subs)
                blocks.append(b)
        if blocks:
            strips.append(dict(st, blocks=blocks))
    return dict(sheet, strips=strips)

def _zadnja_dfs(dij, ploca, trim, kerf, god, dir_, budzet=1.5):
    """Za komade jedne (načete) ploče: pretraga po širinama traka (DFS s vremenskim budžetom) — traži slaganje na JEDNU ploču
    s najmanjim zbrojem širina traka (= najveći korisni ostatak). Vraća ploču (sheet) ili None."""
    import time
    LIM_W, LIM_L = _os_ploce(ploca, trim, dir_)
    pool = {}
    for idx, W, L, kom in dij:
        pool[(W, L)] = pool.get((W, L), 0) + kom
    idmap = {}
    for idx, W, L, kom in dij:
        idmap.setdefault((W, L), []).extend([idx] * kom)
    t0 = time.time()
    best = [None, LIM_W + 1]                                   # (strips, used_w)

    def sirine(pool_):
        ws = set()
        for (W, L), n in pool_.items():
            if n > 0:
                for (w, l) in _orijentacije(W, L, god, dir_, LIM_W, LIM_L):
                    ws.add(w)
        lst = sorted(ws, reverse=True)
        out = set(lst)
        for a in lst[:8]:
            for b in lst[:8]:
                if b <= a: out.add(a + kerf + b)
        return sorted(out, reverse=True)

    def dfs(pool_, strips, used_w):
        if time.time() - t0 > budzet:
            return
        if not any(n > 0 for n in pool_.values()):
            if used_w < best[1]:
                best[0], best[1] = [dict(st) for st in strips], used_w
            return
        avail = LIM_W - used_w - (kerf if strips else 0)
        probe = []
        for sw in sirine(pool_):
            if sw > avail:
                continue
            for varijanta in (None, 1):
                blocks, area, used_l, taken = _kolona(pool_, sw, LIM_L, kerf, False, god, dir_, LIM_W, __import__('random').Random(varijanta) if varijanta else None)
                if taken:
                    probe.append((-(area), sw, blocks, taken))
        probe.sort(key=lambda t: t[0])
        for _, sw, blocks, taken in probe[:6]:
            if used_w + (kerf if strips else 0) + sw >= best[1]:
                continue
            p2 = dict(pool_)
            for (W, L, w, l) in taken:
                p2[(W, L)] -= 1
            strip = dict(w=sw, used_l=sum(b['l'] for b in blocks) + kerf * (len(blocks) - 1), blocks=blocks)
            dfs(p2, strips + [strip], used_w + (kerf if strips else 0) + sw)

    dfs(pool, [], 0)
    if best[0] is None:
        return None
    # upiši idx-e
    im = {k: list(v) for k, v in idmap.items()}
    for st in best[0]:
        for b in st['blocks']:
            for sub in b['subs']:
                sub['parts'] = [(l, im[(W, L)].pop()) for (l, (W, L, w, l_)) in sub['parts']]
    return dict(dir=dir_, strips=best[0], used_w=best[1])

def dotjeraj_zadnju(sheets, dijelovi, ploca, trim, kerf, god, nacini=None):
    """Zadnja (načeta) ploča odlučuje o korisnom ostatku: njene komade presloži svim načinima i zadrži slaganje s najmanjom
    površinom za naplatu te ploče (jedna ploča, ostatak što veći). Ostale ploče se ne diraju."""
    if not sheets:
        return sheets
    zadnja = sheets[-1]
    dij = _dijelovi_ploce(zadnja, dijelovi)
    nacini = nacini or (NACINI_S_GODOM if god else NACINI_BEZ_GODA)
    best = (ocijeni([zadnja], ploca, trim)['m2_naplata'], zadnja)
    for nacin in nacini:
        for duz in ((True,) if god else (True, False)):
            fns = [lambda so=so: slozi(dij, ploca, trim, kerf, god, nacin, so, duz) for so in ('w', 'l', 'area')]
            fns.append(lambda: slozi_trake(dij, ploca, trim, kerf, god, nacin, duz))
            if duz and sum(k for _, _, _, k in dij) <= 40:
                fns += [lambda oc_=oc_: slozi_kolone(dij, ploca, trim, kerf, god, nacin, None, 3, oc_) for oc_ in ('fill', 'area')]
                fns += [lambda so=so, seed=seed: slozi_bf(dij, ploca, trim, kerf, god, nacin, so, seed) for so in ('w', 'l', 'area') for seed in (None, 0, 1)]
            for fn in fns:
                try:
                    sh = fn()
                except ValueError:
                    continue
                if len(sh) != 1:
                    continue
                m2 = ocijeni(sh, ploca, trim)['m2_naplata']
                if m2 < best[0] - 1e-9:
                    best = (m2, sh[0])
    komada = sum(k for _, _, _, k in dij)
    if komada <= 60:                                          # pretraga po širinama traka (kratki budžet)
        for nacin in nacini:
            d_ = 'S' if nacin == 'poprecno' else 'L'
            sh1 = _zadnja_dfs(dij, ploca, trim, kerf, god, d_, budzet=1.0 if komada <= 25 else 2.0)
            if sh1 is not None:
                m2 = ocijeni([sh1], ploca, trim)['m2_naplata']
                if m2 < best[0] - 1e-9:
                    best = (m2, sh1)
    out = sheets[:-1] + [best[1]]
    return _premjesti_u_prethodne(out, dijelovi, ploca, trim, kerf, god)

def najbolje(dijelovi, ploca=(2800, 2070), trim=10, kerf=16.0, god=True, nacini=None, brzo=False):
    """D-19: probaj dopuštene načine (× varijante slaganja), vrati (najbolja_ploce, ocjena, opis, sve_kandidate).
    Kandidati: slozi() s tri redoslijeda + slozi_trake() (širina trake = kombinacija širina komada); bez goda još i obrnuta orijentacija.
    brzo=True (D-75 „brzo“): samo osnovni kandidati (slozi, trake, kolone bez startova, best-fit bez startova), bez smjera po ploči
    i bez dotjerivanja zadnje ploče — ~1 s i na najvećem nalogu; „najbolje“ je puna pretraga."""
    nacini = nacini or (NACINI_S_GODOM if god else NACINI_BEZ_GODA)
    kand = []
    for nacin in nacini:
        for duz in ((True,) if god else (True, False)):
            varijante = [('slozi/' + so, lambda so=so: slozi(dijelovi, ploca, trim, kerf, god, nacin, so, duz)) for so in ('w', 'l', 'area')]
            varijante.append(('trake', lambda: slozi_trake(dijelovi, ploca, trim, kerf, god, nacin, duz)))
            if duz:                                      # kolone i best-fit sami biraju orijentaciju po komadu (korak 5) — jednom po načinu
                komada = sum(k for _, _, _, k in dijelovi)
                if brzo:
                    komada = 10 ** 6                             # kao vrlo velik nalog: bez startova, bez mixa
                for so in ('w', 'l', 'area'):
                    for seed in ((None, 0) if komada > 120 else (None, 0, 1, 2)) + (tuple(range(3, 12)) if komada <= 60 else ()):
                        varijante.append(('bf/%s%s' % (so, '' if seed is None else '/s%d' % seed),
                                          lambda so=so, seed=seed: slozi_bf(dijelovi, ploca, trim, kerf, god, nacin, so, seed)))
                for oc_, pref in ((('fill', 'w'), ('fill', 'l')) if komada > 120 else (('fill', 'w'), ('fill', 'l'), ('area', 'w'))):
                    varijante.append(('kolone/%s/%s' % (oc_, pref), lambda oc_=oc_, pref=pref: slozi_kolone(dijelovi, ploca, trim, kerf, god, nacin, None, 3, oc_, pref)))
                if nacin == 'uzduzno' and komada <= 250:                       # smjer po ploči — jednom po nalogu (ne ovisi o načinu)
                    for oc_, pref in (('fill', 'w'), ('fill', 'l')):
                        varijante.append(('mix/%s/%s' % (oc_, pref), lambda oc_=oc_, pref=pref: slozi_kolone_mix(dijelovi, ploca, trim, kerf, god, None, oc_, pref)))
                for seed in (range(6) if komada <= 40 else range(2) if komada <= 80 else ()):
                    for pref in (('w', 'l') if komada <= 40 else ('w',)):
                        varijante.append(('kolone/fill/%s/s%d' % (pref, seed), lambda seed=seed, pref=pref: slozi_kolone(dijelovi, ploca, trim, kerf, god, nacin, seed, 3, 'fill', pref)))
            for ime, fn in varijante:
                try:
                    sh = fn()
                except ValueError:
                    continue
                oc = ocijeni(sh, ploca, trim)
                kand.append((oc['m2_naplata'], oc['ploca'], oc['rezova'], nacin, ime, duz, sh, oc))
    if kand and not brzo:                                # zadnju ploču najboljih kandidata presloži za veći ostatak (korak 5)
        kand.sort(key=lambda k: (k[0], k[1], k[2]))
        for k in kand[:3]:
            sh = dotjeraj_zadnju(k[6], dijelovi, ploca, trim, kerf, god, nacini)
            oc = ocijeni(sh, ploca, trim)
            if oc['m2_naplata'] < k[0] - 1e-9:
                kand.append((oc['m2_naplata'], oc['ploca'], oc['rezova'], k[3], k[4] + '/zadnja', k[5], sh, oc))
    if not kand:
        raise ValueError('nijedan način ne može složiti nalog')
    kand.sort(key=lambda k: (k[0], k[1], k[2]))
    b = kand[0]
    return b[6], b[7], '%s/%s%s' % (b[3], b[4], '' if b[5] else '/poprijeko'), kand

def optimiraj(dijelovi, ploca=(2800, 2070), trim=10, kerf=5.0, god=True):
    """Kompatibilnost: jednostavno uzdužno slaganje (kao prva verzija)."""
    return slozi(dijelovi, ploca, trim, kerf, god, 'uzduzno', 'w', True)

def statistika(sheets, dijelovi, ploca=(2800, 2070)):
    area_parts = sum(W * L * kom for _, W, L, kom in dijelovi) / 1e6
    n = len(sheets); gross = n * ploca[0] * ploca[1] / 1e6
    return dict(ploca=n, m2_dijelova=round(area_parts, 3), m2_bruto=round(gross, 3), iskoristenje=round(area_parts / gross, 4) if n else None)

def napravi_cpo(els, prog, kupac, material=None, ploca=(2800, 2070), trim=10, kerf=5.0, when=None, price=49.0,
                kerf_slaganja=None, nacini=None, sheets=None):
    """els: elementi iz nalog_io (isti materijal). Sheme: D-19 izbor (najbolje) s kerf_slaganja (zadano = kerf obračuna 16),
    ili unaprijed zadane 'sheets'. U CPO se upisuje kerf pile (zadano 5,00 kao PW). Vraća (bytes, statistika, greške, ocjena, nacin)."""
    when = when or datetime.now()
    material = _san(material or els[0]['mat'])
    deb = float(els[0]['deb'])
    god = any(int(e.get('god', 0)) for e in els)
    dijelovi = [(k + 1, float(e['W']), float(e['L']), int(e['kom'])) for k, e in enumerate(els)]
    nacin = 'zadano'
    if sheets is None:
        sheets, oc, nacin, _ = najbolje(dijelovi, ploca, trim, kerf_slaganja or kerf, god, nacini)   # slaganje s kerfom pile (D-72), ocjena s 16
    else:
        oc = ocijeni(sheets, ploca, trim)
    n = len(sheets)
    d = dict(prog=str(prog), material=material[:52], date=when.strftime('%d.%m.%Y. '), time=when.strftime('%H:%M'),
             ctl1=dict(a='M', b='M', grain='Y' if god else 'N', c=1, d=0), ctl2=[kerf, kerf, 0.0, 0.63, 0.0, 0.0], ctl3=0.0,
             thk=(deb, deb * 5), sta1=[0, 0, 0], sta2=[0, 0, 0], inv=[], ord=[], prt=[], pat=[])
    for _ in sheets:
        d['inv'].append(dict(code=999, qty=n, price=price, W=float(ploca[1]), L=float(ploca[0]), trim=[float(trim)] * 4,
                             name=material[:24], v=[0, 0, 0]))
    for k, e in enumerate(els):
        idx = k + 1
        nap = _san(e.get('napomena', ''))[:40]
        d['ord'].append(dict(qty=int(e['kom']), qty2=int(e['kom']), W=float(e['W']), L=float(e['L']), grain='H', flag='Y',
                             price=5.995, note=nap, a=1, idx=idx))
        tr = e.get('traka', {})
        names = [_san(tr.get(s, '')) for s in ('O', 'D', 'G', 'L')]   # PRT3 maska = [dolje, desno, gore, lijevo]
        edges = [(nm[:8], nm[:20], nm[:10]) for nm in names]
        d['prt'].append(dict(qty=int(e['kom']), n=k, W=float(e['W']), L=float(e['L']), k=1, note=nap, note2='',
                             name='Element %d' % idx, x='', mask=''.join('1' if nm else '0' for nm in names), edges=edges,
                             cust=_san(kupac)[:16], prt4=['', '', '', '', ''], p5=('H', 'N', idx, idx)))
    for i, s in enumerate(sheets):
        d['pat'].append(dict(no=i + 1, dir=s['dir'], qty=1, q2=1, cuts=sheme_u_cuts(s)))
    st = statistika(sheets, dijelovi, ploca); st.update(m2_naplata=oc['m2_naplata'], ostaci=oc['ostaci'], nacin=nacin)
    return cpo_rw.write(d), st, cpo_rw.validate(d), oc, nacin

def _san(s):
    """PW u CPO zamjenjuje ',' i '/' s '-' (polja su odvojena zarezom); PW ne prikazuje dijakritike."""
    from hub.formati import nalog_io
    return nalog_io.bez_dijakritika(s).replace(',', '-').replace('/', '-')

# ------------------------------------------------------------------ "pametne trake" (širina trake = kombinacija širina komada, kao PW)
def _stack_fill(rem, sw, LIM_L, kerf, samo_trake=False):
    """Greedy punjenje jedne trake širine sw: blokovi duž trake; u bloku stog pod-traka (širine ≤ sw). rem = dict (w,l)->kom.
    Vraća (blocks, used_area, used_l). Ne mijenja rem — vraća i popis potrošenih komada."""
    used_l = 0; blocks = []; taken = []
    local = dict(rem)
    def take(w, l):
        local[(w, l)] -= 1
        if local[(w, l)] == 0: del local[(w, l)]
        taken.append((w, l))
    while True:
        avail_l = LIM_L - used_l - (kerf if blocks else 0)
        # najdulji komad koji stane u traku (širina ≤ sw) — kod 'trake' samo w == sw
        cands = [(l, w) for (w, l) in local if w <= sw and l <= avail_l and (w == sw or not samo_trake)]
        if not cands: break
        l0, w0 = max(cands)
        take(w0, l0)
        block = dict(l=l0, used_w=w0, subs=[dict(w3=w0, parts=[(l0, None)])])
        # stog: dopuni širinu bloka pod-trakama komada s l ≤ l0
        if not samo_trake:
            while True:
                aw = sw - block['used_w'] - kerf
                c2 = [(l, w) for (w, l) in local if w <= aw and l <= l0]
                if not c2: break
                # najveći po površini koji stane; unutar pod-trake dopuni i po duljini (razina 4)
                l1, w1 = max(c2, key=lambda t: (t[0] * t[1], t[0]))
                take(w1, l1)
                sub = dict(w3=w1, parts=[(l1, None)]); ul = l1
                while True:
                    al = l0 - ul - kerf
                    c3 = [(l, w) for (w, l) in local if w == w1 and l <= al]
                    if not c3: break
                    l2, w2 = max(c3); take(w2, l2); sub['parts'].append((l2, None)); ul += kerf + l2
                block['subs'].append(sub); block['used_w'] += kerf + w1
        # razina 4 u prvoj pod-traci (isti w0, kraći komadi) — samo ako ne 'trake'
        if not samo_trake:
            ul = l0; sub = block['subs'][0]
            while True:
                al = l0 - ul - kerf
                c3 = [(l, w) for (w, l) in local if w == w0 and l <= al]
                if not c3: break
                l2, w2 = max(c3); take(w2, l2); sub['parts'].append((l2, None)); ul += kerf + l2
        blocks.append(block); used_l += (kerf if len(blocks) > 1 else 0) + l0
    area = sum(l * w for (w, l) in taken)
    return blocks, area, used_l, taken

def slozi_trake(dijelovi, ploca=(2800, 2070), trim=10, kerf=16.0, god=True, nacin='uzduzno', dulja_uz_traku=True, max_komb=3):
    """Širina trake bira se kao najbolja kombinacija širina komada (do max_komb pod-traka) po popunjenosti trake."""
    dir_ = 'S' if nacin == 'poprecno' else 'L'
    LIM_W, LIM_L = _os_ploce(ploca, trim, dir_)
    samo = nacin == 'trake'
    rem = {}; idmap = {}
    for idx, W, L, kom in dijelovi:
        w, l = _orijentiraj(W, L, god, dir_, dulja_uz_traku)
        if w > LIM_W or l > LIM_L:
            if not god and l <= LIM_W and w <= LIM_L: w, l = l, w
            else: raise ValueError('dio %d ne stane' % idx)
        rem[(w, l)] = rem.get((w, l), 0) + kom
        idmap.setdefault((w, l), []).extend([idx] * kom)
    widths = sorted(set(w for (w, l) in rem), reverse=True)
    sheets = []
    while rem:
        sheet = dict(dir=dir_, strips=[], used_w=0); sheets.append(sheet)
        while rem:
            avail_w = LIM_W - sheet['used_w'] - (kerf if sheet['strips'] else 0)
            # kandidati širine trake
            cands = set()
            ws = sorted(set(w for (w, l) in rem), reverse=True)
            for a in ws:
                if a <= avail_w: cands.add(a)
                if not samo and max_komb >= 2:
                    for b in ws:
                        if a + kerf + b <= avail_w: cands.add(a + kerf + b)
                        if max_komb >= 3:
                            for c in ws:
                                if a + kerf + b + kerf + c <= avail_w: cands.add(a + kerf + b + kerf + c)
            if not cands: break
            best = None
            for sw in cands:
                blocks, area, used_l, taken = _stack_fill(rem, sw, LIM_L, kerf, samo)
                if not taken: continue
                score = area / (sw * LIM_L)          # popunjenost trake
                key = (score, area)
                if best is None or key > best[0]: best = (key, sw, blocks, taken)
            if best is None: break
            _, sw, blocks, taken = best
            for (w, l) in taken:
                rem[(w, l)] -= 1
                if rem[(w, l)] == 0: del rem[(w, l)]
            # upiši idx-e u blokove
            for b in blocks:
                for sub in b['subs']:
                    sub['parts'] = [(l, idmap[(sub['w3'], l)].pop()) for (l, _) in sub['parts']]
            strip = dict(w=sw, used_l=sum(b['l'] for b in blocks) + kerf * (len(blocks) - 1), blocks=blocks)
            sheet['strips'].append(strip)
            sheet['used_w'] += (kerf if len(sheet['strips']) > 1 else 0) + sw
        if not sheet['strips']:
            raise ValueError('komad ne stane na praznu ploču')
    return sheets


# ------------------------------------------------------------------ "kolone" (korak 5, D-17/3): traka = kolona, orijentacija po komadu, više startova
def _orijentacije(W, L, god, dir_, LIM_W, LIM_L):
    """Dopuštene (w, l) orijentacije komada W×L u shemi dir_: s godom jedna (D-19), bez goda obje koje stanu."""
    if god:
        o = [(W, L) if dir_ == 'L' else (L, W)]
    else:
        o = [(W, L), (L, W)] if W != L else [(W, L)]
    return [(w, l) for (w, l) in o if w <= LIM_W and l <= LIM_L]

def _kolona(pool, sw, LIM_L, kerf, samo_trake, god, dir_, LIM_W, rnd=None, pref='w'):
    """Napuni jednu traku širine sw iz pool-a {(W,L): kom}: blokovi duž trake (najdulji komad koji stane, orijentacija slobodna bez goda),
    u bloku stog pod-traka (razina 3) i komadi uz pod-traku (razina 4). Vraća (blocks, area, used_l, taken[(W,L,w,l)])."""
    local = {k: n for k, n in pool.items() if n > 0}; taken = []; blocks = []; used_l = 0
    ori = {k: _orijentacije(k[0], k[1], god, dir_, LIM_W, LIM_L) for k in local}
    def opcije(max_w, max_l, tocno_w=None):
        out = []
        for k, n in local.items():
            if n <= 0: continue
            for (w, l) in ori[k]:
                if l <= max_l and (w == tocno_w if tocno_w is not None else w <= max_w):
                    out.append((l, w, k[0], k[1]))
        return out
    def take(W, L, w, l):
        local[(W, L)] -= 1
        taken.append((W, L, w, l))
    while True:
        avail_l = LIM_L - used_l - (kerf if blocks else 0)
        c = opcije(sw, avail_l, sw if samo_trake else None)
        if not c: break
        if rnd is not None and len(c) > 1 and rnd.random() < 0.25:
            l0, w0, W0, L0 = rnd.choice(sorted(c, reverse=True)[:3])
        else:
            l0, w0, W0, L0 = max(c, key=(lambda t: (t[0] * t[1] if not samo_trake else t[0], t[1], t[0])) if pref == 'w' else
                                        (lambda t: (t[0] * t[1] if not samo_trake else t[0], t[0])))     # najveći, pa širi (puni širinu) ili dulji
        take(W0, L0, w0, l0)
        block = dict(l=l0, used_w=w0, subs=[dict(w3=w0, parts=[(l0, (W0, L0, w0, l0))])])
        if not samo_trake:
            # razina 4 u prvoj pod-traci: isti w, kraći komadi
            ul = l0
            while True:
                c3 = opcije(w0, l0 - ul - kerf, w0)
                if not c3: break
                l2, w2, W2, L2 = max(c3); take(W2, L2, w2, l2); block['subs'][0]['parts'].append((l2, (W2, L2, w2, l2))); ul += kerf + l2
            # stog pod-traka do širine trake
            while True:
                aw = sw - block['used_w'] - kerf
                c2 = opcije(aw, l0)
                if not c2: break
                l1, w1, W1, L1 = max(c2, key=lambda t: (t[0] * t[1], t[1], t[0]))
                take(W1, L1, w1, l1)
                sub = dict(w3=w1, parts=[(l1, (W1, L1, w1, l1))]); ul = l1
                while True:
                    c3 = opcije(w1, l0 - ul - kerf, w1)
                    if not c3: break
                    l2, w2, W2, L2 = max(c3); take(W2, L2, w2, l2); sub['parts'].append((l2, (W2, L2, w2, l2))); ul += kerf + l2
                block['subs'].append(sub); block['used_w'] += kerf + w1
        blocks.append(block); used_l += (kerf if len(blocks) > 1 else 0) + l0
    area = sum(w * l for (_, _, w, l) in taken)
    return blocks, area, used_l, taken

KAP_KOM, KAP_TOP, KAP_SW = 120, 30, 200

def slozi_kolone_mix(dijelovi, ploca=(2800, 2070), trim=10, kerf=16.0, god=True, seed=None, ocjena='fill', pref='w'):
    """Kolone sa smjerom po PLOČI: za svaku novu ploču slože se obje sheme (L i S) na preostalim komadima i zadrži ona
    koja na tu ploču stavi više površine (PW miješa smjerove unutar posla, npr. I_02024: L, L, S, L)."""
    pool = {}
    for idx, W, L, kom in dijelovi:
        pool[(idx, W, L)] = kom
    sheets = []
    while any(n > 0 for n in pool.values()):
        dij = [(idx, W, L, n) for (idx, W, L), n in pool.items() if n > 0]
        best = None
        for nacin in ('uzduzno', 'poprecno'):
            try:
                sh = slozi_kolone(dij, ploca, trim, kerf, god, nacin, seed, 3, ocjena, pref, max_ploca=1)
            except ValueError:
                continue
            prva = sh[0]
            area = sum(l * sb['w3'] for st in prva['strips'] for b in st['blocks'] for sb in b['subs'] for (l, i) in sb['parts'])
            kljuc = -area                               # smjer koji na ovu ploču stavi više površine
            if best is None or kljuc < best[0]:
                best = (kljuc, prva)
        if best is None:
            raise ValueError('komad ne stane na praznu ploču')
        prva = best[1]
        sheets.append(prva)
        mjere = {idx: (W, L) for idx, W, L, _ in dijelovi}
        for st in prva['strips']:
            for b in st['blocks']:
                for sb in b['subs']:
                    for l, idx in sb['parts']:
                        pool[(idx,) + mjere[idx]] -= 1
    return sheets

def slozi_kolone(dijelovi, ploca=(2800, 2070), trim=10, kerf=16.0, god=True, nacin='uzduzno', seed=None, max_komb=3, ocjena='fill', pref='w', max_ploca=None):
    """Slaganje po kolonama: širina trake = najbolja kombinacija širina (do max_komb), orijentacija se bira po komadu (bez goda),
    traka se bira po popunjenosti ('fill') ili površini ('area'); seed ≠ None dodaje nasumičnost za više startova."""
    import random
    rnd = random.Random(seed) if seed is not None else None
    dir_ = 'S' if nacin == 'poprecno' else 'L'
    LIM_W, LIM_L = _os_ploce(ploca, trim, dir_)
    samo = nacin == 'trake'
    pool = {}; idmap = {}
    for idx, W, L, kom in dijelovi:
        if not _orijentacije(W, L, god, dir_, LIM_W, LIM_L):
            raise ValueError('dio %d (%sx%s) ne stane na ploču %sx%s u shemi %s' % (idx, W, L, ploca[0], ploca[1], dir_))
        pool[(W, L)] = pool.get((W, L), 0) + kom
        idmap.setdefault((W, L), []).extend([idx] * kom)
    sheets = []
    velik = sum(pool.values()) > KAP_KOM                                   # veliki nalozi: kombinacije samo od najčešćih širina (brzina)
    while any(n > 0 for n in pool.values()):
        sheet = dict(dir=dir_, strips=[], used_w=0); sheets.append(sheet)
        while True:
            avail_w = LIM_W - sheet['used_w'] - (kerf if sheet['strips'] else 0)
            brojac = {}
            for (W, L), n in pool.items():
                if n > 0:
                    for (w, l) in _orijentacije(W, L, god, dir_, LIM_W, LIM_L):
                        brojac[w] = brojac.get(w, 0) + n
            ws = sorted(brojac, reverse=True)
            cands = {a for a in ws if a <= avail_w}
            top = sorted(ws, key=lambda w: -brojac[w])[:KAP_TOP] if velik else ws
            if not samo and max_komb >= 2:
                for a in top:
                    for b in top:
                        if b > a: continue
                        if a + kerf + b <= avail_w: cands.add(a + kerf + b)
                        if max_komb >= 3:
                            for c in top:
                                if c <= b and a + kerf + b + kerf + c <= avail_w: cands.add(a + kerf + b + kerf + c)
            best = None
            for sw in (sorted(cands, reverse=True)[:KAP_SW] if velik else sorted(cands, reverse=True)):
                blocks, area, used_l, taken = _kolona(pool, sw, LIM_L, kerf, samo, god, dir_, LIM_W, rnd, pref)
                if not taken: continue
                fill = area / (sw * LIM_L)
                key = (fill, area) if ocjena == 'fill' else (area, fill)
                if rnd is not None:
                    key = (key[0] * (1 + rnd.uniform(-0.08, 0.08)), key[1])
                if best is None or key > best[0]: best = (key, sw, blocks, taken)
            if best is None: break
            _, sw, blocks, taken = best
            for (W, L, w, l) in taken:
                pool[(W, L)] -= 1
            for b in blocks:
                for sub in b['subs']:
                    sub['parts'] = [(l, idmap[(W, L)].pop()) for (l, (W, L, w, l_)) in sub['parts']]
            sheet['strips'].append(dict(w=sw, used_l=sum(b['l'] for b in blocks) + kerf * (len(blocks) - 1), blocks=blocks))
            sheet['used_w'] += (kerf if len(sheet['strips']) > 1 else 0) + sw
        if not sheet['strips']:
            raise ValueError('komad ne stane na praznu ploču')
        if max_ploca and len(sheets) >= max_ploca:                          # mix: samo prva ploča (smjer po ploči)
            break
    return sheets


def slozi_bf(dijelovi, ploca=(2800, 2070), trim=10, kerf=16.0, god=True, nacin='uzduzno', sort='w', seed=None):
    """Kao `slozi`, ali s najboljim mjestom (best-fit) umjesto prvog koje stane i s izborom orijentacije po komadu (bez goda):
    za svaki komad se probaju obje orijentacije na svim mjestima (pod-traka, blok, nova traka) i uzme ono koje ostavlja najmanji otpad."""
    import random
    rnd = random.Random(seed) if seed is not None else None
    dir_ = 'S' if nacin == 'poprecno' else 'L'
    LIM_W, LIM_L = _os_ploce(ploca, trim, dir_)
    samo_trake = nacin == 'trake'
    pieces = []
    for idx, W, L, kom in dijelovi:
        ors = _orijentacije(W, L, god, dir_, LIM_W, LIM_L)
        if not ors:
            raise ValueError('dio %d (%sx%s) ne stane na ploču %sx%s u shemi %s' % (idx, W, L, ploca[0], ploca[1], dir_))
        pieces += [(W, L, idx, ors)] * kom
    if sort == 'w':
        pieces.sort(key=lambda p: (-max(p[0], p[1]), -min(p[0], p[1])))
    elif sort == 'l':
        pieces.sort(key=lambda p: (-min(p[0], p[1]), -max(p[0], p[1])))
    else:
        pieces.sort(key=lambda p: (-p[0] * p[1], -max(p[0], p[1])))
    if rnd is not None:
        for i in range(len(pieces) - 1):                # blaga zamjena susjeda
            if rnd.random() < 0.3:
                pieces[i], pieces[i + 1] = pieces[i + 1], pieces[i]
    sheets = []

    def kandidati(sheet, w, l):
        out = []                                        # (otpad, vrsta, ref)
        if not samo_trake:
            for st in sheet['strips']:
                for b in st['blocks']:
                    if l <= b['l'] and b['used_w'] + kerf + w <= st['w']:
                        out.append(((b['l'] - l) * w + (st['w'] - b['used_w'] - kerf - w) * 0.1, 0, (st, b)))
        for st in sheet['strips']:
            if (w == st['w'] if samo_trake else w <= st['w']) and st['used_l'] + kerf + l <= LIM_L:
                out.append(((st['w'] - w) * l, 1, st))
        if sheet['used_w'] + (kerf if sheet['strips'] else 0) + w <= LIM_W:
            out.append((w * (LIM_L - l) * 0.5 + 1e6, 2, None))     # nova traka je najskuplja
        return out

    def stavi(sheet, w, l, idx, vrsta, ref):
        if vrsta == 0:
            st, b = ref
            b['subs'].append(dict(w3=w, parts=[(l, idx)])); b['used_w'] += kerf + w
        elif vrsta == 1:
            ref['blocks'].append(dict(l=l, used_w=w, subs=[dict(w3=w, parts=[(l, idx)])])); ref['used_l'] += kerf + l
        else:
            sheet['strips'].append(dict(w=w, used_l=l, blocks=[dict(l=l, used_w=w, subs=[dict(w3=w, parts=[(l, idx)])])]))
            sheet['used_w'] += (kerf if len(sheet['strips']) > 1 else 0) + w

    for W, L, idx, ors in pieces:
        best = None
        for si, sheet in enumerate(sheets):
            for (w, l) in ors:
                for otpad, vrsta, ref in kandidati(sheet, w, l):
                    key = (si if vrsta == 2 else -1, otpad)          # nova traka na kasnijoj ploči je lošija od bilo kojeg mjesta u postojećoj traci
                    if best is None or key < best[0]:
                        best = (key, sheet, w, l, vrsta, ref)
        if best is None:
            sheet = dict(dir=dir_, strips=[], used_w=0); sheets.append(sheet)
            w, l = max(ors, key=lambda o: o[1])
            if not kandidati(sheet, w, l):
                w, l = min(ors, key=lambda o: o[1])
            stavi(sheet, w, l, idx, 2, None)
        else:
            _, sheet, w, l, vrsta, ref = best
            stavi(sheet, w, l, idx, vrsta, ref)
    return sheets
