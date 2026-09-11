"use strict";
const $ = (id) => document.getElementById(id);
const roles = ["samples", "design", "observations", "assays"];
const files = {};
const placeholders = Object.fromEntries(
  roles.map((role) => [role, $(`${role}-name`).textContent]),
);
let busy = false;
let stopped = false;
let limit = 32 * 1024 * 1024;

function status(message, error = false) {
  $("status").textContent = message;
  $("status").className = error ? "error" : "";
  $("status").hidden = !message;
}
function update() {
  const ready = Boolean(files.samples && files.design);
  $("run").disabled = busy || stopped || !ready;
  $("demo").disabled = busy || stopped;
  $("demo-case").disabled = busy || stopped;
  $("quit").disabled = busy || stopped;
  $("all-files").disabled = busy || stopped;
  $("ready").textContent = busy
    ? "Auditing your design…"
    : ready
      ? "Ready to audit your design."
      : "Add samples and design to continue.";
  roles.forEach((role) => {
    $(role).disabled = busy || stopped;
    const selected = files[role];
    $(`${role}-name`).textContent = selected
      ? selected.name
      : placeholders[role];
    $(`${role}-name`).title = selected ? selected.name : "";
    const slot = document.querySelector(`[data-role="${role}"]`);
    slot.classList.toggle("selected", Boolean(selected));
    const remove = slot.querySelector("button");
    remove.hidden = !selected;
    remove.disabled = busy || stopped;
  });
}
function setFile(role, file) {
  if (busy || stopped || !file) return;
  const valid = role === "design" ? /\.ya?ml$/i : /\.(csv|tsv)$/i;
  if (!valid.test(file.name))
    throw new Error(
      `${role}: choose ${role === "design" ? "a YAML" : "a CSV or TSV"} file.`,
    );
  const total =
    file.size +
    roles
      .filter((item) => item !== role)
      .reduce((sum, item) => sum + (files[item]?.size || 0), 0);
  if (total > limit)
    throw new Error(
      "Files exceed the combined 32 MiB limit. Use the CLI for larger inputs.",
    );
  if (!file.size) throw new Error(`${file.name} is empty.`);
  if (role === "design" && file.size > 1000000)
    throw new Error("Design configuration exceeds 1 MB.");
  files[role] = file;
  status("");
  update();
}
function receive(list, role) {
  if (busy || stopped) return;
  try {
    if (role) {
      if (list.length !== 1)
        throw new Error(`Drop one ${role} file into this field.`);
      setFile(role, list[0]);
      return;
    }
    const assigned = new Set();
    for (const file of list) {
      let target;
      if (/\.ya?ml$/i.test(file.name)) target = "design";
      else if (/^(observations?|cells|spots)[._-]/i.test(file.name))
        target = "observations";
      else if (/^assays?[._-]/i.test(file.name)) target = "assays";
      else if (/\.(csv|tsv)$/i.test(file.name)) target = "samples";
      else
        throw new Error(
          `Unsupported file: ${file.name}. Choose CSV, TSV or YAML.`,
        );
      if (assigned.has(target))
        throw new Error(
          `Multiple ${target} files detected. Drop each file into its named field.`,
        );
      assigned.add(target);
      setFile(target, file);
      if (["observations", "assays"].includes(target))
        document.querySelector("details").open = true;
    }
  } catch (error) {
    status(error.message, true);
  }
}
roles.forEach((role) => {
  $(role).addEventListener("change", (event) =>
    receive(Array.from(event.target.files), role),
  );
  document
    .querySelector(`[data-clear="${role}"]`)
    .addEventListener("click", () => {
      delete files[role];
      $(role).value = "";
      status("");
      update();
    });
});
$("all-files").addEventListener("change", (event) => {
  receive(Array.from(event.target.files));
  event.target.value = "";
});
$("drop-all").addEventListener("click", () => {
  if (!busy && !stopped) $("all-files").click();
});
$("drop-all").addEventListener("keydown", (event) => {
  if (["Enter", " "].includes(event.key)) {
    event.preventDefault();
    $("drop-all").click();
  }
});
document.querySelectorAll(".drop-all,.file-slot").forEach((zone) => {
  zone.addEventListener("dragover", (event) => {
    event.preventDefault();
    if (!busy && !stopped) zone.classList.add("dragover");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", (event) => {
    event.preventDefault();
    zone.classList.remove("dragover");
    receive(Array.from(event.dataTransfer.files), zone.dataset.role);
  });
});
window.addEventListener("dragover", (event) => event.preventDefault());
window.addEventListener("drop", (event) => event.preventDefault());

function encode(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () =>
      resolve({ name: file.name, data: reader.result.split(",")[1] });
    reader.onerror = () =>
      reject(new Error(`Cannot read ${file.name}. Please select it again.`));
    reader.readAsDataURL(file);
  });
}
async function post(path, payload) {
  let response;
  try {
    response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (_) {
    throw new Error(
      "Cannot reach BatchLens. Reopen the app or restart batchlens serve. Completed reports remain in your output folder.",
    );
  }
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.error || "The audit could not be completed.");
  return data;
}
async function run(example = false) {
  if (busy || stopped) return;
  busy = true;
  update();
  $("results").hidden = true;
  status(
    "Running audit… Larger studies can take a little longer. Keep this window open.",
  );
  try {
    let result;
    if (example) result = await post(`api/demo/${$("demo-case").value}`, {});
    else {
      const entries = await Promise.all(
        Object.entries(files).map(async ([role, file]) => [
          role,
          await encode(file),
        ]),
      );
      result = await post("api/audit", { files: Object.fromEntries(entries) });
    }
    const prefix = `reports/${encodeURIComponent(result.id)}/`;
    $("download-html").href = prefix + "download.html";
    $("download-zip").href = prefix + "bundle.zip";
    $("result-summary").textContent =
      `${result.counts.samples} samples · ${result.counts.experimental_units} experimental units${result.synthetic ? " · Synthetic example: " + result.synthetic : ""}`;
    $("saved").textContent = `Saved on this computer: ${result.saved_to}`;
    $("contrast-summary").replaceChildren();
    for (const contrast of result.contrasts) {
      const badge = document.createElement("span");
      badge.className =
        "contrast " + contrast.status.toLowerCase().replaceAll("_", "-");
      badge.textContent = `${contrast.id}: ${contrast.status}`;
      $("contrast-summary").append(badge);
    }
    $("report").src = prefix + "report.html";
    $("results").hidden = false;
    status("Audit complete. Review contrast statuses and findings below.");
    $("results").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    status(error.message, true);
  } finally {
    busy = false;
    update();
  }
}
$("run").addEventListener("click", () => run());
$("demo").addEventListener("click", () => run(true));
function templates() {
  const selected = $("demo-case").value;
  const names = ["samples.tsv", "design.yaml"];
  if (selected === "spatial-replicates") names.push("observations.tsv");
  if (selected === "mixed-assays") names.push("assays.tsv");
  $("templates").replaceChildren();
  names.forEach((name) => {
    const link = document.createElement("a");
    link.href = `examples/${selected}/${name}`;
    link.download = name;
    link.textContent = name + " ↓";
    $("templates").append(link);
  });
}
$("demo-case").addEventListener("change", templates);
$("quit").addEventListener("click", async () => {
  if (busy) return;
  try {
    await post("api/quit", {});
    stopped = true;
    update();
    status(
      "BatchLens has stopped. You can close this tab. Saved reports remain on your computer.",
    );
  } catch (error) {
    status(error.message, true);
  }
});
fetch("api/info")
  .then((response) => {
    if (!response.ok) throw new Error();
    return response.json();
  })
  .then((info) => {
    $("version").textContent = `Version ${info.version} · Exploratory alpha`;
    limit = info.max_upload_bytes;
  })
  .catch(() => {
    stopped = true;
    update();
    status(
      "The local server is unavailable. Reopen BatchLens to continue.",
      true,
    );
  });
templates();
update();
