/* HarvestRadar map: SVG regions on an Equal Earth Blue Marble base, coloured with the Radar Night risk
   ramp, hotspot rings, dekad scrubber (play, pause, arrows). Offline: no external request. */
(function () {
  const RAMP = [[-3, [126, 176, 255]], [-2, [63, 116, 216]], [-1, [38, 64, 106]], [0, [30, 40, 51]],
                [1, [138, 100, 36]], [2, [245, 169, 58]], [3, [255, 90, 54]]];
  function ramp(z) {
    z = Math.max(-3, Math.min(3, z));
    for (let i = 0; i < RAMP.length - 1; i++) {
      const [z0, c0] = RAMP[i], [z1, c1] = RAMP[i + 1];
      if (z >= z0 && z <= z1) {
        const t = (z - z0) / (z1 - z0);
        return c0.map((v, k) => Math.round(v + (c1[k] - v) * t));
      }
    }
    return [255, 90, 54];
  }
  const NS = "http://www.w3.org/2000/svg";
  const el = (n, a = {}) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); return e; };

  window.RadarMap = function (root, cfg) {
    const vb = cfg.viewBox;
    const svg = el("svg", { viewBox: vb.join(" "), preserveAspectRatio: "xMidYMid meet", class: "map-svg",
                            role: "img", "aria-label": cfg.ariaLabel || "Stress map" });
    const defs = el("defs");
    defs.innerHTML = `<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="${vb[2] / 500}" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>`;
    svg.appendChild(defs);
    const b = cfg.base;
    svg.appendChild(el("image", { href: b.href, x: b.x, y: b.y, width: b.w, height: b.h, preserveAspectRatio: "none",
                                  opacity: b.opacity || 1 }));
    if (cfg.countries) svg.appendChild(el("path", { d: cfg.countries, fill: "none", stroke: "rgba(199,209,219,0.16)",
                                                     "stroke-width": cfg.borderWidth || 0.6, "vector-effect": "non-scaling-stroke" }));
    const g = el("g");
    const paths = cfg.regions.map((r) => {
      const p = el("path", { d: r.d, stroke: "#0B0F14", "stroke-width": 0.7, "vector-effect": "non-scaling-stroke",
                             "stroke-opacity": 0.9, "data-i": r.i });
      g.appendChild(p);
      return p;
    });
    svg.appendChild(g);
    const rings = el("g", { class: "rings" });
    svg.appendChild(rings);
    root.querySelector(".map-stage").appendChild(svg);

    const label = root.querySelector(".map-label");
    const ticks = root.querySelector(".ticks");
    const playBtn = root.querySelector(".play");
    const speedBtn = root.querySelector(".speed");
    const tip = root.querySelector(".tip");
    const strip = root.querySelector(".strip");
    let idx = cfg.start, timer = null, speed = 1;

    // scrubber ticks: one per frame, height from the frame's weighted positive stress
    cfg.frames.forEach((f, i) => {
      const t = document.createElement("button");
      t.className = "tick"; t.setAttribute("aria-label", "Dekad " + f.label); t.tabIndex = -1;
      t.style.setProperty("--h", (8 + 26 * Math.min(1, f.tick)).toFixed(1) + "px");
      t.addEventListener("click", () => { stop(); show(i); });
      ticks.appendChild(t);
    });

    // film strip (episode mode): small copies of the map at chosen frames
    const thumbs = [];
    if (strip && cfg.strip) {
      cfg.strip.forEach((fi) => {
        const card = document.createElement("button");
        card.className = "thumb"; card.setAttribute("aria-label", "Dekad " + cfg.frames[fi].label);
        const s = el("svg", { viewBox: vb.join(" "), preserveAspectRatio: "xMidYMid slice" });
        s.appendChild(el("image", { href: b.href, x: b.x, y: b.y, width: b.w, height: b.h, preserveAspectRatio: "none" }));
        const gg = el("g");
        cfg.regions.forEach((r) => {
          const v = cfg.frames[fi].values[r.i];
          const c = ramp(v == null ? 0 : v), o = 0.35 + 0.65 * Math.min(1, Math.abs(v || 0) / 2);
          gg.appendChild(el("path", { d: r.d, fill: `rgb(${c})`, "fill-opacity": o, stroke: "#0B0F14",
                                       "stroke-width": 0.4, "vector-effect": "non-scaling-stroke" }));
        });
        s.appendChild(gg);
        card.appendChild(s);
        const cap = document.createElement("div"); cap.className = "thumb-label"; cap.textContent = cfg.frames[fi].short;
        card.appendChild(cap);
        card.addEventListener("click", () => { stop(); show(fi); });
        strip.appendChild(card);
        thumbs.push([fi, card]);
      });
    }

    function drawRings(hs) {
      rings.innerHTML = "";
      const R = cfg.ringRadius;
      hs.forEach(([x, y], k) => {
        const grp = el("g", { class: "ping", style: `animation-delay:${k * 0.5}s` });
        [1, 1.9, 2.9].forEach((m, j) => grp.appendChild(el("circle", { cx: x, cy: y, r: R * m, fill: "none",
          stroke: "#FFB547", "stroke-opacity": [0.9, 0.5, 0.25][j], "stroke-width": 1.4, "vector-effect": "non-scaling-stroke" })));
        grp.appendChild(el("circle", { cx: x, cy: y, r: R * 0.32, fill: "#FFB547", filter: "url(#glow)" }));
        rings.appendChild(grp);
      });
    }

    function show(i) {
      idx = (i + cfg.frames.length) % cfg.frames.length;
      const f = cfg.frames[idx];
      paths.forEach((p, k) => {
        const v = f.values[k];
        if (v == null) { p.setAttribute("fill", "none"); return; }
        const c = ramp(v);
        p.setAttribute("fill", `rgb(${c[0]},${c[1]},${c[2]})`);
        p.setAttribute("fill-opacity", (0.35 + 0.65 * Math.min(1, Math.abs(v) / 2)).toFixed(3));
      });
      drawRings(f.hotspots || []);
      if (label) label.textContent = cfg.labelPrefix + " · " + (cfg.labelWord ? cfg.labelWord + " " : "") + f.label;
      ticks.querySelectorAll(".tick").forEach((t, k) => t.classList.toggle("on", k <= idx));
      ticks.querySelectorAll(".tick").forEach((t, k) => t.classList.toggle("now", k === idx));
      thumbs.forEach(([fi, card]) => card.classList.toggle("active", fi === idx));
      const out = root.querySelector(".frame-date"); if (out) out.textContent = f.date;
    }
    function stop() { if (timer) { clearInterval(timer); timer = null; } root.classList.remove("playing"); playBtn.setAttribute("aria-label", "Play"); }
    function play() {
      if (cfg.capture) return;
      stop(); root.classList.add("playing"); playBtn.setAttribute("aria-label", "Pause");
      if (idx >= cfg.frames.length - 1) show(0);
      timer = setInterval(() => { if (idx >= cfg.frames.length - 1) { stop(); return; } show(idx + 1); }, speed === 1 ? 400 : 160);
    }
    playBtn.addEventListener("click", () => (timer ? stop() : play()));
    if (speedBtn) speedBtn.addEventListener("click", () => {
      speed = speed === 1 ? 2.5 : 1; speedBtn.textContent = "x" + speed; speedBtn.classList.toggle("on", speed !== 1);
      if (timer) play();
    });
    root.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") { stop(); show(idx + 1); e.preventDefault(); }
      else if (e.key === "ArrowLeft") { stop(); show(idx - 1); e.preventDefault(); }
      else if (e.key === " " && e.target === root) { timer ? stop() : play(); e.preventDefault(); }
    });
    if (!cfg.capture) {
      paths.forEach((p, k) => {
        p.addEventListener("mousemove", (e) => {
          const r = cfg.regions[k], v = cfg.frames[idx].values[k];
          tip.innerHTML = `<b>${r.name}</b><span>${r.country}</span><em>${v == null ? "no data" : (v >= 0 ? "+" : "") + v.toFixed(2)}</em>`;
          const box = root.getBoundingClientRect();
          tip.style.left = (e.clientX - box.left + 14) + "px"; tip.style.top = (e.clientY - box.top + 14) + "px";
          tip.style.opacity = 1;
        });
        p.addEventListener("mouseleave", () => { tip.style.opacity = 0; });
      });
    } else {
      root.classList.add("capture");
    }
    show(idx);
    if (cfg.autoplay && !cfg.capture) play();
    return { stop: stop, play: play, show: show };
  };
})();
