"""Benchmark testnih naloga: pila (PanelWizard -> CPO) vs nesting (PPNEST -> bNest) vs Pantheon ponuda.
Pokretanje iz CLAUDE_COWORK:  python Paneli_Production_Hub\20_ANALIZA\skripte\benchmark_nalozi.py
Izlaz: Paneli_Production_Hub\20_ANALIZA\benchmark_nalozi.csv
"""
import os, sys, glob, re, csv, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from hub.formati.parseri import parse_cpo, parse_ppnest_csv, parse_mno

ROOT = os.environ.get('HUB_ROOT') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
NAL = os.path.join(ROOT, '05_NALOZI_ZA_TEST')
OUT = os.path.join(ROOT, '20_ANALIZA', 'benchmark_nalozi.csv')

def ponuda_stavke(pdf):
    try:
        txt = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
    except FileNotFoundError:
        return [], None
    items = re.findall(r'^\s*(\d+)\s+((?:IV|RP|US|TR|OK|PR)\d{6})\s+(.+?)\s{2,}([\d.]+)\s+(M2|M|KOM|KPT|PAR)\s+', txt, re.M)
    br = re.search(r'Ponuda br\. (\S+)', txt)
    def num(x):  # Pantheon: tisuće s točkom, decimale s točkom -> '1.000.00'
        x = x.replace(',', '.')
        return float(x.replace('.', '', x.count('.') - 1)) if x.count('.') > 1 else float(x)
    return [(i[1], i[2].strip(), num(i[3]), i[4]) for i in items], (br.group(1) if br else None)

def match(name, cpos):
    best = (0, None)
    words = [w for w in name.upper().replace('MM', ' ').split() if len(w) > 3]
    for c in cpos:
        n = c['material'].upper().replace('_', ' ')
        sc = sum(1 for w in words if w in n)
        if re.search(r'\b%d\b' % int(c['thickness']), name.replace('MM', ' ')): sc += 1
        if sc > best[0]: best = (sc, c)
    return best[1] if best[0] >= 2 else None

rows = []
for order in sorted(glob.glob(os.path.join(NAL, '_*'))):
    on = os.path.basename(order)
    if 'PREDLOZAK' in on: continue
    cpos = [parse_cpo(c) for c in sorted(glob.glob(os.path.join(order, '03_export_pila', '*.cpo')))]
    csvs = {os.path.basename(c): parse_ppnest_csv(c) for c in glob.glob(os.path.join(order, '04_export_nesting', '**', '*.CSV'), recursive=True)
            + [c for c in glob.glob(os.path.join(ROOT, '03_NESTING_APLIKACIJA', 'primjeri_ulaza', '*.CSV')) if on.strip('_').split('_')[0] in os.path.basename(c)]}
    mnos = {os.path.basename(m): parse_mno(m) for m in glob.glob(os.path.join(order, '04_export_nesting', '**', '*.mno'), recursive=True)
            + glob.glob(os.path.join(ROOT, '03_NESTING_APLIKACIJA', 'export_za_nesting', '**', '*.mno'), recursive=True)}
    pdfs = glob.glob(os.path.join(order, '05_pantheon', '*.pdf'))
    stavke, br = ponuda_stavke(pdfs[0]) if pdfs else ([], None)
    n_st = len(stavke)
    for c in cpos:
        # nesting CSV s istim materijalom (po debljini + riječima)
        nest = None
        for k, v in csvs.items():
            if v and int(float(v[0]['MAT DEB'])) == int(c['thickness']) and abs(sum(r['_qty'] for r in v) - c['parts_qty']) <= 6:
                if nest is None or abs(sum(r['_qty'] for r in v) - c['parts_qty']) < abs(sum(r['_qty'] for r in nest[1]) - c['parts_qty']):
                    nest = (k, v)
        mno = None
        for k, v in mnos.items():
            if nest and k.startswith(nest[0].rsplit('_', 2)[0]):
                mno = v
        pon = None
        if not c['material'].upper().startswith(('RP', 'ZO', 'PS')):
            cands = [(ident, name, q) for ident, name, q, mj in stavke if ident.startswith('IV') and mj == 'M2']
            best = (0, None)
            for ident, name, q in cands:
                words = [w for w in re.sub(r'[^A-Z0-9 ]', ' ', c['material'].upper().replace('_', ' ')).split() if len(w) > 2 and not w.endswith('MM') and not w.isdigit()]
                sc = sum(1 for w in words if w in name.upper())
                if re.search(r'\b%d ?MM\b' % int(c['thickness']), name.upper()): sc += 1
                else: continue
                if sc > best[0]: best = (sc, (ident, name, q))
            pon = best[1] if best[0] >= 2 else None
        rows.append(dict(nalog=on, ponuda=br, ponuda_stavki=n_st, cpo=c['file'], materijal=c['material'], deb=int(c['thickness']),
                         kom=c['parts_qty'], m2_dijelovi=c['parts_area_m2'], pila_ploca=c['sheets'],
                         pila_m2_ploca=round(c['sheets'] * c['sheet_area_m2'], 2), pila_iskor=round(100 * (c['util_gross'] or 0), 1),
                         pila_rezova=c['cuts'],
                         nest_csv=nest[0] if nest else '', nest_kom=sum(r['_qty'] for r in nest[1]) if nest else '',
                         nest_cix=sum(1 for r in nest[1] if r.get('CIX')) if nest else '',
                         nest_ploca=mno['sheets_n'] if mno else '', nest_iskor=round(100 * mno['util'], 1) if mno and mno['util'] else '',
                         ponuda_ident=pon[0] if pon else '', ponuda_m2=pon[2] if pon else '',
                         ponuda_vs_dijelovi=round(pon[2] / c['parts_area_m2'], 2) if pon and c['parts_area_m2'] else ''))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter=';'); w.writeheader(); w.writerows(rows)
print('zapisano', OUT, len(rows), 'redaka')
for r in rows:
    print(f"{r['nalog']:16s} {r['materijal'][:22]:22s} {r['deb']:3d} {r['kom']:4d} {r['m2_dijelovi']:6.2f}  pila {r['pila_ploca']:2d} pl {r['pila_iskor']:5.1f}%  nest kom {str(r['nest_kom']):>3s} {str(r['nest_ploca']):>2s} pl {str(r['nest_iskor']):>5s}%  ponuda {str(r['ponuda_m2']):>6s} m2 ({r['ponuda_vs_dijelovi']})")
