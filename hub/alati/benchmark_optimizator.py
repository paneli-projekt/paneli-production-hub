"""benchmark_optimizator.py — Hubov optimizator (D-19 izbor) protiv PanelWizarda na CPO datotekama.
PW referenca = površina za naplatu rekonstruirana iz PW stabla rezova (obracun.naplata_iz_cpo, kerf 16); Hub slaže s kerfom pile 5 (D-72).
    py -m hub.alati.benchmark_optimizator ..\05_NALOZI_ZA_TEST [izlaz.csv] [--md izvjestaj.md]          (testni nalozi, regresija 22a)
    py -m hub.alati.benchmark_optimizator C:\PW_CPO_DANAS --rekurzivno --md paralelno_2026-09-16.md    (paralelno razdoblje, D-73)"""
import sys, os, glob, csv
from hub.formati import cpo_rw
from hub.optimizacija import obracun, pila_optimizator as po

def run(root, out=None, rekurzivno=False):
    """root = mapa testnih naloga (…/_NALOG/03_export_pila/*.cpo) ili, uz rekurzivno=True, bilo koja mapa s PW CPO datotekama
    (paralelno razdoblje, D-73: dnevna usporedba stvarnih naloga)."""
    rows = []
    files = sorted(glob.glob(os.path.join(root, '**', '*.[cC][pP][oO]'), recursive=True)) if rekurzivno else \
        sorted(glob.glob(os.path.join(root, '*', '03_export_pila', '*.cpo')))
    for f in files:
        d = cpo_rw.parse(f); s = d['inv'][0]
        ploca = (s['L'], s['W']); trim = s['trim'][0]; god = d['ctl1']['grain'] == 'Y'
        dijelovi = [(o['idx'], o['W'], o['L'], o['qty']) for o in d['ord']]
        pw = obracun.naplata_iz_cpo(d)
        rp = d['material'].upper().startswith(('RP', 'ZO'))
        try:
            sh, oc, nacin, _ = po.najbolje(dijelovi, ploca, trim, 5.0, god)     # slaganje s kerfom pile (D-72), naplata s 16
            hub = dict(ploca=oc['ploca'], m2=oc['m2_naplata'], nacin=nacin, rezova=oc['rezova'])
        except ValueError as e:
            hub = dict(ploca=None, m2=None, nacin='GRESKA: ' + str(e)[:40], rezova=None)
        rows.append(dict(nalog=os.path.basename(os.path.dirname(os.path.dirname(f))) if not rekurzivno else os.path.relpath(os.path.dirname(f), root),
                         cpo=os.path.basename(f), materijal=d['material'], god=int(god), rp=int(rp),
                         kom=sum(o['qty'] for o in d['ord']), pw_ploca=pw['ploca'], pw_m2=pw['m2_naplata'],
                         hub_ploca=hub['ploca'], hub_m2=hub['m2'], hub_nacin=hub['nacin'], hub_rezova=hub['rezova'],
                         razlika_m2=None if hub['m2'] is None else round(hub['m2'] - pw['m2_naplata'], 2)))
    if out:
        with open(out, 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=rows[0].keys(), delimiter=';'); w.writeheader(); w.writerows(rows)
    return rows

def markdown(rows, naslov='Paralelno razdoblje — Hub vs PanelWizard'):
    r = [x for x in rows if not x['rp'] and x['hub_m2'] is not None]
    L = ['# %s' % naslov, '', '| Nalog | CPO | Materijal | PW m² / ploča | Hub m² / ploča | Razlika | Način |', '|---|---|---|---|---|---|---|']
    for x in rows:
        L.append('| %s | %s | %s | %s / %s | %s / %s | %s | %s |' % (x['nalog'], x['cpo'], x['materijal'][:24], x['pw_m2'], x['pw_ploca'],
                                                                 '—' if x['hub_m2'] is None else x['hub_m2'], '—' if x['hub_ploca'] is None else x['hub_ploca'],
                                                                 '—' if x['razlika_m2'] is None else ('%+.2f' % x['razlika_m2']), x['hub_nacin']))
    if r:
        tp = sum(x['pw_m2'] for x in r); th = sum(x['hub_m2'] for x in r)
        L += ['', 'Ploče (bez RP/ZO): %d materijala, PW %.2f m² / %d ploča, Hub %.2f m² / %d ploča (%+.1f %%); Hub bolje %d, isto %d, slabije %d.' % (
            len(r), tp, sum(x['pw_ploca'] for x in r), th, sum(x['hub_ploca'] for x in r), 100 * (th / tp - 1),
            sum(1 for x in r if x['razlika_m2'] < -0.005), sum(1 for x in r if abs(x['razlika_m2']) < 0.005), sum(1 for x in r if x['razlika_m2'] > 0.005))]
    gr = [x for x in rows if x['hub_m2'] is None]
    if gr:
        L += ['', '**Hub nije mogao složiti (%d):** ' % len(gr) + ', '.join('%s (%s)' % (x['cpo'], x['hub_nacin']) for x in gr)]
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Hubov optimizator vs PanelWizard CPO datoteke (benchmark ili paralelno razdoblje, D-73)')
    ap.add_argument('mapa', help='05_NALOZI_ZA_TEST ili (uz --rekurzivno) bilo koja mapa s PW CPO datotekama')
    ap.add_argument('csv', nargs='?', help='izlazni CSV')
    ap.add_argument('--rekurzivno', action='store_true', help='svi *.cpo ispod mape (stvarni nalozi u paralelnom razdoblju)')
    ap.add_argument('--md', help='Markdown izvještaj')
    a = ap.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    rows = run(a.mapa, a.csv, a.rekurzivno)
    if a.md:
        open(a.md, 'w', encoding='utf-8').write(markdown(rows))
        print('Izvjestaj:', a.md)
    r = [x for x in rows if not x['rp'] and x['hub_m2'] is not None]
    tp = sum(x['pw_m2'] for x in r); th = sum(x['hub_m2'] for x in r)
    print('ploče (bez RP/ZO): %d materijala, PW %.2f m² / %d ploča, Hub %.2f m² / %d ploča (%+.1f %%); isto %d, Hub manje %d, Hub više %d' % (
        len(r), tp, sum(x['pw_ploca'] for x in r), th, sum(x['hub_ploca'] for x in r), 100 * (th / tp - 1),
        sum(1 for x in r if abs(x['razlika_m2']) < 0.005), sum(1 for x in r if x['razlika_m2'] < -0.005), sum(1 for x in r if x['razlika_m2'] > 0.005)))
    for x in sorted(r, key=lambda x: -x['razlika_m2'])[:8]:
        print('  %-13s %-22s PW %6.2f/%2d  Hub %6.2f/%2d  %+5.2f  %s' % (x['cpo'], x['materijal'][:22], x['pw_m2'], x['pw_ploca'], x['hub_m2'], x['hub_ploca'], x['razlika_m2'], x['hub_nacin']))
