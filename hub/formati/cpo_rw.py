"""cpo_rw.py — čitanje i pisanje Biesse/Selco OSI .cpo datoteka (format koji PanelWizard šalje pili Sektor 450).

Reverse-engineering "crne kutije" iz 50 CPO datoteka testnih naloga (Paneli Production Hub, D-10 / D-16).
Nije korišten kod PanelWizarda — samo usporedba izlaznih datoteka.

Struktura (po redcima, CRLF, cp1250, fiksne širine polja, datoteka završava 'END\r\n'):
  HDR1,<program>,<materijal:52>            HDR2,<datum 'dd.mm.yyyy. '>,<vrijeme hh:mm:43>   HDR3 (konst.)
  CTL1,M,M,<god Y/N>,   1,0                CTL2,<kerf>,<kerf>,0,0.63,0,0   CTL3, THK1,<debljina>,<visina paketa=5×deb>
  STA1, STA2 (konst.)
  INV1,  999,<n ploča>,  49.000,<W>,<L>,<trim×4>   INV2,<naziv:24>,0,0,0   INV3      — jedan INV blok PO SHEMI (n ploča ponovljeno)
  ORD1,<kom>,<kom>,<W>,<L>,H,Y   ORD2,<cijena 5.995>,<napomena:40>   ORD3,1,<rb>     — jedan blok po ELEMENTU (naručeno)
  PRT1,<kom>,<rb-1>,<W>,<L>, 1,<napomena:40>,<:40>,<Element N:16>,<:16>   PRT2   PRT3,<maska rubova>,4×(šifra:8,naziv:20,kratki:10)
  PRT4,<kupac/nalog:16>,...   PRT5,H,N,<rb>,<rb>                                   — jedan blok po ELEMENTU (dijelovi)
  PAT1,<br. sheme:02>,<L|S>,1,1   PAT2..PAT5 (konst.)   BCUT   CUT1,<razina:02>,<pozicija>,<1 ako je dio>,<rb dijela:03>
  END

Stablo rezova (potvrđeno na svih 1.115 dijelova): dio na razini n ima dimenzije točno = (pozicija reza razine n-1, pozicija reza razine n).
  Shema 'L': rez razine 1 ide paralelno s dužom stranicom ploče (trake širine <pos> × puna duljina);
  shema 'S': rez razine 1 okomito (trake <pos> × puna širina). Kod materijala s godom (CTL1 = Y) duljina dijela
  uvijek leži uz duljinu ploče (2800).
"""
import os, re, glob, sys

ENC = 'cp1250'

def _f(s): return float(s.strip())
def _i(s): return int(s.strip())

def parse(path_or_bytes):
    raw = open(path_or_bytes, 'rb').read() if isinstance(path_or_bytes, str) else path_or_bytes
    txt = raw.decode(ENC)
    lines = txt.split('\r\n')
    d = dict(inv=[], ord=[], prt=[], pat=[])
    for line in lines:
        tag = line[:4]
        rest = line[5:]
        if tag == 'HDR1':
            d['prog'] = rest[:rest.index(',')]
            d['material'] = rest[rest.index(',') + 1:].rstrip()
        elif tag == 'HDR2':
            d['date'], d['time'] = rest[:12], rest[13:].rstrip()
        elif tag == 'HDR3':
            d['hdr3'] = rest
        elif tag == 'CTL1':
            f = rest.split(','); d['ctl1'] = dict(a=f[0], b=f[1], grain=f[2], c=_i(f[3]), d=_i(f[4]))
        elif tag == 'CTL2':
            d['ctl2'] = [_f(x) for x in rest.split(',')]
        elif tag == 'CTL3':
            d['ctl3'] = _f(rest)
        elif tag == 'THK1':
            f = rest.split(','); d['thk'] = (_f(f[0]), _f(f[1]))
        elif tag == 'STA1':
            d['sta1'] = [_i(x) for x in rest.split(',')]
        elif tag == 'STA2':
            d['sta2'] = [_f(x) for x in rest.split(',')]
        elif tag == 'INV1':
            f = rest.split(',')
            d['inv'].append(dict(code=_i(f[0]), qty=_i(f[1]), price=_f(f[2]), W=_f(f[3]), L=_f(f[4]),
                                 trim=[_f(x) for x in f[5:9]]))
        elif tag == 'INV2':
            f = rest.split(','); d['inv'][-1]['name'] = f[0].rstrip(); d['inv'][-1]['v'] = [_f(x) for x in f[1:4]]
        elif tag == 'INV3':
            d['inv'][-1]['inv3'] = rest
        elif tag == 'ORD1':
            f = rest.split(',')
            d['ord'].append(dict(qty=_i(f[0]), qty2=_i(f[1]), W=_f(f[2]), L=_f(f[3]), grain=f[4], flag=f[5].strip()))
        elif tag == 'ORD2':
            f = rest.split(','); d['ord'][-1]['price'] = _f(f[0]); d['ord'][-1]['note'] = f[1].rstrip()
        elif tag == 'ORD3':
            f = rest.split(','); d['ord'][-1]['a'] = _i(f[0]); d['ord'][-1]['idx'] = _i(f[1])
        elif tag == 'PRT1':
            f = rest.split(',')
            d['prt'].append(dict(qty=_i(f[0]), n=_i(f[1]), W=_f(f[2]), L=_f(f[3]), k=_i(f[4]), note=f[5].rstrip(),
                                 note2=f[6].rstrip(), name=f[7].rstrip(), x=f[8].rstrip()))
        elif tag == 'PRT2':
            d['prt'][-1]['prt2'] = rest
        elif tag == 'PRT3':
            f = rest.split(',')
            d['prt'][-1]['mask'] = f[0].strip()
            d['prt'][-1]['edges'] = [(f[1 + 3 * i].rstrip(), f[2 + 3 * i].rstrip(), f[3 + 3 * i].rstrip()) for i in range(4)]
        elif tag == 'PRT4':
            f = rest.split(','); d['prt'][-1]['cust'] = f[0].rstrip(); d['prt'][-1]['prt4'] = [x.rstrip() for x in f[1:]]
        elif tag == 'PRT5':
            f = rest.split(','); d['prt'][-1]['p5'] = (f[0], f[1], _i(f[2]), _i(f[3]))
        elif tag == 'PAT1':
            f = rest.split(',')
            d['pat'].append(dict(no=_i(f[0]), dir=f[1], qty=_i(f[2]), q2=_i(f[3]), cuts=[]))
        elif tag == 'PAT2':
            d['pat'][-1]['pat2'] = rest
        elif tag == 'PAT3':
            d['pat'][-1]['pat3'] = rest
        elif tag == 'PAT4':
            d['pat'][-1]['pat4'] = rest
        elif tag == 'PAT5':
            d['pat'][-1]['pat5'] = rest
        elif tag == 'CUT1':
            f = rest.split(',')
            d['pat'][-1]['cuts'].append((_i(f[0]), _f(f[1]), f[2] == '1', _i(f[3])))
    return d

# ------------------------------------------------------------------ pisanje
HDR3 = '  0002,1.00,OP10,BOTH'
INV3 = '                ,                ,0'
PRT2 = ' 0, ,' + ' ' * 50 + ', '
PAT2 = '100.000,        0.0000,        0.0000,        0.0000,       1.000'
PAT3 = '    0,    0,    0,    0'
PAT4 = '     0.00,     0.00,     0.00'
PAT5 = '     0,     0,       0.000,       0.000'

def _edge(e, wsh=10):
    return '%-8s,%-20s,%-*s' % (e[0][:8], e[1][:20], wsh, e[2][:wsh])

def write(d):
    """Vraća bytes (cp1250, CRLF) u identičnom formatu kao PanelWizard."""
    o = []
    o.append('HDR1,%s,%-52s' % (d['prog'], d['material'][:52]))
    o.append('HDR2,%-12s,%-43s' % (d['date'], d['time']))
    o.append('HDR3,' + d.get('hdr3', HDR3))
    c = d['ctl1']
    o.append('CTL1,%s,%s,%s,%4d,%d' % (c['a'], c['b'], c['grain'], c['c'], c['d']))
    o.append('CTL2,' + ','.join('%9.2f' % x for x in d['ctl2']) + '  ')
    o.append('CTL3,%9.2f' % d.get('ctl3', 0.0))
    o.append('THK1,%9.2f,%9.2f  ' % d['thk'])
    o.append('STA1,' + ','.join('%6d' % x for x in d.get('sta1', [0, 0, 0])))
    o.append('STA2,' + ','.join('%11.3f' % x for x in d.get('sta2', [0, 0, 0])))
    for s in d['inv']:
        o.append('INV1,%5d,%5d,%8.3f,%9.2f,%9.2f,%s' % (s['code'], s['qty'], s['price'], s['W'], s['L'],
                 ','.join('%9.2f' % t for t in s['trim'])) + ' ' * 14)
        o.append('INV2,%-24s,%s' % (s['name'][:24], ','.join('%14.3f' % v for v in s.get('v', [0, 0, 0]))) + ' ' * 25)
        o.append('INV3,' + s.get('inv3', INV3))
    for r in d['ord']:
        o.append('ORD1,%5d,%5d,%9.2f,%9.2f,%s,%-3s' % (r['qty'], r['qty2'], r['W'], r['L'], r['grain'], r['flag']))
        o.append('ORD2,%8.3f,%-40s,     ' % (r.get('price', 5.995), r.get('note', '')[:40]))
        o.append('ORD3,%5d,%5d' % (r.get('a', 1), r['idx']) + ' ' * 44)
    for p in d['prt']:
        o.append('PRT1,%5d,%5d,%9.2f,%9.2f,%2d,%-40s,%-40s,%-16s,%-16s' % (
            p['qty'], p['n'], p['W'], p['L'], p.get('k', 1), p.get('note', '')[:40], p.get('note2', '')[:40],
            p['name'][:16], p.get('x', '')[:16]))
        o.append('PRT2,' + p.get('prt2', PRT2))
        e = p.get('edges', [('', '', '')] * 4)
        o.append('PRT3, %s,%s,%s,%s,%s' % (p.get('mask', '0000'), _edge(e[0]), _edge(e[1]), _edge(e[2]), _edge(e[3], 6)))
        p4 = p.get('prt4', ['', '', '', '', ''])
        o.append('PRT4,%-16s,%-12s,%-12s,%-12s,%-30s,%-28s' % (p.get('cust', '')[:16], p4[0], p4[1], p4[2], p4[3], p4[4]))
        p5 = p.get('p5', ('H', 'N', p['n'] + 1, p['n'] + 1))
        o.append('PRT5,%s,%s,%5d,%5d' % p5)
    for q in d['pat']:
        o.append('PAT1,%02d,%s,%5d,%5d' % (q['no'], q['dir'], q['qty'], q.get('q2', 1)) + ' ' * 29)
        o.append('PAT2,' + q.get('pat2', PAT2))
        o.append('PAT3,' + q.get('pat3', PAT3))
        o.append('PAT4,' + q.get('pat4', PAT4))
        o.append('PAT5,' + q.get('pat5', PAT5))
        o.append('BCUT')
        for (lvl, pos, isp, idx) in q['cuts']:
            o.append('CUT1,%02d,%9.2f,%d,%03d' % (lvl, pos, 1 if isp else 0, idx) + ' ' * 15)
    o.append('END')
    return ('\r\n'.join(o) + '\r\n').encode(ENC)

# ------------------------------------------------------------------ provjera stabla rezova
def validate(d):
    """Provjerava da svaki dio u shemama ima dimenzije koje stablo rezova stvarno daje,
    da zbroj traka (s kerfom) stane u ploču i da su svi naručeni komadi izrezani. Vraća listu grešaka."""
    err = []
    kerf = d['ctl2'][0]
    cnt = {}
    for q in d['pat']:
        s = d['inv'][0]
        UL, UW = s['L'] - s['trim'][0] - s['trim'][1], s['W'] - s['trim'][2] - s['trim'][3]
        lvl = {}
        sums = {}
        for (L, pos, isp, idx) in q['cuts']:
            lvl[L] = pos
            for k in list(lvl):
                if k > L: del lvl[k]
            parent = (UW if q['dir'] == 'L' else UL) if L == 1 else lvl[L - 1]
            sums.setdefault((L, tuple(sorted(lvl.items())[:-1])), []).append(pos)
            if isp:
                o = d['ord'][idx - 1]
                got = sorted([pos, (UL if q['dir'] == 'L' else UW) if L == 1 else lvl[L - 1]])
                want = sorted([o['W'], o['L']])
                if got != want:
                    err.append('shema %02d: dio %d dobiva %s, naručeno %s' % (q['no'], idx, got, want))
                if d['ctl1']['grain'] == 'Y':
                    # duljina dijela mora ležati uz duljinu ploče
                    along_L = (L % 2 == 0) if q['dir'] == 'L' else (L % 2 == 1)
                    if o['W'] != o['L'] and ((pos == o['L']) != along_L):
                        err.append('shema %02d: dio %d rotiran protiv goda' % (q['no'], idx))
                cnt[idx] = cnt.get(idx, 0) + q['qty']
        # zbroj traka po razini 1
        l1 = [c[1] for c in q['cuts'] if c[0] == 1]
        lim = UW if q['dir'] == 'L' else UL
        if sum(l1) + kerf * (len(l1) - 1) > lim + 1e-6:
            err.append('shema %02d: trake razine 1 (%s) ne stanu u %s' % (q['no'], l1, lim))
    for o in d['ord']:
        if cnt.get(o['idx'], 0) != o['qty']:
            err.append('dio %d: naručeno %d, u shemama %d' % (o['idx'], o['qty'], cnt.get(o['idx'], 0)))
    return err

def roundtrip_check(folder):
    ok = bad = 0
    for f in sorted(glob.glob(os.path.join(folder, '**', '*.cpo'), recursive=True)):
        raw = open(f, 'rb').read()
        d = parse(raw)
        out = write(d)
        v = validate(d)
        if out == raw and not v:
            ok += 1
        else:
            bad += 1
            if out != raw:
                a, b = raw.split(b'\r\n'), out.split(b'\r\n')
                for i, (x, y) in enumerate(zip(a, b)):
                    if x != y:
                        print(f, 'redak', i + 1); print('  orig', x); print('  novo', y); break
                if len(a) != len(b): print(f, 'broj redaka', len(a), len(b))
            for e in v: print(f, e)
    print('round-trip identično: %d, razlika: %d' % (ok, bad))

if __name__ == '__main__':
    roundtrip_check(sys.argv[1] if len(sys.argv) > 1 else '.')
