"""cpo_crtaj.py — crta sheme rezanja iz .cpo (PW ili Hub) u PNG, po istom modelu stabla rezova kao cpo_rw.validate.
Upotreba: python3 cpo_crtaj.py datoteka.cpo [izlaz.png]"""
import sys
from hub.formati import cpo_rw
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def sheme(d):
    """Zadržano radi starih poziva — geometrija je sada u hub.nalozi.sheme.geometrija."""
    from hub.nalozi.sheme import geometrija
    return [(sh['dir'], sh['pravokutnici']) for sh in geometrija(d)]

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
