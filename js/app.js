(() => {
  const P = Object.fromEntries(PARISHES.map(p => [p.id, p]));
  const $ = s => document.querySelector(s);
  const norm = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9 ]/g, " ");
  const REGIONS = ["Todas", ...new Set(HOSPITALS.map(h => h.regiao))];
  let region = "Todas";

  const km = (a, b) => {
    const r = x => x * Math.PI / 180, R = 6371;
    const dLat = r(b.lat - a.lat), dLng = r(b.lng - a.lng);
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(r(a.lat)) * Math.cos(r(b.lat)) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  };
  // ~25 km/h de média urbana + fator de curva das ruas
  const eta = d => Math.max(3, Math.round(d * 1.35 / 25 * 60));
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function parishesFor(h) {
    const forced = (h.paroquias || []).map(id => P[id]).filter(Boolean);
    const rest = PARISHES.filter(p => !forced.includes(p)).sort((a, b) => km(h, a) - km(h, b));
    return [...forced, ...rest].slice(0, 3).map((p, i) => ({ p, d: km(h, p), curated: i < forced.length }));
  }

  function renderChips() {
    $("#chips").innerHTML = REGIONS.map(r => `<button class="chip${r === region ? " on" : ""}" data-r="${esc(r)}">${esc(r)}</button>`).join("");
    $("#chips").onclick = e => {
      const b = e.target.closest(".chip"); if (!b) return;
      region = b.dataset.r; renderChips(); renderList(); $("#sugg").hidden = true;
    };
  }

  function renderList(items) {
    const hs = (items || HOSPITALS).filter(h => region === "Todas" || h.regiao === region);
    const by = {};
    hs.forEach(h => (by[h.regiao] ||= []).push(h));
    $("#list").innerHTML = Object.entries(by).map(([r, arr]) =>
      `<h2>${esc(r)}</h2>` + arr.map(h =>
        `<button class="row" data-id="${h.id}"><b>${esc(h.nome)}</b><small>${esc(h.bairro)} · ${esc(h.cidade)}${h.dist != null ? " · " + h.dist.toFixed(1) + " km de você" : ""}</small></button>`).join("")).join("");
  }

  function contactBtns(p, h) {
    const b = [];
    if (p.tel) b.push(`<a class="btn" href="tel:${esc(p.tel.replace(/[^\d+]/g, ""))}">📞 Ligar ${esc(p.tel)}</a>`);
    if (p.whatsapp) b.push(`<a class="btn alt" href="https://wa.me/${esc(p.whatsapp.replace(/\D/g, ""))}?text=${encodeURIComponent("Olá, preciso da Unção dos Enfermos no " + h.nome + ".")}">💬 WhatsApp</a>`);
    if (p.email) b.push(`<a class="btn alt" href="mailto:${esc(p.email)}?subject=${encodeURIComponent("Unção dos Enfermos — " + h.nome)}">✉️ E-mail</a>`);
    b.push(`<a class="btn alt" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&origin=${p.lat},${p.lng}&destination=${encodeURIComponent(h.nome + ", " + h.cidade)}">🧭 Rota até o hospital</a>`);
    return b.join("");
  }

  function show(h) {
    const ps = parishesFor(h);
    $("#result").innerHTML = `
      <div class="card"><span class="badge alt">HOSPITAL</span>
        <h2>${esc(h.nome)}</h2><div class="meta">${esc(h.bairro)} · ${esc(h.cidade)}</div></div>
      ${ps.map(({ p, d, curated }, i) => `
        <article class="card par${i === 0 ? " first" : ""}">
          <span class="badge${i ? " alt" : ""}">${i === 0 ? "MAIS RÁPIDA" : i + 1 + "ª OPÇÃO"}${curated ? " · INDICAÇÃO" : ""}</span>
          <h3>${esc(p.nome)}</h3>
          <div class="meta">${esc(p.bairro)} · ${esc(p.cidade)}</div>
          <div>≈ <span class="eta">${d.toFixed(1)} km · ${eta(d)} min</span> de carro <span class="meta">(estimativa)</span></div>
          ${p.padre ? `<div class="meta">Pároco: ${esc(p.padre)}</div>` : ""}
          ${p.tel || p.email || p.whatsapp ? "" : `<div class="pending">Contato em levantamento — ligue também para a capelania do hospital.</div>`}
          <div class="btns">${contactBtns(p, h)}</div>
        </article>`).join("")}`;
    $("#sugg").hidden = true;
    $("#result").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const input = $("#q"), sugg = $("#sugg");
  input.addEventListener("input", () => {
    const t = norm(input.value).trim();
    if (!t) { sugg.hidden = true; return; }
    const words = t.split(/\s+/);
    const m = HOSPITALS.filter(h => { const n = norm(h.nome + " " + h.bairro + " " + h.cidade); return words.every(w => n.includes(w)); }).slice(0, 8);
    sugg.innerHTML = m.length ? m.map(h => `<li data-id="${h.id}"><b>${esc(h.nome)}</b><small>${esc(h.bairro)} · ${esc(h.cidade)}</small></li>`).join("") : `<li>Nenhum resultado. Tente outro nome ou bairro.</li>`;
    sugg.hidden = false;
  });
  input.addEventListener("keydown", e => { if (e.key === "Enter") { const f = sugg.querySelector("li[data-id]"); if (f) pick(f.dataset.id); } });
  const pick = id => show(HOSPITALS.find(h => h.id === id));
  sugg.addEventListener("click", e => { const li = e.target.closest("li[data-id]"); if (li) pick(li.dataset.id); });
  $("#list").addEventListener("click", e => { const r = e.target.closest(".row"); if (r) pick(r.dataset.id); });

  $("#near").addEventListener("click", () => {
    if (!navigator.geolocation) return alert("Seu aparelho não permite localização.");
    navigator.geolocation.getCurrentPosition(pos => {
      const me = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      const sorted = HOSPITALS.map(h => Object.assign({}, h, { dist: km(me, h) })).sort((a, b) => a.dist - b.dist);
      region = "Todas"; renderChips();
      $("#list").innerHTML = `<h2>Mais próximos de você</h2>` + sorted.slice(0, 8).map(h =>
        `<button class="row" data-id="${h.id}"><b>${esc(h.nome)}</b><small>${esc(h.bairro)} · ${esc(h.cidade)} · ${h.dist.toFixed(1)} km de você</small></button>`).join("");
    }, () => alert("Não consegui obter sua localização. Use a busca."), { enableHighAccuracy: true, timeout: 10000 });
  });

  renderChips(); renderList();
  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) navigator.serviceWorker.register("sw.js").catch(() => {});
})();
