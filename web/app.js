/* HarvestRadar static web edition: renders the five pages from the embedded data snapshot. */
(function () {
  "use strict";
  const D = JSON.parse(document.getElementById("data").textContent);
  const CROPS = ["maize", "coffee", "cocoa"];
  const VIEWS = { stress: "Stress map", commodity: "Commodity", replay: "Replay", note: "Weekly note", method: "Method" };
  const S = { crop: "maize", episode: Object.keys(D.episodes)[0], note: null, shap: {}, email: false };
  let mapHandle = null;

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const sg = (x, n = 2) => (x == null || !isFinite(x) ? "n/a" : (x >= 0 ? "+" : "") + x.toFixed(n));
  const fmtPrice = (key, x) => key === "cocoa" ? Math.round(x).toLocaleString("en-US") : x.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const dLabel = (s) => { const d = new Date(s + "T00:00:00Z"); return d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); };
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
        '<div style="min-width:0"><div class="caps" style="white-space:nowrap">' + esc(c.display) + ' &middot; RISK_Z</div><div class="val' + (z >= 2 ? " glow" : "") + '">' + sg(z) + "</div></div>" + sparkline(s) + "</button>";
    }).join("") + "</div>";
  }

  /* ---------- map ---------- */
  const PLAY = '<svg class="i-play" viewBox="0 0 24 24"><path d="M7 4.5v15l13-7.5z" fill="#0B0F14"/></svg><svg class="i-pause" viewBox="0 0 24 24"><path d="M6 4h4.5v16H6zM13.5 4H18v16h-4.5z" fill="#0B0F14"/></svg>';
  const LEG = ["#7EB0FF", "#3F74D8", "#26406A", "#1E2833", "#8A6424", "#F5A93A", "#FF5A36"].map((c) => '<i style="background:' + c + '"></i>').join("");
  function mapShell(mode, height, range) {
    return '<div class="radar ' + mode + '" tabindex="0" style="height:' + height + 'px"><div class="map-stage"></div><div class="corner c-tl"></div><div class="corner c-tr"></div><div class="corner c-bl"></div><div class="corner c-br"></div>' +
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
    const c = D.crops[key], W = 1000, H = 470, m = { l: 46, r: 64, t: 46, b: 34 };
    const end = new Date(c.latest.date + "T00:00:00Z"), start = new Date(end.getTime() - 64 * 7 * 864e5);
    const R = c.risk.d.map((d, i) => [new Date(d + "T00:00:00Z"), c.risk.z[i]]).filter((p) => p[0] >= start && p[1] != null);
    const P = c.pricesRecent.d.map((d, i) => [new Date(d + "T00:00:00Z"), c.pricesRecent.c[i]]).filter((p) => p[0] >= start);
    const zs = R.map((p) => p[1]), lo = Math.min(-0.5, Math.min(...zs) - 0.4), hi = Math.max(2.6, Math.max(...zs) + 0.4);
    const pv = P.map((p) => p[1]), plo = Math.min(...pv), phi = Math.max(...pv);
    const x = (d) => m.l + ((d - start) / (end - start)) * (W - m.l - m.r);
    const y = (v) => m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b);
    const y2 = (v) => m.t + (1 - (v - plo) / (phi - plo || 1)) * (H - m.t - m.b);
    let g = "";
    c.windows.forEach(([s, e, st]) => {
      const xs = x(new Date(s + "T00:00:00Z")), xe = x(new Date(e + "T00:00:00Z"));
      g += '<rect x="' + xs + '" y="' + m.t + '" width="' + Math.max(1, xe - xs) + '" height="' + (H - m.t - m.b) + '" fill="rgba(255,181,71,.07)"/>' +
        '<text x="' + (xs + xe) / 2 + '" y="' + (m.t - 8) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + esc((c.mainCountry + " " + st + " window").toUpperCase()) + "</text>";
    });
    niceTicks(lo, hi, 7).forEach((v) => { g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="' + (v === 0 ? "#2A3646" : "#1E2935") + '"/><text x="' + (m.l - 8) + '" y="' + (y(v) + 4) + '" text-anchor="end" font-size="13" fill="#8A9AAB">' + v + "</text>"; });
    niceTicks(plo, phi, 6).forEach((v) => { g += '<text x="' + (W - m.r + 8) + '" y="' + (y2(v) + 4) + '" font-size="13" fill="#8A9AAB">' + (key === "cocoa" ? Math.round(v).toLocaleString("en-US") : v) + "</text>"; });
    for (let k = 0; k < 16; k++) { const d = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1 + 2 * k, 1)); if (d > end) break; g += '<text x="' + x(d) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + MON[d.getUTCMonth()] + " " + d.getUTCFullYear() + "</text>"; }
    g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(2) + '" y2="' + y(2) + '" stroke="#F5A93A" stroke-dasharray="6 6" stroke-width="1.2"/><text x="' + (m.l + 6) + '" y="' + (y(2) - 6) + '" font-size="13" fill="#F5A93A">+2</text>';
    const pl = P.map((p, i) => (i ? "L" : "M") + x(p[0]).toFixed(1) + "," + y2(p[1]).toFixed(1)).join(" ");
    const il = R.map((p, i) => (i ? "L" : "M") + x(p[0]).toFixed(1) + "," + y(p[1]).toFixed(1)).join(" ");
    const last = R[R.length - 1];
    g += '<path d="' + pl + '" fill="none" stroke="#EAF0F5" stroke-opacity=".7" stroke-width="1.5"/>';
    g += '<path d="' + il + " L" + x(last[0]) + "," + y(0) + " L" + x(R[0][0]) + "," + y(0) + ' Z" fill="rgba(255,181,71,.08)"/>';
    g += '<path d="' + il + '" fill="none" stroke="rgba(255,181,71,.2)" stroke-width="10" stroke-linejoin="round"/><path d="' + il + '" fill="none" stroke="#FFB547" stroke-width="3" stroke-linejoin="round"/>';
    g += '<circle cx="' + x(last[0]) + '" cy="' + y(last[1]) + '" r="9" fill="rgba(255,181,71,.25)"/><circle cx="' + x(last[0]) + '" cy="' + y(last[1]) + '" r="4.5" fill="#FFB547"/>';
    g += '<g font-size="13" fill="#8A9AAB"><line x1="' + m.l + '" x2="' + (m.l + 24) + '" y1="14" y2="14" stroke="#FFB547" stroke-width="3"/><text x="' + (m.l + 32) + '" y="18">HARVEST-RISK INDEX</text>' +
      '<line x1="' + (m.l + 220) + '" x2="' + (m.l + 244) + '" y1="14" y2="14" stroke="#EAF0F5" stroke-width="1.5"/><text x="' + (m.l + 252) + '" y="18">' + esc(c.priceLabel) + "</text></g>";
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
    const rows = mp.top5.map((r) => '<div class="rank"><span class="mono" style="font-size:13px;color:var(--muted)">' + String(r.rank).padStart(2, "0") + "</span>" + glyph(c.glyph, 18) + '<span class="name">' + esc(r.name) + '</span><span class="mono" style="font-size:13px;color:var(--muted)">' + esc(r.iso) + '</span><span class="bar"><i style="width:' + Math.max(3, 100 * r.frac).toFixed(0) + "%;background:linear-gradient(90deg,#8A6424,#F5A93A 70%," + (r.hot ? "#FF5A36" : "#FFB547") + ')"></i></span></div>').join("");
    const n = D.notes.find((x) => x.week === D.asOf && x.commodity === S.crop);
    const o = D.oni;
    const html = ticker() + '<div class="main"><div class="col">' + mapShell("world", mapH(), rng) +
      '<div class="source" style="margin-top:0">' + esc(c.label) + ": " + c.regionsN + " regions covering " + Math.round(100 * c.coverage) + "% of world output (MapSPAM 2020) &middot; stress = heat, rain and root-zone soil moisture vs " + D.meta.climBase[0] + "-" + D.meta.climBase[1] + " &middot; NASA POWER</div></div>" +
      '<div class="col">' + panel("STRESS &times; SHARE OF WORLD SUPPLY", rows, "dekad ending " + dLabel(mp.dekad) + " &middot; stress &times; production weight") +
      '<section class="glass"><div class="caps">CLIMATE DRIVER &middot; CONTEXT</div><div style="font-family:var(--display);font-weight:700;font-size:22px;margin-top:8px">El Ni&ntilde;o</div><div style="display:flex;align-items:flex-end;justify-content:space-between;gap:12px;flex-wrap:wrap"><div><span class="mono" style="font-size:30px;color:var(--signal)">' + sg(o.value) + '</span> <span class="mono" style="font-size:13px;color:var(--muted);letter-spacing:.08em">' + esc(o.label) + "</span></div>" + sparkline(o.series, 200, 48) + '</div><div class="source">NOAA CPC ONI, published ' + o.available_at + " &middot; context, not a driver of the index</div></section>" +
      (n ? '<a class="glass" href="#note" style="display:flex;align-items:center;gap:16px;text-decoration:none;color:var(--frost)"><span style="border-radius:10px;overflow:hidden;display:inline-flex;flex:none">' + D.marks.signal + '</span><div><div style="font-size:17px;font-weight:500">Friday note ready</div><div class="mono" style="font-size:13px;color:var(--muted)">' + n.checks.filter(Boolean).length + '/3 checks passed</div></div><span class="mono" style="margin-left:auto;font-size:13px;color:var(--signal)">OPEN &rarr;</span></a>' : "") +
      "</div></div>";
    return { html: html, after: () => mountMap({ viewBox: D.map.viewBox, base: Object.assign({}, D.map.base, { href: BASE_IMG }), countries: mp.borders, regions: mp.regions, frames: f, start: mp.start, ringRadius: 230, labelPrefix: "STRESS VS OWN HISTORY", rangeLabel: rng, capture: false, autoplay: false, ariaLabel: c.label + " stress map" }) };
  }

  function viewCommodity() {
    const k = S.crop, c = D.crops[k], L = c.latest;
    const rows = L.contributors.map((x) => ({ label: x.name, value: x.contrib_pct, raises: x.contrib_pct < 0, note: sg(x.pred_anom_pct, 1) + "% vs trend, crop " + x.season + (x.window_open ? ", window open" : "") }));
    const countries = L.contributors.map((x) => x.country).filter((iso) => c.shap[iso]);
    const sel = S.shap[k] && countries.includes(S.shap[k]) ? S.shap[k] : countries[0];
    const name = (iso) => (L.contributors.find((x) => x.country === iso) || {}).name || iso;
    const sh = c.shap[sel];
    const shapRows = sh ? sh.rows.map(([lab, v]) => ({ label: lab, value: v, raises: v < 0 })) : [];
    const html = ticker() + '<div class="main c65"><div class="col"><div class="cards3">' +
      '<section class="glass" style="display:flex;align-items:center;gap:22px;min-height:164px">' + glyph(c.glyph, 52) + '<div style="min-width:0"><div class="caps">' + esc(c.display) + ' &middot; HARVEST-RISK INDEX</div><div class="mono glow hero-val" style="font-size:72px;line-height:1;color:var(--signal);font-weight:500;margin-top:6px">' + sg(L.z) + '</div><div class="source">week of ' + dLabel(L.date) + "</div></div></section>" +
      '<section class="glass" style="min-height:164px"><div class="caps">SUPPLY VS TREND</div><div class="mono" style="font-size:34px;margin-top:12px">' + sg(L.dp, 1) + '%</div><div class="source">p10/p90 ' + sg(L.lo, 1) + "% to " + sg(L.hi, 1) + "% &middot; model predictions</div></section>" +
      '<section class="glass" style="min-height:164px"><div class="caps">' + esc(c.priceLabel) + '</div><div class="mono" style="font-size:34px;margin-top:12px">' + fmtPrice(k, c.lastPrice.close) + '</div><div class="source">' + esc(c.ticker) + " close " + dLabel(c.lastPrice.date) + " &middot; " + esc(c.priceUnit) + "</div></section></div>" +
      '<section class="glass" style="padding:14px 18px">' + indexChart(k) + '<div class="source">risk_index.parquet, prices (' + esc(c.priceName) + ", " + esc(c.priceUnit) + ") &middot; windows from config/commodities.yaml (" + esc(c.mainCountry) + ")</div></section></div>" +
      '<div class="col">' + panel("WHO DRIVES THIS WEEK &middot; PP OF WORLD SUPPLY", barRows(rows, "pp", 200), "share of world supply &times; predicted anomaly &middot; amber raises the risk, blue lowers it") +
      '<div class="chips" role="group" aria-label="Country for SHAP">' + countries.map((iso) => '<button class="chip' + (iso === sel ? " on" : "") + '" data-shap="' + iso + '">' + esc(name(iso)) + "</button>").join("") + "</div>" +
      panel("SHAP &middot; WHICH WEATHER <span style='float:right;color:var(--signal)'>" + esc(name(sel).toUpperCase()) + "</span>", barRows(shapRows, "pp", 220), "pp of " + c.target + " anomaly, crop " + (sh ? sh.season : "") + ", model as of " + dLabel(D.asOf)) +
      "</div></div>";
    return { html: html, after: null };
  }

  function viewReplay() {
    const names = Object.keys(D.episodes), ev = D.episodes[S.episode], c = D.crops[ev.commodity];
    const fmt = (x) => ev.commodity === "cocoa" ? Math.round(x).toLocaleString("en-US") : String(+x.toFixed(2));
    let card;
    if (ev.first_above_2) {
      const cap = ev.verdict === "late" ? "after the price peak of " + ev.price_max_date + ": late" : (ev.lead_text || "");
      card = '<section class="glass amber"><div class="caps">RISK_Z FIRST ABOVE +2</div><div class="mono glow" style="font-size:clamp(40px,4vw,60px);line-height:1.15;color:var(--signal);margin-top:10px">' + ev.first_above_2 + '</div><div style="font-size:17px;color:var(--frost-2)">' + esc(cap) + '</div><div class="source">events.json &middot; risk_index.parquet</div></section>';
    } else {
      card = '<section class="glass"><div class="caps">RISK_Z PEAK IN THE EPISODE</div><div class="mono" style="font-size:clamp(40px,4vw,60px);line-height:1.15;color:var(--signal);margin-top:10px">' + sg(ev.peak_risk_z) + '</div><div style="font-size:17px;color:var(--frost-2)">peak on ' + ev.peak_date + ": never above +2, missed</div></section>";
    }
    const ch = ev.price_change_pct, hot = ch > 0;
    const price = '<section class="glass"><div class="caps">' + esc(c.priceLabel) + " &middot; " + ev.price_from_date + " TO " + ev.price_to_date + '</div><div style="display:flex;align-items:baseline;gap:16px;margin-top:12px;flex-wrap:wrap"><span class="mono" style="font-size:34px;color:var(--frost-2)">' + fmt(ev.price_from) + '</span><span style="color:var(--muted)">to</span><span class="mono" style="font-size:40px;color:' + (hot ? "var(--heat)" : "var(--frost)") + '">' + fmt(ev.price_to) + '</span><span class="mono" style="font-size:22px;color:' + (hot ? "var(--heat)" : "var(--frost-2)") + '">' + sg(ch, 1) + '%</span></div><div class="source">' + esc(c.priceUnit) + (ev.price_max ? " &middot; episode high " + fmt(ev.price_max) + " on " + ev.price_max_date : "") + "</div></section>";
    const y0 = ev.start.slice(0, 4), y1 = ev.end.slice(0, 4);
    const html = '<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap"><div class="chips" role="group" aria-label="Episode">' + names.map((n) => '<button class="chip' + (n === S.episode ? " on" : "") + '" data-episode="' + n + '">' + esc(D.episodes[n].label) + "</button>").join("") + "</div>" +
      (ev.model_trained_on_seasons_up_to ? chip("MODEL TRAINED ON SEASONS UP TO " + ev.model_trained_on_seasons_up_to, true) : "") + "</div>" +
      '<div class="main c65"><div class="col">' + mapShell("episode", mapH() + 60, ev.range) + '<div class="source" style="margin-top:0">dekad stress vs ' + D.meta.climBase[0] + "-" + D.meta.climBase[1] + " &middot; NASA POWER &middot; arrow keys step one dekad, space plays</div></div>" +
      '<div class="col">' + card + '<section class="glass"><div class="caps">INDEX, ' + y0 + (y1 !== y0 ? "-" + y1 : "") + "</div>" + pathChart(ev) + "</section>" + price + "</div></div>";
    let startI = ev.strip[0];
    return { html: html, after: () => mountMap({ viewBox: ev.viewBox, base: Object.assign({}, D.map.base, { href: BASE_IMG }), regions: ev.regions, frames: ev.frames, start: startI, strip: ev.strip, ringRadius: ev.viewBox[2] / 40, labelPrefix: "EPISODE REPLAY · " + ev.label.toUpperCase() + " · " + c.display, labelWord: "DEKAD", rangeLabel: ev.range, capture: false, autoplay: false, ariaLabel: "Episode replay " + ev.label, borderWidth: 0.8 }) };
  }

  function splitFigure(t) { const m = /^\s*([-+]?[\d,]*\.?\d+(?:\s?(?:%|pp))?)(.*)$/.exec(t); return m ? [m[1], m[2]] : [t, ""]; }
  function noteBody(n) {
    return n.template.split("\n\n").filter((p) => p.trim()).map((p) => "<p>" + esc(p).replace(/\{([A-Z][A-Z0-9_]*)\}/g, (all, k) => {
      const s = n.slots[k]; if (!s) return all;
      if (s.kind === "figure") { const [f, rest] = splitFigure(s.text); return '<span class="pill" title="' + esc(s.source + " · " + s.date) + '">' + esc(f) + "</span>" + esc(rest); }
      return "<b>" + esc(s.text) + "</b>";
    }) + "</p>").join("");
  }
  function viewNote() {
    const keyOf = (n) => n.week + "|" + n.commodity;
    if (!S.note) S.note = D.asOf + "|" + S.crop;
    const n = D.notes.find((x) => keyOf(x) === S.note) || D.notes[0];
    const inbox = D.notes.map((x) => {
      const tag = x.model === "deterministic-template" ? "DETERMINISTIC-TEMPLATE" : (x.templateParagraphs ? "TEMPLATE " + x.templateParagraphs + "/3" : "");
      return '<button class="glass inbox-item' + (keyOf(x) === keyOf(n) ? " on" : "") + '" data-note="' + keyOf(x) + '"><span style="border-radius:10px;overflow:hidden;display:inline-flex;flex:none;height:40px">' + D.marks.signal + '</span><div style="flex:1;min-width:0"><div style="display:flex;justify-content:space-between;gap:8px"><span style="font-weight:600">HarvestRadar Weekly</span><span class="mono" style="font-size:13px;color:var(--muted)">' + dLabel(x.week).slice(0, -5) + '</span></div><div style="font-size:15px;color:var(--frost-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + esc(x.title) + "</div>" + (tag ? '<div style="margin-top:6px"><span class="chip" style="padding:3px 8px">' + tag + "</span></div>" : "") + "</div></button>";
    }).join("");
    const readings = '<div class="grid3">' + Object.keys(n.readings).map((k) => {
      const r = n.readings[k], s = D.crops[k].risk, i = s.d.indexOf(r.date), series = s.z.slice(Math.max(0, i - 25), i + 1);
      return '<div class="glass tick-card' + (k === n.commodity ? " sel" : "") + '" style="cursor:default">' + glyph(r.glyph, 26) + '<div style="min-width:0"><div class="caps" style="white-space:nowrap">' + esc(r.display) + ' &middot; RISK_Z</div><div class="val' + (r.value >= 2 ? " glow" : "") + '">' + esc(r.text) + "</div></div>" + sparkline(series, 96) + "</div>";
    }).join("") + "</div>";
    const who = n.model === "deterministic-template" ? "Deterministic template" : "Written by " + esc(D.meta.llm.display_name) + ", local" + (n.templateParagraphs ? ", " + n.templateParagraphs + " of 3 paragraphs from the template" : "");
    const figs = Object.values(n.slots).filter((s) => s.kind === "figure").map((s) => '<div class="glass" style="padding:14px 16px"><div class="mono" style="font-size:24px;color:var(--signal)">' + esc(s.text) + '</div><div style="font-size:15px;color:var(--frost-2);margin-top:4px">' + esc(s.label) + '</div><div class="source" style="margin-top:6px">source &middot; ' + esc(s.source) + "<br>" + esc(s.date) + " &middot; " + esc(s.detail || "") + "</div></div>").join("");
    const html = '<div class="main c30"><div class="col"><div style="display:flex;justify-content:space-between;align-items:baseline;margin:4px 4px 0"><span style="font-family:var(--display);font-weight:700;font-size:28px">Inbox</span><span class="caps">FRIDAY 07:00</span></div>' + inbox + "</div>" +
      '<div class="col"><section class="glass" style="padding:22px 24px;display:flex;flex-direction:column;gap:16px"><div style="display:flex;gap:16px;align-items:center"><span style="border-radius:12px;overflow:hidden;display:inline-flex;flex:none">' + D.marks.signal.replace(/width="40" height="40"/, 'width="52" height="52"') + '</span><div><div style="font-family:var(--display);font-weight:700;font-size:30px;line-height:1.15">' + esc(n.title) + '</div><div style="color:var(--muted)">HarvestRadar Weekly &middot; week of ' + dLabel(n.week) + "</div></div></div>" + readings +
      '<div class="note-body">' + noteBody(n) + '</div><div class="chips">' + badge("Numbers checked", n.checks[0]) + badge("Context checked", n.checks[1]) + badge("Claims checked", n.checks[2]) + '<span class="mono" style="font-size:13px;color:var(--muted)">' + who + " &middot; figures inserted by software</span></div>" +
      '<div class="chips"><a class="btn primary" href="#stress" data-crop-link="' + n.commodity + '" style="display:inline-flex;align-items:center;text-decoration:none">Open the map</a><button class="btn" id="email-btn" aria-expanded="' + S.email + '">' + (S.email ? "Hide the email" : "View as email") + "</button></div></section>" +
      (S.email ? '<section class="glass"><div class="caps" style="margin-bottom:10px">THE SAME NOTE AS AN EMAIL (.eml export in the app: Download as email)</div><iframe class="email-frame" id="email-frame" title="Weekly note as an email"></iframe></section>' : "") +
      '<details class="glass"><summary>Data given to the model</summary><div class="figs">' + figs + '</div><div class="source">INSERTED BY SOFTWARE, WITH SOURCE &middot; generated in ' + n.seconds + " s, " + n.attempts + " model attempt(s)</div></details></div></div>";
    return { html: html, after: () => { const f = document.getElementById("email-frame"); if (f) f.srcdoc = n.email; } };
  }

  function viewMethod() {
    const M = D.method, ev = M.eval, pooled = ev.pooled || {};
    const rmW = pooled.rmse_vs_trend_weighted_pct, rmU = pooled.rmse_vs_trend_pct;
    const ramp = (z) => { const R = [[-3, [126, 176, 255]], [-2, [63, 116, 216]], [-1, [38, 64, 106]], [0, [30, 40, 51]], [1, [138, 100, 36]], [2, [245, 169, 58]], [3, [255, 90, 54]]]; z = Math.max(-3, Math.min(3, z)); for (let i = 0; i < 6; i++) { const [a, ca] = R[i], [b, cb] = R[i + 1]; if (z >= a && z <= b) { const t = (z - a) / (b - a); return "rgb(" + ca.map((v, j) => Math.round(v + (cb[j] - v) * t)).join(",") + ")"; } } return "rgb(255,90,54)"; };
    const totalR = CROPS.reduce((s, k) => s + D.crops[k].regionsN, 0);
    const maize = D.crops.maize.latest;
    const shares = maize.contributors.slice().sort((a, b) => b.share_pct - a.share_pct).slice(0, 3);
    const card = (num, t, big, sub, extra, on) => '<section class="glass' + (on ? " amber" : "") + '" style="min-height:290px"><div class="mono" style="font-size:13px;color:' + (on ? "var(--signal)" : "var(--muted)") + '">' + num + '</div><div style="font-family:var(--display);font-weight:700;font-size:28px;margin-top:6px">' + t + '</div><div class="mono" style="font-size:40px;margin-top:8px">' + big + '</div><div style="color:var(--frost-2)">' + sub + "</div>" + (extra || "") + "</section>";
    const strip = '<div style="display:flex;gap:3px;margin-top:22px">' + M.strip.values.map((v) => '<i style="flex:1;height:22px;border-radius:3px;background:' + ramp(v) + '"></i>').join("") + '</div><div class="source">' + esc(M.strip.name.toUpperCase()) + " 2012 &middot; " + M.strip.values.length + " DEKADS</div>";
    const bars = shares.map((x) => '<div style="display:grid;grid-template-columns:110px minmax(0,1fr) 46px;gap:10px;align-items:center;margin-top:8px"><span style="color:var(--frost-2);font-size:15px">' + esc(x.name) + '</span><div style="height:6px;border-radius:3px;background:var(--line)"><div style="height:6px;border-radius:3px;width:' + Math.min(100, 2 * x.share_pct).toFixed(0) + '%;background:var(--frost-2)"></div></div><span class="mono" style="font-size:13px;color:var(--muted);text-align:right">' + Math.round(x.share_pct) + "%</span></div>").join("");
    const verdictRow = (ok, t, f, v) => '<div class="ledger"><span style="font-size:22px;color:' + (ok ? "var(--frost)" : "var(--muted)") + '">' + (ok ? "&#10003;" : "&#10005;") + '</span><span class="t" style="color:' + (ok ? "var(--frost)" : "var(--frost-2)") + '">' + esc(t) + '</span><span class="f">' + esc(f) + '</span><span class="caps" style="text-align:right;color:var(--frost-2)">' + v + "</span></div>";
    const word = (x) => (x <= -10 ? "BETTER" : x < 0 ? "MODEST" : "WORSE");
    let ledger = verdictRow(rmW < 0, "Model vs trend only, " + ev.test[0] + " to " + ev.test[1], sg(rmW, 1) + "% error", word(rmW)) + verdictRow(rmU < 0, "Same, every country counted equally", sg(rmU, 1) + "% error", word(rmU));
    Object.values(M.events).forEach((e) => {
      const d = e.first_above_2 ? new Date(e.first_above_2 + "T00:00:00Z") : null;
      const f = d ? "+2 on " + d.getUTCDate() + " " + MON[d.getUTCMonth()] + (e.verdict === "late" ? ", after the peak" : "") : "peak " + sg(e.peak_risk_z);
      ledger += verdictRow(e.verdict === "caught", e.label, f, e.verdict.toUpperCase());
    });
    const bt = M.backtest;
    ledger += verdictRow(bt.best_rule_p_corrected < 0.05, "Trading rule after costs", "p = " + bt.best_rule_p.toFixed(2) + ", " + bt.best_rule_p_corrected.toFixed(2) + " corrected", bt.best_rule_p_corrected < 0.05 ? "EDGE" : "NO EDGE");
    const trs = Object.entries(ev.byCrop).map(([k, b]) => { const m = b.model || {}, t = b.trend_only || {}; return "<tr><td>" + esc(D.crops[k].label) + "</td><td>" + m.n + "</td><td>" + (100 * m.rmse).toFixed(1) + "</td><td>" + (100 * t.rmse).toFixed(1) + "</td><td>" + sg(m.spearman || 0) + "</td><td>" + Math.round(100 * (m.sign_accuracy || 0)) + "%</td></tr>"; }).join("");
    const html = '<h1 class="ttl">Under the hood, four steps.</h1><div class="grid4">' +
      card("01", "Crop maps", totalR.toLocaleString("en-US"), "regions, each set covering 90% of world output (MapSPAM 2020)", '<div style="display:flex;gap:14px;margin-top:26px">' + glyph("maize", 26) + glyph("arabica", 26) + glyph("cocoa", 26) + "</div>") +
      card("02", "Weather", D.meta.cells.toLocaleString("en-US"), "NASA POWER grid points, daily since 1981", strip) +
      card("03", "Model", sg(rmW, 1) + "%", "error vs trend only, end of season, out of sample, weighted by world share", '<div class="chips" style="margin-top:20px">' + chip("LightGBM · 3 crops") + chip("SHAP", true) + "</div>", true) +
      card("04", "World index", sg(maize.z), "maize today, weighted by world shares", bars) + "</div>" +
      '<div class="chips" style="margin-top:16px"><span class="caps" style="margin-right:8px">BEYOND THE COURSE</span>' + ["Weighted geospatial aggregation", "Leak-free temporal validation", "SHAP explanations", "Guard-railed local LLM", "Permutation-tested backtest"].map((t) => chip(t)).join("") + "</div>" +
      '<div class="main c65" style="margin-top:8px"><div class="col"><h2 class="ttl">Tested like sceptics.</h2><div>' + ledger + '</div><div class="source">HarvestRadar is a radar, not a crystal ball. "Caught" means risk_z crossed +2 before the futures price peaked.</div></div>' +
      '<div class="col"><h2 class="ttl">Evaluation, end of season</h2><section class="glass scroll-x"><table class="ev"><thead><tr><th>CROP</th><th>N</th><th>RMSE MODEL</th><th>RMSE TREND</th><th>SPEARMAN</th><th>SIGN</th></tr></thead><tbody>' + trs + '</tbody></table><div class="source">RMSE in percentage points of the yield (maize) or production (tree crops) anomaly, ' + ev.test[0] + "-" + ev.test[1] + ". Each year is predicted by a model trained only on seasons published before it.</div></section>" +
      '<section class="glass"><div class="caps" style="margin-bottom:8px">CREDITS</div><div style="font-size:15px;line-height:1.7;color:var(--frost-2)"><b>Data</b>: NASA POWER (MERRA-2), MapSPAM 2020 (IFPRI, CC BY 4.0), geoBoundaries (CC BY 4.0), FAOSTAT (CC BY 4.0), NOAA CPC ONI, futures closes via yfinance (Yahoo terms), Natural Earth.<br><b>Imagery</b>: NASA Blue Marble Next Generation (public domain).<br><b>Model</b>: LightGBM, SHAP; weekly note by ' + esc(D.meta.llm.display_name) + " (Hugging Face, Apache 2.0), run locally.<br><b>Fonts</b>: Space Grotesk, Inter, JetBrains Mono (SIL OFL).</div></section></div></div>";
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
  document.getElementById("status").textContent = "LIVE · WEEK OF " + D.weekLabel + " · OFFLINE DATA";
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
