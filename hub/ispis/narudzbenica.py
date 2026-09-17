# -*- coding: utf-8 -*-
"""ispis/narudzbenica.py — PDF narudžbenice dobavljaču (D-42/5, D-76): zaglavlje tvrtke, dobavljač, stavke (ident, naziv, dimenzija, količina, JM),
napomena; bez cijena (naručuje se po ugovorenom cjeniku). Reportlab kao ponuda; bez reportlaba vraća None."""
import os
from html import escape

from ..db import postavka


def podaci(conn, nid):
    from ..nabava import narudzbenica as NB
    d = NB.red(conn, nid)
    if not d:
        raise ValueError("nema narudžbenice %s" % nid)
    d["tvrtka"] = dict(naziv=postavka(conn, "tvrtka_naziv", "Paneli projekt d.o.o."), adresa=postavka(conn, "tvrtka_adresa", "Osijek"),
                       mail=postavka(conn, "tvrtka_mail", "prodaja@paneliprojekt.hr"), web=postavka(conn, "tvrtka_web", "www.paneliprojekt.hr"),
                       tel=postavka(conn, "tvrtka_tel", ""))
    d["naslov"] = "Narudžba %s" % d["broj"]
    return d


def pdf(conn, nid, put):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return None
    d = podaci(conn, nid)
    font = "Helvetica"
    for kand in ("DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            pdfmetrics.registerFont(TTFont("HubFont", kand)); font = "HubFont"; break
        except Exception:
            continue
    st = getSampleStyleSheet()
    norm = ParagraphStyle("n", parent=st["Normal"], fontName=font, fontSize=9, leading=11)
    h = ParagraphStyle("h", parent=norm, fontSize=14, leading=17, spaceAfter=2)
    sitno = ParagraphStyle("s", parent=norm, fontSize=8, textColor=colors.grey)
    doc = SimpleDocTemplate(put, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm, title=d["naslov"])
    t = d["tvrtka"]
    el = [Table([[Paragraph(t["naziv"], h), Paragraph(d["naslov"], h)],
                 [Paragraph("%s<br/>%s · %s%s" % (t["adresa"], t["mail"], t["web"], (" · " + t["tel"]) if t["tel"] else ""), sitno),
                  Paragraph("Datum: %s%s%s" % (d["datum"], (" · Očekivano: " + d["ocekivano"]) if d["ocekivano"] else "", (" · Naručio: " + d["narucio"]) if d["narucio"] else ""), sitno)]],
                colWidths=[95 * mm, 85 * mm]),
          Spacer(1, 6 * mm), Paragraph("<b>Dobavljač:</b> %s%s" % (escape(d["dobavljac"]), (" · " + escape(d["email"])) if d["email"] else ""), norm), Spacer(1, 4 * mm)]
    data = [["#", "Ident", "Naziv", "Dimenzija", "Količina", "JM", "Za nalog"]]
    for i, s in enumerate(d["stavke"], 1):
        data.append([str(i), s["pantheon_ident"], Paragraph(escape(s["naziv"] or ""), norm), s["dimenzija"] or "", ("%g" % s["kom"]), s["jm"] or "", s["nalog"] or ""])
    tb = Table(data, colWidths=[8 * mm, 20 * mm, 72 * mm, 22 * mm, 18 * mm, 14 * mm, 28 * mm], repeatRows=1)
    tb.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
                            ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")), ("ALIGN", (4, 1), (4, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    el.append(tb)
    if d["napomena"]:
        el += [Spacer(1, 4 * mm), Paragraph("<b>Napomena:</b> %s" % escape(d["napomena"]), norm)]
    el += [Spacer(1, 4 * mm), Paragraph("Molimo na otpremnici i računu navesti broj narudžbe %s. Količine ploča su u komadima cijelih ploča navedene dimenzije, trake u metrima." % d["broj"], sitno)]
    doc.build(el)
    return put


def napravi(conn, nid, mapa):
    d = podaci(conn, nid)
    os.makedirs(mapa, exist_ok=True)
    put = os.path.join(mapa, "Narudzba_%s.pdf" % d["broj"])
    return pdf(conn, nid, put)
