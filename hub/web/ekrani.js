/* Paneli Production Hub — ekrani 3 (obračun → ponuda, optimizacija s potvrdom), 4 (skladište), 5 (proizvodnja: pila / nesting), 6 (nabava), šifrarnik, postavke. */
(function (H) {
  "use strict";
  var api = H.api, esc = H.esc, cist = H.cist, mm = H.mm, n = H.n, q = H.q, qa = H.qa, dlg = H.dlg, toast = H.toast, ljuska = H.ljuska, kpi = H.kpi, koraci = H.koraci, S = H.S, E = H.ekrani, idi = H.idi, render = H.render;
  function crumb(d, sto) { return 'Nalozi / <b>' + esc(d.naziv) + '</b> · ' + esc(d.kupac_naziv || "") + ' · ' + sto; }
  function tagPut(p) { return p ? '<span class="tag ' + (p === "nesting" ? "nest" : "pila") + '">' + esc(p) + '</span>' : ""; }
  function pct(x) { return x == null ? "—" : n(x * (x <= 1 ? 100 : 1), 1) + " %"; }
  // radna ploča / ploča stola / zidna obloga: naplata po ploči u metrima umjesto m² za naplatu (Igor, 17. 9.)
  function naplata(x, kratko) {
    var rp = x && x.naplata_rp;
    if (!rp) return '<b>' + n(x.m2_za_naplatu, 2) + ' m²</b> za naplatu';
    return '<b>' + n(rp.ukupno_m, 2) + ' m</b> za naplatu' + (kratko ? "" : ' <span class="note">(' + esc(rp.naziv) + ' — ' + esc(rp.opis_kratko || "") + ')</span>');
  }

  // ---------------------------------------------------------------- optimizacija s potvrdom (zajednički blok za ekrane 3 i 5)
  function sklonMat(k) { var z = k % 10, zz = k % 100; return z === 1 && zz !== 11 ? "materijal" : "materijala"; }
  function sazetakUpozorenja(lista, d, naslov) {
    /* 2A: ponavljajuća upozorenja → jedna poruka iznad tablice; detalji grupirani po materijalu (i uz materijal u tablici).
       Vraća { html, poMaterijalu: {nm_id: [tekst…]} }. Crveno kad nešto blokira (stavka bez cijene / ne može se složiti), inače žuto. */
    var mats = (d.materijali || []).map(function (m) { return { id: m.id, ime: m.naziv_kratki || m.naziv_ulaz || "" }; }).filter(function (m) { return m.ime; })
      .sort(function (a, b) { return b.ime.length - a.ime.length; });
    var grupe = {}, red = [], poMat = {}, broj = 0, crit = false, vidjeno = {};
    (lista || []).forEach(function (u0) {
      var u = cist(u0);
      if (vidjeno[u]) { vidjeno[u].n++; return; }
      var m = mats.filter(function (x) { return u.indexOf(x.ime + ":") === 0 || u.indexOf(x.ime + " el.") === 0; })[0];
      var kljuc = m ? m.ime : "Ostalo", tekst = m ? u.slice(m.ime.length).replace(/^:\s*/, "").replace(/^\s+/, "") : u;
      if (/bez stavke|ne može se složiti|nema u šifrarniku|nije aktivan/.test(u)) crit = true;
      var st = { t: tekst, n: 1 }; vidjeno[u] = st; broj++;
      if (!grupe[kljuc]) { grupe[kljuc] = []; red.push(kljuc); }
      grupe[kljuc].push(st);
      if (m) (poMat[m.id] = poMat[m.id] || []).push(st);
    });
    if (!broj) return { html: "", poMaterijalu: {} };
    var popis = red.map(function (k) { return k + " (" + grupe[k].length + ")"; }).join(" · ");
    var html = '<div class="sazetak' + (crit ? " crit" : "") + '"><span class="ik">!</span><div class="txt"><b>' + esc(naslov) + ': ' + broj + (broj === 1 ? " upozorenje" : broj % 10 >= 2 && broj % 10 <= 4 && (broj % 100 < 12 || broj % 100 > 14) ? " upozorenja" : " upozorenja") + '</b> <span class="note">— ' + esc(popis) + '</span></div>' +
      '<details><summary>Detalji po materijalu</summary>' + red.map(function (k) { return '<div class="grupa">' + esc(k) + '</div><ul>' + grupe[k].map(function (x) { return '<li>' + esc(x.t) + (x.n > 1 ? ' <span class="note">(×' + x.n + ')</span>' : "") + '</li>'; }).join("") + '</ul>'; }).join("") + '</details></div>';
    return { html: html, poMaterijalu: poMat };
  }
  function ploca(nb) { nb = +nb || 0; var z = nb % 10, zz = nb % 100; return z === 1 && zz !== 11 ? "ploča" : (z >= 2 && z <= 4 && (zz < 12 || zz > 14)) ? "ploče" : "ploča"; }
  function brojke(x) {
    /* tri ključne brojke kartice (3A): količina ploča, iskorištenje, za naplatu (m² ili metri za radne ploče) */
    var rp = x.naplata_rp, nap = rp ? n(rp.ukupno_m, 2) + '<small>m</small>' : n(x.m2_za_naplatu, 2) + '<small>m²</small>';
    return '<div class="brojke"><div><div class="bl">Količina</div><div class="bv">' + (x.broj_ploca || 0) + '<small>' + ploca(x.broj_ploca) + '</small></div></div>' +
      '<div><div class="bl">Iskorištenje</div><div class="bv">' + pct(x.iskoristenje) + '</div></div><div><div class="bl">Za naplatu</div><div class="bv">' + nap + '</div></div></div>';
  }
  function dslika(ident, vel) {
    if (!ident) return "";
    return '<img class="dslika' + (vel ? " " + vel : "") + '" src="/api/dekor/slika/' + encodeURIComponent(ident) + '" alt="" loading="lazy" onerror="this.style.display=\'none\'">';
  }
  function optBlok(d, opt) {
    function pdf(o, x) { return '/api/nalog/' + d.id + '/ispis/krojni.pdf?materijal=' + o.nalog_materijal_id + (x ? '&oid=' + x.id : ""); }
    var IMENA = { auto: "Realno za pilu", hub: "Hub rezerva (najmanje m²)", uzduzno: "Uzdužno", poprecno: "Poprečno", trake: "Trake" };
    function lab(x) { return esc(IMENA[x.nacin_trazen] || x.nacin_trazen) + " / " + esc(x.dubina); }
    function slika(o, x) { return '<a class="kart-shema" href="#" data-pregled="' + x.id + '" data-nm="' + o.nalog_materijal_id + '" title="Pregled optimizacije na ekranu"><img src="/api/optimizacija/' + x.id + '/sheme.png?h=140" alt="sheme" onerror="this.parentNode.classList.add(\'nema\')"></a>'; }
    function meta(x, naslov) {
      var rp = x.naplata_rp;
      return '<div class="kart-meta">' + naslov + (x.nacin ? ' · ' + esc(x.nacin) : "") + (x.rezova ? ' · rezova ' + x.rezova : "") + (rp ? '<br>' + esc(rp.naziv) + ': ' + esc(rp.opis_kratko || "") : "") +
        (x.napomena ? '<br><span class="warn-t">⚠ ' + esc(x.napomena) + '</span>' : "") + '</div>';
    }
    return opt.map(function (o) {
      var p = o.potvrdjeno, pr = o.prijedlozi || [];
      var glavni = p || pr.filter(function (x) { return x.nacin_trazen === "auto" && x.dubina === "najbolje"; }).slice(-1)[0] || pr[0] || null;
      var ostali = pr.filter(function (x) { return !glavni || x.id !== glavni.id; });
      var stat = !o.treba ? '<span class="stat info">bez optimizacije</span>' : p ? '<span class="stat ok"><i>✓</i> Potvrđeno</span>' : glavni ? '<span class="stat warn"><i>◷</i> Čeka potvrdu</span>' : '<span class="stat warn"><i>◷</i> Nema prijedloga</span>';
      var head = '<div class="kart-hd"><div class="grow"><div class="naslov" title="' + esc(o.materijal) + '">' + esc(o.materijal) + '</div><div class="meta">' + esc(o.ident || "") + ' ' + tagPut(o.put) + '</div></div>' + stat + '</div>';
      var body, akcije;
      if (!o.treba) { body = '<div class="kart-tijelo">Materijal se ne slaže na ploču — nema optimizacije.</div>'; akcije = ""; }
      else if (p) {
        body = slika(o, p) + brojke(p) + meta(p, "Potvrđena optimizacija");
        akcije = '<button class="btn" data-pregled="' + p.id + '" data-nm="' + o.nalog_materijal_id + '">Pregled shema</button><a class="btn" href="' + pdf(o, p) + '" target="_blank">Krojni nacrt PDF</a>';
      } else if (glavni) {
        body = slika(o, glavni) + brojke(glavni) + meta(glavni, "Prijedlog: " + lab(glavni));
        akcije = '<button class="btn pri" data-potvrdi-opt="' + glavni.id + '">✔ Potvrdi optimizaciju</button><button class="btn" data-pregled="' + glavni.id + '" data-nm="' + o.nalog_materijal_id + '">Pregled shema</button><a class="btn" href="' + pdf(o, glavni) + '" target="_blank" title="Krojni nacrt PDF">PDF</a>';
      } else {
        body = '<div class="kart-tijelo">Hub izračuna optimizaciju kakvu pila realno reže (trake → poprečni rezovi → uži komadi); ti je potvrdiš — ista brojka ide u ponudu i na pilu. Uz nju pokaže i svoju rezervu s najmanje m² ako ona štedi materijal.</div>';
        akcije = '<button class="btn pri" data-pred="' + o.nalog_materijal_id + '">Izračunaj optimizaciju</button>';
      }
      // akcije u jednom redu na svim karticama; varijante u traci ispod — ista visina kartica, poravnati gumbi (3A)
      var traka = o.treba ? '<div class="var-traka">' + (ostali.length ? '<button class="btn lnk-btn" data-var="' + o.nalog_materijal_id + '">Ostale varijante (' + ostali.length + ') ▾</button>' : '<span class="note">Nema drugih varijanti</span>') +
        '<span class="grow"></span><button class="btn lnk-btn" data-alt="' + o.nalog_materijal_id + '">' + (p ? "Druga varijanta…" : "Alternativa…") + '</button></div>' : "";
      var alt = ostali.length ? '<div class="varijante" id="var-' + o.nalog_materijal_id + '" hidden>' + ostali.map(function (x) {
        return '<div class="slag-red"><span>' + lab(x) + ' <span class="note">' + esc(x.nacin || "") + '</span>' + (x.napomena ? ' <span class="stat warn sm" title="' + esc(x.napomena) + '">⚠</span>' : "") + '</span><span class="num">' + x.broj_ploca + ' pl · ' + pct(x.iskoristenje) + ' · ' + (x.naplata_rp ? n(x.naplata_rp.ukupno_m, 2) + ' m' : n(x.m2_za_naplatu, 2) + ' m²') +
          (x.razlika_m2_prema_auto != null ? ' <span class="' + (x.razlika_m2_prema_auto > 0 ? "warn-t" : "ok-t") + '">(' + (x.razlika_m2_prema_auto > 0 ? "+" : "") + n(x.razlika_m2_prema_auto, 2) + ')</span>' : "") + '</span>' +
          '<span class="row"><button class="btn sm" data-pregled="' + x.id + '" data-nm="' + o.nalog_materijal_id + '">Sheme</button><button class="btn sm" data-potvrdi-opt="' + x.id + '">Potvrdi</button></span></div>'; }).join("") + '</div>' : "";
      return '<div class="pane slag-card kart">' + head + body + (akcije ? '<div class="kart-akcije">' + akcije + '</div>' : "") + traka + alt + '</div>';
    }).join("");
  }
  function legendaSheme() { return '<div class="legenda"><i style="background:#DCE9E2;border-color:#2E6B57"></i>iskorišteno za naručene mjere <i style="background:#DCE7F3;border-color:#2F5D8C"></i>naš restl (korisni ostatak, ne naplaćuje se) <i style="background:#F9DEE5;border-color:#C2506B"></i>kupčev restl (naplaćuje se)</div>'; }
  function optCeka(opt) { return (opt || []).filter(function (o) { return o.treba && !o.potvrdjeno; }); }
  function optBanner(d, opt, jedan) {
    var ceka = optCeka(opt);
    if (!ceka.length) return (opt || []).some(function (o) { return o.treba; }) ? '<div class="sazetak ok slag-banner"><span class="ik">✓</span><div class="txt"><b>Optimizacija potvrđena</b> ' + (jedan ? "za ovaj materijal" : "za sve materijale") + ' <span class="note">— ponuda i pila rade s tom brojkom.</span></div></div>' : "";
    return '<div class="sazetak slag-banner"><span class="ik">!</span><div class="txt"><b>' + (ceka.length === 1 ? "1 materijal čeka" : ceka.length + " materijala čeka") + ' potvrdu optimizacije</b> — ' + esc(ceka.map(function (o) { return o.materijal; }).join(", ")) + '.<br><span class="note">Bez potvrde nema ponude ni izvoza na pilu. Pogledaj sheme ' + (jedan ? "ispod" : "na karticama") + ' i potvrdi' + (jedan ? "" : ", ili potvrdi zadane optimizacije (realne za pilu) odjednom") + '.</span></div>' +
      '<button class="btn pri lg" id="potvrdiSve">✔ Potvrdi ' + (jedan ? "zadanu optimizaciju" : "sve zadane optimizacije (" + ceka.length + ")") + '</button></div>';
  }
  async function pregledSlaganja(d, o, x) {
    /* pregled optimizacije na ekranu (Igor, 17. 9.): sve ploče velike, brojevi i mjere, popis elemenata; PDF samo na klik */
    var p = await api("/api/optimizacija/" + x.id + "/pregled");
    /* sve ploče iste veličine (Igor): visina H px, širina iz omjera ploče; kompaktno, više ploča u redu, što manje skrolanja */
    var H = p.listovi.length > 4 ? 340 : 400, Wpx = Math.round(H * p.ploca.W / p.ploca.L);
    var listovi = p.listovi.map(function (li) {
      return '<div class="preg-list" style="width:' + Wpx + 'px"><div class="preg-cap"><b>Ploča ' + li.br + '/' + p.listovi.length + '</b> · ' + (li.dir === "L" ? "uzdužno" : "poprečno") + ' · ' + li.komadi + ' kom · ' + li.rezova + ' rez · isk. <b>' + pct(li.iskoristenje) + '</b>' +
        (li.naplata ? '<br><b>za naplatu ' + n(li.naplata.naplata_m, 2) + ' m</b> <span class="note">(' + esc(li.naplata.opis) + ', komadi ' + n(li.naplata.duljina_mm / 1000, 2) + ' m)</span>' : "") +
        (li.ostatak ? '<br><span class="abs-t">naš restl ' + mm(li.ostatak[0]) + ' × ' + mm(li.ostatak[1]) + ' (' + n(li.ostatak[2], 2) + ' m²)</span>' : "") + '</div>' +
        '<img src="/api/optimizacija/' + x.id + '/sheme.png?list=' + li.br + '&h=' + H + '" style="width:' + Wpx + 'px;height:' + H + 'px" alt="ploča ' + li.br + '"></div>'; }).join("");
    var el = p.elementi.map(function (e) { return '<tr><td class="r num"><b>' + e.idx + '</b></td><td class="wrap">' + esc(e.naziv || "") + (e.napomena ? '<div class="note">' + esc(e.napomena) + '</div>' : "") + '</td><td class="r num">' + mm(e.L) + ' × ' + mm(e.W) + '</td><td class="r num">' + e.kom + '</td></tr>'; }).join("");
    var st = p.statistika || {};
    dlg({ naslov: "Optimizacija — " + (o.materijal || "") + (x.status === "potvrdjeno" ? " (potvrđeno)" : " (prijedlog)"), wide: true,
      tijelo: '<div class="row" style="gap:16px;flex-wrap:wrap"><span><span class="big">' + (st.ploca || x.broj_ploca) + '</span> ploča ' + mm(p.ploca.L) + ' × ' + mm(p.ploca.W) + '</span><span>isk. <b>' + pct(x.iskoristenje) + '</b></span><span>' + naplata(p.naplata_rp ? { naplata_rp: p.naplata_rp } : x, true) + '</span><span>dijelova ' + n(st.m2_dijelova, 2) + ' m²</span><span>rezova ' + (x.rezova || "—") + '</span><span class="note">' + esc(p.nacin || "") + '</span></div>' + legendaSheme() +
        '<div class="preg"><div class="preg-listovi">' + listovi + '</div><div class="preg-el"><table><thead><tr><th class="r">#</th><th>Element</th><th class="r">Mjera (rez)</th><th class="r">kom</th></tr></thead><tbody>' + el + '</tbody></table>' +
        (p.trake && p.trake.length ? '<div class="note" style="padding:8px 10px">Trake: ' + p.trake.map(function (t) { return esc(t.oznaka) + " " + esc(t.naziv || "") + " " + n(t.metri, 1) + " m"; }).join(" · ") + '</div>' : "") + '</div></div>',
      gumbi: [{ txt: "Krojni nacrt PDF", on: function () { window.open('/api/nalog/' + d.id + '/ispis/krojni.pdf?materijal=' + o.nalog_materijal_id + '&oid=' + x.id, "_blank"); return false; } }]
        .concat(x.status === "potvrdjeno" ? [] : [{ txt: "✔ Potvrdi ovu optimizaciju", pri: true, on: async function () { var r = await api("/api/optimizacija/" + x.id + "/potvrdi", { body: {} }); toast(r.ponuda_poslana ? "Potvrđeno — ponuda je već poslana, napravi novu verziju" : "Optimizacija potvrđena", !!r.ponuda_poslana); render(); } }]) });
  }
  function veziOpt(d, opt) {
    qa("[data-var]").forEach(function (b) { b.onclick = function () { var el = q("#var-" + b.dataset["var"]); if (!el) return; el.hidden = !el.hidden; b.textContent = b.textContent.replace(/[▾▴]$/, el.hidden ? "▾" : "▴"); }; });
    qa("[data-pregled]").forEach(function (b) { b.onclick = function (e) { e.preventDefault(); var o = (opt || []).filter(function (y) { return String(y.nalog_materijal_id) === b.dataset.nm; })[0] || {}; var x = (o.potvrdjeno && String(o.potvrdjeno.id) === b.dataset.pregled) ? o.potvrdjeno : (o.prijedlozi || []).filter(function (y) { return String(y.id) === b.dataset.pregled; })[0]; if (x) pregledSlaganja(d, o, x); }; });
    qa("[data-potvrdi-opt]").forEach(function (b) { b.onclick = async function () { b.disabled = true; var r = await api("/api/optimizacija/" + b.dataset.potvrdiOpt + "/potvrdi", { body: {} }); if (r.ponuda_poslana) toast("Ponuda je već poslana — napravi novu verziju", true); else toast("Optimizacija potvrđena"); render(); }; });
    qa("[data-pred]").forEach(function (b) { b.onclick = async function () { b.disabled = true; b.textContent = "računam…"; await api("/api/nalog/" + d.id + "/optimizacija/pripremi", { body: { nm: +b.dataset.pred } }); render(); }; });
    qa("[data-alt]").forEach(function (b) { b.onclick = function () {
      dlg({ naslov: "Alternativna optimizacija", tijelo: '<div class="grid2"><div class="field"><span class="lbl">Način</span><select id="nacin"><option value="auto">Realno za pilu (zadano)</option><option value="hub">Hub rezerva (najmanje m², bez ograničenja pile)</option><option value="uzduzno">Uzdužno</option><option value="poprecno">Poprečno</option><option value="trake">Trake</option></select></div><div class="field"><span class="lbl">Dubina</span><select id="dub"><option value="brzo">brzo</option><option value="najbolje" selected>najbolje</option></select></div></div><div class="note">Zadana optimizacija poštuje ograničenja pile iz Postavki (razine rezanja, širine u traci, orijentacija). Hub rezerva pokazuje koliko bi se moglo uštedjeti bez tih ograničenja — potvrdi je samo ako je pila stvarno može izrezati.</div>',
        gumbi: [{ txt: "Izračunaj", pri: true, on: async function (bg) { await api("/api/nalog/" + d.id + "/materijal/" + b.dataset.alt + "/optimizacija", { body: { nacin: q("#nacin", bg).value, dubina: q("#dub", bg).value } }); render(); } }] }); }; });
    var sve = q("#potvrdiSve");
    if (sve) sve.onclick = async function () {
      sve.disabled = true; sve.textContent = "potvrđujem…";
      var k = 0, poslana = false;
      for (var i = 0; i < (opt || []).length; i++) {
        var o = opt[i];
        if (!o.treba || o.potvrdjeno) continue;
        var g = (o.prijedlozi || []).filter(function (x) { return x.nacin_trazen === "auto" && x.dubina === "najbolje"; }).slice(-1)[0];
        try {
          if (!g) g = await api("/api/nalog/" + d.id + "/materijal/" + o.nalog_materijal_id + "/optimizacija", { body: { nacin: "auto", dubina: "najbolje" } });
          var r = await api("/api/optimizacija/" + g.id + "/potvrdi", { body: {} });
          if (r.ponuda_poslana) poslana = true;
          k++;
        } catch (e) { /* api() već pokaže grešku */ }
      }
      toast(poslana ? "Potvrđeno " + k + " — ponuda je već poslana, napravi novu verziju" : "Potvrđena optimizacija: " + k + " materijal(a)", poslana);
      render();
    };
  }

  // ---------------------------------------------------------------- ekran 3: obračun → ponuda iz Huba
  // ---------------------------------------------------------------- ekran 2: optimizacija (slaganje ploča, korak prije ponude — Igor, 17. 9.: naziv „Optimizacija“)
  E.nalog_slaganje = async function (r) {
    var d = S.nalog = await api("/api/nalog/" + r.id), opt = await api("/api/nalog/" + d.id + "/optimizacija");
    var treba = opt.filter(function (o) { return o.treba; }), pot = treba.filter(function (o) { return o.potvrdjeno; });
    var ploca = pot.reduce(function (a, o) { return a + (o.potvrdjeno.broj_ploca || 0); }, 0), m2 = pot.reduce(function (a, o) { return a + (o.potvrdjeno.m2_za_naplatu || 0); }, 0);
    ljuska({ crumb: crumb(d, "optimizacija"), koraci: koraci(d), rail: "nalozi", cls: "c1 stack",
      akcije: '<a class="tbtn" href="#/nalog/' + d.id + '">← Unos</a><a class="tbtn pri" href="#/nalog/' + d.id + '/ponuda">Ponuda →</a>',
      sadrzaj: optBanner(d, opt) + '<div class="slag">' + (optBlok(d, opt) || '<div class="pane"><div class="bd note">nalog nema materijala — dodaj ih u unosu</div></div>') + '</div>' + (treba.length ? legendaSheme() : ""),
      foot: kpi(pot.length + " / " + treba.length, "materijala potvrđeno") + kpi(ploca, "ploča (potvrđeno)") + kpi(n(m2, 2), "m² za naplatu") + '<span class="grow"></span>' + (pot.length === treba.length ? '<span class="ok-t">sve potvrđeno — može ponuda</span>' : '<span class="warn-t">čeka potvrdu: ' + esc(treba.filter(function (o) { return !o.potvrdjeno; }).map(function (o) { return o.materijal; }).join(", ")) + '</span>') });
    veziOpt(d, opt);
  };

  // ---------------------------------------------------------------- ekran 3: ponuda — pregled i korekcija, novi redak kao u Pantheonu (Igor, 17. 9.)
  // sažetak promjena ispod novije verzije ponude (Igor, 17. 9.): razlika iznosa + najveće promjene stavki, sve na klik
  function znak(x, d) { return (x > 0 ? "+" : x < 0 ? "−" : "±") + n(Math.abs(x), d == null ? 2 : d); }
  function promjenaRedovi(pr) {
    var R = [];
    pr.dodano.forEach(function (x) { R.push({ c: "dod", t: "+ " + (x.naziv || x.ident), d: n(x.kolicina) + " " + (x.jm || ""), r: x.razlika, id: x.ident }); });
    pr.uklonjeno.forEach(function (x) { R.push({ c: "ukl", t: "− " + (x.naziv || x.ident), d: "uklonjeno", r: x.razlika, id: x.ident }); });
    pr.promijenjeno.forEach(function (x) {
      var p = (x.polja || []).map(function (f) { return f.polje === "kolicina" ? n(f.staro) + " → " + n(f.novo) + " " + (x.jm || "") : f.polje === "cijena" ? "cijena " + n(f.staro, 2) + " → " + n(f.novo, 2) : "rabat " + n(f.staro) + " → " + n(f.novo) + " %"; }).join(" · ");
      R.push({ c: "pro", t: x.naziv || x.ident, d: p || "iznos", r: x.razlika, id: x.ident }); });
    R.sort(function (a, b) { return Math.abs(b.r) - Math.abs(a.r); });
    return R;
  }
  function promjeneHtml(v) {
    var pr = v.promjene; if (!pr) return "";
    if (pr.bez_promjene) return '<div class="ver-prom"><div class="note">bez promjena u odnosu na v' + pr.prema + '</div></div>';
    var R = promjenaRedovi(pr), MAX = 4;
    var brojevi = [pr.dodano.length ? pr.dodano.length + " dodano" : "", pr.uklonjeno.length ? pr.uklonjeno.length + " uklonjeno" : "", pr.promijenjeno.length ? pr.promijenjeno.length + " promijenjeno" : ""].filter(Boolean).join(" · ");
    return '<div class="ver-prom"><div class="vp-hd"><span>prema v' + pr.prema + '</span> <b class="num">' + znak(pr.ukupno_razlika) + ' €</b> <span class="note">s PDV-om (neto ' + znak(pr.neto_razlika) + ')</span></div>' +
      R.slice(0, MAX).map(function (x) { return '<div class="vp ' + x.c + '" title="' + esc(x.id + " · " + x.t) + '"><span class="t">' + esc(x.t) + '</span><span class="d">' + esc(x.d) + '</span><span class="r num">' + znak(x.r) + '</span></div>'; }).join("") +
      '<div class="vp-ft"><span class="note">' + esc(brojevi) + '</span>' + (R.length > MAX ? '<button class="lnk" data-promjene="' + v.id + '">sve promjene (' + R.length + ')</button>' : "") + '</div></div>';
  }
  function promjeneDijalog(v, brojP) {
    var pr = v.promjene, R = promjenaRedovi(pr);
    dlg({ naslov: "Ponuda " + brojP + " · v" + v.verzija + " prema v" + pr.prema, wide: true, tijelo: '<div class="note">Razlika: <b>' + znak(pr.ukupno_razlika) + ' €</b> s PDV-om · neto ' + znak(pr.neto_razlika) + ' €</div><div class="lista" style="max-height:60vh"><table><thead><tr><th>Ident</th><th>Stavka</th><th>Promjena</th><th class="r">Razlika neto</th></tr></thead><tbody>' +
      R.map(function (x) { return '<tr class="vp-tr ' + x.c + '"><td class="mono">' + esc(x.id || "") + '</td><td class="wrap">' + esc(x.t) + '</td><td>' + esc(x.d) + '</td><td class="r num"><b>' + znak(x.r) + '</b></td></tr>'; }).join("") + '</tbody></table></div>' });
  }
  E.nalog_ponuda = async function (r) {
    var d = S.nalog = await api("/api/nalog/" + r.id);
    var ob = await api("/api/nalog/" + d.id + "/obracun"), ponude = await api("/api/nalog/" + d.id + "/ponude"), opt = await api("/api/nalog/" + d.id + "/optimizacija");
    var grupe = { materijal: "Materijali", traka: "Trake", kantiranje: "Kantiranje", rezanje: "Rezanje", usluga: "Usluge i obrade", okov: "Okov", ostalo: "Ostalo" }, zadnja = null, rows = "";
    var grupeVid = false;                                                    // nazivi grupa se ne prikazuju (Igor, 17. 9.)
    var uredivo = d.status === "unos" || d.status === "ponuda";
    function inl(kl, polje, v, w, ph) { return '<input class="inl num" data-st="' + esc(kl) + '" data-polje="' + polje + '" value="' + (v == null ? "" : esc(String(v).replace(".", ","))) + '" placeholder="' + esc(ph || "") + '" style="width:' + w + 'px"' + (uredivo ? "" : " disabled") + '>'; }
    var bruto = 0, saz = sazetakUpozorenja(ob.upozorenja, d, "Obračun"), oznacen = {};
    (ob.stavke || []).forEach(function (s) {
      if (grupeVid && s.grupa !== zadnja) { rows += '<tr class="grp"><td colspan="8">' + esc(grupe[s.grupa] || s.grupa) + '</td></tr>'; zadnja = s.grupa; }
      bruto += (s.kolicina || 0) * (s.cijena || 0);
      var kl = s.rucna_id ? "R:" + s.rucna_id : "K:" + s.kljuc, kor = s.korekcija || null;
      var um = s.grupa === "materijal" && s.nalog_materijal_id && saz.poMaterijalu[s.nalog_materijal_id] && !oznacen[s.nalog_materijal_id] ? saz.poMaterijalu[s.nalog_materijal_id] : null;
      if (um) oznacen[s.nalog_materijal_id] = true;
      rows += '<tr' + (s.rucna_id ? ' class="rucna"' : kor ? ' class="korig"' : "") + '><td class="mono">' + esc(s.pantheon_ident) + '</td><td class="wrap">' + esc(s.naziv || "") + (um ? ' <span class="stat warn sm" title="' + esc(um.map(function (x) { return x.t; }).join("\n")) + '">⚠ ' + um.length + '</span>' : "") + (s.pravilo ? '<div class="note">' + esc(cist(s.pravilo)) + '</div>' : "") + '</td>' +
        '<td class="r num">' + inl(kl, "kolicina", s.kolicina, 76) + '</td><td>' + esc(s.jm || "") + '</td>' +
        '<td class="r num">' + inl(kl, "cijena", s.cijena, 84, s.cijena == null ? "bez cijene" : "") + '</td>' +
        '<td class="r num">' + inl(kl, "rabat", s.rabat == null ? 0 : s.rabat, 56) + '</td><td class="r num"><b>' + n(s.iznos, 2) + '</b></td>' +
        '<td class="r">' + (s.provjeri ? '<span class="tag warn">provjeri</span> ' : "") + (kor ? '<button class="btn sm" data-vrati="' + esc(s.kljuc) + '" title="Vrati izračunato (' + esc(Object.keys(kor).join(", ")) + ')">↺</button>' : "") + (s.rucna_id ? '<button class="btn sm" data-rucna="' + s.rucna_id + '" title="Ukloni redak">×</button>' : "") + '</td></tr>';
    });
    var rabatIzn = bruto - (ob.neto || 0);
    var novi = uredivo ? '<tr class="novi"><td colspan="2"><div class="pad-wrap"><input id="nQ" placeholder="+ novi redak: ident ili naziv iz Pantheona…" autocomplete="off"><div class="pad" id="nPad"></div></div></td>' +
      '<td class="r"><input id="nKol" class="inl num" value="1" style="width:76px"></td><td><span id="nJm" class="note">—</span></td><td class="r"><input id="nCij" class="inl num" style="width:84px" placeholder="—"></td><td class="r"><input id="nRab" class="inl num" style="width:56px" placeholder="' + n(d.rabat_usluge, 0) + '"></td><td class="r num" id="nIzn">—</td><td class="r"><button class="btn sm pri" id="nDodaj">Dodaj</button></td></tr>' : "";
    var zbRedovi = (rabatIzn > 0.005 ? [["Ukupno bez rabata", n(bruto, 2), ""], ["Rabat", "− " + n(rabatIzn, 2), ""]] : []).concat([["Ukupno neto", n(ob.neto, 2), ""], ["PDV 25 %", n(ob.pdv, 2), ""], ["ZA PLATITI", n(ob.ukupno, 2) + " €", "uk"]]);
    var vis = zbRedovi.map(function (r) { return r[2] === "uk" ? 38 : 26; }), zbroj = '<tfoot class="zbroj">';
    zbRedovi.forEach(function (r, i) { var dno = vis.slice(i + 1).reduce(function (a, b) { return a + b; }, 0), st = ' style="bottom:' + dno + 'px;height:' + vis[i] + 'px"';
      zbroj += '<tr class="' + r[2] + '"><td colspan="6" class="r lbl2"' + st + '>' + r[0] + '</td><td class="r num"' + st + '>' + r[1] + '</td><td' + st + '></td></tr>'; });
    zbroj += '</tfoot>';
    var zadnjaV = ponude.length ? ponude[ponude.length - 1] : null, brojP = d.ponuda_pantheon || d.broj;
    var verLbl = zadnjaV ? (zadnjaV.status === "nacrt" ? "v" + zadnjaV.verzija + " · nacrt" : "v" + zadnjaV.verzija + " · " + zadnjaV.status + (uredivo ? " · nova verzija u pripremi" : "")) : "još nema verzije — radne stavke";
    var verz = ponude.slice().reverse().map(function (v) {                       // najnovija gore; PDF i stavke za SVAKU verziju (i stare, za usporedbu)
      var st = v.status === "potvrdjena" ? "ok" : v.status === "poslana" ? "warn" : v.status === "zamijenjena" ? "" : "info";
      var gumbi = '<a class="btn sm" href="/api/ponuda/' + v.id + '/pdf" target="_blank">PDF</a><button class="btn sm" data-stavke="' + v.id + '" title="stavke ove verzije">Stavke</button>' +
        (v.status === "nacrt" || v.status === "poslana" ? '<button class="btn sm zuti" data-posalji="' + v.id + '">Pošalji kupcu</button>' : "") +
        (v.status !== "potvrdjena" && v.status !== "zamijenjena" ? '<button class="btn sm plavi" data-kupac="' + v.id + '">Kupac potvrdio</button>' : "") +
        (v.status === "potvrdjena" ? '<button class="btn sm" data-eslog="' + v.id + '">eSlog</button>' : "");
      return '<div class="ver"><div class="row"><b>v' + v.verzija + '</b><span class="tag ' + st + '">' + esc(v.status) + '</span><span class="grow"></span><span class="num"><b>' + n((v.iznos_neto || 0) + (v.iznos_pdv || 0), 2) + ' €</b> <span class="note">s PDV-om · neto ' + n(v.iznos_neto, 2) + '</span></span></div>' +
        (v.poslano_kada ? '<div class="note">poslano ' + esc(v.poslano_kada.slice(0, 16).replace("T", " ")) + ' → ' + esc(v.poslano_na || "") + '</div>' : "") +
        '<div class="ver-gumbi">' + gumbi + '</div>' + promjeneHtml(v) + '</div>';
    }).join("");
    var upoz = saz.html;
    var ceka = optCeka(opt);
    var slagUpoz = ceka.length ? '<div class="sazetak slag-banner"><span class="ik">!</span><div class="txt"><b>Optimizacija čeka potvrdu</b> — ' + esc(ceka.map(function (o) { return o.materijal; }).join(", ")) + '.<br><span class="note">Brojke ploča dolje su Hubov prijedlog; bez potvrde nema verzije ponude.</span></div><a class="btn pri" href="#/nalog/' + d.id + '/optimizacija">Otvori optimizaciju</a></div>' : "";
    ljuska({ crumb: crumb(d, "ponuda"), koraci: koraci(d), rail: "nalozi", cls: "c1 stack",
      akcije: '<a class="tbtn" href="#/nalog/' + d.id + '/optimizacija">← Optimizacija</a><span class="grow"></span>' + (uredivo ? '<button class="tbtn" id="btnRabat">Rabat na sve…</button><button class="tbtn" id="btnNap">Napomena' + (d.napomena_ponude ? " ✓" : "") + '</button><button class="tbtn' + (d.zbroji_idente ? " on" : "") + '" id="btnZbroji" title="isti ident, cijena i rabat → jedan redak sa zbrojenom količinom">' + (d.zbroji_idente ? "✓ " : "") + 'Zbroji iste idente</button><button class="tbtn pri" id="btnVerzija">Nova verzija ponude</button>' : "") +
        (d.status === "potvrdjeno" ? '<button class="tbtn pri" id="btnUSkladiste">→ Skladište (rezerviraj materijal)</button>' : ""),
      sadrzaj: slagUpoz + '<div class="dvo"><div class="pane"><div class="hd ponuda-hd"><div><div class="naslov-p">PONUDA <span class="broj">' + esc(brojP) + '</span></div><div class="note">' + esc(verLbl) + ' · ' + esc(d.kupac_naziv || "") + ' · nalog ' + esc(d.naziv) + '</div></div><span class="grow"></span>' + (d.napomena_ponude ? '<div class="note nap-p" title="napomena na dokumentu">„' + esc(d.napomena_ponude.slice(0, 90)) + (d.napomena_ponude.length > 90 ? "…" : "") + '“</div>' : "") + '</div><div class="bd tight">' + upoz + '<table class="ponuda-t"><thead><tr><th>Ident</th><th>Naziv</th><th class="r">Količina</th><th>JM</th><th class="r">Cijena</th><th class="r">Rabat %</th><th class="r">Iznos</th><th></th></tr></thead><tbody>' + (rows || '<tr><td colspan="8" class="note">nema stavki — nalog nema elemenata ili materijali nisu potvrđeni</td></tr>') + novi + '</tbody>' + zbroj + '</table></div></div>' +
        '<div class="pane"><div class="hd"><b>Verzije ponude</b></div><div class="bd">' + (verz || '<div class="note">još nema verzije — „Nova verzija ponude“ snimi stavke</div>') + '</div></div></div>',
      foot: null });                                                              // statistika u podnožju nije potrebna (Igor) — zbroj je u tablici
    if (q("#btnVerzija")) q("#btnVerzija").onclick = async function () { var v = await api("/api/nalog/" + d.id + "/ponude", { body: { pravila: true } }); toast("Ponuda v" + v.verzija + " — " + n((v.iznos_neto || 0) + (v.iznos_pdv || 0), 2) + " € s PDV-om"); render(); };
    if (q("#btnZbroji")) q("#btnZbroji").onclick = async function () { await api("/api/nalog/" + d.id, { method: "PUT", body: { zbroji_idente: d.zbroji_idente ? 0 : 1 } }); render(); };
    if (q("#btnUSkladiste")) q("#btnUSkladiste").onclick = async function () { var rr = await api("/api/nalog/" + d.id + "/status", { body: { status: "skladiste" } }); if (rr.skladiste && rr.skladiste.upozorenja.length) toast("Skladište: " + rr.skladiste.upozorenja.join("; "), true); idi("#/nalog/" + d.id + "/skladiste"); };
    qa("[data-posalji]").forEach(function (b) { b.onclick = function () { posaljiPonudu(d, b.dataset.posalji); }; });
    if (q("#btnNap")) q("#btnNap").onclick = function () {
      dlg({ naslov: "Napomena na ponudi", tijelo: '<div class="field"><span class="lbl">Ispisuje se na dokumentu ispod uvjeta (kupac je vidi)</span><textarea id="np" rows="5">' + esc(d.napomena_ponude || "") + '</textarea></div>',
        gumbi: [{ txt: "Spremi", pri: true, on: async function (bg) { await api("/api/nalog/" + d.id, { method: "PUT", body: { napomena_ponude: q("#np", bg).value } }); render(); } }], nakon: function (bg) { q("#np", bg).focus(); } }); };
    if (q("#btnRabat")) q("#btnRabat").onclick = function () {
      dlg({ naslov: "Rabat na sve stavke", tijelo: '<div class="grid3"><div class="field"><span class="lbl">Sve stavke %</span><input id="rs" inputmode="decimal" placeholder="npr. 10"></div><div class="field"><span class="lbl">Materijal (ploče, trake, okov) %</span><input id="rm" value="' + n(d.rabat_materijal, 0) + '"></div><div class="field"><span class="lbl">Usluge (rezanje, kantiranje, CNC) %</span><input id="ru" value="' + n(d.rabat_usluge, 0) + '"></div></div><div class="note">Rabat na nalogu vrijedi za sve izračunate stavke; pojedinu stavku možeš i dalje ispraviti u tablici (ručne stavke bez upisanog rabata prate nalog).</div>',
        gumbi: [{ txt: "Primijeni", pri: true, on: async function (bg) { var sve = q("#rs", bg).value.trim().replace(",", "."), m = q("#rm", bg).value.trim().replace(",", "."), u = q("#ru", bg).value.trim().replace(",", "."); if (sve !== "") m = u = sve; await api("/api/nalog/" + d.id, { method: "PUT", body: { rabat_materijal: parseFloat(m) || 0, rabat_usluge: parseFloat(u) || 0 } }); toast("Rabat primijenjen"); render(); } }], nakon: function (bg) { q("#rs", bg).focus(); } }); };
    qa("[data-rucna]").forEach(function (b) { b.onclick = async function () { await api("/api/rucne/" + b.dataset.rucna + "?tko=" + S.korisnik, { method: "DELETE" }); render(); }; });
    qa("[data-vrati]").forEach(function (b) { b.onclick = async function () { await api("/api/nalog/" + d.id + "/stavka", { method: "PUT", body: { kljuc: b.dataset.vrati } }); render(); }; });
    qa("[data-st]").forEach(function (i) { i.onchange = async function () {
      var kl = i.dataset.st, polje = i.dataset.polje, v = i.value.trim().replace(",", "."), b = {};
      if (v === "") { if (polje === "kolicina") { toast("količina mora biti > 0", true); render(); return; } b.ponisti = [polje]; } else { if (isNaN(parseFloat(v))) { toast("upiši broj", true); render(); return; } b[polje] = parseFloat(v); }
      if (kl.indexOf("R:") === 0) await api("/api/rucne/" + kl.slice(2), { method: "PUT", body: b }); else { b.kljuc = kl.slice(2); await api("/api/nalog/" + d.id + "/stavka", { method: "PUT", body: b }); }
      render(); }; i.onkeydown = function (e) { if (e.key === "Enter") i.blur(); }; });
    qa("[data-kupac]").forEach(function (b) { b.onclick = function () { H.kupacPotvrdio(d); }; });
    qa("[data-promjene]").forEach(function (b) { b.onclick = function () { promjeneDijalog(ponude.filter(function (v) { return v.id === +b.dataset.promjene; })[0], brojP); }; });
    qa("[data-eslog]").forEach(function (b) { b.onclick = async function () { var r = await api("/api/ponuda/" + b.dataset.eslog + "/eslog", { body: {} }); toast("eSlog: " + (r.put || r.eslog || JSON.stringify(r)).toString().slice(0, 120)); }; });
    qa("[data-stavke]").forEach(function (b) { b.onclick = async function () {
      var v = await api("/api/ponuda/" + b.dataset.stavke), neto = 0;
      var t = (v.stavke || []).map(function (s) { neto += s.iznos || 0; return '<tr><td class="mono">' + esc(s.pantheon_ident) + '</td><td class="wrap">' + esc(s.naziv || "") + '</td><td class="r num">' + n(s.kolicina, 2) + '</td><td>' + esc(s.jm || "") + '</td><td class="r num">' + n(s.cijena, 2) + '</td><td class="r num">' + n(s.rabat || 0, 0) + ' %</td><td class="r num"><b>' + n(s.iznos, 2) + '</b></td></tr>'; }).join("");
      dlg({ naslov: "Ponuda " + esc(brojP) + " · v" + v.verzija + " (" + esc(v.status) + ")", wide: true, tijelo: '<div class="note">' + (v.poslano_kada ? "poslano " + esc(v.poslano_kada.slice(0, 16).replace("T", " ")) + " → " + esc(v.poslano_na || "") : "nije poslana") + '</div><div class="lista" style="max-height:60vh"><table><thead><tr><th>Ident</th><th>Naziv</th><th class="r">Količina</th><th>JM</th><th class="r">Cijena</th><th class="r">Rabat</th><th class="r">Iznos</th></tr></thead><tbody>' + t + '</tbody><tfoot><tr><td colspan="6" class="r"><b>Neto</b></td><td class="r num"><b>' + n(neto, 2) + '</b></td></tr><tr><td colspan="6" class="r">S PDV-om</td><td class="r num"><b>' + n(neto * 1.25, 2) + ' €</b></td></tr></tfoot></table></div>',
        gumbi: [{ txt: "PDF", on: function () { window.open("/api/ponuda/" + v.id + "/pdf", "_blank"); return false; } }] }); }; });
    if (uredivo) noviRedak(d);
    if (S.fokusNovi) { S.fokusNovi = false; if (q("#nQ")) q("#nQ").focus(); }
  };
  E.nalog_obracun = E.nalog_ponuda;                    // stara ruta
  function noviRedak(d) {
    /* redak „+ novi“ na dnu tablice, kao u Pantheonu: tipkaš ident ili naziv → padajući popis iz šifrarnika (ident + naziv + cijena) →
       strelice / Enter ili klik → količina → Enter doda. Cijena prazna = iz Pantheona; rabat prazan = s naloga po grupi. */
    var inp = q("#nQ"), pad = q("#nPad"), kol = q("#nKol"), cij = q("#nCij"), rab = q("#nRab"), jm = q("#nJm"), izn = q("#nIzn"), t = null, lst = [], sel = -1, odabran = null;
    function grupa(x) { var k = (x.klasif || x.ident || "").slice(0, 2); return k === "OK" ? "okov" : k === "US" ? "usluga" : (k === "IV" || k === "TR" || k === "RP" || k === "ZO") ? "materijal" : "ostalo"; }
    function rabatZa(g) { return g === "usluga" ? d.rabat_usluge : d.rabat_materijal; }
    function iznos() { if (!odabran) { izn.textContent = "—"; return; } var c = cij.value !== "" ? parseFloat(cij.value.replace(",", ".")) : odabran.cijena_neto, k = parseFloat(kol.value.replace(",", ".")) || 0, r = rab.value !== "" ? parseFloat(rab.value) : rabatZa(grupa(odabran)); izn.textContent = c == null ? "—" : n(k * c * (1 - (r || 0) / 100), 2); }
    function prikazi() { pad.innerHTML = lst.map(function (x, i) { return '<div class="li' + (i === sel ? " on" : "") + '" data-i="' + i + '"><span class="mono" style="width:86px">' + esc(x.ident) + '</span><span class="grow">' + esc(x.naziv) + (x.aktivan ? "" : ' <span class="tag">neaktivan</span>') + '</span><span class="note">' + esc(x.jm || "") + '</span><span class="num" style="width:72px;text-align:right">' + (x.cijena_neto == null ? "—" : n(x.cijena_neto, 2)) + '</span></div>'; }).join("") || '<div class="note" style="padding:8px 10px">nema takvog identa ni naziva — artikl prvo otvoriti u Pantheonu pa osvježiti šifrarnik</div>';
      var rc = inp.getBoundingClientRect(); pad.style.left = rc.left + "px"; pad.style.top = (rc.bottom + 2) + "px"; pad.style.width = Math.max(rc.width, 560) + "px";   // fixed: izlazi iz tablice koja skrola
      pad.classList.add("on"); qa(".li", pad).forEach(function (el) { el.onmousedown = function (e) { e.preventDefault(); odaberi(lst[+el.dataset.i]); }; }); }
    function odaberi(x) { odabran = x; inp.value = x.ident + " · " + x.naziv; jm.textContent = x.jm || "KOM"; cij.value = ""; cij.placeholder = x.cijena_neto == null ? "nema cijene" : n(x.cijena_neto, 2); rab.placeholder = n(rabatZa(grupa(x)), 0); pad.classList.remove("on"); iznos(); kol.focus(); kol.select(); }
    inp.oninput = function () { odabran = null; jm.textContent = "—"; izn.textContent = "—"; clearTimeout(t); var v = inp.value.trim(); if (v.length < 2) { pad.classList.remove("on"); return; }
      t = setTimeout(async function () { lst = await api("/api/sifrarnik/identi?q=" + encodeURIComponent(v) + "&limit=25"); sel = lst.length ? 0 : -1; prikazi(); }, 200); };
    inp.onkeydown = function (e) { if (!pad.classList.contains("on")) { if (e.key === "Enter" && odabran) kol.focus(); return; } if (e.key === "ArrowDown") { sel = Math.min(sel + 1, lst.length - 1); prikazi(); e.preventDefault(); } else if (e.key === "ArrowUp") { sel = Math.max(sel - 1, 0); prikazi(); e.preventDefault(); } else if (e.key === "Enter") { e.preventDefault(); if (sel >= 0) odaberi(lst[sel]); } else if (e.key === "Escape") pad.classList.remove("on"); };
    inp.onblur = function () { setTimeout(function () { pad.classList.remove("on"); }, 150); };
    inp.onfocus = function () { if (lst.length && !odabran) prikazi(); };
    [kol, cij, rab].forEach(function (el) { el.oninput = iznos; el.onkeydown = function (e) { if (e.key === "Enter") { e.preventDefault(); dodaj(); } }; });
    async function dodaj() {
      if (!odabran) { toast("odaberi artikl iz popisa (ident ili naziv)", true); inp.focus(); return; }
      var k = parseFloat(kol.value.replace(",", ".")); if (!(k > 0)) { toast("količina mora biti > 0", true); kol.focus(); return; }
      await api("/api/nalog/" + d.id + "/rucne", { body: { pantheon_ident: odabran.ident, kolicina: k, cijena: cij.value === "" ? null : parseFloat(cij.value.replace(",", ".")), rabat: rab.value === "" ? null : parseFloat(rab.value), grupa: grupa(odabran) } });
      S.fokusNovi = true; render();
    }
    q("#nDodaj").onclick = dodaj;
  }
  async function potpis() { try { return (await api("/api/korisnici/" + encodeURIComponent(S.korisnik) + "/potpis", { tiho: true })).potpis || "Paneli projekt d.o.o."; } catch (e) { return "Paneli projekt d.o.o."; } }
  async function posaljiPonudu(d, vid) {
    var pot = await potpis();
    dlg({ naslov: "Pošalji ponudu kupcu", tijelo: '<div class="field"><span class="lbl">Na adresu</span><input id="na" value="' + esc(d.kupac_email || "") + '" placeholder="kupac@…"></div><div class="field"><span class="lbl">Tekst poruke (PDF ide u prilogu)</span><textarea id="tekst" rows="5">Poštovani,\n\nu prilogu je ponuda za ' + esc(d.naziv) + '. Za potvrdu ili pitanja slobodno se javite.\n\nLijep pozdrav,\n' + esc(pot) + '</textarea></div><div class="row"><label class="note"><input type="checkbox" id="suho"> samo pripremi, ne šalji</label></div>',
      gumbi: [{ txt: "Pošalji", pri: true, on: async function (bg) { if (!q("#na", bg).value.trim()) { toast("upiši adresu", true); return false; } var r = await api("/api/ponuda/" + vid + "/posalji", { body: { na: q("#na", bg).value.trim(), tekst: q("#tekst", bg).value, suho: q("#suho", bg).checked } }); toast(r.poslano === false || (r.mail && r.mail.poslano === false) ? "Pripremljeno (nije poslano)" : "Poslano na " + q("#na", bg).value); render(); } }] });
  }

  // ---------------------------------------------------------------- ekran 4: skladište naloga
  E.nalog_skladiste = async function (r) {
    var d = S.nalog = await api("/api/nalog/" + r.id), pr = await api("/api/nalog/" + d.id + "/skladiste");
    function statusSkl(m) {
      /* 2A: stanje materijala uz sam materijal — zeleno dostupno, crveno manjak, žuto čeka (optimizacija / potvrda), sivo informacija */
      if (m.manjak) return m.na_restlu ? '<span class="stat crit"><i>!</i> Nema restla</span>' : '<span class="stat crit"><i>!</i> Manjak ' + n(m.manjak, 0) + '</span>';
      if (m.manjak === 0) return '<span class="stat ok"><i>✓</i> Dostupno</span>';
      if (m.vrsta === "RP" || m.vrsta === "ZO") return '<span class="stat info">Ne vodi se u Winstoreu</span>';
      return m.upozorenje ? '<span class="stat warn" title="' + esc(cist(m.upozorenje)) + '"><i>◷</i> ' + esc(cist(m.upozorenje).split(" — ")[0]) + '</span>' : "";
    }
    var rows = pr.materijali.map(function (m) {
      var st = m.stanje || { ploce: {}, restlovi: {} }, tr = Object.keys(m.trake || {}).map(function (k) { return m.trake[k]; });
      return '<tr><td><b>' + esc(m.naziv) + '</b><div class="note">' + esc(m.ident || "") + ' ' + tagPut(m.put) + '</div></td>' +
        '<td class="r num">' + (m.na_restlu ? 'restl ' + m.restl_mjera.join("×") : (m.ploce == null ? '<span class="warn-t">?</span>' : m.ploce + ' pl.')) + '</td>' +
        '<td class="r num">' + n(st.ploce.fizicko, 0) + (st.ploce.lokacija ? '<div class="note">' + esc(st.ploce.lokacija) + '</div>' : "") + '</td><td class="r num">' + n(st.ploce.rezervirano, 0) + (m.rezervirano_ovaj ? '<div class="note">ovaj ' + m.rezervirano_ovaj + '</div>' : "") + '</td><td class="r num">' + n(st.ploce.naruceno, 0) + '</td><td class="r num"><b>' + n(st.ploce.raspolozivo, 0) + '</b></td>' +
        '<td>' + statusSkl(m) + '</td>' +
        '<td>' + ((st.restlovi.kom || 0) ? st.restlovi.kom + ' restl / ' + n(st.restlovi.m2, 2) + ' m²' : '—') + (m.restl_rezerviran && m.restl_rezerviran.length ? '<div class="note">rezerviran ' + m.restl_rezerviran.map(function (x) { return x.oznaka; }).join(", ") + '</div>' : "") +
        ((m.restl_kandidati || []).length ? '<div class="row" style="margin-top:4px">' + m.restl_kandidati.slice(0, 4).map(function (k) { return '<button class="btn sm" data-restl="' + m.nalog_materijal_id + ':' + k.id + '" title="' + esc(k.lokacija || "") + '">' + esc(k.oznaka) + ' ' + mm(k.L) + '×' + mm(k.W) + '</button>'; }).join("") + '</div>' : "") + '</td>' +
        '<td class="trake-c">' + tr.map(function (t) { return '<div>' + esc(t.ident) + ' <span class="note">' + esc((t.naziv || "").slice(0, 26)) + '</span> ' + t.metri + ' m' + (t.na_roli != null ? ' <span class="' + (t.manjak ? "crit-t" : "ok-t") + '">(na roli ' + n(t.na_roli, 1) + ')</span>' : ' <span class="note">(Regal traka nedostupna)</span>') + (t.pretinac ? ' <span class="tag info">' + esc(t.pretinac) + '</span>' : "") + '</div>'; }).join("") + '</td></tr>';
    }).join("");
    var pri = await api("/api/skladiste/prijedlozi?nalog=" + d.id);
    var sazSkl = (function () {
      /* 2A: jedna poruka iznad tablice umjesto žute trake po materijalu */
      var man = pr.materijali.filter(function (m) { return m.manjak && !m.na_restlu; }), ploca_ = man.reduce(function (a, m) { return a + (+m.manjak || 0); }, 0);
      var restl = pr.materijali.filter(function (m) { return m.manjak && m.na_restlu; }).length;
      var trake = 0; pr.materijali.forEach(function (m) { Object.keys(m.trake || {}).forEach(function (k) { if (m.trake[k].manjak) trake++; }); });
      var nepoz = pr.materijali.filter(function (m) { return m.manjak == null && m.upozorenje && m.vrsta !== "RP" && m.vrsta !== "ZO"; }).length;
      var dij = [];
      if (man.length) dij.push('<b>' + man.length + ' ' + sklonMat(man.length) + ' ' + (man.length % 10 >= 2 && man.length % 10 <= 4 && (man.length % 100 < 12 || man.length % 100 > 14) ? "imaju" : "ima") + ' manjak · ukupno ' + n(ploca_, 0) + ' ' + ploca(ploca_) + '</b>');
      if (restl) dij.push('<b>' + restl + ' bez restla na stanju</b>');
      if (trake) dij.push('<b>' + trake + (trake === 1 ? " traka nema" : " traka nema") + ' dovoljno metara na roli</b>');
      if (nepoz) dij.push(nepoz + ' ' + sklonMat(nepoz) + ' bez potvrđene optimizacije (broj ploča nepoznat)');
      if (!dij.length) return pr.materijali.length ? '<div class="sazetak ok"><span class="ik">✓</span><div class="txt"><b>Sav materijal je raspoloživ</b></div></div>' : "";
      return '<div class="sazetak' + (man.length || restl || trake ? "" : " info") + '"><span class="ik">!</span><div class="txt">' + dij.join(" · ") + '</div>' + (pr.za_nabavu.length ? '<a class="btn pri" href="#/nabava">Otvori nabavu</a>' : "") + '</div>';
    })();
    var priHtml = pri.prijedlozi.map(function (p) { return '<tr><td class="mono">' + esc(p.oznaka) + '</td><td>' + esc(p.ident) + ' ' + esc(p.naziv_kratki || "") + '</td><td class="r num">' + mm(p.L) + ' × ' + mm(p.W) + '</td><td class="r num">' + n(p.m2, 2) + '</td><td class="note">' + esc(p.napomena || "") + '</td><td class="r"><button class="btn sm pri" data-potvrdi-restl="' + p.id + '">Potvrdi (QR)</button> <button class="btn sm" data-odbaci-restl="' + p.id + '">Nema ga</button></td></tr>'; }).join("");
    ljuska({ crumb: crumb(d, "skladište"), koraci: koraci(d), rail: "nalozi", cls: "c1 puna",
      akcije: '<a class="tbtn" href="#/nalog/' + d.id + '/ponuda">← Ponuda</a><span class="grow"></span><button class="tbtn" id="btnOslobodi">Oslobodi</button><button class="tbtn' + (d.status === "skladiste" ? "" : " pri") + '" id="btnRezerviraj">' + (d.status === "skladiste" ? "Rezerviraj ponovno" : "Rezerviraj materijal") + '</button>' + (d.status === "skladiste" ? '<button class="tbtn pri" id="btnNaStroj">→ Proizvodnja</button>' : ""),
      sadrzaj: '<div class="col"><div class="pane"><div class="hd"><b>Provjera skladišta</b><span class="note">raspoloživo = fizičko (Winstore) − rezervirano (drugi nalozi) + naručeno</span></div>' +
        '<div class="bd tight">' + sazSkl + '<table><thead><tr><th>Materijal</th><th class="r">Treba</th><th class="r">Fizičko</th><th class="r">Rezerv.</th><th class="r">Naručeno</th><th class="r">Raspoloživo</th><th>Status</th><th>Restlovi</th><th>Trake</th></tr></thead><tbody>' + (rows || '<tr><td colspan="9" class="note">nalog nema materijala</td></tr>') + '</tbody></table>' +
        (pr.materijali.some(function (m) { return m.vrsta === "RP" || m.vrsta === "ZO"; }) ? '<div class="info-red"><span class="ik">i</span><span><b>Radne ploče i zidne obloge:</b> stanje se ne vodi u Winstoreu.</span></div>' : "") + '</div></div>' +
        (pr.za_nabavu.length ? '<div class="pane"><div class="hd"><b>Za nabavu</b></div><div class="bd tight"><table><thead><tr><th>Ident</th><th>Naziv</th><th class="r">Količina</th><th>JM</th></tr></thead><tbody>' + pr.za_nabavu.map(function (z) { return '<tr><td class="mono">' + esc(z.ident) + '</td><td>' + esc(z.naziv || "") + '</td><td class="r num">' + n(z.kom, 1) + '</td><td>' + esc(z.jm) + '</td></tr>'; }).join("") + '</tbody></table></div></div>' : "") +
        '<div class="pane"><div class="hd"><b>Restlovi iz shema ovog naloga</b><span class="note">korisni ostaci ≥ 400 × 400 i ≥ 1 m² koje kupcu ne naplaćujemo — skladištar ih potvrdi kad ih izreže i zalijepi QR</span><span class="grow"></span>' + (pri.prijedlozi.length ? '<a class="btn sm" href="/api/skladiste/restlovi/naljepnice.pdf?nalog=' + d.id + '" target="_blank">Naljepnice PDF</a>' : "") + '</div><div class="bd tight"><table><thead><tr><th>Oznaka</th><th>Materijal</th><th class="r">Mjere</th><th class="r">m²</th><th>Iz sheme</th><th></th></tr></thead><tbody>' + (priHtml || '<tr><td colspan="6" class="note">nema prijedloga (nastaju kad nalog uđe u Skladište s potvrđenom optimizacijom)</td></tr>') + '</tbody></table></div></div></div>',
      foot: kpi(pr.materijali.length, "materijala") + kpi(pr.za_nabavu.length, "za nabavu") + kpi(pri.prijedlozi.length, "restl prijedloga") + '<span class="grow"></span><span class="note">' + esc(H.statusNaziv(d.status)) + '</span>' });
    q("#btnRezerviraj").onclick = async function () {
      if (d.status === "potvrdjeno" || d.status === "ponuda") {           // prijelaz u Skladište sam rezervira — zelena točka ide na 4 Skladište
        var rs = await api("/api/nalog/" + d.id + "/status", { body: { status: "skladiste" } }); var up = (rs.skladiste && rs.skladiste.upozorenja) || [];
        toast(up.length ? "U skladištu — " + up.join("; ") : "U skladištu, materijal rezerviran", !!up.length); render(); return; }
      var rr = await api("/api/nalog/" + d.id + "/skladiste/rezerviraj", { body: { restlovi: {} } }); toast(rr.ok ? "Rezervirano, sve raspoloživo" : "Rezervirano — " + rr.upozorenja.length + " upozorenja", !rr.ok); render(); };
    q("#btnOslobodi").onclick = async function () { await api("/api/nalog/" + d.id + "/skladiste/oslobodi", { body: {} }); render(); };
    if (q("#btnNaStroj")) q("#btnNaStroj").onclick = async function () { await api("/api/nalog/" + d.id + "/status", { body: { status: "pila_nesting" } }); idi("#/nalog/" + d.id + "/proizvodnja"); };
    qa("[data-restl]").forEach(function (b) { b.onclick = async function () { var p = b.dataset.restl.split(":"), o = {}; o[p[0]] = +p[1]; await api("/api/nalog/" + d.id + "/skladiste/rezerviraj", { body: { restlovi: o } }); render(); }; });
    qa("[data-potvrdi-restl]").forEach(function (b) { b.onclick = async function () { var lok = prompt("Lokacija restla (A001, SATOR B 2.1…)"); if (lok === null) return; await api("/api/skladiste/restlovi/" + b.dataset.potvrdiRestl + "/potvrdi", { body: { lokacija: lok || null } }); render(); }; });
    qa("[data-odbaci-restl]").forEach(function (b) { b.onclick = async function () { await api("/api/skladiste/restlovi/" + b.dataset.odbaciRestl + "/odbaci", { body: { razlog: "nema ga nakon rezanja" } }); render(); }; });
  };

  // ---------------------------------------------------------------- ekran 5: proizvodnja (pila / nesting) — Igor, 17. 9.: naziv „Proizvodnja“, materijali u punoj visini bez unutarnjeg skrolanja
  E.nalog_pila = async function (r) {
    var d = S.nalog = await api("/api/nalog/" + r.id), opt = await api("/api/nalog/" + d.id + "/optimizacija"), rez = await api("/api/nalog/" + d.id + "/rezultati");
    var post = {}; (await api("/api/postavke/optimizacija")).forEach(function (x) { post[x.kljuc] = x.vrijednost; });
    var mapaN = post.mapa_nesting || "C:\\PPNESTING", mapaP = post.mapa_pila || "C:\\PILA";      // mape su postavke (jednom se podese), ne polja na ekranu
    var mats = d.materijali.map(function (m) {
      /* 3A: naslov + stanje + put, shema, tri ključne brojke, rezultat nestinga, poravnate akcije (pregled i PDF neutralni) */
      var rr = (rez || []).filter(function (x) { return x.nalog_materijal_id === m.id; })[0] || null;
      var o = opt.filter(function (x) { return x.nalog_materijal_id === m.id; })[0] || {}, p = o.potvrdjeno;
      var stat = p ? '<span class="stat ok"><i>✓</i> Potvrđeno</span>' : (o.treba === false ? '<span class="stat info">bez optimizacije</span>' : '<span class="stat crit"><i>!</i> Nije potvrđeno</span>');
      var put = '<span class="lbl">Put</span><select data-put="' + m.id + '"><option value="">— ' + (m.put_prijedlog ? "Hub: " + esc(m.put_prijedlog) : "") + '</option><option value="pila"' + (m.put === "pila" ? " selected" : "") + '>pila</option><option value="nesting"' + (m.put === "nesting" ? " selected" : "") + '>nesting</option></select>';
      var head = '<div class="kart-hd"><div class="grow"><div class="naslov">' + esc(m.naziv_kratki || m.naziv_ulaz || "") + '</div><div class="meta">' + esc(m.ident || "") + ' · ' + m.elemenata + ' el / ' + m.komada + ' kom · ' + n(m.m2, 2) + ' m²' + (m.debljina ? ' · ' + m.debljina + ' mm' : "") + '</div></div>' + stat + '<span class="row nw" style="gap:6px;margin-left:8px">' + put + '</span></div>';
      if (!p) return '<div class="pane kart">' + head + (o.treba === false ? '<div class="kart-tijelo">Materijal po dužnom metru — nema optimizacije.</div>' : '<div class="upoz crit">Optimizacija nije potvrđena — <a href="#/nalog/' + d.id + '/optimizacija">potvrdi je u koraku 2 Optimizacija</a>; bez toga nema izvoza na stroj.</div>') + '</div>';
      var rezultat = [rr && rr.bnest ? 'bNest: <b>' + rr.bnest.broj_ploca + ' ' + ploca(rr.bnest.broj_ploca) + '</b> · isk. ' + pct(rr.bnest.iskoristenje) + (rr.razlika_ploca != null ? ' · razlika <b class="' + (rr.razlika_ploca < 0 ? "ok-t" : "warn-t") + '">' + rr.razlika_ploca + '</b>' : "") : "",
        rr && rr.spojeni_posao ? '<span class="tag info">spojeno: ' + esc(rr.spojeni_posao.naziv) + (rr.spojeni_posao.rezultat_stigao ? " ✓" : "") + '</span>' : "", rr && rr.hub ? 'izvezeno na pilu' : ""].filter(Boolean).join(" · ");
      return '<div class="pane kart">' + head + '<div class="kart-red">' + '<a class="kart-shema" href="#" data-pregled="' + p.id + '" data-nm="' + m.id + '" title="Pregled shema"><img src="/api/optimizacija/' + p.id + '/sheme.png?h=130" alt="" onerror="this.parentNode.classList.add(\'nema\')"></a>' +
        '<div class="kart-desno">' + brojke(p) + '<div class="kart-meta">' + esc(p.nacin || "") + (p.rezova ? ' · rezova ' + p.rezova : "") + (p.naplata_rp ? '<br>' + esc(p.naplata_rp.naziv) + ': ' + esc(p.naplata_rp.opis_kratko || "") : "") + (rezultat ? '<br>' + rezultat : "") + '</div></div></div>' +
        '<div class="kart-akcije"><button class="btn" data-pregled="' + p.id + '" data-nm="' + m.id + '">Pregled shema</button><a class="btn" href="/api/nalog/' + d.id + '/ispis/krojni.pdf?materijal=' + m.id + '" target="_blank">Krojni nacrt PDF</a></div></div>';
    }).join("");
    ljuska({ crumb: crumb(d, "proizvodnja"), koraci: koraci(d), rail: "nalozi", cls: "c2 proizv",
      akcije: '<a class="tbtn" href="#/nalog/' + d.id + '/skladiste">← Skladište</a><span class="grow"></span><a class="tbtn" href="/api/nalog/' + d.id + '/ispis/krojni.pdf" target="_blank">Krojni nacrt</a><button class="tbtn" id="btnRez">Rezultat bNest (.mno)</button>',
      sadrzaj: '<div class="col">' + mats + '</div>' +
        '<div class="col"><div class="pane"><div class="hd"><b>Izvoz na stroj</b></div><div class="bd">' +
        '<div class="row"><button class="btn" data-izvoz="nesting" data-suho="1">Nesting — pregled</button><button class="btn pri" data-izvoz="nesting">Nesting — pošalji</button></div><div class="row"><button class="btn" data-izvoz="pila" data-suho="1">Pila — pregled</button><button class="btn pri" data-izvoz="pila">Pila — pošalji</button></div><div class="row"><button class="btn" data-izvoz="pw">PanelWizard CPW</button></div>' +
        '<div class="note">Mape: nesting <span class="mono">' + esc(mapaN) + '</span> · pila <span class="mono">' + esc(mapaP) + '</span> <a href="#/postavke">(Postavke)</a>. Na stroj ide samo nalog u statusu potvrđeno / skladište / pila-nesting, bez stavki za potvrdu i s potvrđenom optimizacijom.</div><div id="izvozRez"></div></div></div>' +
        '<div class="pane"><div class="hd hd-dva"><b>Spajanje s drugim nalozima</b><span class="note">isti materijal, zajedno na nesting — tu se bira drukčija optimizacija</span></div><div class="bd" id="spajanje"><span class="note">učitavam…</span></div></div></div>',
      foot: kpi(d.sazetak.materijala, "materijala") + kpi(d.sazetak.elemenata + " / " + d.sazetak.komada, "el / kom") + '<span class="grow"></span><span class="note">' + esc(H.statusNaziv(d.status)) + '</span>' });
    veziOpt(d, opt);
    qa("[data-put]").forEach(function (s) { s.onchange = async function () { await api("/api/nalog/materijal/" + s.dataset.put, { method: "PUT", body: { put: s.value || null } }); render(); }; });
    qa("[data-izvoz]").forEach(function (b) { b.onclick = async function () {
      var vrsta = b.dataset.izvoz, suho = !!b.dataset.suho, mapa = vrsta === "pila" ? mapaP : mapaN;
      var rr = await api("/api/nalog/" + d.id + "/izvoz/" + vrsta, { body: { mapa: mapa, suho: suho } });
      q("#izvozRez").innerHTML = '<div class="upoz ' + (suho ? "" : "ok") + '"><b>' + (suho ? "Pregled" : "Izvezeno") + ' — ' + esc(vrsta) + '</b> → ' + esc(rr.mapa || mapa) + '<br>' + (rr.paketi || []).map(function (p) { return esc(p.materijal) + ': ' + (p.program ? esc(p.program) + ' · ' : "") + p.elemenata + ' el / ' + p.komada + ' kom' + (p.ploca ? ' · ' + p.ploca + ' ploča' : "") + (p.cix ? ' · ' + p.cix.length + ' CIX' : "") + (p.optimizacija_potvrdjena === false ? ' <span class="warn-t">(optimizacija nije potvrđena)</span>' : ""); }).join("<br>") +
        ((rr.preskoceno || []).length ? '<br><span class="warn-t">preskočeno: ' + rr.preskoceno.map(function (x) { return esc(x.materijal) + " (" + esc(x.razlog) + ")"; }).join("; ") + '</span>' : "") + ((rr.upozorenja || []).length ? '<br>' + rr.upozorenja.map(function (u) { return esc(cist(u)); }).join("<br>") : "") + '</div>';
      if (!suho) render(); }; });
    q("#btnRez").onclick = function () { dlg({ naslov: "Rezultat s nestinga (bNest .mno)", tijelo: '<div class="field"><span class="lbl">Datoteka .mno ili mapa na poslužitelju</span><input id="put" placeholder="C:\\PPNESTING\\' + esc(d.naziv) + '\\NESTING\\OUT"></div>', gumbi: [{ txt: "Učitaj", pri: true, on: async function (bg) { var v = q("#put", bg).value.trim(); var rr = await api("/api/rezultat/nesting", { body: v.toLowerCase().endsWith(".mno") ? { put: v } : { mapa: v } }); toast("Uvezeno: " + JSON.stringify(rr).slice(0, 160)); render(); } }] }); };
    api("/api/spajanje").then(function (sp) {
      var lst = (sp.prijedlozi || []).filter(function (p) { return (p.stavke || []).some(function (x) { return x.nalog_id === d.id; }); });
      q("#spajanje").innerHTML = lst.length ? lst.map(function (p) { return '<div class="upoz"><b>' + esc(p.naziv) + '</b>: ' + p.naloga + ' naloga, zasebno ' + p.ploca_zasebno + ' → spojeno ' + p.ploca_spojeno + ' ploča (ušteda ' + p.usteda + ')<div class="note">' + (p.stavke || []).map(function (x) { return esc(x.naziv) + " " + n(x.ploca, 2) + " pl."; }).join(", ") + '</div><div class="row" style="margin-top:6px"><button class="btn sm pri" data-spoji="' + (p.stavke || []).map(function (x) { return x.nm_id; }).join(",") + '">Spoji i izvezi na nesting</button></div></div>'; }).join("") : '<span class="note">nema prijedloga za ovaj nalog</span>';
      qa("[data-spoji]").forEach(function (b) { b.onclick = async function () { var rr = await api("/api/spajanje/izvezi", { body: { nm_ids: b.dataset.spoji.split(",").map(Number), mapa: mapaN } }); toast("Spojeni posao " + (rr.posao || rr.naziv || "") + " izvezen"); render(); }; });
    }).catch(function () { q("#spajanje").innerHTML = '<span class="note">—</span>'; });
  };

  E.nalog_proizvodnja = E.nalog_pila;
  E.nalog_optimizacija = E.nalog_slaganje;               // „/slaganje“ ostaje za stare poveznice (naziv „Optimizacija“, Igor 17. 9.)                 // „/pila“ ostaje za stare poveznice

  // ---------------------------------------------------------------- skladište (globalno): stanje, restlovi, potvrde dekora
  E.skladiste = async function (r) {
    var pod = r.id || "stanje";
    var akcije = '<a class="tbtn' + (pod === "stanje" ? " on" : "") + '" href="#/skladiste/stanje">Stanje</a><a class="tbtn' + (pod === "restlovi" ? " on" : "") + '" href="#/skladiste/restlovi">Restlovi</a><a class="tbtn' + (pod === "potvrde" ? " on" : "") + '" href="#/skladiste/potvrde">Dekori za potvrdu</a><a class="tbtn" href="#/skladistar">Skladištar</a>';
    if (pod === "restlovi") {
      var f = S.restlFilter || (S.restlFilter = { status: "slobodan,rezerviran,provjeri,prijedlog", q: "" });
      var rs = await api("/api/skladiste/restlovi?status=" + encodeURIComponent(f.status) + "&q=" + encodeURIComponent(f.q) + "&limit=400"), sz = await api("/api/skladiste/restlovi/sazetak");
      var rows = rs.restlovi.map(function (x) { return '<tr><td class="mono"><a href="/r/' + esc(x.oznaka) + '" target="_blank">' + esc(x.oznaka) + '</a></td><td>' + (x.ident ? esc(x.ident) + ' ' + esc(x.naziv_kratki || "") : '<span class="warn-t">' + esc(x.dekor_ulaz || "") + ' (za potvrdu)</span>') + '</td><td class="r num">' + mm(x.L) + ' × ' + mm(x.W) + (x.kom > 1 ? ' × ' + x.kom : "") + '</td><td class="r num">' + n(x.m2, 2) + '</td><td>' + esc(x.lokacija || "—") + '</td><td><span class="tag ' + (x.status === "slobodan" ? "ok" : x.status === "prijedlog" ? "warn" : x.status === "rezerviran" ? "abs" : "") + '">' + esc(x.status) + '</span></td><td class="note">' + esc(x.napomena || "") + '</td>' +
        '<td class="r">' + (x.status === "prijedlog" || x.status === "provjeri" ? '<button class="btn sm pri" data-potvrdi-restl="' + x.id + '">Potvrdi</button> ' : "") + (x.status !== "potrosen" && x.status !== "otpisan" ? '<button class="btn sm" data-otpis="' + x.id + '">Otpiši</button>' : "") + '</td></tr>'; }).join("");
      ljuska({ crumb: "<b>Skladište</b> · restlovi", rail: "sklad", cls: "c1", akcije: akcije + '<button class="tbtn" id="btnNoviRestl">+ Restl</button><a class="tbtn" href="/api/skladiste/restlovi/naljepnice.pdf?status=prijedlog" target="_blank">Naljepnice prijedloga</a>',
        sadrzaj: '<div class="pane"><div class="hd"><div class="row">' + [["slobodan,rezerviran,provjeri,prijedlog", "Na stanju + prijedlozi"], ["slobodan", "Slobodni"], ["prijedlog", "Prijedlozi"], ["provjeri", "Provjeri"], ["potrosen,otpisan", "Potrošeni / otpisani"]].map(function (x) { return '<span class="chip' + (f.status === x[0] ? " on" : "") + '" data-st="' + x[0] + '">' + x[1] + '</span>'; }).join("") + '</div><span class="grow"></span><input id="q" placeholder="oznaka, dekor, lokacija…" value="' + esc(f.q) + '" style="width:240px"></div>' +
          '<div class="bd tight"><table><thead><tr><th>Oznaka</th><th>Materijal</th><th class="r">Mjere</th><th class="r">m²</th><th>Lokacija</th><th>Status</th><th>Napomena</th><th></th></tr></thead><tbody>' + (rows || '<tr><td colspan="8" class="note">nema restlova</td></tr>') + '</tbody></table></div></div>',
        foot: kpi(sz.ukupno, "restlova") + kpi(n(sz.m2_na_stanju, 0), "m² na stanju") + kpi(sz.dekora_za_potvrdu, "dekora za potvrdu") + kpi((sz.po_statusu || {}).prijedlog || 0, "prijedloga") + '<span class="grow"></span><span class="note">' + esc(sz.zadnji_uvoz || "") + '</span>' });
      qa("[data-st]").forEach(function (c) { c.onclick = function () { f.status = c.dataset.st; render(); }; });
      var t; q("#q").oninput = function () { clearTimeout(t); f.q = this.value; t = setTimeout(render, 250); };
      qa("[data-potvrdi-restl]").forEach(function (b) { b.onclick = async function () { var lok = prompt("Lokacija (A001, SATOR B 2.1…)"); if (lok === null) return; await api("/api/skladiste/restlovi/" + b.dataset.potvrdiRestl + "/potvrdi", { body: { lokacija: lok || null } }); render(); }; });
      qa("[data-otpis]").forEach(function (b) { b.onclick = async function () { var z = prompt("Razlog otpisa"); if (z === null) return; await api("/api/skladiste/restlovi/" + b.dataset.otpis + "/odbaci", { body: { razlog: z } }); render(); }; });
      q("#btnNoviRestl").onclick = function () { var mat = null; dlg({ naslov: "Novi restl", tijelo: '<div class="field"><span class="lbl">Materijal</span><input placeholder="dekor, ident…"><div class="lista"></div></div><div id="odm" class="note">—</div><div class="grid3"><div class="field"><span class="lbl">L</span><input id="L"></div><div class="field"><span class="lbl">W</span><input id="W"></div><div class="field"><span class="lbl">Kom</span><input id="kom" value="1"></div></div><div class="grid2"><div class="field"><span class="lbl">Lokacija</span><input id="lok"></div><div class="field"><span class="lbl">Napomena</span><input id="nap"></div></div>',
        gumbi: [{ txt: "Spremi", pri: true, on: async function (bg) { if (!mat) { toast("odaberi materijal", true); return false; } var rr = await api("/api/skladiste/restlovi", { body: { ident: mat.ident, L: +q("#L", bg).value, W: +q("#W", bg).value, kom: +q("#kom", bg).value || 1, lokacija: q("#lok", bg).value || null, napomena: q("#nap", bg).value || null } }); toast("Restl " + rr.oznaka); render(); } }],
        nakon: function (bg) { H.pretragaLista(q(".field", bg), async function (s) { return (await api("/api/sifrarnik/materijali?q=" + encodeURIComponent(s) + "&limit=30")).materijali; }, function (x) { return '<span class="mono">' + esc(x.ident) + '</span> ' + esc(x.naziv); }, function (x) { mat = x; q("#odm", bg).innerHTML = "<b>" + esc(x.ident) + "</b> " + esc(x.naziv); }); } }); };
      return;
    }
    if (pod === "potvrde") {
      var zp = await api("/api/skladiste/restlovi?za_potvrdu=1&limit=500"), grupe = {};
      zp.restlovi.forEach(function (x) { var g = grupe[x.dekor_ulaz] || (grupe[x.dekor_ulaz] = { dekor: x.dekor_ulaz, n: 0, kandidati: x.kandidati || [], ident_ulaz: x.ident_ulaz }); g.n += 1; });
      var lst = Object.keys(grupe).map(function (k) { return grupe[k]; }).sort(function (a, b) { return b.n - a.n; });
      ljuska({ crumb: "<b>Skladište</b> · dekori za potvrdu", rail: "sklad", cls: "c1", akcije: akcije,
        sadrzaj: '<div class="pane"><div class="hd"><b>Dekori iz evidencije restlova bez sigurnog identa</b><span class="note">potvrda vrijedi za sve restlove tog dekora i pamti se (alias)</span></div><div class="bd">' + (lst.map(function (g) {
          return '<div class="upoz"><b>' + esc(g.dekor) + '</b> <span class="note">' + g.n + ' restl' + (g.n === 1 ? "" : "ova") + (g.ident_ulaz ? ' · Excel: ' + esc(g.ident_ulaz) : "") + '</span><div class="row" style="margin-top:6px">' + g.kandidati.slice(0, 4).map(function (k) { return '<button class="btn sm" data-dekor="' + esc(g.dekor) + '" data-ident="' + esc(k[0]) + '">' + esc(k[0]) + ' ' + esc((k[1] || "").slice(0, 36)) + '</button>'; }).join("") + '<button class="btn sm ghost" data-dekor="' + esc(g.dekor) + '" data-ident="">drugi…</button></div></div>'; }).join("") || '<div class="note">svi dekori su vezani</div>') + '</div></div>', foot: kpi(lst.length, "dekora za potvrdu") + kpi(zp.broj, "restlova") });
      qa("[data-dekor]").forEach(function (b) { b.onclick = function () {
        var dekor = b.dataset.dekor; async function upisi(ident) { var rr = await api("/api/skladiste/restlovi/potvrdi-dekor", { body: { dekor: dekor, ident: ident } }); toast(dekor + " → " + ident + " (" + rr.restlova + " restlova)"); render(); }
        if (b.dataset.ident) return upisi(b.dataset.ident);
        dlg({ naslov: "Materijal za „" + dekor + "“", tijelo: '<div class="field"><span class="lbl">Traži u šifrarniku</span><input><div class="lista"></div></div>', nakon: function (bg, zatvori) { H.pretragaLista(q(".field", bg), async function (s) { return (await api("/api/sifrarnik/materijali?q=" + encodeURIComponent(s) + "&limit=40")).materijali; }, function (x) { return '<span class="mono">' + esc(x.ident) + '</span> ' + esc(x.naziv); }, function (x) { zatvori(); upisi(x.ident); }); } }); }; });
      return;
    }
    var st = await api("/api/skladiste/stanje?q=" + encodeURIComponent(S.stanjeQ || "") + "&limit=300");
    var rows = st.materijali.map(function (m) { return '<tr><td class="mono">' + esc(m.ident) + '</td><td>' + esc(m.naziv) + (m.debljina ? ' <span class="note">' + m.debljina + ' mm</span>' : "") + '</td><td>' + esc(m.ploce.lokacija || "—") + '</td><td class="r num">' + n(m.ploce.fizicko, 0) + '</td><td class="r num">' + n(m.ploce.rezervirano, 0) + '</td><td class="r num">' + n(m.ploce.naruceno, 0) + '</td><td class="r num"><b>' + n(m.ploce.raspolozivo, 0) + '</b></td><td class="r num">' + (m.ploce.drop || "") + '</td><td class="r num">' + (m.restlovi.kom ? m.restlovi.kom + ' / ' + n(m.restlovi.m2, 1) + ' m²' : "—") + '</td></tr>'; }).join("");
    ljuska({ crumb: "<b>Skladište</b> · stanje", rail: "sklad", cls: "c1", akcije: akcije,
      sadrzaj: '<div class="pane"><div class="hd"><b>Ploče (Winstore) i restlovi (Hub) po materijalu</b><span class="note">trake su u Regal traki</span><span class="grow"></span><input id="q" placeholder="dekor, ident, Winstore kod…" value="' + esc(S.stanjeQ || "") + '" style="width:260px"></div>' +
        '<div class="bd tight"><table><thead><tr><th>Ident</th><th>Materijal</th><th>Winstore kod</th><th class="r">Fizičko</th><th class="r">Rezerv.</th><th class="r">Naručeno</th><th class="r">Raspol.</th><th class="r">Drop</th><th class="r">Restlovi</th></tr></thead><tbody>' + (rows || '<tr><td colspan="9" class="note">ništa</td></tr>') + '</tbody></table></div></div>',
      foot: kpi(st.broj, "materijala sa stanjem") + kpi(st.materijali.reduce(function (a, m) { return a + (m.ploce.fizicko || 0); }, 0), "ploča u Winstoreu") + kpi(st.materijali.reduce(function (a, m) { return a + (m.restlovi.kom || 0); }, 0), "restlova") });
    var t2; q("#q").oninput = function () { clearTimeout(t2); S.stanjeQ = this.value; t2 = setTimeout(render, 250); };
  };

  // ---------------------------------------------------------------- slike dekora: ekran ureda za potvrdu ponuđenih slika
  E.dekori = async function () {
    var d = await api("/api/dekori/za-potvrdu?limit=60&q=" + encodeURIComponent(S.dekQ || ""));
    var sz = d.sazetak || {};
    var kartice = d.materijali.map(function (m) {
      return '<section class="pane pk dek-kart"><div class="hd"><b>' + esc(m.naziv_pantheon) + '</b><span class="note mono">' + esc(m.pantheon_ident) + '</span>' +
        (m.debljina ? '<span class="note">' + m.debljina + ' mm</span>' : "") + '<span class="grow"></span>' +
        '<button class="btn sm" data-nema="' + esc(m.pantheon_ident) + '">Nijedna ne odgovara</button></div>' +
        '<div class="bd dek-red">' + m.kandidati.map(function (k) {
          return '<button class="dek-izbor" data-pot="' + esc(m.pantheon_ident) + '" data-kat="' + esc(k.katalog_id) + '">' +
            '<img src="/api/dekor/katalog/slika/' + encodeURIComponent(k.katalog_id) + '" alt="" loading="lazy">' +
            '<span class="naz">' + esc(k.naziv) + '</span><span class="note">' + esc(k.dobavljac) + (k.proizvodac ? ' · ' + esc(k.proizvodac) : "") + '</span></button>';
        }).join("") + '</div></section>';
    }).join("") || (sz.katalog ? '<div class="sazetak ok"><span class="ik">✓</span><div class="txt"><b>Nema dekora koji čekaju potvrdu.</b> <span class="note">Nove slike dolaze kad se katalog dobavljača ponovno uveze.</span></div></div>'
      : '<div class="sazetak"><span class="ik">!</span><div class="txt"><b>Katalog dobavljača još nije uvezen.</b> Kopiraj mapu <span class="mono">dekori</span> na poslužitelj Huba (npr. <span class="mono">C:\\Paneli\\dekori</span>) pa klikni <b>Uvezi katalog</b>. <span class="note">Uvoz traje nekoliko minuta: slike se umanjuju i spremaju uz bazu, a dekori se vežu na naše identе.</span></div></div>');
    ljuska({ crumb: "<b>Šifrarnik</b> · slike dekora", rail: "sifr", cls: "c1 puna dek",
      akcije: '<a class="tbtn" href="#/sifrarnik">Materijali i trake</a><a class="tbtn on" href="#/dekori">Slike dekora</a><span class="grow"></span><input id="q" class="tbtn" style="min-width:220px" placeholder="traži dekor…" value="' + esc(S.dekQ || "") + '"><button class="tbtn' + (sz.katalog ? '' : ' pri') + '" id="btnUvoz">Uvezi katalog…</button>',
      sadrzaj: '<div class="post-omot"><div class="sazetak info"><span class="ik">i</span><div class="txt"><b>' + (sz.sa_slikom || 0) + '</b> materijala ima sliku · <b>' + (sz.za_potvrdu || 0) + '</b> čeka potvrdu · katalog ' + (sz.katalog || 0) + ' dekora ' +
        '<span class="note">(' + (sz.dobavljaci || []).map(function (x) { return esc(x.dobavljac) + " " + x.n; }).join(" · ") + ')</span><br><span class="note">Klik na sliku koja odgovara dekoru upisuje je uz materijal; slike se koriste samo na internim ekranima.</span></div></div>' +
        kartice + '</div>' });
    var t; q("#q").oninput = function () { clearTimeout(t); S.dekQ = this.value; t = setTimeout(render, 300); };
    q("#btnUvoz").onclick = function () {
      dlg({ naslov: "Uvoz kataloga dobavljača", tijelo: '<div class="field"><span class="lbl">Mapa na poslužitelju Huba</span><input id="mp" value="' + esc(S.dekMapa || "C:\\Paneli\\dekori") + '"></div>' +
        '<div class="note">Mapa s katalozima (Iverpan, Elgrad, Frischeis, Blažić) i zbirnim CSV-om. Uvoz kopira slike umanjene na 640 px uz bazu Huba i veže dekore na naše identе; ponavljanje je bezopasno i ne dira potvrde ureda.</div>',
        gumbi: [{ txt: "Uvezi", pri: true, on: async function (bg, zatvori) {
          var mapa = q("#mp", bg).value.trim();
          if (!mapa) { toast("upiši mapu", true); return false; }
          S.dekMapa = mapa;
          var gumb = q(".dlg .ft .btn.pri", bg.ownerDocument || document);
          if (gumb) { gumb.disabled = true; gumb.textContent = "Uvozim…"; }
          var r = await api("/api/dekori/uvoz", { body: { mapa: mapa } });
          toast("Katalog: " + r.redaka + " dekora, " + r.slika + " slika; sa slikom odmah " + r.po_kodu + ", čeka potvrdu " + r.s_kandidatima);
          render();
        } }], nakon: function (bg) { q("#mp", bg).focus(); } });
    };
    qa("[data-pot]").forEach(function (b) { b.onclick = async function () {
      b.disabled = true;
      await api("/api/dekor/potvrdi", { body: { ident: b.dataset.pot, katalog_id: b.dataset.kat } });
      toast("Slika je spremljena"); render();
    }; });
    qa("[data-nema]").forEach(function (b) { b.onclick = async function () {
      await api("/api/dekor/odbij", { body: { ident: b.dataset.nema } }); render();
    }; });
  };

  // ---------------------------------------------------------------- ekran skladištara: QR restla, potvrde, izdavanje
  function restlRed(x) {
    return '<div class="mjera">' + mm(x.L) + ' × ' + mm(x.W) + '</div>' + (x.lokacija ? '<span class="tag">' + esc(x.lokacija) + '</span>' : '<span class="note">bez lokacije</span>');
  }
  function noviRestlDlg(nakon) {
    var mat = null;
    dlg({ naslov: "Novi restl", tijelo: '<div class="field"><span class="lbl">Materijal</span><input placeholder="dekor, ident…"><div class="lista"></div></div>' +
      '<div class="grid3"><div class="field"><span class="lbl">Duljina (mm)</span><input id="L" class="num" inputmode="numeric"></div><div class="field"><span class="lbl">Širina (mm)</span><input id="W" class="num" inputmode="numeric"></div><div class="field"><span class="lbl">Komada</span><input id="kom" class="num" value="1" inputmode="numeric"></div></div>' +
      '<div class="grid2"><div class="field"><span class="lbl">Lokacija</span><input id="lok" placeholder="A001, SATOR B 2.1…"></div><div class="field"><span class="lbl">Napomena</span><input id="nap"></div></div>' +
      '<label class="prek" style="margin-top:4px"><input type="checkbox" id="kup"><span class="kl"></span><span class="st">Kupac ga je ostavio nama</span></label>',
      gumbi: [{ txt: "Spremi", pri: true, on: async function (bg) {
        if (!mat) { toast("odaberi materijal", true); return false; }
        var L = +q("#L", bg).value, W = +q("#W", bg).value;
        if (!L || !W) { toast("upiši mjere", true); return false; }
        var r = await api("/api/skladiste/restlovi", { body: { ident: mat.ident, L: L, W: W, kom: +q("#kom", bg).value || 1, lokacija: q("#lok", bg).value.trim() || null,
          napomena: q("#nap", bg).value.trim() || null, izvor: q("#kup", bg).checked ? "kupac" : "rucno" } });
        toast("Restl " + r.oznaka + " je na stanju");
        if (nakon) nakon(r); else render();
      } }],
      nakon: function (bg) { H.pretragaLista(q(".field", bg), async function (s) { return (await api("/api/sifrarnik/materijali?q=" + encodeURIComponent(s) + "&limit=30")).materijali; },
        function (x) { return '<span class="mono">' + esc(x.ident) + '</span> ' + esc(x.naziv); }, function (x) { mat = x; }); } });
  }
  E.skladistar = async function () {
    var izd = await api("/api/skladiste/izdavanje"), pri = (await api("/api/skladiste/prijedlozi")).prijedlozi || [];
    var izdRedovi = izd.map(function (x) {
      var sto = x.restlovi.length ? x.restlovi.map(function (r) { return '<b>' + esc(r.oznaka) + '</b> ' + mm(r.L) + ' × ' + mm(r.W) + (r.lokacija ? ' <span class="tag">' + esc(r.lokacija) + '</span>' : ""); }).join("<br>")
        : '<b>' + n(x.kom, 0) + '</b> ploč' + (x.kom === 1 ? "a" : "e") + ' <span class="note">iz regala (nije u Winstoreu)</span>';
      return '<div class="skl-red">' + dslika(x.ident) + '<div class="grow"><div class="naslov">' + esc(x.naziv || x.ident || "") + '</div><div class="note">' + esc(x.ident || "") + ' · nalog ' + esc(x.nalog) + ' · ' + H.statusNaziv(x.status) + '</div><div class="sto">' + sto + '</div></div>' +
        '<button class="btn pri lg" data-izdaj="' + x.nalog_materijal_id + '">Izdano</button></div>';
    }).join("") || '<div class="note" style="padding:12px 16px">Nema ničega za izdavanje.</div>';
    var priRedovi = pri.map(function (x) {
      return '<div class="skl-red"><div class="grow"><div class="naslov">' + mm(x.L) + ' × ' + mm(x.W) + ' <span class="note">' + n(x.m2, 2) + ' m²</span></div>' +
        '<div class="note">' + esc(x.ident || "") + ' ' + esc(x.naziv_kratki || x.naziv || "") + (x.nalog ? ' · ' + esc(x.nalog) : "") + '</div>' +
        (x.napomena ? '<div class="note">' + esc(x.napomena) + '</div>' : "") + '</div>' +
        '<button class="btn pri lg" data-pot="' + x.id + '">Potvrdi</button><button class="btn lg" data-odb="' + x.id + '">Odbaci</button></div>';
    }).join("") || '<div class="note" style="padding:12px 16px">Nema prijedloga koji čekaju.</div>';
    ljuska({ crumb: "<b>Skladištar</b>", rail: "sklad", cls: "c1 puna skl",
      akcije: '<a class="tbtn" href="#/skladiste/stanje">Stanje</a><a class="tbtn" href="#/skladiste/restlovi">Restlovi</a><a class="tbtn on" href="#/skladistar">Skladištar</a><span class="grow"></span><button class="tbtn pri" id="btnNovi">+ Novi restl</button>',
      sadrzaj: '<div class="post-omot"><div class="pane pk"><div class="bd"><div class="skener"><input id="skener" placeholder="Skeniraj QR ili upiši oznaku restla (R1364)" autocomplete="off"><button class="btn pri lg" id="btnTrazi">Otvori</button></div>' +
        '<div class="note">QR s naljepnice otvara isti ekran; oznaku možeš i upisati.</div></div></div>' +
        '<section class="pane pk"><div class="hd"><b>Za izdavanje</b><span class="stat ' + (izd.length ? "warn" : "ok") + ' sm">' + izd.length + '</span><span class="grow"></span><span class="note">restlovi i materijali kojih Winstore nema</span></div><div class="bd tight">' + izdRedovi + '</div></section>' +
        '<section class="pane pk"><div class="hd"><b>Restlovi koji čekaju potvrdu</b><span class="stat ' + (pri.length ? "warn" : "ok") + ' sm">' + pri.length + '</span><span class="grow"></span><a class="btn sm" href="/api/skladiste/restlovi/naljepnice.pdf?status=prijedlog" target="_blank">Naljepnice</a></div><div class="bd tight">' + priRedovi + '</div></section></div>' });
    function otvori() {
      var v = (q("#skener").value || "").trim().toUpperCase().replace(/^.*\//, "").replace(/[^A-Z0-9]/g, "");
      if (v) idi("#/restl/" + v);
    }
    q("#btnTrazi").onclick = otvori;
    q("#skener").onkeydown = function (e) { if (e.key === "Enter") otvori(); };
    q("#skener").focus();
    q("#btnNovi").onclick = function () { noviRestlDlg(function (r) { idi("#/restl/" + r.oznaka); }); };
    qa("[data-izdaj]").forEach(function (b) { b.onclick = async function () { b.disabled = true; await api("/api/skladiste/izdaj", { body: { nm: +b.dataset.izdaj } }); toast("Izdano"); render(); }; });
    qa("[data-pot]").forEach(function (b) { b.onclick = function () { potvrdiDlg(b.dataset.pot); }; });
    qa("[data-odb]").forEach(function (b) { b.onclick = async function () { var z = prompt("Zašto se ne čuva?"); if (z === null) return; await api("/api/skladiste/restlovi/" + b.dataset.odb + "/odbaci", { body: { razlog: z } }); render(); }; });
  };
  function potvrdiDlg(id, x) {
    x = x || {};
    dlg({ naslov: "Potvrdi restl" + (x.oznaka ? " " + x.oznaka : ""), tijelo: '<div class="grid3"><div class="field"><span class="lbl">Lokacija</span><input id="lok" value="' + esc(x.lokacija || "") + '" placeholder="A001, SATOR B 2.1…"></div>' +
      '<div class="field"><span class="lbl">Duljina (mm)</span><input id="L" class="num" inputmode="numeric" value="' + (x.L || "") + '"></div><div class="field"><span class="lbl">Širina (mm)</span><input id="W" class="num" inputmode="numeric" value="' + (x.W || "") + '"></div></div>' +
      '<div class="note">Mjeru ispravi ako je drukčija nego što piše; zalijepi QR naljepnicu i potvrdi.</div>',
      gumbi: [{ txt: "Potvrdi", pri: true, on: async function (bg) {
        await api("/api/skladiste/restlovi/" + id + "/potvrdi", { body: { lokacija: q("#lok", bg).value.trim() || null, L: +q("#L", bg).value || null, W: +q("#W", bg).value || null } });
        toast("Restl je na stanju"); render();
      } }], nakon: function (bg) { q("#lok", bg).focus(); } });
  }
  E.restl = async function (r) {
    var x = await api("/api/skladiste/restl/" + encodeURIComponent(r.id || "")).catch(function () { return null; });
    if (!x) {
      ljuska({ crumb: "<b>Restl</b>", rail: "sklad", cls: "c1 puna skl", akcije: '<a class="tbtn" href="#/skladistar">← Skladištar</a>',
        sadrzaj: '<div class="post-omot"><div class="sazetak crit"><span class="ik">!</span><div class="txt"><b>Nema restla ' + esc(r.id || "") + '</b> — provjeri oznaku na naljepnici.</div></div></div>' });
      return;
    }
    var STAT = { slobodan: ["ok", "Slobodan"], rezerviran: ["warn", "Rezerviran"], prijedlog: ["warn", "Čeka potvrdu"], provjeri: ["warn", "Provjeriti"], potrosen: ["info", "Potrošen"], otpisan: ["info", "Otpisan"] };
    var st = STAT[x.status] || ["info", x.status];
    var zivi = x.status !== "potrosen" && x.status !== "otpisan";
    var red = function (k, v) { return '<div class="pf ro"><span class="opis"><span class="naz">' + k + '</span></span><div class="ctl"><span class="rov">' + v + '</span></div></div>'; };
    ljuska({ crumb: '<b>Restl</b> · ' + esc(x.oznaka), rail: "sklad", cls: "c1 puna skl",
      akcije: '<a class="tbtn" href="#/skladistar">← Skladištar</a><span class="grow"></span><a class="tbtn" href="/api/skladiste/restlovi/naljepnice.pdf?oznake=' + esc(x.oznaka) + '" target="_blank">Naljepnica</a>',
      sadrzaj: '<div class="post-omot"><section class="pane pk"><div class="hd"><b class="restl-oz">' + esc(x.oznaka) + '</b><span class="stat ' + st[0] + '">' + esc(st[1]) + '</span><span class="grow"></span>' +
        (x.provjeri ? '<span class="stat warn sm">dekor za potvrdu</span>' : "") + '</div><div class="bd">' +
        red("Materijal", dslika(x.ident, "uz-red") + (x.ident ? '<span class="mono">' + esc(x.ident) + '</span> ' : "") + esc(x.naziv_kratki || x.naziv || x.dekor_ulaz || "—")) +
        red("Mjere", '<b>' + mm(x.L) + ' × ' + mm(x.W) + '</b> mm' + (x.kom > 1 ? ' × ' + x.kom + ' kom' : "") + ' <span class="note">' + n(x.m2, 2) + ' m²</span>') +
        red("Debljina", x.debljina ? x.debljina + " mm" : '<span class="note">—</span>') +
        red("Lokacija", x.lokacija ? '<b>' + esc(x.lokacija) + '</b>' : '<span class="note">—</span>') +
        (x.napomena ? red("Napomena", esc(x.napomena)) : "") +
        (x.nalog_izlaz ? red("Potrošen u nalogu", esc(x.nalog_izlaz)) : "") +
        (x.potvrdio ? red("Potvrdio", esc(x.potvrdio) + ' <span class="note">' + esc((x.potvrdjeno || "").slice(0, 10)) + '</span>') : "") + '</div>' +
        (zivi ? '<div class="kart-akcije">' + (x.status === "prijedlog" || x.status === "provjeri" ? '<button class="btn pri lg" id="btnPot">✔ Potvrdi i zalijepi QR</button>' : "") +
          '<button class="btn lg" id="btnMjera">Ispravi mjeru</button><span class="grow"></span><button class="btn lg crit" id="btnOtpis">Otpiši</button></div>' : "") + '</section></div>' });
    if (q("#btnPot")) q("#btnPot").onclick = function () { potvrdiDlg(x.id, x); };
    if (q("#btnMjera")) q("#btnMjera").onclick = function () { potvrdiDlg(x.id, x); };
    if (q("#btnOtpis")) q("#btnOtpis").onclick = async function () {
      var z = prompt("Razlog otpisa (potrošen, uništen, nema ga…)");
      if (z === null) return;
      await api("/api/skladiste/restlovi/" + x.id + "/odbaci", { body: { razlog: z } });
      toast("Otpisano"); idi("#/skladistar");
    };
  };

  // ---------------------------------------------------------------- ekran 6: nabava
  E.nabava = async function (r) {
    var pod = r.id || "potrebe";
    var akcije = '<a class="tbtn' + (pod === "potrebe" ? " on" : "") + '" href="#/nabava/potrebe">Potrebe</a><a class="tbtn' + (pod === "narudzbenice" ? " on" : "") + '" href="#/nabava/narudzbenice">Narudžbenice</a><a class="tbtn' + (pod === "dobavljaci" ? " on" : "") + '" href="#/nabava/dobavljaci">Dobavljači</a>';
    if (pod === "narudzbenice" || /^\d+$/.test(pod)) {
      if (/^\d+$/.test(pod)) return narudzbenica(+pod, akcije);
      var lst = await api("/api/nabava/narudzbenice");
      var rows = lst.map(function (x) { return '<tr class="klik" data-n="' + x.id + '"><td class="mono">' + esc(x.broj) + '</td><td>' + esc(x.dobavljac) + '</td><td>' + esc(x.datum) + '</td><td><span class="tag ' + (x.status === "zaprimljena" ? "ok" : x.status === "nacrt" ? "info" : x.status === "ponistena" ? "" : "warn") + '">' + esc(x.status) + '</span></td><td class="r num">' + x.stavki + '</td><td class="r num">' + n(x.otvoreno, 1) + '</td><td class="note">' + esc(x.poslano_na || "") + '</td></tr>'; }).join("");
      ljuska({ crumb: "<b>Nabava</b> · narudžbenice", rail: "nabava", cls: "c1", akcije: akcije + '<button class="tbtn" id="btnPrimka">eSlog primka</button><button class="tbtn pri" id="btnNova">+ Ručna narudžbenica</button>',
        sadrzaj: '<div class="pane"><div class="hd"><b>Narudžbenice</b></div><div class="bd tight"><table><thead><tr><th>Broj</th><th>Dobavljač</th><th>Datum</th><th>Status</th><th class="r">Stavki</th><th class="r">Otvoreno</th><th>Poslano na</th></tr></thead><tbody>' + (rows || '<tr><td colspan="7" class="note">nema narudžbenica</td></tr>') + '</tbody></table></div></div>', foot: kpi(lst.length, "narudžbenica") + kpi(lst.filter(function (x) { return x.status === "poslana" || x.status === "djelomicno"; }).length, "otvorenih") });
      qa("tr[data-n]").forEach(function (x) { x.onclick = function () { idi("#/nabava/" + x.dataset.n); }; });
      q("#btnPrimka").onclick = function () { dlg({ naslov: "eSlog primka → zatvaranje narudžbenica", tijelo: '<div class="field"><span class="lbl">Putanja eSlog XML-a na poslužitelju</span><input id="p" placeholder="C:\\…\\eslog_uvoz\\primka.xml"></div><div class="note">Stavke se spajaju po našem broju narudžbe (ako ga dobavljač vrati) ili po dobavljaču i identu redom; m² s računa → ploče.</div>', gumbi: [{ txt: "Učitaj", pri: true, on: async function (bg) { var rr = await api("/api/nabava/primka", { body: { putanja: q("#p", bg).value } }); toast("Primka " + rr.racun + ": spojeno " + rr.spojeno.length + ", nespojeno " + rr.nespojeno.length, rr.nespojeno.length > 0); render(); } }] }); };
      q("#btnNova").onclick = async function () { var dob = await api("/api/nabava/dobavljaci"); dlg({ naslov: "Ručna narudžbenica", tijelo: '<div class="field"><span class="lbl">Dobavljač</span><select id="dob">' + dob.map(function (x) { return '<option>' + esc(x.naziv) + '</option>'; }).join("") + '</select></div><div class="field"><span class="lbl">Napomena</span><input id="nap"></div>', gumbi: [{ txt: "Otvori nacrt", pri: true, on: async function (bg) { var rr = await api("/api/nabava/narudzbenice", { body: { dobavljac: q("#dob", bg).value, napomena: q("#nap", bg).value || null } }); idi("#/nabava/" + rr.id); } }] }); };
      return;
    }
    if (pod === "dobavljaci") {
      var dob = await api("/api/nabava/dobavljaci");
      ljuska({ crumb: "<b>Nabava</b> · dobavljači", rail: "nabava", cls: "c1", akcije: akcije,
        sadrzaj: '<div class="pane"><div class="hd"><b>Dobavljači</b><span class="note">iz Pantheona (po identima) — e-mail za narudžbe upisuje se ovdje</span></div><div class="bd tight"><table><thead><tr><th>Dobavljač</th><th class="r">Identa</th><th>E-mail za narudžbe</th><th>Kontakt</th><th></th></tr></thead><tbody>' + dob.map(function (x) { return '<tr><td><b>' + esc(x.naziv) + '</b></td><td class="r num">' + (x.identa || 0) + '</td><td>' + esc(x.email || "—") + '</td><td>' + esc(x.kontakt || "") + '</td><td class="r"><button class="btn sm" data-dob="' + esc(x.naziv) + '" data-mail="' + esc(x.email || "") + '" data-kontakt="' + esc(x.kontakt || "") + '">Uredi</button></td></tr>'; }).join("") + '</tbody></table></div></div>', foot: kpi(dob.length, "dobavljača") + kpi(dob.filter(function (x) { return x.email; }).length, "s e-mailom") });
      qa("[data-dob]").forEach(function (b) { b.onclick = function () { dlg({ naslov: b.dataset.dob, tijelo: '<div class="grid2"><div class="field"><span class="lbl">E-mail za narudžbe</span><input id="m" value="' + esc(b.dataset.mail) + '"></div><div class="field"><span class="lbl">Kontakt</span><input id="k" value="' + esc(b.dataset.kontakt) + '"></div></div>', gumbi: [{ txt: "Spremi", pri: true, on: async function (bg) { await api("/api/nabava/dobavljaci", { body: { naziv: b.dataset.dob, email: q("#m", bg).value || null, kontakt: q("#k", bg).value || null } }); render(); } }] }); }; });
      return;
    }
    var u = await api("/api/skladiste/potrebe");
    var mats = u.materijali.map(function (m) { return '<tr><td class="mono">' + esc(m.ident) + '</td><td>' + esc(m.naziv) + '<div class="note">' + m.nalozi.map(function (x) { return esc(x.nalog) + (x.ploce != null ? " " + x.ploce : x.na_restlu ? " restl" : " ?"); }).join(" · ") + '</div></td><td class="r num">' + m.potrebno + '</td><td class="r num">' + n(m.fizicko, 0) + '</td><td class="r num">' + n(m.rezervirano, 0) + '</td><td class="r num">' + n(m.naruceno, 0) + '</td><td class="r num">' + (m.manjak ? '<b class="crit-t">' + m.manjak + '</b>' : '<span class="ok-t">0</span>') + '</td><td class="r num">' + (m.restlovi_kom ? m.restlovi_kom + ' / ' + n(m.restlovi_m2, 1) : "—") + '</td></tr>'; }).join("");
    var trake = u.trake.map(function (t) { return '<tr><td class="mono">' + esc(t.ident) + '</td><td>' + esc(t.naziv || "") + '<div class="note">' + t.nalozi.map(function (x) { return esc(x.nalog) + " " + x.metri + " m"; }).join(" · ") + '</div></td><td class="r num">' + t.potrebno + ' m</td><td class="r num">' + (t.na_roli == null ? '<span class="note">?</span>' : n(t.na_roli, 1)) + '</td><td>' + esc(t.pretinac || "") + '</td><td class="r num">' + (t.manjak ? '<b class="crit-t">' + n(t.manjak, 1) + ' m</b>' : (t.manjak === 0 ? '<span class="ok-t">0</span>' : "")) + '</td></tr>'; }).join("");
    ljuska({ crumb: "<b>Nabava</b> · potrebe", rail: "nabava", cls: "c1", akcije: akcije + '<button class="tbtn pri" id="btnIzPotreba">Narudžbenice iz potreba</button>',
      sadrzaj: '<div class="pane"><div class="hd"><b>Ploče — potreba preko svih potvrđenih naloga</b><span class="note">manjak = Σ potrebno − fizičko − naručeno</span></div><div class="bd tight">' + (u.nepoznato.length ? '<div class="upoz">Nepoznata potreba (optimizacija nije potvrđena): ' + u.nepoznato.map(function (x) { return esc(x.nalog) + " / " + esc(x.materijal); }).join("; ") + '</div>' : "") + '<table><thead><tr><th>Ident</th><th>Materijal · nalozi</th><th class="r">Potrebno</th><th class="r">Fizičko</th><th class="r">Rezerv.</th><th class="r">Naručeno</th><th class="r">Manjak</th><th class="r">Restlovi</th></tr></thead><tbody>' + (mats || '<tr><td colspan="8" class="note">nema potvrđenih naloga</td></tr>') + '</tbody></table></div></div>' +
        '<div class="pane"><div class="hd"><b>Trake — Σ metara vs rola (Regal traka)</b></div><div class="bd tight"><table><thead><tr><th>Ident</th><th>Traka · nalozi</th><th class="r">Potrebno</th><th class="r">Na roli</th><th>Pretinac</th><th class="r">Manjak</th></tr></thead><tbody>' + (trake || '<tr><td colspan="6" class="note">—</td></tr>') + '</tbody></table></div></div>',
      foot: kpi(u.materijali.length, "materijala") + kpi(u.za_nabavu.filter(function (z) { return z.jm === "PLOČA"; }).reduce(function (a, z) { return a + z.kom; }, 0), "ploča za naručiti") + kpi(u.za_nabavu.filter(function (z) { return z.jm === "M"; }).length, "traka s manjkom") + kpi(u.nepoznato.length, "nepoznato") });
    q("#btnIzPotreba").onclick = async function () { var ns = await api("/api/nabava/narudzbenice", { body: { iz_potreba: true } }); if (!ns.length) { toast("nema manjka — nema što naručiti"); return; } toast(ns.length + " nacrt(a): " + ns.map(function (x) { return x.broj + " " + x.dobavljac; }).join(", ")); idi("#/nabava/" + ns[0].id); };
  };
  async function narudzbenica(nid, akcije) {
    var d = await api("/api/nabava/narudzbenica/" + nid), nacrt = d.status === "nacrt";
    var rows = d.stavke.map(function (s) { return '<tr><td class="mono">' + esc(s.pantheon_ident) + '</td><td>' + esc(s.naziv || "") + (s.nalog ? '<div class="note">' + esc(s.nalog) + '</div>' : "") + '</td><td>' + esc(s.dimenzija || "") + '</td><td class="r num">' + (nacrt ? '<input value="' + s.kom + '" data-kom="' + s.id + '" style="width:70px;text-align:right">' : n(s.kom, 1)) + '</td><td>' + esc(s.jm || "") + '</td><td class="r num">' + n(s.zaprimljeno_kom, 1) + '</td><td class="r num">' + n(s.otvoreno, 1) + '</td><td class="note">' + esc(s.primka_ref || "") + '</td><td class="r">' + (nacrt ? '<button class="btn sm" data-brisi="' + s.id + '">×</button>' : "") + '</td></tr>'; }).join("");
    ljuska({ crumb: 'Nabava / <b>' + esc(d.broj) + '</b> · ' + esc(d.dobavljac) + ' · ' + esc(d.datum), rail: "nabava", cls: "c1",
      akcije: akcije + (nacrt ? '<button class="tbtn" id="btnStavka">+ Stavka</button><button class="tbtn pri" id="btnPosalji">Pošalji dobavljaču</button>' : "") + (d.status === "poslana" || d.status === "djelomicno" ? '<button class="tbtn pri" id="btnZaprimi">Zaprimi</button>' : "") + (d.put_pdf ? '<a class="tbtn" href="/api/nabava/narudzbenica/' + d.id + '/pdf" target="_blank">PDF</a>' : "") + (d.status !== "zaprimljena" && d.status !== "ponistena" ? '<button class="tbtn" id="btnPonisti">Poništi</button>' : ""),
      sadrzaj: '<div class="pane"><div class="hd"><b>' + esc(d.broj) + '</b><span class="tag ' + (d.status === "zaprimljena" ? "ok" : nacrt ? "info" : "warn") + '">' + esc(d.status) + '</span><span class="note">' + esc(d.dobavljac) + (d.email ? " · " + esc(d.email) : " · <span class='warn-t'>bez e-maila (Nabava → Dobavljači)</span>") + (d.poslano_kada ? " · poslano " + esc(d.poslano_kada.slice(0, 16).replace("T", " ")) + " na " + esc(d.poslano_na || "") : "") + '</span></div>' +
        '<div class="bd tight"><table><thead><tr><th>Ident</th><th>Naziv</th><th>Dimenzija</th><th class="r">Količina</th><th>JM</th><th class="r">Zaprimljeno</th><th class="r">Otvoreno</th><th>Primka</th><th></th></tr></thead><tbody>' + (rows || '<tr><td colspan="9" class="note">nema stavki</td></tr>') + '</tbody></table>' + (d.napomena ? '<div class="note" style="padding:8px 12px">' + esc(d.napomena) + '</div>' : "") + '</div></div>',
      foot: kpi(d.stavke.length, "stavki") + kpi(n(d.stavke.reduce(function (a, s) { return a + s.otvoreno; }, 0), 1), "otvoreno") });
    qa("[data-kom]").forEach(function (i) { i.onchange = async function () { await api("/api/nabava/stavka/" + i.dataset.kom, { method: "PUT", body: { kom: +i.value } }); render(); }; });
    qa("[data-brisi]").forEach(function (b) { b.onclick = async function () { await api("/api/nabava/stavka/" + b.dataset.brisi, { method: "DELETE" }); render(); }; });
    if (q("#btnStavka")) q("#btnStavka").onclick = function () { var mat = null; dlg({ naslov: "Stavka narudžbenice", tijelo: '<div class="field"><span class="lbl">Materijal / ident</span><input placeholder="dekor, ident…"><div class="lista"></div></div><div id="odm" class="note">—</div><div class="grid2"><div class="field"><span class="lbl">Količina</span><input id="kom" value="1"></div><div class="field"><span class="lbl">JM</span><select id="jm"><option>PLOČA</option><option>M</option><option>KOM</option><option>M2</option></select></div></div>', gumbi: [{ txt: "Dodaj", pri: true, on: async function (bg) { if (!mat) { toast("odaberi materijal", true); return false; } await api("/api/nabava/narudzbenica/" + d.id + "/stavke", { body: { ident: mat.ident, kom: +q("#kom", bg).value, jm: q("#jm", bg).value } }); render(); } }],
      nakon: function (bg) { H.pretragaLista(q(".field", bg), async function (s) { var m = (await api("/api/sifrarnik/materijali?q=" + encodeURIComponent(s) + "&limit=20")).materijali, t = (await api("/api/sifrarnik/trake?q=" + encodeURIComponent(s) + "&limit=20")); return m.concat(t.trake || t); }, function (x) { return '<span class="mono">' + esc(x.ident) + '</span> ' + esc(x.naziv); }, function (x) { mat = x; q("#odm", bg).innerHTML = "<b>" + esc(x.ident) + "</b> " + esc(x.naziv); if (/^TR/.test(x.ident)) q("#jm", bg).value = "M"; }); } }); };
    if (q("#btnPosalji")) q("#btnPosalji").onclick = async function () { var pot = await potpis(); dlg({ naslov: "Pošalji narudžbu " + d.broj, tijelo: '<div class="field"><span class="lbl">Na adresu</span><input id="na" value="' + esc(d.email || "") + '"></div><div class="field"><span class="lbl">Tekst</span><textarea id="t" rows="4">Poštovani,\n\nu prilogu je narudžba ' + esc(d.broj) + '. Molimo potvrdu roka isporuke.\n\nLijep pozdrav,\n' + esc(pot) + '</textarea></div><label class="note"><input type="checkbox" id="suho"> samo PDF, ne šalji</label>', gumbi: [{ txt: "Pošalji", pri: true, on: async function (bg) { var rr = await api("/api/nabava/narudzbenica/" + d.id + "/posalji", { body: { na: q("#na", bg).value || null, tekst: q("#t", bg).value, suho: q("#suho", bg).checked } }); toast(rr.status === "poslana" ? "Poslano na " + rr.poslano_na : "PDF pripremljen"); render(); } }] }); };
    if (q("#btnZaprimi")) q("#btnZaprimi").onclick = function () { dlg({ naslov: "Ručna primka", tijelo: '<div class="field"><span class="lbl">Otpremnica / račun</span><input id="ref"></div>' + d.stavke.map(function (s) { return '<div class="row"><span class="mono" style="width:90px">' + esc(s.pantheon_ident) + '</span><span class="grow">' + esc((s.naziv || "").slice(0, 40)) + ' <span class="note">otvoreno ' + n(s.otvoreno, 1) + ' ' + esc(s.jm) + '</span></span><input data-z="' + esc(s.pantheon_ident) + '" value="' + s.otvoreno + '" style="width:80px;text-align:right"></div>'; }).join(""), gumbi: [{ txt: "Zaprimi", pri: true, on: async function (bg) { var st = {}; qa("[data-z]", bg).forEach(function (i) { if (+i.value > 0) st[i.dataset.z] = +i.value; }); var rr = await api("/api/nabava/narudzbenica/" + d.id + "/zaprimi", { body: { stavke: st, ref: q("#ref", bg).value || null } }); if (rr.upozorenja && rr.upozorenja.length) toast(rr.upozorenja.join("; "), true); render(); } }] }); };
    if (q("#btnPonisti")) q("#btnPonisti").onclick = async function () { var z = prompt("Razlog poništenja"); if (z === null) return; await api("/api/nabava/narudzbenica/" + d.id + "/ponisti", { body: { razlog: z } }); render(); };
  }

  // ---------------------------------------------------------------- šifrarnik (pretraga, aliasi) i postavke
  E.sifrarnik = async function () {
    var s = S.sifQ || "", vr = S.sifVrsta || "materijali";
    var r = s ? await api((vr === "trake" ? "/api/sifrarnik/trake?q=" : "/api/sifrarnik/materijali?q=") + encodeURIComponent(s) + "&limit=100") : { materijali: [], trake: [] };
    var lst = r.materijali || r.trake || r;
    var rows = lst.map(function (x) { return '<tr><td class="dst">' + (vr === "trake" ? "" : dslika(x.ident)) + '</td><td class="mono">' + esc(x.ident) + '</td><td>' + esc(x.naziv) + '</td><td>' + esc(x.naziv_kratki || x.klasa || "") + '</td><td class="r">' + (x.debljina ? x.debljina + " mm" : "") + '</td><td>' + esc(x.winstore_kod || x.dekor || "") + '</td><td class="r">' + (x.stanje_kom != null ? x.stanje_kom : "") + '</td><td>' + (x.pogodak ? '<span class="tag info">' + esc(x.pogodak) + '</span>' : "") + '</td></tr>'; }).join("");
    ljuska({ crumb: "<b>Šifrarnik</b>", rail: "sifr", cls: "c1",
      sadrzaj: '<div class="pane"><div class="hd"><span class="chip' + (vr === "materijali" ? " on" : "") + '" data-v="materijali">Materijali</span><span class="chip' + (vr === "trake" ? " on" : "") + '" data-v="trake">Trake</span><a class="chip" href="#/dekori">Slike dekora</a><span class="grow"></span><input id="q" placeholder="naziv, ident, Winstore kod, tekst iz naloga…" value="' + esc(s) + '" style="width:340px"></div>' +
        '<div class="bd tight"><table><thead><tr><th></th><th>Ident</th><th>Naziv</th><th>Kratki / klasa</th><th class="r">Debljina</th><th>Winstore / dekor</th><th class="r">Stanje</th><th></th></tr></thead><tbody>' + (rows || '<tr><td colspan="8" class="note">upiši pojam za pretragu</td></tr>') + '</tbody></table></div></div>', foot: kpi(lst.length, "pogodaka") + '<span class="note">Šifrarnik se puni dnevnim uvozom iz Pantheona i Winstorea; ispravci ureda (debljina, „ne koristi se“, veza koda) žive u Hubu.</span>' });
    qa("[data-v]").forEach(function (c) { c.onclick = function () { S.sifVrsta = c.dataset.v; render(); }; });
    var t; q("#q").oninput = function () { clearTimeout(t); S.sifQ = this.value; t = setTimeout(render, 250); }; q("#q").focus();
  };
  // ---------------------------------------------------------------- Postavke (stil 1A + 2A + 3A, Igor 17. 9.): cjeline, jedinice uz unos, prekidači, Spremi ispod polja
  var ULOGE = { ured: "Ured", nabava: "Nabava", voditelj: "Voditelj", admin: "Administrator", sustav: "Sustav" };
  E.postavke = async function () {
    var p0 = await api("/api/postavke/optimizacija"), m = await api("/api/mail/postavke").catch(function () { return {}; });
    var tv = await api("/api/postavke/tvrtka").catch(function () { return null; });
    var p = {}; (Array.isArray(p0) ? p0 : Object.keys(p0).map(function (k) { return { kljuc: k, vrijednost: p0[k] }; })).forEach(function (x) { p[x.kljuc] = x.vrijednost; });
    var ja = (await H.ucitajJa()) || {}, admin = !ja.prijava_obavezna || (ja.korisnik && ja.korisnik.uloga === "admin");
    var korisnici = admin ? await api("/api/korisnici").catch(function () { return []; }) : (ja.korisnik ? [ja.korisnik] : []);
    var v = function (k, izvor) { var x = (izvor || p)[k]; return x == null ? "" : String(x); };

    // polje: [ključ, naziv, pomoć, vrsta, dodatno] — vrsta: broj (s jedinicom) | tekst | izbor | prekidac
    function polje(k, naziv, pomoc, vrsta, o, izvor) {
      o = o || {}; var val = v(k, izvor), grupa = izvor === tv ? "t" : "o", ctl;
      var atr = ' data-k="' + k + '" data-g="' + grupa + '" id="pf-' + k + '"';
      if (vrsta === "izbor") {
        var opc = o.opcije.slice(); if (val && !opc.some(function (x) { return x[0] === val; })) opc.push([val, val]);
        ctl = '<select' + atr + ' class="w-' + (o.w || "m") + '">' + opc.map(function (x) { return '<option value="' + esc(x[0]) + '"' + (x[0] === val ? " selected" : "") + '>' + esc(x[1]) + '</option>'; }).join("") + '</select>';
      } else if (vrsta === "prekidac") {
        ctl = '<label class="prek"><input type="checkbox"' + atr + (val === "1" ? " checked" : "") + '><span class="kl"></span><span class="st">' + (val === "1" ? "Uključeno" : "Isključeno") + '</span></label>';
      } else {
        var inp = '<input' + atr + ' class="w-' + (o.w || (o.jed ? "s" : "m")) + (vrsta === "broj" ? " num" : "") + (o.mono ? " mono" : "") + '" value="' + esc(val) + '"' + (vrsta === "broj" ? ' inputmode="decimal"' : "") + (o.ph ? ' placeholder="' + esc(o.ph) + '"' : "") + ' autocomplete="off">';
        ctl = o.jed ? '<span class="jed">' + inp + '<span>' + esc(o.jed) + '</span></span>' : inp;
      }
      return '<div class="pf" data-pf="' + k + '"><label class="opis" for="pf-' + k + '"><span class="naz">' + esc(naziv) + '</span>' + (pomoc ? '<span class="pom">' + esc(pomoc) + '</span>' : "") + '<span class="gr" data-gr="' + k + '"></span></label><div class="ctl">' + ctl + '</div></div>';
    }
    function karta(naslov, desno, tijelo, cls) { return '<section class="pane pk' + (cls ? " " + cls : "") + '"><div class="hd"><b>' + naslov + '</b><span class="grow"></span>' + (desno || "") + '</div><div class="bd">' + tijelo + '</div></section>'; }
    function ro(naziv, val, mono) { return '<div class="pf ro"><span class="opis"><span class="naz">' + esc(naziv) + '</span></span><div class="ctl"><span class="rov' + (mono ? " mono" : "") + '">' + (val === "" || val == null ? '<span class="note">—</span>' : esc(val)) + '</span></div></div>'; }

    var obracun = karta("Obračun", "", polje("kerf", "Kerf za naplatu", "širina reza u obračunu korisnog ostatka ploče", "broj", { jed: "mm" }) +
      polje("nadmjera_trake", "Nadmjera trake", "dodatak na zbroj kantiranih stranica", "broj", { jed: "%" }) +
      polje("obracun_rezanja", "Obračun rezanja", "kako se usluga rezanja naplaćuje na ponudi", "izbor", { opcije: [["m2", "Po m² ploče"], ["rezova", "Po broju rezova"], ["m_reza", "Po dužnom metru reza"]] }) +
      polje("ident_rezanje_rez", "Usluga po rezu", "Pantheon ident usluge kad se reže po broju rezova", "tekst", { mono: true, ph: "npr. US000303" }) +
      polje("ident_rezanje_m", "Usluga po dužnom metru", "Pantheon ident; prazno dok se usluga ne otvori", "tekst", { mono: true, ph: "nije otvorena" }) +
      '<div class="info-red"><span class="ik">i</span>Svaka ponuda čuva snimku obračunskih vrijednosti.</div>');
    var pila = karta("Pravila pile", "", polje("kerf_pile", "Fizički kerf pile", "širina lista pile za optimizaciju i program pile", "broj", { jed: "mm" }) +
      polje("pila_max_razina", "Najviše razina rezanja", "traka → poprečni rez → pod-traka → komad", "izbor", { w: "s", opcije: [["2", "2 razine"], ["3", "3 razine"], ["4", "4 razine"]] }) +
      polje("pila_max_sirina_u_traci", "Najviše različitih širina u traci", "0 = bez ograničenja", "broj", { w: "s" }) +
      polje("pila_min_komad_4", "Najmanji komad 4. razine", "0 = bez ograničenja", "broj", { jed: "mm" }) +
      polje("pila_mijesana_orijentacija", "Miješana orijentacija", "isti element smije biti složen u oba smjera na ploči", "prekidac"));
    var restl = karta("Restlovi", "", polje("restl_min_m2", "Najmanja površina restla", "manji ostatak ne ide u regal", "broj", { jed: "m²" }) +
      polje("restl_traka_mm", "Traka se čuva od duljine", "duga traka čuva se i kad je ispod te površine", "broj", { jed: "mm" }) +
      polje("restl_min_mm", "Najmanja kraća stranica", "uži komad se ne čuva", "broj", { jed: "mm" }) +
      '<div class="info-red"><span class="ik">i</span>Naplata kupcu se ne mijenja: ne naplaćuje se ostatak od 400 mm i 1 m². Komad ispod toga kupac plaća, a mi ga zadržimo u regalu.</div>');
    var mape = karta("Mape izvoza", "", polje("mapa_nesting", "Nesting (bNest)", "mapa za program nesting stroja", "tekst", { w: "l", mono: true }) +
      polje("mapa_pila", "Pila (OSI)", "mapa za program pile", "tekst", { w: "l", mono: true }));
    var poznato = ["smtp_host", "smtp_port", "mail_od", "mail_od_naziv", "smtp_user", "mail_kopija", "lozinka_datoteka", "spreman"];
    var mail = karta("E-pošta", Object.keys(m).length ? (m.spreman ? '<span class="stat ok sm"><i>✓</i> Konfigurirano</span>' : '<span class="stat warn sm"><i>!</i> Lozinka nije postavljena</span>') : '<span class="stat info sm">Nije dostupno</span>',
      ro("Poslužitelj", m.smtp_host, true) + ro("Port", m.smtp_port, true) + ro("Pošiljatelj", m.mail_od) + ro("Naziv pošiljatelja", m.mail_od_naziv) +
      '<details class="napredno"><summary>Napredni podaci</summary>' + ro("Korisničko ime", m.smtp_user) + ro("Kopija svake poruke", m.mail_kopija) + ro("Datoteka s lozinkom", m.lozinka_datoteka, true) +
      ro("Lozinka", m.spreman ? "postavljena" : "nije postavljena") + Object.keys(m).filter(function (k) { return poznato.indexOf(k) < 0; }).map(function (k) { return ro(k, typeof m[k] === "object" ? JSON.stringify(m[k]) : m[k]); }).join("") +
      '<div class="note">Podatke e-pošte i lozinku mijenja administrator na poslužitelju Huba.</div></details>', "mail");
    var tvrtka = tv ? karta("Podaci tvrtke", '<span class="note">na ponudi, narudžbenici i u potpisu e-pošte</span>', '<div class="pk-2">' +
      polje("tvrtka_naziv", "Naziv tvrtke", "", "tekst", { w: "l" }, tv) + polje("tvrtka_adresa", "Adresa", "", "tekst", { w: "l" }, tv) +
      polje("tvrtka_oib", "OIB", "11 znamenki", "tekst", { mono: true, ph: "00000000000" }, tv) + polje("tvrtka_iban", "IBAN", "", "tekst", { w: "l", mono: true, ph: "HR…" }, tv) +
      polje("tvrtka_tel", "Telefon", "", "tekst", {}, tv) + polje("tvrtka_mail", "E-mail", "", "tekst", { w: "l" }, tv) + polje("tvrtka_web", "Web", "", "tekst", {}, tv) + '</div>', "puna") : "";

    var loz0 = korisnici.some(function (k) { return k.ima_lozinku; });
    var korRed = korisnici.map(function (k) {
      var smije = admin || k.oznaka === S.korisnik;
      return '<tr' + (k.aktivan === 0 ? ' class="neakt"' : "") + '><td><span class="koz mono">' + esc(k.oznaka) + '</span></td><td><b>' + esc(k.ime || "") + '</b>' + (k.funkcija ? '<div class="note">' + esc(k.funkcija) + '</div>' : "") + (k.aktivan === 0 ? ' <span class="stat info sm">neaktivan</span>' : "") + '</td>' +
        '<td>' + esc(ULOGE[k.uloga] || k.uloga || "") + '</td><td class="kontakt">' + (k.email ? '<div>' + esc(k.email) + '</div>' : "") + (k.telefon ? '<div class="note">' + esc(k.telefon) + '</div>' : "") + (!k.email && !k.telefon ? '<span class="note">—</span>' : "") + '</td>' +
        '<td>' + (k.ima_lozinku ? '<span class="stat ok sm"><i>✓</i> Postavljena</span>' : '<span class="stat warn sm">Nije postavljena</span>') + '</td>' +
        '<td class="r akc">' + (smije ? '<button class="btn sm" data-kor="' + esc(k.oznaka) + '">Uredi</button><button class="btn sm" data-loz="' + esc(k.oznaka) + '">' + (k.ima_lozinku ? "Promijeni lozinku" : "Postavi lozinku") + '</button>' : "") + '</td></tr>';
    }).join("") || '<tr><td colspan="6" class="note">popis korisnika vidi samo administrator</td></tr>';
    var kor = '<section class="pane pk puna"><div class="hd"><b>Korisnici i prijava</b><span class="grow"></span>' + (admin ? '<button class="btn sm" id="btnNoviKor">+ Novi korisnik</button>' : "") + '</div><div class="bd tight">' +
      (ja.prijava_obavezna ? '<div class="info-red"><span class="ik">i</span>Prijava s lozinkom je obavezna za sve korisnike.</div>'
        : '<div class="sazetak"><span class="ik">!</span><span class="txt"><b>Prijava nije obavezna.</b> Aktivira se postavljanjem prve lozinke' + (loz0 ? "" : " — nijedan korisnik još nema lozinku") + '.</span></div>') +
      '<table class="kor-t"><thead><tr><th>Oznaka</th><th>Korisnik</th><th>Uloga</th><th>E-mail / telefon</th><th>Lozinka</th><th class="r">Akcije</th></tr></thead><tbody>' + korRed + '</tbody></table>' +
      '<div class="kor-foot"><span>Prijavljeni korisnik: <b>' + esc(S.korisnik) + '</b></span>' + (ja.potpis ? '<span class="note" title="potpis u e-pošti">potpis: ' + esc(ja.potpis).replace(/\n/g, " · ") + '</span>' : "") + '<span class="grow"></span>' +
      (ja.prijava_obavezna ? '<button class="btn sm" id="btnOdjava">Odjava</button>' : '<button class="btn sm" id="btnKor">Promijeni korisnika</button>') + '</div></div></section>';

    ljuska({ crumb: "<b>Postavke</b>", rail: "post", cls: "c1 puna post",
      sadrzaj: '<div class="post-omot"><div class="post-nasl"><h1>Postavke</h1><span>Optimizacija, obračun, izvoz i korisnici</span></div>' +
        '<div class="pk-grid">' + obracun + pila + restl + mape + mail + tvrtka + '</div>' +
        '<div class="spremi-traka"><span class="stanje" id="spStanje"><span class="note">Nema nespremljenih promjena</span></span><span class="grow"></span><button class="btn" id="btnOdustani" disabled>Odustani</button><button class="btn pri" id="btnSpremi" disabled>Spremi postavke</button></div>' +
        kor + '</div>' });

    // praćenje promjena: gumbi rade samo kad nešto nije spremljeno
    var pocetno = {};
    function vrijednost(el) { return el.type === "checkbox" ? (el.checked ? "1" : "0") : el.value; }
    function greska(el) {
      var k = el.dataset.k, x = vrijednost(el).trim();
      if (["kerf", "kerf_pile", "nadmjera_trake", "pila_min_komad_4"].indexOf(k) >= 0 && (x === "" || isNaN(+x.replace(",", ".")))) return "upiši broj";
      if (k === "pila_max_sirina_u_traci" && !/^\d+$/.test(x)) return "cijeli broj, 0 = bez ograničenja";
      if (k === "tvrtka_oib" && x && !/^\d{11}$/.test(x)) return "OIB ima 11 znamenki";
      return "";
    }
    function osvjezi(spremljeno) {
      var n = 0, gr = 0;
      qa("[data-k]").forEach(function (el) {
        var prom = vrijednost(el) !== pocetno[el.dataset.k], g = greska(el), red = el.closest(".pf");
        if (prom) n++; if (g) gr++;
        red.classList.toggle("prom", prom); red.classList.toggle("gres", !!g);
        q('[data-gr="' + el.dataset.k + '"]').textContent = g;
        if (el.type === "checkbox") q(".st", el.parentNode).textContent = el.checked ? "Uključeno" : "Isključeno";
      });
      q("#btnSpremi").disabled = !n || gr > 0; q("#btnOdustani").disabled = !n;
      q("#spStanje").innerHTML = gr ? '<span class="stat crit sm"><i>!</i> Ispravi označena polja</span>' : n ? '<span class="stat warn sm">' + n + (n === 1 ? " nespremljena promjena" : n < 5 ? " nespremljene promjene" : " nespremljenih promjena") + '</span>'
        : spremljeno ? '<span class="stat ok sm"><i>✓</i> Postavke su spremljene</span>' : '<span class="note">Nema nespremljenih promjena</span>';
    }
    qa("[data-k]").forEach(function (el) { pocetno[el.dataset.k] = vrijednost(el); el.addEventListener(el.tagName === "INPUT" && el.type !== "checkbox" ? "input" : "change", function () { osvjezi(); }); });
    q("#btnOdustani").onclick = function () {
      qa("[data-k]").forEach(function (el) { if (el.type === "checkbox") el.checked = pocetno[el.dataset.k] === "1"; else el.value = pocetno[el.dataset.k]; });
      osvjezi();
    };
    q("#btnSpremi").onclick = async function () {
      var b = { o: {}, t: {} }, btn = this;
      qa("[data-k]").forEach(function (el) { var x = vrijednost(el); if (x !== pocetno[el.dataset.k]) b[el.dataset.g][el.dataset.k] = el.type === "checkbox" ? x : x.trim(); });
      btn.disabled = true; btn.textContent = "Spremam…";
      try {
        var novo = Object.keys(b.o).length ? await api("/api/postavke/optimizacija", { body: Object.assign({ tko: S.korisnik }, b.o) }) : null;
        var novoT = Object.keys(b.t).length ? await api("/api/postavke/tvrtka", { body: Object.assign({ tko: S.korisnik }, b.t) }) : null;
        (novo || []).forEach(function (x) { var el = q('[data-k="' + x.kljuc + '"]'); if (el && el.type !== "checkbox") el.value = x.vrijednost == null ? "" : x.vrijednost; });
        if (novoT) Object.keys(novoT).forEach(function (k) { var el = q('[data-k="' + k + '"]'); if (el) el.value = novoT[k]; });
        qa("[data-k]").forEach(function (el) { pocetno[el.dataset.k] = vrijednost(el); });
        btn.textContent = "Spremi postavke"; osvjezi(true); toast("Postavke su spremljene");
      } catch (e) { btn.textContent = "Spremi postavke"; osvjezi(); q("#spStanje").innerHTML = '<span class="stat crit sm"><i>!</i> ' + esc(e.message || "spremanje nije uspjelo") + '</span>'; }
    };
    osvjezi();

    if (q("#btnKor")) q("#btnKor").onclick = function () { q("#korisnik").click(); };
    if (q("#btnOdjava")) q("#btnOdjava").onclick = function () { q("#korisnik").click(); };
    function urediKorisnika(k) {
      k = k || {};
      dlg({ naslov: k.oznaka ? "Korisnik " + k.oznaka : "Novi korisnik", tijelo: '<div class="grid3"><div class="field"><span class="lbl">Oznaka</span><input id="oz" value="' + esc(k.oznaka || "") + '"' + (k.oznaka ? " disabled" : "") + ' placeholder="IVANA"></div><div class="field"><span class="lbl">Ime i prezime</span><input id="ime" value="' + esc(k.ime || "") + '"></div><div class="field"><span class="lbl">Uloga</span><select id="ul"' + (admin ? "" : " disabled") + '>' + ["ured", "nabava", "voditelj", "admin"].map(function (u) { return '<option value="' + u + '"' + ((k.uloga || "ured") === u ? " selected" : "") + '>' + ULOGE[u] + '</option>'; }).join("") + '</select></div></div>' +
        '<div class="grid3"><div class="field"><span class="lbl">Funkcija (u potpisu)</span><input id="fn" value="' + esc(k.funkcija || "") + '" placeholder="prodaja / priprema proizvodnje"></div><div class="field"><span class="lbl">E-mail (za odgovore kupaca)</span><input id="em" value="' + esc(k.email || "") + '"></div><div class="field"><span class="lbl">Telefon</span><input id="tel" value="' + esc(k.telefon || "") + '"></div></div>' +
        '<div class="field"><span class="lbl">Vlastiti potpis (prazno = ime / funkcija / tvrtka / kontakt)</span><textarea id="pot" rows="3">' + esc(k.potpis || "") + '</textarea></div>' +
        (admin ? '<div class="grid2"><div class="field"><span class="lbl">' + (k.oznaka ? "Nova lozinka (prazno = ne mijenjaj)" : "Početna lozinka") + '</span><input id="loz" type="password" autocomplete="new-password"></div><label class="prek" style="align-self:end;margin-bottom:8px"><input type="checkbox" id="akt"' + (k.aktivan === 0 ? "" : " checked") + '><span class="kl"></span><span class="st">Aktivan korisnik</span></label></div>' : ""),
        gumbi: [{ txt: "Spremi", pri: true, on: async function (bg) {
          var b = { oznaka: q("#oz", bg).value.trim(), ime: q("#ime", bg).value.trim(), funkcija: q("#fn", bg).value.trim(), email: q("#em", bg).value.trim(), telefon: q("#tel", bg).value.trim(), potpis: q("#pot", bg).value };
          if (admin) { b.uloga = q("#ul", bg).value; b.aktivan = q("#akt", bg).checked ? 1 : 0; if (q("#loz", bg).value) b.lozinka = q("#loz", bg).value; }
          if (!b.oznaka) { toast("upiši oznaku", true); return false; }
          await api("/api/korisnici", { body: b }); toast("Spremljeno"); render();
        } }] });
    }
    if (q("#btnNoviKor")) q("#btnNoviKor").onclick = function () { urediKorisnika(null); };
    qa("[data-kor]").forEach(function (b) { b.onclick = function () { urediKorisnika(korisnici.filter(function (k) { return k.oznaka === b.dataset.kor; })[0]); }; });
    qa("[data-loz]").forEach(function (b) { b.onclick = function () { H.postaviLozinku(false, b.dataset.loz); }; });
  };
  H.optBlok = optBlok; H.optBanner = optBanner; H.veziOpt = veziOpt; H.legendaSheme = legendaSheme;   // ekran unosa: kartica „Optimizacija“
})(Hub);
