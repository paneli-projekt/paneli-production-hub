# -*- coding: utf-8 -*-
"""ispis/naljepnica_restl.py — QR naljepnice restlova (D-64/3): skladištar ih zalijepi pri potvrdi restla; QR nosi adresu Huba `…/r/R1364`
(kao Regal traka `…/t/TR000103`), pa skeniranje otvara restl (ident, mjere, lokacija, status). Reportlab, bez dodatnih paketa.

Format: A4 s mrežom naljepnica (zadano 2 × 5 = 10 kom, 99 × 57 mm — Avery 3652 / L7173) ili jedna naljepnica po stranici za rolu (62 × 40 mm,
postavka `naljepnica_restl_format` = a4 | rola). Sadržaj: oznaka (veliko), QR, ident + naziv materijala, debljina, L × W (× kom), lokacija, datum.
Prazan `naljepnica_restl_url` u postavkama → QR nosi samo oznaku.
"""
import os

from ..db import postavka

ZADANI_URL = "http://192.168.5.201:8766/r/"


def url_restla(conn, oznaka):
    u = postavka(conn, "naljepnica_restl_url", ZADANI_URL)
    return (u.rstrip("/") + "/" + oznaka) if u else oznaka


def pdf(conn, restlovi, put, format_=None):
    """restlovi = popis dict-ova (RS.restl / RS.popis). Vraća put ili None bez reportlaba."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.graphics.barcode import qr
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics import renderPDF
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return None
    font = "Helvetica"
    for kand in ("DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            pdfmetrics.registerFont(TTFont("HubFont", kand)); font = "HubFont"; break
        except Exception:
            continue
    format_ = format_ or postavka(conn, "naljepnica_restl_format", "a4")
    if format_ == "rola":
        W, H, kol, red, x0, y0, gw, gh = 62 * mm, 40 * mm, 1, 1, 0, 0, 62 * mm, 40 * mm
    else:
        W, H, kol, red, x0, y0, gw, gh = A4[0], A4[1], 2, 5, 4.5 * mm, 13.5 * mm, 101 * mm, 57 * mm
    c = canvas.Canvas(put, pagesize=(W, H))
    c.setTitle("Naljepnice restlova")
    lw, lh = (gw - 2 * mm, gh - 2 * mm) if format_ != "rola" else (W - 4 * mm, H - 4 * mm)
    for i, r in enumerate(restlovi):
        k = i % (kol * red)
        if i and k == 0:
            c.showPage()
        cx = x0 + (k % kol) * gw + 1 * mm if format_ != "rola" else 2 * mm
        cy = H - y0 - (k // kol + 1) * gh + 1 * mm if format_ != "rola" else 2 * mm
        _naljepnica(c, r, cx, cy, lw, lh, font, url_restla(conn, r["oznaka"]), mm, qr, Drawing, renderPDF)
    c.showPage()
    c.save()
    return put


def _naljepnica(c, r, x, y, w, h, font, url, mm, qr, Drawing, renderPDF):
    c.setLineWidth(0.3)
    c.rect(x, y, w, h)
    q = qr.QrCodeWidget(url)
    b = q.getBounds()
    qs = min(h - 6 * mm, 30 * mm)
    d = Drawing(qs, qs, transform=[qs / (b[2] - b[0]), 0, 0, qs / (b[3] - b[1]), 0, 0])
    d.add(q)
    renderPDF.draw(d, c, x + w - qs - 3 * mm, y + (h - qs) / 2)
    tx = x + 3 * mm
    c.setFont(font, 20)
    c.drawString(tx, y + h - 9 * mm, r["oznaka"])
    c.setFont(font, 8.5)
    ident = r.get("ident") or "—"
    naziv = (r.get("naziv_kratki") or r.get("naziv") or r.get("dekor_ulaz") or "")[:34]
    c.drawString(tx, y + h - 14 * mm, "%s  %s" % (ident, naziv))
    deb = r.get("debljina")
    c.setFont(font, 13)
    c.drawString(tx, y + h - 21 * mm, "%g × %g%s%s" % (r["L"], r["W"], ("  × %d kom" % r["kom"]) if (r.get("kom") or 1) > 1 else "", ("  · %g mm" % deb) if deb else ""))
    c.setFont(font, 9)
    c.drawString(tx, y + h - 27 * mm, "Lokacija: %s" % (r.get("lokacija") or "________"))
    c.setFont(font, 7)
    st = r.get("status") or ""
    c.drawString(tx, y + 3 * mm, "%s%s · %s" % ((r.get("datum") or "")[:10], ("  · " + st.upper()) if st in ("prijedlog", "provjeri") else "", r.get("napomena") or "")[:70])


def napravi(conn, restlovi, mapa, ime=None, format_=None):
    os.makedirs(mapa, exist_ok=True)
    ime = ime or ("Naljepnice_restl_%s.pdf" % (restlovi[0]["oznaka"] if len(restlovi) == 1 else "%s-%s" % (restlovi[0]["oznaka"], restlovi[-1]["oznaka"])))
    return pdf(conn, restlovi, os.path.join(mapa, ime), format_)
