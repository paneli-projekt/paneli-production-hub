"""pila_optimizator.py — giljotinski optimizator za pilu (D-16/D-17) + izbor načina po pravilu D-19.

Daje stablo rezova u obliku koji Selco OSI čita (CUT1 razine 1..4) i CPO datoteku preko cpo_rw; površina za
naplatu računa se PW-metodom (obracun.py). Potvrđeno na 50 PW datoteka: dio na razini n ima točno dimenzije
(pozicija roditelja, pozicija reza); shema 'L' = trake uz duljinu ploče (rez razine 1 paralelan s dužom stranicom),
'S' = trake poprijeko.

Načini (kao u PanelWizardu, desni klik na žarulju):
  'uzduzno'  → shema L, trake razine 1 uz duljinu (2800); u traci blokovi (razina 2), pod-trake (3), komadi (4)
  'poprecno' → shema S, trake razine 1 poprijeko (uz širinu 2070)
  'trake'    → shema L, ali u traci samo komadi ISTE širine (bez pod-traka razine 3/4) — jednostavnije rezanje
Svaki način se vrti u više varijanti (redoslijed komada, orijentacija bez goda) i uzima se varijanta s najmanjom
površinom za naplatu, pa manje ploča, pa manje rezova.  D-19: s godom samo 'uzduzno' + 'trake'; bez goda i 'poprecno'.

Orijentacija komada: (w, l) = (mjera uz os širine trake, mjera uz traku). S godom duljina dijela (L) mora ležati uz
duljinu ploče: u L-shemi (w,l)=(W,L), u S-shemi (w,l)=(L,W). Bez goda obje orijentacije su dopuštene.
"""
from hub.formati import cpo_rw
from hub.optimizacija import obracun
from datetime import datetime

NACINI_S_GODOM = ('uzduzno', 'trake')
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

def najbolje(dijelovi, ploca=(2800, 2070), trim=10, kerf=16.0, god=True, nacini=None):
    """D-19: probaj dopuštene načine (× varijante slaganja), vrati (najbolja_ploce, ocjena, opis, sve_kandidate).
    Kandidati: slozi() s tri redoslijeda + slozi_trake() (širina trake = kombinacija širina komada); bez goda još i obrnuta orijentacija."""
    nacini = nacini or (NACINI_S_GODOM if god else NACINI_BEZ_GODA)
    kand = []
    for nacin in nacini:
        for duz in ((True,) if god else (True, False)):
            varijante = [('slozi/' + so, lambda so=so: slozi(dijelovi, ploca, trim, kerf, god, nacin, so, duz)) for so in ('w', 'l', 'area')]
            varijante.append(('trake', lambda: slozi_trake(dijelovi, ploca, trim, kerf, god, nacin, duz)))
            for ime, fn in varijante:
                try:
                    sh = fn()
                except ValueError:
                    continue
                oc = ocijeni(sh, ploca, trim)
                kand.append((oc['m2_naplata'], oc['ploca'], oc['rezova'], nacin, ime, duz, sh, oc))
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
        sheets, oc, nacin, _ = najbolje(dijelovi, ploca, trim, kerf_slaganja or obracun.KERF_OBRACUN, god, nacini)
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
