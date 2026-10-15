(() => {
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const norm = s => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9 ]/g, " ");
  const UFS = { AC: "Acre", AL: "Alagoas", AP: "Amapá", AM: "Amazonas", BA: "Bahia", CE: "Ceará", DF: "Distrito Federal", ES: "Espírito Santo", GO: "Goiás", MA: "Maranhão", MT: "Mato Grosso", MS: "Mato Grosso do Sul", MG: "Minas Gerais", PA: "Pará", PB: "Paraíba", PR: "Paraná", PE: "Pernambuco", PI: "Piauí", RJ: "Rio de Janeiro", RN: "Rio Grande do Norte", RS: "Rio Grande do Sul", RO: "Rondônia", RR: "Roraima", SC: "Santa Catarina", SP: "São Paulo", SE: "Sergipe", TO: "Tocantins" };
  const PAGE = 30;
  const TIPO = { "Hospital": 0, "Hospital especializado": 1, "Unidade mista": 2 };
  const state = { uf: "", city: "", bairro: "", tipo: "", q: "", shown: PAGE, data: null, near: null };
  const cache = {};

  const load = async uf => cache[uf] ||= fetch(`data/${uf}.json`).then(r => { if (!r.ok) throw 0; return r.json(); });
  const km = (a, b, c, d) => { const r = x => x * Math.PI / 180, h = Math.sin(r(c - a) / 2) ** 2 + Math.cos(r(a)) * Math.cos(r(c)) * Math.sin(r(d - b) / 2) ** 2; return 12742 * Math.asin(Math.sqrt(h)); };
  const eta = d => Math.max(3, Math.round(d * 1.35 / 25 * 60));
  const hosp = a => ({ id: a[0], nome: a[1], tipo: a[2], cidade: state.data.c[a[3]], bairro: a[4], end: a[5], tel: a[6], email: a[7], lat: a[8], lng: a[9], pr: a[10], par: a[11] });
  const par = a => ({ nome: a[0], cidade: a[1], end: a[2], tel: a[3], email: a[4], site: a[5], lat: a[6], lng: a[7] });
  const opts = (sel, ph, items, val) => { sel.innerHTML = `<option value="">${esc(ph)}</option>` + items.map(([v, t]) => `<option value="${esc(v)}"${v === val ? " selected" : ""}>${esc(t)}</option>`).join(""); };
  const counts = arr => arr.reduce((m, x) => (m[x] = (m[x] || 0) + 1, m), {});

  // ---------- filtros em cascata ----------
  function fillUF() { opts($("#uf"), "Escolha o estado…", Object.entries(UFS).map(([k, v]) => [k, `${v} (${k})`]), state.uf); }

  async function setUF(uf) {
    Object.assign(state, { uf, city: "", bairro: "", q: "", shown: PAGE, near: null });
    $("#q").value = ""; $("#result").innerHTML = "";
    if (!uf) { state.data = null; refresh(); return; }
    $("#list").innerHTML = `<p class="meta">Carregando ${esc(UFS[uf])}…</p>`;
    try { state.data = await load(uf); } catch { state.data = null; $("#list").innerHTML = `<p class="meta">Não foi possível carregar os dados. Verifique a conexão.</p>`; return; }
    refresh();
  }

  function refresh() {
    const D = state.data, citySel = $("#city"), bSel = $("#bairro"), q = $("#q");
    if (!D) { citySel.disabled = bSel.disabled = q.disabled = true; opts(citySel, "Primeiro escolha o estado", []); opts(bSel, "Primeiro escolha a cidade", []); $("#list").innerHTML = ""; crumbs(); return; }
    const hs = D.h.map(hosp);
    const byCity = counts(hs.map(h => h.cidade));
    citySel.disabled = false;
    opts(citySel, "Escolha a cidade…", Object.keys(byCity).sort((a, b) => a.localeCompare(b, "pt")).map(c => [c, `${c} (${byCity[c]})`]), state.city);
    const inCity = hs.filter(h => h.cidade === state.city);
    bSel.disabled = !state.city; q.disabled = !state.city;
    const byB = counts(inCity.map(h => h.bairro));
    opts(bSel, state.city ? "Todos os bairros" : "Primeiro escolha a cidade", Object.keys(byB).sort((a, b) => a.localeCompare(b, "pt")).map(b => [b, `${b} (${byB[b]})`]), state.bairro);
    crumbs(); renderList();
  }

  function crumbs() {
    const p = ["Brasil"]; if (state.uf) p.push(UFS[state.uf]); if (state.city) p.push(state.city); if (state.bairro) p.push(state.bairro);
    $("#crumbs").innerHTML = state.near ? "📍 Perto de você" : p.map((x, i) => `<span>${esc(x)}</span>`).join(" › ");
  }

  function filtered() {
    if (state.near) return state.near;
    if (!state.data || !state.city) return [];
    const words = norm(state.q).split(/\s+/).filter(Boolean);
    return state.data.h.map(hosp).filter(h => h.cidade === state.city && (!state.bairro || h.bairro === state.bairro) &&
      (!state.tipo || (state.tipo === "Clínica" ? h.tipo === "Clínica" : h.tipo !== "Clínica")) &&
      words.every(w => norm(h.nome + " " + h.bairro).includes(w))).sort((a, b) => (TIPO[a.tipo] ?? 3) - (TIPO[b.tipo] ?? 3) || a.nome.localeCompare(b.nome, "pt"));
  }

  function renderList() {
    const el = $("#list");
    if (!state.data && !state.near) { el.innerHTML = ""; return; }
    if (!state.city && !state.near) { el.innerHTML = `<p class="meta">Agora escolha a cidade.</p>`; return; }
    const hs = filtered();
    if (!hs.length) { el.innerHTML = `<p class="meta">Nenhum hospital ou clínica encontrado com esses filtros.</p>`; return; }
    el.innerHTML = `<h2>${hs.length} ${hs.length === 1 ? "local" : "locais"}</h2>` +
      hs.slice(0, state.shown).map(h => `<button class="row" data-id="${esc(h.id)}"><span class="tag">${esc(h.tipo)}</span><b>${esc(h.nome)}</b><small>${esc(h.bairro)} · ${esc(h.cidade)}${h.dist != null ? " · " + h.dist.toFixed(1) + " km de você" : ""}</small></button>`).join("") +
      (hs.length > state.shown ? `<button class="more" id="more">Mostrar mais (${hs.length - state.shown})</button>` : "");
  }

  // ---------- resultado ----------
  function contactBtns(p, h) {
    const b = [];
    if (p.tel) { const n = p.tel.replace(/[^\d+]/g, ""); b.push(`<a class="btn" href="tel:${esc(n)}">📞 Ligar ${esc(p.tel)}</a>`); }
    if (p.email) b.push(`<a class="btn alt" href="mailto:${esc(p.email)}?subject=${encodeURIComponent("Unção dos Enfermos — " + h.nome)}">✉️ E-mail</a>`);
    if (p.site) b.push(`<a class="btn alt" target="_blank" rel="noopener" href="${esc(/^https?:/.test(p.site) ? p.site : "https://" + p.site)}">🌐 Site</a>`);
    b.push(`<a class="btn alt" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&origin=${p.lat},${p.lng}&destination=${h.lat},${h.lng}">🧭 Rota até o hospital</a>`);
    return b.join("");
  }

  const AGAIN = `<div class="again"><button type="button" class="btn newsearch" data-a="outro">🔍 Buscar outro hospital</button><button type="button" class="btn alt newsearch" data-a="zero">↺ Nova busca do zero</button></div>`;

  function show(h) {
    const ps = h.par.map(([i, d, cur]) => ({ p: par(state.data.p[i]), d, cur }));
    $("#result").innerHTML = `
      <div class="card"><span class="badge alt">${esc(h.tipo.toUpperCase())}</span>
        <h2>${esc(h.nome)}</h2>
        <div class="meta">${esc(h.end)} · ${esc(h.bairro)} · ${esc(h.cidade)}/${esc(state.uf)}</div>
        ${h.pr ? `<div class="warn">⚠️ Localização ${["", "aproximada (pela rua)", "aproximada (pelo bairro)", "aproximada (centro do município)"][h.pr]}. As distâncias abaixo podem não ser exatas — <b>confirme por telefone</b>.</div>` : ""}
        <div class="btns">${h.tel ? `<a class="btn alt" href="tel:${esc(h.tel.replace(/[^\d+]/g, ""))}">📞 Hospital: ${esc(h.tel)}</a>` : ""}
          <a class="btn alt" target="_blank" rel="noopener" href="https://www.google.com/maps/search/?api=1&query=${h.lat},${h.lng}">📍 Ver no mapa</a></div></div>
      ${AGAIN}
      ${ps.length ? ps.map(({ p, d, cur }, i) => `
        <article class="card par${i === 0 ? " first" : ""}">
          <span class="badge${i ? " alt" : ""}">${i === 0 ? "MAIS PRÓXIMA" : i + 1 + "ª OPÇÃO"}${cur ? " · INDICAÇÃO" : ""}</span>
          <h3>${esc(p.nome)}</h3>
          <div class="meta">${esc(p.end || "")}${p.end && p.cidade ? " · " : ""}${esc(p.cidade || "")}</div>
          ${d > 10 && h.pr < 3 ? `<div class="warn">⚠️ Paróquia distante: nenhuma foi encontrada mais perto no mapa.</div>` : ""}
          ${h.pr >= 3 ? `<div class="meta">Distância indisponível (localização do hospital não confirmada).</div>` : `<div>≈ <span class="eta">${d.toFixed(1)} km · ${eta(d)} min</span> de carro <span class="meta">(estimativa)</span></div>`}
          ${p.tel || p.email || p.site ? "" : `<div class="pending">Contato não encontrado — ligue para a capelania do hospital.</div>`}
          <div class="btns">${contactBtns(p, h)}</div>
        </article>`).join("") : `<div class="card"><p>Nenhuma paróquia encontrada por perto. Pergunte na capelania do hospital ou na diocese da região.</p></div>`}
      ${AGAIN}`;
    $("#result").scrollIntoView({ behavior: "smooth", block: "start" });
    try { history.replaceState(null, "", `#${state.uf}/${h.id}`); } catch {}
  }

  const find = id => state.data && state.data.h.map(hosp).find(h => h.id === id);

  // ---------- nova busca ----------
  function novaBusca(modo) {
    $("#result").innerHTML = "";
    try { history.replaceState(null, "", location.pathname); } catch {}
    if (modo === "zero") { state.near = null; $("#uf").value = ""; $("#q").value = ""; setUF(""); }
    else { state.q = ""; $("#q").value = ""; state.shown = PAGE; if (state.near) { state.near = null; refresh(); } else renderList(); }
    $("#filters").scrollIntoView({ behavior: "smooth", block: "start" });
    setTimeout(() => { const el = modo !== "zero" && !$("#q").disabled ? $("#q") : $("#uf"); el.focus({ preventScroll: true }); }, 400);
  }
  $("#result").addEventListener("click", e => { const b = e.target.closest(".newsearch"); if (b) novaBusca(b.dataset.a); });

  // ---------- eventos ----------
  $("#uf").addEventListener("change", e => setUF(e.target.value));
  $("#city").addEventListener("change", e => { state.city = e.target.value; state.bairro = ""; state.shown = PAGE; state.near = null; $("#result").innerHTML = ""; refresh(); });
  $("#bairro").addEventListener("change", e => { state.bairro = e.target.value; state.shown = PAGE; crumbs(); renderList(); });
  let t; $("#q").addEventListener("input", e => { clearTimeout(t); t = setTimeout(() => { state.q = e.target.value; state.shown = PAGE; renderList(); }, 150); });
  document.querySelector(".seg").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return; document.querySelectorAll(".seg button").forEach(x => x.classList.toggle("on", x === b)); state.tipo = b.dataset.t; state.shown = PAGE; renderList(); });
  $("#list").addEventListener("click", e => {
    if (e.target.closest("#more")) { state.shown += PAGE; renderList(); return; }
    const r = e.target.closest(".row"); if (r) { const h = find(r.dataset.id); if (h) show(h); }
  });

  $("#near").addEventListener("click", () => {
    if (!navigator.geolocation) return alert("Seu aparelho não permite localização.");
    navigator.geolocation.getCurrentPosition(async pos => {
      const { latitude: la, longitude: lo } = pos.coords;
      try {
        const idx = await fetch("data/index.json").then(r => r.json());
        const uf = idx.reduce((b, x) => { const d = km(la, lo, x[1], x[2]); return d < b.d ? { d, uf: x[0] } : b; }, { d: 1e9 }).uf;
        state.data = await load(uf); Object.assign(state, { uf, city: "", bairro: "", q: "" });
        fillUF(); refresh();
        state.near = state.data.h.map(hosp).map(h => Object.assign(h, { dist: km(la, lo, h.lat, h.lng) })).sort((a, b) => a.dist - b.dist).slice(0, 15);
        $("#result").innerHTML = ""; crumbs(); renderList();
      } catch { alert("Não consegui carregar os dados."); }
    }, () => alert("Não consegui obter sua localização. Use os filtros."), { enableHighAccuracy: true, timeout: 10000 });
  });

  // instalar como app: botão nativo no Android/Chrome; passo a passo no iOS
  let dip; const ib = $("#installBtn");
  window.addEventListener("beforeinstallprompt", e => { e.preventDefault(); dip = e; ib.hidden = false; });
  ib.addEventListener("click", async () => { if (!dip) return; dip.prompt(); await dip.userChoice; dip = null; ib.hidden = true; });
  window.addEventListener("appinstalled", () => { $("#install").hidden = true; });
  const ua = navigator.userAgent;
  if (/iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1)) $("#ios").open = true;
  else if (/Android/.test(ua)) $("#android").open = true;

  // link direto: #UF/idCNES
  fillUF();
  const m = location.hash.match(/^#([A-Z]{2})\/(\d+)$/);
  if (m && UFS[m[1]]) load(m[1]).then(d => { state.data = d; state.uf = m[1]; fillUF(); const h = find(m[2]); if (h) { state.city = h.cidade; refresh(); show(h); } else refresh(); }).catch(() => {});
  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) navigator.serviceWorker.register("sw.js").catch(() => {});
})();
