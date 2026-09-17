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
  function optBlok(d, opt) {
    function pdf(o, x) { return '/api/nalog/' + d.id + '/ispis/krojni.pdf?materijal=' + o.nalog_materijal_id + (x ? '&oid=' + x.id : ""); }
    var IMENA = { auto: "Realno za pilu", hub: "Hub rezerva (najmanje m²)", uzduzno: "Uzdužno", poprecno: "Poprečno", trake: "Trake" };
    function lab(x) { return esc(IMENA[x.nacin_trazen] || x.nacin_trazen) + " / " + esc(x.dubina); }
    function nap(x) { return x.napomena ? '<div class="note warn-t">' + esc(x.napomena) + '</div>' : ""; }
    function slika(o, x) { return '<a class="slag-img" href="#" data-pregled="' + x.id + '" data-nm="' + o.nalog_materijal_id + '" title="Pregled optimizacije na ekranu"><img src="/api/optimizacija/' + x.id + '/sheme.png?h=150" alt="sheme" onerror="this.parentNode.classList.add(\'nema\')"></a>'; }
    function brojke(x) { return '<span class="big">' + x.broj_ploca + '</span> ploča &nbsp;·&nbsp; isk. <b>' + pct(x.iskoristenje) + '</b> &nbsp;·&nbsp; ' + naplata(x) + (x.rezova ? ' &nbsp;·&nbsp; rezova ' + x.rezova : ""); }
    return opt.map(function (o) {
      var p = o.potvrdjeno, pr = o.prijedlozi || [];
      var glavni = p || pr.filter(function (x) { return x.nacin_trazen === "auto" && x.dubina === "najbolje"; }).slice(-1)[0] || pr[0] || null;
      var ostali = pr.filter(function (x) { return !glavni || x.id !== glavni.id; });
      var head = '<div class="hd"><b class="ell">' + esc(o.materijal) + '</b><span class="note">' + esc(o.ident || "") + '</span>' + tagPut(o.put) + '<span class="grow"></span>' +
        (!o.treba ? '<span class="tag">po dužnom metru</span>' : p ? '<span class="tag ok">potvrđeno</span>' : '<span class="tag warn">čeka potvrdu</span>') + '</div>';
      var body;
      if (!o.treba) body = '<div class="bd"><span class="note">materijal se ne slaže na ploču — nema optimizacije</span></div>';
      else if (p) body = '<div class="bd slag-bd ok">' + slika(o, p) + '<div class="slag-txt"><div class="slag-naslov ok-t">✔ Potvrđena optimizacija <span class="note">' + esc(p.nacin || "") + '</span></div><div>' + brojke(p) + '</div>' +
        '<div class="row"><button class="btn" data-pregled="' + p.id + '" data-nm="' + o.nalog_materijal_id + '">Pregled shema</button><a class="btn" href="' + pdf(o, p) + '" target="_blank">Krojni nacrt PDF</a><button class="btn" data-alt="' + o.nalog_materijal_id + '">Druga varijanta…</button></div></div></div>';
      else if (glavni) body = '<div class="bd slag-bd ceka">' + slika(o, glavni) + '<div class="slag-txt"><div class="slag-naslov">' + lab(glavni) + ' <span class="note">' + esc(glavni.nacin || "") + '</span></div><div>' + brojke(glavni) + '</div>' + nap(glavni) +
        '<div class="row"><button class="btn pri lg" data-potvrdi-opt="' + glavni.id + '">✔ Potvrdi optimizaciju</button><button class="btn lg" data-pregled="' + glavni.id + '" data-nm="' + o.nalog_materijal_id + '">Pregled shema</button><a class="btn" href="' + pdf(o, glavni) + '" target="_blank">PDF</a><button class="btn" data-alt="' + o.nalog_materijal_id + '">Alternativa…</button></div></div></div>';
      else body = '<div class="bd slag-bd ceka"><div class="slag-txt"><div class="slag-naslov">Još nema prijedloga optimizacije</div><div class="note">Hub izračuna optimizaciju kakvu pila realno reže (trake → poprečni rezovi → uži komadi); ti ga potvrdiš — ista brojka ide u ponudu i na pilu. Uz njega pokaže i svoju rezervu s najmanje m² ako ona štedi materijal.</div>' +
        '<div class="row"><button class="btn pri lg" data-pred="' + o.nalog_materijal_id + '">Izračunaj optimizaciju</button><button class="btn" data-alt="' + o.nalog_materijal_id + '">Alternativa…</button></div></div></div>';
      var alt = ostali.length ? '<div class="slag-alt"><div class="note" style="padding:6px 14px 2px">Ostale varijante</div>' + ostali.map(function (x) {
        return '<div class="slag-red"><span>' + lab(x) + ' <span class="note">' + esc(x.nacin || "") + '</span>' + (x.napomena ? ' <span class="note warn-t" title="' + esc(x.napomena) + '">⚠</span>' : "") + '</span><span class="num">' + x.broj_ploca + ' pl · ' + pct(x.iskoristenje) + ' · ' + (x.naplata_rp ? n(x.naplata_rp.ukupno_m, 2) + ' m' : n(x.m2_za_naplatu, 2) + ' m²') +
          (x.razlika_m2_prema_auto != null ? ' <span class="' + (x.razlika_m2_prema_auto > 0 ? "warn-t" : "ok-t") + '">(' + (x.razlika_m2_prema_auto > 0 ? "+" : "") + n(x.razlika_m2_prema_auto, 2) + ')</span>' : "") + '</span>' +
          '<span class="row"><button class="btn sm" data-pregled="' + x.id + '" data-nm="' + o.nalog_materijal_id + '">sheme</button><button class="btn sm pri" data-potvrdi-opt="' + x.id + '">Potvrdi</button></span></div>'; }).join("") + '</div>' : "";
      return '<div class="pane slag-card">' + head + body + alt + '</div>';
    }).join("");
  }
  function legendaSheme() { return '<div class="legenda"><i style="background:#DCE9E2;border-color:#2E6B57"></i>iskorišteno za naručene mjere <i style="background:#DCE7F3;border-color:#2F5D8C"></i>naš restl (korisni ostatak, ne naplaćuje se) <i style="background:#F9DEE5;border-color:#C2506B"></i>kupčev restl (naplaćuje se)</div>'; }
  function optCeka(opt) { return (opt || []).filter(function (o) { return o.treba && !o.potvrdjeno; }); }
  function optBanner(d, opt, jedan) {
    var ceka = optCeka(opt);
    if (!ceka.length) return (opt || []).some(function (o) { return o.treba; }) ? '<div class="upoz ok slag-banner"><b>✔ Optimizacija potvrđena</b> ' + (jedan ? "za ovaj materijal" : "za sve materijale") + ' — ponuda i pila rade s tom brojkom.</div>' : "";
    return '<div class="upoz crit slag-banner"><div><b>Optimizacija čeka potvrdu</b> — ' + esc(ceka.map(function (o) { return o.materijal; }).join(", ")) + '.<br><span class="note">Bez potvrde nema ponude ni izvoza na pilu. Pogledaj sheme ' + (jedan ? "ispod" : "dolje") + ' i potvrdi' + (jedan ? "" : ", ili potvrdi zadane optimizacije (realne za pilu) odjednom") + '.</span></div>' +
      '<span class="grow"></span><button class="btn pri lg" id="potvrdiSve">✔ Potvrdi ' + (jedan ? "zadanu optimizaciju" : "sve zadane optimizacije (" + ceka.length + ")") + '</button></div>';
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
    var bruto = 0;
    (ob.stavke || []).forEach(function (s) {
      if (grupeVid && s.grupa !== zadnja) { rows += '<tr class="grp"><td colspan="8">' + esc(grupe[s.grupa] || s.grupa) + '</td></tr>'; zadnja = s.grupa; }
      bruto += (s.kolicina || 0) * (s.cijena || 0);
      var kl = s.rucna_id ? "R:" + s.rucna_id : "K:" + s.kljuc, kor = s.korekcija || null;
      rows += '<tr' + (s.rucna_id ? ' class="rucna"' : kor ? ' class="korig"' : "") + '><td class="mono">' + esc(s.pantheon_ident) + '</td><td class="wrap">' + esc(s.naziv || "") + (s.pravilo ? '<div class="note">' + esc(cist(s.pravilo)) + '</div>' : "") + '</td>' +
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
    var upoz = (ob.upozorenja || []).map(function (u) { return '<div class="upoz">' + esc(cist(u)) + '</div>'; }).join("");
    var ceka = optCeka(opt);
    var slagUpoz = ceka.length ? '<div class="upoz crit slag-banner"><div><b>Optimizacija čeka potvrdu</b> — ' + esc(ceka.map(function (o) { return o.materijal; }).join(", ")) + '. <span class="note">Brojke ploča dolje su Hubov prijedlog; bez potvrde nema verzije ponude.</span></div><span class="grow"></span><a class="btn pri" href="#/nalog/' + d.id + '/optimizacija">Otvori optimizaciju</a></div>' : "";
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
    var rows = pr.materijali.map(function (m) {
      var st = m.stanje || { ploce: {}, restlovi: {} }, tr = Object.keys(m.trake || {}).map(function (k) { return m.trake[k]; });
      return '<tr><td><b>' + esc(m.naziv) + '</b><div class="note">' + esc(m.ident || "") + ' ' + tagPut(m.put) + '</div></td>' +
        '<td class="r num">' + (m.na_restlu ? 'restl ' + m.restl_mjera.join("×") : (m.ploce == null ? '<span class="warn-t">?</span>' : m.ploce + ' pl.')) + '</td>' +
        '<td class="r num">' + n(st.ploce.fizicko, 0) + (st.ploce.lokacija ? '<div class="note">' + esc(st.ploce.lokacija) + '</div>' : "") + '</td><td class="r num">' + n(st.ploce.rezervirano, 0) + (m.rezervirano_ovaj ? '<div class="note">ovaj ' + m.rezervirano_ovaj + '</div>' : "") + '</td><td class="r num">' + n(st.ploce.naruceno, 0) + '</td><td class="r num"><b>' + n(st.ploce.raspolozivo, 0) + '</b></td>' +
        '<td>' + (m.manjak ? '<span class="tag crit">manjak ' + m.manjak + '</span>' : (m.manjak === 0 ? '<span class="tag ok">ok</span>' : "")) + '</td>' +
        '<td>' + ((st.restlovi.kom || 0) ? st.restlovi.kom + ' restl / ' + n(st.restlovi.m2, 2) + ' m²' : '—') + (m.restl_rezerviran && m.restl_rezerviran.length ? '<div class="note">rezerviran ' + m.restl_rezerviran.map(function (x) { return x.oznaka; }).join(", ") + '</div>' : "") +
        ((m.restl_kandidati || []).length ? '<div class="row" style="margin-top:4px">' + m.restl_kandidati.slice(0, 4).map(function (k) { return '<button class="btn sm" data-restl="' + m.nalog_materijal_id + ':' + k.id + '" title="' + esc(k.lokacija || "") + '">' + esc(k.oznaka) + ' ' + mm(k.L) + '×' + mm(k.W) + '</button>'; }).join("") + '</div>' : "") + '</td>' +
        '<td>' + tr.map(function (t) { return '<div>' + esc(t.ident) + ' <span class="note">' + esc((t.naziv || "").slice(0, 26)) + '</span> ' + t.metri + ' m' + (t.na_roli != null ? ' <span class="' + (t.manjak ? "crit-t" : "ok-t") + '">(na roli ' + n(t.na_roli, 1) + ')</span>' : ' <span class="note">(Regal traka nedostupna)</span>') + (t.pretinac ? ' <span class="tag info">' + esc(t.pretinac) + '</span>' : "") + '</div>'; }).join("") + '</td></tr>';
    }).join("");
    var pri = await api("/api/skladiste/prijedlozi?nalog=" + d.id);
    var priHtml = pri.prijedlozi.map(function (p) { return '<tr><td class="mono">' + esc(p.oznaka) + '</td><td>' + esc(p.ident) + ' ' + esc(p.naziv_kratki || "") + '</td><td class="r num">' + mm(p.L) + ' × ' + mm(p.W) + '</td><td class="r num">' + n(p.m2, 2) + '</td><td class="note">' + esc(p.napomena || "") + '</td><td class="r"><button class="btn sm pri" data-potvrdi-restl="' + p.id + '">Potvrdi (QR)</button> <button class="btn sm" data-odbaci-restl="' + p.id + '">Nema ga</button></td></tr>'; }).join("");
    ljuska({ crumb: crumb(d, "skladište"), koraci: koraci(d), rail: "nalozi", cls: "c1",
      akcije: '<a class="tbtn" href="#/nalog/' + d.id + '/ponuda">← Ponuda</a><span class="grow"></span><button class="tbtn" id="btnOslobodi">Oslobodi</button><button class="tbtn' + (d.status === "skladiste" ? "" : " pri") + '" id="btnRezerviraj">' + (d.status === "skladiste" ? "Rezerviraj ponovno" : "Rezerviraj materijal") + '</button>' + (d.status === "skladiste" ? '<button class="tbtn pri" id="btnNaStroj">→ Proizvodnja</button>' : ""),
      sadrzaj: '<div class="col"><div class="pane"><div class="hd"><b>Provjera skladišta</b><span class="note">raspoloživo = fizičko (Winstore) − rezervirano (drugi nalozi) + naručeno</span><span class="grow"></span>' + (pr.ok ? '<span class="tag ok">sve raspoloživo</span>' : '<span class="tag crit">manjak</span>') + '</div>' +
        '<div class="bd tight">' + pr.upozorenja.map(function (u) { return '<div class="upoz">' + esc(cist(u)) + '</div>'; }).join("") + '<table><thead><tr><th>Materijal</th><th class="r">Treba</th><th class="r">Fizičko</th><th class="r">Rezerv.</th><th class="r">Naručeno</th><th class="r">Raspol.</th><th></th><th>Restlovi</th><th>Trake</th></tr></thead><tbody>' + (rows || '<tr><td colspan="9" class="note">nalog nema materijala</td></tr>') + '</tbody></table></div></div>' +
        (pr.za_nabavu.length ? '<div class="pane"><div class="hd"><b>Za nabavu</b></div><div class="bd tight"><table><thead><tr><th>Ident</th><th>Naziv</th><th class="r">Količina</th><th>JM</th></tr></thead><tbody>' + pr.za_nabavu.map(function (z) { return '<tr><td class="mono">' + esc(z.ident) + '</td><td>' + esc(z.naziv || "") + '</td><td class="r num">' + n(z.kom, 1) + '</td><td>' + esc(z.jm) + '</td></tr>'; }).join("") + '</tbody></table><div class="row" style="padding:8px 12px"><a class="btn sm" href="#/nabava">Otvori Nabavu</a></div></div></div>' : "") +
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
      var rr = (rez || []).filter(function (x) { return x.nalog_materijal_id === m.id; })[0] || null;
      var o = opt.filter(function (x) { return x.nalog_materijal_id === m.id; })[0] || {}, p = o.potvrdjeno;
      return '<div class="pane slag-card"><div class="hd"><b>' + esc(m.naziv_kratki || m.naziv_ulaz || "") + '</b><span class="note">' + esc(m.ident || "") + ' · ' + m.elemenata + ' el / ' + m.komada + ' kom · ' + n(m.m2, 2) + ' m²' + (m.debljina ? ' · ' + m.debljina + ' mm' : "") + '</span><span class="grow"></span>' +
        '<span class="lbl">put</span><select data-put="' + m.id + '"><option value="">— ' + (m.put_prijedlog ? "Hub: " + esc(m.put_prijedlog) : "") + '</option><option value="pila"' + (m.put === "pila" ? " selected" : "") + '>pila</option><option value="nesting"' + (m.put === "nesting" ? " selected" : "") + '>nesting</option></select></div>' +
        '<div class="bd slag-bd' + (p ? " ok" : "") + '">' + (p ? '<a class="slag-img" href="#" data-pregled="' + p.id + '" data-nm="' + m.id + '" title="Pregled shema"><img src="/api/optimizacija/' + p.id + '/sheme.png?h=96" alt=""></a><div class="slag-txt"><div><b>' + p.broj_ploca + ' ploča</b> · isk. ' + pct(p.iskoristenje) + ' · ' + naplata(p) + ' · rezova ' + (p.rezova || "—") + ' <span class="note">' + esc(p.nacin || "") + '</span></div>' +
          '<div class="row">' + (rr && rr.bnest ? '<span>bNest: <b>' + rr.bnest.broj_ploca + ' ploča</b> · isk. ' + pct(rr.bnest.iskoristenje) + (rr.razlika_ploca != null ? ' · razlika <b class="' + (rr.razlika_ploca < 0 ? "ok-t" : "warn-t") + '">' + rr.razlika_ploca + '</b>' : "") + '</span>' : "") + (rr && rr.spojeni_posao ? '<span class="tag info">spojeno: ' + esc(rr.spojeni_posao.naziv) + (rr.spojeni_posao.rezultat_stigao ? " ✓" : "") + '</span>' : "") + (rr && rr.hub ? '<span class="note">izvezeno na pilu</span>' : "") + '<button class="btn sm" data-pregled="' + p.id + '" data-nm="' + m.id + '">Pregled shema</button><a class="btn sm" href="/api/nalog/' + d.id + '/ispis/krojni.pdf?materijal=' + m.id + '" target="_blank">Krojni nacrt</a></div></div>'
          : (o.treba === false ? '<span class="note">materijal po dužnom metru — nema optimizacije</span>' : '<div class="upoz crit">Optimizacija nije potvrđena — <a href="#/nalog/' + d.id + '/optimizacija">potvrdi je u koraku 2 Optimizacija</a>; bez toga nema izvoza na stroj.</div>')) + '</div></div>';
    }).join("");
    ljuska({ crumb: crumb(d, "proizvodnja"), koraci: koraci(d), rail: "nalozi", cls: "c2 proizv",
      akcije: '<a class="tbtn" href="#/nalog/' + d.id + '/skladiste">← Skladište</a><span class="grow"></span><a class="tbtn" href="/api/nalog/' + d.id + '/ispis/krojni.pdf" target="_blank">Krojni nacrt</a><button class="tbtn" id="btnRez">Rezultat bNest (.mno)</button>',
      sadrzaj: '<div class="col">' + mats + '</div>' +
        '<div class="col"><div class="pane"><div class="hd"><b>Izvoz na stroj</b></div><div class="bd">' +
        '<div class="row"><button class="btn" data-izvoz="nesting" data-suho="1">Nesting — pregled</button><button class="btn pri" data-izvoz="nesting">Nesting — pošalji</button></div><div class="row"><button class="btn" data-izvoz="pila" data-suho="1">Pila — pregled</button><button class="btn pri" data-izvoz="pila">Pila — pošalji</button></div><div class="row"><button class="btn" data-izvoz="pw">PanelWizard CPW</button></div>' +
        '<div class="note">Mape: nesting <span class="mono">' + esc(mapaN) + '</span> · pila <span class="mono">' + esc(mapaP) + '</span> <a href="#/postavke">(Postavke)</a>. Na stroj ide samo nalog u statusu potvrđeno / skladište / pila-nesting, bez stavki za potvrdu i s potvrđenom optimizacijom.</div><div id="izvozRez"></div></div></div>' +
        '<div class="pane"><div class="hd"><b>Spajanje s drugim nalozima</b><span class="note">isti materijal, zajedno na nesting — tu se bira drukčija optimizacija</span></div><div class="bd" id="spajanje"><span class="note">učitavam…</span></div></div></div>',
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
    var akcije = '<a class="tbtn' + (pod === "stanje" ? " pri" : "") + '" href="#/skladiste/stanje">Stanje</a><a class="tbtn' + (pod === "restlovi" ? " pri" : "") + '" href="#/skladiste/restlovi">Restlovi</a><a class="tbtn' + (pod === "potvrde" ? " pri" : "") + '" href="#/skladiste/potvrde">Dekori za potvrdu</a>';
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

  // ---------------------------------------------------------------- ekran 6: nabava
  E.nabava = async function (r) {
    var pod = r.id || "potrebe";
    var akcije = '<a class="tbtn' + (pod === "potrebe" ? " pri" : "") + '" href="#/nabava/potrebe">Potrebe</a><a class="tbtn' + (pod === "narudzbenice" ? " pri" : "") + '" href="#/nabava/narudzbenice">Narudžbenice</a><a class="tbtn' + (pod === "dobavljaci" ? " pri" : "") + '" href="#/nabava/dobavljaci">Dobavljači</a>';
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
    var rows = lst.map(function (x) { return '<tr><td class="mono">' + esc(x.ident) + '</td><td>' + esc(x.naziv) + '</td><td>' + esc(x.naziv_kratki || x.klasa || "") + '</td><td class="r">' + (x.debljina ? x.debljina + " mm" : "") + '</td><td>' + esc(x.winstore_kod || x.dekor || "") + '</td><td class="r">' + (x.stanje_kom != null ? x.stanje_kom : "") + '</td><td>' + (x.pogodak ? '<span class="tag info">' + esc(x.pogodak) + '</span>' : "") + '</td></tr>'; }).join("");
    ljuska({ crumb: "<b>Šifrarnik</b>", rail: "sifr", cls: "c1",
      sadrzaj: '<div class="pane"><div class="hd"><span class="chip' + (vr === "materijali" ? " on" : "") + '" data-v="materijali">Materijali</span><span class="chip' + (vr === "trake" ? " on" : "") + '" data-v="trake">Trake</span><span class="grow"></span><input id="q" placeholder="naziv, ident, Winstore kod, tekst iz naloga…" value="' + esc(s) + '" style="width:340px"></div>' +
        '<div class="bd tight"><table><thead><tr><th>Ident</th><th>Naziv</th><th>Kratki / klasa</th><th class="r">Debljina</th><th>Winstore / dekor</th><th class="r">Stanje</th><th></th></tr></thead><tbody>' + (rows || '<tr><td colspan="7" class="note">upiši pojam za pretragu</td></tr>') + '</tbody></table></div></div>', foot: kpi(lst.length, "pogodaka") + '<span class="note">Šifrarnik se puni dnevnim uvozom iz Pantheona i Winstorea; ispravci ureda (debljina, „ne koristi se“, veza koda) žive u Hubu.</span>' });
    qa("[data-v]").forEach(function (c) { c.onclick = function () { S.sifVrsta = c.dataset.v; render(); }; });
    var t; q("#q").oninput = function () { clearTimeout(t); S.sifQ = this.value; t = setTimeout(render, 250); }; q("#q").focus();
  };
  E.postavke = async function () {
    var p0 = await api("/api/postavke/optimizacija"), m = await api("/api/mail/postavke").catch(function () { return {}; });
    var p = {}; (Array.isArray(p0) ? p0 : Object.keys(p0).map(function (k) { return { kljuc: k, vrijednost: p0[k] }; })).forEach(function (x) { p[x.kljuc] = x.vrijednost; });
    var ja = (await H.ucitajJa()) || {}, admin = !ja.prijava_obavezna || (ja.korisnik && ja.korisnik.uloga === "admin");
    var korisnici = admin ? await api("/api/korisnici").catch(function () { return []; }) : (ja.korisnik ? [ja.korisnik] : []);
    var polja = [["kerf", "Kerf za naplatu (mm)"], ["kerf_pile", "Fizički kerf pile (mm)"], ["nadmjera_trake", "Nadmjera trake (%)"], ["obracun_rezanja", "Obračun rezanja (m2 | m | rez)"], ["ident_rezanje_rez", "Ident usluge po rezu"], ["ident_rezanje_m", "Ident usluge po dužnom metru"], ["mapa_nesting", "Mapa izvoza na nesting (bNest)"], ["mapa_pila", "Mapa izvoza na pilu (OSI)"],
      ["pila_max_razina", "Pila: najviše razina rezanja (2 | 3 | 4)"], ["pila_max_sirina_u_traci", "Pila: najviše različitih širina u traci (0 = bez)"], ["pila_min_komad_4", "Pila: najmanji komad 4. razine (mm, 0 = bez)"], ["pila_mijesana_orijentacija", "Pila: miješana orijentacija dopuštena (0 | 1)"]];
    ljuska({ crumb: "<b>Postavke</b>", rail: "post", cls: "c2",
      sadrzaj: '<div class="col"><div class="pane"><div class="hd"><b>Optimizacija i obračun</b><span class="note">globalno; svaka ponuda nosi snimku brojki</span></div><div class="bd"><div class="grid2">' + polja.map(function (x) { return '<div class="field"><span class="lbl">' + esc(x[1]) + '</span><input data-k="' + x[0] + '" value="' + esc(p[x[0]] == null ? "" : p[x[0]]) + '"></div>'; }).join("") + '</div><div class="row"><button class="btn pri" id="btnSpremi">Spremi</button></div></div></div>' + '<div class="pane"><div class="hd"><b>Korisnici i prijava</b><span class="note">' + (ja.prijava_obavezna ? "prijava s lozinkom je obavezna" : "prijava još nije obavezna — uključi se prvom lozinkom") + '</span><span class="grow"></span>' + (admin ? '<button class="btn sm pri" id="btnNoviKor">+ Novi korisnik</button>' : "") + '</div><div class="bd tight"><table><thead><tr><th>Oznaka</th><th>Ime</th><th>Uloga</th><th>E-mail / telefon</th><th>Lozinka</th><th></th></tr></thead><tbody>' +
        (korisnici.map(function (k) { return '<tr' + (k.aktivan ? "" : ' class="note"') + '><td class="mono"><b>' + esc(k.oznaka) + '</b></td><td>' + esc(k.ime || "") + (k.funkcija ? '<div class="note">' + esc(k.funkcija) + '</div>' : "") + '</td><td>' + esc(k.uloga || "") + '</td><td class="note">' + esc(k.email || "") + (k.telefon ? " · " + esc(k.telefon) : "") + '</td><td>' + (k.ima_lozinku ? '<span class="tag ok">ima</span>' : '<span class="tag warn">nema</span>') + '</td><td class="r">' + (admin || k.oznaka === S.korisnik ? '<button class="btn sm" data-kor="' + esc(k.oznaka) + '">Uredi</button> <button class="btn sm" data-loz="' + esc(k.oznaka) + '">Lozinka</button>' : "") + '</td></tr>'; }).join("") || '<tr><td colspan="6" class="note">samo administrator vidi popis</td></tr>') +
        '</tbody></table></div><div class="bd"><div class="row"><span>Prijavljen: <b>' + esc(S.korisnik) + '</b>' + (ja.potpis ? ' · potpis u mailu: <span class="note">' + esc(ja.potpis).replace(/\n/g, " · ") + '</span>' : "") + '</span><span class="grow"></span>' + (ja.prijava_obavezna ? '<button class="btn sm" id="btnOdjava">Odjava</button>' : '<button class="btn sm" id="btnKor">Promijeni korisnika</button>') + '</div></div></div></div>' +
        '<div class="col"><div class="pane"><div class="hd"><b>E-pošta (ponude, narudžbe)</b></div><div class="bd"><div class="kv">' + Object.keys(m).map(function (k) { return '<b>' + esc(k) + '</b><span>' + esc(typeof m[k] === "object" ? JSON.stringify(m[k]) : m[k]) + '</span>'; }).join("") + '</div></div></div></div>', foot: "" });
    q("#btnSpremi").onclick = async function () { var b = {}; qa("[data-k]").forEach(function (i) { b[i.dataset.k] = i.value; }); await api("/api/postavke/optimizacija", { body: b }); toast("Spremljeno"); };
    if (q("#btnKor")) q("#btnKor").onclick = function () { q("#korisnik").click(); };
    if (q("#btnOdjava")) q("#btnOdjava").onclick = function () { q("#korisnik").click(); };
    function urediKorisnika(k) {
      k = k || {};
      dlg({ naslov: k.oznaka ? "Korisnik " + k.oznaka : "Novi korisnik", tijelo: '<div class="grid3"><div class="field"><span class="lbl">Oznaka</span><input id="oz" value="' + esc(k.oznaka || "") + '"' + (k.oznaka ? " disabled" : "") + ' placeholder="IVANA"></div><div class="field"><span class="lbl">Ime i prezime</span><input id="ime" value="' + esc(k.ime || "") + '"></div><div class="field"><span class="lbl">Uloga</span><select id="ul"' + (admin ? "" : " disabled") + '>' + ["ured", "nabava", "voditelj", "admin"].map(function (u) { return '<option value="' + u + '"' + ((k.uloga || "ured") === u ? " selected" : "") + '>' + u + '</option>'; }).join("") + '</select></div></div>' +
        '<div class="grid3"><div class="field"><span class="lbl">Funkcija (u potpisu)</span><input id="fn" value="' + esc(k.funkcija || "") + '" placeholder="prodaja / priprema proizvodnje"></div><div class="field"><span class="lbl">E-mail (Reply-To)</span><input id="em" value="' + esc(k.email || "") + '"></div><div class="field"><span class="lbl">Telefon</span><input id="tel" value="' + esc(k.telefon || "") + '"></div></div>' +
        '<div class="field"><span class="lbl">Vlastiti potpis (prazno = ime / funkcija / tvrtka / kontakt)</span><textarea id="pot" rows="3">' + esc(k.potpis || "") + '</textarea></div>' +
        (admin ? '<div class="grid2"><div class="field"><span class="lbl">' + (k.oznaka ? "Nova lozinka (prazno = ne mijenjaj)" : "Početna lozinka") + '</span><input id="loz" type="password" autocomplete="new-password"></div><label class="note" style="align-self:end"><input type="checkbox" id="akt"' + (k.aktivan === 0 ? "" : " checked") + '> aktivan</label></div>' : ""),
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
