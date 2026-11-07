(async () => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // Per-browser storage for checklist ticks. Never sent anywhere; may be
  // unavailable (private mode, blocked storage), so every access is guarded.
  const store = {
    get(k, d) { try { const v = localStorage.getItem("lao:" + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem("lao:" + k, JSON.stringify(v)); } catch { /* ignore */ } },
  };

  let plan, budget;
  try {
    [plan, budget] = await Promise.all(["data/plan.json", "data/budget.json"].map(u => fetch(u).then(r => {
      if (!r.ok) throw new Error(u + " " + r.status);
      return r.json();
    })));
  } catch (err) {
    $("#main").insertAdjacentHTML("afterbegin", `<p class="noscript">Couldn't load the plan data (${err.message}). If you opened this file directly, serve the folder instead: <code>python3 -m http.server -d site</code></p>`);
    return;
  }

  const today = new Date();
  const fmtDate = iso => new Date(iso + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const PHASE_NAME = { 1: "Phase 1", 2: "Phase 2", 3: "Phase 3" };

  // ---------- overview ----------
  $("[data-asof]").textContent = "Plan as of " + fmtDate(plan.asOf);
  $("[data-stats]").innerHTML = plan.stats.map(s => `
    <div class="stat"><div class="stat-v">${s.value}${s.unit ? ` <small>${s.unit}</small>` : ""}</div><div class="stat-l">${s.label}</div></div>`).join("");

  $("[data-deadlines]").innerHTML = plan.deadlines.map(d => {
    const end = new Date(d.date + "T23:59:59");
    const days = Math.ceil((end - today) / 864e5);
    const status = days < 0 ? `<span class="due closed">Closed</span>`
      : days === 0 ? `<span class="due soon">Due today</span>`
      : `<span class="due ${days <= 30 ? "soon" : ""}">${days} day${days === 1 ? "" : "s"} left</span>`;
    return `<a class="deadline ${days < 0 ? "past" : ""}" href="${d.url}" rel="noopener noreferrer" target="_blank">
      <div class="dl-top"><span class="dl-date">Due ${fmtDate(d.date)}</span>${status}</div>
      <div class="dl-t">${d.title} ↗</div><p>${d.detail}</p></a>`;
  }).join("");

  $("[data-principles]").innerHTML = plan.principles.map(p => `<li><b>${p.t}.</b> ${p.d}</li>`).join("");

  // ---------- site model ----------
  const detail = $("#detail");
  const plantsFor = id => plan.plants.filter(p => p.z.includes(id));
  function renderDetail(id) {
    const i = plan.areas[id];
    if (!i) return;
    const plants = plantsFor(id);
    detail.innerHTML = `
      <div class="detail-head">${i.zone ? `<span class="zcode">${i.zone}</span>` : ""}<h3>${i.t}</h3></div>
      <div class="meta">${[i.area, i.light, i.phase ? PHASE_NAME[i.phase] : "", i.when].filter(Boolean).map(m => `<span class="chip">${m}</span>`).join("")}</div>
      ${i.body}
      ${plants.length ? `<div class="mini-plants"><h4>Plants</h4>${plants.map(p => `<span class="pchip">${p.n}</span>`).join("")}</div>` : ""}`;
  }
  const pick = $("[data-pick]");
  const map = SiteMap.create($("#site-svg"), {
    info: plan.areas,
    onSelect(id, { fromMap, fromList, viewChanged } = {}) {
      renderDetail(id);
      if (viewChanged) syncView();
      $$("[data-pid]", pick).forEach(b => b.setAttribute("aria-pressed", String(b.dataset.pid === id)));
      if ((fromMap || fromList) && window.matchMedia("(max-width: 899px)").matches) {
        const r = detail.getBoundingClientRect();
        if (r.top > window.innerHeight - 80) detail.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    },
  });

  // The tappable list under the map: every area you can select, with a
  // swatch in the same color the map uses for it in the current view.
  pick.innerHTML = plan.pickOrder.map(([id, label]) => {
    const a = plan.areas[id];
    const sub = a.phase ? PHASE_NAME[a.phase] : id === "blvd" ? "Existing" : "Feature";
    return `<button type="button" class="pick-btn" data-pid="${id}" aria-pressed="false">
      <span class="pick-sw"></span><span class="pick-t">${label}<small>${sub}</small></span></button>`;
  }).join("");
  pick.addEventListener("click", e => {
    const b = e.target.closest("[data-pid]");
    if (b) map.select(b.dataset.pid, { fromList: true });
  });
  function renderPick() {
    $$("[data-pid]", pick).forEach(b => { b.querySelector(".pick-sw").style.background = map.colorOf(b.dataset.pid); });
  }

  function renderLegend() {
    $("[data-legend]").innerHTML = map.legend().map(([c, s]) =>
      `<span class="lg"><span class="sw${c ? "" : " sw-tree"}"${c ? ` data-c="${c}"` : ""}></span>${s}</span>`).join("");
    $$("[data-legend] .sw[data-c]").forEach(sw => { sw.style.background = sw.dataset.c; });
  }
  function syncView() {
    $$("[data-view]").forEach(x => x.setAttribute("aria-pressed", String(x.dataset.view === map.state.view)));
    renderLegend();
    renderPick();
  }
  $$("[data-view]").forEach(b => b.addEventListener("click", () => { map.set("view", b.dataset.view); syncView(); }));
  $$("[data-layer]").forEach(c => c.addEventListener("change", () => { map.set(c.dataset.layer, c.checked); renderLegend(); }));
  map.draw(); syncView(); map.select("corner");

  // ---------- zones ----------
  const zoneWrap = $("[data-zones]");
  zoneWrap.innerHTML = plan.zoneOrder.map(id => {
    const z = plan.areas[id];
    const plants = plantsFor(id);
    return `<article class="card zone-card" data-phase="${z.phase}" data-id="${id}">
      <div class="zc-head"><span class="zcode">${z.zone}</span><span class="phase-pill ph${z.phase}">${PHASE_NAME[z.phase]}</span></div>
      <h3>${z.t}</h3>
      <div class="meta">${[z.area, z.light].filter(Boolean).map(m => `<span class="chip">${m}</span>`).join("")}</div>
      <p class="zc-when">${z.when}</p>
      ${plants.length ? `<div class="mini-plants">${plants.map(p => `<span class="pchip">${p.n}</span>`).join("")}</div>` : ""}
      <button type="button" class="link-btn" data-show="${id}">Show on map →</button>
    </article>`;
  }).join("");
  zoneWrap.addEventListener("click", e => {
    const b = e.target.closest("[data-show]");
    if (!b) return;
    if (map.state.view === "existing") $("[data-view='plan']").click();
    map.select(b.dataset.show);
    $("#map").scrollIntoView({ behavior: "smooth" });
  });
  $("[data-zone-filter]").addEventListener("click", e => {
    const b = e.target.closest("[data-ph]");
    if (!b) return;
    $$("[data-zone-filter] [data-ph]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
    $$(".zone-card").forEach(c => { c.hidden = b.dataset.ph !== "all" && c.dataset.phase !== b.dataset.ph; });
  });

  // ---------- plants / bloom calendar ----------
  const FILTERS = [
    ["all", "All"], ["corner", "Corner prairie"], ["fdn", "Stump island"], ["shade", "Shade bed"],
    ["border", "South border"], ["lawn", "Bee lawn"], ["rain", "Rain pocket"],
  ];
  const inFilter = (p, f) => f === "all" || (f === "lawn" ? p.z.includes("z1") || p.z.includes("blvd") : p.z.includes(f));
  $("[data-plant-filter]").innerHTML = FILTERS.map(([k, s], i) => `<button type="button" data-pf="${k}" aria-pressed="${i === 0}">${s}</button>`).join("");
  const M0 = 3, M1 = 10; // March..October
  function renderBloom(f) {
    const list = plan.plants.filter(p => inFilter(p, f)).sort((a, b) => a.b[0] - b.b[0] || a.b[1] - b.b[1]);
    const cols = M1 - M0 + 1;
    const counts = Array.from({ length: cols }, (_, i) => list.filter(p => p.b[0] <= M0 + i && p.b[1] >= M0 + i).length);
    const maxC = Math.max(...counts, 1);
    const head = `<div class="bl-row bl-head"><div class="bl-name"></div>${Array.from({ length: cols }, (_, i) => `<div class="bl-m">${MONTHS[M0 + i - 1]}</div>`).join("")}</div>`;
    const rows = list.map(p => `
      <div class="bl-row">
        <div class="bl-name"><b>${p.n}</b>${p.native === false ? ' <em class="tag">non-native</em>' : ""}<small><i>${p.l}</i> · ${p.h}${p.note ? ` · ${p.note}` : ""}</small></div>
        <div class="bl-track"><span class="bl-bar k-${p.kind}" data-s="${p.b[0] - M0 + 1}" data-e="${p.b[1] - M0 + 2}" title="${MONTHS[p.b[0] - 1]}–${MONTHS[p.b[1] - 1]}"></span></div>
      </div>`).join("");
    const cov = `<div class="bl-row bl-cov"><div class="bl-name"><b>Species in bloom</b></div>${counts.map(c =>
      `<div class="bl-c${c === 0 ? " gap" : ""}" data-o="${0.15 + 0.85 * (c / maxC)}">${c || "–"}</div>`).join("")}</div>`;
    const bloom = $("[data-bloom]");
    bloom.innerHTML = `<div class="bl-grid">${head}${rows}${cov}</div>
      <p class="fine"><span class="key k-forb"></span>Wildflower <span class="key k-grass"></span>Grass/sedge <span class="key k-shrub"></span>Shrub <span class="key k-bulb"></span>Bulb · ${list.length} species${counts.includes(0) ? " · <b>gaps</b> show months with nothing in flower" : ""}</p>`;
    $$(".bl-bar", bloom).forEach(b => { b.style.gridColumn = `${b.dataset.s} / ${b.dataset.e}`; });
    $$(".bl-c", bloom).forEach(c => { c.style.setProperty("--o", c.dataset.o); });
  }
  $("[data-plant-filter]").addEventListener("click", e => {
    const b = e.target.closest("[data-pf]");
    if (!b) return;
    $$("[data-pf]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
    renderBloom(b.dataset.pf);
  });
  renderBloom("all");

  // ---------- timeline ----------
  const done = new Set(store.get("steps", []));
  const t0 = today.toISOString().slice(0, 10);
  let nowId = (plan.timeline.find(s => s.start <= t0 && t0 <= s.end) || plan.timeline.find(s => s.start > t0) || {}).id;
  function renderSteps() {
    $("[data-steps]").innerHTML = plan.timeline.map(s => `
      <li class="step ${done.has(s.id) ? "done" : ""} ${s.id === nowId ? "now" : ""} ph${s.phase}">
        <label class="step-check"><input type="checkbox" data-step="${s.id}" ${done.has(s.id) ? "checked" : ""}><span class="sr-only">Mark “${s.t}” done</span></label>
        <div class="step-body">
          <div class="step-when">${s.when}${s.id === nowId ? ' <span class="now-pill">Now</span>' : ""}</div>
          <h3>${s.t}</h3>
          <p>${s.d}</p>
        </div>
      </li>`).join("");
    const n = plan.timeline.filter(s => done.has(s.id)).length;
    $("[data-progress]").innerHTML = `<div class="prog-track"><span data-w="${(n / plan.timeline.length) * 100}"></span></div><span>${n} of ${plan.timeline.length} steps done</span>`;
    $("[data-progress] .prog-track span").style.width = (n / plan.timeline.length) * 100 + "%";
  }
  $("[data-steps]").addEventListener("change", e => {
    const id = e.target.dataset.step;
    if (!id) return;
    e.target.checked ? done.add(id) : done.delete(id);
    store.set("steps", [...done]);
    renderSteps();
  });
  renderSteps();

  // ---------- budget ----------
  Budget.mount($("[data-budget]"), budget);

  // ---------- rules + programs ----------
  const ruleLi = r => `<li><b>${r.t}</b><span>${r.d}</span>${r.url ? `<a href="${r.url}" rel="noopener noreferrer" target="_blank">Source ↗</a>` : ""}</li>`;
  $("[data-rules-private]").innerHTML = plan.rules.private.map(ruleLi).join("");
  $("[data-programs]").innerHTML = plan.programs.map(p => `
    <a class="card program" href="${p.url}" rel="noopener noreferrer" target="_blank">
      <h4>${p.t} ↗</h4><p class="offer">${p.offer}</p><p>${p.fit}</p></a>`).join("");

  // ---------- open questions ----------
  const answered = new Set(store.get("questions", []));
  $("[data-questions]").innerHTML = plan.openQuestions.filter(q => !q.a).map(q => `
    <li><label><input type="checkbox" data-q="${q.id}" ${answered.has(q.id) ? "checked" : ""}><span>${q.t}</span></label></li>`).join("");
  $("[data-answered]").innerHTML = plan.openQuestions.filter(q => q.a).map(q => `
    <li><span class="ans-q">${q.t}</span><span class="ans-a">${q.a}</span></li>`).join("");
  $("[data-questions]").addEventListener("change", e => {
    const id = e.target.dataset.q;
    if (!id) return;
    e.target.checked ? answered.add(id) : answered.delete(id);
    store.set("questions", [...answered]);
  });

  // ---------- sources ----------
  const allSources = [...plan.sources, ...budget.sources.filter(s => s.url && !plan.sources.some(p => p.url === s.url))];
  $("[data-sources]").innerHTML = allSources.map(s => `<li><a href="${s.url}" rel="noopener noreferrer" target="_blank">${s.label}</a></li>`).join("") +
    `<li>All pages opened ${fmtDate(plan.asOf)}.</li>`;

  // ---------- nav highlight ----------
  const links = $$(".top nav a");
  const io = new IntersectionObserver(entries => {
    entries.forEach(en => {
      if (!en.isIntersecting) return;
      links.forEach(a => a.classList.toggle("on", a.getAttribute("href") === "#" + en.target.id));
      const on = links.find(a => a.classList.contains("on"));
      const nav = on && on.parentElement;
      if (nav && nav.scrollWidth > nav.clientWidth) nav.scrollTo({ left: on.offsetLeft - 24, behavior: "smooth" });
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  $$("main > section[id]").forEach(s => io.observe(s));
})();
