"""nalog_io.py — "standardni nalog" Huba: čitanje PPNEST TXT/CSV i CPW, pisanje PPNEST CSV + CIX (bNest) i CPW (PanelWizard).

Sve je izvedeno iz KROJNA.vb (PPNEST 1.2, vlastiti kod) i iz stvarnih datoteka testnih naloga — bez PanelWizard koda.

Element (dict):
  rb, nalog, kupac, L (=MJERA1, duljina, CIX LPX), W (=MJERA2, širina, CIX LPY), kom, sifra_mat, deb, mat, god (0/1),
  traka  = {'L':naziv,'D':naziv,'G':naziv,'O':naziv}   (lijevo, desno, gore, dolje — kako je u PPNEST ekranu)
  tip    = {'L':'M'|'A'|'', ...}                        (M = melamin, A = ABS; prazno = bez trake)
  cix    = id CIX datoteke (bez .cix), napomena, prolaza (1|2), glodalo (12|14)

Redoslijed rubova po formatima (potvrđeno usporedbom PPNEST TXT ↔ CPW ↔ CPO na testnim nalozima):
  CPW  ELEMENT;naziv;L;W;kom;tipL;tipO;tipD;tipG;trakaL;trakaO;trakaD;trakaG;   → (lijevo, dolje, desno, gore) = duža1, kraća1, duža2, kraća2
  CPO  PRT3 maska = [dolje, desno, gore, lijevo]
  CSV  TR1SIFRA=lijevo, TRS2IFRA=desno, TR3SIFRA=gore, TR4SIFRA=dolje (RUBx stupci uvijek prazni)
"""
import csv, io, os, re
from datetime import datetime, timedelta

CSV_HEADER = ('RB;RN;NAZIV ELEMENTA;BROJ ELE;IME DASKE;KONACNA DIMENZIJA;SIRINA;DUZINA;KOLICINA;SIFRA MAT;MAT DEB;MAT NAZIV;GOD;'
              'PROGRAM1;PROGRAM2;OBRADA;RUB1;TR1SIFRA;RUB2;TRS2IFRA;RUB3;TR3SIFRA;RUB4;TR4SIFRA;LJEPLJENJE;CIX;NAPOMENA;GLODANJE')

def _num(s):
    s = str(s).strip().replace(',', '.')
    return int(float(s)) if float(s) == int(float(s)) else float(s)

_TRANS = str.maketrans('ŠšČčĆćŽžĐđ', 'SsCcCcZzDd')

def bez_dijakritika(s):
    """PanelWizard (VB6) ne prikazuje Š/Č/Ć/Ž/Đ ni iz UTF-8 ni iz cp1250 (Igor, 11. 9. 2026.) → u CPW i CPO idu samo ASCII nazivi."""
    return str(s).translate(_TRANS)

def _fmt(x):
    """VB-stil: cijeli broj bez decimala, inače s točkom."""
    return str(int(x)) if float(x) == int(x) else repr(float(x))

# ------------------------------------------------------------------ čitanje
def read_ppnest_txt(path):
    """PPNEST interni TXT: header (KUPAC/NALOG/MATERIJAL/DEBLJINA/ŠIFRA/GOD) + 'ELEMENTSVI' + 33 redaka = SubItems(0..32)."""
    lines = open(path, 'rb').read().decode('utf-8', errors='replace').split('\r\n')
    els = []
    i = 0
    hdr = {}
    while i < len(lines):
        ln = lines[i]
        if ln in ('KUPAC', 'NALOG', 'MATERIJAL', 'DEBLJINA', 'GOD') or ln.endswith('IFRA'):
            hdr[ln if not ln.endswith('IFRA') else 'SIFRA'] = lines[i + 1]; i += 2; continue
        if ln == 'ELEMENTSVI':
            s = lines[i + 1:i + 34]           # SubItems(0..32)
            s += [''] * (33 - len(s))
            els.append(dict(rb=int(s[0] or len(els) + 1), nalog=s[1], kupac=hdr.get('KUPAC', s[1]),
                            L=_num(s[6]), W=_num(s[7]), kom=int(_num(s[8])), sifra_mat=s[9], deb=_num(s[10]), mat=s[11],
                            god=int(_num(s[12] or 0)),
                            traka={'L': s[17], 'D': s[19], 'G': s[21], 'O': s[23]},
                            tip={'L': s[29], 'D': s[30], 'G': s[31], 'O': s[32]},
                            cix=s[25], napomena=s[26], prolaza=int(_num(s[27] or 1)), glodalo=int(_num(s[28] or 12))))
            i += 34; continue
        i += 1
    return els

def read_ppnest_csv(path, kupac=None):
    raw = open(path, 'rb').read()
    txt = raw.decode('utf-8-sig') if b'\xef\xbb\xbf' == raw[:3] or _is_utf8(raw) else raw.decode('cp1250')
    els = []
    for r in csv.DictReader(io.StringIO(txt), delimiter=';'):
        els.append(dict(rb=int(r['RB']), nalog=r['RN'], kupac=kupac or r['RN'], L=_num(r['DUZINA']), W=_num(r['SIRINA']),
                        kom=int(_num(r['KOLICINA'])), sifra_mat=r['SIFRA MAT'], deb=_num(r['MAT DEB']), mat=r['MAT NAZIV'],
                        god=int(_num(r['GOD'] or 0)),
                        traka={'L': r['TR1SIFRA'], 'D': r['TRS2IFRA'], 'G': r['TR3SIFRA'], 'O': r['TR4SIFRA']},
                        tip={k: ('A' if v.upper().startswith('ABS') else ('M' if v else '')) for k, v in
                             (('L', r['TR1SIFRA']), ('D', r['TRS2IFRA']), ('G', r['TR3SIFRA']), ('O', r['TR4SIFRA']))},
                        cix=r['CIX'], napomena=r['NAPOMENA'], prolaza=int(_num(r['GLODANJE'] or 1)),
                        glodalo=14 if _num(r['MAT DEB']) > 20 else 12))
    return els

def _is_utf8(b):
    try: b.decode('utf-8'); return True
    except UnicodeDecodeError: return False

def read_cpw(path, nalog='', kupac=''):
    """CPW (PPW/PanelWizard): FORMAT;CORPUS->PW;002600; / MATERIJAL;naziv;deb; / ELEMENT;naziv;L;W;kom;t1;t2;t3;t4;n1;n2;n3;n4;"""
    raw = open(path, 'rb').read()
    txt = raw.decode('utf-8') if _is_utf8(raw) else raw.decode('cp1250')
    els, mat, deb = [], '', 0
    for ln in txt.splitlines():
        f = ln.split(';')
        if f[0] == 'MATERIJAL':
            mat, deb = f[1], _num(f[2])
        elif f[0] == 'ELEMENT':
            t = f[5:9] + [''] * 4; n = f[9:13] + [''] * 4
            els.append(dict(rb=len(els) + 1, nalog=nalog, kupac=kupac, L=_num(f[2]), W=_num(f[3]), kom=int(_num(f[4])),
                            sifra_mat='', deb=deb, mat=mat, god=0,
                            traka={'L': n[0], 'O': n[1], 'D': n[2], 'G': n[3]}, tip={'L': t[0], 'O': t[1], 'D': t[2], 'G': t[3]},
                            cix='', napomena=f[1], prolaza=2 if (_num(f[2]) < 200 or _num(f[3]) < 200) else 1,
                            glodalo=14 if deb > 20 else 12))
    return els

# ------------------------------------------------------------------ pisanje
_CIX_SEQ = [None]

def dodijeli_cix_ids(els, start=None, brojac=None):
    """Ime CIX-a mora biti jedinstveno ZAUVIJEK — bNest datoteku s istim imenom pregazi (operater, 11. 9. 2026.).
    PPNEST koristi ddMMyy_HHmmss trenutka unosa elementa; Hub isto (privremeno), s globalnim brojačem sekundi unutar procesa
    da se dva izvoza u istoj sekundi ne sudare. U Hubu s bazom: brojac=callable koji vraća sljedeći globalni id (npr. 'H0001234')."""
    if brojac is not None:
        for e in els:
            e['cix'] = brojac()
        return els
    t = start or _CIX_SEQ[0] or datetime.now()
    for e in els:
        e['cix'] = t.strftime('%d%m%y_%H%M%S')
        t += timedelta(seconds=1)
    _CIX_SEQ[0] = t
    return els

def write_ppnest_csv(els, path):
    """Identičan zapis kao KROJNA.vb BTNSNIMI (UTF-8 bez BOM, CRLF, ';')."""
    rows = [CSV_HEADER]
    for e in els:
        rows.append(';'.join([str(e['rb']), e['nalog'], '', '', '%d_ELEMENT' % e['rb'], '', _fmt(e['W']), _fmt(e['L']),
                              str(e['kom']), e['sifra_mat'], _fmt(e['deb']), e['mat'], str(e['god']), '', '', '', '',
                              e['traka']['L'], '', e['traka']['D'], '', e['traka']['G'], '', e['traka']['O'], '',
                              e['cix'], e['napomena'], str(e['prolaza'])]))
    open(path, 'wb').write(('\r\n'.join(rows) + '\r\n').encode('utf-8'))

def cix_text(e):
    """CIX v5 kao iz KROJNA.vb: pravokutna kontura (start na pola donje stranice, u smjeru kazaljke) + ROUTG."""
    L, W, Z = e['L'], e['W'], e['deb']
    dia = e.get('glodalo') or (14 if Z > 20 else 12)
    o = ['BEGIN ID CID3', '    REL = 5.0', 'END ID', '',
         'BEGIN MAINDATA', '    LPX=%s' % _fmt(L), '    LPY=%s' % _fmt(W), '    LPZ=%s' % _fmt(Z), '    ORLST="1"', '    TLCHK=0',
         '    TOOLING=""', '    CUSTSTR=$B$KBsExportToNcRoverNET.XncExtraPanelData$V""', '    FCN=1.000000', '    JIGTH=0',
         '    CKOP=0', '    UNIQUE=0', '    MATERIAL="wood"', '    OPPWKRS=0', '    UNICLAMP=0', '    CHKCOLL=0', '    WTPIANI=0',
         '    COLLTOOL=0', '    CALCEDTH=0', '    ENABLELABEL=0', '    LOCKWASTE=0', '    LOADEDGEOPT=0', '    ITLTYPE=0',
         '    RUNPAV=0', '    XCUT=0', '    YCUT=0', 'END MAINDATA', '',
         'BEGIN VB', '    VBLINE="\'ELEMENT"', 'END VB', '',
         'BEGIN MACRO', '    NAME=NOPRK', '    PARAM,NAME=ABL,VALUE=0', 'END MACRO', '',
         'BEGIN MACRO', 'NAME=GEO', '    PARAM,NAME=LAY,VALUE="GEO"', '    PARAM,NAME=ID,VALUE="P0"', '    PARAM,NAME=SIDE,VALUE=0',
         '    PARAM,NAME=CRN,VALUE="1"', 'END MACRO', '',
         'BEGIN MACRO', '    NAME=START_POINT', '    PARAM,NAME=X,VALUE=%s' % _fmt(L / 2), '    PARAM,NAME=Y,VALUE=0', 'END MACRO', '']
    for xe, ye in ((L, 0), (L, W), (0, W), (0, 0), (L / 2, 0)):
        o += ['BEGIN MACRO', '    NAME=LINE_EP', '    PARAM,NAME=XE,VALUE=%s' % _fmt(xe), '    PARAM,NAME=YE,VALUE=%s' % _fmt(ye), 'END MACRO', '']
    o += ['BEGIN MACRO', '    NAME=ENDPATH', 'END MACRO', '',
          'BEGIN MACRO', '    NAME=ROUTG', '    PARAM,NAME=LAY,VALUE="GEO"', '    PARAM,NAME=ID,VALUE="ROUTG_P0"',
          '    PARAM,NAME=GID,VALUE="P0"', '    PARAM,NAME=THR,VALUE=NO', '    PARAM,NAME=DP,VALUE=%s' % _fmt(Z + 0.15),
          '    PARAM,NAME=DIA,VALUE=%d' % dia, '    PARAM,NAME=TNM,VALUE="%d"' % dia, '    PARAM,NAME=SHP,VALUE=9',
          '    PARAM,NAME=DVR,VALUE=1', '    PARAM,NAME=VTR,VALUE=%d' % e.get('prolaza', 1), '    PARAM,NAME=CRC,VALUE=1',
          '    PARAM,NAME=TIN,VALUE=8', '    PARAM,NAME=AIN,VALUE=45', '    PARAM,NAME=TOU,VALUE=8', '    PARAM,NAME=AOU,VALUE=45',
          'END MACRO', '', 'BEGIN MACRO', '    NAME=ENDPATH', 'END MACRO']
    return '\r\n'.join(o) + '\r\n'

_BSOLID_TPL = None

def alat_za_debljinu(deb):
    """Pravilo operatera nestinga (11. 9. 2026.): do 19 mm glodalo "8D", deblje (do najviše 26 mm) glodalo "14";
    u oba slučaja 2 prolaza, ulaz glodala na L/2 donje stranice."""
    deb = float(deb)
    if deb > 26:
        raise ValueError('debljina %s mm > 26 mm — nesting ne reže tako debele ploče' % _fmt(deb))
    return '8D' if deb <= 19 else '14'

def cix_text_bsolid(e, vtr=2, tnm=None, din=None):
    """CIX u obliku koji operater nestinga ručno postavlja u bSolidu (predložak: 04_STROJEVI\\NESTING\\korekcija\\Korekcija.cix,
    11. 9. 2026.). U odnosu na PPNEST oblik: ORLST=5, kontura počinje u (0,W) i ide (0,0)→(L,0)→(L,W)→(0,W), ROUTG kroz ploču
    (THR=1, DP=0.1), alat po imenu (TNM="8D", DIA=0), kompenzacija CRC=2, 2 prolaza (VTR=2), ulaz/izlaz TIN/TOU 8 mm pod 45°,
    DIN = mjesto ulaza glodala mjereno po konturi od startne točke — u predlošku ≈ sredina donje (duže) stranice; Hub stavlja
    točno W + L/2. Sve ostale parametre (brzine, CKA, OPT, PRP, SDS…) prepisuje iz predloška nepromijenjene."""
    global _BSOLID_TPL
    if _BSOLID_TPL is None:
        _BSOLID_TPL = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cix_bsolid_template.cix'), newline='').read()
    L, W, Z = e['L'], e['W'], e['deb']
    if din is None:
        din = W + L / 2
    if tnm is None:
        tnm = alat_za_debljinu(Z)
    return _BSOLID_TPL.format(L=_fmt(L), W=_fmt(W), Z=_fmt(Z), DIN=_fmt(round(din, 6)), VTR=vtr, TNM=tnm)

def write_cix(els, folder, stil='bsolid', **kw):
    """stil='bsolid' (postavke operatera, zadano od 11. 9. 2026.) ili 'ppnest' (točno kao KROJNA.vb)."""
    os.makedirs(folder, exist_ok=True)
    for e in els:
        txt = cix_text_bsolid(e, **kw) if stil == 'bsolid' else cix_text(e)
        open(os.path.join(folder, e['cix'] + '.cix'), 'wb').write(txt.encode('ascii', errors='replace'))

def write_cpw(els, path, header_once=True, enc='cp1250'):
    """CPW za PanelWizard. header_once=True piše FORMAT/MATERIJAL jednom (kao PPW); False ponavlja ih ispred svakog
    elementa (kao PPNEST — PW prihvaća oboje). Redoslijed rubova: lijevo, dolje, desno, gore."""
    o = []
    mat, deb = bez_dijakritika(els[0]['mat']), els[0]['deb']
    hdr = ['FORMAT;CORPUS->PW;002600;', 'MATERIJAL;%s;%s;' % (mat, _fmt(deb))]
    if header_once: o += hdr
    for e in els:
        if not header_once: o += hdr
        t = e['tip']; n = {k: bez_dijakritika(v) for k, v in e['traka'].items()}
        o.append('ELEMENT;%s;%s;%s;%d;%s;%s;%s;%s;%s;%s;%s;%s;' % (bez_dijakritika(e['napomena']), _fmt(e['L']), _fmt(e['W']), e['kom'],
                 t['L'], t['O'], t['D'], t['G'], n['L'], n['O'], n['D'], n['G']))
    open(path, 'wb').write(('\r\n'.join(o) + '\r\n').encode(enc, errors='replace'))

def write_ppnest_txt(els, path):
    """PPNEST TXT (interni zapis) — da se Hub nalog može otvoriti/usporediti i u starom alatu."""
    o = []
    for e in els:
        o += ['KUPAC', e['kupac'], 'NALOG', e['nalog'], 'MATERIJAL', e['mat'], 'DEBLJINA', _fmt(e['deb']), 'ŠIFRA', e['sifra_mat'],
              'GOD', str(e['god']), 'ELEMENTSVI', str(e['rb']), e['nalog'], '', '', 'ELEMENT', '', _fmt(e['L']), _fmt(e['W']),
              str(e['kom']), e['sifra_mat'], _fmt(e['deb']), e['mat'], str(e['god']), '', '', '', '',
              e['traka']['L'], '', e['traka']['D'], '', e['traka']['G'], '', e['traka']['O'], '', e['cix'], e['napomena'],
              str(e['prolaza']), str(e['glodalo']), e['tip']['L'], e['tip']['D'], e['tip']['G'], e['tip']['O']]
    open(path, 'wb').write(('\r\n'.join(o) + '\r\n').encode('utf-8'))
