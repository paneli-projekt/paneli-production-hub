# -*- coding: utf-8 -*-
"""Sheme rezanja iz CPO-a kao slike (PNG) — po jedna po shemi (PAT), za ekran naloga (D-34: sheme su uz svaki materijal uvijek vidljive)
i za operatera na pili. Geometrija je ista kao u `cpo_rw.validate` (stablo rezova); crtanje je matplotlib, koji se učitava tek pri pozivu —
bez njega izvoz na pilu i dalje radi, samo bez slika (vrati upozorenje).

    py -m hub.nalozi.sheme datoteka.cpo [mapa_izlaza]
"""
import os
import sys

from ..formati import cpo_rw


def geometrija(d):
    """Za svaku shemu (PAT): dict(no, dir, qty, pravokutnici=[(x, y, w, h, idx|None)]) u koordinatama ploče (x uz L, y uz W);
    idx = redni broj ORD retka (1-based) za dio, None za otpad / međukomad."""
    s = d["inv"][0]
    UL, UW = s["L"] - s["trim"][0] - s["trim"][1], s["W"] - s["trim"][2] - s["trim"][3]
    kerf = d["ctl2"][0]
    out = []
    for q in d["pat"]:
        rects = []
        stack = {0: (s["trim"][0], s["trim"][2], UL, UW)}
        pos = {}
        for (L, p, isp, idx) in q["cuts"]:
            px, py, pw, ph = stack[L - 1]
            horiz = (L % 2 == 1) if q["dir"] == "L" else (L % 2 == 0)
            off = pos.get(L, 0)
            rect = (px, py + off, pw, p) if horiz else (px + off, py, p, ph)
            pos[L] = off + p + kerf
            stack[L] = rect
            for k in list(pos):
                if k > L:
                    del pos[k]
            for k in list(stack):
                if k > L:
                    del stack[k]
            rects.append(rect + (idx if isp else None,))
        out.append(dict(no=q["no"], dir=q["dir"], qty=q["qty"], pravokutnici=rects))
    return out


def _iskoristenje(d, sh):
    s = d["inv"][0]
    m2_dio = sum(w * h for (x, y, w, h, idx) in sh["pravokutnici"] if idx is not None)
    return m2_dio / (s["L"] * s["W"]) if s["L"] and s["W"] else 0.0


def nacrtaj(cpo_put, mapa=None, osnova=None, dpi=80):
    """Nacrtaj sve sheme CPO-a; vraća (popis dict(png, shema, qty, dir, iskoristenje, dijelova), upozorenje|None).
    Slike: `<mapa>/<osnova>_S1.png`, `_S2.png` … (zadano uz CPO)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except ImportError:
        return [], "matplotlib nije instaliran (pip install -r requirements.txt) — sheme nisu nacrtane"
    d = cpo_rw.parse(cpo_put)
    s = d["inv"][0]
    mapa = mapa or os.path.dirname(os.path.abspath(cpo_put))
    osnova = osnova or os.path.splitext(os.path.basename(cpo_put))[0]
    os.makedirs(mapa, exist_ok=True)
    sheme = geometrija(d)
    out = []
    for i, sh in enumerate(sheme, 1):
        fig, ax = plt.subplots(figsize=(11, 8.6))
        ax.add_patch(Rectangle((0, 0), s["L"], s["W"], fill=False, lw=2, ec="#333"))
        dijelova = 0
        for (x, y, w, h, idx) in sh["pravokutnici"]:
            if idx is None:
                ax.add_patch(Rectangle((x, y), w, h, fill=False, ls=":", lw=0.6, ec="#999"))
                continue
            dijelova += 1
            o = d["ord"][idx - 1]
            prt = d["prt"][idx - 1] if idx - 1 < len(d["prt"]) else {}
            ax.add_patch(Rectangle((x, y), w, h, fc="#d8e6f2", ec="#1f3a5f", lw=1))
            naziv = (prt.get("note") or "").strip()
            ax.text(x + w / 2, y + h / 2, "%d\n%g x %g%s" % (idx, o["L"], o["W"], ("\n" + naziv[:16]) if naziv else ""),
                    ha="center", va="center", fontsize=8 if min(w, h) > 120 else 6)
        isk = _iskoristenje(d, sh)
        ax.set_xlim(-30, s["L"] + 30)
        ax.set_ylim(-30, s["W"] + 30)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title("%s   %s   ploca %g x %g   shema %d/%d  x %d kom   %d dijelova   iskoristenje %.0f %%"
                     % (d["prog"], d["material"], s["L"], s["W"], i, len(sheme), sh["qty"], dijelova, isk * 100), fontsize=10)
        fig.tight_layout()
        png = os.path.join(mapa, "%s_S%d.png" % (osnova, i))
        fig.savefig(png, dpi=dpi)
        plt.close(fig)
        out.append(dict(png=png, shema=i, qty=sh["qty"], dir=sh["dir"], iskoristenje=round(isk, 4), dijelova=dijelova))
    return out, None


def main(argv=None):
    a = argv if argv is not None else sys.argv[1:]
    if not a:
        print("upotreba: py -m hub.nalozi.sheme datoteka.cpo [mapa_izlaza]")
        return 1
    slike, upoz = nacrtaj(a[0], a[1] if len(a) > 1 else None)
    for s in slike:
        print("%s  shema %d x %d  %d dijelova  %.1f %%" % (s["png"], s["shema"], s["qty"], s["dijelova"], s["iskoristenje"] * 100))
    if upoz:
        print("PAZI:", upoz)
    return 0


if __name__ == "__main__":
    sys.exit(main())
