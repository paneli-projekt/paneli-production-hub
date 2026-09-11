"""d09_tri_naloga.py — D-09: tri testna naloga (HUMER, BRATEK, ROMIC) kroz cijeli lanac "na papiru".
Za svaki nalog: ulaz kupca → nalog (materijali/elementi iz PW CPO-a, jer ga imaju sva tri) → exporti (nesting CSV/CIX, PW CPW,
CPO programi) → rezultati (PW ploče, bNest .mno, Hub optimizator) → obračun PW-metodom (m² naplata, metri trake) → ponuda Pantheon.
Upotreba: python3 d09_tri_naloga.py <05_NALOZI_ZA_TEST> <izlaz.md>"""
import sys, os, glob, re, subprocess
from hub.formati import cpo_rw, parseri
from hub.optimizacija import obracun, pila_optimizator as po

NALOZI = {
    '_HUMER_OMIS':    dict(naziv='HUMER_2823_OMIS', ponuda='26-010-002823', tip='CPW iz klijentske aplikacije (PPW) + skice + Excel okova'),
    '_BRATEK_KUPAC1': dict(naziv='BRATEK_3231',     ponuda='26-010-003231', tip='Excel kupca (NARUDŽBA + OKOV)'),
    '_ROMIC_NALOG':   dict(naziv='ROMIC_2423',      ponuda='26-010-002423', tip='sken rukom pisanog upita (PDF)'),
}
# ručno mapiranje PW program ↔ ident materijala u ponudi (po debljini/nazivu)
MAPA = {
    'I_01913': 'IV000090', 'I_01915': 'IV001210', 'I_01911': 'IV001219', 'I_01912': 'IV000002', 'I_01914': 'IV000054', 'I_01916': 'RP000259',
    'SA_016447': 'IV000090', 'SA_016449': 'IV000002', 'SA_016451': 'IV001157', 'SA_016452': 'IV000054',
    'SA_015891': 'IV000171', 'SA_015892': 'IV000091', 'SA_015893': 'IV000351', 'SA_015894': 'IV000090', 'SA_015895': 'IV000054', 'SA_015896': 'RP000068',
}

def ponuda_stavke(pdf):
    t = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
    out = []
    for m in re.finditer(r'^\s*(\d+)\s+([A-Z]{2}\d{6})\s+(.*?)\s{2,}([\d.]+)\s+(M2|M|KOM|KPT)\s', t, re.M):
        q = m.group(4).replace('.', '') if m.group(4).count('.') > 1 else m.group(4)
        out.append(dict(rb=int(m.group(1)), ident=m.group(2), naziv=m.group(3).strip(), kol=float(q), jm=m.group(5)))
    return out

def files(path, pat='*'):
    return sorted(os.path.basename(x) for x in glob.glob(os.path.join(path, '**', pat), recursive=True) if os.path.isfile(x))

def nalog_md(root, key, meta):
    p = os.path.join(root, key)
    L = ['## %s — ponuda %s' % (meta['naziv'], meta['ponuda']), '']
    ul = files(os.path.join(p, '01_ulaz_kupca'))
    L += ['**1. Ulaz kupca** (%s): %s' % (meta['tip'], ', '.join('`%s`' % f for f in ul)), '']
    nest = glob.glob(os.path.join(p, '04_export_nesting', '**', '*.CSV'), recursive=True)
    cix = glob.glob(os.path.join(p, '04_export_nesting', '**', '*.cix'), recursive=True)
    txt = glob.glob(os.path.join(p, '04_export_nesting', '**', '*.txt'), recursive=True)
    cpw = glob.glob(os.path.join(p, '04_export_nesting', '**', '*.CPW'), recursive=True)
    mno = glob.glob(os.path.join(p, '**', '*.mno'), recursive=True)
    cpos = sorted(glob.glob(os.path.join(p, '03_export_pila', '*.cpo')))
    L += ['**2. Unos i exporti:** PPNEST zapisa (TXT) %d, nesting CSV %d + CIX %d, CPW za PW %d, PW programa za pilu (CPO) %d%s' % (
        len(txt), len(nest), len(cix), len(cpw), len(cpos), ', bNest rezultat (.mno) %d' % len(mno) if mno else ', bNest rezultata nema'), '']
    pon = ponuda_stavke(glob.glob(os.path.join(p, '05_pantheon', '*.pdf'))[0])
    pon_by = {}
    for s in pon: pon_by.setdefault(s['ident'], []).append(s)
    L += ['**3. Materijali kroz lanac** (nalog = PW program; obračun PW-metodom iz stabla rezova; Hub = vlastiti optimizator, D-19):', '',
          '| PW program | Materijal | Elem. | Kom | m² dijelova | God | PW ploča | PW m² naplata | Hub ploča | Hub m² (način) | Ponuda ident | Ponuda kol. | Razlika ponuda−PW |',
          '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    tot_pw = tot_hub = tot_pon = 0.0
    kant_rows = []
    for f in cpos:
        d = cpo_rw.parse(f); rn = os.path.basename(f)[:-4]; s = d['inv'][0]
        god = d['ctl1']['grain'] == 'Y'; ploca = (s['L'], s['W'])
        pw = obracun.naplata_iz_cpo(d)
        dijelovi = [(o['idx'], o['W'], o['L'], o['qty']) for o in d['ord']]
        rp = d['material'].upper().startswith(('RP', 'ZO'))
        try:
            sh, oc, nacin, _ = po.najbolje(dijelovi, ploca, s['trim'][0], obracun.KERF_OBRACUN, god)
            hub = '%d | %.2f (%s)' % (oc['ploca'], oc['m2_naplata'], nacin.split('/')[0])
            hub_m2 = oc['m2_naplata']
        except ValueError as e:
            hub = '– | greška'; hub_m2 = 0
        ident = MAPA.get(rn, '?'); st = pon_by.get(ident, [])
        kol = ', '.join('%g %s' % (x['kol'], x['jm']) for x in st) or '—'
        raz = ''
        if st and st[0]['jm'] == 'M2':
            raz = '%+.2f' % (st[0]['kol'] - pw['m2_naplata']); tot_pon += st[0]['kol']
        elif st and st[0]['jm'] == 'M' and rp:
            dm = sum(o['qty'] * max(o['W'], o['L']) for o in d['ord']) / 1000
            raz = 'RP po dužnom m: elementi %.2f m' % dm
        if not rp: tot_pw += pw['m2_naplata']; tot_hub += hub_m2
        m2d = sum(o['qty'] * o['W'] * o['L'] for o in d['ord']) / 1e6
        L.append('| %s | %s | %d | %d | %.2f | %s | %d | %.2f | %s | %s | %s | %s |' % (
            rn, d['material'], len(d['ord']), sum(o['qty'] for o in d['ord']), m2d, 'da' if god else 'ne', pw['ploca'], pw['m2_naplata'], hub, ident, kol, raz))
        for name, m in obracun.kant_metri_iz_cpo(d).items():
            kant_rows.append((rn, d['material'], name, m))
    L += ['', 'Ukupno ploče (bez RP/ZO): **PW %.2f m² · Hub %.2f m² · ponuda %.2f m²**' % (tot_pw, tot_hub, tot_pon), '']
    L += ['**4. Trake** (PW "Kantiranje sortirano po dekorima" = Σ stranica × 1,10; rekonstruirano iz CPO PRT3):', '',
          '| PW program | Materijal | Traka (naziv u nalogu) | PW metri | Ponuda (TR ident, m) |', '|---|---|---|---|---|']
    tr = [s for s in pon if s['ident'].startswith('TR')]
    for rn, mat, name, m in kant_rows:
        L.append('| %s | %s | %s | %.1f | %s |' % (rn, mat, name, m, ''))
    L += ['', 'Stavke traka u ponudi: ' + '; '.join('%s %s %g m' % (s['ident'], s['naziv'], s['kol']) for s in tr), '']
    us = [s for s in pon if s['ident'].startswith('US')]
    ok = [s for s in pon if s['ident'].startswith('OK')]
    L += ['**5. Usluge u ponudi:** ' + '; '.join('%s %s %g %s' % (s['ident'], s['naziv'], s['kol'], s['jm']) for s in us), '',
          '**6. Okov u ponudi:** %d stavki (ručni unos iz upita kupca — Hub ne računa, D-07/pravila §6)' % len(ok), '']
    if mno:
        for m in mno:
            r = parseri.parse_mno(m)
            L.append('**7. Nesting (bNest .mno `%s`):** %d ploča, iskorištenje %.1f %% (%.1f od %.1f m²)' % (os.path.basename(m), r['sheets_n'], 100 * (r['util'] or 0), r['used_m2'], r['area_m2']))
        L.append('')
    return L

if __name__ == '__main__':
    root, out = sys.argv[1], sys.argv[2]
    md = ['# Paneli Production Hub — D-09: tri naloga kroz cijeli lanac "na papiru"', '',
          'Generirano skriptom `skripte/d09_tri_naloga.py` (11. 9. 2026.) iz datoteka u `05_NALOZI_ZA_TEST`. Izvor istine za elemente i sheme je PW CPO',
          '(imaju ga sva tri naloga); obračun je PW-metodom po pravilima iz 05 §5.3 (kerf 16, obrub 10, korisni ostatak ≥ 400×400 mm i ≥ 1 m²,',
          'naplata = Σ ploča − Σ korisnih ostataka; trake = Σ stranica × 1,10). Ponuda = stavke iz Pantheon PDF-a.', '']
    for k, meta in NALOZI.items():
        md += nalog_md(root, k, meta)
    open(out, 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    print('OK', out)
