"""benchmark_optimizator.py — Hubov optimizator (D-19 izbor) protiv PanelWizarda na svim CPO datotekama testnih naloga.
PW referenca = površina za naplatu rekonstruirana iz PW stabla rezova (obracun.naplata_iz_cpo, kerf 16).
Upotreba: python3 benchmark_optimizator.py <mapa 05_NALOZI_ZA_TEST> [izlaz.csv]"""
import sys, os, glob, csv
from hub.formati import cpo_rw
from hub.optimizacija import obracun, pila_optimizator as po

def run(root, out=None):
    rows = []
    for f in sorted(glob.glob(os.path.join(root, '*', '03_export_pila', '*.cpo'))):
        d = cpo_rw.parse(f); s = d['inv'][0]
        ploca = (s['L'], s['W']); trim = s['trim'][0]; god = d['ctl1']['grain'] == 'Y'
        dijelovi = [(o['idx'], o['W'], o['L'], o['qty']) for o in d['ord']]
        pw = obracun.naplata_iz_cpo(d)
        rp = d['material'].upper().startswith(('RP', 'ZO'))
        try:
            sh, oc, nacin, _ = po.najbolje(dijelovi, ploca, trim, obracun.KERF_OBRACUN, god)
            hub = dict(ploca=oc['ploca'], m2=oc['m2_naplata'], nacin=nacin, rezova=oc['rezova'])
        except ValueError as e:
            hub = dict(ploca=None, m2=None, nacin='GRESKA: ' + str(e)[:40], rezova=None)
        rows.append(dict(nalog=f.split(os.sep)[-3], cpo=os.path.basename(f), materijal=d['material'], god=int(god), rp=int(rp),
                         kom=sum(o['qty'] for o in d['ord']), pw_ploca=pw['ploca'], pw_m2=pw['m2_naplata'],
                         hub_ploca=hub['ploca'], hub_m2=hub['m2'], hub_nacin=hub['nacin'], hub_rezova=hub['rezova'],
                         razlika_m2=None if hub['m2'] is None else round(hub['m2'] - pw['m2_naplata'], 2)))
    if out:
        with open(out, 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=rows[0].keys(), delimiter=';'); w.writeheader(); w.writerows(rows)
    return rows

if __name__ == '__main__':
    rows = run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    r = [x for x in rows if not x['rp'] and x['hub_m2'] is not None]
    tp = sum(x['pw_m2'] for x in r); th = sum(x['hub_m2'] for x in r)
    print('ploče (bez RP/ZO): %d materijala, PW %.2f m² / %d ploča, Hub %.2f m² / %d ploča (%+.1f %%); isto %d, Hub manje %d, Hub više %d' % (
        len(r), tp, sum(x['pw_ploca'] for x in r), th, sum(x['hub_ploca'] for x in r), 100 * (th / tp - 1),
        sum(1 for x in r if abs(x['razlika_m2']) < 0.005), sum(1 for x in r if x['razlika_m2'] < -0.005), sum(1 for x in r if x['razlika_m2'] > 0.005)))
    for x in sorted(r, key=lambda x: -x['razlika_m2'])[:8]:
        print('  %-13s %-22s PW %6.2f/%2d  Hub %6.2f/%2d  %+5.2f  %s' % (x['cpo'], x['materijal'][:22], x['pw_m2'], x['pw_ploca'], x['hub_m2'], x['hub_ploca'], x['razlika_m2'], x['hub_nacin']))
