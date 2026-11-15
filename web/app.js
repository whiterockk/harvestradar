/* HarvestRadar static web edition: renders the five pages from the embedded data snapshot. */
(function () {
  "use strict";
  const D = JSON.parse(document.getElementById("data").textContent);
  const CROPS = ["maize", "coffee", "cocoa"];
  const VIEWS = { stress: "Stress map", commodity: "Commodity", replay: "Replay", note: "Daily note", method: "Method" };
  const S = { crop: "maize", episode: Object.keys(D.episodes)[0], note: null, shap: {}, email: false };
  let mapHandle = null;

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const sg = (x, n = 2) => (x == null || !isFinite(x) ? "n/a" : (x >= 0 ? "+" : "") + x.toFixed(n));
  const fmtPrice = (key, x) => key === "cocoa" ? Math.round(x).toLocaleString("en-US") : x.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const dLabel = (s) => { const d = new Date(s + "T00:00:00Z"); return d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); };
  const MONTH = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const dLong = (s) => { const d = new Date(s + "T00:00:00Z"); return d.getUTCDate() + " " + MONTH[d.getUTCMonth()] + " " + d.getUTCFullYear(); };
  const pct = (x, n = 1) => sg(x, n) + "%";
  const glyph = (k, size = 22) => '<span class="gl">' + D.glyphs[k].replace(/width="\d+" height="\d+"/, 'width="' + size + '" height="' + size + '"') + "</span>";

  function sparkline(values, w = 132, h = 46, color = "var(--signal)") {
    const v = values.filter((x) => x != null && isFinite(x));
    if (v.length < 2) return '<svg width="' + w + '" height="' + h + '"></svg>';
    const pad = 5, lo = Math.min(...v), hi = Math.max(...v) === lo ? lo + 1 : Math.max(...v);
    const xs = v.map((_, i) => pad + (i * (w - 2 * pad)) / (v.length - 1));
    const ys = v.map((y) => h - pad - ((y - lo) / (hi - lo)) * (h - 2 * pad));
    let d = "M" + xs[0].toFixed(1) + "," + ys[0].toFixed(1);
    for (let i = 1; i < v.length; i++) { const cx = (xs[i - 1] + xs[i]) / 2; d += " C" + cx.toFixed(1) + "," + ys[i - 1].toFixed(1) + " " + cx.toFixed(1) + "," + ys[i].toFixed(1) + " " + xs[i].toFixed(1) + "," + ys[i].toFixed(1); }
    const id = "g" + Math.random().toString(36).slice(2, 8);
    return '<svg class="spark" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + " " + h + '" aria-hidden="true"><defs><linearGradient id="' + id + '" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFB547" stop-opacity=".28"/><stop offset="1" stop-color="#FFB547" stop-opacity="0"/></linearGradient></defs>' +
      '<path d="' + d + " L" + xs[xs.length - 1].toFixed(1) + "," + h + " L" + xs[0].toFixed(1) + "," + h + ' Z" fill="url(#' + id + ')"/><path d="' + d + '" fill="none" stroke="#FFB547" stroke-width="2" stroke-linecap="round"/>' +
      '<circle cx="' + xs[xs.length - 1].toFixed(1) + '" cy="' + ys[ys.length - 1].toFixed(1) + '" r="3.6" fill="#FFB547" style="filter:drop-shadow(0 0 5px #FFB547)"/></svg>';
  }

  const panel = (title, body, source, extra = "") => '<section class="glass" style="' + extra + '"><div class="caps" style="margin-bottom:12px">' + title + "</div>" + body + (source ? '<div class="source">' + source + "</div>" : "") + "</section>";
  const chip = (t, amber) => '<span class="chip' + (amber ? " amber" : "") + '">' + esc(t) + "</span>";
  const badge = (t, ok) => '<span class="badge"><span style="color:' + (ok ? "var(--signal)" : "var(--heat)") + '">' + (ok ? "&#10003;" : "&#10005;") + "</span>" + esc(t) + "</span>";

  function barRows(rows, unit, labelW) {
    if (!rows.length) return '<p style="color:var(--muted)">No data.</p>';
    const m = Math.max(...rows.map((r) => Math.abs(r.value))) || 1;
    return rows.map((r) => {
      const f = Math.min(1, Math.abs(r.value) / m), amber = r.raises;
      const b = '<div class="b" style="width:' + Math.max(2, 100 * f).toFixed(1) + "%;background:" + (amber ? "linear-gradient(90deg,#8A6424,#F5A93A);box-shadow:0 0 12px rgba(255,181,71,.45)" : "#3F74D8;box-shadow:0 0 10px rgba(63,116,216,.4);margin-left:auto") + '"></div>';
      return '<div class="brow" style="grid-template-columns:minmax(110px,' + (labelW || 200) + 'px) minmax(0,1fr) minmax(0,1fr) 84px"><div class="lab"><div>' + esc(r.label) + "</div>" + (r.note ? '<div class="mono" style="font-size:13px;color:var(--muted)">' + esc(r.note) + "</div>" : "") +
        '</div><div class="neg">' + (amber ? "" : b) + '</div><div class="pos">' + (amber ? b : "") + '</div><div class="v" style="color:' + (amber ? "var(--signal)" : "var(--frost-2)") + '">' + sg(r.value) + (unit ? " " + unit : "") + "</div></div>";
    }).join("");
  }

  function ticker() {
    return '<div class="grid3">' + CROPS.map((k) => {
      const c = D.crops[k], z = c.latest.z, s = c.risk.z.slice(-26);
      return '<button class="glass tick-card' + (k === S.crop ? " sel" : "") + '" data-crop="' + k + '" aria-label="Select ' + esc(c.label) + '">' + glyph(c.glyph, 26) +
        '<div style="min-width:0"><div class="caps" style="white-space:nowrap">' + esc(c.display) + ' &middot; RISK INDEX</div><div class="val' + (z >= 2 ? " glow" : "") + '">' + sg(z) + "</div></div>" + sparkline(s) + "</button>";
    }).join("") + "</div>";
  }

  /* ---------- map ---------- */
  const PLAY = '<svg class="i-play" viewBox="0 0 24 24"><path d="M7 4.5v15l13-7.5z" fill="#0B0F14"/></svg><svg class="i-pause" viewBox="0 0 24 24"><path d="M6 4h4.5v16H6zM13.5 4H18v16h-4.5z" fill="#0B0F14"/></svg>';
  const LEG = ["#7EB0FF", "#3F74D8", "#26406A", "#1E2833", "#8A6424", "#F5A93A", "#FF5A36"].map((c) => '<i style="background:' + c + '"></i>').join("");
  function mapShell(mode, height, range) {
    return '<div class="radar ' + mode + '" tabindex="0" style="height:' + height + 'px"><div class="map-stage"></div>' +
      '<div class="map-label"></div><div class="legend"><div class="sw">' + LEG + '</div><div class="lg"><span>lower stress</span><span>higher stress</span></div></div>' +
      '<div class="bar"><button class="play" aria-label="Play">' + PLAY + '</button><div class="ticks"></div><div class="range">' + esc(range) + '</div><button class="speed" aria-label="Playback speed">x1</button></div>' +
      (mode === "episode" ? '<div class="strip"></div>' : "") + '<div class="tip"></div></div>';
  }
  function mountMap(cfg) {
    const el = document.querySelector(".radar");
    if (!el) return;
    if (mapHandle && mapHandle.stop) mapHandle.stop();
    mapHandle = window.RadarMap(el, cfg);
  }
  const mapH = () => (window.innerWidth < 700 ? 360 : 700);

  /* ---------- charts ---------- */
  function niceTicks(lo, hi, n) {
    const span = hi - lo, step0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= n) || 10 * mag;
    const out = []; for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(6)); return out;
  }
  function indexChart(key) {
    const c = D.crops[key], W = 1000, H = 480, m = { l: 62, r: 78, t: 40, b: 34 };
    const end = new Date(c.latest.date + "T00:00:00Z"), start = new Date(end.getTime() - 64 * 7 * 864e5);
    const R = c.riskRecent.d.map((d, i) => [new Date(d + "T00:00:00Z"), c.riskRecent.z[i]]).filter((p) => p[0] >= start && p[1] != null);
    const P = c.pricesRecent.d.map((d, i) => [new Date(d + "T00:00:00Z"), c.pricesRecent.c[i]]).filter((p) => p[0] >= start);
    const zs = R.map((p) => p[1]), lo = Math.min(-0.5, Math.min(...zs) - 0.4), hi = Math.max(2.6, Math.max(...zs) + 0.4);
    const pv = P.map((p) => p[1]), plo = Math.min(...pv), phi = Math.max(...pv);
    const x = (d) => m.l + ((d - start) / (end - start)) * (W - m.l - m.r);
    const y = (v) => m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b);
    const y2 = (v) => m.t + (1 - (v - plo) / (phi - plo || 1)) * (H - m.t - m.b);
    let g = "";
    c.windows.forEach(([s0, e0, st]) => {
      const xs = x(new Date(s0 + "T00:00:00Z")), xe = x(new Date(e0 + "T00:00:00Z"));
      g += '<rect x="' + xs + '" y="' + m.t + '" width="' + Math.max(1, xe - xs) + '" height="' + (H - m.t - m.b) + '" fill="rgba(255,181,71,.07)"/>' +
        '<text x="' + (xs + xe) / 2 + '" y="' + (m.t - 10) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + esc((c.mainCountry + " " + st + " window").toUpperCase()) + "</text>";
    });
    niceTicks(lo, hi, 7).forEach((v) => { g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="' + (v === 0 ? "#2A3646" : "#1E2935") + '"/><text x="' + (m.l - 8) + '" y="' + (y(v) + 4) + '" text-anchor="end" font-size="13" fill="#FFB547">' + (v > 0 ? "+" : "") + v + "</text>"; });
    niceTicks(plo, phi, 6).forEach((v) => { g += '<text x="' + (W - m.r + 8) + '" y="' + (y2(v) + 4) + '" font-size="13" fill="#C7D1DB">' + (key === "cocoa" ? Math.round(v).toLocaleString("en-US") : v) + "</text>"; });
    g += '<text transform="translate(16,' + (m.t + (H - m.t - m.b) / 2) + ') rotate(-90)" text-anchor="middle" font-size="13" fill="#FFB547">RISK INDEX (0 = NORMAL)</text>';
    g += '<text transform="translate(' + (W - 12) + "," + (m.t + (H - m.t - m.b) / 2) + ') rotate(90)" text-anchor="middle" font-size="13" fill="#C7D1DB">' + esc(c.priceUnit.toUpperCase()) + "</text>";
    for (let k = 0; k < 16; k++) { const d = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1 + 2 * k, 1)); if (d > end) break; g += '<text x="' + x(d) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + MON[d.getUTCMonth()] + " " + d.getUTCFullYear() + "</text>"; }
    g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(2) + '" y2="' + y(2) + '" stroke="#F5A93A" stroke-dasharray="6 6" stroke-width="1.2"/><text x="' + (m.l + 6) + '" y="' + (y(2) - 6) + '" font-size="13" fill="#F5A93A">+2: RARE</text>';
    const pl = P.map((p, i) => (i ? "L" : "M") + x(p[0]).toFixed(1) + "," + y2(p[1]).toFixed(1)).join(" ");
    const il = R.map((p, i) => (i ? "L" : "M") + x(p[0]).toFixed(1) + "," + y(p[1]).toFixed(1)).join(" ");
    const last = R[R.length - 1];
    g += '<path d="' + pl + '" fill="none" stroke="#EAF0F5" stroke-opacity=".7" stroke-width="1.5"/>';
    g += '<path d="' + il + " L" + x(last[0]) + "," + y(0) + " L" + x(R[0][0]) + "," + y(0) + ' Z" fill="rgba(255,181,71,.08)"/>';
    g += '<path d="' + il + '" fill="none" stroke="rgba(255,181,71,.2)" stroke-width="10" stroke-linejoin="round"/><path d="' + il + '" fill="none" stroke="#FFB547" stroke-width="3" stroke-linejoin="round"/>';
    g += '<circle cx="' + x(last[0]) + '" cy="' + y(last[1]) + '" r="9" fill="rgba(255,181,71,.25)"/><circle cx="' + x(last[0]) + '" cy="' + y(last[1]) + '" r="4.5" fill="#FFB547"/>';
    return '<svg viewBox="0 0 ' + W + " " + H + '" width="100%" role="img" aria-label="Harvest-risk index and futures price, last 64 weeks">' + g + "</svg>";
  }
  function pathChart(ev) {
    const W = 600, H = 200, m = { l: 34, r: 12, t: 12, b: 28 };
    const P = ev.path.map((p) => [new Date(p.date + "T00:00:00Z"), p.risk_z]);
    const zs = P.map((p) => p[1]), lo = Math.min(-0.5, Math.min(...zs) - 0.3), hi = Math.max(2.5, Math.max(...zs) + 0.4);
    const t0 = P[0][0], t1 = P[P.length - 1][0];
    const x = (d) => m.l + ((d - t0) / (t1 - t0)) * (W - m.l - m.r), y = (v) => m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b);
    let g = "";
    niceTicks(lo, hi, 4).forEach((v) => { g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="#1E2935"/><text x="' + (m.l - 6) + '" y="' + (y(v) + 4) + '" text-anchor="end" font-size="13" fill="#8A9AAB">' + v + "</text>"; });
    const months = []; for (let d = new Date(Date.UTC(t0.getUTCFullYear(), t0.getUTCMonth() + 1, 1)); d < t1; d = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1))) months.push(d);
    const stepM = Math.ceil(months.length / 5);
    months.forEach((d, i) => { if (i % stepM === 0) g += '<text x="' + x(d) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + MON[d.getUTCMonth()] + " " + String(d.getUTCFullYear()).slice(2) + "</text>"; });
    g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(2) + '" y2="' + y(2) + '" stroke="#F5A93A" stroke-dasharray="6 6"/>';
    const l = P.map((p, i) => (i ? "L" : "M") + x(p[0]).toFixed(1) + "," + y(p[1]).toFixed(1)).join(" ");
    g += '<path d="' + l + '" fill="none" stroke="rgba(255,181,71,.2)" stroke-width="9"/><path d="' + l + '" fill="none" stroke="#FFB547" stroke-width="2.6"/>';
    const mk = ev.first_above_2 || ev.peak_date, pt = P.find((p) => p[0].toISOString().slice(0, 10) === mk);
    if (pt) g += '<circle cx="' + x(pt[0]) + '" cy="' + y(pt[1]) + '" r="10" fill="rgba(255,181,71,.28)"/><circle cx="' + x(pt[0]) + '" cy="' + y(pt[1]) + '" r="5" fill="#FFB547"/>';
    return '<svg viewBox="0 0 ' + W + " " + H + '" width="100%" role="img" aria-label="Index path during the episode">' + g + "</svg>";
  }

  /* ---------- views ---------- */
  function viewStress() {
    const c = D.crops[S.crop], mp = c.map, f = mp.frames;
    const first = new Date(f[0].date + "T00:00:00Z"), lastF = new Date(f[f.length - 1].date + "T00:00:00Z");
    const rng = (MON[first.getUTCMonth()] + " · " + MON[lastF.getUTCMonth()] + " " + lastF.getUTCFullYear()).toUpperCase();
    const rows = mp.top5.map((r) => '<div class="rank"><span class="mono" style="font-size:13px;color:var(--muted)">' + String(r.rank).padStart(2, "0") + "</span>" + glyph(c.glyph, 18) + '<span class="name">' + esc(r.name) + '</span><span style="font-size:14px;color:var(--muted)">' + esc(r.iso) + '</span><span class="bar"><i style="width:' + Math.max(3, 100 * r.frac).toFixed(0) + "%;background:linear-gradient(90deg,#8A6424,#F5A93A 70%," + (r.hot ? "#FF5A36" : "#FFB547") + ')"></i></span></div>').join("");
    const n = D.notes.find((x) => x.week === D.asOf && x.commodity === S.crop);
    const o = D.oni;
    const html = ticker() + '<div class="main"><div class="col">' + mapShell("world", mapH(), rng) +
      '<div class="source" style="margin-top:0">' + esc(c.label) + ": " + c.regionsN + " producing regions, " + Math.round(100 * c.coverage) + "% of world output (MapSPAM 2020). Stress combines heat, rainfall and soil moisture, compared with the same 10 days in " + D.meta.climBase[0] + "-" + D.meta.climBase[1] + ". Weather: NASA POWER.</div></div>" +
      '<div class="col">' + panel("MOST STRESSED REGIONS, WEIGHTED BY OUTPUT", rows, "10 days to " + dLong(mp.dekad) + ". Ranked by stress times the region's share of world output.") +
      '<section class="glass"><div class="caps">EL NI&Ntilde;O &middot; BACKGROUND</div><div style="font-family:var(--display);font-weight:700;font-size:22px;margin-top:8px">' + esc(o.strength.charAt(0).toUpperCase() + o.strength.slice(1)) + '</div><div style="display:flex;align-items:flex-end;justify-content:space-between;gap:12px;flex-wrap:wrap"><div><span class="mono" style="font-size:30px;color:var(--signal)">' + sg(o.value) + ' &deg;C</span><div style="font-size:14px;color:var(--muted);margin-top:2px">Pacific sea temperature vs normal, ' + esc(o.period) + "</div></div>" + sparkline(o.series, 200, 48) + '</div><div class="source">NOAA Oceanic Ni&ntilde;o Index, published ' + dLong(o.available_at) + ". Shown for context: it is not part of the index.</div></section>" +
      (n ? '<a class="glass" href="#note" style="display:flex;align-items:center;gap:16px;text-decoration:none;color:var(--frost)"><span style="border-radius:10px;overflow:hidden;display:inline-flex;flex:none">' + D.marks.signal + '</span><div><div style="font-size:17px;font-weight:500">Today\'s note is ready</div><div style="font-size:14px;color:var(--muted)">' + n.checks.filter(Boolean).length + ' of 3 checks passed</div></div><span class="mono" style="margin-left:auto;font-size:13px;color:var(--signal)">OPEN &rarr;</span></a>' : "") +
      "</div></div>";
    return { html: html, after: () => mountMap({ viewBox: D.map.viewBox, base: Object.assign({}, D.map.base, { href: BASE_IMG }), countries: mp.borders, regions: mp.regions, frames: f, start: mp.start, ringRadius: 230, labelPrefix: "STRESS VS NORMAL", labelWord: "", rangeLabel: rng, capture: false, autoplay: false, ariaLabel: c.label + " stress map" }) };
  }

  function priceCard(k) {
    const c = D.crops[k], pi = (D.priceImpact.commodities || {})[k];
    if (!pi) return "";
    if (!pi.reliable) {
      return panel("WHAT IT MEANS FOR THE PRICE", '<div style="font-size:17px;color:var(--frost-2);line-height:1.6">No reliable link between world supply gaps and the ' + esc(c.label.toLowerCase()) + " price since " + pi.years[0] + " (" + pi.n + " years). No price estimate is shown.</div>", "Marketing-year average futures price against the realised world supply gap, " + pi.years[0] + "-" + pi.years[1] + ".");
    }
    const per = -pi.slope_pct_per_pct;
    return panel("WHAT IT MEANS FOR THE PRICE", '<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap"><span class="mono" style="font-size:40px;color:var(--signal)">' + pct(pi.implied_pct) + '</span><span style="color:var(--frost-2)">expected move of the futures price over the marketing year</span></div>' +
      '<div style="font-size:16px;color:var(--frost-2);margin-top:8px;line-height:1.6">Likely between <span class="mono">' + pct(pi.low_pct) + '</span> and <span class="mono">' + pct(pi.high_pct) + "</span> (8 chances in 10). Since " + pi.years[0] + ", each 1% of world supply missing came with about <span class=\"mono\">" + pct(per) + "</span> on the " + esc(c.label.toLowerCase()) + " price.</div>",
      "Based on " + pi.n + " marketing years, " + pi.years[0] + "-" + pi.years[1] + "; the supply gap explains " + Math.round(100 * pi.r2) + "% of the yearly price changes. A rough guide, not a price forecast.");
  }

  function viewCommodity() {
    const k = S.crop, c = D.crops[k], L = c.latest;
    const rows = L.contributors.map((x) => ({ label: x.name, value: x.contrib_pct, raises: x.contrib_pct < 0, note: x.season + " harvest: " + pct(x.pred_anom_pct) + " vs normal" + (x.window_open ? ", critical window open" : "") }));
    const countries = L.contributors.map((x) => x.country).filter((iso) => c.shap[iso]);
    const sel = S.shap[k] && countries.includes(S.shap[k]) ? S.shap[k] : countries[0];
    const name = (iso) => (L.contributors.find((x) => x.country === iso) || {}).name || iso;
    const sh = c.shap[sel];
    const shapRows = sh ? sh.rows.map(([lab, v]) => ({ label: lab, value: v, raises: v < 0 })) : [];
    const html = ticker() + '<div class="main c65"><div class="col"><div class="cards3">' +
      '<section class="glass" style="display:flex;align-items:center;gap:22px;min-height:164px">' + glyph(c.glyph, 52) + '<div style="min-width:0"><div class="caps">' + esc(c.display) + ' &middot; HARVEST-RISK INDEX</div><div class="mono glow hero-val" style="font-size:72px;line-height:1;color:var(--signal);font-weight:500;margin-top:6px">' + sg(L.z) + '</div><div class="source">' + dLong(L.date) + ". 0 is a normal season, above +2 is rare.</div></div></section>" +
      '<section class="glass" style="min-height:164px"><div class="caps">EXPECTED WORLD SUPPLY VS NORMAL</div><div class="mono" style="font-size:34px;margin-top:12px">' + pct(L.dp) + '</div><div class="source">Likely between ' + pct(L.lo) + " and " + pct(L.hi) + " (8 chances in 10), from the model's forecasts by country.</div></section>" +
      '<section class="glass" style="min-height:164px"><div class="caps">' + esc(c.priceLabel) + '</div><div class="mono" style="font-size:34px;margin-top:12px">' + fmtPrice(k, c.lastPrice.close) + '</div><div class="source">' + esc(c.priceUnit.charAt(0).toUpperCase() + c.priceUnit.slice(1)) + ", nearest contract, close on " + dLong(c.lastPrice.date) + ".</div></section></div>" +
      '<section class="glass" style="padding:16px 18px"><div style="display:flex;flex-wrap:wrap;gap:8px 22px;align-items:center;margin-bottom:6px"><span style="font-family:var(--display);font-weight:700;font-size:20px">Risk index and futures price, last 64 weeks</span><span style="display:inline-flex;align-items:center;gap:8px;color:var(--frost-2);font-size:14px"><i style="width:22px;height:3px;background:#FFB547;display:inline-block;border-radius:2px"></i>Risk index, left scale</span><span style="display:inline-flex;align-items:center;gap:8px;color:var(--frost-2);font-size:14px"><i style="width:22px;height:2px;background:#EAF0F5;display:inline-block;border-radius:2px"></i>' + esc(c.priceName) + ', right scale</span></div>' + indexChart(k) +
      '<div style="font-size:15px;color:var(--frost-2);line-height:1.6;margin-top:6px">How to read it: the orange line rises when the model expects less ' + esc(c.label.toLowerCase()) + " than usual for this time of year. The shaded band is the " + esc(c.mainCountry) + " critical window, when weather matters most for the harvest. The white line is the price, for comparison.</div></section></div>" +
      '<div class="col">' + priceCard(k) + panel("WHICH COUNTRIES DRIVE TODAY'S READING", barRows(rows, "", 240), "In points of world supply: each country's share of world output times its expected harvest gap. Amber raises the risk, blue lowers it.") +
      '<div class="chips" role="group" aria-label="Country">' + countries.map((iso) => '<button class="chip' + (iso === sel ? " on" : "") + '" data-shap="' + iso + '">' + esc(name(iso)) + "</button>").join("") + "</div>" +
      panel("WHICH WEATHER DRIVES THE FORECAST <span style='float:right;color:var(--signal)'>" + esc(name(sel).toUpperCase()) + "</span>", barRows(shapRows, "", 220), "In points of " + c.target + " vs normal. Contribution of each weather factor to the forecast for the " + (sh ? sh.season : "") + " harvest (SHAP values).") +
      "</div></div>";
    return { html: html, after: null };
  }

  function viewReplay() {
    const names = Object.keys(D.episodes), ev = D.episodes[S.episode], c = D.crops[ev.commodity];
    const fmt = (x) => ev.commodity === "cocoa" ? Math.round(x).toLocaleString("en-US") : String(+x.toFixed(2));
    let card;
    if (ev.first_above_2) {
      const cap = ev.verdict === "late" ? "after the price had already peaked on " + dLong(ev.price_max_date) + ": too late" : (ev.lead_text || "");
      card = '<section class="glass' + (ev.verdict === "late" ? "" : " amber") + '"><div class="caps">INDEX FIRST ABOVE +2</div><div class="mono glow" style="font-size:clamp(34px,3.4vw,52px);line-height:1.15;color:var(--signal);margin-top:10px">' + dLong(ev.first_above_2) + '</div><div style="font-size:17px;color:var(--frost-2)">' + esc(cap) + '</div><div class="source">Weekly index during the episode.</div></section>';
    } else {
      card = '<section class="glass"><div class="caps">HIGHEST INDEX IN THE EPISODE</div><div class="mono" style="font-size:clamp(34px,3.4vw,52px);line-height:1.15;color:var(--signal);margin-top:10px">' + sg(ev.peak_risk_z) + '</div><div style="font-size:17px;color:var(--frost-2)">on ' + dLong(ev.peak_date) + ": it never went above +2, the episode was missed.</div></section>";
    }
    const ch = ev.price_change_pct, hot = ch > 0, pi = (D.priceImpact.episodes || {})[S.episode];
    const exp = pi ? (pi.reliable ? '<div style="font-size:16px;color:var(--frost-2);margin-top:10px;line-height:1.6">Expected from the supply gap the model saw on ' + dLong(pi.date) + ': <span class="mono">' + pct(pi.implied_pct) + "</span> (likely " + pct(pi.low_pct) + " to " + pct(pi.high_pct) + ") over the marketing year. Actual move shown above.</div>" : '<div style="font-size:16px;color:var(--frost-2);margin-top:10px">No reliable supply-price link for this crop, so no expected move is shown.</div>') : "";
    const fromLabel = ev.price_from_kind === "signal" ? "from the signal" : "from the start of the episode";
    const price = '<section class="glass"><div class="caps">' + esc(c.priceLabel) + '</div><div style="font-size:14px;color:var(--muted);margin-top:4px">' + fromLabel + ", " + dLong(ev.price_from_date) + " to " + dLong(ev.price_to_date) + '</div><div style="display:flex;align-items:baseline;gap:16px;margin-top:10px;flex-wrap:wrap"><span class="mono" style="font-size:34px;color:var(--frost-2)">' + fmt(ev.price_from) + '</span><span style="color:var(--muted)">to</span><span class="mono" style="font-size:40px;color:' + (hot ? "var(--heat)" : "var(--frost)") + '">' + fmt(ev.price_to) + '</span><span class="mono" style="font-size:22px;color:' + (hot ? "var(--heat)" : "var(--frost-2)") + '">' + pct(ch) + "</span></div>" + exp + '<div class="source">' + esc(c.priceUnit.charAt(0).toUpperCase() + c.priceUnit.slice(1)) + (ev.price_max ? ". Highest price of the episode: " + fmt(ev.price_max) + " on " + dLong(ev.price_max_date) : "") + ".</div></section>";
    const y0 = ev.start.slice(0, 4), y1 = ev.end.slice(0, 4);
    const html = '<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap"><div class="chips" role="group" aria-label="Episode">' + names.map((n) => '<button class="chip' + (n === S.episode ? " on" : "") + '" data-episode="' + n + '">' + esc(D.episodes[n].label) + "</button>").join("") + "</div>" +
      (ev.model_trained_on_seasons_up_to ? chip("THE MODEL ONLY KNEW HARVESTS UP TO " + ev.model_trained_on_seasons_up_to, true) : "") + "</div>" +
      '<div class="main c65"><div class="col">' + mapShell("episode", mapH() + 60, ev.range) + '<div class="source" style="margin-top:0">Stress every 10 days, compared with ' + D.meta.climBase[0] + "-" + D.meta.climBase[1] + ". Press play, or use the arrow keys to step.</div></div>" +
      '<div class="col">' + card + '<section class="glass"><div class="caps">RISK INDEX, ' + y0 + (y1 !== y0 ? " TO " + y1 : "") + '</div><div style="font-size:14px;color:var(--muted);margin-top:4px">Dashed line: +2, the rare level</div>' + pathChart(ev) + "</section>" + price + "</div></div>";
    let startI = ev.strip[0];
    return { html: html, after: () => mountMap({ viewBox: ev.viewBox, base: Object.assign({}, D.map.base, { href: BASE_IMG }), regions: ev.regions, frames: ev.frames, start: startI, strip: ev.strip, ringRadius: ev.viewBox[2] / 40, labelPrefix: "EPISODE REPLAY · " + ev.label.toUpperCase() + " · " + c.display, labelWord: "", rangeLabel: ev.range, capture: false, autoplay: false, ariaLabel: "Episode replay " + ev.label, borderWidth: 0.8 }) };
  }

  function splitFigure(t) { const m = /[-+]?[\d,]*\.?\d+(?:\s?(?:%|pp|points))?/.exec(t); return m ? [t.slice(0, m.index), m[0], t.slice(m.index + m[0].length)] : ["", "", t]; }
  function noteBody(n) {
    return n.template.split("\n\n").filter((p) => p.trim()).map((p) => "<p>" + esc(p).replace(/\{([A-Z][A-Z0-9_]*)\}/g, (all, k) => {
      const s = n.slots[k]; if (!s) return all;
      if (s.kind === "figure") { const [pre, f, rest] = splitFigure(s.text); return esc(pre) + (f ? '<span class="pill" title="' + esc(s.source + " \u00b7 " + s.date) + '">' + esc(f) + "</span>" : "") + esc(rest); }
      return "<b>" + esc(s.text) + "</b>";
    }) + "</p>").join("");
  }
  function emailBody(html) {
    const m = /<body[^>]*>([\s\S]*)<\/body>/i.exec(html);
    return m ? m[1] : html;
  }
  function viewNote() {
    const keyOf = (n) => n.week + "|" + n.commodity;
    if (!S.note) S.note = D.asOf + "|" + S.crop;
    const n = D.notes.find((x) => keyOf(x) === S.note) || D.notes[0];
    let lastDay = "";
    const inbox = D.notes.map((x) => {
      const tag = x.model === "deterministic-template" ? "FIXED TEMPLATE" : (x.templateParagraphs ? x.templateParagraphs + " OF 3 FROM TEMPLATE" : "");
      const head = x.week !== lastDay ? '<div class="caps" style="margin:8px 4px 0">' + dLong(x.week) + "</div>" : "";
      lastDay = x.week;
      return head + '<button class="glass inbox-item' + (keyOf(x) === keyOf(n) ? " on" : "") + '" data-note="' + keyOf(x) + '"><span style="border-radius:10px;overflow:hidden;display:inline-flex;flex:none;height:40px">' + D.marks.signal + '</span><div style="flex:1;min-width:0"><div style="display:flex;justify-content:space-between;gap:8px"><span style="font-weight:600">HarvestRadar Daily</span><span class="mono" style="font-size:13px;color:var(--muted)">07:00</span></div><div style="font-size:15px;color:var(--frost-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + esc(x.title) + "</div>" + (tag ? '<div style="margin-top:6px"><span class="chip" style="padding:3px 8px">' + tag + "</span></div>" : "") + "</div></button>";
    }).join("");
    const readings = '<div class="grid3">' + Object.keys(n.readings).map((k) => {
      const r = n.readings[k], s = D.crops[k].riskRecent, i = s.d.indexOf(r.date), series = s.z.slice(Math.max(0, i - 25), i + 1);
      return '<div class="glass tick-card' + (k === n.commodity ? " sel" : "") + '" style="cursor:default">' + glyph(r.glyph, 26) + '<div style="min-width:0"><div class="caps" style="white-space:nowrap">' + esc(r.display) + ' &middot; RISK INDEX</div><div class="val' + (r.value >= 2 ? " glow" : "") + '">' + esc(r.text) + "</div></div>" + sparkline(series, 96) + "</div>";
    }).join("") + "</div>";
    const who = n.model === "deterministic-template" ? "Written from the fixed template (the AI model failed the checks)" : "Written by a small AI model running locally (" + esc(D.meta.llm.display_name) + ")" + (n.templateParagraphs ? "; " + n.templateParagraphs + " of 3 paragraphs from the fixed template" : "");
    const figs = Object.values(n.slots).filter((s) => s.kind === "figure").map((s) => '<div class="glass" style="padding:14px 16px"><div class="mono" style="font-size:22px;color:var(--signal)">' + esc(s.text) + '</div><div style="font-size:15px;color:var(--frost-2);margin-top:4px">' + esc(s.label) + '</div><div class="source" style="margin-top:6px">Source: ' + esc(s.source) + "<br>" + esc(s.date) + (s.detail ? ", " + esc(s.detail) : "") + "</div></div>").join("");
    const html = '<div class="main c30"><div class="col"><div style="display:flex;justify-content:space-between;align-items:baseline;margin:4px 4px 0"><span style="font-family:var(--display);font-weight:700;font-size:28px">Inbox</span><span class="caps">EVERY WORKING DAY, 07:00</span></div>' + inbox + "</div>" +
      '<div class="col"><section class="glass" style="padding:22px 24px;display:flex;flex-direction:column;gap:16px"><div style="display:flex;gap:16px;align-items:center"><span style="border-radius:12px;overflow:hidden;display:inline-flex;flex:none">' + D.marks.signal.replace(/width="40" height="40"/, 'width="52" height="52"') + '</span><div><div style="font-family:var(--display);font-weight:700;font-size:30px;line-height:1.15">' + esc(n.title) + '</div><div style="color:var(--muted)">HarvestRadar Daily &middot; ' + dLong(n.week) + "</div></div></div>" + readings +
      '<div class="note-body">' + noteBody(n) + '</div><div class="chips">' + badge("Numbers checked", n.checks[0]) + badge("Context checked", n.checks[1]) + badge("Claims checked", n.checks[2]) + "</div>" +
      '<div style="font-size:14px;color:var(--muted)">' + who + ". Every figure is inserted by the software, with its source; hover a figure to see it.</div>" +
      '<div class="chips"><a class="btn primary" href="#stress" data-crop-link="' + n.commodity + '" style="display:inline-flex;align-items:center;text-decoration:none">Open the map</a><button class="btn" id="email-btn" aria-expanded="' + S.email + '">' + (S.email ? "Hide the email" : "Show as email") + "</button></div></section>" +
      (S.email ? '<section class="glass scroll-x"><div class="caps" style="margin-bottom:10px">THE SAME NOTE AS AN EMAIL</div><div style="font-size:14px;color:var(--muted);margin-bottom:12px">In the HarvestRadar app, "Download as email" saves this as an .eml file.</div><div class="email-wrap">' + emailBody(n.email) + "</div></section>" : "") +
      '<details class="glass"><summary>Data given to the model</summary><div class="figs">' + figs + '</div><div class="source">Written in ' + n.seconds + " seconds, " + n.attempts + " model attempt(s).</div></details></div></div>";
    return { html: html, after: null };
  }

  function viewMethod() {
    const M = D.method, ev = M.eval, pooled = ev.pooled || {};
    const rmW = pooled.rmse_vs_trend_weighted_pct, rmU = pooled.rmse_vs_trend_pct;
    const ramp = (z) => { const R = [[-3, [126, 176, 255]], [-2, [63, 116, 216]], [-1, [38, 64, 106]], [0, [30, 40, 51]], [1, [138, 100, 36]], [2, [245, 169, 58]], [3, [255, 90, 54]]]; z = Math.max(-3, Math.min(3, z)); for (let i = 0; i < 6; i++) { const [a, ca] = R[i], [b, cb] = R[i + 1]; if (z >= a && z <= b) { const t = (z - a) / (b - a); return "rgb(" + ca.map((v, j) => Math.round(v + (cb[j] - v) * t)).join(",") + ")"; } } return "rgb(255,90,54)"; };
    const totalR = CROPS.reduce((s0, k) => s0 + D.crops[k].regionsN, 0);
    const maize = D.crops.maize.latest;
    const shares = maize.contributors.slice().sort((a, b) => b.share_pct - a.share_pct).slice(0, 3);
    const card = (num, t, big, sub, extra, on) => '<section class="glass' + (on ? " amber" : "") + '" style="min-height:290px"><div class="mono" style="font-size:13px;color:' + (on ? "var(--signal)" : "var(--muted)") + '">STEP ' + num + '</div><div style="font-family:var(--display);font-weight:700;font-size:28px;margin-top:6px">' + t + '</div><div class="mono" style="font-size:40px;margin-top:8px">' + big + '</div><div style="color:var(--frost-2)">' + sub + "</div>" + (extra || "") + "</section>";
    const strip = '<div style="display:flex;gap:3px;margin-top:22px">' + M.strip.values.map((v) => '<i style="flex:1;height:22px;border-radius:3px;background:' + ramp(v) + '"></i>').join("") + '</div><div class="source">' + esc(M.strip.name) + ", summer 2012, every 10 days</div>";
    const bars = shares.map((x) => '<div style="display:grid;grid-template-columns:110px minmax(0,1fr) 46px;gap:10px;align-items:center;margin-top:8px"><span style="color:var(--frost-2);font-size:15px">' + esc(x.name) + '</span><div style="height:6px;border-radius:3px;background:var(--line)"><div style="height:6px;border-radius:3px;width:' + Math.min(100, 2 * x.share_pct).toFixed(0) + '%;background:var(--frost-2)"></div></div><span class="mono" style="font-size:13px;color:var(--muted);text-align:right">' + Math.round(x.share_pct) + "%</span></div>").join("");
    const row = (ok, t, f, v) => '<div class="ledger"><span style="font-size:22px;color:' + (ok ? "var(--frost)" : "var(--muted)") + '">' + (ok ? "&#10003;" : "&#10005;") + '</span><span class="t" style="color:' + (ok ? "var(--frost)" : "var(--frost-2)") + '">' + t + '</span><span class="f">' + f + '</span><span class="caps" style="text-align:right;color:var(--frost-2)">' + v + "</span></div>";
    const word = (x) => (x <= -10 ? "CLEAR GAIN" : x < 0 ? "SMALL GAIN" : "NO GAIN");
    let ledger = row(rmW < 0, "Forecast error vs a simple trend, harvests " + ev.test[0] + " to " + ev.test[1], pct(rmW), word(rmW)) + row(rmU < 0, "Same, every country counted equally", pct(rmU), word(rmU));
    Object.values(M.events).forEach((e) => {
      const f = e.first_above_2 ? "above +2 on " + dLong(e.first_above_2) + (e.verdict === "late" ? ", after the price peak" : ", before the price peak") : "highest " + sg(e.peak_risk_z) + ", never above +2";
      ledger += row(e.verdict === "caught", esc(e.label), f, { caught: "CAUGHT", late: "TOO LATE", missed: "MISSED" }[e.verdict]);
    });
    const bt = M.backtest;
    ledger += row(bt.best_rule_p_corrected < 0.05, "Trading on the index, after costs", Math.round(100 * bt.best_rule_p_corrected) + "% chance it is luck", bt.best_rule_p_corrected < 0.05 ? "REAL GAIN" : "NO RELIABLE GAIN");
    const trs = Object.entries(ev.byCrop).map(([k, b]) => { const m = b.model || {}, t = b.trend_only || {}; return "<tr><td>" + esc(D.crops[k].label) + "</td><td>" + m.n + "</td><td>" + (100 * m.rmse).toFixed(1) + "</td><td>" + (100 * t.rmse).toFixed(1) + "</td><td>" + sg(m.spearman || 0) + "</td><td>" + Math.round(100 * (m.sign_accuracy || 0)) + "%</td></tr>"; }).join("");
    const html = '<h1 class="ttl">Under the hood, four steps.</h1><div class="grid4">' +
      card("1", "Crop maps", totalR.toLocaleString("en-US"), "producing regions, covering 90% of world output of each crop (MapSPAM 2020)", '<div style="display:flex;gap:14px;margin-top:26px">' + glyph("maize", 26) + glyph("arabica", 26) + glyph("cocoa", 26) + "</div>") +
      card("2", "Weather", D.meta.cells.toLocaleString("en-US"), "NASA weather points, read every day since 1981", strip) +
      card("3", "Model", pct(rmW), "smaller harvest-forecast error than a simple trend, on harvests the model had never seen, weighted by world share", '<div class="chips" style="margin-top:20px">' + chip("Gradient boosting") + chip("Explained factor by factor", true) + "</div>", true) +
      card("4", "World index", sg(maize.z), "maize today: country forecasts weighted by their share of world output", bars) + "</div>" +
      '<div class="chips" style="margin-top:16px"><span class="caps" style="margin-right:8px">BEYOND THE COURSE</span>' + ["Weather weighted by where crops grow", "Testing without peeking at the future", "Explanations by weather factor (SHAP)", "Local AI writer with fact checks", "Trading test against luck"].map((t) => chip(t)).join("") + "</div>" +
      '<div class="main c65" style="margin-top:8px"><div class="col"><h2 class="ttl">Tested like sceptics.</h2><div>' + ledger + '</div><div class="source">HarvestRadar is a radar, not a crystal ball. "Caught" means the index went above +2 before the futures price peaked.</div></div>' +
      '<div class="col"><h2 class="ttl">Forecast errors at the end of each season</h2><section class="glass scroll-x"><table class="ev"><thead><tr><th>CROP</th><th>HARVESTS</th><th>MODEL ERROR</th><th>TREND ERROR</th><th>RANK MATCH</th><th>RIGHT DIRECTION</th></tr></thead><tbody>' + trs + '</tbody></table><div class="source">Typical error, in percentage points of yield (maize) or production (tree crops) vs normal, harvests ' + ev.test[0] + " to " + ev.test[1] + ". Rank match: how well the model orders good and bad harvests (1 = perfectly). Each year is forecast by a model trained only on harvests published before it.</div></section>" +
      '<section class="glass"><div class="caps" style="margin-bottom:8px">CREDITS</div><div style="font-size:15px;line-height:1.7;color:var(--frost-2)"><b>Data</b>: NASA POWER weather, MapSPAM 2020 crop maps (IFPRI), geoBoundaries regions, FAOSTAT harvests, NOAA El Ni&ntilde;o index, futures prices via Yahoo Finance, Natural Earth.<br><b>Imagery</b>: NASA Blue Marble (public domain).<br><b>Model</b>: LightGBM gradient boosting, SHAP explanations; daily note by ' + esc(D.meta.llm.display_name) + " (Hugging Face), run locally.<br><b>Fonts</b>: Space Grotesk, Inter, JetBrains Mono.</div></section></div></div>";
    return { html: html, after: null };
  }

  const RENDER = { stress: viewStress, commodity: viewCommodity, replay: viewReplay, note: viewNote, method: viewMethod };
  function current() { const v = location.hash.slice(1); return RENDER[v] ? v : "stress"; }
  function render() {
    const v = current();
    if (mapHandle && mapHandle.stop) { mapHandle.stop(); mapHandle = null; }
    document.getElementById("tabs").innerHTML = Object.entries(VIEWS).map(([k, l]) => '<a class="tab' + (k === v ? " on" : "") + '" href="#' + k + '"' + (k === v ? ' aria-current="page"' : "") + ">" + l + "</a>").join("");
    const out = RENDER[v]();
    document.getElementById("view").innerHTML = out.html;
    if (out.after) out.after();
  }

  document.getElementById("brand").innerHTML = D.marks.small + "<span>Harvest<b>Radar</b></span>";
  document.getElementById("status").textContent = "DATA AS OF " + D.weekLabel;
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-crop],[data-shap],[data-episode],[data-note],#email-btn,[data-crop-link]");
    if (!t) return;
    if (t.dataset.crop) { S.crop = t.dataset.crop; render(); }
    else if (t.dataset.shap) { S.shap[S.crop] = t.dataset.shap; render(); }
    else if (t.dataset.episode) { S.episode = t.dataset.episode; render(); }
    else if (t.dataset.note) { S.note = t.dataset.note; render(); }
    else if (t.id === "email-btn") { S.email = !S.email; render(); }
    else if (t.dataset.cropLink) { S.crop = t.dataset.cropLink; }
  });
  window.addEventListener("hashchange", render);
  let rw = window.innerWidth;
  window.addEventListener("resize", () => { if ((rw < 700) !== (window.innerWidth < 700)) { rw = window.innerWidth; render(); } });
  render();
})();
