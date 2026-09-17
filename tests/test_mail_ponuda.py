# -*- coding: utf-8 -*-
"""D-41: slanje ponude mailom (SMTP SSL hostinga) + PDF / HTML ponude. SMTP je zamijenjen lažnim poslužiteljem — ništa se stvarno ne šalje."""
import os
import pytest

from hub.nalozi import nalozi as N, ponuda as PO, ponuda_pdf as PP, mail as M
from tests.test_nalozi import baza  # noqa: F401
from tests.test_popravci_2026_09_15 import _nalog
from tests.test_obracun_ponuda import baza_o  # noqa: F401


class LazniSMTP:
    poslano = []
    prijave = []

    def __init__(self, host, port, context=None, timeout=None):
        self.host, self.port = host, port

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def login(self, u, p):
        LazniSMTP.prijave.append((self.host, self.port, u, p))

    def send_message(self, msg):
        LazniSMTP.poslano.append(msg)


def test_postavke_i_lozinka(baza_o, tmp_path, monkeypatch):
    monkeypatch.delenv("HUB_SMTP_LOZINKA", raising=False)
    monkeypatch.setenv("HUB_DB", str(tmp_path / "hub.db"))        # lozinka se traži uz bazu — ne uz smtp_lozinka.txt u radnoj mapi (30_NOVI_PROGRAM)
    p = M.postavke_smtp(baza_o)
    assert (p["smtp_host"], p["smtp_port"], p["smtp_user"], p["mail_od"]) == ("mail.paneliprojekt.hr", 465, "prodaja@paneliprojekt.hr", "prodaja@paneliprojekt.hr")
    assert not p["spreman"] and p["lozinka_datoteka"].endswith("smtp_lozinka.txt")
    with pytest.raises(M.MailGreska) as ex:
        M.posalji(baza_o, "x@y.hr", "p", "t")
    assert "lozinka" in str(ex.value)
    monkeypatch.setenv("HUB_SMTP_LOZINKA", "tajna")
    assert M.postavke_smtp(baza_o)["spreman"] and M.postavke_smtp(baza_o)["lozinka"] == "tajna"
    monkeypatch.delenv("HUB_SMTP_LOZINKA")
    (tmp_path / "loz.txt").write_text("iz_datoteke\n")
    M.upisi_postavke(baza_o, mail_kopija="ured@paneliprojekt.hr")
    from hub.db import postavi
    postavi(baza_o, "smtp_lozinka_datoteka", str(tmp_path / "loz.txt"))
    baza_o.commit()
    p = M.postavke_smtp(baza_o)
    assert p["lozinka"] == "iz_datoteke" and p["mail_kopija"] == "ured@paneliprojekt.hr"
    with pytest.raises(M.MailGreska):
        M.upisi_postavke(baza_o, nesto="x")
    r = M.posalji(baza_o, "x@y.hr", "Proba", "tekst", suho=True)
    assert not r["poslano"] and r["cc"] == "ured@paneliprojekt.hr"


def test_ponuda_html_pdf_i_slanje(baza_o, tmp_path, monkeypatch):
    monkeypatch.delenv("HUB_SMTP_LOZINKA", raising=False)
    nid, nm, e1, e2 = _nalog(baza_o)
    n = N.nalog(baza_o, nid)
    v = PO.nova_verzija(baza_o, nid, "IVANA")
    h = PP.html(baza_o, v["id"])
    assert "<table" in h and "IV000090" in h and "UKUPNO" in h
    dok = PP.napravi(baza_o, v["id"], str(tmp_path / "ponude"))
    assert os.path.isfile(dok["html"]) and dok["naslov"].startswith("Ponuda ")
    if dok["pdf"]:
        assert open(dok["pdf"], "rb").read()[:4] == b"%PDF"
    # bez e-maila kupca → greška s uputom
    baza_o.execute("UPDATE kupac SET email = NULL WHERE id = ?", (n["kupac_id"],))
    baza_o.commit()
    with pytest.raises(PO.PonudaGreska) as ex:
        PO.posalji(baza_o, v["id"], "IVANA")
    assert "e-mail" in str(ex.value)
    # s adresom, lažni SMTP
    monkeypatch.setattr(M.smtplib, "SMTP_SSL", LazniSMTP)
    monkeypatch.setenv("HUB_SMTP_LOZINKA", "tajna")
    LazniSMTP.poslano.clear()
    r = PO.posalji(baza_o, v["id"], "IVANA", na="kupac@primjer.hr", mapa=str(tmp_path / "ponude"))
    assert r["status"] == "poslana" and r["poslano_na"] == "kupac@primjer.hr" and r["mail"]["poslano"] and r["pdf_putanja"]
    assert LazniSMTP.prijave[-1] == ("mail.paneliprojekt.hr", 465, "prodaja@paneliprojekt.hr", "tajna")
    msg = LazniSMTP.poslano[-1]
    assert msg["To"] == "kupac@primjer.hr" and msg["From"].endswith("<prodaja@paneliprojekt.hr>") and "Ponuda" in msg["Subject"]
    prilozi = [p.get_filename() for p in msg.iter_attachments()]
    assert len(prilozi) == 1 and prilozi[0].startswith("Ponuda_") and prilozi[0].split(".")[-1] in ("pdf", "html")
    assert baza_o.execute("SELECT COUNT(*) FROM dokument WHERE nalog_id = ? AND vrsta = 'ponuda_pdf'", (nid,)).fetchone()[0] == 1
    assert any("ponuda v1 poslana" in d["razlog"] for d in N.dogadjaji(baza_o, nid))
    # neuspjelo slanje (SMTP greška) → MailGreska, verzija ostaje kakva je bila
    class Pada(LazniSMTP):
        def login(self, u, p):
            raise M.smtplib.SMTPAuthenticationError(535, b"bad")
    monkeypatch.setattr(M.smtplib, "SMTP_SSL", Pada)
    with pytest.raises(M.MailGreska) as ex:
        PO.posalji(baza_o, v["id"], "IVANA", na="kupac@primjer.hr", mapa=str(tmp_path / "ponude"))
    assert "nije uspjelo" in str(ex.value) and PO.verzija(baza_o, v["id"])["status"] == "poslana"


def test_api_posalji(baza_o, monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import hub.api.app as A
    from hub.sifrarnici import prepoznaj as P
    monkeypatch.delenv("HUB_SMTP_LOZINKA", raising=False)
    monkeypatch.setenv("HUB_DB", str(baza_o.dir / "hub.db"))
    A._veza = None
    P.ocisti_kes()
    nid, nm, e1, e2 = _nalog(baza_o)
    v = PO.nova_verzija(baza_o, nid, "IVANA")
    c = TestClient(A.app, raise_server_exceptions=False)
    try:
        r = c.get("/api/mail/postavke")
        assert r.status_code == 200 and "lozinka" not in r.json() and r.json()["smtp_host"] == "mail.paneliprojekt.hr"
        r = c.post("/api/ponuda/%d/posalji" % v["id"], json=dict(na="kupac@primjer.hr", mapa=str(tmp_path)))
        assert r.status_code == 400 and "lozinka" in r.text and not A.veza().in_transaction
        r = c.post("/api/ponuda/%d/posalji" % v["id"], json=dict(na="kupac@primjer.hr", mapa=str(tmp_path), suho=True))
        assert r.status_code == 200 and not r.json()["mail"]["poslano"] and r.json()["status"] == "nacrt"
        monkeypatch.setattr(M.smtplib, "SMTP_SSL", LazniSMTP)
        monkeypatch.setenv("HUB_SMTP_LOZINKA", "tajna")
        r = c.post("/api/ponuda/%d/posalji" % v["id"], json=dict(na="kupac@primjer.hr", mapa=str(tmp_path), tko="IVANA"))
        assert r.status_code == 200 and r.json()["status"] == "poslana"
    finally:
        A._veza = None
