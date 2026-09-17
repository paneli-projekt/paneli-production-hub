# -*- coding: utf-8 -*-
"""Sličica slaganja (PNG) za ekran — sve ploče jednog prijedloga / potvrđenog slaganja u jednom redu, ploča uspravno kao u
krojnom nacrtu (L okomito). Isti podaci kao krojni nacrt (ispis.krojni.podaci); služi da operater vidi shemu ODMAH na ekranu
obračuna / pile, bez otvaranja PDF-a (Igor, 17. 9.)."""
import os
import tempfile

from . import krojni as KR

BOJA_KOMAD, BOJA_RUB, BOJA_OST = "#DCE9E2", "#2E6B57", "#9AA0A6"
BOJA_KUPAC, BOJA_KUPAC_RUB = "#F9DEE5", "#C2506B"      # kupčev restl: ostatak koji se naplaćuje kupcu (roza, Igor 17. 9.)
BOJA_NAS, BOJA_NAS_RUB = "#DCE7F3", "#2F5D8C"          # naš restl: korisni ostatak ≥ 400 × 400 i ≥ 1 m², ne naplaćuje se (plava)
MAX_LISTOVA = 8


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    return plt, Rectangle


def pregled(conn, oid):
    """JSON za ekran „Pregled slaganja“: listovi (br, smjer, komada, iskorištenje, ostatak) + elementi (idx, naziv, mjere, kom) + statistika."""
    r = conn.execute("SELECT id, nalog_materijal_id, status, nacin, broj_ploca, iskoristenje, m2_za_naplatu, rezova FROM optimizacija WHERE id = ?", (oid,)).fetchone()
    if not r:
        return None
    d = KR.podaci(conn, r["nalog_materijal_id"], oid=oid)
    return dict(id=r["id"], nalog_materijal_id=r["nalog_materijal_id"], status=r["status"], nacin=r["nacin"], materijal=d["materijal"], ploca=d["ploca"],
                statistika=d["statistika"], trake=[dict(oznaka=t["oznaka"], naziv=t["naziv"], metri=round(t["metri"], 1)) for t in d["trake"]],
                listovi=[dict(br=li["br"], dir=li["dir"], komadi=li["komadi"], rezova=li["rezova"], iskoristenje=li["iskoristenje"], m2_dijelova=li["m2_dijelova"],
                              ostatak=list(li["ostatak"]) if li.get("ostatak") else None) for li in d["listovi"]],
                elementi=[dict(idx=e["idx"], naziv=e["naziv"], L=e["L"], W=e["W"], kom=e["kom"], napomena=e["napomena"], vrsta=e["vrsta"]) for e in d["elementi"]])


def png(conn, oid, put=None, visina_px=150, list_br=None):
    """PNG za optimizaciju `oid`: sve ploče u redu (sličica), ili jedna ploča `list_br` s brojevima i mjerama (pregled na ekranu).
    Vraća putanju ili None kad nema slaganja."""
    r = conn.execute("SELECT id, nalog_materijal_id, slaganje_json FROM optimizacija WHERE id = ?", (oid,)).fetchone()
    if not r or not r["slaganje_json"]:
        return None
    d = KR.podaci(conn, r["nalog_materijal_id"], oid=oid)
    listovi = d["listovi"]
    if not listovi:
        return None
    if list_br:
        listovi = [li for li in listovi if li["br"] == list_br]
        if not listovi:
            return None
    L, W = d["ploca"]["L"], d["ploca"]["W"]
    plt, Rectangle = _mpl()
    n = 1 if list_br else min(len(listovi), MAX_LISTOVA)
    dpi = 100
    h_in = visina_px / dpi
    w_in = h_in * (W / L) * (1.0 if list_br else 1.02)
    fig, axes = plt.subplots(1, n, figsize=(w_in * n + 0.1, h_in + (0.22 if not list_br else 0.05)), dpi=dpi)
    if n == 1:
        axes = [axes]
    velik = bool(list_br) and visina_px >= 300
    for ax, li in zip(axes, listovi[:n]):
        # podloga = kupčev restl (roza): sve što nije komad ni naš korisni ostatak naplaćuje se kupcu
        ax.add_patch(Rectangle((0, 0), W, L, fill=True, fc=BOJA_KUPAC, ec="#333333", lw=1.0))
        o = li.get("ostatak")
        if o:                                            # naš restl (plava): dir L = traka uz duljinu → ostatak po širini (desno), inače po duljini (dolje)
            oL, oW = float(o[0]), float(o[1])
            if li["dir"] == "L":
                ax.add_patch(Rectangle((W - oW, 0), oW, L, fc=BOJA_NAS, ec=BOJA_NAS_RUB, lw=0.8, ls=(0, (3, 2))))
            else:
                ax.add_patch(Rectangle((0, 0), W, oL, fc=BOJA_NAS, ec=BOJA_NAS_RUB, lw=0.8, ls=(0, (3, 2))))
        for (x, y, w, h, idx) in li["pravokutnici"]:
            X, Y, Wd, Hd = y, L - x - w, h, w
            if idx is None:
                ax.add_patch(Rectangle((X, Y), Wd, Hd, fill=False, ls=(0, (2, 2)), lw=0.4, ec=BOJA_OST))
                continue
            ax.add_patch(Rectangle((X, Y), Wd, Hd, fc=BOJA_KOMAD, ec=BOJA_RUB, lw=0.6 if not velik else 0.9))
            if velik:
                fs = 9 if min(Wd, Hd) > W * 0.12 else 6.5
                if Wd > W * 0.08 and Hd > L * 0.03:
                    ax.text(X + Wd / 2, Y + Hd / 2 + (L * 0.012 if Hd > L * 0.06 else 0), str(idx), ha="center", va="center", fontsize=fs, fontweight="bold", color="#1F2A26")
                    if Hd > L * 0.06 and Wd > W * 0.16:
                        ax.text(X + Wd / 2, Y + Hd / 2 - L * 0.018, "%g × %g" % (w, h), ha="center", va="center", fontsize=6.5, color="#4A5560")
            elif Wd > W * 0.12 and Hd > L * 0.05:
                ax.text(X + Wd / 2, Y + Hd / 2, str(idx), ha="center", va="center", fontsize=6, color="#1F2A26")
        if not list_br:
            ax.set_title("%d · %s %%%s" % (li["br"], ("%.0f" % (100 * li["iskoristenje"])), (" · restl" if o else "")), fontsize=6.5, pad=2, color="#333333")
        ax.set_xlim(-L * 0.01, W + L * 0.01)
        ax.set_ylim(-L * 0.01, L + L * 0.01)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.99 if list_br else 0.9, bottom=0.005, wspace=0.06)
    put = put or os.path.join(tempfile.gettempdir(), "hub_sheme_%d_%s_%d.png" % (oid, list_br or "sve", visina_px))
    fig.savefig(put, dpi=dpi, facecolor="#FFFFFF")
    plt.close(fig)
    return put
