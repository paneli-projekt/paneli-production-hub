/* Paneli Production Hub — web ekrani na API-ju (ljuska, router, ekran 1 popis, ekran 2 unos). Bez okvira, bez builda: vanilla JS.
   Pravila: na ekranu nikad riječ „AI“ ni oznake odluka; na radnom ekranu samo ono što korisnik u tom koraku treba, ostalo na klik. */
var Hub = (function () {
  "use strict";
  var S = { korisnik: localStorage.getItem("hub_korisnik") || "IVANA", ruta: {}, nalog: null, nm: null, trake: {}, aktivna: {}, odabran: null, filter: {status: "", q: ""} };
  var BOJE = ["--t1", "--t2", "--t3", "--t4", "--t5", "--t6"];
  var STATUSI = [["unos", "Unos"], ["ponuda", "Ponuda — čeka kupca"], ["potvrdjeno", "Potvrđeno"], ["skladiste", "Skladište"], ["pila_nesting", "Pila / nesting"],
                 ["proizvodnja", "Proizvodnja"], ["izdatnica", "Izdatnica"], ["zatvoren", "Zatvoren"]];
  var KORAK = { unos: 0, ponuda: 2, potvrdjeno: 2, skladiste: 3, pila_nesting: 4, proizvodnja: 4, izdatnica: 4, zatvoren: 4 };   // koraci: unos, optimizacija, ponuda, skladište, proizvodnja
  var ekrani = {};

  // ---------------------------------------------------------------- pomoćno
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function cist(s) { return String(s == null ? "" : s).replace(/\s*\(D-\d+(?:\/\d+)?[^)]*\)/g, "").replace(/\s*—?\s*D-\d+(?:\/\d+)?/g, ""); }   // oznake odluka ne idu na ekran
  function mm(x) { return x == null ? "—" : String(Math.round(+x * 10) / 10); }
  function n(x, d) { if (x == null || x === "") return "—"; var v = Number(x); return isFinite(v) ? v.toLocaleString("hr-HR", { minimumFractionDigits: d || 0, maximumFractionDigits: d == null ? 2 : d }) : esc(x); }
  function q(sel, root) { return (root || document).querySelector(sel); }
  function qa(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function tok(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  function statusNaziv(s) { for (var i = 0; i < STATUSI.length; i++) if (STATUSI[i][0] === s) return STATUSI[i][1]; return s; }
  function toast(msg, crit) {
    var t = document.createElement("div"); t.className = "toast" + (crit ? " crit" : ""); t.textContent = msg; document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, crit ? 6000 : 2800);
  }
  async function api(path, opts) {
    opts = opts || {};
    var o = { method: opts.method || (opts.body ? "POST" : "GET"), headers: {} };
    if (opts.body instanceof FormData) o.body = opts.body;
    else if (opts.body) { o.headers["Content-Type"] = "application/json"; o.body = JSON.stringify(Object.assign({ tko: S.korisnik }, opts.body)); }
    var r = await fetch(path, o);
    var ct = r.headers.get("content-type") || "";
    var data = ct.indexOf("json") >= 0 ? await r.json() : await r.text();
    if (r.status === 401 && data && data.detail === "prijava") { await ucitajJa(); ekranPrijava(); throw new Error("prijava"); }
    if (!r.ok) { var msg = (data && data.detail) ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)) : ("Greška " + r.status); if (!opts.tiho) toast(msg, true); throw new Error(msg); }
    return data;
  }
  // ---------------------------------------------------------------- prijava korisnika (lozinka, sesija u kolačiću)
  S.ja = null;                                   // { korisnik, prijava_obavezna, oznake, potpis }
  async function ucitajJa() {
    S.ja = await fetch("/api/ja").then(function (r) { return r.json(); }).catch(function () { return null; });
    if (S.ja && S.ja.korisnik) { S.korisnik = S.ja.korisnik.oznaka; localStorage.setItem("hub_korisnik", S.korisnik); }
    return S.ja;
  }
  function ekranPrijava(poruka, oznaka) {
    var ja = S.ja || { oznake: [] }, oz = oznaka || S.korisnik || "";
    var gumbi = (ja.oznake || []).map(function (k) { return '<button class="btn kor' + (k.oznaka === oz ? " pri" : "") + '" data-oz="' + esc(k.oznaka) + '" title="' + esc(k.ime || "") + '">' + esc(k.oznaka) + '</button>'; }).join("");
    q("#app").innerHTML = '<div class="prijava"><div class="pane kartica"><div class="brand"><img src="/static/logo-mark.png" alt=""><b>Paneli<span class="us">_</span> Production Hub</b></div>' +
      '<div class="note">Odaberi svoju oznaku i upiši lozinku.</div><div class="row wrap" id="oznake">' + gumbi + '</div>' +
      '<div class="field"><span class="lbl">Oznaka</span><input id="oz" value="' + esc(oz) + '" autocomplete="username"></div>' +
      '<div class="field"><span class="lbl">Lozinka</span><input id="loz" type="password" autocomplete="current-password" placeholder="prva prijava: ostavi prazno"></div>' +
      (poruka ? '<div class="upoz crit">' + esc(poruka) + '</div>' : "") + '<button class="btn pri lg" id="btnPrijava">Prijava</button></div></div>';
    qa("[data-oz]").forEach(function (b) { b.onclick = function () { q("#oz").value = b.dataset.oz; qa("[data-oz]").forEach(function (x) { x.classList.toggle("pri", x === b); }); q("#loz").focus(); }; });
    async function prijavi() {
      var r = await fetch("/api/prijava", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ oznaka: q("#oz").value.trim(), lozinka: q("#loz").value }) });
      var d = await r.json();
      if (!r.ok) { ekranPrijava(d.detail || "prijava nije uspjela", q("#oz").value.trim().toUpperCase()); return; }
      S.korisnik = d.korisnik.oznaka; localStorage.setItem("hub_korisnik", S.korisnik);
      await ucitajJa();
      if (d.treba_lozinka) postaviLozinku(true); else render();
    }
    q("#btnPrijava").onclick = prijavi;
    q("#loz").onkeydown = function (e) { if (e.key === "Enter") prijavi(); };
    q("#oz").onkeydown = function (e) { if (e.key === "Enter") q("#loz").focus(); };
    (q("#oz").value ? q("#loz") : q("#oz")).focus();
  }
  function postaviLozinku(prva, oznaka) {
    var moja = !oznaka || oznaka === S.korisnik;
    dlg({ naslov: prva ? "Postavi svoju lozinku" : (moja ? "Promjena lozinke" : "Lozinka za " + oznaka),
      tijelo: (prva ? '<div class="upoz">Prva prijava: odaberi lozinku (najmanje 4 znaka). Od sada se Hub otvara samo s lozinkom.</div>' : "") +
        (!prva && moja && S.ja && S.ja.korisnik && S.ja.korisnik.ima_lozinku ? '<div class="field"><span class="lbl">Stara lozinka</span><input id="st" type="password"></div>' : "") +
        '<div class="field"><span class="lbl">Nova lozinka</span><input id="n1" type="password" autocomplete="new-password"></div><div class="field"><span class="lbl">Ponovi novu lozinku</span><input id="n2" type="password" autocomplete="new-password"></div>',
      gumbi: [{ txt: "Spremi", pri: true, on: async function (bg) {
        if (q("#n1", bg).value !== q("#n2", bg).value) { toast("lozinke nisu jednake", true); return false; }
        var b = { nova: q("#n1", bg).value }; if (q("#st", bg)) b.stara = q("#st", bg).value; if (!moja) b.oznaka = oznaka;
        var r = await api("/api/ja/lozinka", { body: b });
        toast("Lozinka spremljena" + (r.prijava_ukljucena ? " — prijava s lozinkom je sada obavezna za sve" : ""));
        if (prva || moja) { await ucitajJa(); if (!S.ja || !S.ja.korisnik) { ekranPrijava(); return; } }
        render();
      } }], nakon: function (bg) { (q("#st", bg) || q("#n1", bg)).focus(); } });
  }
  async function odjava() { await fetch("/api/odjava", { method: "POST" }); S.ja = null; await ucitajJa(); if (S.ja && S.ja.prijava_obavezna) ekranPrijava(); else render(); }
  function izbornikKorisnika() {
    var ja = S.ja || {}, k = ja.korisnik;
    if (!ja.prijava_obavezna && !k) {
      var o = prompt("Oznaka korisnika (IVANA, GORAN, SANELA, IGOR…)", S.korisnik);
      if (o) { S.korisnik = o.toUpperCase(); localStorage.setItem("hub_korisnik", S.korisnik); render(); }
      return;
    }
    dlg({ naslov: (k ? (k.ime || k.oznaka) + " (" + k.oznaka + ")" : S.korisnik), tijelo: '<div class="note">' + esc(k && k.uloga ? "uloga: " + k.uloga : "") + '</div>',
      gumbi: [{ txt: "Promijeni lozinku", on: function (bg, z) { z(); postaviLozinku(false); return false; } }, { txt: "Odjava", pri: true, on: function () { odjava(); } }] });
  }
  function dlg(o) {
    var bg = document.createElement("div"); bg.className = "dlg-bg";
    bg.innerHTML = '<div class="dlg' + (o.wide ? " wide" : "") + '"><div class="hd"><b>' + esc(o.naslov) + '</b><button class="btn sm" data-x>×</button></div>' +
      '<div class="bd">' + (o.tijelo || "") + '</div><div class="ft">' + (o.gumbi || []).map(function (g, i) { return '<button class="btn' + (g.pri ? " pri" : "") + '" data-g="' + i + '">' + esc(g.txt) + '</button>'; }).join("") + '</div></div>';
    document.body.appendChild(bg);
    function zatvori() { bg.remove(); document.removeEventListener("keydown", esc_); }
    function esc_(e) { if (e.key === "Escape") zatvori(); }
    document.addEventListener("keydown", esc_);
    q("[data-x]", bg).onclick = zatvori;
    bg.addEventListener("click", function (e) { if (e.target === bg) zatvori(); });
    (o.gumbi || []).forEach(function (g, i) { q('[data-g="' + i + '"]', bg).onclick = async function () { try { var r = await g.on(bg, zatvori); if (r !== false) zatvori(); } catch (e) { /* toast već */ } }; });
    if (o.nakon) o.nakon(bg, zatvori);
    return { el: bg, zatvori: zatvori };
  }
  function pretragaLista(el, ucitaj, prikaz, odaberi) {
    /* input + lista rezultata: ucitaj(q) → [] ; prikaz(x) → html ; odaberi(x) */
    var inp = q("input", el), lst = q(".lista", el), t = null, zadnji = [];
    async function osvjezi() { zadnji = await ucitaj(inp.value.trim()); lst.innerHTML = zadnji.map(function (x, i) { return '<div class="li" data-i="' + i + '">' + prikaz(x) + '</div>'; }).join("") || '<div class="li note">ništa</div>'; }
    inp.addEventListener("input", function () { clearTimeout(t); t = setTimeout(osvjezi, 180); });
    lst.addEventListener("click", function (e) { var li = e.target.closest("[data-i]"); if (li) odaberi(zadnji[+li.dataset.i]); });
    osvjezi(); inp.focus();
  }

  // ---------------------------------------------------------------- ljuska
  function ico(name) {
    var p = { nalozi: '<path d="M5 3h10l4 4v14H5z"/><path d="M15 3v4h4M8 12h8M8 16h8"/>', sklad: '<path d="M3 9 12 4l9 5v11H3z"/><path d="M9 20v-7h6v7"/>',
      nabava: '<path d="M4 8h16v12H4z"/><path d="M4 8l2.5-4h11L20 8M12 11v6M9 14h6"/>', sifr: '<path d="M4 6h16M4 12h16M4 18h10"/>',
      post: '<circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.4-2.3.9a7 7 0 0 0-1.7-1L14.5 3h-5l-.4 2.5a7 7 0 0 0-1.7 1L5.1 5.6l-2 3.4L5.1 10.5a7 7 0 0 0 0 2L3.1 14l2 3.4 2.3-.9a7 7 0 0 0 1.7 1l.4 2.5h5l.4-2.5a7 7 0 0 0 1.7-1l2.3.9 2-3.4-2-1.5c.1-.3.1-.7.1-1z"/>' }[name];
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' + p + '</svg>';
  }
  function koraci(nalog) {
    if (!nalog) return "";
    /* bijela pilula = ekran koji je OTVOREN; kvačica = korak koji je nalog prošao; zelena točka = korak u kojem je nalog sada (Igor, 17. 9.) */
    var k = KORAK[nalog.status] || 0, rute = ["", "/optimizacija", "/ponuda", "/skladiste", "/proizvodnja"], imena = ["1 Unos", "2 Optimizacija", "3 Ponuda", "4 Skladište", "5 Proizvodnja"];   // ekran pile / nestinga = Proizvodnja (Igor, 17. 9.)
    var podovi = ["unos", "slaganje", "ponuda", "skladiste", "pila"], pod = (S.ruta || {}).pod || "unos", otvoren = podovi.indexOf(pod === "obracun" ? "ponuda" : pod === "proizvodnja" ? "pila" : pod === "optimizacija" ? "slaganje" : pod);
    return '<div class="steps">' + imena.map(function (s, i) {
      var cls = (i === otvoren ? " on" : "") + (i < k ? " done" : "") + (i === k ? " tu" : "");
      var t = i === k ? "nalog je sada u ovom koraku (" + statusNaziv(nalog.status) + ")" : i < k ? "korak je prošao" : "još nije na redu";
      return '<a class="pill' + cls + '" href="#/nalog/' + nalog.id + rute[i] + '" title="' + esc(t) + '">' + (i < k ? '<span class="kv">✓</span>' : i === k ? '<span class="dot"></span>' : "") + s + '</a>'; }).join("") + '</div>';
  }
  function ljuska(o) {
    var app = q("#app");
    app.innerHTML = '<div class="top"><div class="brand" onclick="location.hash=\'#/nalozi\'"><img src="/static/logo-mark.png" alt=""><b>Paneli<span class="us">_</span> Production Hub</b></div><div class="sep"></div>' +
      '<div class="crumb">' + (o.crumb || "") + '</div>' + (o.koraci || "") + '</div>' +
      '<div class="main"><nav class="rail">' + [["nalozi", "Nalozi", "#/nalozi"], ["sklad", "Skladište", "#/skladiste"], ["nabava", "Nabava", "#/nabava"], ["sifr", "Šifrarnik", "#/sifrarnik"], ["post", "Postavke", "#/postavke"]].map(function (x) {
        return '<a class="it' + (o.rail === x[0] ? " on" : "") + '" href="' + x[2] + '">' + ico(x[0]) + x[1] + '</a>'; }).join("") +
      '<div class="user" title="Korisnik (klik za promjenu)" id="korisnik">' + esc(S.korisnik.slice(0, 2)) + '</div></nav>' +
      '<div class="content ' + (o.cls || "c1") + (o.akcije ? " ima-alat" : "") + '" id="content">' + (o.akcije ? '<div class="alatna">' + o.akcije + '</div>' : "") + (o.sadrzaj || "") + '</div></div>' +   // gumbi ekrana su NA ekranu, u zaglavlju samo koraci (Igor, 17. 9.)
      (o.foot != null ? '<div class="foot">' + o.foot + '</div>' : "");
    q("#korisnik").onclick = izbornikKorisnika;
  }
  function kpi(v, l) { return '<div class="kpi"><b>' + v + '</b><span>' + esc(l) + '</span></div>'; }

  // ---------------------------------------------------------------- router
  function parse() {
    var h = location.hash.replace(/^#\/?/, "") || "nalozi", p = h.split("/");
    if (p[0] === "nalog" && p[1]) return { ekran: "nalog", id: +p[1], pod: p[2] || "unos" };
    return { ekran: p[0], id: p[1] };
  }
  async function render() {
    S.ruta = parse();
    qa(".dlg-bg").forEach(function (x) { x.remove(); });        // promjena ekrana zatvara otvorene dijaloge
    var f = ekrani[S.ruta.ekran] || ekrani.nalozi;
    try { await f(S.ruta); } catch (e) { if (e && e.message === "prijava") return; console.error(e); q("#app").innerHTML = '<div class="spin">Greška: ' + esc(e.message) + ' — <a href="#/nalozi">natrag na naloge</a></div>'; }
  }
  function idi(hash) { if (location.hash === hash) render(); else location.hash = hash; }

  // ---------------------------------------------------------------- ekran 1: popis naloga
  ekrani.nalozi = async function () {
    var par = new URLSearchParams(); if (S.filter.status) par.set("status", S.filter.status); if (S.filter.q) par.set("q", S.filter.q);
    var sve = (await api("/api/nalozi?limit=300")).nalozi, popis = (S.filter.status || S.filter.q) ? (await api("/api/nalozi?" + par)).nalozi : sve;
    var brojac = {}; sve.forEach(function (x) { brojac[x.status] = (brojac[x.status] || 0) + 1; });
    var chips = '<span class="chip' + (S.filter.status ? "" : " on") + '" data-st="">Svi <span class="n">' + sve.length + '</span></span>' +
      STATUSI.map(function (s) { return '<span class="chip' + (S.filter.status === s[0] ? " on" : "") + '" data-st="' + s[0] + '">' + esc(s[1]) + ' <span class="n">' + (brojac[s[0]] || 0) + '</span></span>'; }).join("");
    var redovi = popis.map(function (x) {
      return '<tr class="klik" data-id="' + x.id + '"><td class="mono">' + esc(x.broj) + '</td><td><b>' + esc(x.naziv) + '</b></td><td>' + esc(x.kupac_naziv || "") + '</td>' +
        '<td><span class="tag ' + (x.status === "unos" ? "info" : x.status === "ponuda" ? "warn" : x.status === "zatvoren" ? "" : "ok") + '">' + esc(x.status_naziv) + '</span>' +
        (x.vrsta === "vlastita_proizvodnja" ? ' <span class="tag">vlastita</span>' : "") + '</td>' +
        '<td class="r num">' + x.materijala + '</td><td class="r num">' + x.elemenata + ' / ' + x.komada + '</td>' +
        '<td>' + (x.za_potvrdu ? '<span class="tag warn">za potvrdu ' + x.za_potvrdu + '</span>' : "") + '</td>' +
        '<td>' + esc(x.rok_obecan || x.rok_kupca || "") + (x.prioritet ? ' <span class="tag crit">' + esc(x.prioritet) + '</span>' : "") + '</td><td class="note">' + esc((x.datum || "").slice(0, 10)) + ' · ' + esc(x.izradio || "") + '</td></tr>';
    }).join("");
    ljuska({ crumb: "<b>Nalozi</b>", rail: "nalozi", cls: "c1",
      akcije: '<button class="tbtn" id="btnCorpus">Corpus paket</button><button class="tbtn pri" id="btnNovi">+ Novi nalog</button>',
      sadrzaj: '<div class="pane"><div class="hd"><div class="row" id="chips">' + chips + '</div><span class="grow"></span><input id="q" placeholder="traži nalog / kupca…" value="' + esc(S.filter.q) + '" style="width:260px"></div>' +
        '<div class="bd tight"><table><thead><tr><th>Broj</th><th>Nalog</th><th>Kupac</th><th>Status</th><th class="r">Mat.</th><th class="r">El. / kom</th><th></th><th>Rok</th><th>Otvoren</th></tr></thead><tbody>' + (redovi || '<tr><td colspan="9" class="note">nema naloga</td></tr>') + '</tbody></table></div></div>',
      foot: kpi(sve.length, "naloga") + kpi(brojac.unos || 0, "u unosu") + kpi(brojac.ponuda || 0, "čeka kupca") + kpi((brojac.potvrdjeno || 0) + (brojac.skladiste || 0), "za proizvodnju") + kpi(brojac.pila_nesting || 0, "na stroju") });
    qa("#chips .chip").forEach(function (c) { c.onclick = function () { S.filter.status = c.dataset.st; render(); }; });
    var t; q("#q").oninput = function () { clearTimeout(t); S.filter.q = this.value; t = setTimeout(render, 250); };
    qa("tr[data-id]").forEach(function (r) { r.onclick = function () { idi("#/nalog/" + r.dataset.id); }; });
    q("#btnNovi").onclick = noviNalog;
    q("#btnCorpus").onclick = uvozCorpus;
  };

  function noviNalog() {
    var kupac = null;
    dlg({ naslov: "Novi nalog", tijelo: '<div class="field"><span class="lbl">Kupac</span><input placeholder="naziv, mjesto, OIB, telefon…"><div class="lista"></div></div>' +
      '<div id="odabrani" class="note">kupac nije odabran</div><div class="grid2"><div class="field"><span class="lbl">Naziv / projekt (npr. OMIS)</span><input id="projekt"></div>' +
      '<div class="field"><span class="lbl">Vrsta</span><select id="vrsta"><option value="usluga">usluga (kupac)</option><option value="vlastita_proizvodnja">vlastita proizvodnja</option></select></div></div>' +
      '<div class="field"><span class="lbl">Rok kupca</span><input id="rok" type="date"></div><div class="note">Naziv naloga nastaje kao KUPAC_PROJEKT_BROJ; broj daje Hub.</div>',
      gumbi: [{ txt: "Novi kupac", on: function (bg) { noviKupac(function (k) { kupac = k; q("#odabrani", bg).innerHTML = "<b>" + esc(k.naziv) + "</b> " + esc(k.mjesto || ""); }); return false; } },
              { txt: "Otvori nalog", pri: true, on: async function (bg) {
                if (!kupac) { toast("odaberi kupca", true); return false; }
                var r = await api("/api/nalozi", { body: { kupac_id: kupac.id, projekt: q("#projekt", bg).value.trim(), vrsta: q("#vrsta", bg).value, rok_kupca: q("#rok", bg).value || null } });
                idi("#/nalog/" + r.id); } }],
      nakon: function (bg) {
        pretragaLista(q(".field", bg), async function (s) { return (await api("/api/kupci?q=" + encodeURIComponent(s) + "&limit=25")).kupci; },
          function (k) { return '<b>' + esc(k.naziv) + '</b> <span class="note">' + esc(k.mjesto || "") + (k.vrsta ? " · " + esc(k.vrsta) : "") + '</span>'; },
          function (k) { kupac = k; q("#odabrani", bg).innerHTML = "<b>" + esc(k.naziv) + "</b> " + esc(k.mjesto || "") + (k.rabat_materijal != null ? ' · rabat ' + k.rabat_materijal + ' % / ' + k.rabat_usluge + ' %' : ""); });
      } });
  }
  function noviKupac(cb) {
    dlg({ naslov: "Novi kupac (fizička osoba ili tvrtka koje nema u Pantheonu)", tijelo: '<div class="grid2"><div class="field"><span class="lbl">Ime / naziv</span><input id="ime"></div><div class="field"><span class="lbl">Mjesto</span><input id="mjesto"></div>' +
      '<div class="field"><span class="lbl">Telefon</span><input id="tel"></div><div class="field"><span class="lbl">E-mail</span><input id="mail"></div></div><div class="field"><span class="lbl">Vrsta</span><select id="vr"><option value="krajnji">krajnji kupac (fizička osoba)</option><option value="obrt">obrt</option><option value="tvrtka">tvrtka</option></select></div>',
      gumbi: [{ txt: "Spremi", pri: true, on: async function (bg) {
        var b = { ime: q("#ime", bg).value.trim(), mjesto: q("#mjesto", bg).value, telefon: q("#tel", bg).value, email: q("#mail", bg).value, vrsta: q("#vr", bg).value };
        try { var k = await api("/api/kupci", { body: b, tiho: true }); cb(k); }
        catch (e) { if (!confirm("Postoji sličan kupac (" + e.message.slice(0, 120) + "). Svejedno otvoriti novog?")) return false; b.svejedno = true; cb(await api("/api/kupci", { body: b })); } } }] });
  }
  function uvozCorpus() {
    dlg({ naslov: "Uvoz Corpusovog paketa (vlastita proizvodnja)", tijelo: '<div class="field"><span class="lbl">Mapa izvoza (na poslužitelju)</span><input id="mapa" placeholder="Z:\\CORPUS\\IZVOZ\\PROJEKT\\NESTING\\PROJEKT"></div>' +
      '<div class="grid2"><div class="field"><span class="lbl">Kupac (kratki naziv)</span><input id="kupac" placeholder="HUMER"></div><div class="field"><span class="lbl">Projekt</span><input id="projekt"></div></div><div id="rez"></div>',
      gumbi: [{ txt: "Provjeri (suho)", on: async function (bg) { var r = await api("/api/nalozi/uvoz-corpus", { body: { mapa: q("#mapa", bg).value, kupac_kratki: q("#kupac", bg).value, projekt: q("#projekt", bg).value, suho: true } });
                q("#rez", bg).innerHTML = '<div class="upoz ok">' + esc(JSON.stringify(r.uvoz || r).slice(0, 400)) + '</div>' + (r.upozorenja || []).map(function (u) { return '<div class="upoz">' + esc(u) + '</div>'; }).join(""); return false; } },
              { txt: "Uvezi", pri: true, on: async function (bg) { var r = await api("/api/nalozi/uvoz-corpus", { body: { mapa: q("#mapa", bg).value, kupac_kratki: q("#kupac", bg).value, projekt: q("#projekt", bg).value } }); idi("#/nalog/" + (r.nalog_id || r.id)); } }] });
  }

  // ---------------------------------------------------------------- ekran 2: unos naloga
  function nazivTip(t) { return t === "M" ? "MEL" : "ABS"; }
  function tipKoda(kod, klasa) { var k = (kod || "").toUpperCase(); if (/^MEL|0[,.]5\//.test(k) || (klasa || "").indexOf("0,5") === 0) return "M"; return "A"; }
  function trakeMaterijala(m) {
    /* popis traka s oznakama: ABS-ISTI, MEL-ISTI + sve što elementi materijala koriste + što je korisnik dodao */
    var lst = S.trake[m.id] || (S.trake[m.id] = [{ tip: "A", kod: "ABS-ISTI" }, { tip: "M", kod: "MEL-ISTI" }]);
    function ima(kod) { return lst.some(function (t) { return t.kod.toUpperCase() === (kod || "").toUpperCase(); }); }
    (m.elementi || []).forEach(function (e) { for (var i = 1; i <= 4; i++) { var kod = e["rub" + i + "_kod"]; if (kod && !ima(kod)) lst.push({ tip: tipKoda(kod, e["rub" + i + "_klasa"]), kod: kod, ident: e["rub" + i + "_traka"], naziv: e["rub" + i + "_naziv"] }); } });
    lst.forEach(function (t, i) { t.i = i; var nn = 0; for (var k = 0; k <= i; k++) if (lst[k].tip === t.tip) nn++; t.oznaka = t.tip + nn; t.boja = tok(BOJE[i % BOJE.length]); });
    (m.elementi || []).forEach(function (e) { e.rub = []; for (var i = 1; i <= 4; i++) { var kod = e["rub" + i + "_kod"]; var t = kod ? lst.filter(function (x) { return x.kod.toUpperCase() === kod.toUpperCase(); })[0] : null; e.rub.push(t ? t.i : null); if (t && !t.ident && e["rub" + i + "_traka"]) { t.ident = e["rub" + i + "_traka"]; t.naziv = e["rub" + i + "_naziv"]; } } });
    return lst;
  }
  function rubTekst(m, rub) { var lst = S.trake[m.id]; return { L: rub[0] == null ? "" : lst[rub[0]].kod, O: rub[1] == null ? "" : lst[rub[1]].kod, D: rub[2] == null ? "" : lst[rub[2]].kod, G: rub[3] == null ? "" : lst[rub[3]].kod }; }
  function skicaSvg(L, W, kom, rub, lst, naziv) {
    /* pravokutnik u odnosu mjera, okreće se kad je 2. mjera dulja; uski komadi blaže od stvarnog odnosa; rub1 = L, rub2 = O, rub3 = D, rub4 = G (duža1, kraća1, duža2, kraća2) */
    L = +L || 600; W = +W || 400;
    var vodoravno = W > L, r = Math.max(L, W) / Math.min(L, W), rr = Math.min(r, 3.2), maxW = 200, maxH = 190, bw, bh;
    if (vodoravno) { bw = maxW; bh = maxW / rr; if (bh > maxH) { bh = maxH; bw = maxH * rr; } } else { bh = maxH; bw = maxH / rr; if (bw > maxW) { bw = maxW; bh = maxW * rr; } }
    var bx = 160 - bw / 2, by = 118 - bh / 2;
    var lijevo = { x1: bx, y1: by, x2: bx, y2: by + bh, ox: -24, oy: 4 }, dolje = { x1: bx, y1: by + bh, x2: bx + bw, y2: by + bh, ox: 0, oy: 19 }, desno = { x1: bx + bw, y1: by, x2: bx + bw, y2: by + bh, ox: 24, oy: 4 }, gore = { x1: bx, y1: by, x2: bx + bw, y2: by, ox: 0, oy: -12 };
    var strane = vodoravno ? [gore, desno, dolje, lijevo] : [lijevo, dolje, desno, gore];   // duža strana (L) uvijek na rub 1 i 3
    var s = ['<rect x="' + bx + '" y="' + by + '" width="' + bw + '" height="' + bh + '" fill="' + tok("--field") + '" stroke="' + tok("--line") + '"/>'];
    strane.forEach(function (p, i) { var t = rub[i] == null ? null : lst[rub[i]]; s.push('<line x1="' + p.x1 + '" y1="' + p.y1 + '" x2="' + p.x2 + '" y2="' + p.y2 + '" stroke="' + (t ? t.boja : tok("--line")) + '" stroke-width="' + (t ? 7 : 1.5) + '" stroke-linecap="round"/>'); });
    strane.forEach(function (p, i) { var t = rub[i] == null ? null : lst[rub[i]], mx = (p.x1 + p.x2) / 2 + p.ox, my = (p.y1 + p.y2) / 2 + p.oy;
      s.push('<g class="tag-g" data-i="' + i + '"><rect x="' + (mx - 15) + '" y="' + (my - 12) + '" width="30" height="17" rx="4" fill="' + (t ? t.boja : tok("--surf")) + '" stroke="' + (t ? "none" : tok("--line")) + '" stroke-dasharray="' + (t ? 0 : "3 3") + '"/>' +
        '<text x="' + mx + '" y="' + my + '" text-anchor="middle" font-size="11" font-weight="700" font-family="IBM Plex Mono, monospace" fill="' + (t ? "#fff" : tok("--muted")) + '">' + (t ? t.oznaka : "+") + '</text></g>'); });
    s.push('<text x="160" y="' + (by + bh / 2 - 2) + '" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-weight="600" font-size="13" fill="' + tok("--ink") + '">' + L + " × " + W + '</text>');
    s.push('<text x="160" y="' + (by + bh / 2 + 12) + '" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="' + tok("--muted") + '">' + (kom || 1) + ' kom' + (r > 3.2 ? " · nije u mjerilu" : "") + '</text>');
    if (naziv) s.push('<text x="160" y="16" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="' + tok("--muted") + '">' + esc(naziv) + '</text>');
    return '<svg id="skica" viewBox="0 0 320 236">' + s.join("") + '</svg>';
  }

  function skicaMini(L, W, kom, rub, lst) {
    /* varijanta B (Igor, 17. 9.): mala daska uz mjere, velike kućice rubova na pravim stranama; rub 0 = L, 1 = O, 2 = D, 3 = G (duža1, kraća1, duža2, kraća2) */
    L = +L || 600; W = +W || 400;
    var vodoravno = W > L, r = Math.min(Math.max(L, W) / Math.min(L, W), 3.2), bw, bh;
    if (vodoravno) { bw = 196; bh = Math.max(60, Math.round(196 / r)); } else { bh = 190; bw = Math.max(60, Math.round(190 / r)); }
    var poz = vodoravno ? ["gore", "desno", "dolje", "lijevo"] : ["lijevo", "dolje", "desno", "gore"];   // duža strana (L) uvijek rub 1 i 3
    var kut = { lijevo: "grid-area:1/1/4/2", desno: "grid-area:1/3/4/4", gore: "grid-area:1/2/2/3", dolje: "grid-area:3/2/4/3" };
    var ime = ["L", "O", "D", "G"];
    var gumbi = [0, 1, 2, 3].map(function (i) { var t = rub[i] == null ? null : lst[rub[i]]; return '<button type="button" class="tag-g' + (t ? " puna" : "") + '" data-i="' + i + '" style="' + kut[poz[i]] + (t ? ";background:" + t.boja : "") + '" title="rub ' + ime[i] + '">' + (t ? t.oznaka : "+") + '<small>' + ime[i] + '</small></button>'; }).join("");
    var crte = [0, 1, 2, 3].map(function (i) { var t = rub[i] == null ? null : lst[rub[i]]; if (!t) return ""; var p = poz[i]; return '<i style="position:absolute;background:' + t.boja + ';' + (p === "lijevo" ? "left:0;top:0;bottom:0;width:6px" : p === "desno" ? "right:0;top:0;bottom:0;width:6px" : p === "gore" ? "top:0;left:0;right:0;height:6px" : "bottom:0;left:0;right:0;height:6px") + '"></i>'; }).join("");
    /* mjere zalijepljene na rub kojem pripadaju (Igor): L uz dužu stranu, W uz kraću; bez teksta u sredini */
    var dimL = vodoravno ? '<span class="dim dolje">' + L + '</span>' : '<span class="dim lijevo">' + L + '</span>';
    var dimW = vodoravno ? '<span class="dim lijevo">' + W + '</span>' : '<span class="dim dolje">' + W + '</span>';
    return '<div id="skica" class="skm">' + gumbi + '<div class="dsk" style="grid-area:2/2/3/3;width:' + bw + 'px;height:' + bh + 'px" title="' + L + ' × ' + W + ' · ' + (kom || 1) + ' kom">' + crte + dimL + dimW + '</div></div>';
  }
  ekrani.nalog = async function (r) { return (ekrani["nalog_" + r.pod] || ekrani.nalog_unos)(r); };
  ekrani.nalog_unos = async function (r) {
    var d = S.nalog = await api("/api/nalog/" + r.id);
    if (!S.nm || !d.materijali.some(function (m) { return m.id === S.nm; })) S.nm = d.materijali.length ? d.materijali[0].id : null;
    var m = d.materijali.filter(function (x) { return x.id === S.nm; })[0] || null;
    var lst = m ? trakeMaterijala(m) : [];
    if (S.aktivna[S.nm] == null || S.aktivna[S.nm] >= lst.length) S.aktivna[S.nm] = 0;
    var uredivo = d.status === "unos" || d.status === "ponuda";
    var tab = S.unosTab || "elementi", optSve = m ? await api("/api/nalog/" + d.id + "/optimizacija") : [], opt = optSve.filter(function (o) { return m && o.nalog_materijal_id === m.id; });
    var optSt = opt.length && opt[0].treba ? (opt[0].potvrdjeno ? '<span class="tag ok">potvrđeno</span>' : '<span class="tag warn">čeka potvrdu</span>') : "";
    var forma = S.forma || (S.forma = { L: "", W: "", kom: 1, naziv: "", napomena: "", rub: [null, null, null, null] });
    var sel = S.odabran != null && m ? m.elementi.filter(function (e) { return e.id === S.odabran; })[0] : null;
    var sk = sel ? skicaMini(sel.L, sel.W, sel.kom, sel.rub, lst) : skicaMini(forma.L, forma.W, forma.kom, forma.rub, lst);
    var matHtml = d.materijali.map(function (x) {
      return '<div class="mat' + (x.id === S.nm ? " on" : "") + '" data-nm="' + x.id + '"><div class="row"><b>' + esc(x.naziv_kratki || x.naziv_ulaz || "?") + '</b>' +
        (x.provjeri || !x.materijal_id ? '<span class="tag warn">za potvrdu</span>' : "") + (x.put ? '<span class="tag ' + (x.put === "nesting" ? "nest" : "pila") + '">' + esc(x.put) + '</span>' : "") + '</div>' +
        '<div class="m">' + esc(x.ident || "") + ' · ' + x.elemenata + ' el / ' + x.komada + ' kom · ' + n(x.m2, 2) + ' m²' + (x.ploca_L ? ' · restl ' + x.ploca_L + '×' + x.ploca_W : "") + (x.god ? ' · god' : "") + '</div></div>';
    }).join("");
    var elHtml = m ? m.elementi.map(function (e) {
      return '<tr class="klik' + (e.id === S.odabran ? " sel" : "") + '" data-e="' + e.id + '"><td>' + esc(e.naziv || "") + (e.provjeri ? ' <span class="tag warn">?</span>' : "") + (e.niz ? ' <span class="tag info">niz ' + esc(e.niz) + '</span>' : "") + (e.ljepljenje ? ' <span class="tag info">sloj ' + esc(e.ljepljenje) + '</span>' : "") + '</td>' +
        '<td class="r num">' + mm(e.L) + '</td><td class="r num">' + mm(e.W) + '</td><td class="r num">' + e.kom + '</td>' +
        e.rub.map(function (ri, k) { var t = ri == null ? null : lst[ri]; return '<td><button class="cell' + (t ? " puna" : "") + '" data-rub="' + e.id + ':' + k + '" style="' + (t ? "background:" + t.boja : "") + '">' + (t ? t.oznaka : "+") + '</button></td>'; }).join("") +
        '<td class="note">' + esc(e.napomena_rez || e.napomena || "") + '</td><td class="r">' + (uredivo ? '<button class="btn sm" data-del="' + e.id + '">×</button>' : "") + '</td></tr>';
    }).join("") : "";
    var trHtml = lst.map(function (t) {
      return '<div class="tr-row' + (t.i === S.aktivna[S.nm] ? " on" : "") + '" data-t="' + t.i + '"><span class="oz" style="background:' + t.boja + '">' + t.oznaka + '</span><span class="tag ' + (t.tip === "A" ? "abs" : "mel") + '">' + nazivTip(t.tip) + '</span>' +
        '<span class="nm" title="' + esc(t.kod) + '">' + esc(t.naziv || t.kod) + (t.ident ? ' <span class="note">' + esc(t.ident) + '</span>' : "") + '</span>' + (t.i === S.aktivna[S.nm] ? '<span class="note">aktivna</span>' : "") + (t.i > 1 ? '<button class="x" data-ukloni="' + t.i + '">×</button>' : "") + '</div>';
    }).join("");
    var zp = d.za_potvrdu.map(function (z, i) {
      return '<div class="upoz"><b>' + esc(z.tekst || z.naziv_ulaz || "") + '</b> <span class="note">' + esc(z.vrsta) + (z.debljina_ulaz ? " · " + z.debljina_ulaz + " mm" : "") + '</span><div class="row" style="margin-top:6px">' +
        (z.kandidati || []).slice(0, 4).map(function (k) { return '<button class="btn sm" data-potvrdi="' + i + '" data-ident="' + esc(k.ident) + '">' + esc(k.ident) + ' ' + esc((k.naziv || "").slice(0, 34)) + '</button>'; }).join("") +
        '<button class="btn sm ghost" data-potvrdi="' + i + '" data-ident="">drugi…</button></div></div>';
    }).join("");
    var akcije = '<span class="note">Status</span><select id="status" class="tbtn">' + STATUSI.map(function (s) { return '<option value="' + s[0] + '"' + (s[0] === d.status ? " selected" : "") + '>' + esc(s[1]) + '</option>'; }).join("") + '</select>' +
      '<a class="tbtn" href="#/nalog/' + d.id + '/dogadjaji">Događaji</a><a class="tbtn pri" href="#/nalog/' + d.id + '/optimizacija">Optimizacija →</a>';
    var dis = (!m || !uredivo) ? " disabled" : "";
    ljuska({ crumb: 'Nalozi / <b>' + esc(d.naziv) + '</b> · ' + esc(d.kupac_naziv || "") + ' · ' + esc((d.datum || "").slice(0, 10)) + (d.ponuda_pantheon ? ' · ponuda ' + esc(d.ponuda_pantheon) : ""), koraci: koraci(d), akcije: akcije, rail: "nalozi", cls: "c3",
      sadrzaj:
        '<div class="col"><div class="pane" style="flex:1"><div class="hd"><b>Materijali</b><span class="grow"></span>' + (uredivo ? '<button class="btn sm" id="btnMat">+ Materijal</button><button class="btn sm" id="btnUvoz">Uvoz datoteke</button>' : "") + '</div><div class="bd tight">' + (matHtml || '<div class="note" style="padding:12px">nema materijala — dodaj ga ili uvezi CPW / CSV</div>') + '</div></div>' +
          (m ? '<div class="pane"><div class="hd"><b>' + esc(m.naziv_kratki || m.naziv_ulaz || "") + '</b><span class="grow"></span>' + (uredivo ? '<button class="btn sm" id="btnMatUredi">…</button>' : "") + '</div><div class="bd"><div class="kv"><b>Ident</b><span>' + esc(m.ident || "—") + '</span><b>Naziv</b><span>' + esc(m.naziv || m.naziv_ulaz || "") + '</span><b>Debljina</b><span>' + n(m.debljina || m.debljina_ulaz, 0) + ' mm</span><b>Winstore</b><span>' + esc(m.winstore_kod || "—") + '</span><b>Put</b><span>' + esc(m.put || m.put_prijedlog || "—") + '</span><b>Zadana traka</b><span>' + esc(m.traka_zadana) + '</span><b>Obrub</b><span>' + n(m.obrub != null ? m.obrub : m.obrub_zadano, 0) + ' mm' + (m.obrub != null ? "" : ' <span class="note">zadano</span>') + '</span></div></div></div>' : "") + '</div>' +
        '<div class="col"><div class="pane"><div class="hd"><b>Element</b><span class="note">' + (sel ? "uređivanje — Esc za novi" : "novi — Enter prihvati") + '</span><span class="grow"></span>' + (m && uredivo ? '<button class="btn sm" id="btnGrupe" title="mjera za rezanje, majke, sklopovi">Grupe</button>' : "") + '</div>' +
          '<div class="bd"><div class="unos3">' +
          '<div class="zona z-mjere"><span class="zlbl">Mjere</span>' +
          '<div class="row nw"><div class="field fx"><span class="lbl">Dužina L</span><input class="big" id="fL" inputmode="numeric" value="' + esc(sel ? sel.L : forma.L) + '"' + dis + '></div><span class="puta">×</span><div class="field fx"><span class="lbl">Širina W</span><input class="big" id="fW" inputmode="numeric" value="' + esc(sel ? sel.W : forma.W) + '"' + dis + '></div><div class="field fk"><span class="lbl">Kom</span><input class="big" id="fK" inputmode="numeric" value="' + esc(sel ? sel.kom : forma.kom) + '"' + dis + '></div></div>' +
          '<div class="row nw"><div class="field" style="width:162px"><span class="lbl">Naziv</span><input id="fN" value="' + esc(sel ? sel.naziv || "" : forma.naziv) + '"' + dis + '></div><div class="field" style="width:118px"><span class="lbl">Napomena</span><input id="fP" maxlength="60" value="' + esc(sel ? sel.napomena || "" : forma.napomena) + '"' + dis + '></div></div>' +
          '<div class="row">' + (uredivo && m ? '<button class="btn pri" id="btnPrihvati">' + (sel ? "Spremi izmjene" : "Prihvati (Enter)") + '</button>' + (sel ? '<button class="btn" id="btnNoviEl">Novi element (Esc)</button>' : "") : "") + '</div></div>' +
          '<div class="zona z-rub"><span class="zlbl">Kantiranje <span class="note">klik = aktivna traka · dvoklik na dasku = sva 4</span></span><div id="skicaBox">' + sk + '</div><div class="row"><button class="btn sm" id="btnSviA">svi rubovi</button><button class="btn sm" id="btnBez">bez trake</button></div></div>' +
          '<div class="zona z-trake"><span class="zlbl">Traka <span class="note">klik = aktivna</span></span><div id="trake">' + (trHtml || '<div class="note">odaberi materijal</div>') + '</div>' + (m && uredivo ? '<div class="row"><button class="btn sm" id="btnA">+ ABS</button><button class="btn sm" id="btnM">+ MEL</button></div>' : "") + '</div>' +
          '</div></div></div>' +
          '<div class="pane" style="flex:1"><div class="hd tabs-hd"><div class="tabs"><button class="tb' + (tab === "elementi" ? " on" : "") + '" data-tab="elementi">Elementi <span class="note">' + (m ? m.elemenata + " el / " + m.komada + " kom / " + n(m.m2, 2) + " m²" : "") + '</span></button><button class="tb' + (tab === "slaganje" ? " on" : "") + '" data-tab="slaganje">Optimizacija ' + optSt + '</button></div><span class="grow"></span>' +
          (tab === "slaganje" && m && opt.length && opt[0].treba ? '<button class="btn sm pri" id="btnOptim" title="nova zadana optimizacija (realna za pilu) + Hub rezerva">Optimiziraj</button>' : "") + '</div>' +
          (tab === "elementi" ? '<div class="bd tight"><table><thead><tr><th>Naziv</th><th class="r">L</th><th class="r">W</th><th class="r">Kom</th><th>L</th><th>O</th><th>D</th><th>G</th><th>Napomena</th><th></th></tr></thead><tbody>' + (elHtml || '<tr><td colspan="10" class="note">nema elemenata</td></tr>') + '</tbody></table></div>'
            : '<div class="bd">' + (m ? (Hub.optBanner(d, opt, true) + '<div class="slag">' + Hub.optBlok(d, opt) + '</div>' + (opt.length && opt[0].treba ? Hub.legendaSheme() : "")) : '<div class="note">odaberi materijal</div>') + '</div>') + '</div></div>' +
        '<div class="col"><div class="pane"><div class="hd"><b>Za potvrdu</b> ' + (d.za_potvrdu.length ? '<span class="tag warn">' + d.za_potvrdu.length + '</span>' : '<span class="tag ok">0</span>') + '</div><div class="bd">' + (zp || '<div class="note">sve prepoznato</div>') + '</div></div>' +
          '<div class="pane"><div class="hd"><b>Nalog</b></div><div class="bd"><div class="kv"><b>Kupac</b><span>' + esc(d.kupac_naziv || "") + '</span><b>Rabat</b><span>' + n(d.rabat_materijal, 0) + ' % / ' + n(d.rabat_usluge, 0) + ' %</span><b>Kerf</b><span>' + n(d.kerf, 0) + ' mm</span><b>Rok</b><span>' + esc(d.rok_obecan || d.rok_kupca || "—") + '</span><b>Napomena</b><span>' + esc(d.napomena || "") + '</span></div><div class="row" style="margin-top:8px"><button class="btn sm" id="btnNalogUredi">Zaglavlje naloga…</button></div></div></div></div>',
      foot: kpi(d.sazetak.materijala, "materijala") + kpi(d.sazetak.elemenata + " / " + d.sazetak.komada, "elemenata / kom") + kpi(n(d.sazetak.m2, 2), "m² neto") + kpi(d.sazetak.za_potvrdu, "za potvrdu") + '<span class="grow"></span><span class="note">' + esc(statusNaziv(d.status)) + '</span>' });

    // ---- događaji na ekranu
    function spremiRub(e) { return api("/api/nalog/element/" + e.id, { method: "PUT", body: { rubovi: rubTekst(m, e.rub) } }); }
    qa(".mat[data-nm]").forEach(function (x) { x.onclick = function () { S.nm = +x.dataset.nm; S.odabran = null; render(); }; });
    qa("[data-tab]").forEach(function (b) { b.onclick = function () { S.unosTab = b.dataset.tab; render(); }; });
    if (tab === "slaganje") { Hub.veziOpt(d, opt); if (q("#btnOptim")) q("#btnOptim").onclick = async function () { this.disabled = true; this.textContent = "računam…"; await api("/api/nalog/" + d.id + "/optimizacija/pripremi", { body: { nm: m.id, svjeze: true } }); render(); }; }
    qa("tr[data-e]").forEach(function (x) { x.onclick = function (e) { if (e.target.closest("button")) return; S.odabran = S.odabran === +x.dataset.e ? null : +x.dataset.e; render(); }; });
    qa("[data-del]").forEach(function (b) { b.onclick = async function () { if (!confirm("Obrisati element?")) return; await api("/api/nalog/element/" + b.dataset.del + "?tko=" + S.korisnik, { method: "DELETE" }); S.odabran = null; render(); }; });
    qa("[data-t]").forEach(function (x) { x.onclick = function (e) { if (e.target.closest("[data-ukloni]")) return; S.aktivna[S.nm] = +x.dataset.t; render(); }; });
    qa("[data-ukloni]").forEach(function (b) { b.onclick = function () { var i = +b.dataset.ukloni; if ((m.elementi || []).some(function (e) { return e.rub.indexOf(i) >= 0; })) { toast("traka je na elementima — prvo je makni s rubova", true); return; } lst.splice(i, 1); S.aktivna[S.nm] = 0; render(); }; });
    qa("[data-rub]").forEach(function (b) { b.onclick = async function () { if (!uredivo) return; var p = b.dataset.rub.split(":"), e = m.elementi.filter(function (x) { return x.id === +p[0]; })[0], k = +p[1]; e.rub[k] = e.rub[k] === S.aktivna[S.nm] ? null : S.aktivna[S.nm]; await spremiRub(e); render(); }; });
    function osvjeziSkicu() { forma.L = q("#fL").value; forma.W = q("#fW").value; forma.kom = q("#fK").value; forma.naziv = q("#fN").value; forma.napomena = q("#fP").value; q("#skicaBox").innerHTML = skicaMini(forma.L, forma.W, forma.kom, forma.rub, lst); veziSkicu(); }
    function veziSkicu() {
      var skica = q("#skica"); if (!skica) return;
      skica.onclick = async function (ev) { var g = ev.target.closest(".tag-g"); if (!g) return; var i = +g.dataset.i; if (sel) { if (!uredivo) return; sel.rub[i] = sel.rub[i] === S.aktivna[S.nm] ? null : S.aktivna[S.nm]; await spremiRub(sel); render(); } else { forma.rub[i] = forma.rub[i] === S.aktivna[S.nm] ? null : S.aktivna[S.nm]; osvjeziSkicu(); } };
      skica.ondblclick = async function (ev) { if (ev.target.closest(".tag-g")) return; var cilj = sel || forma, a = S.aktivna[S.nm], svi = cilj.rub.every(function (x) { return x === a; }); cilj.rub = [0, 1, 2, 3].map(function () { return svi ? null : a; }); if (sel) { if (!uredivo) return; await spremiRub(sel); render(); } else osvjeziSkicu(); };
    }
    veziSkicu();
    ["#fL", "#fW", "#fK", "#fN"].forEach(function (id) { var el = q(id); if (el && !sel) el.oninput = osvjeziSkicu; });
    q("#btnSviA").onclick = function () { var cilj = sel || forma; cilj.rub = [0, 1, 2, 3].map(function () { return S.aktivna[S.nm]; }); if (sel) spremiRub(sel).then(render); else osvjeziSkicu(); };
    q("#btnBez").onclick = function () { var cilj = sel || forma; cilj.rub = [null, null, null, null]; if (sel) spremiRub(sel).then(render); else osvjeziSkicu(); };
    async function prihvati() {
      var L = +q("#fL").value, W = +q("#fW").value, kom = +q("#fK").value || 1;
      if (!(L > 0 && W > 0)) { toast("upiši L i W", true); return; }
      var body = { L: L, W: W, kom: kom, naziv: q("#fN").value.trim() || null, napomena: q("#fP").value.trim() || null, rubovi: rubTekst(m, (sel || forma).rub) };
      if (sel) { await api("/api/nalog/element/" + sel.id, { method: "PUT", body: body }); S.odabran = null; }
      else { await api("/api/nalog/materijal/" + m.id + "/elementi", { body: body }); forma.L = ""; forma.W = ""; forma.kom = 1; forma.naziv = ""; forma.napomena = ""; }
      await render(); var f = q("#fL"); if (f) f.focus();
    }
    if (q("#btnPrihvati")) q("#btnPrihvati").onclick = prihvati;
    if (q("#btnNoviEl")) q("#btnNoviEl").onclick = function () { S.odabran = null; render(); };
    qa("#fL,#fW,#fK,#fN,#fP").forEach(function (el) { el.onkeydown = function (e) { if (e.key === "Enter") { e.preventDefault(); prihvati(); } if (e.key === "Escape" && sel) { S.odabran = null; render(); } }; });
    if (q("#btnA")) q("#btnA").onclick = function () { dodajTraku("A", m, lst); };
    if (q("#btnM")) q("#btnM").onclick = function () { dodajTraku("M", m, lst); };
    if (q("#btnMat")) q("#btnMat").onclick = function () { dodajMaterijal(d); };
    if (q("#btnUvoz")) q("#btnUvoz").onclick = function () { uvozDatoteke(d); };
    if (q("#btnMatUredi")) q("#btnMatUredi").onclick = function () { urediMaterijal(d, m); };
    if (q("#btnGrupe")) q("#btnGrupe").onclick = function () { grupe(d); };
    q("#btnNalogUredi").onclick = function () { urediNalog(d); };
    qa("[data-potvrdi]").forEach(function (b) { b.onclick = function () { potvrdi(d, d.za_potvrdu[+b.dataset.potvrdi], b.dataset.ident); }; });
    q("#status").onchange = async function () { var novi = this.value, selEl = this; if (novi === d.status) return;
      if (novi === "potvrdjeno") { selEl.value = d.status; return kupacPotvrdio(d); }
      try { var rr = await api("/api/nalog/" + d.id + "/status", { body: { status: novi } }); if (rr.skladiste && rr.skladiste.upozorenja.length) toast("Skladište: " + rr.skladiste.upozorenja.join("; "), true); idi("#/nalog/" + d.id + (novi === "skladiste" ? "/skladiste" : novi === "pila_nesting" ? "/proizvodnja" : "")); }
      catch (e) { selEl.value = d.status; } };
    if (!sel) { var f0 = q("#fL"); if (f0 && document.activeElement === document.body) f0.focus(); }
  };

  function dodajTraku(tip, m, lst) {
    dlg({ naslov: "Dodaj " + nazivTip(tip) + " traku", tijelo: '<div class="field"><span class="lbl">Traka iz šifrarnika</span><input placeholder="dekor, ident…"><div class="lista"></div></div><div class="note">Oznaka (' + tip + 'n) se upisuje uz rub umjesto cijelog naziva; u ponudu, na etiketu i u CPW ide traka iz šifrarnika.</div>',
      nakon: function (bg, zatvori) {
        pretragaLista(q(".field", bg), async function (s) { var r = await api("/api/sifrarnik/trake?q=" + encodeURIComponent(s) + "&limit=40"); return (r.trake || r).filter(function (t) { return tip === "M" ? /^0,5/.test(t.klasa || "") : !/^0,5/.test(t.klasa || ""); }); },
          function (t) { return '<span class="mono">' + esc(t.ident) + '</span> ' + esc(t.naziv) + ' <span class="note">' + esc(t.klasa || "") + '</span>'; },
          function (t) { if (!lst.some(function (x) { return x.kod.toUpperCase() === t.naziv.toUpperCase(); })) lst.push({ tip: tip, kod: t.naziv, ident: t.ident, naziv: t.naziv }); S.aktivna[m.id] = lst.length - 1; zatvori(); render(); });
      } });
  }
  function dodajMaterijal(d) {
    dlg({ naslov: "Dodaj materijal", tijelo: '<div class="field"><span class="lbl">Materijal iz šifrarnika (naziv, ident, Winstore kod)</span><input placeholder="bijeli nk 18…"><div class="lista"></div></div><div class="row"><span class="lbl">Zadana traka</span><select id="tz"><option>ABS-ISTI</option><option>MEL-ISTI</option><option>ABS-ISTI 2mm</option></select></div>',
      nakon: function (bg, zatvori) {
        pretragaLista(q(".field", bg), async function (s) { return (await api("/api/sifrarnik/materijali?q=" + encodeURIComponent(s) + "&limit=40")).materijali; },
          function (x) { return '<span class="mono">' + esc(x.ident) + '</span> ' + esc(x.naziv) + ' <span class="note">' + (x.debljina ? x.debljina + " mm" : "") + (x.winstore_kod ? " · " + esc(x.winstore_kod) : "") + (x.stanje_kom != null ? " · " + x.stanje_kom + " pl." : "") + '</span>'; },
          async function (x) { var r = await api("/api/nalog/" + d.id + "/materijali", { body: { ident: x.ident, traka_zadana: q("#tz", bg).value } }); S.nm = (r.materijal || r).id; zatvori(); render(); });
      } });
  }
  function urediMaterijal(d, m) {
    var ob0 = m.obrub != null ? m.obrub : m.obrub_zadano;       // obrub ploče za optimizaciju (Igor, 17. 9.): zadano 10 mm, radne ploče / stol / zidne 0
    dlg({ naslov: "Materijal " + (m.naziv_kratki || ""), tijelo: '<div class="grid2"><div class="field"><span class="lbl">Put</span><select id="put"><option value="">— (Hub predlaže)</option><option value="pila"' + (m.put === "pila" ? " selected" : "") + '>pila</option><option value="nesting"' + (m.put === "nesting" ? " selected" : "") + '>nesting</option></select></div>' +
      '<div class="field"><span class="lbl">God</span><select id="god"><option value="0"' + (!m.god ? " selected" : "") + '>ne</option><option value="1"' + (m.god ? " selected" : "") + '>da</option></select></div>' +
      '<div class="field"><span class="lbl">Restl / vlastita ploča L</span><input id="pL" value="' + (m.ploca_L || "") + '"></div><div class="field"><span class="lbl">W</span><input id="pW" value="' + (m.ploca_W || "") + '"></div>' +
      '<div class="field"><span class="lbl">Zadana traka</span><select id="tz">' + ["ABS-ISTI", "MEL-ISTI", "ABS-ISTI 2mm"].map(function (x) { return '<option' + (x === m.traka_zadana ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select></div><div class="field"><span class="lbl">Napomena</span><input id="nap" value="' + esc(m.napomena || "") + '"></div>' +
      '<div class="field"><span class="lbl">Obrub (rubljenje) mm</span><input id="obrub" inputmode="decimal" value="' + n(ob0) + '"></div><div class="field"><span class="lbl">&nbsp;</span><span class="note" style="padding-top:8px">' + (m.obrub != null ? "upisano za ovaj materijal — prazno = zadano " + n(m.obrub_zadano, 0) + " mm" : "zadano " + n(m.obrub_zadano, 0) + " mm" + (m.obrub_zadano ? "" : " (radne ploče, ploče stola, zidne obloge)")) + '</span></div></div>',
      gumbi: [{ txt: "Obriši materijal", on: async function () { if (!confirm("Obrisati materijal i njegove elemente?")) return false; await api("/api/nalog/materijal/" + m.id + "?tko=" + S.korisnik, { method: "DELETE" }); S.nm = null; render(); } },
              { txt: "Spremi", pri: true, on: async function (bg) { await api("/api/nalog/materijal/" + m.id, { method: "PUT", body: { put: q("#put", bg).value || null, god: +q("#god", bg).value, ploca_L: +q("#pL", bg).value || null, ploca_W: +q("#pW", bg).value || null, traka_zadana: q("#tz", bg).value, napomena: q("#nap", bg).value, obrub: obrubIz(q("#obrub", bg).value) } }); render(); } }] });
    function obrubIz(v) { v = String(v).trim().replace(",", "."); if (v === "") return null; var x = parseFloat(v); return isNaN(x) || x === ob0 ? (m.obrub != null ? m.obrub : undefined) : x; }
  }
  function urediNalog(d) {
    dlg({ naslov: "Zaglavlje naloga", tijelo: '<div class="grid2"><div class="field"><span class="lbl">Naziv</span><input id="naziv" value="' + esc(d.naziv) + '"></div><div class="field"><span class="lbl">Kerf (mm)</span><input id="kerf" value="' + (d.kerf || 16) + '"></div>' +
      '<div class="field"><span class="lbl">Rabat materijal %</span><input id="rm" value="' + (d.rabat_materijal == null ? "" : d.rabat_materijal) + '"></div><div class="field"><span class="lbl">Rabat usluge %</span><input id="ru" value="' + (d.rabat_usluge == null ? "" : d.rabat_usluge) + '"></div>' +
      '<div class="field"><span class="lbl">Rok kupca</span><input id="rk" type="date" value="' + esc(d.rok_kupca || "") + '"></div><div class="field"><span class="lbl">Prioritet</span><select id="pr"><option value="">—</option>' + ["hitno", "visok", "normalan"].map(function (x) { return '<option' + (x === d.prioritet ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select></div></div>' +
      '<div class="field"><span class="lbl">Napomena</span><textarea id="nap" rows="2">' + esc(d.napomena || "") + '</textarea></div>',
      gumbi: [{ txt: "Spremi", pri: true, on: async function (bg) { await api("/api/nalog/" + d.id, { method: "PUT", body: { naziv: q("#naziv", bg).value, kerf: +q("#kerf", bg).value || null, rabat_materijal: q("#rm", bg).value === "" ? null : +q("#rm", bg).value, rabat_usluge: q("#ru", bg).value === "" ? null : +q("#ru", bg).value, rok_kupca: q("#rk", bg).value || null, prioritet: q("#pr", bg).value || null, napomena: q("#nap", bg).value } }); render(); } }] });
  }
  function uvozDatoteke(d) {
    /* više datoteka odjednom (Igor, 17. 9.: kupci pošalju 5–7 CPW-ova, jedan po jedan je naporno): odabir s Ctrl / Shift ili povlačenje u okvir,
       Hub ih uvozi redom u isti nalog i uz svaku javi što je ušlo; ista datoteka drugi put se preskače (hash), greška jedne ne zaustavlja ostale. */
    var ODB = /\.(cpw|pnl|csv)$/i, lista = [], radi = false;
    function vel(b) { return b > 1048576 ? n(b / 1048576, 1) + " MB" : Math.max(1, Math.round(b / 1024)) + " kB"; }
    var h = dlg({ naslov: "Uvoz datoteka u nalog", tijelo:
      '<label class="drop" id="drop"><input type="file" id="dat" multiple accept=".cpw,.CPW,.pnl,.PNL,.csv,.CSV"><b>Odaberi datoteke</b> ili ih povuci ovamo<span class="note">CPW (kupčev PPW, Corpus), PNL (PanelWizard nalog), PPNEST CSV — više odjednom (Ctrl / Shift)</span></label>' +
      '<div class="uvoz-lista" id="ulista"></div>' +
      '<div class="field"><span class="lbl">Izvor za .CPW datoteke</span><select id="izvor"><option value="kupac_ppw">kupčev PPW (.cpw)</option><option value="cpw">PanelWizard (.pnl / .cpw)</option></select></div>' +
      '<div class="note">Sve datoteke idu u ovaj nalog; materijali i trake prolaze kroz šifrarnik, nesigurno ide „za potvrdu“. Ista datoteka drugi put se preskače.</div>',
      gumbi: [{ txt: "Uvezi", pri: true, on: async function (bg) { await uvezi(bg); return false; } }],
      nakon: function (bg) {
        var inp = q("#dat", bg), drop = q("#drop", bg);
        inp.onchange = function () { dodaj(bg, inp.files); inp.value = ""; };
        ["dragenter", "dragover"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("on"); }); });
        ["dragleave", "drop"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove("on"); }); });
        drop.addEventListener("drop", function (e) { dodaj(bg, e.dataTransfer.files); });
        prikazi(bg);
      } });
    function dodaj(bg, files) {
      Array.prototype.forEach.call(files || [], function (f) {
        if (lista.some(function (x) { return x.f.name === f.name && x.f.size === f.size; })) return;
        lista.push({ f: f, st: ODB.test(f.name) ? "ceka" : "krivo", poruka: ODB.test(f.name) ? "" : "nije .CPW / .PNL / .CSV — preskače se" });
      });
      prikazi(bg);
    }
    function prikazi(bg) {
      var ikona = { ceka: "·", radi: "…", ok: "✓", presk: "=", greska: "✕", krivo: "✕" };
      q("#ulista", bg).innerHTML = lista.map(function (x, i) {
        return '<div class="uf ' + x.st + '"><span class="ik">' + ikona[x.st] + '</span><span class="grow ime" title="' + esc(x.f.name) + '">' + esc(x.f.name) + '</span><span class="note">' + (x.poruka ? esc(x.poruka) : vel(x.f.size)) + '</span>' +
          (!radi && (x.st === "ceka" || x.st === "krivo") ? '<button class="x" data-ukloni="' + i + '" title="makni s popisa">×</button>' : "") + '</div>';
      }).join("");
      qa("[data-ukloni]", bg).forEach(function (b) { b.onclick = function (e) { e.preventDefault(); lista.splice(+b.dataset.ukloni, 1); prikazi(bg); }; });
      var cekaju = lista.filter(function (x) { return x.st === "ceka"; }).length, gb = q('[data-g="0"]', bg);
      q("#drop", bg).classList.toggle("mali", lista.length > 0);
      if (!gb) return;
      if (radi) { var gotovo = lista.filter(function (x) { return x.st === "ok" || x.st === "presk" || x.st === "greska"; }).length, ukupno = gotovo + lista.filter(function (x) { return x.st === "ceka" || x.st === "radi"; }).length; gb.textContent = "Uvozim " + Math.min(gotovo + 1, ukupno) + " / " + ukupno + "…"; gb.disabled = true; return; }
      gb.textContent = cekaju > 1 ? "Uvezi " + cekaju + (cekaju % 10 >= 2 && cekaju % 10 <= 4 && (cekaju % 100 < 12 || cekaju % 100 > 14) ? " datoteke" : " datoteka") : "Uvezi"; gb.disabled = !cekaju;
    }
    async function uvezi(bg) {
      var za = lista.filter(function (x) { return x.st === "ceka"; });
      if (!za.length) { toast(lista.length ? "nema datoteka za uvoz" : "odaberi datoteke", true); return; }
      radi = true;
      var el = 0, pot = 0, ok = 0, greske = 0;
      for (var i = 0; i < za.length; i++) {
        var x = za[i]; x.st = "radi"; x.poruka = "uvozim…"; prikazi(bg);
        try {
          var fd = new FormData(); fd.append("datoteka", x.f);
          var r = await api("/api/nalog/" + d.id + "/uvoz?izvor=" + q("#izvor", bg).value + "&tko=" + S.korisnik, { body: fd, tiho: true });
          if (r.preskoceno) { x.st = "presk"; x.poruka = "već uvezena — preskočeno"; }
          else { var zp = (r.za_potvrdu_materijal || 0) + (r.za_potvrdu_rub || 0); x.st = "ok"; ok++; el += r.elementi || 0; pot += zp; x.poruka = (r.elementi || 0) + " el / " + (r.komada || 0) + " kom" + (zp ? " · za potvrdu " + zp : ""); }
        } catch (e) { if (e && e.message === "prijava") { radi = false; return; } x.st = "greska"; x.poruka = e.message || "greška"; greske++; }
        prikazi(bg);
      }
      radi = false; S.nm = null;
      toast("Uvezeno " + ok + " od " + za.length + (za.length % 10 >= 2 && za.length % 10 <= 4 && (za.length % 100 < 12 || za.length % 100 > 14) || za.length % 10 === 1 && za.length % 100 !== 11 ? " datoteke" : " datoteka") + ": " + el + " el" + (pot ? ", za potvrdu " + pot : "") + (greske ? " · greška u " + greske : ""), greske > 0);
      if (!greske) { h.zatvori(); render(); return; }
      q(".ft", bg).innerHTML = '<span class="note grow" style="align-self:center">Neke datoteke nisu uvezene — ostale su u nalogu.</span><button class="btn pri" id="uGotovo">Zatvori</button>';
      q("#uGotovo", bg).onclick = function () { h.zatvori(); render(); };
    }
  }
  function potvrdi(d, z, ident) {
    var traka = z.vrsta === "traka";
    async function upisi(id) {
      if (traka) await api("/api/nalog/materijal/" + z.nalog_materijal_id + "/potvrdi-traku", { body: { oznaka: z.tekst, traka: id } });
      else await api("/api/nalog/materijal/" + z.nalog_materijal_id + "/potvrdi", { body: { ident: id } });
      render();
    }
    if (ident) return upisi(ident);
    dlg({ naslov: (traka ? "Traka za „" : "Materijal za „") + (z.tekst || z.naziv_ulaz) + "“", tijelo: '<div class="field"><span class="lbl">Traži u šifrarniku</span><input><div class="lista"></div></div>',
      nakon: function (bg, zatvori) { pretragaLista(q(".field", bg), async function (s) { var r = await api((traka ? "/api/sifrarnik/trake?q=" : "/api/sifrarnik/materijali?q=") + encodeURIComponent(s) + "&limit=40"); return r.trake || r.materijali || r; },
        function (x) { return '<span class="mono">' + esc(x.ident) + '</span> ' + esc(x.naziv); }, function (x) { zatvori(); upisi(x.ident); }); } });
  }
  function grupe(d) {
    var g = d.grupe || {};
    var majke = (g.majke || []).map(function (mk) { return '<tr><td><span class="tag info">' + esc(mk.vrsta) + '</span> ' + esc(mk.oznaka || "") + '</td><td>' + esc(mk.materijal || "") + '</td><td class="r">' + n(mk.L, 0) + ' × ' + n(mk.W, 0) + '</td><td class="r">' + (mk.clanova || "") + '</td><td>' + (mk.provjeri ? '<span class="tag warn">provjeri</span> ' : "") + esc(mk.napomena || "") + '</td><td><a href="/api/majka/' + mk.id + '/skica.png" target="_blank">skica</a></td></tr>'; }).join("");
    dlg({ naslov: "Grupe: majke i sklopovi (mjera za rezanje)", wide: true, tijelo: '<div class="note">Hub sam iz naziva, oznaka i rubova radi: SUZITI NA (rub < 150 / širina < 60), majku za ≥ 4 ista mala komada, sklop lijepljenja (_LA1 / _LA2), niz goda (_A1, _E1H, _C1-2). Ponovna primjena ne mijenja ništa što je već ispravno.</div>' +
      '<table><thead><tr><th>Grupa</th><th>Materijal</th><th class="r">Majka</th><th class="r">Članova</th><th>Napomena</th><th></th></tr></thead><tbody>' + (majke || '<tr><td colspan="6" class="note">nema majki ni sklopova</td></tr>') + '</tbody></table>',
      gumbi: [{ txt: "Ponovno primijeni pravila", on: async function () { await api("/api/nalog/" + d.id + "/grupe", { body: {} }); render(); } }, { txt: "Zatvori", pri: true, on: function () { } }] });
  }
  function kupacPotvrdio(d) {
    dlg({ naslov: "Kupac potvrdio ponudu", tijelo: '<div class="grid2"><div class="field"><span class="lbl">Datum potvrde</span><input id="dat" type="date" value="' + new Date().toISOString().slice(0, 10) + '"></div><div class="field"><span class="lbl">Način</span><select id="nac"><option>mail</option><option>telefon</option><option>osobno</option></select></div>' +
      '<div class="field"><span class="lbl">Rok obećan kupcu</span><input id="rok" type="date"></div><div class="field"><span class="lbl">Prioritet</span><select id="pr"><option value="">normalan</option><option>visok</option><option>hitno</option></select></div><div class="field"><span class="lbl">Pantheon broj ponude (ako je poznat)</span><input id="pb" placeholder="26-010-00xxxx"></div></div>' +
      '<div class="note">Potvrđena verzija ponude ide eSlog-om u Pantheon; nalog prelazi u „Potvrđeno“ i može u Skladište.</div>',
      gumbi: [{ txt: "Potvrdi", pri: true, on: async function (bg) {
        var v = (await api("/api/nalog/" + d.id + "/ponude")).filter(function (x) { return x.status === "poslana" || x.status === "nacrt"; }).pop();
        if (v) await api("/api/ponuda/" + v.id + "/potvrdi", { body: { datum: q("#dat", bg).value, nacin: q("#nac", bg).value, rok_obecan: q("#rok", bg).value || null, prioritet: q("#pr", bg).value || null, ponuda_pantheon: q("#pb", bg).value || null } });
        else await api("/api/nalog/" + d.id + "/status", { body: { status: "potvrdjeno", datum: q("#dat", bg).value, nacin: q("#nac", bg).value, rok_obecan: q("#rok", bg).value || null, prioritet: q("#pr", bg).value || null } });
        idi("#/nalog/" + d.id + "/skladiste"); } }] });
  }

  ekrani.nalog_dogadjaji = async function (r) {
    var d = S.nalog = await api("/api/nalog/" + r.id);
    var rows = d.dogadjaji.map(function (x) { return '<tr><td class="mono">' + esc((x.kada || "").replace("T", " ").slice(0, 16)) + '</td><td>' + esc(x.tko || "") + '</td><td>' + esc(statusNaziv(x.iz_statusa)) + ' → <b>' + esc(statusNaziv(x.u_status)) + '</b></td><td>' + esc(x.razlog || "") + '</td></tr>'; }).join("");
    ljuska({ crumb: 'Nalozi / <b>' + esc(d.naziv) + '</b> · događaji', koraci: koraci(d), rail: "nalozi", cls: "c1", akcije: '<a class="tbtn" href="#/nalog/' + d.id + '">Natrag na nalog</a>',
      sadrzaj: '<div class="pane"><div class="hd"><b>Vremenska crta naloga</b></div><div class="bd tight"><table><thead><tr><th>Kada</th><th>Tko</th><th>Prijelaz</th><th>Razlog</th></tr></thead><tbody>' + (rows || '<tr><td colspan="4" class="note">nema događaja</td></tr>') + '</tbody></table></div></div>', foot: kpi(d.dogadjaji.length, "događaja") });
  };

  async function start() { window.addEventListener("hashchange", render); await ucitajJa(); if (S.ja && S.ja.prijava_obavezna && !S.ja.korisnik) ekranPrijava(); else render(); }
  return { start: start, api: api, esc: esc, cist: cist, mm: mm, n: n, q: q, qa: qa, dlg: dlg, toast: toast, ljuska: ljuska, kpi: kpi, koraci: koraci, S: S, ekrani: ekrani, idi: idi, render: render, statusNaziv: statusNaziv, pretragaLista: pretragaLista, kupacPotvrdio: kupacPotvrdio, postaviLozinku: postaviLozinku, ucitajJa: ucitajJa, ekranPrijava: ekranPrijava };
})();
