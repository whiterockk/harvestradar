/* HarvestRadar static web edition: renders the seven pages from the embedded data snapshot. */
(function () {
  "use strict";
  const D = JSON.parse(document.getElementById("data").textContent);
  const CROPS = ["maize", "coffee", "cocoa"];
  const VIEWS = { stress: "Stress map", commodity: "Commodity", fair: "Fair value", replay: "Replay", note: "Daily note", method: "Method", ask: "Ask Claude" };
  const S = { crop: "maize", episode: Object.keys(D.episodes)[0], note: null, shap: {}, email: false, range: "recent", calc: {}, hist: {}, pending: null, view: null, prev: null, scroll: {}, goto: null, restore: false,
              chat: { turns: [], busy: false, ctl: null, error: "" } };
  let mapHandle = null;

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const sg = (x, n = 2) => (x == null || !isFinite(x) ? "n/a" : (x >= 0 ? "+" : "") + x.toFixed(n));
  const fmtPrice = (key, x) => key === "cocoa" ? Math.round(x).toLocaleString("en-US") : x.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const dLabel = (s) => { const d = new Date(s + "T00:00:00Z"); return d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); };
  const MONTH = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const dLong = (s) => { const d = new Date(s + "T00:00:00Z"); return d.getUTCDate() + " " + MONTH[d.getUTCMonth()] + " " + d.getUTCFullYear(); };
  const pct = (x, n = 1) => (x != null && Math.abs(x) < 0.5 * Math.pow(10, -n) ? (0).toFixed(n) : sg(x, n)) + "%";
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
  const badge = (t, ok) => '<span class="tag plain ' + (ok ? "good" : "bad") + '">' + esc(t) + (ok ? "" : ": failed") + "</span>";
  const tag = (t, tone) => '<span class="tag ' + (tone || "") + '">' + esc(t) + "</span>";

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
        '<div style="min-width:0"><div class="caps" style="white-space:nowrap">' + esc(c.display) + '<span class="hide-sm"> &middot; RISK INDEX</span></div><div class="val' + (z >= 2 ? " glow" : "") + '">' + sg(z) + "</div></div>" + sparkline(s) + "</button>";
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
    const small = window.innerWidth < 700, c = D.crops[key], W = small ? Math.max(300, window.innerWidth - 72) : 1000, H = small ? 320 : 480, m = { l: small ? 44 : 62, r: small ? 52 : 78, t: 40, b: 34 };
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
        '<text x="' + (xs + xe) / 2 + '" y="' + (m.t - 10) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + esc((small ? st : c.mainCountry + " " + st + " window").toUpperCase()) + "</text>";
    });
    niceTicks(lo, hi, 7).forEach((v) => { g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="' + (v === 0 ? "#2A3646" : "#1E2935") + '"/><text x="' + (m.l - 8) + '" y="' + (y(v) + 4) + '" text-anchor="end" font-size="13" fill="#FFB547">' + (v > 0 ? "+" : "") + v + "</text>"; });
    niceTicks(plo, phi, 6).forEach((v) => { g += '<text x="' + (W - m.r + 8) + '" y="' + (y2(v) + 4) + '" font-size="13" fill="#C7D1DB">' + (key === "cocoa" ? Math.round(v).toLocaleString("en-US") : v) + "</text>"; });
    if (!small) g += '<text transform="translate(16,' + (m.t + (H - m.t - m.b) / 2) + ') rotate(-90)" text-anchor="middle" font-size="13" fill="#FFB547">RISK INDEX (0 = NORMAL)</text>';
    if (!small) g += '<text transform="translate(' + (W - 12) + "," + (m.t + (H - m.t - m.b) / 2) + ') rotate(90)" text-anchor="middle" font-size="13" fill="#C7D1DB">' + esc(c.priceUnit.toUpperCase()) + "</text>";
    for (let k = 0; k < 16; k++) { const d = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1 + (small ? 5 : 2) * k, 1)); if (d > end) break; g += '<text x="' + x(d) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + MON[d.getUTCMonth()] + " " + d.getUTCFullYear() + "</text>"; }
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
    const per = -pi.slope_pct_per_pct, fv = c.fair && c.fair.now;
    const fvLine = fv ? '<div style="font-size:16px;color:var(--frost-2);margin-top:12px;line-height:1.6;padding-top:12px;border-top:1px solid var(--line)">Climate fair value today: <span class="mono" style="color:var(--signal)">' + fmtPrice(k, fv.fair) + "</span>. The price (" + '<span class="mono">' + fmtPrice(k, fv.close) + "</span>) is " + gapWords(fv.gap_to_fair_pct) + '. <a href="#fair" data-goto="calc">Open the pricing tool &rarr;</a></div>' : "";
    return panel("WHAT IT MEANS FOR THE PRICE", '<div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap"><span class="mono" style="font-size:40px;color:var(--signal)">' + pct(pi.implied_pct) + '</span><span style="color:var(--frost-2)">expected move of the futures price over the marketing year</span></div>' +
      '<div style="font-size:16px;color:var(--frost-2);margin-top:8px;line-height:1.6">Likely between <span class="mono">' + pct(pi.low_pct) + '</span> and <span class="mono">' + pct(pi.high_pct) + "</span> (8 chances in 10). Since " + pi.years[0] + ", each 1% of world supply missing came with about <span class=\"mono\">" + pct(per) + "</span> on the " + esc(c.label.toLowerCase()) + " price.</div>" + fvLine,
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
      '<div style="font-size:15px;color:var(--frost-2);line-height:1.6;margin-top:6px">How to read it: the orange line rises when the model expects less ' + esc(c.label.toLowerCase()) + " than usual for this time of year. The shaded band is the " + esc(c.mainCountry) + " critical window, when weather matters most for the harvest. The white line is the price, for comparison.</div></section>" +
      comovePanel(k, true) + "</div>" +
      '<div class="col">' + priceCard(k) + askPanel(k) + panel("WHICH COUNTRIES DRIVE TODAY'S READING", barRows(rows, "", 240), "In points of world supply: each country's share of world output times its expected harvest gap. Amber raises the risk, blue lowers it.") +
      '<div class="chips" role="group" aria-label="Country">' + countries.map((iso) => '<button class="chip' + (iso === sel ? " on" : "") + '" data-shap="' + iso + '">' + esc(name(iso)) + "</button>").join("") + "</div>" +
      panel("WHICH WEATHER DRIVES THE FORECAST <span style='float:right;color:var(--signal)'>" + esc(name(sel).toUpperCase()) + "</span>", barRows(shapRows, "", 220), "In points of " + c.target + " vs normal. Contribution of each weather factor to the forecast for the " + (sh ? sh.season : "") + " harvest (SHAP values).") +
      "</div></div>";
    return { html: html, after: null };
  }

  /* ---------- climate fair value and pricing tool ---------- */
  function gapWords(g) {
    if (g == null || !isFinite(g)) return "not comparable";
    if (Math.abs(g) < 1) return "in line with it";
    return Math.abs(g).toFixed(1) + "% " + (g < 0 ? "below" : "above") + " it";
  }
  const corrWord = (r) => (r == null ? "n/a" : Math.abs(r) < 0.1 ? "no link" : Math.abs(r) < 0.3 ? "weak link" : Math.abs(r) < 0.5 ? "moderate link" : "strong link");

  function comovePanel(k, compact) {
    const c = D.crops[k], cm = c.fair && c.fair.comove;
    if (!cm) return "";
    const tile = (v, lab) => '<div class="stat"><div class="mono">' + (v == null ? "n/a" : sg(v)) + '</div><div class="lab">' + lab + " <span style=\"color:var(--muted)\">(" + corrWord(v) + ")</span></div></div>";
    const tiles = '<div class="grid3" style="margin-top:4px">' + tile(cm.weekly_changes, "Week-to-week changes of the index and of the price") +
      tile(cm.weekly_changes_in_windows, "Same, only in critical weather windows (" + cm.weeks_in_windows + " weeks)") +
      tile(cm.index_vs_next_13_weeks, "Index level vs the price change over the next 13 weeks") + "</div>";
    const text = '<div style="font-size:15px;color:var(--frost-2);line-height:1.65;margin-top:12px">The index measures how much ' + esc(c.label.toLowerCase()) +
      " the world should harvest compared with normal for the time of year. It is not a price model. Prices also move with demand, stocks, the dollar, fund positions, other origins and the official crop reports, and traders often price a weather scare before it shows up in harvest forecasts. " +
      "So the two lines can diverge for weeks. Read the index for the supply side, then use the " + (compact ? '<a href="#fair">climate fair value</a>' : "climate fair value") + " to turn it into a price.</div>";
    return '<section class="glass"><div class="caps" style="margin-bottom:12px">WHY THE INDEX AND THE PRICE DO NOT MOVE TOGETHER</div>' + tiles + text +
      '<div class="source">Correlations, weekly data since ' + cm.from.slice(0, 4) + " (" + cm.weeks + " weeks). 0 means no link, 1 means the two move as one.</div></section>";
  }

  function fairChart(k, mode) {
    const f = D.crops[k].fair, s = mode === "long" ? f.long : f.recent, small = window.innerWidth < 700;
    const W = small ? Math.max(300, window.innerWidth - 72) : 1000, H = small ? 300 : 440, m = { l: small ? 46 : 70, r: small ? 10 : 128, t: 18, b: 34 };
    const T = s.d.map((d) => new Date(d + "T00:00:00Z"));
    const vals = [].concat(s.close, s.fair_lo, s.fair_hi, s.anchor).filter((v) => v != null && isFinite(v));
    let lo = Math.min(...vals), hi = Math.max(...vals); const pad = (hi - lo) * 0.06; lo -= pad; hi += pad;
    const t0 = T[0], t1 = T[T.length - 1];
    const x = (d) => m.l + ((d - t0) / (t1 - t0)) * (W - m.l - m.r);
    const y = (v) => m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b);
    const line = (arr) => arr.map((v, i) => (i ? "L" : "M") + x(T[i]).toFixed(1) + "," + y(v).toFixed(1)).join(" ");
    let g = "";
    niceTicks(lo, hi, 6).forEach((v) => { g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="#1E2935"/><text x="' + (m.l - 8) + '" y="' + (y(v) + 4) + '" text-anchor="end" font-size="13" fill="#8A9AAB">' + (k === "cocoa" ? Math.round(v).toLocaleString("en-US") : v) + "</text>"; });
    if (mode === "long") {
      const step = small ? 5 : 2;
      for (let yr = t0.getUTCFullYear() + 1; yr <= t1.getUTCFullYear(); yr++) if (yr % step === 0) { const d = new Date(Date.UTC(yr, 0, 1)); g += '<text x="' + x(d) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + yr + "</text>"; }
    } else {
      const step = small ? 6 : 3;
      for (let d = new Date(Date.UTC(t0.getUTCFullYear(), t0.getUTCMonth() + 1, 1)); d <= t1; d = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1))) if (d.getUTCMonth() % step === 0) g += '<text x="' + x(d) + '" y="' + (H - 10) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + MON[d.getUTCMonth()] + " " + d.getUTCFullYear() + "</text>";
    }
    const band = s.fair_hi.map((v, i) => (i ? "L" : "M") + x(T[i]).toFixed(1) + "," + y(v).toFixed(1)).join(" ") + " " +
      s.fair_lo.map((v, i) => [i, v]).reverse().map(([i, v]) => "L" + x(T[i]).toFixed(1) + "," + y(v).toFixed(1)).join(" ") + " Z";
    g += '<path d="' + band + '" fill="rgba(255,181,71,.16)"/>';
    g += '<path d="' + line(s.anchor) + '" fill="none" stroke="#8A9AAB" stroke-width="1.3" stroke-dasharray="5 6"/>';
    g += '<path d="' + line(s.close) + '" fill="none" stroke="#EAF0F5" stroke-opacity=".85" stroke-width="1.6"/>';
    g += '<path d="' + line(s.fair) + '" fill="none" stroke="#FFB547" stroke-width="2.6" stroke-linejoin="round"/>';
    const n = T.length - 1, xf = x(T[n]);
    let yf = y(s.fair[n]), yp = y(s.close[n]);
    g += '<circle cx="' + xf + '" cy="' + yf + '" r="4.5" fill="#FFB547"/><circle cx="' + xf + '" cy="' + yp + '" r="4" fill="#EAF0F5"/>';
    if (!small) {
      if (Math.abs(yf - yp) < 34) { const mid = (yf + yp) / 2, up = yf < yp ? -1 : 1; yf = mid + up * 17; yp = mid - up * 17; }
      g += '<text x="' + (xf + 10) + '" y="' + (yf - 2) + '" font-size="13" fill="#FFB547">FAIR VALUE</text><text x="' + (xf + 10) + '" y="' + (yf + 14) + '" font-size="13" fill="#FFB547">' + fmtPrice(k, s.fair[n]) + "</text>";
      g += '<text x="' + (xf + 10) + '" y="' + (yp - 2) + '" font-size="13" fill="#EAF0F5">PRICE</text><text x="' + (xf + 10) + '" y="' + (yp + 14) + '" font-size="13" fill="#EAF0F5">' + fmtPrice(k, s.close[n]) + "</text>";
    }
    g += '<line class="cross" x1="0" x2="0" y1="' + m.t + '" y2="' + (H - m.b) + '" stroke="#C7D1DB" stroke-opacity=".5" visibility="hidden"/>';
    return '<div class="chart-wrap" data-chart="fair" data-mode="' + mode + '" data-w="' + W + '" data-l="' + m.l + '" data-r="' + m.r + '"><svg viewBox="0 0 ' + W + " " + H + '" width="100%" role="img" aria-label="Futures price and climate fair value">' + g + '</svg><div class="chart-tip"></div></div>';
  }

  function hookFairChart() {
    const wrap = document.querySelector('[data-chart="fair"]');
    if (!wrap) return;
    const k = S.crop, f = D.crops[k].fair, s = wrap.dataset.mode === "long" ? f.long : f.recent;
    const W = +wrap.dataset.w, L = +wrap.dataset.l, R = +wrap.dataset.r, svg = wrap.querySelector("svg"), tip = wrap.querySelector(".chart-tip"), cross = svg.querySelector(".cross");
    const T = s.d.map((d) => Date.parse(d + "T00:00:00Z")), t0 = T[0], t1 = T[T.length - 1];
    const move = (e) => {
      const b = svg.getBoundingClientRect(), vx = ((e.clientX - b.left) / b.width) * W;
      const t = t0 + ((vx - L) / (W - L - R)) * (t1 - t0);
      let lo = 0, hi = T.length - 1; while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (T[mid] < t) lo = mid; else hi = mid; }
      const i = Math.abs(T[lo] - t) < Math.abs(T[hi] - t) ? lo : hi, cx = L + ((T[i] - t0) / (t1 - t0)) * (W - L - R);
      cross.setAttribute("x1", cx); cross.setAttribute("x2", cx); cross.setAttribute("visibility", "visible");
      const gp = 100 * (s.close[i] / s.fair[i] - 1);
      tip.innerHTML = '<div style="color:var(--frost);font-weight:600;margin-bottom:2px">' + dLong(s.d[i]) + '</div><div><span class="k">Price</span><span class="mono">' + fmtPrice(k, s.close[i]) + '</span></div><div><span class="k" style="color:var(--signal)">Fair value</span><span class="mono">' + fmtPrice(k, s.fair[i]) +
        '</span></div><div><span class="k">80% range</span><span class="mono">' + fmtPrice(k, s.fair_lo[i]) + " to " + fmtPrice(k, s.fair_hi[i]) + '</span></div><div><span class="k">12-month average</span><span class="mono">' + fmtPrice(k, s.anchor[i]) + '</span></div><div><span class="k">Price vs fair value</span><span class="mono">' + pct(gp) + "</span></div>";
      const px = (cx / W) * b.width, wb = wrap.getBoundingClientRect();
      tip.style.left = Math.min(wb.width - tip.offsetWidth - 4, Math.max(4, px + 14)) + "px"; tip.style.top = "8px"; tip.style.opacity = 1;
    };
    svg.addEventListener("mousemove", move);
    svg.addEventListener("mouseleave", () => { tip.style.opacity = 0; cross.setAttribute("visibility", "hidden"); });
  }

  function flexChart(k) {
    const small = window.innerWidth < 700, f = D.crops[k].fair, fx = f.flex, P = fx.points, W = small ? Math.max(300, window.innerWidth - 72) : 600, H = small ? 300 : 380, m = { l: 58, r: 16, t: 16, b: 52 };
    const xs = P.map((p) => p[1]), ys = P.map((p) => p[2]), gNow = f.now.supply_gap_pct;
    const xr = Math.max(2, ...xs.map(Math.abs), Math.abs(gNow)) * 1.12, yr = Math.max(10, ...ys.map(Math.abs)) * 1.1;
    const x = (v) => m.l + ((v + xr) / (2 * xr)) * (W - m.l - m.r), y = (v) => m.t + (1 - (v + yr) / (2 * yr)) * (H - m.t - m.b);
    const mx = xs.reduce((a, b) => a + b, 0) / xs.length, my = ys.reduce((a, b) => a + b, 0) / ys.length, b = fx.slope_pct_per_pct, a = my - b * mx;
    let g = "";
    niceTicks(-yr, yr, 5).forEach((v) => { g += '<line x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(v) + '" y2="' + y(v) + '" stroke="' + (v === 0 ? "#2A3646" : "#1E2935") + '"/><text x="' + (m.l - 6) + '" y="' + (y(v) + 4) + '" text-anchor="end" font-size="13" fill="#8A9AAB">' + (v > 0 ? "+" : "") + v + "</text>"; });
    niceTicks(-xr, xr, 6).forEach((v) => { g += '<line x1="' + x(v) + '" x2="' + x(v) + '" y1="' + m.t + '" y2="' + (H - m.b) + '" stroke="' + (v === 0 ? "#2A3646" : "#1E2935") + '"/><text x="' + x(v) + '" y="' + (H - m.b + 18) + '" text-anchor="middle" font-size="13" fill="#8A9AAB">' + (v > 0 ? "+" : "") + v + "</text>"; });
    g += '<text x="' + ((m.l + W - m.r) / 2) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="13" fill="#C7D1DB">WORLD SUPPLY VS NORMAL (%)</text>';
    g += '<text transform="translate(14,' + ((m.t + H - m.b) / 2) + ') rotate(-90)" text-anchor="middle" font-size="13" fill="#C7D1DB">PRICE CHANGE IN THE YEAR (%)</text>';
    g += '<line x1="' + x(-xr) + '" y1="' + y(a - b * xr) + '" x2="' + x(xr) + '" y2="' + y(a + b * xr) + '" stroke="#FFB547" stroke-width="2.4"/>';
    g += '<line x1="' + x(gNow) + '" x2="' + x(gNow) + '" y1="' + m.t + '" y2="' + (H - m.b) + '" stroke="#FFB547" stroke-dasharray="5 5" stroke-opacity=".8"/><text x="' + (x(gNow) + (gNow > 0 ? -6 : 6)) + '" y="' + (H - m.b - 8) + '" text-anchor="' + (gNow > 0 ? "end" : "start") + '" font-size="13" fill="#FFB547">TODAY</text>';
    P.forEach((p) => { g += '<circle cx="' + x(p[1]).toFixed(1) + '" cy="' + y(p[2]).toFixed(1) + '" r="5" fill="#C7D1DB" fill-opacity=".75"><title>' + p[0] + ": supply " + pct(p[1]) + ", price " + pct(p[2]) + "</title></circle>"; });
    return '<svg viewBox="0 0 ' + W + " " + H + '" width="100%" role="img" aria-label="World supply gap and price change, one dot per marketing year">' + g + "</svg>";
  }

  function calcDefaults(k) {
    const f = D.crops[k].fair;
    return { gap: f.now.supply_gap_pct, r: -f.flex.slope_pct_per_pct, anchor: f.now.anchor, scen: "today" };
  }
  function calcResult(k, st) {
    const f = D.crops[k].fair, se = f.flex.se, e = (r) => Math.exp((r * -st.gap) / 100), d0 = calcDefaults(k), nw = f.now;
    if (st.gap === d0.gap && st.r === d0.r && st.anchor === d0.anchor) return { fair: nw.fair, lo: nw.fair_lo, hi: nw.fair_hi, prem: nw.premium_pct, vs: nw.gap_to_fair_pct, z: D.crops[k].latest.z };
    const fair = st.anchor * e(st.r), a = st.anchor * e(st.r - 1.2816 * se), b = st.anchor * e(st.r + 1.2816 * se);
    return { fair: fair, lo: Math.min(a, b), hi: Math.max(a, b), prem: 100 * (e(st.r) - 1), vs: 100 * (f.now.close / fair - 1), z: (f.mu - st.gap) / f.sigma };
  }
  function calcPanel(k) {
    const f = D.crops[k].fair, st = S.calc[k] || (S.calc[k] = calcDefaults(k)), fx = f.flex;
    const scen = [["Today", null], ["Normal season (index 0)", 0], ["Rare (index +2)", 2], ["Extreme (index +3)", 3], ["Good harvest (index -2)", -2]];
    const gmin = Math.floor(Math.min(-6, f.mu - 4 * f.sigma)), gmax = Math.ceil(Math.max(6, f.mu + 4 * f.sigma));
    const back = S.prev && S.prev !== "fair" && VIEWS[S.prev] ? '<a href="#' + S.prev + '" data-back="1" style="display:inline-flex;align-items:center;gap:8px;margin-bottom:14px;font-size:15px;color:var(--signal);text-decoration:none;min-height:32px">&larr; Back to ' + esc(VIEWS[S.prev]) + "</a>" : "";
    return '<section class="glass calc" id="calc" style="scroll-margin-top:12px">' + back + '<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap"><div class="caps">PRICING TOOL &middot; ' + esc(D.crops[k].display) + '</div><div style="display:flex;gap:8px"><button class="btn sm" id="calc-undo" type="button">Undo</button><button class="btn sm" id="calc-reset" type="button">Back to today</button></div></div>' +
      '<div style="font-size:15px;color:var(--frost-2);margin-top:8px;line-height:1.55">Move the expected world supply, or pick a scenario, to see the fair value it would justify.</div>' +
      '<div class="chips" style="margin-top:12px" role="group" aria-label="Scenario">' + scen.map(([l, z]) => { const v = z == null ? "today" : String(z); return '<button class="chip' + (st.scen === v ? " on" : "") + '" data-scen="' + v + '" aria-pressed="' + (st.scen === v) + '">' + l + "</button>"; }).join("") + "</div>" +
      '<label for="i-gap"><span>Expected world supply vs normal</span><output id="o-gap"></output></label><input type="range" id="i-gap" min="' + gmin + '" max="' + gmax + '" step="0.05" value="' + st.gap + '"><div class="hint" id="o-z"></div>' +
      '<label for="i-r"><span>Price reaction to 1% of world supply missing</span><output id="o-r"></output></label><input type="range" id="i-r" min="0" max="8" step="0.05" value="' + st.r + '"><div class="hint">Measured ' + fx.years[0] + "-" + fx.years[1] + ": " + (-fx.slope_pct_per_pct).toFixed(2) + "% (uncertainty " + fx.se.toFixed(2) + ")</div>" +
      '<label for="i-anchor"><span>Anchor price, ' + esc(D.crops[k].priceUnit) + '</span></label><input type="number" id="i-anchor" step="any" value="' + (+st.anchor.toFixed(2)) + '"><div class="hint">Default: average close of the last 12 months (' + fmtPrice(k, f.now.anchor) + ")</div>" +
      '<div class="result"><div class="caps">FAIR VALUE IN THIS SCENARIO</div><div class="mono glow" id="o-fair" style="font-size:44px;color:var(--signal);margin-top:6px"></div><div id="o-range" style="font-size:15px;color:var(--frost-2);line-height:1.6"></div><div id="o-vs" style="font-size:15px;color:var(--frost-2);line-height:1.6;margin-top:6px"></div><button class="btn sm" style="margin-top:12px" data-askopen="Explain the scenario I set in the pricing tool and what would have to happen for it to play out.">Ask Claude about this scenario</button></div>' +
      '<div class="source">Fair value = anchor &times; exp(reaction &times; supply missing / 100). The 80% range comes from the uncertainty of the measured reaction. Research tool, not investment advice.</div></section>';
  }
  const snap = (st) => ({ gap: st.gap, r: st.r, anchor: st.anchor, scen: st.scen });
  function calcPush(k, prev) { const h = S.hist[k] || (S.hist[k] = []); h.push(prev); if (h.length > 50) h.shift(); }
  function calcSync() {
    const k = S.crop, st = S.calc[k], el = (id) => document.getElementById(id);
    if (!el("i-gap")) return;
    el("i-gap").value = st.gap; el("i-r").value = st.r;
    if (document.activeElement !== el("i-anchor")) el("i-anchor").value = +(+st.anchor).toFixed(2);
    calcUpdate();
  }
  function calcUpdate() {
    const k = S.crop, st = S.calc[k], el = (id) => document.getElementById(id);
    if (!el("o-fair")) return;
    document.querySelectorAll("[data-scen]").forEach((b) => { const on = b.dataset.scen === st.scen; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
    const d0 = calcDefaults(k), atToday = st.gap === d0.gap && st.r === d0.r && st.anchor === d0.anchor;
    el("calc-undo").disabled = !(S.hist[k] || []).length; el("calc-reset").disabled = atToday;
    const r = calcResult(k, st), c = D.crops[k];
    el("o-gap").textContent = pct(st.gap, 2); el("o-r").textContent = st.r.toFixed(2) + "%";
    el("o-z").textContent = "Same as a risk index of " + sg(r.z) + " today";
    el("o-fair").textContent = fmtPrice(k, r.fair);
    el("o-range").textContent = "Likely between " + fmtPrice(k, r.lo) + " and " + fmtPrice(k, r.hi) + " (8 chances in 10). Climate premium " + pct(r.prem) + " on the anchor.";
    el("o-vs").textContent = "Last close " + fmtPrice(k, c.fair.now.close) + " (" + dLong(c.fair.now.date) + ") is " + gapWords(r.vs) + ".";
  }

  function viewFair() {
    const k = S.crop, c = D.crops[k], f = c.fair;
    if (!f) return { html: ticker() + '<section class="glass" style="margin-top:16px">No fair value in this data snapshot. Run <span class="mono">harvestradar index price</span>.</section>', after: null };
    const nw = f.now, fx = f.flex, unreliable = !nw.reliable;
    const warn = unreliable ? '<div class="warnbox" style="margin-top:16px">No reliable link between world supply gaps and the ' + esc(c.label.toLowerCase()) + " price was found over " + fx.years[0] + "-" + fx.years[1] + " (" + Math.round(100 * fx.p_value) + "% chance that the measured slope is pure luck). The fair value therefore stays close to the 12-month average whatever the weather. Use it with care.</div>" : "";
    const cards = '<div class="cards3">' +
      '<section class="glass' + (unreliable ? "" : " amber") + '" style="min-height:170px"><div class="caps">CLIMATE FAIR VALUE</div><div class="mono glow hero-val" style="font-size:56px;line-height:1.1;color:var(--signal);margin-top:8px">' + fmtPrice(k, nw.fair) + '</div><div class="source">Likely between ' + fmtPrice(k, nw.fair_lo) + " and " + fmtPrice(k, nw.fair_hi) + ". The price that today's expected supply justifies on its own.</div></section>" +
      '<section class="glass" style="min-height:170px"><div class="caps">' + esc(c.priceLabel) + '</div><div class="mono" style="font-size:34px;margin-top:12px">' + fmtPrice(k, nw.close) + '</div><div style="margin-top:10px">' + tag(Math.abs(nw.gap_to_fair_pct) < 1 ? "In line with fair value" : Math.abs(nw.gap_to_fair_pct).toFixed(1) + "% " + (nw.gap_to_fair_pct < 0 ? "below" : "above") + " fair value", nw.gap_to_fair_pct < 0 ? "good" : "warn") + '</div><div class="source">Close on ' + dLong(nw.date) + ".</div></section>" +
      '<section class="glass" style="min-height:170px"><div class="caps">CLIMATE PREMIUM</div><div class="mono" style="font-size:34px;margin-top:12px">' + pct(nw.premium_pct) + '</div><div class="source">On the 12-month average of ' + fmtPrice(k, nw.anchor) + ", for an expected world supply of " + pct(nw.supply_gap_pct, 2) + " vs normal.</div></section></div>";
    const rng = '<div class="chips" role="group" aria-label="Period">' + [["recent", "2 years"], ["long", "Since 2006"]].map(([v, l]) => '<button class="chip' + (S.range === v ? " on" : "") + '" data-range="' + v + '">' + l + "</button>").join("") + "</div>";
    const chart = '<section class="glass" style="padding:16px 18px"><div style="display:flex;flex-wrap:wrap;gap:10px 20px;align-items:center;justify-content:space-between;margin-bottom:8px"><span style="font-family:var(--display);font-weight:700;font-size:20px">Futures price and climate fair value</span>' + rng + "</div>" +
      '<div class="legend-row" style="margin-bottom:6px"><span><i style="background:#FFB547"></i>Climate fair value</span><span><i style="background:rgba(255,181,71,.35);height:10px"></i>80% range</span><span><i style="background:#EAF0F5"></i>' + esc(c.priceName) + '</span><span><i style="background:repeating-linear-gradient(90deg,#8A9AAB 0 5px,transparent 5px 10px)"></i>12-month average (anchor)</span></div>' +
      fairChart(k, S.range) +
      '<div style="font-size:15px;color:var(--frost-2);line-height:1.6;margin-top:6px">How to read it: the orange line is the 12-month average price moved up or down by what the expected world supply implies. When the white price line is below it, the market prices less weather risk than the supply forecast suggests; above it, more. The gap is what other drivers explain (demand, stocks, the dollar, funds). Hover the chart for the values of each day.</div>' +
      '<div class="source">' + (S.range === "long" ? "Weekly (Fridays) since 2006" : "Every trading day, last 2 years") + ". Updated with every data run. The price reaction is measured on " + fx.years[0] + "-" + fx.years[1] + ", so values before " + (fx.years[1] + 1) + " are in-sample.</div></section>";
    const scatter = panel("HOW THE PRICE REACTION IS MEASURED", flexChart(k) + '<div style="font-size:15px;color:var(--frost-2);line-height:1.6;margin-top:8px">One dot per marketing year: the realised world supply vs normal (FAOSTAT) and the change of the average futures price. The orange line is the fitted reaction: ' + (-fx.slope_pct_per_pct).toFixed(2) + "% on the price for each 1% of world supply missing.</div>",
      fx.n + " marketing years, " + fx.years[0] + "-" + fx.years[1] + ". Share of yearly price changes explained: " + Math.round(100 * fx.r2) + "%. Chance the link is pure luck: " + (fx.p_value < 0.01 ? "under 1%" : Math.round(100 * fx.p_value) + "%") + ".");
    const back = S.prev && S.prev !== "fair" && VIEWS[S.prev] ? '<div style="margin-bottom:12px"><a class="chip" href="#' + S.prev + '" data-back="1" style="text-decoration:none;letter-spacing:.04em;text-transform:none;font-family:var(--body);font-size:15px">&larr; Back to ' + esc(VIEWS[S.prev]) + "</a></div>" : "";
    const html = back + ticker() + warn + '<div class="main c65"><div class="col">' + cards + chart + comovePanel(k, false) + '</div><div class="col">' + calcPanel(k) + scatter + "</div></div>";
    return { html: html, after: () => { hookFairChart(); calcUpdate(); } };
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
      const tag = x.model === "deterministic-template" ? "Fixed template" : (x.templateParagraphs ? x.templateParagraphs + " of 3 paragraphs from the template" : "Written by the AI model");
      const head = x.week !== lastDay ? '<div class="caps" style="margin:8px 4px 0">' + dLong(x.week) + "</div>" : "";
      lastDay = x.week;
      return head + '<button class="glass inbox-item' + (keyOf(x) === keyOf(n) ? " on" : "") + '" data-note="' + keyOf(x) + '">' + glyph(D.crops[x.commodity].glyph, 22) + '<div style="flex:1;min-width:0"><div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline"><span style="font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + esc(x.title) + '</span><span class="mono" style="font-size:13px;color:var(--muted);flex:none">07:00</span></div><div style="font-size:13px;color:var(--muted);margin-top:2px">' + tag + "</div></div></button>";
    }).join("");
    const readings = '<div><div class="caps" style="margin-bottom:8px">RISK INDEX ON ' + dLong(n.week).toUpperCase() + '</div><div class="grid3">' + Object.keys(n.readings).map((k) => {
      const r = n.readings[k], s = D.crops[k].riskRecent, i = s.d.indexOf(r.date), series = s.z.slice(Math.max(0, i - 25), i + 1);
      return '<div class="glass tick-card' + (k === n.commodity ? " sel" : "") + '" style="cursor:default">' + glyph(r.glyph, 26) + '<div style="min-width:0"><div class="caps" style="white-space:nowrap">' + esc(r.display) + '</div><div class="val' + (r.value >= 2 ? " glow" : "") + '">' + esc(r.text) + "</div></div>" + sparkline(series, 96) + "</div>";
    }).join("") + "</div></div>";
    const who = n.model === "deterministic-template" ? "Written from the fixed template (the AI model failed the checks)" : "Written by a small AI model running locally (" + esc(D.meta.llm.display_name) + ")" + (n.templateParagraphs ? "; " + n.templateParagraphs + " of 3 paragraphs from the fixed template" : "");
    const figs = Object.values(n.slots).filter((s) => s.kind === "figure").map((s) => '<div class="glass" style="padding:14px 16px"><div class="mono" style="font-size:22px;color:var(--signal)">' + esc(s.text) + '</div><div style="font-size:15px;color:var(--frost-2);margin-top:4px">' + esc(s.label) + '</div><div class="source" style="margin-top:6px">Source: ' + esc(s.source) + "<br>" + esc(s.date) + (s.detail ? ", " + esc(s.detail) : "") + "</div></div>").join("");
    const html = '<div class="main c30"><div class="col"><div style="display:flex;justify-content:space-between;align-items:baseline;margin:4px 4px 0"><span style="font-family:var(--display);font-weight:700;font-size:28px">Inbox</span><span class="caps">EVERY WORKING DAY, 07:00</span></div><div class="inbox-list">' + inbox + "</div></div>" +
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
    const row = (t, f, v, tone) => '<tr><td class="t">' + t + '</td><td class="f">' + f + '</td><td class="v">' + tag(v, tone) + "</td></tr>";
    const gain = (x) => (x <= -10 ? ["Clear gain", "good"] : x < 0 ? ["Small gain", "good"] : ["No gain", "bad"]);
    const errTxt = (x) => Math.abs(x).toFixed(1) + "% " + (x < 0 ? "smaller" : "larger") + " error than the trend";
    let ledger = row("Harvest forecasts vs a simple trend, " + ev.test[0] + " to " + ev.test[1] + ", weighted by world share", errTxt(rmW), ...gain(rmW)) + row("Same, every country counted equally", errTxt(rmU), ...gain(rmU));
    Object.values(M.events).forEach((e) => {
      const f = e.first_above_2 ? "Above +2 on " + dLong(e.first_above_2) + (e.verdict === "late" ? ", after the price peak" : ", before the price peak") : "Highest " + sg(e.peak_risk_z) + ", never above +2";
      ledger += row(esc(e.label), f, ...({ caught: ["Caught", "good"], late: ["Too late", "warn"], missed: ["Missed", "bad"] }[e.verdict]));
    });
    const bt = M.backtest, sig = bt.best_rule_p_corrected < 0.05;
    ledger += row("Trading on the index, after costs", Math.round(100 * bt.best_rule_p_corrected) + "% chance the gain is luck", sig ? "Significant" : "Not significant", sig ? "good" : "neutral");
    ledger = '<section class="glass"><table class="ledger"><thead><tr><th>TEST</th><th>RESULT</th><th class="r">VERDICT</th></tr></thead><tbody>' + ledger + "</tbody></table></section>";
    const trs = Object.entries(ev.byCrop).map(([k, b]) => { const m = b.model || {}, t = b.trend_only || {}; return "<tr><td>" + esc(D.crops[k].label) + "</td><td>" + m.n + "</td><td>" + (100 * m.rmse).toFixed(1) + "</td><td>" + (100 * t.rmse).toFixed(1) + "</td><td>" + sg(m.spearman || 0) + "</td><td>" + Math.round(100 * (m.sign_accuracy || 0)) + "%</td></tr>"; }).join("");
    const html = '<h1 class="ttl">Under the hood, four steps.</h1><div class="grid4">' +
      card("1", "Crop maps", totalR.toLocaleString("en-US"), "producing regions, covering 90% of world output of each crop (MapSPAM 2020)", '<div style="display:flex;gap:14px;margin-top:26px">' + glyph("maize", 26) + glyph("arabica", 26) + glyph("cocoa", 26) + "</div>") +
      card("2", "Weather", D.meta.cells.toLocaleString("en-US"), "NASA weather points, read every day since 1981", strip) +
      card("3", "Model", pct(rmW), "smaller harvest-forecast error than a simple trend, on harvests the model had never seen, weighted by world share", '<div class="chips" style="margin-top:20px">' + chip("Gradient boosting") + chip("Explained factor by factor", true) + "</div>", true) +
      card("4", "World index", sg(maize.z), "maize today: country forecasts weighted by their share of world output", bars) + "</div>" +
      '<div class="chips" style="margin-top:16px"><span class="caps" style="margin-right:8px">BEYOND THE COURSE</span>' + ["Weather weighted by where crops grow", "Testing without peeking at the future", "Explanations by weather factor (SHAP)", "Local AI writer with fact checks", "Trading test against luck"].map((t) => chip(t)).join("") + "</div>" +
      '<div class="main c65" style="margin-top:8px"><div class="col"><h2 class="ttl">Tested like sceptics.</h2>' + ledger + '<div class="source">HarvestRadar is a radar, not a crystal ball. "Caught" means the index went above +2 before the futures price peaked.</div></div>' +
      '<div class="col"><h2 class="ttl">Forecast errors by crop</h2><section class="glass scroll-x"><table class="ev"><thead><tr><th>CROP</th><th>HARVESTS</th><th>MODEL ERROR</th><th>TREND ERROR</th><th>RANK MATCH</th><th>RIGHT DIRECTION</th></tr></thead><tbody>' + trs + '</tbody></table><div class="source">Typical error, in percentage points of yield (maize) or production (tree crops) vs normal, harvests ' + ev.test[0] + " to " + ev.test[1] + ". Rank match: how well the model orders good and bad harvests (1 = perfectly). Each year is forecast by a model trained only on harvests published before it.</div></section>" +
      '<section class="glass"><div class="caps" style="margin-bottom:8px">CREDITS</div><div style="font-size:15px;line-height:1.7;color:var(--frost-2)"><b>Data</b>: NASA POWER weather, MapSPAM 2020 crop maps (IFPRI), geoBoundaries regions, FAOSTAT harvests, NOAA El Ni&ntilde;o index, futures prices via Yahoo Finance, Natural Earth.<br><b>Imagery</b>: NASA Blue Marble (public domain).<br><b>Model</b>: LightGBM gradient boosting, SHAP explanations; daily note by ' + esc(D.meta.llm.display_name) + " (Hugging Face), run locally.<br><b>Fonts</b>: Space Grotesk, Inter, JetBrains Mono.</div></section></div></div>";
    return { html: html, after: null };
  }

  /* ---------- Ask Claude: runs on the viewer's own Claude plan through the artifact "sample" capability ---------- */
  const ASK = { fn: undefined, state: "connecting" };
  function connectClaude() {
    if (ASK.fn !== undefined) return;
    ASK.fn = null;
    if (!window.claude || typeof window.claude.use !== "function") { ASK.state = "absent"; return; }
    window.claude.use("sample").then((fn) => {
      ASK.fn = fn; ASK.state = fn ? "ready" : "absent"; askRefresh();
      if (fn && S.queued) { const q = S.queued; S.queued = null; askSend(q); }
    }).catch(() => { ASK.state = "absent"; S.queued = null; askRefresh(); });
  }
  const NOTE_TEXT = (n) => n.template.replace(/\{([A-Z][A-Z0-9_]*)\}/g, (all, k) => (n.slots[k] ? n.slots[k].text : all));
  function claudeContext() {
    const L = ["HARVESTRADAR DATA SNAPSHOT (data as of " + dLong(D.asOf) + ")", "",
      "What the numbers mean: the harvest-risk index compares the model's expected world supply of a crop with what is normal for the same time of year (0 = normal, positive = less supply than normal, above +2 = rare). Expected world supply vs normal is the sum over producing countries of share of world output times the forecast harvest gap. Climate fair value = 12-month average futures close x exp(-reaction x supply gap / 100), where the reaction is the measured % change of the marketing-year average futures price per 1% of world supply (OLS on FAOSTAT world supply gaps, 2002 onwards). The model sees weather, not stocks, demand, positioning or news.", ""];
    CROPS.forEach((k) => {
      const c = D.crops[k], la = c.latest, f = c.fair, pi = (D.priceImpact.commodities || {})[k];
      L.push("## " + c.label + " (" + c.priceName + ", " + c.priceUnit + ")");
      L.push("- Risk index: " + sg(la.z) + " on " + dLong(la.date) + ". Weeks above +2 since 2001: " + (c.above2 != null ? c.above2 + "%" : "n/a") + ".");
      const rs = c.riskRecent, i5 = Math.max(0, rs.z.length - 6), i20 = Math.max(0, rs.z.length - 21);
      L.push("- Index 5 working days ago: " + sg(rs.z[i5]) + "; 20 working days ago: " + sg(rs.z[i20]) + ".");
      L.push("- Expected world supply vs normal: " + pct(la.dp, 2) + " (model range " + pct(la.lo) + " to " + pct(la.hi) + ", a deliberately wide worst-case range).");
      L.push("- Countries driving it (points of world supply): " + la.contributors.map((x) => x.name + " " + sg(x.contrib_pct) + " (" + x.season + " harvest " + pct(x.pred_anom_pct) + " vs normal, " + Math.round(x.share_pct) + "% of world output" + (x.window_open ? ", critical window open" : "") + ")").join("; ") + ".");
      const sh = c.shap[la.contributors[0] && la.contributors[0].country];
      if (sh) L.push("- Weather factors behind the " + (la.contributors[0].name) + " forecast (SHAP, points of " + c.target + "): " + sh.rows.map((r) => r[0] + " " + sg(r[1])).join(", ") + ".");
      if (c.windows.length) L.push("- " + c.mainCountry + " critical windows in the last 64 weeks: " + c.windows.map((w) => w[2] + " " + dLong(w[0]) + " to " + dLong(w[1])).join("; ") + ".");
      L.push("- Last futures close: " + fmtPrice(k, c.lastPrice.close) + " on " + dLong(c.lastPrice.date) + ".");
      const pw = c.pricesWeekly.c, n = pw.length;
      if (n > 53) L.push("- Price change: 4 weeks " + pct(100 * (pw[n - 1] / pw[n - 5] - 1)) + ", 13 weeks " + pct(100 * (pw[n - 1] / pw[n - 14] - 1)) + ", 52 weeks " + pct(100 * (pw[n - 1] / pw[n - 53] - 1)) + ".");
      if (f) {
        const nw = f.now, fx = f.flex;
        L.push("- Climate fair value: " + fmtPrice(k, nw.fair) + " (80% range " + fmtPrice(k, nw.fair_lo) + " to " + fmtPrice(k, nw.fair_hi) + "); 12-month average " + fmtPrice(k, nw.anchor) + "; climate premium " + pct(nw.premium_pct) + "; price vs fair value " + pct(nw.gap_to_fair_pct) + ".");
        L.push("- Measured price reaction: " + (-fx.slope_pct_per_pct).toFixed(2) + "% per 1% of world supply missing (standard error " + fx.se.toFixed(2) + ", p-value " + fx.p_value + ", R2 " + fx.r2 + ", " + fx.n + " marketing years " + fx.years[0] + "-" + fx.years[1] + ")" + (nw.reliable ? "." : ". NOT statistically reliable.") + " Index level that would mean a scenario: supply gap = " + f.mu + " - index x " + f.sigma + " (%).");
        if (f.comove) L.push("- Correlation since 2006: weekly index change vs weekly price change " + f.comove.weekly_changes + " (in critical windows " + f.comove.weekly_changes_in_windows + "); index level vs price change over next 13 weeks " + f.comove.index_vs_next_13_weeks + ".");
      }
      if (pi) L.push("- Implied move of the marketing-year average price: " + pct(pi.implied_pct) + " (" + pct(pi.low_pct) + " to " + pct(pi.high_pct) + ").");
      const note = D.notes.find((x) => x.week === D.asOf && x.commodity === k);
      if (note) L.push("- Today's daily note: " + NOTE_TEXT(note).replace(/\s+/g, " "));
      L.push("");
    });
    const o = D.oni;
    L.push("## Background\n- El Nino index (ONI): " + sg(o.value) + " C, " + o.strength + ", " + o.period + " (published " + dLong(o.available_at) + "). Context only, not in the index.");
    L.push("- Track record: forecast error vs a simple trend " + pct(D.method.eval.pooled.rmse_vs_trend_weighted_pct) + " on harvests " + D.method.eval.test[0] + "-" + D.method.eval.test[1] + "; " + Object.values(D.method.events).map((e) => e.label + ": " + e.verdict).join("; ") + "; trading on the index alone after costs: " + Math.round(100 * D.method.backtest.best_rule_p_corrected) + "% chance the gain is luck (not significant).");
    return L.join("\n");
  }
  const RULES = "You are the HarvestRadar trading assistant, built into a research dashboard on weather risk for maize, arabica coffee and cocoa futures. Help the user think through commodity trades: reading the signals, scenarios, fair value, what is priced in, risks, hedging, position sizing principles and what would invalidate a view.\n\n" +
    "Rules:\n- Every HarvestRadar figure must come from the data snapshot below; quote it with its date. If something is not in it (stocks, positioning, spreads, live news, options), say so plainly instead of inventing it.\n- You may add general market knowledge, flagged as background that may be out of date.\n- Be concrete and brief: short paragraphs or bullet lists, numbers with units. A trade idea states direction, instrument, entry logic, invalidation level, main risks and what to watch next.\n- Frame trade ideas as scenarios for discussion. Add one short line that this is not personalised investment advice when you give one.\n- The index is a supply signal with weak short-term correlation to prices: never present it as a price forecast.\n- No em dashes. Reply in the language the user writes in.\n\n";

  function md(src) {
    const inline = (t) => esc(t).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>").replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<i>$2</i>");
    const lines = src.replace(/\s*\u2014\s*/g, ", ").replace(/\r/g, "").split("\n"), out = [];
    let list = null, para = [];
    const flush = () => { if (para.length) { out.push("<p>" + para.map(inline).join("<br>") + "</p>"); para = []; } if (list) { out.push("</" + list + ">"); list = null; } };
    for (let i = 0; i < lines.length; i++) {
      const ln = lines[i];
      if (/^\s*\|.*\|\s*$/.test(ln) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
        flush();
        const cells = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((x) => x.trim());
        let t = "<table><thead><tr>" + cells(ln).map((h) => "<th>" + inline(h) + "</th>").join("") + "</tr></thead><tbody>";
        i += 2;
        while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { t += "<tr>" + cells(lines[i]).map((h) => "<td>" + inline(h) + "</td>").join("") + "</tr>"; i++; }
        i--; out.push(t + "</tbody></table>"); continue;
      }
      let m;
      if ((m = /^\s*#{1,6}\s+(.*)$/.exec(ln))) { flush(); out.push("<h4>" + inline(m[1]) + "</h4>"); }
      else if ((m = /^\s*[-*•]\s+(.*)$/.exec(ln))) { if (para.length) { const l = list; list = null; flush(); list = l; } if (list !== "ul") { if (list) out.push("</" + list + ">"); out.push("<ul>"); list = "ul"; } out.push("<li>" + inline(m[1]) + "</li>"); }
      else if ((m = /^\s*\d+[.)]\s+(.*)$/.exec(ln))) { if (para.length) { const l = list; list = null; flush(); list = l; } if (list !== "ol") { if (list) out.push("</" + list + ">"); out.push("<ol>"); list = "ol"; } out.push("<li>" + inline(m[1]) + "</li>"); }
      else if (!ln.trim()) flush();
      else { if (list) { out.push("</" + list + ">"); list = null; } para.push(ln); }
    }
    flush();
    return out.join("");
  }

  /* What the viewer is looking at: added to every question, so Claude answers about this page. */
  function viewContext() {
    const v = current(), k = S.crop, c = D.crops[k], L = ["## What the user is looking at now", "- Page: " + VIEWS[v] + (v === "ask" || v === "method" ? "" : ", crop: " + c.label) + "."];
    if (v === "commodity") {
      const cs = c.latest.contributors.map((x) => x.country).filter((iso) => c.shap[iso]), sel = S.shap[k] && cs.includes(S.shap[k]) ? S.shap[k] : cs[0], sh = c.shap[sel];
      L.push("- On screen: the " + c.label + " risk index (" + sg(c.latest.z) + "), expected world supply (" + pct(c.latest.dp, 2) + "), the last close (" + fmtPrice(k, c.lastPrice.close) + "), the index against the price over 64 weeks, what it means for the price, the countries behind the reading and the weather factors" + (sh ? " for " + ((c.latest.contributors.find((x) => x.country === sel) || {}).name || sel) + " (" + sh.rows.map((r) => r[0] + " " + sg(r[1])).join(", ") + ")" : "") + ".");
    } else if (v === "fair" && c.fair) {
      const st = S.calc[k] || calcDefaults(k), r = calcResult(k, st);
      L.push("- On screen: " + c.label + " futures price vs climate fair value (" + (S.range === "long" ? "since 2006" : "last 2 years") + ").");
      L.push("- Pricing tool scenario set by the user: " + (st.scen === "today" ? "today's values" : st.scen != null ? "risk index " + sg(+st.scen, 0) : "custom") + "; expected world supply " + pct(st.gap, 2) + " (same as a risk index of " + sg(r.z) + "), price reaction " + st.r.toFixed(2) + "% per 1% missing, anchor " + fmtPrice(k, st.anchor) + " -> fair value " + fmtPrice(k, r.fair) + " (80% range " + fmtPrice(k, r.lo) + " to " + fmtPrice(k, r.hi) + "); last close is " + gapWords(r.vs) + ".");
    } else if (v === "stress") {
      L.push("- On screen: the " + c.label + " stress map for the 10 days to " + dLong(c.map.dekad) + ". Most stressed regions weighted by output: " + c.map.top5.map((r) => r.name + " (" + r.iso + ")").join(", ") + ".");
    } else if (v === "replay") {
      const e = D.episodes[S.episode], pi = (D.priceImpact.episodes || {})[S.episode];
      L.push("- On screen: the replay of " + e.label + ": " + (e.first_above_2 ? "index first above +2 on " + dLong(e.first_above_2) + " (" + ({ caught: "before", late: "after" }[e.verdict] || "") + " the price peak)" : "index never above +2, highest " + sg(e.peak_risk_z)) + "; futures " + pct(e.price_change_pct) + " from " + dLong(e.price_from_date) + " to " + dLong(e.price_to_date) + (pi && pi.reliable ? "; move expected from the supply gap " + pct(pi.implied_pct) : "") + ".");
    } else if (v === "note") {
      const n = D.notes.find((x) => x.week + "|" + x.commodity === S.note) || D.notes[0];
      L.push("- On screen: the daily note of " + dLong(n.week) + " on " + D.crops[n.commodity].label + ": " + NOTE_TEXT(n).replace(/\s+/g, " "));
    }
    return L.join("\n");
  }

  function suggestions() {
    const v = current(), c = D.crops[S.crop], lab = c.label.toLowerCase(), e = D.episodes[S.episode];
    return ({
      commodity: ["What drives the " + lab + " risk index today, and how much does it matter for the price?", "Build a " + lab + " trade idea from this page: direction, entry logic, invalidation and risks.", "Which country or weather factor could change the " + lab + " reading most in the coming weeks?"],
      fair: ["Is " + lab + " cheap or expensive against its climate fair value, and what could close the gap?", "Explain the scenario I set in the pricing tool and what would have to happen for it to play out.", "How reliable is this fair value, and how should I use it in a trade?"],
      stress: ["Which regions matter most for " + lab + " right now, and why?", "Is the stress on this map already in the " + lab + " price?", "What weather should I watch next for " + lab + "?"],
      replay: ["What can a trader learn from " + e.label + "?", "Would trading on the index have worked in " + e.label + "?", "Why did the price move more or less than the supply gap suggests?"],
      note: ["Summarise this note for a trader in three bullet points.", "What should I watch tomorrow for " + lab + "?", "Does this note change the trade idea on " + lab + "?"],
      method: ["How much should I trust this model, given its track record?", "What are the main weaknesses of this approach?", "How should I combine this index with other information in a trade?"],
    })[v] || ["Summarise today's signals across the three crops for a trader.", "Is maize cheap or expensive against its climate fair value, and what could close the gap?",
      "Build a cocoa trade idea from today's data: direction, entry logic, invalidation and risks.", "What would make the maize index wrong this month?", "How should I size a weather trade given this level of uncertainty?"];
  }
  const ctxLabel = () => { const v = current(); return v === "ask" || v === "method" ? "all three crops" : VIEWS[v] + " · " + D.crops[S.crop].label; };
  const ERR = { not_granted: "Access to Claude was not allowed for this page. Reload the page to be asked again.", sampling_disabled: "Claude is not available for this account.", rate_limited: "Too many questions at once, or your Claude usage limit is reached. Try again later.",
    session_expired: "Your Claude session has expired. Sign in again, then retry.", refused: "Claude declined this request. Try rephrasing it.", empty_completion: "No answer came back. Try a shorter question.", prompt_too_large: "The conversation is too long. Clear it and ask again.",
    capability_disabled: "Claude is not available in this view.", not_declared: "This page is not allowed to use Claude.", capability_removed: "Claude is not available in this view." };

  /* One chat widget, moved between the Ask Claude page and the side panel, so the conversation follows the viewer. */
  let chatEl = null;
  function chatWidget() {
    if (chatEl) return chatEl;
    chatEl = document.createElement("div");
    chatEl.className = "chat-widget";
    chatEl.innerHTML = '<div class="warnbox" id="ask-off" hidden style="margin-bottom:12px">The assistant works when this page is opened inside Claude (claude.ai or the Claude app) while you are signed in. It then runs on your own Claude plan: no API key and nothing to pay on top.</div>' +
      '<div class="chat-log" id="chat-log" aria-live="polite"></div><div class="chips" id="ask-suggest" style="margin-top:10px"></div>' +
      '<div class="ctx-line" id="ask-ctx"></div>' +
      '<form class="composer" id="ask-form"><textarea id="ask-input" rows="2" placeholder="Ask about this page..." aria-label="Your question"></textarea><button class="btn primary" id="ask-send" type="submit">Send</button><button class="btn" id="ask-stop" type="button" hidden>Stop</button></form>' +
      '<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-top:10px"><span class="source" style="margin:0">Claude can be wrong. Research and education, not investment advice.</span><button class="btn sm" id="ask-clear" type="button">Clear conversation</button></div>';
    chatEl.querySelector("#ask-form").addEventListener("submit", (e) => { e.preventDefault(); askSend(chatEl.querySelector("#ask-input").value); });
    chatEl.querySelector("#ask-input").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); askSend(e.target.value); } });
    chatEl.querySelector("#ask-stop").addEventListener("click", () => { if (S.chat.ctl) S.chat.ctl.abort(); });
    chatEl.querySelector("#ask-clear").addEventListener("click", () => { if (S.chat.ctl) S.chat.ctl.abort(); S.chat.turns = []; S.chat.error = ""; askRefresh(); });
    return chatEl;
  }

  function askRefresh() {
    const log = document.getElementById("chat-log");
    if (!log) return;
    const C = S.chat;
    let h = C.turns.length ? "" : '<div class="msg bot"><p>Ask anything about what you see: what it means for prices, trade ideas, scenarios or risks. Claude reads this page (' + esc(ctxLabel()) + "), the HarvestRadar data of " + dLong(D.asOf) + " and your conversation, nothing else.</p></div>";
    C.turns.forEach((t, i) => { h += t.role === "user" ? '<div class="msg user">' + esc(t.content) + (t.where ? '<div class="meta">' + esc(t.where) + "</div>" : "") + "</div>" : '<div class="msg bot" data-i="' + i + '">' + md(t.content) + (t.meta ? '<div class="meta">' + esc(t.meta) + "</div>" : "") + "</div>"; });
    if (C.busy && (!C.turns.length || C.turns[C.turns.length - 1].role === "user")) h += '<div class="msg bot" id="live"><span class="thinking">Thinking...</span></div>';
    if (C.error) h += '<div class="warnbox">' + esc(C.error) + "</div>";
    log.innerHTML = h;
    log.scrollTop = log.scrollHeight;
    const ok = ASK.state === "ready", badgeHtml = ok ? tag("Connected to Claude", "good") : ASK.state === "connecting" ? tag("Connecting", "neutral") : tag("Not available here", "bad");
    document.querySelectorAll(".ask-state").forEach((e) => { e.innerHTML = badgeHtml; });
    const off = document.getElementById("ask-off"); if (off) off.hidden = ok || ASK.state === "connecting";
    ["ask-send", "ask-input"].forEach((id) => { const e = document.getElementById(id); if (e) e.disabled = !ok || C.busy; });
    const stop = document.getElementById("ask-stop"); if (stop) stop.hidden = !C.busy;
    const sug = document.getElementById("ask-suggest");
    if (sug) { sug.hidden = C.turns.length > 0; sug.innerHTML = suggestions().map((q) => '<button class="chip" data-ask="' + esc(q) + '">' + esc(q) + "</button>").join(""); }
    const cx = document.getElementById("ask-ctx"); if (cx) cx.textContent = "Claude sees: " + ctxLabel() + ", data of " + dLong(D.asOf);
    const dl = document.getElementById("drawer-ctx"); if (dl) dl.textContent = ctxLabel();
    document.querySelectorAll("[data-ask],[data-askopen]").forEach((b) => { b.disabled = !ok || C.busy; });
  }

  async function askSend(text) {
    const C = S.chat;
    text = (text || "").trim();
    if (!text || C.busy || !ASK.fn) return;
    C.error = ""; C.turns.push({ role: "user", content: text, where: ctxLabel() }); C.busy = true;
    const inp = document.getElementById("ask-input"); if (inp) inp.value = "";
    askRefresh();
    const history = C.turns.slice(-12).map((t) => ({ role: t.role, content: t.content }));
    while (history.length && history[0].role !== "user") history.shift();
    history[history.length - 1].content = "[Asked while viewing: " + ctxLabel() + "]\n" + text;
    const input = [{ role: "user", content: RULES + claudeContext() + "\n\n" + viewContext() }].concat(history);
    const ctl = new AbortController(); C.ctl = ctl;
    let slot = null;
    try {
      const res = await ASK.fn(input, { cache: false, signal: ctl.signal, onText: ({ text: t }) => {
        if (!slot) { slot = { role: "assistant", content: "" }; C.turns.push(slot); }
        slot.content = t;
        const live = document.querySelector("#chat-log .msg.bot:last-of-type"), log = document.getElementById("chat-log");
        if (live && live.dataset.i == C.turns.length - 1) { live.innerHTML = md(t); if (log) log.scrollTop = log.scrollHeight; } else askRefresh();
      } });
      if (!slot) { slot = { role: "assistant", content: res.text }; C.turns.push(slot); }
      slot.content = res.text;
      if (res.truncated) slot.meta = "Answer cut short. Ask for less at a time.";
    } catch (e) {
      const code = e && e.code;
      if (slot && e && e.text) { slot.content = e.text; slot.meta = code === "cancelled" ? "Stopped." : "Interrupted."; }
      else if (slot && (!e || !e.text)) { C.turns.pop(); }
      if (code !== "cancelled") C.error = ERR[code] || "Connection problem. Try again.";
      if (code === "not_granted" || code === "sampling_disabled" || code === "not_declared" || code === "capability_disabled" || code === "capability_removed") ASK.state = "absent";
    } finally { C.busy = false; C.ctl = null; askRefresh(); }
  }

  /* Side panel available on every page; the floating button opens it with the page as context. */
  function drawerShell() {
    if (document.getElementById("drawer")) return;
    const fab = document.createElement("button");
    fab.id = "fab"; fab.className = "fab"; fab.type = "button"; fab.setAttribute("aria-controls", "drawer");
    fab.innerHTML = '<span class="dot"></span>Ask Claude';
    const dr = document.createElement("aside");
    dr.id = "drawer"; dr.className = "drawer"; dr.setAttribute("aria-label", "Ask Claude"); dr.hidden = true;
    dr.innerHTML = '<div class="drawer-head"><div style="min-width:0"><div style="font-family:var(--display);font-weight:700;font-size:20px">Ask Claude</div><div class="mono" id="drawer-ctx" style="font-size:13px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis"></div></div><span class="ask-state"></span><button class="btn sm" id="drawer-close" type="button" aria-label="Close the assistant">Close</button></div><div class="drawer-body"></div>';
    document.body.appendChild(fab); document.body.appendChild(dr);
    fab.addEventListener("click", () => openDrawer());
    dr.querySelector("#drawer-close").addEventListener("click", closeDrawer);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && S.drawer) closeDrawer(); });
  }
  function openDrawer(q) {
    connectClaude(); drawerShell();
    S.drawer = true;
    document.body.classList.add("drawer-open");
    const dr = document.getElementById("drawer");
    dr.querySelector(".drawer-body").appendChild(chatWidget());
    dr.hidden = false; requestAnimationFrame(() => dr.classList.add("open"));
    document.getElementById("fab").hidden = true;
    askRefresh();
    if (q && ASK.state === "connecting") S.queued = q;
    else if (q) askSend(q);
    else { const i = document.getElementById("ask-input"); if (i && !i.disabled) i.focus(); }
  }
  function closeDrawer() {
    S.drawer = false;
    document.body.classList.remove("drawer-open");
    const dr = document.getElementById("drawer");
    if (dr) { dr.classList.remove("open"); setTimeout(() => { if (!S.drawer) dr.hidden = true; }, 220); }
    const f = document.getElementById("fab"); if (f) f.hidden = current() === "ask";
  }
  function placeChat(v) {
    drawerShell();
    const fab = document.getElementById("fab"), dr = document.getElementById("drawer");
    if (v === "ask") {
      S.drawer = false; document.body.classList.remove("drawer-open"); dr.classList.remove("open"); dr.hidden = true; fab.hidden = true;
      document.getElementById("ask-slot").appendChild(chatWidget());
    } else {
      fab.hidden = !!S.drawer;
      if (S.drawer) dr.querySelector(".drawer-body").appendChild(chatWidget());
    }
    askRefresh();
  }
  function askPanel(k) {
    const c = D.crops[k], qs = suggestions();
    return panel("ASK CLAUDE ABOUT " + esc(c.label.toUpperCase()), '<div style="font-size:15px;color:var(--frost-2);line-height:1.55">Claude reads this page and today\'s data, then answers in the side panel.</div><div class="chips" style="margin-top:12px">' +
      qs.map((q) => '<button class="chip" data-askopen="' + esc(q) + '">' + esc(q) + "</button>").join("") + '<button class="chip" data-askopen="">Ask your own question</button></div>', "Runs on your Claude plan when this page is opened in Claude. Not investment advice.");
  }

  function viewAsk() {
    connectClaude();
    const seen = CROPS.map((k) => { const c = D.crops[k], f = c.fair; return '<div style="display:grid;grid-template-columns:26px minmax(0,1fr);gap:10px;align-items:start;padding:10px 0;border-top:1px solid var(--line)">' + glyph(c.glyph, 22) + '<div style="min-width:0"><div style="font-weight:600">' + esc(c.label) + '</div><div class="mono" style="font-size:14px;color:var(--frost-2);line-height:1.6">Risk index ' + sg(c.latest.z) + ", supply " + pct(c.latest.dp, 2) + "<br>Price " + fmtPrice(k, c.lastPrice.close) + (f ? ", fair value " + fmtPrice(k, f.now.fair) : "") + "</div></div></div>"; }).join("");
    const html = '<div class="main c65"><div class="col"><section class="glass" style="padding:18px 20px"><div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:12px"><span style="font-family:var(--display);font-weight:700;font-size:24px">Ask Claude about today\'s signals</span><span class="ask-state"></span></div><div id="ask-slot"></div></section></div>' +
      '<div class="col">' + panel("WHAT CLAUDE SEES", '<div style="font-size:15px;color:var(--frost-2);line-height:1.55;margin-bottom:6px">With each question, the page sends Claude this data snapshot (' + dLong(D.asOf) + "), the page you are on and your conversation:</div>" + seen +
        '<div style="font-size:14px;color:var(--muted);line-height:1.55;border-top:1px solid var(--line);padding-top:10px">Plus the countries and weather factors behind each reading, price changes, the measured price reaction, today\'s daily notes, El Ni&ntilde;o and the track record. No live news, stocks or positioning.</div>') +
      panel("HOW IT WORKS", '<div style="font-size:15px;color:var(--frost-2);line-height:1.65">The "Ask Claude" button on every page opens the same conversation in a side panel, with that page as context. Inside Claude, answers run on your own Claude plan, so the page needs no API key. The first question asks you to allow it. The page keeps the conversation only while it is open.</div>') + "</div></div>";
    return { html: html, after: null };
  }

  const RENDER = { stress: viewStress, commodity: viewCommodity, fair: viewFair, replay: viewReplay, note: viewNote, method: viewMethod, ask: viewAsk };
  function current() { const v = location.hash.slice(1); return RENDER[v] ? v : "stress"; }
  function render() {
    const v = current();
    const changed = v !== S.view;
    if (changed) { if (S.view) S.scroll[S.view] = window.scrollY; S.prev = S.view; S.view = v; }
    if (mapHandle && mapHandle.stop) { mapHandle.stop(); mapHandle = null; }
    document.getElementById("tabs").innerHTML = Object.entries(VIEWS).map(([k, l]) => '<a class="tab' + (k === v ? " on" : "") + '" href="#' + k + '"' + (k === v ? ' aria-current="page"' : "") + ">" + l + "</a>").join("");
    const out = RENDER[v]();
    document.getElementById("view").innerHTML = out.html;
    if (out.after) out.after();
    placeChat(v);
    if (changed) {
      const tgt = S.goto && document.getElementById(S.goto);
      if (tgt) tgt.scrollIntoView({ block: "start" });
      else window.scrollTo(0, S.restore ? S.scroll[v] || 0 : 0);
      S.goto = null; S.restore = false;
    }
    if (window.innerWidth < 700) { const on = document.querySelector(".tab.on"), tb = document.getElementById("tabs"); if (on && tb) tb.scrollLeft = on.offsetLeft - (tb.clientWidth - on.offsetWidth) / 2; }
  }

  connectClaude();
  document.getElementById("brand").innerHTML = D.marks.small + "<span>Harvest<b>Radar</b></span>";
  document.getElementById("status").textContent = "DATA AS OF " + D.weekLabel;
  document.addEventListener("click", (e) => {
    const nav = e.target.closest("a[data-goto],a[data-back]");
    if (nav) { if (nav.dataset.goto) S.goto = nav.dataset.goto; if (nav.dataset.back) S.restore = true; }
    const t = e.target.closest("[data-crop],[data-shap],[data-episode],[data-note],#email-btn,[data-crop-link],[data-range],[data-scen],#calc-reset,#calc-undo,[data-ask],[data-askopen]");
    if (!t) return;
    if (t.dataset.ask) { askSend(t.dataset.ask); return; }
    if (t.dataset.askopen !== undefined) { openDrawer(t.dataset.askopen || null); return; }
    if (t.dataset.range) { S.range = t.dataset.range; render(); return; }
    if (t.dataset.scen) {
      const k = S.crop, f = D.crops[k].fair, st = S.calc[k] || (S.calc[k] = calcDefaults(k));
      if (st.scen === t.dataset.scen) return;
      calcPush(k, snap(st));
      if (t.dataset.scen === "today") Object.assign(st, calcDefaults(k));
      else { st.gap = f.mu - +t.dataset.scen * f.sigma; st.scen = t.dataset.scen; }
      calcSync(); return;
    }
    if (t.id === "calc-reset") { const k = S.crop; calcPush(k, snap(S.calc[k])); S.calc[k] = calcDefaults(k); calcSync(); return; }
    if (t.id === "calc-undo") { const k = S.crop, h = S.hist[k] || []; if (h.length) { S.calc[k] = h.pop(); calcSync(); } return; }
    if (t.dataset.crop) { S.crop = t.dataset.crop; render(); }
    else if (t.dataset.shap) { S.shap[S.crop] = t.dataset.shap; render(); }
    else if (t.dataset.episode) { S.episode = t.dataset.episode; render(); }
    else if (t.dataset.note) { S.note = t.dataset.note; render(); }
    else if (t.id === "email-btn") { S.email = !S.email; render(); }
    else if (t.dataset.cropLink) { S.crop = t.dataset.cropLink; }
  });
  document.addEventListener("input", (e) => {
    const id = e.target.id, st = S.calc[S.crop];
    if (!st || !["i-gap", "i-r", "i-anchor"].includes(id)) return;
    const v = parseFloat(e.target.value);
    if (!isFinite(v)) return;
    if (!S.pending) S.pending = snap(st);
    if (id === "i-gap") { st.gap = v; st.scen = null; } else if (id === "i-r") st.r = v; else if (v > 0) st.anchor = v;
    calcUpdate();
  });
  document.addEventListener("change", (e) => {
    if (!["i-gap", "i-r", "i-anchor"].includes(e.target.id) || !S.pending) return;
    calcPush(S.crop, S.pending); S.pending = null; calcUpdate();
  });
  window.addEventListener("hashchange", render);
  let rw = window.innerWidth;
  window.addEventListener("resize", () => { if ((rw < 700) !== (window.innerWidth < 700)) { rw = window.innerWidth; render(); } });
  render();
})();
