# -*- coding: utf-8 -*-
"""Ponuda kao dokument za kupca (D-40): HTML (tijelo maila i pregled na ekranu) + PDF (prilog; reportlab — bez njega ide samo HTML).
Isti sadržaj kao Pantheonova ponuda: zaglavlje tvrtke, kupac, broj i datum, stavke (ident, naziv, količina, JM, cijena, rabat, iznos),
neto, PDV 25 %, ukupno, napomena. Cijene i rabati su iz verzije ponude — ovdje se ništa ne računa iznova."""
import datetime
import os
from xml.sax.saxutils import escape

from ..db import postavka
from . import nalozi as N, ponuda as PO

TVRTKA = dict(naziv="PANELI PROJEKT d.o.o.", adresa="Svilajska ulica 30A, 31000 Osijek", web="www.paneliprojekt.hr", mail="prodaja@paneliprojekt.hr")


def _fmt(x, dec=2):
    s = ("%%.%df" % dec) % (x or 0)
    cijeli, _, d = s.partition(".")
    cijeli = "{:,}".format(int(cijeli)).replace(",", ".")
    return cijeli + "," + d if dec else cijeli


def podaci(conn, verzija_id):
    v = PO.verzija(conn, verzija_id)
    n = N.nalog(conn, v["nalog_id"])
    k = n.get("kupac") or {}
    broj = n["ponuda_pantheon"] or ("%s / v%d" % (n["broj"], v["verzija"]))
    neto = round(sum(s["iznos"] for s in v["stavke"]), 2)
    return dict(verzija=v, nalog=n, kupac=k, broj=broj, datum=datetime.date.today().strftime("%d.%m.%Y."), neto=neto, pdv=round(neto * PO.OC.PDV, 2),
                ukupno=round(neto * (1 + PO.OC.PDV), 2), naslov="Ponuda %s" % broj, tvrtka=dict(TVRTKA, naziv=postavka(conn, "tvrtka_naziv", TVRTKA["naziv"])),
                vrijedi_dana=int(postavka(conn, "ponuda_vrijedi_dana", "15") or 15), napomena=v.get("mail_tekst") or "")


def html(conn, verzija_id):
    d = podaci(conn, verzija_id)
    k, n = d["kupac"], d["nalog"]
    redovi = "".join(
        "<tr><td>%d</td><td>%s</td><td>%s</td><td class='r'>%s</td><td>%s</td><td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td></tr>"
        % (i, escape(s["pantheon_ident"]), escape(s["naziv"] or ""), _fmt(s["kolicina"]), escape(s["jm"] or ""), _fmt(s["cijena"]), _fmt(s["rabat"] or 0, 0) + " %", _fmt(s["iznos"]))
        for i, s in enumerate(d["verzija"]["stavke"], 1))
    return """<!doctype html><html lang="hr"><head><meta charset="utf-8"><title>%(naslov)s</title>
<style>body{font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#222;margin:24px}h1{font-size:18px;margin:0 0 4px}
table{border-collapse:collapse;width:100%%;margin-top:14px}th,td{border-bottom:1px solid #ddd;padding:4px 6px;text-align:left;vertical-align:top}
th{background:#f2f2f2;font-weight:600}td.r,th.r{text-align:right;white-space:nowrap}.zbroj td{border:0;font-weight:600}.sitno{color:#666;font-size:11px}
.zag{display:flex;justify-content:space-between;gap:24px}.zag div{flex:1}</style></head><body>
<div class="zag"><div><h1>%(tvrtka_naziv)s</h1><div class="sitno">%(tvrtka_adresa)s<br>%(tvrtka_mail)s · %(tvrtka_web)s</div></div>
<div><h1>%(naslov)s</h1><div class="sitno">Datum: %(datum)s · Nalog: %(nalog)s · Vrijedi %(vrijedi)d dana</div></div></div>
<p><b>Kupac:</b> %(kupac)s%(kupac_adresa)s</p>
<table><thead><tr><th>#</th><th>Ident</th><th>Naziv</th><th class="r">Količina</th><th>JM</th><th class="r">Cijena</th><th class="r">Rabat</th><th class="r">Iznos</th></tr></thead>
<tbody>%(redovi)s</tbody>
<tfoot><tr class="zbroj"><td colspan="7" class="r">Osnovica</td><td class="r">%(neto)s EUR</td></tr>
<tr class="zbroj"><td colspan="7" class="r">PDV 25 %%</td><td class="r">%(pdv)s EUR</td></tr>
<tr class="zbroj"><td colspan="7" class="r">UKUPNO</td><td class="r">%(ukupno)s EUR</td></tr></tfoot></table>
%(napomena)s<p class="sitno">Cijene su bez PDV-a; količine ploča po površini za naplatu, trake po metru (10 %% otpada uključeno). Ponuda je informativna do potvrde.</p>
</body></html>""" % dict(naslov=escape(d["naslov"]), tvrtka_naziv=escape(d["tvrtka"]["naziv"]), tvrtka_adresa=escape(d["tvrtka"]["adresa"]), tvrtka_mail=d["tvrtka"]["mail"],
                          tvrtka_web=d["tvrtka"]["web"], datum=d["datum"], nalog=escape(n["naziv"]), vrijedi=d["vrijedi_dana"],
                          kupac=escape(k.get("naziv") or "—"), kupac_adresa=escape((", " + ", ".join(x for x in (k.get("adresa"), k.get("mjesto")) if x)) if k.get("adresa") or k.get("mjesto") else ""),
                          redovi=redovi, neto=_fmt(d["neto"]), pdv=_fmt(d["pdv"]), ukupno=_fmt(d["ukupno"]),
                          napomena=("<p><b>Napomena:</b> %s</p>" % escape(d["napomena"])) if d["napomena"] else "")


def pdf(conn, verzija_id, put):
    """PDF ponude (reportlab). Vraća put ili None ako reportlab nije instaliran."""
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
    d = podaci(conn, verzija_id)
    font = "Helvetica"
    for kand in ("DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            pdfmetrics.registerFont(TTFont("HubFont", kand))
            font = "HubFont"
            break
        except Exception:
            continue
    st = getSampleStyleSheet()
    norm = ParagraphStyle("n", parent=st["Normal"], fontName=font, fontSize=9, leading=11)
    h = ParagraphStyle("h", parent=norm, fontSize=14, leading=17, spaceAfter=2)
    sitno = ParagraphStyle("s", parent=norm, fontSize=8, textColor=colors.grey)
    k, n = d["kupac"], d["nalog"]
    doc = SimpleDocTemplate(put, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm, title=d["naslov"])
    el = [Table([[Paragraph(d["tvrtka"]["naziv"], h), Paragraph(d["naslov"], h)],
                 [Paragraph("%s<br/>%s · %s" % (d["tvrtka"]["adresa"], d["tvrtka"]["mail"], d["tvrtka"]["web"]), sitno),
                  Paragraph("Datum: %s · Nalog: %s · Vrijedi %d dana" % (d["datum"], n["naziv"], d["vrijedi_dana"]), sitno)]], colWidths=[95 * mm, 85 * mm]),
          Spacer(1, 6 * mm), Paragraph("<b>Kupac:</b> %s%s" % (escape(k.get("naziv") or "—"), escape((", " + ", ".join(x for x in (k.get("adresa"), k.get("mjesto")) if x)) if k.get("adresa") or k.get("mjesto") else "")), norm),
          Spacer(1, 4 * mm)]
    data = [["#", "Ident", "Naziv", "Količina", "JM", "Cijena", "Rabat", "Iznos"]]
    for i, s in enumerate(d["verzija"]["stavke"], 1):
        data.append([str(i), s["pantheon_ident"], Paragraph(escape(s["naziv"] or ""), norm), _fmt(s["kolicina"]), s["jm"] or "", _fmt(s["cijena"]), _fmt(s["rabat"] or 0, 0) + " %", _fmt(s["iznos"])])
    data += [["", "", "", "", "", "", "Osnovica", _fmt(d["neto"]) + " EUR"], ["", "", "", "", "", "", "PDV 25 %", _fmt(d["pdv"]) + " EUR"], ["", "", "", "", "", "", "UKUPNO", _fmt(d["ukupno"]) + " EUR"]]
    t = Table(data, colWidths=[8 * mm, 20 * mm, 70 * mm, 20 * mm, 10 * mm, 18 * mm, 14 * mm, 22 * mm], repeatRows=1)
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
                           ("LINEBELOW", (0, 0), (-1, -4), 0.3, colors.HexColor("#dddddd")), ("ALIGN", (3, 1), (3, -1), "RIGHT"), ("ALIGN", (5, 1), (-1, -1), "RIGHT"),
                           ("FONTNAME", (6, -3), (-1, -1), font), ("LINEABOVE", (6, -3), (-1, -3), 0.8, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    el.append(t)
    if d["napomena"]:
        el += [Spacer(1, 4 * mm), Paragraph("<b>Napomena:</b> %s" % escape(d["napomena"]), norm)]
    el += [Spacer(1, 4 * mm), Paragraph("Cijene su bez PDV-a; količine ploča po površini za naplatu, trake po metru (10 % otpada uključeno). Ponuda je informativna do potvrde.", sitno)]
    doc.build(el)
    return put


def napravi(conn, verzija_id, mapa):
    """HTML + (ako može) PDF u mapu; vraća dict(html, pdf)."""
    d = podaci(conn, verzija_id)
    os.makedirs(mapa, exist_ok=True)
    osnova = "Ponuda_%s_v%d" % (d["nalog"]["naziv"], d["verzija"]["verzija"])
    h = os.path.join(mapa, osnova + ".html")
    open(h, "w", encoding="utf-8").write(html(conn, verzija_id))
    p = pdf(conn, verzija_id, os.path.join(mapa, osnova + ".pdf"))
    return dict(html=h, pdf=p, naslov=d["naslov"], neto=d["neto"], ukupno=d["ukupno"])
