# -*- coding: utf-8 -*-
"""Slanje e-pošte iz Huba (D-41; podaci od Igora, 15. 9. 2026.): poslužitelj hostinga `mail.paneliprojekt.hr`, SMTP 465 (SSL/TLS),
korisnik `prodaja@paneliprojekt.hr`, lozinka = lozinka tog računa.

Postavke žive u tablici `postavke` (smtp_host, smtp_port, smtp_user, mail_od, mail_od_naziv, mail_kopija); LOZINKA nikad ne ide u bazu ni u Git:
čita se iz varijable okoline `HUB_SMTP_LOZINKA` ili iz datoteke `smtp_lozinka.txt` uz bazu (postavka `smtp_lozinka_datoteka`) —
datoteka je u .gitignore. Ako lozinke nema, slanje vrati jasnu poruku, a ponuda se može poslati ručno (ured, kao i danas).

    py -m hub.nalozi.mail --db hub.db --proba igor@primjer.hr        (probna poruka)
"""
import argparse
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from .. import db
from ..db import postavka, postavi, dnevnik, sada

ZADANO = dict(smtp_host="mail.paneliprojekt.hr", smtp_port="465", smtp_user="prodaja@paneliprojekt.hr", mail_od="prodaja@paneliprojekt.hr",
              mail_od_naziv="Paneli projekt d.o.o.", mail_kopija="")


class MailGreska(RuntimeError):
    pass


def postavke_smtp(conn):
    p = {k: postavka(conn, k, v) for k, v in ZADANO.items()}
    p["smtp_port"] = int(p["smtp_port"] or 465)
    dat = postavka(conn, "smtp_lozinka_datoteka") or os.path.join(os.path.dirname(os.path.abspath(db.putanja_baze())), "smtp_lozinka.txt")
    p["lozinka_datoteka"] = dat
    loz = os.environ.get("HUB_SMTP_LOZINKA")
    if not loz and os.path.isfile(dat):
        loz = open(dat, encoding="utf-8").read().strip()
    p["lozinka"] = loz or ""
    p["spreman"] = bool(loz)
    return p


def upisi_postavke(conn, **kv):
    """Promjena SMTP postavki (bez lozinke) — npr. upisi_postavke(conn, mail_kopija='ured@paneliprojekt.hr')."""
    for k, v in kv.items():
        if k not in ZADANO:
            raise MailGreska("nepoznata postavka %s" % k)
        postavi(conn, k, str(v), "SMTP / e-pošta (D-41)")
    conn.commit()
    return postavke_smtp(conn)


def poruka(p, na, predmet, tekst, html=None, prilozi=(), cc=None):
    msg = EmailMessage()
    msg["From"] = formataddr((p["mail_od_naziv"] or "", p["mail_od"]))
    msg["To"] = na if isinstance(na, str) else ", ".join(na)
    kopija = [x for x in ((cc or "") + "," + (p.get("mail_kopija") or "")).split(",") if x.strip()]
    if kopija:
        msg["Cc"] = ", ".join(x.strip() for x in kopija)
    msg["Subject"] = predmet
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=(p["mail_od"].split("@")[-1] if "@" in p["mail_od"] else None))
    msg.set_content(tekst)
    if html:
        msg.add_alternative(html, subtype="html")
    for put in prilozi:
        ime = os.path.basename(put)
        ext = ime.lower().rsplit(".", 1)[-1] if "." in ime else ""
        mt, st = {"pdf": ("application", "pdf"), "xml": ("application", "xml"), "html": ("text", "html"), "csv": ("text", "csv")}.get(ext, ("application", "octet-stream"))
        with open(put, "rb") as f:
            msg.add_attachment(f.read(), maintype=mt, subtype=st, filename=ime)
    return msg


def posalji(conn, na, predmet, tekst, html=None, prilozi=(), cc=None, tko="web", nalog_id=None, suho=False):
    """Pošalji poruku preko SMTP SSL. Vraća dict(poslano, na, cc, predmet, prilozi, message_id). suho: sastavi poruku, ne šalji."""
    p = postavke_smtp(conn)
    if not na:
        raise MailGreska("nema adrese primatelja")
    if not p["spreman"] and not suho:
        raise MailGreska("SMTP lozinka nije postavljena — upisati je u %s (ili HUB_SMTP_LOZINKA); do tada ponudu poslati ručno" % p["lozinka_datoteka"])
    msg = poruka(p, na, predmet, tekst, html, prilozi, cc)
    if not suho:
        try:
            with smtplib.SMTP_SSL(p["smtp_host"], p["smtp_port"], context=ssl.create_default_context(), timeout=30) as s:
                s.login(p["smtp_user"], p["lozinka"])
                s.send_message(msg)
        except (smtplib.SMTPException, OSError) as e:
            raise MailGreska("slanje nije uspjelo (%s:%s, %s): %s" % (p["smtp_host"], p["smtp_port"], p["smtp_user"], e))
    if nalog_id:
        dnevnik(conn, tko, "nalog", nalog_id, "mail", "%s%s: %s" % ("[suho] " if suho else "", msg["To"], predmet))
        conn.commit()
    return dict(poslano=not suho, na=msg["To"], cc=msg.get("Cc"), predmet=predmet, prilozi=[os.path.basename(x) for x in prilozi], message_id=msg["Message-ID"], kada=sada())


def main(argv=None):
    ap = argparse.ArgumentParser(description="E-pošta iz Huba (D-41)")
    ap.add_argument("--db")
    ap.add_argument("--proba", help="pošalji probnu poruku na ovu adresu")
    ap.add_argument("--postavke", action="store_true", help="ispiši SMTP postavke")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    conn = db.spoji(a.db)
    p = postavke_smtp(conn)
    if a.postavke or not a.proba:
        print("SMTP %s:%s  korisnik %s  od %s <%s>  kopija: %s  lozinka: %s (%s)" % (p["smtp_host"], p["smtp_port"], p["smtp_user"], p["mail_od_naziv"], p["mail_od"],
                                                                                      p["mail_kopija"] or "—", "postavljena" if p["spreman"] else "NEMA", p["lozinka_datoteka"]))
    if a.proba:
        try:
            r = posalji(conn, a.proba, "Proba — Paneli Production Hub", "Ovo je probna poruka iz Huba (D-41). Ako je stigla, slanje ponuda radi.")
            print("poslano na", r["na"])
        except MailGreska as e:
            print("GRESKA:", e)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
