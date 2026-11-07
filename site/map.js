// To-scale site model of the front yard. Lot frame in feet: x runs east from
// the front property line, y runs south from the north line. "Plan north" is
// up; the street is on the left. Geometry is scaled from an aerial photo
// (±2–3 ft).
window.SiteMap = (() => {
  const NS = "http://www.w3.org/2000/svg";

  // Map colors are fixed (the plan is drawn on "paper" in both themes).
  const C = {
    paper: "#fbfaf6", ink: "#22261f", muted: "#646b5e", sel: "#b5522b",
    street: "#b9b9b4", walk: "#e4e1d8", conc: "#d5d2c8", house: "#8c8a84", lot: "#4a4a44",
    turf: "#cfe0b4", bee: "#e9e3a6", prairie: "#e7b866", shade: "#8fb59a", fdn: "#c9a77a",
    water: "#7fb6d6", tree: "#2f6b3a", back: "#e7e5de", path: "#c8b49a", deck: "#bfa58a", hive: "#a8873f",
    stump: "#7a5a3a", p1: "#d9822b", p2: "#3f8f6b", p3: "#7d5ba6",
  };

  const G = {
    lot: [[0,0],[114,0],[114,67.8],[0,67.8]],
    house: [[20.2,3.5],[48.0,3.0],[48.1,9.9],[74.6,9.8],[74.6,50.1],[46.6,51.1],[44.8,38.4],[20.8,39.1]],
    drive: [[0.6,3.7],[20.2,3.5],[20.4,24.5],[-0.2,27.5]],
    apron: [[-15,1],[0.6,3.7],[-0.2,27.5],[-15,30]],
    walk: [[15.1,25.1],[20.4,24.4],[20.6,35.3],[16.5,36.0]],
    deck: [[74.6,29.7],[83.0,29.6],[83.8,49.1],[74.6,50.1]],
    fdn: [[10.3,25.8],[15.1,25.1],[16.9,38.6],[12.7,38.8]],
    cornerExisting: [[33.2,38.7],[44.8,38.4],[46.6,51.1],[39.2,51.3],[34.9,46.5]],
    hive: [[57.3,52.8],[66.1,52.3],[66.3,54.9],[57.5,55.6]],
    stumpIsland: [[1,27.3],[10.3,25.8],[16.9,38.6],[13,40.5],[6,41.5],[1,36.5]],
    cornerBed: [[20.8,39.1],[44.8,38.4],[46.6,51.1],[36,51.3],[28,50.6],[22.5,47.5]],
    shadeN: [[33,51.3],[46.6,51.1],[57.3,50.8],[57.3,56],[33,56]],
    shadeS: [[33,59],[69.3,59],[69.4,67.8],[33,67.8]],
    path: [[33,56],[69.2,56],[69.3,59],[33,59]],
    border: [[1.5,59.5],[33,59],[33,65.4],[9,65.4],[7.4,67.6],[1.5,67.6]],
    z1: [[-3,27.5],[-0.2,27.5],[10.3,25.8],[12.7,38.8],[16.9,38.6],[20.8,39.1],[33,38.8],[33,67.8],[-3,67.8]],
    blvd: [[-15,30],[-8,30],[-8,67.8],[-15,67.8]],
  };
  const TREES = [
    { id: "T2", c: [-11.5, 34], r: 12 },
    { id: "T3", c: [-11.5, 71.5], r: 9 },
    { id: "T4", c: [48, 60], r: 8 },
    { id: "T5", c: [56, 75], r: 15 },
  ];
  const VIEW = [-26, -10, 104, 88];

  // Which areas exist in which view (the existing view has no new beds).
  const PLAN_ONLY = new Set(["border", "path", "rain"]);

  // The swatch color for an area in the current view (used by the list too).
  function colorOf(id, view) {
    const phases = view === "phases";
    const P = {
      corner: phases ? C.p1 : view === "existing" ? C.fdn : C.prairie,
      fdn: phases ? C.p1 : view === "existing" ? C.fdn : C.prairie,
      shade: phases ? C.p2 : view === "existing" ? C.turf : C.shade,
      border: phases ? C.p3 : C.prairie,
      z1: C.bee, blvd: C.bee, path: C.path, rain: C.water, hive: C.hive, stump: C.stump,
    };
    return P[id] || C.tree;
  }

  const pts = a => a.map(p => p.join(",")).join(" ");

  function create(svg, { info, onSelect }) {
    const state = { view: "plan", trees: true, dims: true, sel: null };
    const Z = {};
    let k = 1; // label scale, larger on narrow screens

    const el = (tag, attrs = {}, parent = svg) => {
      const e = document.createElementNS(NS, tag);
      for (const key in attrs) e.setAttribute(key, attrs[key]);
      parent.appendChild(e);
      return e;
    };
    const hit = (node, id) => {
      node.classList.add("zone");
      node.dataset.z = id;
      if (!Z[id]) {
        Z[id] = [];
        node.setAttribute("tabindex", "0");
        node.setAttribute("role", "button");
        node.setAttribute("aria-label", (info[id] && info[id].t) || id);
      }
      Z[id].push(node);
      return node;
    };
    const poly = (p, fill, o = {}) => el("polygon", {
      points: pts(p), fill, stroke: o.stroke || "rgba(0,0,0,.25)", "stroke-width": o.sw || 0.15,
      ...(o.op != null ? { "fill-opacity": o.op } : {}),
    });
    const zone = (id, p, fill, o = {}) => hit(poly(p, fill, o), id);
    const text = (x, y, s, o = {}) => {
      const t = el("text", {
        x, y, "font-size": (o.fs || 1.9) * 1.35 * k, "text-anchor": o.anchor || "middle",
        fill: o.fill || C.ink, "font-weight": o.w || 400, "pointer-events": "none",
        ...(o.rot ? { transform: `rotate(${o.rot} ${x} ${y})` } : {}),
      });
      t.textContent = s;
      return t;
    };

    function draw() {
      for (const key in Z) delete Z[key];
      svg.replaceChildren();
      const [vx, vy, vw, vh] = VIEW;
      svg.setAttribute("viewBox", `${vx} ${vy} ${vw} ${vh}`);
      const px = svg.getBoundingClientRect().width || 800;
      k = Math.min(1.4, Math.max(1, 480 / px));
      const view = state.view, plan = view !== "existing", phases = view === "phases";
      const col = id => colorOf(id, view);
      const op = phases ? 0.8 : 1;

      // Context: street, sidewalk, backyard, house, paving. Not tappable.
      el("rect", { x: vx, y: vy, width: vw, height: vh, fill: C.paper });
      el("rect", { x: -26, y: -10, width: 11, height: 88, fill: C.street });
      text(-20.5, 54, "street", { fs: 2.2, rot: -90, fill: "#fff", w: 600 });
      el("line", { x1: -15, y1: -10, x2: -15, y2: 78, stroke: "#8d8d88", "stroke-width": 0.3 });
      el("rect", { x: -8, y: -10, width: 5, height: 88, fill: C.walk });
      text(-5.5, 50, "sidewalk", { fs: 1.4, rot: -90, fill: C.muted });
      el("rect", { x: -15, y: -10, width: 7, height: 11, fill: C.turf });
      poly([[69.3,50.6],[114,50.6],[114,67.8],[69.4,67.8]], C.back);
      poly([[74.6,0],[114,0],[114,50.6],[74.6,50.6]], C.back);
      poly([[48,0],[74.6,0],[74.6,9.8],[48.1,9.9]], C.back);
      poly([[0,0],[20.2,0],[20.2,3.5],[0.6,3.7]], C.turf);
      poly([[20.2,0],[48,0],[48,3],[20.2,3.5]], C.turf);
      poly([[-3,0],[0.6,3.7],[-0.2,27.5],[-3,27.5]], C.bee);

      // Existing bee lawn: the boulevard and the open front lawn.
      zone("blvd", G.blvd, col("blvd"));
      zone("z1", G.z1, col("z1"));
      if (!plan) zone("shade", [[33,51.3],[46.6,51.1],[69,50.6],[69.4,67.8],[33,67.8]], col("shade"));

      poly(G.apron, C.conc);
      poly(G.drive, C.conc);
      poly(G.walk, C.conc, { stroke: "rgba(0,0,0,.2)", sw: 0.12 });
      poly(G.deck, C.deck, { stroke: "rgba(0,0,0,.2)", sw: 0.12 });

      if (!plan) {
        zone("fdn", G.fdn, col("fdn"));
        zone("corner", G.cornerExisting, col("corner"));
      } else {
        zone("corner", G.cornerBed, col("corner"), { op });
        zone("fdn", G.stumpIsland, col("fdn"), { op: phases ? op : 0.85 });
        zone("fdn", G.fdn, phases ? C.p1 : C.fdn, { op });
        zone("shade", G.shadeN, col("shade"), { op });
        zone("shade", G.shadeS, col("shade"), { op });
        zone("path", G.path, col("path"));
        zone("border", G.border, col("border"), { op: phases ? op : 0.9 });
        hit(el("circle", { cx: 12.5, cy: 51.5, r: 3, fill: C.water, "fill-opacity": 0.55, stroke: C.water, "stroke-width": 0.3, "stroke-dasharray": ".6 .3" }), "rain");
        hit(el("circle", { cx: 19.6, cy: 40.2, r: 1.1, fill: C.water, stroke: "#3d7ea6", "stroke-width": 0.2 }), "rain");
        el("path", { d: "M19.6 41.3 C 18 46, 15 48, 13.8 49", fill: "none", stroke: "#3d7ea6", "stroke-width": 0.3, "stroke-dasharray": ".7 .4", "pointer-events": "none" });
      }
      el("circle", { cx: 12.4, cy: 30.5, r: 1.3, fill: C.stump, stroke: "#4a3522", "stroke-width": 0.25, "pointer-events": "none" });
      hit(el("circle", { cx: 12.4, cy: 30.5, r: 2.6, fill: "transparent" }), "stump");
      text(10.4, 29.8, "T1 stump", { fs: 1.2, anchor: "end", w: 600, fill: "#4a3522" });
      poly(G.house, C.house);
      text(47, 25, "HOUSE", { fs: 2.4, fill: "#fff", w: 700 });
      text(10, 15, "driveway", { fs: 1.6, fill: C.muted });

      hit(el("polygon", { points: pts(G.hive), fill: C.hive, stroke: "#6b5520", "stroke-width": 0.15 }), "hive");
      text(61.8, 54.6, "old hive", { fs: 1.1, fill: "#fff" });
      el("line", { x1: 7.4, y1: 67.6, x2: 114, y2: 67.6, stroke: "#6b5136", "stroke-width": 0.6 });
      text(24, 70.4, "neighbor's 6 ft privacy fence", { fs: 1.3, fill: C.muted });
      el("line", { x1: 69, y1: 50.6, x2: 69.4, y2: 67.8, stroke: "#5b4a3a", "stroke-width": 0.45 });
      text(71.2, 59, "backyard fence", { fs: 1.2, rot: 90, fill: C.muted });
      text(22.2, 31, "door", { fs: 1.2, anchor: "start", fill: "#fff" });
      el("polygon", { points: pts(G.lot), fill: "none", stroke: C.lot, "stroke-width": 0.25, "stroke-dasharray": "1.2 .6", "pointer-events": "none" });

      if (plan) {
        const L = phases
          ? [[33.5,45.2,"Phase 1"],[6.5,37.5,"Phase 1"],[42,64,"Phase 2"],[6,49,"touch-ups"],[17,64,"Phase 3"]]
          : [[33.5,45.2,"corner prairie"],[42,64,"shade bed"],[17,64,"south border"],[6,49,"bee lawn"],[6.5,37.5,"stump island"]];
        L.forEach(([x, y, s]) => text(x, y, s, { fs: 1.7, w: 600 }));
        if (!phases) text(38.5, 58.2, "path", { fs: 1.2, fill: C.muted });
      } else {
        [[8,48,"bee lawn"],[38.5,45.5,"bed"],[51,62,"lawn (under T4)"]].forEach(([x, y, s]) => text(x, y, s, { fs: 1.6, fill: C.muted }));
      }
      text(-11.5, 54, "boulevard", { fs: 1.5, rot: -90, fill: C.muted, w: 600 });

      if (state.trees) {
        TREES.forEach(t => {
          // The canopy is click-through so the beds underneath stay tappable;
          // the trunk marker (with a finger-sized hit area) selects the tree.
          el("circle", { cx: t.c[0], cy: t.c[1], r: t.r, fill: C.tree, "fill-opacity": 0.12, stroke: C.tree, "stroke-width": 0.25, "stroke-dasharray": "1 .5", "pointer-events": "none" });
          el("circle", { cx: t.c[0], cy: t.c[1], r: 0.6, fill: C.tree, "pointer-events": "none" });
          hit(el("circle", { cx: t.c[0], cy: t.c[1], r: 2.4, fill: "transparent" }), t.id);
          text(t.c[0] + 1.2, t.c[1] - 1, t.id, { fs: 1.5, anchor: "start", fill: C.tree, w: 700 });
        });
      }

      const right = vx + vw;
      if (state.dims) {
        const d = "#555", fx = right - 3.5;
        el("line", { x1: fx, y1: 0, x2: fx, y2: 67.8, stroke: d, "stroke-width": 0.15 });
        text(fx + 1.8, 34, "≈68 ft frontage", { fs: 1.4, rot: 90, fill: d });
        el("line", { x1: 0, y1: -2.5, x2: 114, y2: -2.5, stroke: d, "stroke-width": 0.15 });
        text(48, -3.6, "≈114 ft lot depth →", { fs: 1.4, fill: d });
        el("line", { x1: -15, y1: 73.5, x2: 20.8, y2: 73.5, stroke: d, "stroke-width": 0.15 });
        text(2.9, 75.8, "curb → house front ≈ 36 ft", { fs: 1.3, fill: d });
      }
      el("rect", { x: 0, y: -5.6, width: 10, height: 0.8, fill: "#333" });
      el("rect", { x: 10, y: -5.6, width: 10, height: 0.8, fill: "#fff", stroke: "#333", "stroke-width": 0.1 });
      text(0, -6.6, "0", { fs: 1.2 }); text(10, -6.6, "10", { fs: 1.2 }); text(20, -6.6, "20 ft", { fs: 1.2 });
      // True north is ~9° counter-clockwise from plan north.
      const g = el("g", { transform: `translate(${right - 6} -4.2) rotate(-8.9)` });
      el("path", { d: "M0 -3 L1.1 1.4 L0 .6 L-1.1 1.4 Z", fill: "#333" }, g);
      const tn = el("text", { x: 0, y: -3.3, "font-size": 1.8 * k, "text-anchor": "middle", fill: "#333", "font-weight": 700 }, g);
      tn.textContent = "N";

      if (state.sel) mark(state.sel);
    }

    // The selection is drawn as an outline layer on top of everything, so a
    // big shape (the lawn) never covers the beds drawn over it.
    function mark(id) {
      svg.querySelectorAll(".zone.sel").forEach(e => e.classList.remove("sel"));
      svg.querySelector(".sel-layer")?.remove();
      const layer = el("g", { class: "sel-layer", "pointer-events": "none" });
      (Z[id] || []).forEach(e => {
        e.classList.add("sel");
        const c = e.cloneNode(false);
        c.removeAttribute("class"); c.removeAttribute("tabindex"); c.removeAttribute("role"); c.removeAttribute("aria-label");
        c.setAttribute("fill", "none");
        c.setAttribute("stroke", C.sel);
        c.setAttribute("stroke-width", e.tagName === "circle" && +e.getAttribute("r") < 3 ? 0.5 : 0.7);
        c.removeAttribute("stroke-dasharray");
        c.setAttribute("stroke-linejoin", "round");
        layer.appendChild(c);
      });
    }
    function select(id, opts = {}) {
      if (state.view === "existing" && PLAN_ONLY.has(id)) {
        state.view = "plan";
        draw();
        opts.viewChanged = true;
      }
      state.sel = id;
      mark(id);
      onSelect(id, opts);
    }

    svg.addEventListener("click", e => {
      const z = e.target.closest(".zone");
      if (z) select(z.dataset.z, { fromMap: true });
    });
    svg.addEventListener("keydown", e => {
      const z = e.target.closest(".zone");
      if (z && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); select(z.dataset.z, { fromMap: true }); }
    });

    let rt, lastW = 0;
    new ResizeObserver(([entry]) => {
      const w = Math.round(entry.contentRect.width);
      if (Math.abs(w - lastW) < 8) return;
      lastW = w;
      clearTimeout(rt);
      rt = setTimeout(draw, 80);
    }).observe(svg);

    function legend() {
      const rows = state.view === "phases"
        ? [[C.p1, "Phase 1 · fall 2026 to spring 2027"], [C.p2, "Phase 2 · 2027"], [C.p3, "Phase 3 · 2028"], [C.bee, "Existing bee lawn"]]
        : state.view === "plan"
        ? [[C.prairie, "Sun prairie bed"], [C.shade, "Shade / woodland bed"], [C.bee, "Bee lawn (existing)"], [C.fdn, "Foundation shrubs"], [C.water, "Rain barrel + overflow"]]
        : [[C.bee, "Bee lawn"], [C.turf, "Turf"], [C.fdn, "Existing beds"], [C.conc, "Paving"]];
      if (state.trees) rows.push([null, "Tree canopy (approx.)"]);
      return rows;
    }

    return {
      state, draw, select, legend,
      colorOf: id => colorOf(id, state.view),
      set(key, val) { state[key] = val; draw(); },
    };
  }

  return { create };
})();
