"use strict";

const state = {
  direction: "recipient",
  lastReport: null,
  lastComparison: null,
  lastAudit: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function setStatus(text, tone = "muted") {
  const output = $("#connectionStatus");
  output.textContent = text;
  output.className = `status-pill ${tone}`;
}

function setRaw(payload) {
  $("#rawJson").textContent = JSON.stringify(payload || {}, null, 2);
}

function setBusy(button, busy) {
  button.disabled = busy;
  button.dataset.originalText = button.dataset.originalText || button.textContent;
  button.textContent = busy ? "Working..." : button.dataset.originalText;
}

function activeView(name) {
  $$(".tab-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === name);
  });
  $$(".view").forEach((view) => {
    view.classList.toggle("active", view.id === `view-${name}`);
  });
}

function cleanList(value) {
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function requestHeaders(hasBody) {
  const headers = {
    "Accept": "application/json",
    "X-Request-ID": $("#requestId").value.trim() || `ui-${Date.now()}`,
  };
  const apiKey = $("#apiKey").value.trim();
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  if (hasBody) {
    headers["Content-Type"] = "application/json";
  }
  return headers;
}

async function apiFetch(path, options = {}) {
  const hasBody = options.body !== undefined;
  const response = await fetch(`/api${path}`, {
    method: options.method || "GET",
    headers: requestHeaders(hasBody),
    body: hasBody ? JSON.stringify(options.body) : undefined,
  });

  const text = await response.text();
  let payload = {};
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch (error) {
      payload = { error: "InvalidJSON", message: text };
    }
  }

  setRaw(payload);
  $("#requestId").value = response.headers.get("X-Request-ID") || $("#requestId").value;

  if (!response.ok) {
    const message = payload.message || payload.error || `HTTP ${response.status}`;
    throw new Error(message);
  }

  return payload;
}

function collectBasePayload() {
  const payload = {
    direction: state.direction,
    external_id: $("#externalId").value.trim(),
    level: $("#level").value,
    sort_order: $("#sortOrder").value,
    include_text: $("#includeText").checked,
  };

  const typingId = $("#typingId").value.trim();
  const candidates = cleanList($("#candidateIds").value);
  const loci = cleanList($("#loci").value);
  const sortBy = $("#sortBy").value;

  if (typingId) {
    payload.typing_id = Number(typingId);
  }
  if (candidates.length) {
    payload.candidate_external_ids = candidates;
  }
  if (loci.length) {
    payload.loci = loci;
  }
  if (sortBy) {
    payload.sort_by = sortBy;
  }

  return payload;
}

function comparisonLevels() {
  return $$("input[name='comparisonLevel']:checked").map((input) => input.value);
}

function textValue(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function titleFromKey(key) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function tableColumns(rows, preferred) {
  const seen = new Set();
  const columns = [];
  for (const key of preferred) {
    if (rows.some((row) => Object.prototype.hasOwnProperty.call(row, key))) {
      seen.add(key);
      columns.push(key);
    }
  }
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (!seen.has(key)) {
        seen.add(key);
        columns.push(key);
      }
    }
  }
  return columns.slice(0, 9);
}

function renderTable(headSelector, bodySelector, rows, preferred = []) {
  const head = $(headSelector);
  const body = $(bodySelector);
  head.innerHTML = "";
  body.innerHTML = "";

  if (!Array.isArray(rows) || rows.length === 0) {
    const tr = document.createElement("tr");
    tr.className = "empty-row";
    tr.innerHTML = "<td>No rows loaded</td>";
    body.appendChild(tr);
    return;
  }

  const columns = tableColumns(rows, preferred);
  const headerRow = document.createElement("tr");
  for (const column of columns) {
    const th = document.createElement("th");
    th.textContent = titleFromKey(column);
    headerRow.appendChild(th);
  }
  head.appendChild(headerRow);

  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const column of columns) {
      const td = document.createElement("td");
      td.textContent = textValue(row[column]);
      tr.appendChild(td);
    }
    body.appendChild(tr);
  }
}

function updateMetrics(report, envelope) {
  const pairRows = report.pair_rows || [];
  const anchor = report.anchor || report.source || {};
  const reference = report.hla_reference || {};

  $("#metricPairs").textContent = textValue(report.pair_count ?? pairRows.length);
  $("#metricLevel").textContent = textValue(report.level || reference.level || $("#level").value);
  $("#metricAnchor").textContent = textValue(anchor.external_id || anchor.anchor_external_id || $("#externalId").value);
  $("#metricRequest").textContent = textValue(envelope.request_id);
}

function renderLocusRail(rows) {
  const rail = $("#locusRail");
  rail.innerHTML = "";
  if (!Array.isArray(rows) || rows.length === 0) {
    const empty = document.createElement("div");
    empty.className = "locus-item";
    empty.innerHTML = "<span>Loci</span><strong>No locus rows</strong>";
    rail.appendChild(empty);
    return;
  }

  const counts = rows.map((row) => Number(row.mismatch_count ?? row.mismatched_pairs ?? row.total_mismatches ?? 0));
  const max = Math.max(1, ...counts);

  rows.slice(0, 12).forEach((row, index) => {
    const count = counts[index];
    const item = document.createElement("div");
    item.className = "locus-item";
    item.innerHTML = `
      <span>${textValue(row.locus || row.hla_locus || row.name)}</span>
      <strong>${textValue(count)}</strong>
      <div class="locus-bar" aria-hidden="true"><i style="width: ${Math.round((count / max) * 100)}%"></i></div>
    `;
    rail.appendChild(item);
  });
}

function renderReport(envelope) {
  const report = envelope.data?.report || envelope.report || {};
  state.lastReport = report;
  updateMetrics(report, envelope);

  renderTable("#pairHead", "#pairRows", report.pair_rows || [], [
    "rank",
    "donor_external_id",
    "recipient_external_id",
    "candidate_external_id",
    "mismatch_count",
    "matched_pairs",
    "mismatched_pairs",
    "level",
  ]);
  renderLocusRail(report.locus_rows || []);

  const provenance = report.provenance || {};
  $("#reportMeta").textContent = [
    report.schema || "report",
    provenance.generated_at || report.generated_at,
    report.imgthla_version,
  ].filter(Boolean).join(" | ") || "Report loaded";
}

function renderComparison(envelope) {
  const comparison = envelope.data?.comparison || envelope.comparison || {};
  state.lastComparison = comparison;

  renderTable("#levelHead", "#levelRows", comparison.level_rows || [], [
    "level",
    "level_label",
    "pair_count",
    "matched_pairs",
    "mismatched_pairs",
    "mismatch_count",
    "stability",
  ]);
  renderTable("#pairDeltaHead", "#pairDeltaRows", comparison.pair_delta_rows || [], [
    "donor_external_id",
    "recipient_external_id",
    "candidate_external_id",
    "reference_mismatch_count",
    "comparison_mismatch_count",
    "delta",
    "stability",
  ]);
  renderTable("#locusDeltaHead", "#locusDeltaRows", comparison.locus_delta_rows || [], [
    "locus",
    "reference_mismatch_count",
    "comparison_mismatch_count",
    "delta",
    "stability",
  ]);
}

function renderAudit(envelope) {
  const bundle = envelope.data?.audit_bundle || envelope.audit_bundle || {};
  state.lastAudit = bundle;
  const doctor = bundle.doctor_summary || {};
  const fileCount = Object.keys(bundle.files || {}).length;
  const values = [
    [bundle.bundle_name || "-", bundle.bundle_dir || ""],
    [`OK ${doctor.OK ?? 0} / WARN ${doctor.WARN ?? 0} / FAIL ${doctor.FAIL ?? 0}`, ""],
    [String(fileCount), ""],
    [bundle.zip_path ? "Zip created" : "Directory", bundle.zip_path || ""],
  ];

  $$("#auditSummary > div").forEach((item, index) => {
    const strong = item.querySelector("strong");
    strong.textContent = values[index][0];
    strong.title = values[index][1];
  });
}

function handleError(error) {
  setStatus(error.message, "error");
  setRaw({ error: error.name || "Error", message: error.message });
}

async function runProbe(path, button) {
  setBusy(button, true);
  try {
    const payload = await apiFetch(path);
    const ready = payload.status || payload.state || "ok";
    setStatus(`${path.replace("/", "")}: ${ready}`, "ok");
  } catch (error) {
    handleError(error);
  } finally {
    setBusy(button, false);
  }
}

async function buildReport(button) {
  setBusy(button, true);
  try {
    const payload = await apiFetch("/reports/live", {
      method: "POST",
      body: collectBasePayload(),
    });
    renderReport(payload);
    activeView("report");
    setStatus("Report loaded", "ok");
  } catch (error) {
    handleError(error);
  } finally {
    setBusy(button, false);
  }
}

async function compareLevels(button) {
  const levels = comparisonLevels();
  if (levels.length < 2) {
    handleError(new Error("Select at least two levels."));
    return;
  }

  setBusy(button, true);
  try {
    const body = collectBasePayload();
    delete body.level;
    body.levels = levels;
    const payload = await apiFetch("/comparisons/levels", {
      method: "POST",
      body,
    });
    renderComparison(payload);
    activeView("comparison");
    setStatus("Comparison loaded", "ok");
  } catch (error) {
    handleError(error);
  } finally {
    setBusy(button, false);
  }
}

async function createAudit(button) {
  setBusy(button, true);
  try {
    const body = collectBasePayload();
    body.comparison_levels = comparisonLevels();
    body.zip_bundle = $("#zipBundle").checked;
    const payload = await apiFetch("/audit/live", {
      method: "POST",
      body,
    });
    renderAudit(payload);
    activeView("audit");
    setStatus("Audit created", "ok");
  } catch (error) {
    handleError(error);
  } finally {
    setBusy(button, false);
  }
}

function bindEvents() {
  $$(".tab-button").forEach((button) => {
    button.addEventListener("click", () => activeView(button.dataset.view));
  });

  $$(".segmented [data-direction]").forEach((button) => {
    button.addEventListener("click", () => {
      state.direction = button.dataset.direction;
      $$(".segmented [data-direction]").forEach((item) => {
        item.classList.toggle("active", item === button);
      });
    });
  });

  $("#liveButton").addEventListener("click", (event) => runProbe("/live", event.currentTarget));
  $("#readyButton").addEventListener("click", (event) => runProbe("/ready", event.currentTarget));
  $("#buildReport").addEventListener("click", (event) => buildReport(event.currentTarget));
  $("#compareLevels").addEventListener("click", (event) => compareLevels(event.currentTarget));
  $("#createAudit").addEventListener("click", (event) => createAudit(event.currentTarget));
  $("#clearRaw").addEventListener("click", () => setRaw({}));
  $("#saveNote").addEventListener("click", () => {
    localStorage.setItem("hlaValidationNote", $("#reviewNote").value);
    setStatus("Review note saved locally", "ok");
  });
}

function init() {
  $("#requestId").value = `ui-${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}`;
  $("#reviewNote").value = localStorage.getItem("hlaValidationNote") || "";
  bindEvents();
}

document.addEventListener("DOMContentLoaded", init);
