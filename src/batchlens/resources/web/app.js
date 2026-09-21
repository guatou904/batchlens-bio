"use strict";
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const esc = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const roles = [
  "sample",
  "unit",
  "target",
  "batch",
  "cell_type",
  "timepoint",
  "cell_id",
];
const scenarios = {
  quick: [
    ["confounded", "confounded"],
    ["balanced", "balanced"],
    ["paired", "pairedDemo"],
  ],
  advanced: [
    ["confounded-time", "confoundedTime"],
    ["balanced", "balanced"],
    ["partial-overlap", "partial"],
    ["redundant-nuisance", "redundant"],
    ["paired", "pairedDemo"],
    ["spatial-replicates", "spatial"],
    ["mixed-assays", "mixed"],
  ],
};
const state = {
  lang: "zh",
  mode: "quick",
  busy: false,
  stopped: false,
  file: null,
  preview: null,
  mapping: {},
  study: null,
  numerator: "",
  denominator: "",
  design_mode: "",
  thresholds: { min_units: 3, min_cells: 20, dominance: 0.6 },
  files: {},
  handoff: false,
  result: null,
  document: null,
  tab: "overview",
  filter: "all",
  settingsOpen: false,
  version: "",
};
const t = (key) => COPY[state.lang][key] ?? key;
const number = (value) =>
  Number(value).toLocaleString(state.lang === "zh" ? "zh-CN" : "en-US");
const motion = () =>
  matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
function clearStatus() {
  $("#status").hidden = true;
}
function showStatus(message, error = false) {
  const e = $("#status");
  e.textContent = message;
  e.classList.toggle("error", error);
  e.hidden = false;
  e.scrollIntoView({ block: "center", behavior: motion() });
}
function readableError(error) {
  const msg = error.message || t("failed");
  if (state.lang === "en" || !error.server) return msg;
  const translated = [
    [/Duplicate cell IDs/, "发现重复细胞 ID，请核对源表或使用全局唯一的 ID。"],
    [
      /conflicting unit/,
      "同一样本的供体、条件、批次或已选时间点不一致，请核对样本 ID。",
    ],
    [/empty\/padded/, "选中列包含空值或首尾空格，请核对并修正真实元数据。"],
    [/distinct column/, t("mappingDuplicate")],
    [/two different observed/, "请明确选择两个不同条件及比较方向。"],
    [/at least two observed/, "指定比较需要至少两个实际观测到的条件。"],
    [
      /exactly two conditions/,
      "当前配对模型仅支持两个条件。请在高级模式中复核其他重复结构。",
    ],
    [
      /coverage threshold/,
      "阈值无效：供体数至少为 2，细胞数至少为 1，占比须为 0.5–1。",
    ],
    [
      /UTF-8|quoted fields|Cannot read table/,
      "无法读取表格，请检查 UTF-8 编码、引号和分隔符。",
    ],
    [/Wrong number of fields/, "表格某行与表头的列数不一致，请检查 CSV/TSV。"],
    [
      /Duplicate column|Header names/,
      "列名重复、为空或含首尾空格，请修正表头。",
    ],
    [/100,000 cell/, "快速检查最多接收 100,000 行细胞元数据。"],
    [/10 MiB/, "快速检查需要不超过 10 MiB 的非空元数据表。"],
    [/already running/, "本机服务正在执行另一份审计，请稍后重试。"],
    [/Cell coverage requires/, "供体覆盖检查需要含 cell_type 列的细胞观测表。"],
    [
      /control characters/,
      "所选元数据或列名含有不支持的控制字符，请修正后重试。",
    ],
  ];
  return (
    translated.find(([pattern]) => pattern.test(msg))?.[1] ||
    `${t("failed")}：${msg}`
  );
}
async function request(path, payload) {
  let response;
  try {
    response = await fetch(path, {
      method: payload ? "POST" : "GET",
      headers: payload ? { "Content-Type": "application/json" } : {},
      body: payload ? JSON.stringify(payload) : undefined,
      cache: "no-store",
    });
  } catch {
    throw new Error(t("networkError"));
  }
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(t("networkError"));
  }
  if (!response.ok) {
    const error = new Error(data.error || t("failed"));
    error.server = true;
    throw error;
  }
  return data;
}
async function work(action, focus = "#main") {
  if (state.busy || state.stopped) return;
  state.busy = true;
  clearStatus();
  $("#busy").hidden = false;
  $("#main").inert = true;
  $(".topbar").inert = true;
  $("#main").setAttribute("aria-busy", "true");
  let failed = false;
  try {
    await action();
  } catch (error) {
    failed = true;
    showStatus(readableError(error), true);
  } finally {
    state.busy = false;
    $("#busy").hidden = true;
    $("#main").inert = false;
    $(".topbar").inert = false;
    $("#main").setAttribute("aria-busy", "false");
    updateReady();
    const target = $(failed ? "#status" : focus);
    target?.focus({ preventScroll: true });
    if (focus === "#results" && !failed)
      target?.scrollIntoView({ behavior: motion(), block: "start" });
  }
}
function invalidate() {
  state.result = null;
  state.document = null;
  $("#results").hidden = true;
}
function applyLanguage() {
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
  document.title = `BatchLens Bio · ${state.lang === "zh" ? "研究设计工作台" : "Study-design workbench"}`;
  $$("[data-i18n]").forEach((e) => (e.innerHTML = t(e.dataset.i18n)));
  $("#language").textContent = state.lang === "zh" ? "EN" : "中";
  $("#language").setAttribute(
    "aria-label",
    state.lang === "zh" ? "Switch to English" : "切换为中文",
  );
  $("#version").textContent = state.version
    ? `v${state.version} · ${t("alpha")}`
    : "BatchLens Bio";
  renderWorkspace();
  if (state.result) renderResults();
}
function switchMode(mode, focus = true) {
  state.mode = mode;
  clearStatus();
  renderWorkspace();
  if (focus) $(`#mode-${mode}`).focus({ preventScroll: true });
}
function renderWorkspace() {
  $("#mode-tabs").setAttribute("aria-label", t("entryMode"));
  $("#mode-tabs").innerHTML = ["quick", "advanced"]
    .map(
      (mode, i) =>
        `<button class="mode-tab ${state.mode === mode ? "active" : ""}" id="mode-${mode}" role="tab" aria-selected="${state.mode === mode}" aria-controls="input-panel" tabindex="${state.mode === mode ? 0 : -1}" data-mode="${mode}"><span class="mode-icon" aria-hidden="true">${i ? "≡" : "↗"}</span><span><strong>${t(mode)}</strong><small>${t(mode + "Intro")}</small></span><span class="mode-check" aria-hidden="true">${state.mode === mode ? "✓" : ""}</span></button>`,
    )
    .join("");
  $("#input-panel").setAttribute("aria-labelledby", `mode-${state.mode}`);
  state.mode === "quick" ? renderQuick() : renderAdvanced();
  renderGuide();
  updateReady();
}
function sectionTitle(step, title, copy) {
  return `<div class="section-heading"><span class="step">${step}</span><div><h2>${t(title)}</h2><p>${t(copy)}</p></div></div>`;
}
function mappingState() {
  if (roles.slice(0, 5).some((role) => !state.mapping[role]))
    return "mappingMissing";
  const cols = Object.values(state.mapping).filter(Boolean);
  if (new Set(cols).size !== cols.length) return "mappingDuplicate";
  return "ready";
}
function quickReady() {
  const c = state.thresholds;
  return (
    state.file &&
    state.study &&
    mappingState() === "ready" &&
    state.numerator &&
    state.denominator &&
    state.numerator !== state.denominator &&
    state.design_mode &&
    Number.isInteger(c.min_units) &&
    c.min_units >= 2 &&
    c.min_units <= 100000 &&
    Number.isInteger(c.min_cells) &&
    c.min_cells >= 1 &&
    c.min_cells <= 1000000 &&
    Number.isFinite(c.dominance) &&
    c.dominance >= 0.5 &&
    c.dominance <= 1
  );
}
function updateReady() {
  const run = $("#run");
  if (!run) return;
  const valid =
    state.mode === "quick"
      ? quickReady()
      : state.files.samples && state.files.design;
  run.disabled = !valid || state.busy || state.stopped;
  const ready = $("#ready");
  if (ready)
    ready.textContent = t(
      state.mode === "quick"
        ? valid
          ? "ready"
          : "notReady"
        : valid
          ? "allFilesReady"
          : "chooseBoth",
    );
  const handoff = $("#handoff");
  if (handoff) handoff.disabled = !valid || state.busy || state.stopped;
}
function renderQuick() {
  let body = sectionTitle("01", "quickTitle", "quickCopy");
  body += `<input id="cell-file" type="file" accept=".csv,.tsv" hidden>`;
  if (!state.preview) {
    body += `<div id="quick-drop" class="drop-zone" tabindex="0" role="button" aria-label="${esc(t("choose"))}"><span class="upload-icon" aria-hidden="true">↥</span><strong>${t("drop")}</strong><p>${t("dropCopy")}</p><span class="primary">${t("choose")} <span aria-hidden="true">↗</span></span><small>${t("quickLimit")}</small></div><p class="fine-print">${t("noH5ad")}</p><div class="mini-flow"><span>01 ${t("preview")}</span><span>02 ${t("mappingTitle")}</span><span>03 ${t("confirmStudy")}</span></div>`;
  } else {
    const columns = state.preview.columns,
      shown = columns.slice(0, 8);
    body += `<div class="file-summary"><span class="file-symbol" aria-hidden="true">▤</span><div><strong>${esc(state.file.name)}</strong><small>${number(state.preview.row_count)} ${t("rows")} · ${columns.length} ${t("columns")}</small></div><button class="quiet" data-action="choose-cell">${t("changed")}</button></div><div class="mapping-intro"><h3>${t("mappingTitle")}</h3><p>${t("mappingHelp")}</p></div><div class="role-list">${roles.map((role, i) => `<div class="role-row"><label for="role-${role}"><strong>${t(role)} ${i < 5 ? "<em>*</em>" : `<small>${t("optional")}</small>`}</strong><span>${t(role + "Help")}</span></label><select id="role-${role}" data-role="${role}" ${i < 5 ? "required" : ""}><option value="">${t(i < 5 ? "selectColumn" : "omit")}</option>${columns.map((c) => `<option value="${esc(c)}" ${state.mapping[role] === c ? "selected" : ""}>${esc(c)}</option>`).join("")}</select></div>`).join("")}</div><p class="fine-print">${t("onlyMapped")}</p><div class="comparison-box">${sectionTitle("02", "confirmStudy", "comparisonHelp")}`;
    if (state.study) {
      const levels = state.study.levels;
      body += `<p class="study-stats">${t("studySummary")} <strong>${state.study.samples}</strong> ${t("samples")} · <strong>${state.study.units}</strong> ${t("units")}</p>${state.study.repeated_units ? `<p class="note">${t("repeatHint")}</p>` : ""}<div class="comparison-grid">${["numerator", "denominator"].map((key) => `<label>${t(key)}<select id="${key}" data-choice="${key}"><option value="">${t("selectLevel")}</option>${levels.map((l) => `<option value="${esc(l)}" ${state[key] === l ? "selected" : ""}>${esc(l)}</option>`).join("")}</select></label>`).join("")}</div><label class="full-label">${t("mode")}<select id="design-mode" data-choice="design_mode"><option value="">${t("selectMode")}</option>${["independent", "paired"].map((mode) => `<option value="${mode}" ${state.design_mode === mode ? "selected" : ""}>${t(mode)}</option>`).join("")}</select></label><p class="model-hint">${t("modelHint")}</p>`;
    } else
      body += `<p class="note">${t(mappingState() === "ready" ? "mappingMissing" : mappingState())}</p>`;
    body += `</div><details id="thresholds" ${state.settingsOpen ? "open" : ""}><summary>${t("thresholds")}</summary><p class="fine-print">${t("thresholdHint")}</p><div class="threshold-grid">${["min_units", "min_cells", "dominance"].map((key, i) => `<label>${t(key)}<input type="number" id="setting-${key}" data-setting="${key}" value="${state.thresholds[key]}" min="${i === 0 ? 2 : i === 1 ? 1 : 0.5}" max="${i === 0 ? 100000 : i === 1 ? 1000000 : 1}" step="${i === 2 ? 0.05 : 1}"></label>`).join("")}</div></details><details><summary>${t("preview")}</summary><p class="fine-print">${t("previewHelp")}</p><div class="table-scroll" tabindex="0"><table><thead><tr>${shown.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${state.preview.rows.map((row) => `<tr>${shown.map((c) => `<td title="${esc(row[c])}">${esc(row[c])}</td>`).join("")}</tr>`).join("")}</tbody></table></div></details><div class="run-row"><button id="run" class="primary" data-action="run">${t("runQuick")} <span aria-hidden="true">→</span></button><button id="handoff" class="secondary" data-action="handoff">${t("handoff")}</button></div><p id="ready" class="fine-print" role="status"></p>`;
  }
  body += `<p class="privacy-note"><span aria-hidden="true">◉</span> ${t("localCopy")}</p>`;
  $("#input-panel").innerHTML = body;
}
function renderAdvanced() {
  let body = sectionTitle("01", "advancedTitle", "advancedCopy");
  if (state.handoff) body += `<p class="note">${t("handoffNote")}</p>`;
  const slot = (role) =>
    `<div data-drop-role="${role}" class="file-slot ${state.files[role] ? "selected" : ""}"><label for="${role}"><strong>${t(role + "File")} ${["samples", "design"].includes(role) ? `<small>${t("required")}</small>` : ""}</strong><span>${esc(state.files[role]?.name || t("notChosen"))}</span><input type="file" id="${role}" data-file="${role}" accept="${role === "design" ? ".yaml,.yml" : ".csv,.tsv"}"></label>${state.files[role] ? `<button class="remove" data-clear="${role}" aria-label="${esc(t("remove"))} ${role}">×</button>${state.handoff ? `<button class="input-download" data-download-input="${role}">${t("saveInput")} ↓</button>` : ""}` : ""}</div>`;
  body += `<div id="advanced-drop" class="advanced-drop" tabindex="0" role="button"><strong>${t("advancedDrop")}</strong><span>${t("advancedDropHint")}</span><input id="advanced-files" type="file" multiple accept=".csv,.tsv,.yaml,.yml" hidden></div><div class="file-grid">${slot("samples")}${slot("design")}</div><details ${state.files.observations || state.files.assays ? "open" : ""}><summary>${t("optionalFiles")}</summary><div class="file-grid">${slot("observations")}${slot("assays")}</div></details><p class="fine-print">${t("advancedLimit")}</p><p class="note">${t("advancedCoverage")}</p><div class="run-row"><button id="run" class="primary" data-action="run">${t("runAdvanced")} <span aria-hidden="true">↗</span></button></div><p id="ready" class="fine-print" role="status"></p><p class="privacy-note">◉ ${t("localCopy")}</p>`;
  $("#input-panel").innerHTML = body;
}
function renderGuide() {
  $("#guide-panel").innerHTML =
    `<section class="card demo-card"><div class="eyebrow">EXPLORE A STUDY</div><h2>${t("demoTitle")}</h2><p>${t("demoCopy")}</p><label class="sr-only" for="demo-case">${t("synthetic")}</label><select id="demo-case">${scenarios[state.mode].map(([value, key]) => `<option value="${value}">${t(key)}</option>`).join("")}</select><button id="demo" class="secondary" data-action="demo">${t("demo")} <span aria-hidden="true">→</span></button><div id="templates" class="templates"></div></section><section class="learning-card"><span class="learning-icon" aria-hidden="true">2 → 1</span><h3>${t("learnTitle")}</h3><p>${t("learnCopy")}</p></section><p class="scope-note">${t("boundary")}</p>`;
  renderTemplates();
}
function renderTemplates() {
  const value = $("#demo-case").value;
  const names =
    state.mode === "quick"
      ? [value + ".csv"]
      : [
          "samples.tsv",
          "design.yaml",
          ...(value === "spatial-replicates"
            ? ["observations.tsv"]
            : value === "mixed-assays"
              ? ["assays.tsv"]
              : []),
        ];
  $("#templates").innerHTML =
    `<span>${t("template")}</span>${names.map((name) => `<a href="${state.mode === "quick" ? "quick-examples/" + name : "examples/" + value + "/" + name}" download>${esc(name)} ↓</a>`).join("")}`;
}
function fileValue(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () =>
      resolve({ name: file.name, data: reader.result.split(",")[1] });
    reader.onerror = () => reject(new Error(t("failed")));
    reader.readAsDataURL(file);
  });
}
async function inspectMapping() {
  state.study = null;
  if (mappingState() !== "ready") return;
  const response = await request("api/quick/preview", {
    file: state.file,
    mapping: state.mapping,
  });
  state.study = response.study;
  for (const key of ["numerator", "denominator"])
    if (!state.study.levels.includes(state[key])) state[key] = "";
}
async function importCells(file) {
  if (!file) return;
  await work(async () => {
    if (!/\.(csv|tsv)$/i.test(file.name)) throw new Error(t("wrongType"));
    if (!file.size) throw new Error(t("emptyFile"));
    if (file.size > 10 * 1024 * 1024) throw new Error(t("tooLarge"));
    try {
      new TextDecoder("utf-8", { fatal: true }).decode(
        await file.arrayBuffer(),
      );
    } catch {
      throw new Error(t("badUtf8"));
    }
    const encoded = await fileValue(file);
    const preview = await request("api/quick/preview", { file: encoded });
    state.file = encoded;
    state.preview = preview;
    state.mapping = { ...preview.suggested_mapping };
    state.study = null;
    state.numerator = "";
    state.denominator = "";
    state.design_mode = "";
    state.thresholds = { min_units: 3, min_cells: 20, dominance: 0.6 };
    state.settingsOpen = false;
    invalidate();
    renderQuick();
    await inspectMapping();
    renderQuick();
  }, "#main");
}
function quickPayload() {
  return {
    file: state.file,
    mapping: { ...state.mapping },
    numerator: state.numerator,
    denominator: state.denominator,
    design_mode: state.design_mode,
    cell_coverage: { ...state.thresholds },
    language: state.lang,
  };
}
async function run(example = false) {
  await work(async () => {
    let response;
    if (example)
      response = await request(
        `${state.mode === "quick" ? "api/quick/demo/" : "api/demo/"}${$("#demo-case").value}`,
        { language: state.lang },
      );
    else if (state.mode === "quick") {
      if (!quickReady()) throw new Error(t("notReady"));
      response = await request("api/quick/audit", quickPayload());
    } else {
      if (!state.files.samples || !state.files.design)
        throw new Error(t("advancedRequired"));
      const entries = await Promise.all(
        Object.entries(state.files).map(async ([role, file]) => [
          role,
          await fileValue(file),
        ]),
      );
      response = await request("api/audit", {
        files: Object.fromEntries(entries),
        language: state.lang,
      });
    }
    const document = await request(
      `reports/${encodeURIComponent(response.id)}/result.json`,
    );
    state.result = response;
    state.document = document;
    state.tab = "overview";
    state.filter = "all";
    renderResults();
  }, "#results");
}
async function handoff() {
  await work(async () => {
    if (!quickReady()) return;
    const result = await request("api/quick/prepare", quickPayload());
    state.files = {};
    for (const [role, file] of Object.entries(result.files)) {
      const bytes = Uint8Array.from(atob(file.data), (c) => c.charCodeAt(0));
      state.files[role] = new File([bytes], file.name);
    }
    state.handoff = true;
    state.mode = "advanced";
    invalidate();
    renderWorkspace();
  }, "#input-panel");
}
function validateAdvanced(next) {
  for (const [role, file] of Object.entries(next)) {
    if (!(role === "design" ? /\.ya?ml$/i : /\.(csv|tsv)$/i).test(file.name))
      throw new Error(role === "design" ? t("designType") : t("wrongType"));
    if (!file.size) throw new Error(t("emptyFile"));
    if (role === "design" && file.size > 1000000)
      throw new Error(t("tooLarge"));
  }
  if (
    Object.values(next).reduce((sum, file) => sum + file.size, 0) >
    32 * 1024 * 1024
  )
    throw new Error(t("tooLarge"));
}
async function importAdvanced(role, file) {
  if (!file) return;
  await work(async () => {
    const next = { ...state.files, [role]: file };
    validateAdvanced(next);
    state.files = next;
    state.handoff = false;
    invalidate();
    renderAdvanced();
  }, "#" + role);
}
async function importAdvancedGroup(files) {
  if (!files.length) return;
  await work(async () => {
    const next = { ...state.files };
    const assigned = new Set();
    for (const file of files) {
      const role = /\.ya?ml$/i.test(file.name)
        ? "design"
        : /^(observations?|cells|spots)[._-]/i.test(file.name)
          ? "observations"
          : /^assays?[._-]/i.test(file.name)
            ? "assays"
            : /\.(csv|tsv)$/i.test(file.name)
              ? "samples"
              : null;
      if (!role || assigned.has(role)) throw new Error(t("namedFiles"));
      assigned.add(role);
      next[role] = file;
    }
    validateAdvanced(next);
    state.files = next;
    state.handoff = false;
    invalidate();
    renderAdvanced();
  }, "#advanced-drop");
}
function downloadInput(role) {
  const file = state.files[role];
  if (!file) return;
  const url = URL.createObjectURL(file);
  const a = document.createElement("a");
  a.href = url;
  a.download = file.name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}
function evidence(finding) {
  return finding.evidence_refs.map((ref) =>
    ref
      .split("/")
      .slice(1)
      .reduce(
        (value, key) => value[key.replaceAll("~1", "/").replaceAll("~0", "~")],
        state.document,
      ),
  );
}
function renderResults() {
  if (!state.result) return;
  const result = state.result,
    report = state.document,
    prefix = `reports/${encodeURIComponent(result.id)}/`;
  $("#results").hidden = false;
  const flags = result.findings.filter((f) => f.severity !== "info").length;
  $("#results").innerHTML =
    `<div class="result-heading"><div><p class="eyebrow">YOUR STUDY / THE EVIDENCE</p><h2 id="results-title">${t("resultTitle")}</h2>${result.synthetic ? `<span class="tag">${t("synthetic")} · ${esc(result.synthetic)}</span>` : ""}</div><div class="downloads"><a id="download-html" class="primary" href="${prefix}download.${state.lang}.html" download>${t("downloadHtml")} ↓</a><a id="download-zip" class="secondary" href="${prefix}bundle.zip" download>${t("downloadZip")}</a><a class="quiet" href="${prefix}result.json" download>${t("downloadJson")}</a></div></div><div class="stats">${[
      ["samples", result.counts.samples],
      ["units", result.counts.experimental_units],
      ["observations", result.counts.observations],
      ["reviewFlags", flags],
    ]
      .map(
        ([key, value]) =>
          `<div class="card stat"><span>${t(key)}</span><strong>${number(value)}</strong></div>`,
      )
      .join(
        "",
      )}</div><div class="contrasts">${result.contrasts.map((c) => `<div class="contrast ${c.status}"><span class="badge">${t(c.status)}</span><strong>${esc(c.numerator)} <span aria-hidden="true">−</span> ${esc(c.denominator)}</strong><small>${t(c.status === "NOT_ASSESSED" ? "notAssessedHint" : "estimableHint")}</small></div>`).join("")}</div><div class="result-tabs" role="tablist" aria-label="${esc(t("resultTitle"))}">${["overview", "report", "provenance"].map((tab) => `<button id="tab-${tab}" role="tab" data-tab="${tab}" aria-selected="${tab === state.tab}" tabindex="${tab === state.tab ? 0 : -1}" aria-controls="result-panel">${t(tab)}</button>`).join("")}</div><div id="result-panel" role="tabpanel" aria-labelledby="tab-${state.tab}"></div><p class="saved">${t("saved")}: <span>${esc(result.saved_to)}</span></p><p class="fine-print">${t("scope")} ${t("copyLanguage")}</p>`;
  const panel = $("#result-panel");
  if (state.tab === "report") {
    panel.innerHTML = `<iframe id="report" title="${esc(t("report"))}" sandbox="allow-same-origin" referrerpolicy="no-referrer"></iframe>`;
    const frame = $("#report");
    frame.onload = () => {
      const doc = frame.contentDocument;
      if (!doc) return;
      const resize = () => {
        frame.style.height = "400px";
        frame.style.height =
          Math.max(500, doc.documentElement.scrollHeight + 4) + "px";
      };
      resize();
      doc.addEventListener("toggle", resize, true);
    };
    frame.src = prefix + `report.${state.lang}.html`;
    return;
  }
  if (state.tab === "provenance") {
    panel.innerHTML = `<section class="card provenance"><h3>${t("rawConfig")}</h3><pre>${esc(JSON.stringify(report.declared_design, null, 2))}</pre><h3>${t("adapter")}</h3>${report.input_adapter ? `<pre>${esc(JSON.stringify(report.input_adapter, null, 2))}</pre>` : `<p>${t("standardMode")}</p>`}</section>`;
    return;
  }
  const findings = result.findings
    .map((f, i) => ({ f, i }))
    .filter(({ f }) => state.filter === "all" || f.severity === state.filter);
  panel.innerHTML = `<div class="result-grid"><section class="card findings"><div class="card-title"><h3>${t("findings")}</h3><span class="tag">${result.findings.length}</span></div><div class="filters" role="group" aria-label="${esc(t("findings"))}">${["all", "critical", "warning", "info"].map((filter) => `<button data-filter="${filter}" aria-pressed="${state.filter === filter}">${t(filter)} ${filter === "all" ? result.findings.length : result.findings.filter((f) => f.severity === filter).length}</button>`).join("")}</div>${
    findings.length
      ? findings
          .map(({ f, i }) => {
            const copy = result.display_findings[state.lang][i];
            return `<details class="finding ${f.severity}" ${i === 0 ? "open" : ""}><summary><span class="finding-meta"><span class="badge ${f.severity}">${t(f.severity)}</span><code>${esc(f.rule_id)}</code></span><strong>${esc(copy.title)}</strong></summary><div class="finding-body"><div class="next-step"><b>${t("nextStep")}</b><p>${esc(copy.action)}</p></div><details class="evidence"><summary>${t("evidence")}</summary><pre>${esc(JSON.stringify(evidence(f), null, 2))}</pre></details></div></details>`;
          })
          .join("")
      : `<p class="empty">${t(result.findings.length ? "noFindings" : "noFlags")}</p>`
  }</section><aside><section class="card support"><h3>${t("coverageTitle")}</h3>${report.cell_support.length ? report.cell_support.map((row) => `<div class="support-row"><strong>${esc(row.cell_type)}</strong><span>${esc(row.target_level)}</span><div class="support-numbers"><div><b>${row.supported_units} / ${row.eligible_units}</b><small>${t("supported")}</small></div><div><b>${row.largest_unit_share === null ? "—" : (row.largest_unit_share * 100).toFixed(1) + "%"}</b><small>${t("share")}</small></div></div><div class="support-track"><i style="width:${row.eligible_units ? (100 * row.supported_units) / row.eligible_units : 0}%"></i></div><small>${number(row.cells)} ${t("cells")} · ≥ ${row.min_cells} / ${t("unit")}</small></div>`).join("") : `<p class="fine-print">${t("coverageEmpty")}</p>`}</section><p class="scope-note">${t("boundary")}</p></aside></div>`;
}
function selectTab(tab) {
  state.tab = tab;
  renderResults();
  $(`#tab-${tab}`).focus({ preventScroll: true });
}
document.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button || state.busy || state.stopped) return;
  if (button.dataset.mode) switchMode(button.dataset.mode);
  if (button.dataset.action === "choose-cell") $("#cell-file").click();
  if (button.dataset.action === "run") run();
  if (button.dataset.action === "demo") run(true);
  if (button.dataset.action === "handoff") handoff();
  if (button.dataset.clear) {
    delete state.files[button.dataset.clear];
    invalidate();
    renderAdvanced();
    updateReady();
    $("#" + button.dataset.clear).focus();
  }
  if (button.dataset.downloadInput) downloadInput(button.dataset.downloadInput);
  if (button.dataset.tab) selectTab(button.dataset.tab);
  if (button.dataset.filter) {
    state.filter = button.dataset.filter;
    renderResults();
    $(`[data-filter="${state.filter}"]`).focus({ preventScroll: true });
  }
});
document.addEventListener("change", async (event) => {
  if (state.busy || state.stopped) return;
  const input = event.target;
  if (input.id === "cell-file") importCells(input.files[0]);
  if (input.id === "advanced-files") importAdvancedGroup([...input.files]);
  if (input.dataset.file) importAdvanced(input.dataset.file, input.files[0]);
  if (input.id === "demo-case") renderTemplates();
  if (input.dataset.role) {
    state.mapping[input.dataset.role] = input.value || null;
    invalidate();
    state.study = null;
    await work(async () => {
      try {
        await inspectMapping();
      } finally {
        renderQuick();
      }
    }, "#" + input.id);
    updateReady();
  }
  if (input.dataset.choice) {
    state[input.dataset.choice] = input.value;
    invalidate();
    clearStatus();
    updateReady();
  }
});
document.addEventListener("input", (event) => {
  if (event.target.dataset.setting) {
    const key = event.target.dataset.setting;
    state.thresholds[key] =
      event.target.value === "" ? NaN : Number(event.target.value);
    invalidate();
    clearStatus();
    updateReady();
  }
});
document.addEventListener(
  "toggle",
  (event) => {
    if (event.target.id === "thresholds")
      state.settingsOpen = event.target.open;
  },
  true,
);
document.addEventListener("keydown", (event) => {
  const tab = event.target.closest('[role="tab"]');
  if (
    !tab ||
    !["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key) ||
    state.busy
  )
    return;
  event.preventDefault();
  const values = tab.dataset.mode
    ? ["quick", "advanced"]
    : ["overview", "report", "provenance"];
  const index = values.indexOf(tab.dataset.mode || tab.dataset.tab);
  const next =
    values[
      event.key === "Home"
        ? 0
        : event.key === "End"
          ? values.length - 1
          : (index + (event.key === "ArrowRight" ? 1 : values.length - 1)) %
            values.length
    ];
  tab.dataset.mode ? switchMode(next) : selectTab(next);
});
document.addEventListener("click", (event) => {
  if (state.busy || state.stopped) return;
  if (event.target.closest("#quick-drop")) $("#cell-file").click();
  if (
    event.target.closest("#advanced-drop") &&
    event.target.id !== "advanced-files"
  )
    $("#advanced-files").click();
});
document.addEventListener("keydown", (event) => {
  if (state.busy || state.stopped) return;
  if (
    ["quick-drop", "advanced-drop"].includes(event.target.id) &&
    ["Enter", " "].includes(event.key)
  ) {
    event.preventDefault();
    $(
      event.target.id === "quick-drop" ? "#cell-file" : "#advanced-files",
    ).click();
  }
});
for (const name of ["dragover", "drop"])
  window.addEventListener(name, (event) => event.preventDefault());
const dropTarget = (event) =>
  event.target.closest("#quick-drop,#advanced-drop,[data-drop-role]");
document.addEventListener("dragover", (event) => {
  const drop = dropTarget(event);
  if (drop && !state.busy && !state.stopped) drop.classList.add("dragover");
});
document.addEventListener("dragleave", (event) =>
  dropTarget(event)?.classList.remove("dragover"),
);
document.addEventListener("drop", (event) => {
  const drop = dropTarget(event);
  if (!drop || state.busy || state.stopped) return;
  drop.classList.remove("dragover");
  const files = [...event.dataTransfer.files];
  if (drop.id === "advanced-drop") {
    importAdvancedGroup(files);
    return;
  }
  if (files.length !== 1) {
    showStatus(t("oneFile"), true);
    $("#status").focus();
    return;
  }
  drop.dataset.dropRole
    ? importAdvanced(drop.dataset.dropRole, files[0])
    : importCells(files[0]);
});
$("#language").addEventListener("click", () => {
  if (state.busy || state.stopped) return;
  state.lang = state.lang === "zh" ? "en" : "zh";
  clearStatus();
  applyLanguage();
  $("#language").focus();
});
$("#quit").addEventListener("click", () =>
  work(async () => {
    await request("api/quit", {});
    state.stopped = true;
    showStatus(t("stopped"));
    $$("button,input,select").forEach((e) => (e.disabled = true));
  }, "#status"),
);
applyLanguage();
request("api/info")
  .then((info) => {
    state.version = info.version;
    $("#version").textContent = `v${info.version} · ${t("alpha")}`;
  })
  .catch((error) => {
    state.stopped = true;
    showStatus(error.message, true);
    updateReady();
  });
