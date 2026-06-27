/* Antiques Inference Engine — single-page UI logic. Vanilla JS, fully offline.
   Renders the field-guide page + the purple "Can it Run AI?" panel + the
   "open the potato ledger" trace from runs/<case>/ artifacts — and lets the
   visitor UPLOAD a photo to watch the live pipeline (Claude + granite) run. */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
let CASES = [];        // last /cases payload
let CURRENT = null;    // currently-open case id
let BUSY = false;      // a live upload is in flight — lock the rail

/* ── humanize seconds → the verdict number + unit (the demo arc punchline) ── */
function humanize(seconds, canEval) {
  if (canEval === false || seconds == null || seconds < 0) {
    return { big: "Never", unit: "it never finishes a single token", never: true };
  }
  const YR = 31557600, DAY = 86400, HR = 3600, MIN = 60;
  let val, unit;
  if (seconds >= YR) { val = seconds / YR; unit = "years to generate ONE AI token"; }
  else if (seconds >= DAY) { val = seconds / DAY; unit = "days to generate ONE AI token"; }
  else if (seconds >= HR) { val = seconds / HR; unit = "hours to generate ONE AI token"; }
  else if (seconds >= MIN) { val = seconds / MIN; unit = "minutes to generate ONE AI token"; }
  else { val = seconds; unit = "seconds to generate ONE AI token"; }
  const rounded = val >= 1000 ? Math.round(val).toLocaleString() : (Math.round(val * 100) / 100);
  return { big: String(rounded), unit, never: false };
}

/* the headline verdict — power/absurd_power artifacts have no compute time, so
   render their watts (and how many AI-hellos that's worth) instead of "0 seconds" */
function verdict(m) {
  if ((m.mode === "power" || m.mode === "absurd_power") && m.can_evaluate && m.input_value > 0) {
    const w = m.input_value;
    const mult = m.units_for_ai_hello > 0 ? Math.round(1 / m.units_for_ai_hello) : 0;
    return {
      big: w >= 1000 ? Math.round(w).toLocaleString() : (Math.round(w * 100) / 100),
      unit: mult > 0 ? `watts — ~${mult.toLocaleString()}× one AI hello's appetite` : "watts available",
      never: false,
    };
  }
  return humanize(m.time_seconds, m.can_evaluate);
}

function fmtNum(n) {
  if (n == null) return "—";
  if (n === -1) return "∞";
  return Math.abs(n) >= 1000 ? Math.round(n).toLocaleString() : (Math.round(n * 1000) / 1000);
}

/* ── tiny offline markdown → HTML for the article (no CDN). Handles the subset
      the writer template uses: headings, **bold**, *italic*, `code`, > quote,
      tables, fenced ``` blocks, - lists, hr, paragraphs. HTML-escaped first. ── */
function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function inline(s) {
  return esc(s)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}
function mdToHtml(md) {
  const lines = (md || "").replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let i = 0;
  while (i < lines.length) {
    let line = lines[i];

    if (line.trim().startsWith("```")) {            // fenced code
      const buf = []; i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) { buf.push(esc(lines[i])); i++; }
      i++; out.push("<pre><code>" + buf.join("\n") + "</code></pre>"); continue;
    }
    if (/^\s*\|.*\|\s*$/.test(line)) {              // table
      const rows = [];
      while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { rows.push(lines[i]); i++; }
      const cells = r => r.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
      let html = "<table>";
      rows.forEach((r, idx) => {
        if (idx === 1 && /^[\s|:-]+$/.test(r)) return; // separator row
        const tag = idx === 0 ? "th" : "td";
        html += "<tr>" + cells(r).map(c => `<${tag}>${inline(c)}</${tag}>`).join("") + "</tr>";
      });
      out.push(html + "</table>"); continue;
    }
    if (/^\s*-\s+/.test(line)) {                    // unordered list
      const items = [];
      while (i < lines.length && /^\s*-\s+/.test(lines[i])) { items.push(lines[i].replace(/^\s*-\s+/, "")); i++; }
      out.push("<ul>" + items.map(it => `<li>${inline(it)}</li>`).join("") + "</ul>"); continue;
    }
    if (/^#{1,3}\s/.test(line)) {                   // headings
      const level = line.match(/^#+/)[0].length;
      out.push(`<h${level}>${inline(line.replace(/^#+\s/, ""))}</h${level}>`); i++; continue;
    }
    if (/^\s*>\s?/.test(line)) {                    // blockquote
      out.push(`<blockquote>${inline(line.replace(/^\s*>\s?/, ""))}</blockquote>`); i++; continue;
    }
    if (/^\s*---\s*$/.test(line)) { out.push("<hr>"); i++; continue; }
    if (line.trim() === "") { i++; continue; }
    out.push(`<p>${inline(line)}</p>`); i++;        // paragraph
  }
  return out.join("\n");
}

/* ── render the verdict panel from math.json ── */
function verdictCard(math, obs) {
  const h = verdict(math);
  const stats = [];
  if (math.input_value != null) stats.push(["input", `${fmtNum(math.input_value)} ${math.input_unit || ""}`.trim()]);
  if (math.units_for_ai_hello && math.units_for_ai_hello > 0) stats.push(["units for AI hello", fmtNum(math.units_for_ai_hello)]);
  if (math.potatoes_equivalent && math.potatoes_equivalent > 0) stats.push(["🥔 potatoes", fmtNum(math.potatoes_equivalent)]);
  if (math.cyclists_equivalent && math.cyclists_equivalent > 0) stats.push(["🚴 cyclists", fmtNum(math.cyclists_equivalent)]);
  const statHtml = stats.map(([k, v]) => `<div class="stat"><span class="k">${esc(k)}</span><span class="v">${esc(String(v))}</span></div>`).join("");
  return `
    <div class="verdict-card${h.never ? " never" : ""}">
      <p class="q">Can it Run AI?</p>
      <p class="answer">${esc(h.big)}<span class="unit">${esc(h.unit)}</span></p>
      ${statHtml ? `<div class="stat-grid">${statHtml}</div>` : ""}
    </div>`;
}

/* ── honest receipts: surface latency/tokens/cost/skills on a step if present.
      Field-name-agnostic so it renders whatever the --live wiring writes.
      FLOOR steps have none → nothing shows (honest: deterministic, no model). ── */
function receiptChips(s) {
  const out = [];
  for (const [k, v] of Object.entries(s)) {
    if (/(latency|token|cost|duration|elapsed|_ms$|_s$)/i.test(k) && (typeof v === "number" || typeof v === "string")) {
      let val = v;
      if (typeof v === "number" && /latency|duration|elapsed/i.test(k)) val = /ms/i.test(k) ? `${v} ms` : `${v} s`;
      out.push(`<span class="rcpt">${esc(k.replace(/_/g, " "))}: ${esc(String(val))}</span>`);
    }
  }
  if (Array.isArray(s.skills) && s.skills.length) out.push(`<span class="rcpt">skills: ${s.skills.length}</span>`);
  return out.length ? `<span class="rcpts">${out.join("")}</span>` : "";
}

/* ── agent display name: drop underscores, Title Case (artifact_goblin → Artifact Goblin) ── */
function prettyAgent(name) {
  return String(name).replace(/_/g, " ").replace(/\b([a-z])/g, (_, c) => c.toUpperCase());
}

/* ── render the trace ledger from trace.json ── */
function ledger(trace) {
  const steps = (trace && trace.steps) || [];
  const rows = steps.map(s => {
    const detail = s.guess || s.family || s.reason || (s.route_to ? `→ ${s.route_to}` : "") || "";
    const model = s.model || "—";
    const cls = (model === "deterministic" || model === "fixture") ? " deterministic" : "";
    const passBit = ("pass" in s) ? (s.pass ? " ✓ pass" : " ✗ fail") : "";
    return `<div class="step"><span class="agent">${esc(prettyAgent(s.agent || ""))}</span>
      <span class="detail">${esc(detail)}${passBit}${receiptChips(s)}</span>
      <span class="model${cls}">${esc(model)}</span></div>`;
  }).join("");
  const loops = (trace && trace.loops != null) ? trace.loops : "?";
  return `
    <details class="ledger">
      <summary>🥔 Open the potato ledger <span class="pill">${steps.length} agents · ${loops} loop(s)</span><span class="chev">▸</span></summary>
      <div class="ledger-body">${rows || "<p>No trace recorded.</p>"}</div>
    </details>`;
}

/* ── render the whole page for one case ── */
function renderPage(data, scroll = true) {
  const obs = data.observation || {};
  const conf = obs.confidence != null ? ` · confidence ${Math.round(obs.confidence * 100)}%` : "";
  const path = (data.math && data.math.path) || obs.power_or_compute_path || "";
  const shot = data.has_image ? `<img class="shot" src="/image/${encodeURIComponent(data.case)}?t=${Date.now()}" alt="${esc(data.display)}">` : "";
  $("#page").innerHTML = `
    <div class="page-head">
      ${shot}
      <div class="meta">
        <h2>${esc(data.display)}</h2>
        <div class="tags">
          ${path ? `<span class="tag path">${esc(path)}</span>` : ""}
          ${obs.artifact_guess ? `<span class="tag">${esc(obs.artifact_guess)}</span>` : ""}
          ${conf ? `<span class="tag">${esc(conf.replace(" · ", ""))}</span>` : ""}
        </div>
      </div>
    </div>
    ${verdictCard(data.math || {}, obs)}
    <div class="article">${mdToHtml(data.article_md)}</div>
    ${ledger(data.trace || {})}`;
  if (scroll) $("#page").scrollIntoView({ block: "nearest" });
}

/* ── the live-compute loader: a scanning instrument while the agents actually run ── */
const LIVE_STEPS = [
  ["01", "artifact_goblin", "Claude opens its eyes on your photo…"],
  ["02", "sherlock_ohms", "granite4:micro researches the mechanism…"],
  ["03", "potato_accountant", "Python computes the physics (frozen, deterministic)…"],
  ["04", "reality_badger", "granite audits the units — can it be bullied into AI?"],
  ["05", "page_goblin", "Claude writes the verdict over the frozen math…"],
];
let LOADER_TIMER = null, ELAPSED_TIMER = null, QUIP_TIMER = null;

/* ── absurd-but-on-brand status quips, rotated while the agents actually run ── */
const LIVE_QUIPS = [
  "Bullying a calculator into sentience…",
  "Converting hubris into watts…",
  "Asking the potato nicely…",
  "Carrying the 1. Carrying it a very long way…",
  "Negotiating with thermodynamics…",
  "Checking whether “powers AI” counts as “runs AI”…",
  "Counting the electrons by hand…",
  "Weighing the verdict against a sack of potatoes…",
];
function renderLoading(name) {
  const steps = LIVE_STEPS.map(([n, agent, detail]) =>
    `<li data-step="${n}"><span class="mark">${n}</span><span class="ll-line"><b>${esc(prettyAgent(agent))}</b> — ${esc(detail)}</span></li>`).join("");
  $("#page").innerHTML = `
    <div class="live-loader">
      <div class="ll-bar"></div>
      <div class="ll-body">
        <p class="ll-head">Our AI Potato-Power Experts are analyzing your antique… <span id="ll-elapsed" style="font-family:var(--mono);font-size:.82rem;font-weight:400;color:var(--ink-soft)">0s</span></p>
        <p class="ll-sub">Looking at <strong>${esc(name)}</strong>. Real models, real receipts — typically ~60–90 seconds. The math stays deterministic.</p>
        <p class="ll-quip" id="ll-quip">${esc(LIVE_QUIPS[0])}</p>
        <ul class="ll-steps">${steps}</ul>
      </div>
    </div>`;
  const items = [...document.querySelectorAll(".ll-steps li")];
  let idx = 0;
  const advance = () => {
    items.forEach((li, k) => {
      li.classList.toggle("done", k < idx);
      li.classList.toggle("active", k === idx);
    });
    if (idx < items.length - 1) idx++;   // hold on the last step until the real result lands
  };
  advance();
  LOADER_TIMER = setInterval(advance, 14000);  // ~14s/step ≈ the real cadence; the last step waits
  // The one number that's ALWAYS honest regardless of step pacing: real wall-clock.
  let secs = 0;
  const el = $("#ll-elapsed");
  ELAPSED_TIMER = setInterval(() => { secs += 1; if (el) el.textContent = `${secs}s`; }, 1000);
  // rotate the absurd quips: fade out, swap, fade in
  let q = 0;
  const quipEl = $("#ll-quip");
  QUIP_TIMER = setInterval(() => {
    q = (q + 1) % LIVE_QUIPS.length;
    if (!quipEl) return;
    quipEl.style.opacity = "0";
    setTimeout(() => { quipEl.textContent = LIVE_QUIPS[q]; quipEl.style.opacity = "1"; }, 220);
  }, 3600);
}
function stopLoading() {
  if (LOADER_TIMER) { clearInterval(LOADER_TIMER); LOADER_TIMER = null; }
  if (ELAPSED_TIMER) { clearInterval(ELAPSED_TIMER); ELAPSED_TIMER = null; }
  if (QUIP_TIMER) { clearInterval(QUIP_TIMER); QUIP_TIMER = null; }
}

/* ── load + render one case ── */
async function loadCase(c, scroll = true) {
  if (BUSY) return;
  CURRENT = c;
  syncActive();
  try {
    const r = await fetch(`/run/${encodeURIComponent(c)}`);
    if (!r.ok) throw new Error(`run ${c}: ${r.status}`);
    renderPage(await r.json(), scroll);
  } catch (e) {
    $("#page").innerHTML = `<div class="article"><p><strong>Could not load ${esc(c)}.</strong> ${esc(e.message)}</p></div>`;
  }
}
function syncActive() {
  document.querySelectorAll(".specimen").forEach(b => b.setAttribute("aria-current", String(b.dataset.case === CURRENT)));
}

/* ── the specimen rail — scales to hundreds without burying the demo ──
   A pinned "Arc" group (the curated demo + live runs, never paged) sits above a
   "Community" group (visitor uploads) that is SEARCHABLE + PAGINATED (20/page),
   with a 🎲 random pick. Split is by `deletable`: curated = pinned, uploads = community. */
const PAGE_SIZE = 20;
let PAGE = 0;        // current community page
let FILTER = "";     // community search text

function specimenRow(c, idx) {
  const v = verdict(c);
  const vtxt = v.never ? "Never · ∞" : `${v.big} ${v.unit.split(" ")[0]}`;
  const num = String(idx).padStart(2, "0");
  const liveCls = c.live ? " is-live" : "";
  const del = c.deletable
    ? `<button class="del" type="button" data-del="${esc(c.case)}" title="Remove this specimen" aria-label="Remove ${esc(c.display)}">✕</button>`
    : "";
  return `<li class="spec-row">
    <button class="specimen${liveCls}" type="button" data-case="${esc(c.case)}" aria-current="${c.case === CURRENT}">
      <span class="idx">${num}</span>
      <span class="lbl"><span class="name">${esc(c.display)}</span><span class="verdict">${esc(vtxt)}</span></span>
    </button>${del}</li>`;
}

const communityCases = () => CASES.filter(c => c.deletable);
function filteredCommunity() {
  const f = FILTER.trim().toLowerCase();
  const all = communityCases();
  return f ? all.filter(c => (c.display || "").toLowerCase().includes(f)) : all;
}

/* re-render ONLY the community list + pager — leaves the search box (and its focus) alone. */
function renderCommunity() {
  const listEl = $("#community-list");
  if (!listEl) return;
  const filtered = filteredCommunity();
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  PAGE = Math.min(Math.max(0, PAGE), pages - 1);
  const start = PAGE * PAGE_SIZE;
  const pageItems = filtered.slice(start, start + PAGE_SIZE);
  listEl.innerHTML = pageItems.length
    ? pageItems.map((c, i) => specimenRow(c, start + i + 1)).join("")
    : `<div class="rail-empty">No specimens match “${esc(FILTER)}”.</div>`;
  const pagerEl = $("#rail-pager");
  if (!pagerEl) return;
  if (filtered.length > PAGE_SIZE) {
    const a = start + 1, b = Math.min(start + PAGE_SIZE, filtered.length);
    pagerEl.innerHTML = `
      <div class="pager-info">showing ${a}–${b} of ${filtered.length}${FILTER.trim() ? " · filtered" : ""}</div>
      <div class="pager-row">
        <button class="pager-btn" type="button" data-page="first" ${PAGE === 0 ? "disabled" : ""} title="First" aria-label="First page">◀</button>
        <button class="pager-btn" type="button" data-page="prev"  ${PAGE === 0 ? "disabled" : ""} title="Previous" aria-label="Previous page">‹</button>
        <span class="pager-cur">${PAGE + 1}/${pages}</span>
        <button class="pager-btn" type="button" data-page="next"  ${PAGE >= pages - 1 ? "disabled" : ""} title="Next" aria-label="Next page">›</button>
        <button class="pager-btn" type="button" data-page="last"  ${PAGE >= pages - 1 ? "disabled" : ""} title="Last" aria-label="Last page">▶</button>
      </div>`;
  } else {
    pagerEl.innerHTML = FILTER.trim() && filtered.length
      ? `<div class="pager-info">${filtered.length} match${filtered.length === 1 ? "" : "es"}</div>` : "";
  }
}

function gotoPage(which) {
  const pages = Math.max(1, Math.ceil(filteredCommunity().length / PAGE_SIZE));
  if (which === "first") PAGE = 0;
  else if (which === "prev") PAGE = Math.max(0, PAGE - 1);
  else if (which === "next") PAGE = Math.min(pages - 1, PAGE + 1);
  else if (which === "last") PAGE = pages - 1;
  renderCommunity();
}

/* make a community case visible: clear the filter, jump to its page. (Arc cases are always shown.) */
function revealCase(caseId) {
  const pos = communityCases().findIndex(c => c.case === caseId);
  if (pos < 0) return;
  FILTER = ""; const s = $("#rail-search"); if (s) s.value = "";
  PAGE = Math.floor(pos / PAGE_SIZE);
  renderCommunity();
}

/* 🎲 — load a random specimen (≠ current); surface its page if it's a community one. */
function surpriseMe() {
  if (!CASES.length) return;
  const pool = CASES.filter(c => c.case !== CURRENT);
  const list = pool.length ? pool : CASES;
  const pick = list[Math.floor(Math.random() * list.length)];
  revealCase(pick.case);
  loadCase(pick.case);
}

/* full rail rebuild — pinned Arc (all) + Community (search + paged). */
function renderRail() {
  const list = $("#case-list");
  $("#case-count").textContent = CASES.length ? `(${CASES.length})` : "";
  const arc = CASES.filter(c => !c.deletable);
  const community = communityCases();
  let html = "";
  if (arc.length) {
    html += `<div class="rail-grp"><span class="rgl">The Arc — the demo</span></div>`;
    html += arc.map((c, i) => specimenRow(c, i + 1)).join("");
  }
  if (community.length) {
    html += `<div class="rail-grp"><span class="rgl">Community <span class="rgc">(${community.length})</span></span>
      <button class="surprise" type="button" data-surprise title="Load a random specimen">🎲 random</button></div>`;
    html += `<div class="rail-search-row"><input id="rail-search" class="rail-search" type="search"
      placeholder="🔍 filter specimens…" value="${esc(FILTER)}" autocomplete="off" aria-label="Filter community specimens"></div>`;
    html += `<div id="community-list"></div><div id="rail-pager"></div>`;
  }
  list.innerHTML = html;
  if (community.length) renderCommunity();
}

/* rail-control styles, injected once — keeps this in main.js's lane (no index.html edit). */
function injectRailCSS() {
  if ($("#rail-css")) return;
  const s = document.createElement("style");
  s.id = "rail-css";
  s.textContent = `
    .rail-grp{display:flex;align-items:center;justify-content:space-between;gap:.5rem;padding:.6rem .15rem .35rem;margin-top:.35rem}
    .rail-grp:first-child{margin-top:0}
    .rgl{font-family:var(--mono);font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft)}
    .rgc{opacity:.65}
    .surprise{font-family:var(--mono);font-size:.64rem;letter-spacing:.05em;text-transform:uppercase;cursor:pointer;
      background:var(--cream-2);border:1px solid var(--border);color:var(--purple-700);padding:.22rem .45rem;transition:background .14s,border-color .14s}
    .surprise:hover{background:var(--purple-100);border-color:var(--lime-500)}
    .rail-search-row{padding:.1rem 0 .55rem}
    .rail-search{width:100%;font:inherit;font-size:.85rem;padding:.45rem .6rem;color:var(--ink);background:var(--paper);border:1px solid var(--border);outline:none}
    .rail-search:focus{border-color:var(--lime-500)}
    .rail-empty{font-size:.82rem;color:var(--ink-soft);padding:.55rem .15rem}
    #rail-pager{display:flex;flex-direction:column;gap:.35rem;padding:.55rem .15rem .2rem}
    .pager-info{font-family:var(--mono);font-size:.66rem;color:var(--ink-soft);text-align:center}
    .pager-row{display:flex;gap:.2rem;justify-content:center;align-items:center}
    .pager-btn{font-family:var(--mono);font-size:.72rem;cursor:pointer;background:var(--paper);border:1px solid var(--border);
      color:var(--ink);padding:.22rem .42rem;min-width:1.9rem;transition:background .14s,color .14s,border-color .14s}
    .pager-btn:hover:not(:disabled){background:var(--purple-700);color:var(--cream);border-color:var(--purple-700)}
    .pager-btn:disabled{opacity:.35;cursor:default}
    .pager-cur{font-family:var(--mono);font-size:.72rem;color:var(--ink-soft);padding:0 .45rem;white-space:nowrap}`;
  document.head.appendChild(s);
}

async function refreshCases() {
  const r = await fetch("/cases");
  CASES = (await r.json()).cases || [];
  renderRail();
}

/* ── upload a photo → run the live pipeline → show the result ── */
async function handleUpload(file) {
  if (!file || BUSY) return;
  const name = file.name || "";
  // iPhone default is HEIC — Claude vision can't read it and most browsers won't
  // render it. Catch it here for instant, actionable feedback (no slow round-trip).
  if (/\.(heic|heif)$/i.test(name) || /image\/(heic|heif)/i.test(file.type)) {
    alert("iPhone HEIC photos can't run live vision yet.\n\nExport/share the photo as JPEG first — or set iPhone → Settings → Camera → Formats → “Most Compatible” — then upload.");
    return;
  }
  if (file.type && !/^image\//.test(file.type)) { alert("Please choose an image file (JPG / PNG)."); return; }
  BUSY = true;
  $("#upload-btn").style.pointerEvents = "none";
  renderLoading(file.name);
  try {
    const r = await fetch(`/upload?filename=${encodeURIComponent(file.name)}`, {
      method: "POST",
      headers: { "Content-Type": file.type || "application/octet-stream" },
      body: file,
    });
    stopLoading();
    if (!r.ok) {
      const msg = await r.text().catch(() => r.status);
      throw new Error(typeof msg === "string" ? msg.slice(0, 300) : `HTTP ${r.status}`);
    }
    const { case: newCase } = await r.json();
    BUSY = false;
    await refreshCases();
    revealCase(newCase);          // surface the new upload's page in the rail
    await loadCase(newCase);
  } catch (e) {
    stopLoading();
    BUSY = false;
    $("#page").innerHTML = `<div class="article"><p><strong>Live run failed.</strong> ${esc(e.message)}</p>
      <p>The deterministic demo still works — pick a curated specimen on the left. (Live needs Ollama running and an Anthropic key in <code>.env</code>.)</p></div>`;
  } finally {
    $("#upload-btn").style.pointerEvents = "";
  }
}

/* ── delete an uploaded specimen ── */
async function handleDelete(caseId) {
  if (BUSY) return;
  const c = CASES.find(x => x.case === caseId);
  if (!confirm(`Remove “${c ? c.display : caseId}” and its run?`)) return;
  try {
    const r = await fetch(`/case/${encodeURIComponent(caseId)}`, { method: "DELETE" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    await refreshCases();
    if (CURRENT === caseId) {
      if (CASES.length) await loadCase(CASES[0].case);
      else $("#page").innerHTML = "";
    } else {
      syncActive();
    }
  } catch (e) {
    alert(`Could not delete: ${e.message}`);
  }
}

async function init() {
  injectRailCSS();
  // rail interactions via delegation (survives re-renders)
  $("#case-list").addEventListener("click", (e) => {
    const del = e.target.closest(".del");
    if (del) { handleDelete(del.dataset.del); return; }
    if (e.target.closest(".surprise")) { surpriseMe(); return; }
    const pg = e.target.closest("[data-page]");
    if (pg) { gotoPage(pg.dataset.page); return; }
    const spec = e.target.closest(".specimen");
    if (spec) loadCase(spec.dataset.case);
  });
  // search the community pile (re-renders only the list+pager → keeps input focus)
  $("#case-list").addEventListener("input", (e) => {
    if (e.target.id === "rail-search") { FILTER = e.target.value; PAGE = 0; renderCommunity(); }
  });

  // upload: file picker + drag-and-drop onto the uploader
  $("#file-input").addEventListener("change", (e) => {
    const f = e.target.files && e.target.files[0];
    if (f) handleUpload(f);
    e.target.value = "";   // allow re-uploading the same file
  });
  const dz = $("#uploader"), btn = $("#upload-btn");
  ["dragenter", "dragover"].forEach(ev => dz.addEventListener(ev, (e) => { e.preventDefault(); btn.classList.add("dragover"); }));
  ["dragleave", "drop"].forEach(ev => dz.addEventListener(ev, (e) => { e.preventDefault(); btn.classList.remove("dragover"); }));
  dz.addEventListener("drop", (e) => {
    const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) handleUpload(f);
  });

  try {
    await refreshCases();
  } catch (e) {
    $("#case-list").innerHTML = `<li class="spec-row" style="padding:.7rem;color:#b82105">Could not reach the server (${esc(e.message)}).</li>`;
    return;
  }
  if (CASES.length) loadCase(CASES[0].case, false); // open on the first beat of the arc (∞) — keep the masthead in view
}

document.addEventListener("DOMContentLoaded", init);
