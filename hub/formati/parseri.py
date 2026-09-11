"""Parseri formata koje Paneli Production Hub mora čitati/pisati (audit, 10.9.2026.).

CPW  - export klijentske aplikacije (PPW) i PanelWizard-a  -> ulaz u PanelWizard / PPNEST
CPO  - Biesse/Selco OSI datoteka koju PanelWizard šalje pili (Selco Sektor 450); sadrži i optimirane sheme rezanja
CSV  - popis elemenata koji PPNEST šalje u bNest (Biesse bSolid/bNest)
TXT  - interni zapis naloga PPNEST-a (isti sadržaj kao CSV, "ključ / vrijednost" po recima)
CIX  - Biesse CIX program po elementu (kontura + glodanje), generira PPNEST
MNO  - rezultat nestinga (XML) iz bNesta: listovi, pozicije, PartUsedArea
lbl.xml - CutList za etikete (bNest)
"""
import csv, io, os, re, xml.etree.ElementTree as ET
from collections import defaultdict

# ---------------------------------------------------------------- CPW
def parse_cpw(path):
    """Vraća listu elemenata: dict(materijal, debljina, naziv, L, W, kom, rub[4] (kod), traka[4] (naziv)).
    Redoslijed rubova u datoteci: 4 koda (M/A/prazno) pa 4 naziva trake; smjer = (duža1, kraća1, duža2, kraća2)?
    NAPOMENA: točan redoslijed strana treba potvrditi s Igorom (audit pitanje)."""
    out = []
    raw = open(path, 'rb').read().decode('cp1250', errors='replace')
    mat, deb = None, None
    for line in raw.splitlines():
        f = line.split(';')
        if not f or not f[0]:
            continue
        if f[0] == 'FORMAT':
            continue
        if f[0] == 'MATERIJAL':
            mat, deb = f[1], f[2]
        elif f[0] == 'ELEMENT':
            out.append(dict(materijal=mat, debljina=deb, naziv=f[1], L=int(float(f[2])), W=int(float(f[3])),
                            kom=int(float(f[4])), rub=f[5:9], traka=f[9:13]))
    return out

# ---------------------------------------------------------------- CPO
def parse_cpo(path):
    """Selco OSI .cpo (PanelWizard export). Vraća dict s headerom, listom naloga (ORD), dijelova (PRT),
    ploča iz inventara (INV), shema (PAT) i rezova (CUT)."""
    d = dict(file=os.path.basename(path), inv=[], ord=[], prt=[], pat=[])
    cur_pat = None
    txt = open(path, 'rb').read().decode('cp1250', errors='replace')
    for line in txt.splitlines():
        if not line.strip():
            continue
        tag = line[:4]
        f = [x.strip() for x in line[5:].split(',')]
        if tag == 'HDR1':
            d['program_no'], d['material'] = f[0], f[1]
        elif tag == 'HDR2':
            d['date'], d['time'] = f[0], f[1]
        elif tag == 'CTL2':
            d['kerf'] = float(f[0])
        elif tag == 'THK1':
            d['thickness'], d['stack_h'] = float(f[0]), float(f[1])
        elif tag == 'INV1':
            d['inv'].append(dict(code=f[0], qty=int(f[1]), price=float(f[2]), W=float(f[3]), L=float(f[4]),
                                 trim=[float(x) for x in f[5:9]]))
        elif tag == 'INV2':
            d['inv'][-1]['name'] = f[0]
        elif tag == 'ORD1':
            d['ord'].append(dict(qty=int(f[0]), qty2=int(f[1]), W=float(f[2]), L=float(f[3]), grain=f[4], flag=f[5]))
        elif tag == 'ORD2':
            d['ord'][-1]['price'] = float(f[0]); d['ord'][-1]['label'] = f[1]
        elif tag == 'ORD3':
            d['ord'][-1]['idx'] = int(f[1])
        elif tag == 'PRT1':
            d['prt'].append(dict(qty=int(f[0]), n=int(f[1]), W=float(f[2]), L=float(f[3]), name=f[7] if len(f) > 7 else ''))
        elif tag == 'PRT3':
            # f[0] = maska rubova (npr. 1111), zatim po 3 polja po strani (kod, naziv, kratki)
            d['prt'][-1]['edge_mask'] = f[0]
            d['prt'][-1]['edges'] = [f[i] for i in (1, 4, 7, 10) if i < len(f)]
        elif tag == 'PRT4':
            d['prt'][-1]['customer'] = f[0]
        elif tag == 'PAT1':
            cur_pat = dict(no=f[0], orient=f[1], qty=int(f[2]), cuts=[])
            d['pat'].append(cur_pat)
        elif tag == 'PAT2':
            cur_pat['util_pct'] = float(f[0])
        elif tag == 'CUT1' and cur_pat is not None:
            cur_pat['cuts'].append(dict(level=int(f[0]), pos=float(f[1]), is_part=f[2] == '1', part=f[3]))
    # izvedene veličine
    parts_area = sum(p['qty'] * p['W'] * p['L'] for p in d['prt']) / 1e6
    d['parts_area_m2'] = round(parts_area, 3)
    d['parts_qty'] = sum(p['qty'] for p in d['prt'])
    d['sheets'] = sum(p['qty'] for p in d['pat'])
    if d['inv']:
        s = d['inv'][0]
        d['sheet_dim'] = (s['L'], s['W'])
        d['sheet_area_m2'] = s['L'] * s['W'] / 1e6
        d['util_gross'] = round(parts_area / (d['sheets'] * d['sheet_area_m2']), 4) if d['sheets'] else None
    d['cuts'] = sum(len(p['cuts']) * p['qty'] for p in d['pat'])
    return d

# ---------------------------------------------------------------- PPNEST CSV
CSV_COLS = ['RB', 'RN', 'NAZIV ELEMENTA', 'BROJ ELE', 'IME DASKE', 'KONACNA DIMENZIJA', 'SIRINA', 'DUZINA', 'KOLICINA',
            'SIFRA MAT', 'MAT DEB', 'MAT NAZIV', 'GOD', 'PROGRAM1', 'PROGRAM2', 'OBRADA', 'RUB1', 'TR1SIFRA', 'RUB2',
            'TRS2IFRA', 'RUB3', 'TR3SIFRA', 'RUB4', 'TR4SIFRA', 'LJEPLJENJE', 'CIX', 'NAPOMENA', 'GLODANJE']

def parse_ppnest_csv(path):
    raw = open(path, 'rb').read()
    for enc in ('utf-8-sig', 'cp1250'):
        try:
            txt = raw.decode(enc); break
        except UnicodeDecodeError:
            continue
    rows = list(csv.DictReader(io.StringIO(txt), delimiter=';'))
    for r in rows:
        r['_W'] = float(r['SIRINA']); r['_L'] = float(r['DUZINA']); r['_qty'] = int(float(r['KOLICINA']))
    return rows

def parse_ppnest_txt(path):
    """TXT = blokovi 'KUPAC/NALOG/MATERIJAL/DEBLJINA/ŠIFRA/GOD/ELEMENTSVI/<rb>/<kupac>' + 'ELEMENT' + fiksni redoslijed polja."""
    txt = open(path, 'rb').read().decode('utf-8', errors='replace')
    lines = txt.split('\n')
    elems = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == 'ELEMENT':
            blk = [x.rstrip('\r') for x in lines[i + 1:i + 32]]
            elems.append(dict(naziv=blk[0], L=blk[1], W=blk[2], kom=blk[3], sifra=blk[4], deb=blk[5], mat=blk[6], cix=[x for x in blk if re.match(r'\d{6}_\d{6}$', x)]))
            i += 30
        else:
            i += 1
    return elems

# ---------------------------------------------------------------- MNO (bNest rezultat)
def parse_mno(path):
    root = ET.parse(path).getroot()
    res = dict(descr=root.findtext('COMMESSA/DESCR', ''), sheets=[])
    for f in root.iter('FOGLIO'):
        name = f.get('NAME', '')
        m = re.search(r'(\d{4})[X\-](\d{4})', name)
        L, W = (int(m.group(1)), int(m.group(2))) if m else (None, None)
        st = f.find('.//StatisticInfo')
        used = float(st.get('PartUsedArea', 0)) if st is not None else None
        n_parts = len(f.findall('.//Production/POS')) or len(f.findall('.//POS'))
        res['sheets'].append(dict(id=f.get('ID'), qty=int(f.get('QTY', 1)), name=name, L=L, W=W,
                                  used_mm2=used, util=round(used / (L * W), 4) if used and L else None, parts=n_parts))
    tot_used = sum(s['used_mm2'] or 0 for s in res['sheets'])
    tot_area = sum((s['L'] or 0) * (s['W'] or 0) for s in res['sheets'])
    res['sheets_n'] = len(res['sheets'])
    res['util'] = round(tot_used / tot_area, 4) if tot_area else None
    res['used_m2'] = round(tot_used / 1e6, 2); res['area_m2'] = round(tot_area / 1e6, 2)
    return res

def parse_lbl(path):
    root = ET.parse(path).getroot()
    return [dict(p.attrib) for p in root.iter('Part')]

if __name__ == '__main__':
    import sys, json
    p = sys.argv[1]
    ext = p.lower().rsplit('.', 1)[-1]
    fn = dict(cpw=parse_cpw, cpo=parse_cpo, csv=parse_ppnest_csv, txt=parse_ppnest_txt, mno=parse_mno, xml=parse_lbl)[ext]
    r = fn(p)
    if ext == 'cpo':
        r = {k: v for k, v in r.items() if k not in ('pat',)}
    print(json.dumps(r, ensure_ascii=False, indent=1, default=str)[:6000])
