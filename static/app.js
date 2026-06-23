const $ = (id) => document.getElementById(id);

const fileInput = $("resume");
const drop = $("drop");
const dropLabel = $("drop-label");
const go = $("go");
let file = null;

function setFile(f) {
  if (!f) return;
  if (f.type !== "application/pdf" && !f.name.toLowerCase().endsWith(".pdf")) {
    dropLabel.textContent = "That's not a PDF — try again.";
    return;
  }
  file = f;
  drop.classList.add("ready");
  dropLabel.textContent = `📎 ${f.name}`;
  go.disabled = false;
}

drop.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => setFile(e.target.files[0]));
["dragover", "dragenter"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); })
);
["dragleave", "drop"].forEach((ev) =>
  drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); })
);
drop.addEventListener("drop", (e) => setFile(e.dataTransfer.files[0]));

function scoreColor(v) {
  if (v >= 75) return "var(--good)";
  if (v >= 50) return "var(--warn)";
  return "var(--bad)";
}

function setRing(scoreEl, value) {
  const ring = scoreEl.querySelector(".ring");
  ring.style.setProperty("--val", value);
  ring.style.setProperty("--col", scoreColor(value));
  ring.querySelector("span").textContent = value;
}

function li(parent, items, empty = "—") {
  parent.innerHTML = "";
  if (!items || !items.length) {
    parent.innerHTML = `<li class="missing">${empty}</li>`;
    return;
  }
  for (const it of items) {
    const el = document.createElement("li");
    el.textContent = it;
    parent.appendChild(el);
  }
}

function row(table, label, value) {
  const tr = document.createElement("tr");
  const v = value ? `<td>${value}</td>` : `<td class="missing">not captured</td>`;
  tr.innerHTML = `<td>${label}</td>${v}`;
  table.appendChild(tr);
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!file) return;

  const status = $("status");
  $("results").hidden = true;
  status.hidden = false;
  status.className = "status";
  status.innerHTML = `<span class="spinner"></span> Parsing your PDF and running the ATS evaluation… (~10–20s)`;
  go.disabled = true;

  const fd = new FormData();
  fd.append("resume", file);
  fd.append("job_description", $("jd").value);

  try {
    const res = await fetch("/api/evaluate", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");
    render(data);
    status.hidden = true;
  } catch (err) {
    status.innerHTML = `<span class="error">⚠️ ${err.message}</span>`;
  } finally {
    go.disabled = false;
  }
});

function render({ evaluation, parse }) {
  const r = evaluation;
  setRing($("score-ats"), r.ats_readiness_score);

  const kwScore = $("score-kw");
  if (r.keyword_match) {
    kwScore.hidden = false;
    setRing(kwScore, r.keyword_match.match_score);
  } else {
    kwScore.hidden = true;
  }

  $("summary").textContent = r.summary;
  li($("fixes"), r.fixes, "No fixes — looks clean!");

  const kwCard = $("kw-card");
  if (r.keyword_match) {
    kwCard.hidden = false;
    li($("kw-matched"), r.keyword_match.matched, "none");
    li($("kw-missing"), r.keyword_match.missing, "none");
  } else {
    kwCard.hidden = true;
  }

  const fields = $("fields");
  fields.innerHTML = "";
  const e = r.extracted;
  row(fields, "Name", e.name);
  row(fields, "Email", e.email);
  row(fields, "Phone", e.phone);
  row(fields, "Location", e.location);
  row(fields, "Recent title", e.most_recent_title);
  row(fields, "Recent employer", e.most_recent_employer);
  row(fields, "Experience", e.years_experience);
  row(fields, "Education", e.education);
  row(fields, "Skills", (e.skills || []).join(", "));

  $("parse-problems").innerHTML = e.parse_problems && e.parse_problems.length
    ? "Parse problems: " + e.parse_problems.join("; ") : "";

  const warnCard = $("warn-card");
  if (parse.warnings && parse.warnings.length) {
    warnCard.hidden = false;
    li($("warnings"), parse.warnings);
  } else {
    warnCard.hidden = true;
  }

  renderExtracted(parse.text, e, r.keyword_match);

  $("results").hidden = false;
  $("results").scrollIntoView({ behavior: "smooth" });
}

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function renderExtracted(text, fields, keywordMatch) {
  const note = $("legend-note");
  if (!text) {
    $("dumb").textContent = "(no text could be extracted — your resume may be image-based/scanned)";
    note.textContent = "";
    return;
  }

  let html = escapeHtml(text);

  // Blue: contact details the parser actually captured.
  for (const f of [fields.email, fields.phone]) {
    if (f) html = html.replace(new RegExp(escapeRegex(f), "g"), `<mark class="contact">${escapeHtml(f)}</mark>`);
  }

  // Green: matched keywords from the job description (longest first so phrases win).
  const matched = ((keywordMatch && keywordMatch.matched) || [])
    .filter(Boolean)
    .sort((a, b) => b.length - a.length);
  let hits = 0;
  for (const kw of matched) {
    const re = new RegExp("(?<![\\w>])(" + escapeRegex(kw) + ")(?![\\w<])", "gi");
    html = html.replace(re, (m) => { hits++; return `<mark class="hit">${m}</mark>`; });
  }

  $("dumb").innerHTML = html;

  if (keywordMatch) {
    note.textContent = `Found ${matched.length} of the job's keywords highlighted in your resume text.`;
  } else {
    note.textContent = "Tip: paste a job description above and re-analyze to see keyword matches highlighted here.";
  }
}
