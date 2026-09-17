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
    bruto = round(sum((s["kolicina"] or 0) * (s["cijena"] or 0) for s in v["stavke"]), 2)
    dat = datetime.date.today()
    if v.get("poslano_kada"):                              # stara verzija: datum kad je poslana, ne današnji
        try:
            dat = datetime.date.fromisoformat(v["poslano_kada"][:10])
        except ValueError:
            pass
    return dict(verzija=v, nalog=n, kupac=k, broj=broj, datum=dat.strftime("%d.%m.%Y."), neto=neto, pdv=round(neto * PO.OC.PDV, 2),
                bruto=bruto, rabat_iznos=round(bruto - neto, 2),
                ukupno=round(neto * (1 + PO.OC.PDV), 2), naslov="Ponuda %s" % broj, tvrtka=dict(TVRTKA, naziv=postavka(conn, "tvrtka_naziv", TVRTKA["naziv"])),
                vrijedi_dana=int(postavka(conn, "ponuda_vrijedi_dana", "15") or 15), napomena=(n.get("napomena_ponude") or "").strip())   # D-90: napomena kupcu ispod uvjeta


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
<p class="sitno">Cijene su bez PDV-a; količine ploča po površini za naplatu, trake i kantiranje po dužnom metru. Ponuda je informativna do potvrde.</p>%(napomena)s
</body></html>""" % dict(naslov=escape(d["naslov"]), tvrtka_naziv=escape(d["tvrtka"]["naziv"]), tvrtka_adresa=escape(d["tvrtka"]["adresa"]), tvrtka_mail=d["tvrtka"]["mail"],
                          tvrtka_web=d["tvrtka"]["web"], datum=d["datum"], nalog=escape(n["naziv"]), vrijedi=d["vrijedi_dana"],
                          kupac=escape(k.get("naziv") or "—"), kupac_adresa=escape((", " + ", ".join(x for x in (k.get("adresa"), k.get("mjesto")) if x)) if k.get("adresa") or k.get("mjesto") else ""),
                          redovi=redovi, neto=_fmt(d["neto"]), pdv=_fmt(d["pdv"]), ukupno=_fmt(d["ukupno"]),
                          napomena=("<p><b>Napomena:</b> %s</p>" % escape(d["napomena"])) if d["napomena"] else "")


LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ispis", "logo-mark.png")
ANT, ACC, ACC_SOFT, SIVA, LINIJA = "#5A5F64", "#2E6B57", "#E3EFE9", "#66727C", "#DDD8CF"


def _fontovi():
    """(regular, bold) — Arial na Windowsu, DejaVu na Linuxu, inače Helvetica (bez dijakritike u ugrađenom fontu)."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for reg, bold in (("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"), ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
                      ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")):
        try:
            pdfmetrics.registerFont(TTFont("HubFont", reg))
            pdfmetrics.registerFont(TTFont("HubFontB", bold))
            return "HubFont", "HubFontB"
        except Exception:
            continue
    return "Helvetica", "Helvetica-Bold"


def pdf(conn, verzija_id, put, tko=None):
    """PDF ponude (reportlab): zaglavlje s logom i podacima tvrtke, kupac, stavke, zbroj, podnožje na svakoj stranici (Igor, 17. 9.: ljepši dizajn).
    Vraća put ili None ako reportlab nije instaliran."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
    except ImportError:
        return None
    from .. import korisnici as KO
    d = podaci(conn, verzija_id)
    f, fb = _fontovi()
    t = d["tvrtka"]
    t.update(adresa=postavka(conn, "tvrtka_adresa", t["adresa"]), mail=postavka(conn, "tvrtka_mail", t["mail"]), web=postavka(conn, "tvrtka_web", t["web"]),
             tel=postavka(conn, "tvrtka_tel", ""), oib=postavka(conn, "tvrtka_oib", ""), iban=postavka(conn, "tvrtka_iban", ""))
    k, n, v = d["kupac"], d["nalog"], d["verzija"]
    kontakt = KO.korisnik(conn, tko) if tko else None
    if kontakt and kontakt.get("uloga") == "sustav":
        kontakt = None
    PW, PH = A4
    M = 16 * mm
    st = getSampleStyleSheet()
    norm = ParagraphStyle("n", parent=st["Normal"], fontName=f, fontSize=9, leading=11.5, textColor=colors.HexColor("#1C2A33"))
    sitno = ParagraphStyle("s", parent=norm, fontSize=7.8, leading=10, textColor=colors.HexColor(SIVA))
    lbl = ParagraphStyle("l", parent=sitno, fontName=fb, fontSize=7, textColor=colors.HexColor(SIVA))
    jaki = ParagraphStyle("b", parent=norm, fontName=fb)
    velik = ParagraphStyle("v", parent=norm, fontName=fb, fontSize=12, leading=14)

    def zaglavlje(c, doc):
        c.saveState()
        y0 = PH - 14 * mm
        # logo + naziv tvrtke
        x = M
        if os.path.exists(LOGO):
            try:
                c.drawImage(LOGO, x, y0 - 13 * mm, width=13 * mm * 109 / 120.0, height=13 * mm, mask="auto", preserveAspectRatio=True)
                x += 13 * mm * 109 / 120.0 + 4 * mm
            except Exception:
                pass
        c.setFillColor(colors.HexColor(ANT))
        c.setFont(fb, 15)
        c.drawString(x, y0 - 6 * mm, t["naziv"])
        c.setFillColor(colors.HexColor(SIVA))
        c.setFont(f, 8)
        c.drawString(x, y0 - 10.2 * mm, t["adresa"])
        c.drawString(x, y0 - 13.6 * mm, " · ".join(z for z in (t["tel"], t["mail"], t["web"]) if z))
        # desno: PONUDA + broj
        c.setFillColor(colors.HexColor(ACC))
        c.setFont(fb, 20)
        c.drawRightString(PW - M, y0 - 6.5 * mm, "PONUDA")
        c.setFillColor(colors.HexColor("#1C2A33"))
        c.setFont(fb, 11)
        c.drawRightString(PW - M, y0 - 11.5 * mm, d["broj"])
        c.setFillColor(colors.HexColor(SIVA))
        c.setFont(f, 8)
        c.drawRightString(PW - M, y0 - 15.5 * mm, "Datum: %s   ·   vrijedi %d dana" % (d["datum"], d["vrijedi_dana"]))
        # crta
        c.setStrokeColor(colors.HexColor(ACC))
        c.setLineWidth(1.4)
        c.line(M, y0 - 18.5 * mm, PW - M, y0 - 18.5 * mm)
        # podnožje
        c.setStrokeColor(colors.HexColor(LINIJA))
        c.setLineWidth(0.5)
        c.line(M, 14 * mm, PW - M, 14 * mm)
        c.setFillColor(colors.HexColor(SIVA))
        c.setFont(f, 7.2)
        desno = "%s · stranica %d" % (d["naslov"], doc.page)
        dno = " · ".join(z for z in (t["naziv"], t["adresa"], ("OIB " + t["oib"]) if t["oib"] else "", ("IBAN " + t["iban"]) if t["iban"] else "", t["mail"]) if z)
        max_w = PW - 2 * M - c.stringWidth(desno, f, 7.2) - 6 * mm
        while dno and c.stringWidth(dno, f, 7.2) > max_w:
            dno = dno[:-4].rstrip(" ·") + "…"
        c.drawString(M, 9.5 * mm, dno)
        c.drawRightString(PW - M, 9.5 * mm, desno)
        c.restoreState()

    doc = SimpleDocTemplate(put, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=38 * mm, bottomMargin=20 * mm, title=d["naslov"], author=t["naziv"])
    # kupac (lijevo) + podaci ponude (desno)
    kup = [Paragraph("KUPAC", lbl), Paragraph(escape(k.get("naziv") or "—"), velik)]
    adr = ", ".join(x for x in (k.get("adresa"), " ".join(y for y in ((k.get("posta") or "").replace("HR-", ""), k.get("mjesto")) if y)) if x and x.strip())
    if adr:
        kup.append(Paragraph(escape(adr), norm))
    if k.get("oib"):
        kup.append(Paragraph("OIB: %s" % escape(k["oib"]), norm))
    if k.get("email") or k.get("telefon"):
        kup.append(Paragraph(escape(" · ".join(x for x in (k.get("telefon"), k.get("email")) if x)), sitno))
    inf = [Paragraph("PODACI O PONUDI", lbl), Paragraph("Nalog: <b>%s</b>" % escape(n["naziv"]), norm), Paragraph("Verzija ponude: v%d" % v["verzija"], norm)]
    if n.get("rok") or n.get("rok_isporuke"):
        inf.append(Paragraph("Rok: %s" % escape(str(n.get("rok") or n.get("rok_isporuke"))), norm))
    if kontakt:
        inf.append(Paragraph("Vaš kontakt: <b>%s</b>%s" % (escape(kontakt.get("ime") or kontakt["oznaka"].title()), escape(" · " + " · ".join(x for x in (kontakt.get("telefon"), kontakt.get("email")) if x)) if (kontakt.get("telefon") or kontakt.get("email")) else ""), norm))
    zag = Table([[kup, inf]], colWidths=[(PW - 2 * M) * 0.56, (PW - 2 * M) * 0.44])
    zag.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                             ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F6F4EF")), ("LEFTPADDING", (1, 0), (1, 0), 5 * mm), ("TOPPADDING", (1, 0), (1, 0), 3 * mm), ("BOTTOMPADDING", (1, 0), (1, 0), 3 * mm)]))
    el = [zag, Spacer(1, 7 * mm)]
    # stavke
    data = [["#", "Ident", "Naziv", "Količina", "JM", "Cijena €", "Rabat", "Iznos €"]]
    for i, s in enumerate(v["stavke"], 1):
        data.append([str(i), s["pantheon_ident"], Paragraph(escape(s["naziv"] or ""), norm), _fmt(s["kolicina"]), s["jm"] or "", _fmt(s["cijena"]), (_fmt(s["rabat"] or 0, 0) + " %") if s["rabat"] else "—", _fmt(s["iznos"])])
    sir = [8 * mm, 20 * mm, 70 * mm, 19 * mm, 10 * mm, 17 * mm, 12 * mm, 22 * mm]         # Σ = 178 mm = širina okvira → zbroj ispod stoji točno pod „Iznos“
    tab = Table(data, colWidths=sir, repeatRows=1)
    stil = [("FONTNAME", (0, 0), (-1, -1), f), ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("FONTNAME", (0, 0), (-1, 0), fb), ("FONTSIZE", (0, 0), (-1, 0), 7.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(ANT)), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"), ("ALIGN", (5, 0), (-1, -1), "RIGHT"), ("ALIGN", (0, 0), (0, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor(LINIJA)), ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("TEXTCOLOR", (0, 1), (0, -1), colors.HexColor(SIVA)), ("TEXTCOLOR", (1, 1), (1, -1), colors.HexColor(SIVA)), ("FONTNAME", (7, 1), (7, -1), fb)]
    for r in range(2, len(data), 2):
        stil.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#FAF9F6")))
    tab.setStyle(TableStyle(stil))
    el.append(tab)
    # zbroj
    redovi_zb = ([["Ukupno bez rabata", _fmt(d["bruto"]) + " €"], ["Rabat", "− " + _fmt(d["rabat_iznos"]) + " €"]] if d["rabat_iznos"] > 0.005 else []) + \
        [["Osnovica", _fmt(d["neto"]) + " €"], ["PDV 25 %", _fmt(d["pdv"]) + " €"], ["UKUPNO ZA PLATITI", _fmt(d["ukupno"]) + " €"]]
    zb = Table(redovi_zb, colWidths=[45 * mm, 32 * mm], hAlign="RIGHT")
    zb.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), f), ("FONTSIZE", (0, 0), (-1, -1), 9), ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("TEXTCOLOR", (0, 0), (0, -2), colors.HexColor(SIVA)),
                            ("FONTNAME", (0, -1), (-1, -1), fb), ("FONTSIZE", (0, -1), (-1, -1), 10.5), ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor(ACC_SOFT)), ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor(ACC)),
                            ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.HexColor(ACC)), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (1, 0), (1, -1), 6)]))
    el += [Spacer(1, 3 * mm), KeepTogether([zb])]
    el += [Spacer(1, 6 * mm), Paragraph("UVJETI", lbl),
           Paragraph("Cijene su izražene u eurima bez PDV-a. Količine ploča obračunavaju se po površini za naplatu, trake i kantiranje po dužnom metru. "
                     "Ponuda vrijedi %d dana od datuma izdavanja i informativna je do potvrde kupca." % d["vrijedi_dana"], sitno)]
    if d["napomena"]:
        el += [Spacer(1, 4 * mm), Paragraph("NAPOMENA", lbl), Paragraph(escape(d["napomena"]).replace("\n", "<br/>"), norm)]
    if kontakt:
        el += [Spacer(1, 8 * mm), Paragraph(escape(KO.potpis(conn, tko)).replace("\n", "<br/>"), norm)]
    doc.build(el, onFirstPage=zaglavlje, onLaterPages=zaglavlje)
    return put


def napravi(conn, verzija_id, mapa, tko=None):
    """HTML + (ako može) PDF u mapu; vraća dict(html, pdf). `tko` = tko šalje (kontakt i potpis na ponudi)."""
    d = podaci(conn, verzija_id)
    os.makedirs(mapa, exist_ok=True)
    osnova = "Ponuda_%s_v%d" % (d["nalog"]["naziv"], d["verzija"]["verzija"])
    h = os.path.join(mapa, osnova + ".html")
    open(h, "w", encoding="utf-8").write(html(conn, verzija_id))
    p = pdf(conn, verzija_id, os.path.join(mapa, osnova + ".pdf"), tko=tko)
    return dict(html=h, pdf=p, naslov=d["naslov"], neto=d["neto"], ukupno=d["ukupno"])
