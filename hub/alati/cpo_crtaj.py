"""cpo_crtaj.py — crta sheme rezanja iz .cpo (PW ili Hub) u PNG, po istom modelu stabla rezova kao cpo_rw.validate.
Upotreba: python3 cpo_crtaj.py datoteka.cpo [izlaz.png]"""
import sys
from hub.formati import cpo_rw
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def sheme(d):
    """Vraća listu shema; shema = (dir, [(x, y, w, h, idx|None)]) u koordinatama ploče (x uz duljinu L, y uz širinu W)."""
    s = d['inv'][0]
    UL, UW = s['L'] - s['trim'][0] - s['trim'][1], s['W'] - s['trim'][2] - s['trim'][3]
    kerf = d['ctl2'][0]
    out = []
    for q in d['pat']:
        rects = []
        # stog: po razini (početak x, početak y, dostupno w, dostupno h, orijentacija reza)
        # razina 1 u 'L' shemi: reže se po y (širina), traka = puna duljina
        # razina n: alternira smjer
        cursor = {}   # razina -> (x0, y0, dx, dy) pomak unutar roditelja
        stack = {0: (s['trim'][0], s['trim'][2], UL, UW)}
        pos = {}
        for (L, p, isp, idx) in q['cuts']:
            px, py, pw, ph = stack[L - 1]
            horiz = (L % 2 == 1) if q['dir'] == 'L' else (L % 2 == 0)   # rez razine 1 kod 'L' dijeli širinu (y)
            off = pos.get(L, 0)
            if horiz:
                rect = (px, py + off, pw, p)
                pos[L] = off + p + kerf
            else:
                rect = (px + off, py, p, ph)
                pos[L] = off + p + kerf
            stack[L] = rect
            for k in list(pos):
                if k > L: del pos[k]
            for k in list(stack):
                if k > L: del stack[k]
            rects.append(rect + (idx if isp else None,))
        out.append((q['dir'], rects))
    return out

def crtaj(path, out=None):
    d = cpo_rw.parse(path)
    s = d['inv'][0]
    sh = sheme(d)
    n = len(sh)
    fig, axes = plt.subplots(n, 1, figsize=(10, 7.5 * n))
    if n == 1: axes = [axes]
    for ax, (dr, rects) in zip(axes, sh):
        ax.add_patch(Rectangle((0, 0), s['L'], s['W'], fill=False, lw=2))
        for (x, y, w, h, idx) in rects:
            if idx is None:
                ax.add_patch(Rectangle((x, y), w, h, fill=False, ls=':', lw=0.6, ec='gray'))
            else:
                o = d['ord'][idx - 1]
                ax.add_patch(Rectangle((x, y), w, h, fc='#cde', ec='k', lw=1))
                ax.text(x + w / 2, y + h / 2, '%d\n%gx%g' % (idx, o['W'], o['L']), ha='center', va='center', fontsize=7)
        ax.set_xlim(-20, s['L'] + 20); ax.set_ylim(-20, s['W'] + 20); ax.set_aspect('equal')
        ax.set_title('%s  %s  ploča %gx%g  shema %s' % (d['prog'], d['material'], s['L'], s['W'], dr), fontsize=9)
    fig.tight_layout()
    out = out or path.rsplit('.', 1)[0] + '.png'
    fig.savefig(out, dpi=90); plt.close(fig)
    return out

if __name__ == '__main__':
    print(crtaj(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
