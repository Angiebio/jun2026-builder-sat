/* Antique Infernal Engine — single-page UI logic. Vanilla JS, fully offline.
   Renders the field-guide page + the purple "Can it Run AI?" card + the
   "open the potato ledger" trace accordion from runs/<case>/ artifacts. */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);

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

function fmtNum(n) {
  if (n == null) return "—";
  if (n === -1) return "∞";
  return Math.abs(n) >= 1000 ? Math.round(n).toLocaleString() : (Math.round(n * 1000) / 1000);
}

/* ── tiny offline markdown → HTML for the article (no CDN). Handles the subset
      the writer template uses: headings, **bold**, *italic*, `code`, > quote,
      tables, fenced ``` blocks, - lists, hr, paragraphs. HTML-escaped first. ── */
function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
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

/* ── render the verdict card from math.json ── */
function verdictCard(math, obs) {
  const h = humanize(math.time_seconds, math.can_evaluate);
  const stats = [];
  if (math.input_value != null) stats.push(["input", `${fmtNum(math.input_value)} ${math.input_unit || ""}`.trim()]);
  if (math.units_for_ai_hello && math.units_for_ai_hello > 0) stats.push(["units for AI hello", fmtNum(math.units_for_ai_hello)]);
  if (math.potatoes_equivalent && math.potatoes_equivalent > 0) stats.push(["🥔 potatoes", fmtNum(math.potatoes_equivalent)]);
  if (math.cyclists_equivalent && math.cyclists_equivalent > 0) stats.push(["🚴 cyclists", fmtNum(math.cyclists_equivalent)]);
  const statHtml = stats.map(([k, v]) => `<div class="stat"><span class="k">${esc(k)}</span><span class="v">${esc(String(v))}</span></div>`).join("");
  return `
    <div class="verdict-card${h.never ? " never" : ""}">
      <p class="q">Can it run AI?</p>
      <p class="answer">${esc(h.big)}<span class="unit">${esc(h.unit)}</span></p>
      ${statHtml ? `<div class="stat-grid">${statHtml}</div>` : ""}
    </div>`;
}

/* ── render the trace ledger from trace.json ── */
function ledger(trace) {
  const steps = (trace && trace.steps) || [];
  const rows = steps.map(s => {
    const detail = s.guess || s.family || s.reason || (s.route_to ? `→ ${s.route_to}` : "") || "";
    const model = s.model || "—";
    const cls = (model === "deterministic" || model === "fixture") ? " deterministic" : "";
    const passBit = ("pass" in s) ? (s.pass ? " ✓ pass" : " ✗ fail") : "";
    return `<div class="step"><span class="agent">${esc(s.agent || "")}</span>
      <span class="detail">${esc(detail)}${passBit}</span>
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
function renderPage(data) {
  const obs = data.observation || {};
  const conf = obs.confidence != null ? ` · confidence ${Math.round(obs.confidence * 100)}%` : "";
  const path = (data.math && data.math.path) || obs.power_or_compute_path || "";
  const shot = data.has_image ? `<img class="shot" src="/image/${encodeURIComponent(data.case)}" alt="${esc(data.display)}">` : "";
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
  $("#page").scrollIntoView({ block: "nearest" });
}

async function loadCase(c, btn) {
  document.querySelectorAll(".specimen").forEach(b => b.setAttribute("aria-current", String(b === btn)));
  try {
    const r = await fetch(`/run/${encodeURIComponent(c)}`);
    if (!r.ok) throw new Error(`run ${c}: ${r.status}`);
    renderPage(await r.json());
  } catch (e) {
    $("#page").innerHTML = `<div class="article"><p><strong>Could not load ${esc(c)}.</strong> ${esc(e.message)}</p></div>`;
  }
}

async function init() {
  let cases;
  try {
    const r = await fetch("/cases");
    cases = (await r.json()).cases || [];
  } catch (e) {
    $("#case-list").innerHTML = `<li style="color:#b82105">Could not reach the server (${esc(e.message)}).</li>`;
    return;
  }
  const list = $("#case-list");
  list.innerHTML = "";
  cases.forEach((c, idx) => {
    const v = humanize(c.time_seconds, c.can_evaluate);
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.className = "specimen";
    btn.type = "button";
    btn.innerHTML = `<span class="name">${esc(c.display)}</span><span class="verdict">${esc(v.never ? "Never · ∞" : v.big + " " + v.unit.split(" ")[0])}</span>`;
    btn.addEventListener("click", () => loadCase(c.case, btn));
    li.appendChild(btn);
    list.appendChild(li);
    if (idx === 0) loadCase(c.case, btn); // open on the first beat of the arc (∞)
  });
}

document.addEventListener("DOMContentLoaded", init);
