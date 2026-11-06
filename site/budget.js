// Budget math. Mirrors budget/build_budget.py: keep the two in step.
window.Budget = (() => {
  const round = (x, places = 0) => {
    const f = 10 ** places;
    return Math.round((x + Number.EPSILON) * f) / f;
  };

  function compute(data, a) {
    let requiredPlugs = 0;
    return data.items.map(it => {
      const q = it.qty;
      let qty;
      if ("fixed" in q) qty = q.fixed;
      else if ("plugs" in q) qty = round(a[q.plugs] * a.plugDensity);
      else if ("mulch" in q) qty = round(a[q.mulch] * a.mulchDepth / 12 / 27, 1);
      else if ("seed" in q) qty = round(a[q.seed] / 1000 * a.seedRate, 1);
      else if (q.replacement) qty = round(requiredPlugs * a.replacementPct);
      if (it.unit === "plugs" && !it.optional && !q.replacement) requiredPlugs += qty;
      const [lo, hi] = it.price.map(p => (typeof p === "string" ? a[p] : p));
      return { ...it, qtyValue: qty, lo, hi, totalLo: qty * lo, totalHi: qty * hi };
    });
  }

  const money = x => "$" + Math.round(x).toLocaleString("en-US");
  const range = (lo, hi) => (Math.round(lo) === Math.round(hi) ? money(lo) : `${money(lo)}–${money(hi)}`);
  const num = x => (Number.isInteger(x) ? x.toLocaleString("en-US") : x.toFixed(1));

  // Inputs exposed as controls on the page.
  const CONTROLS = [
    { key: "plugLow", label: "Plug price, low", step: 0.05, min: 0, prefix: "$" },
    { key: "plugHigh", label: "Plug price, high", step: 0.05, min: 0, prefix: "$" },
    { key: "plugDensity", label: "Plugs per sq ft", step: 0.02, min: 0.3, max: 1, hint: "0.44 = 18 in. grid · 0.64 = 15 in." },
    { key: "mulchHigh", label: "Mulch donation per cu yd (high)", step: 1, min: 0, prefix: "$" },
    { key: "grantL2L", label: "Lawns to Legumes award", step: 50, min: 0, max: 400, prefix: "$" },
    { key: "grantGarden", label: "Garden Grant award", step: 50, min: 0, max: 1000, prefix: "$" },
  ];

  function mount(root, data) {
    const defaults = Object.fromEntries(data.assumptions.filter(r => r.key).map(r => [r.key, r.value]));
    const a = { ...defaults };
    const optional = new Set(); // keys of optional items the user switched on
    const itemKey = it => it.item;

    root.innerHTML = `
      <div class="budget-grid">
        <div class="card budget-controls">
          <h3>Adjust the inputs</h3>
          <div class="controls"></div>
          <button type="button" class="link-btn" data-reset>Reset to plan values</button>
        </div>
        <div class="card budget-result" aria-live="polite">
          <div class="big-total"></div>
          <div class="phase-bars"></div>
          <p class="fine"></p>
        </div>
      </div>
      <div class="card">
        <h3>Optional extras</h3>
        <p class="fine">Switch on what you plan to buy. The boulevard Option B lines move together.</p>
        <div class="opt-list"></div>
      </div>
      <details class="card line-items">
        <summary>All line items</summary>
        <div class="items"></div>
      </details>`;

    const controls = root.querySelector(".controls");
    CONTROLS.forEach(c => {
      const row = document.createElement("label");
      row.className = "ctl";
      row.innerHTML = `<span>${c.label}${c.hint ? `<small>${c.hint}</small>` : ""}</span>
        <span class="ctl-in">${c.prefix ? `<i>${c.prefix}</i>` : ""}<input type="number" inputmode="decimal" step="${c.step}" min="${c.min}" ${c.max != null ? `max="${c.max}"` : ""} data-k="${c.key}"></span>`;
      controls.appendChild(row);
    });

    const opts = root.querySelector(".opt-list");
    const seenGroups = new Set();
    data.items.filter(it => it.optional).forEach(it => {
      if (it.group) {
        if (seenGroups.has(it.group)) return;
        seenGroups.add(it.group);
      }
      const label = it.group === "blvdB" ? "Boulevard Option B: permit, mulch and short native plugs" : it.item;
      const row = document.createElement("label");
      row.className = "opt";
      row.innerHTML = `<input type="checkbox" data-opt="${it.group || itemKey(it)}"><span>${label}<small>Phase ${it.phase}</small></span><b class="opt-cost"></b>`;
      opts.appendChild(row);
    });

    function sync() {
      root.querySelectorAll("[data-k]").forEach(i => { i.value = a[i.dataset.k]; });
      root.querySelectorAll("[data-opt]").forEach(i => { i.checked = optional.has(i.dataset.opt); });
    }

    function render() {
      const rows = compute(data, a);
      const on = r => !r.optional || optional.has(r.group || itemKey(r));
      const active = rows.filter(on);
      const lo = active.reduce((s, r) => s + r.totalLo, 0);
      const hi = active.reduce((s, r) => s + r.totalHi, 0);
      const grants = (a.grantL2L || 0) + (a.grantGarden || 0);
      const plugs = active.filter(r => r.unit === "plugs").reduce((s, r) => s + r.qtyValue, 0);
      const mulch = active.filter(r => r.unit === "cu yd").reduce((s, r) => s + r.qtyValue, 0);

      root.querySelector(".big-total").innerHTML = `
        <div class="kicker">Your cash outlay, net of grants</div>
        <div class="amount">${range(Math.max(0, lo - grants), Math.max(0, hi - grants))}</div>
        <div class="sub">${range(lo, hi)} before ${money(grants)} in grants · ${num(plugs)} plugs · ${num(round(mulch, 1))} cu yd mulch &amp; topsoil</div>`;

      const maxHi = Math.max(...data.phases.map(p => active.filter(r => r.phase === p.phase).reduce((s, r) => s + r.totalHi, 0)), 1);
      root.querySelector(".phase-bars").innerHTML = data.phases.map(p => {
        const pr = active.filter(r => r.phase === p.phase);
        const plo = pr.reduce((s, r) => s + r.totalLo, 0), phi = pr.reduce((s, r) => s + r.totalHi, 0);
        return `<div class="pbar">
          <div class="pbar-head"><span><b>Phase ${p.phase}</b> · ${p.title}</span><span>${range(plo, phi)}</span></div>
          <div class="pbar-track"><span class="pbar-lo ph${p.phase}" data-w="${(plo / maxHi) * 100}"></span><span class="pbar-hi ph${p.phase}" data-w="${(phi / maxHi) * 100}"></span></div>
          <div class="pbar-when">${p.timing}</div></div>`;
      }).join("");
      root.querySelectorAll(".pbar-track span").forEach(s => { s.style.width = s.dataset.w + "%"; });

      root.querySelector(".budget-result .fine").textContent =
        "Low end assumes the cheapest plug trays and free city mulch; high end assumes pricier species and a modest donation per load. Plugs are most of the cost.";

      // optional costs
      root.querySelectorAll("[data-opt]").forEach(i => {
        const key = i.dataset.opt;
        const rs = rows.filter(r => r.optional && (r.group || itemKey(r)) === key);
        i.closest(".opt").querySelector(".opt-cost").textContent = range(
          rs.reduce((s, r) => s + r.totalLo, 0), rs.reduce((s, r) => s + r.totalHi, 0));
      });

      root.querySelector(".items").innerHTML = data.phases.map(p => `
        <h4>Phase ${p.phase} <small>${p.timing}</small></h4>
        <ul class="item-list">${rows.filter(r => r.phase === p.phase).map(r => `
          <li class="${on(r) ? "" : "off"}">
            <div class="it-main"><span class="it-name">${r.item}${r.optional ? ' <em class="tag">optional</em>' : ""}</span>
            <span class="it-total">${range(r.totalLo, r.totalHi)}</span></div>
            <div class="it-meta">${r.when} · ${num(r.qtyValue)} ${r.unit} × ${r.lo === r.hi ? "$" + r.lo.toFixed(2) : `$${r.lo.toFixed(2)}–$${r.hi.toFixed(2)}`}</div>
            <div class="it-note">${r.note}</div>
          </li>`).join("")}</ul>`).join("") +
        `<p class="fine">Download: <a href="https://github.com/jkastl/lawn-and-order/blob/main/budget/budget.csv">budget.csv</a> · <a href="https://github.com/jkastl/lawn-and-order/blob/main/budget/assumptions.csv">assumptions.csv</a> · <a href="data/budget.json">budget.json</a></p>`;
    }

    root.addEventListener("input", e => {
      const k = e.target.dataset.k;
      if (k) {
        const v = parseFloat(e.target.value);
        if (!Number.isNaN(v)) { a[k] = v; render(); }
      }
    });
    root.addEventListener("change", e => {
      const o = e.target.dataset.opt;
      if (o) { e.target.checked ? optional.add(o) : optional.delete(o); render(); }
    });
    root.querySelector("[data-reset]").addEventListener("click", () => {
      Object.assign(a, defaults);
      optional.clear();
      sync(); render();
    });

    sync(); render();
  }

  return { compute, mount, money, range };
})();
