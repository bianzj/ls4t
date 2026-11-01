"use strict";

const state = {
  types: {},
  labels: {},
  tasks: [],
  selectedId: null,
  mode: "view", // view | edit | new
  detail: null, // {task, status, check}
  draft: null,
  check: null,
  runtime: null,
  runtimeChecks: {},
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `请求失败（${response.status}）`);
  return data;
}

let toastTimer;
function toast(message, bad = false) {
  const box = $("toast");
  box.textContent = message;
  box.classList.toggle("bad", bad);
  box.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => box.classList.remove("show"), bad ? 7000 : 3000);
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat(Infinity)) {
    if (child !== null && child !== undefined && child !== false) node.append(child.nodeType ? child : document.createTextNode(child));
  }
  return node;
}

const STATE_TEXT = { queued: "排队中", running: "运行中", done: "已完成", failed: "失败", cancelled: "已取消" };
const typeName = (kind) => (state.types[kind] ? state.types[kind].name : kind);
const baseName = (path) => (path || "").split(/[\\/]/).filter(Boolean).pop() || path || "";
const shortPath = (path) => {
  const parts = (path || "").split(/[\\/]/).filter(Boolean);
  return parts.length > 3 ? `${parts[0]}\\…\\${parts.slice(-2).join("\\")}` : path;
};
const fmtClock = (t) => (t ? new Date(t * 1000).toLocaleString("zh-CN", { hour12: false }) : "");

function duration(status) {
  if (!status || !status.started) return "";
  const seconds = Math.round((status.finished || Date.now() / 1000) - status.started);
  if (seconds < 60) return `${seconds} 秒`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分 ${seconds % 60} 秒`;
  return `${(seconds / 3600).toFixed(1)} 小时`;
}

function progress(status) {
  if (!status || !status.total) return 0;
  const c = status.counts;
  return (c.done + c.skipped + c.failed) / status.total;
}

/* ---------- task list ---------- */

function renderTaskList() {
  const items = state.tasks.map((task) => {
    const status = task.status;
    const current = state.mode !== "new" && task.id === state.selectedId;
    const stateText = status ? STATE_TEXT[status.state] || status.state : "未运行";
    const c = status && status.counts;
    return el(
      "li",
      {},
      el(
        "button",
        { type: "button", "aria-current": current ? "true" : "false", onclick: () => selectTask(task.id) },
        el("span", { class: `tag t-${task.type}`, text: typeName(task.type) }),
        el("span", { class: "name", text: task.name }),
        el("span", { class: "paths", title: `${task.input_dir} → ${task.output_dir}` }, shortPath(task.input_dir), " → ", shortPath(task.output_dir)),
        el(
          "span",
          { class: "line" },
          el("span", { class: `state s-${status ? status.state : "none"}`, text: stateText }),
          c && status.total ? el("span", { class: "nums", text: `${c.done + c.skipped + c.failed}/${status.total}${c.failed ? `　失败 ${c.failed}` : ""}` }) : null
        ),
        status && status.total ? el("span", { class: "bar" }, el("span", { style: `width:${100 * progress(status)}%` })) : null
      )
    );
  });
  if (state.mode === "new") {
    items.unshift(
      el("li", {}, el("button", { type: "button", "aria-current": "true" }, el("span", { class: "tag", text: typeName(state.draft.type) }), el("span", { class: "name", text: state.draft.name || "新任务" }), el("span", { class: "paths", text: "尚未保存" })))
    );
  }
  $("task-list").replaceChildren(...(items.length ? items : [el("li", { class: "empty", text: "还没有任务。点“新建任务”，选择要做解压、LST 反演还是 LSCT 反演。" })]));
}

async function loadTasks() {
  const data = await api("/api/tasks");
  state.tasks = data.tasks;
  renderTaskList();
}

/* ---------- task detail ---------- */

async function selectTask(id) {
  state.mode = "view";
  state.selectedId = id;
  localStorage.setItem("ls4t-task", id);
  renderTaskList();
  await loadDetail(true);
}

async function loadDetail(withCheck) {
  if (!state.selectedId) return;
  const id = state.selectedId;
  try {
    const data = await api(`/api/task?id=${encodeURIComponent(id)}${withCheck ? "" : "&check=0"}`);
    if (state.selectedId !== id || state.mode !== "view") return;
    if (!withCheck && state.detail && state.detail.task.id === id) data.check = state.detail.check;
    state.detail = data;
    renderDetail();
  } catch (error) {
    $("detail").replaceChildren(el("div", { class: "empty", text: error.message }));
  }
}

function infoRows(task) {
  const kind = state.types[task.type];
  const rows = [
    ["输入目录", task.input_dir],
    ["输出目录", task.output_dir],
    ["处理年份", task.years.join("、") || "未选"],
  ];
  if (kind.fields.includes("lai_root")) rows.push(["LAI", task.lai_root]);
  if (kind.fields.includes("tcwv_root")) rows.push(["TCWV", task.tcwv_root]);
  if (kind.fields.includes("aux_dir")) {
    rows.push(["辅助数据", task.aux_dir]);
    rows.push(["土壤发射率", `${baseName(task.soil_emis_b1)}　${baseName(task.soil_emis_b2)}`]);
    rows.push(["类型图", task.type_map]);
  }
  const options = [];
  if (kind.fields.includes("include_night")) options.push(task.include_night ? "处理夜间场景" : "跳过夜间场景");
  options.push(task.overwrite ? "覆盖已有结果" : "已有结果的场景跳过");
  rows.push(["选项", options.join("；")]);
  return el("dl", { class: "info" }, rows.map(([k, v]) => [el("dt", { text: k }), el("dd", { text: v || "—" })]));
}

function renderDetail() {
  const { task, status, check } = state.detail;
  const active = status && ["queued", "running"].includes(status.state);
  const bad = check ? Object.values(check.fields).filter((f) => !f.ok) : [];
  const box = $("detail");
  const nodes = [];
  nodes.push(
    el(
      "div",
      { class: "detail-head" },
      el("span", { class: `tag t-${task.type}`, text: typeName(task.type) }),
      el("h2", { text: task.name }),
      el(
        "div",
        { class: "buttons" },
        active
          ? el("button", { class: "primary danger-fill", type: "button", text: "取消运行", onclick: () => cancelRun(task.id) })
          : el("button", { class: "primary", type: "button", text: status ? "重新运行" : "开始运行", disabled: bad.length ? true : undefined, onclick: () => startRun(task.id) }),
        el("button", { class: "plain", type: "button", text: "编辑", disabled: active ? true : undefined, onclick: () => editTask() }),
        el("button", { class: "plain", type: "button", text: "删除", disabled: active ? true : undefined, onclick: () => deleteTask(task) })
      )
    )
  );
  nodes.push(el("p", { class: "summary", text: state.types[task.type].summary }));
  if (bad.length) {
    nodes.push(
      el(
        "div",
        { class: "problems" },
        el("strong", { text: "配置还有问题，修正后才能运行：" }),
        el("ul", {}, bad.map((f) => el("li", { text: `${f.label}：${f.message}` }))),
        el("button", { class: "plain", type: "button", text: "编辑任务", onclick: () => editTask() })
      )
    );
  }

  // execution status
  const panel = el("section", { class: "run" });
  panel.append(el("h3", { text: "执行情况" }));
  if (!status) {
    panel.append(el("p", { class: "muted", text: bad.length ? "还没有运行过。" : "还没有运行过。点“开始运行”处理所选年份的全部场景；已有结果的场景会自动跳过。" }));
  } else {
    const c = status.counts;
    const finished = c.done + c.skipped + c.failed;
    panel.append(
      el(
        "div",
        { class: "run-head" },
        el("span", { class: `big s-${status.state}`, text: STATE_TEXT[status.state] || status.state }),
        status.total != null ? el("span", { class: "fraction" }, el("b", { text: String(finished) }), ` / ${status.total} 景`) : el("span", { class: "fraction", text: status.state === "running" ? "正在统计场景…" : "" }),
        el("span", { class: "when", text: status.started ? `开始 ${fmtClock(status.started)}　用时 ${duration(status)}` : `排队于 ${fmtClock(status.queued)}` })
      ),
      el("div", { class: "bar big" }, el("span", { style: `width:${status.state === "done" ? 100 : 100 * progress(status)}%` })),
      el(
        "div",
        { class: "counts" },
        el("span", {}, el("i", { class: "k-done" }), `完成 ${c.done}`),
        el("span", {}, el("i", { class: "k-skip" }), `跳过 ${c.skipped}`),
        el("span", {}, el("i", { class: "k-fail" }), `失败 ${c.failed}`),
        status.state === "running" && status.current ? el("span", { class: "current", text: `正在处理 ${status.current}` }) : null
      )
    );
    if (status.failures && status.failures.length) {
      panel.append(
        el("h4", { text: `失败的场景（${status.failures.length}）` }),
        el("div", { class: "failures" }, el("table", {}, el("tbody", {}, status.failures.map((f) => el("tr", {}, el("td", { class: "scene", text: f.scene }), el("td", { text: f.message }))))))
      );
    }
    const log = el("pre", { class: "log", text: (status.log || []).join("\n") || "（暂无输出）" });
    panel.append(el("h4", {}, "日志", status.log_file ? el("span", { class: "muted", text: `　${status.log_file}` }) : null), log);
  }
  nodes.push(panel);
  nodes.push(el("section", { class: "config" }, el("h3", { text: "配置" }), infoRows(task)));

  const previousLog = box.querySelector("pre.log");
  const stick = !previousLog || previousLog.scrollTop + previousLog.clientHeight >= previousLog.scrollHeight - 4;
  box.replaceChildren(...nodes);
  const log = box.querySelector("pre.log");
  if (log && stick) log.scrollTop = log.scrollHeight;
}

async function startRun(id) {
  try {
    await api("/api/task/run", { method: "POST", body: { id } });
    toast("已开始运行");
    await Promise.all([loadTasks(), loadDetail(false)]);
  } catch (error) {
    toast(error.message, true);
  }
}

async function cancelRun(id) {
  try {
    await api("/api/task/cancel", { method: "POST", body: { id } });
    toast("已请求取消");
    await Promise.all([loadTasks(), loadDetail(false)]);
  } catch (error) {
    toast(error.message, true);
  }
}

async function deleteTask(task) {
  if (!confirm(`从列表中删除任务“${task.name}”？\n\n只删除任务记录，输出目录里的数据不会被删除。`)) return;
  try {
    await api("/api/task/delete", { method: "POST", body: { id: task.id } });
    toast("已删除任务");
    state.selectedId = null;
    await loadTasks();
    if (state.tasks.length) selectTask(state.tasks[0].id);
    else showWelcome();
  } catch (error) {
    toast(error.message, true);
  }
}

function showWelcome() {
  state.detail = null;
  $("detail").replaceChildren(
    el("div", { class: "welcome" }, el("h2", { text: "新建一个任务开始" }), el("p", { text: "任务有三种：解压、LST 反演、LSCT 反演。每个任务选择输入目录和输出目录，以及需要的全球数据，然后运行。" }), el("button", { class: "primary", type: "button", text: "新建任务", onclick: () => newTask() }))
  );
}

/* ---------- edit form ---------- */

async function newTask(kind) {
  const type = kind || (state.draft && state.mode === "new" ? state.draft.type : "lst");
  const template = (await api(`/api/template?type=${type}`)).task;
  state.mode = "new";
  state.draft = template;
  state.check = null;
  renderTaskList();
  renderForm();
  runCheck();
}

function editTask() {
  state.mode = "edit";
  state.draft = { ...state.detail.task };
  state.check = state.detail.check || null;
  renderTaskList();
  renderForm();
  if (!state.check) runCheck();
}

function draftFromForm() {
  const draft = { ...state.draft };
  for (const key of ["name", "input_dir", "output_dir", "lai_root", "tcwv_root", "aux_dir", "type_map", "soil_emis_b1", "soil_emis_b2"]) {
    const input = $(`f-${key}`);
    if (input) draft[key] = input.value;
  }
  for (const key of ["include_night", "overwrite"]) {
    const input = $(`f-${key}`);
    if (input) draft[key] = input.checked;
  }
  if (document.querySelector("#detail input[data-year]") || state.check) {
    draft.years = [...document.querySelectorAll("#detail input[data-year]:checked")].map((i) => i.dataset.year);
  }
  return draft;
}

let checkTimer;
function scheduleCheck() {
  state.draft = draftFromForm();
  clearTimeout(checkTimer);
  checkTimer = setTimeout(runCheck, 350);
}

async function runCheck() {
  const draft = state.draft;
  try {
    const check = await api("/api/task/check", { method: "POST", body: { task: draft } });
    if (draft !== state.draft || state.mode === "view") return; // a newer edit is being checked
    // keep what was typed while the check ran; the next change event re-checks it
    if ($("task-form")) state.draft = draftFromForm();
    const suggest = check.suggest || {};
    for (const key of ["soil_emis_b1", "soil_emis_b2"]) if (!state.draft[key] && suggest[key]) state.draft[key] = suggest[key];
    // a single available year is the obvious choice
    if (!state.draft.years.length && check.years_available.length === 1) {
      state.draft.years = [check.years_available[0].year];
      state.check = check;
      renderForm(true);
      return scheduleCheck();
    }
    state.check = check;
    renderForm(true);
    if (state.mode === "new") renderTaskList();
  } catch (error) {
    toast(error.message, true);
  }
}

function status(key) {
  const f = state.check && state.check.fields[key];
  if (!f) return el("span", { class: "check-wait", text: state.check ? "" : "检查中" });
  return el("span", { class: f.ok ? "check-ok" : "check-bad", text: f.message || (f.ok ? "已找到" : "未找到") });
}

function pathField(key, mode, hint) {
  const id = `f-${key}`;
  const label = state.labels[key];
  const input = el("input", { id, value: state.draft[key] || "", onchange: scheduleCheck });
  return [
    el("label", { for: id, text: label }),
    el("div", { class: "row" }, input, el("button", { class: "plain", type: "button", text: "浏览", onclick: () => pick(input, mode, label) })),
    el("div", { class: "hint" }, status(key), hint ? ["　", hint] : null),
  ];
}

function renderForm(keepFocus = false) {
  const activeId = keepFocus && document.activeElement ? document.activeElement.id : null;
  const d = state.draft;
  const kind = state.types[d.type];
  const check = state.check || { years_available: [], years: {}, emissivity: [] };
  const rows = [];

  rows.push(el("label", { text: "任务类型" }));
  rows.push(
    el(
      "div",
      { class: "types", role: "radiogroup" },
      Object.entries(state.types).map(([key, value]) =>
        el(
          "button",
          {
            type: "button",
            role: "radio",
            "aria-checked": key === d.type ? "true" : "false",
            class: `type-choice t-${key}`,
            onclick: () => {
              state.draft = { ...draftFromForm(), type: key, years: [] };
              state.check = null;
              renderForm();
              runCheck();
            },
          },
          el("b", { text: value.name }),
          el("small", { text: value.summary })
        )
      )
    )
  );
  rows.push(el("label", { for: "f-name", text: state.labels.name }), el("input", { id: "f-name", value: d.name || "", placeholder: `例如 北京 2023 ${kind.name}`, onchange: scheduleCheck }));
  rows.push(el("div", { class: "hint" }, status("name")));

  rows.push(el("h3", { text: "目录" }));
  rows.push(...pathField("input_dir", "dir", `${kind.input}：${kind.input_hint}`));
  rows.push(...pathField("output_dir", "dir", kind.output_hint));

  rows.push(el("label", { text: state.labels.years }));
  const years = check.years_available || [];
  rows.push(
    years.length
      ? el(
          "div",
          { class: "years" },
          years.map(({ year, scenes }) => {
            const flags = check.years[year] || {};
            const missing = [flags.lai === false ? "缺 LAI" : "", flags.tcwv === false ? "缺 TCWV" : ""].filter(Boolean).join("、");
            return el(
              "label",
              { class: `year${missing ? " bad" : ""}` },
              el("input", { type: "checkbox", "data-year": year, checked: (d.years || []).includes(year), onchange: scheduleCheck }),
              ` ${year}`,
              el("small", { text: `　${scenes} 景${missing ? "　" + missing : ""}` })
            );
          })
        )
      : el("span", { class: "muted", text: "选好输入目录后，这里会列出有数据的年份。" })
  );
  rows.push(el("div", { class: "hint" }, status("years")));

  if (kind.fields.includes("lai_root")) {
    rows.push(el("h3", { text: "全球数据" }));
    rows.push(...pathField("lai_root", "dir", "全球 0.01° LAI：年份/LAI_YYYYDDD.h5，或分在 lai_2002-2020_0p01deg、lai_2021-2025_0p01deg 里。"));
    if (kind.fields.includes("tcwv_root")) rows.push(...pathField("tcwv_root", "dir", "全球 ERA5 小时 TCWV：年份/tcwv_YYYYMMDD.h5。"));
    rows.push(...pathField("aux_dir", "dir", d.type === "lst" ? "需包含土壤发射率、IGBP_Emi.txt 和 Seebor 分裂窗系数。" : "需包含土壤发射率和 IGBP_Emi.txt。"));
    const options = check.emissivity || [];
    for (const [key, hint] of [
      ["soil_emis_b1", "对应 S8（约 10.8 μm），生产使用 MODIS LSE11"],
      ["soil_emis_b2", "对应 S9（约 12 μm），生产使用 MODIS LSE12"],
    ]) {
      const value = d[key] || "";
      const choices = options.includes(value) || !value ? options : [value, ...options];
      rows.push(
        el("label", { for: `f-${key}`, text: state.labels[key] }),
        el(
          "select",
          { id: `f-${key}`, onchange: scheduleCheck },
          el("option", { value: "", text: choices.length ? "选择辅助数据目录里的一个文件" : "辅助数据目录里没有 .tif 文件" }),
          choices.map((path) => el("option", { value: path, selected: path === value, text: baseName(path) }))
        ),
        el("div", { class: "hint" }, status(key), "　", hint)
      );
    }
    rows.push(...pathField("type_map", "file", "0.01° 全球 IGBP 类型图，例如 type_world_1000.tif。"));
  }

  rows.push(el("h3", { text: "选项" }));
  if (kind.fields.includes("include_night")) {
    rows.push(el("label", { for: "f-include_night", text: state.labels.include_night }), el("input", { id: "f-include_night", type: "checkbox", checked: !!d.include_night, onchange: scheduleCheck }));
    rows.push(el("div", { class: "hint", text: "生产算法只有白天的分裂窗系数；勾选后夜间场景也套用白天系数。" }));
  }
  rows.push(el("label", { for: "f-overwrite", text: state.labels.overwrite }), el("input", { id: "f-overwrite", type: "checkbox", checked: !!d.overwrite, onchange: scheduleCheck }));
  rows.push(el("div", { class: "hint", text: "不勾选时，输出目录里已有结果的场景会跳过，中断后再运行会接着做。" }));

  const bad = Object.values((state.check && state.check.fields) || {}).filter((f) => !f.ok);
  $("detail").replaceChildren(
    el("div", { class: "detail-head" }, el("h2", { text: state.mode === "new" ? "新建任务" : `编辑：${state.detail.task.name}` })),
    el("div", { class: "form", id: "task-form" }, rows),
    el(
      "div",
      { class: "actions sticky" },
      el("button", { class: "primary", type: "button", text: state.mode === "new" ? "创建任务" : "保存", onclick: saveTask }),
      el("button", { class: "plain", type: "button", text: "取消", onclick: cancelEdit }),
      el("span", { class: "note", text: !state.check ? "检查中…" : bad.length ? `还有 ${bad.length} 项需要处理；可以先保存，处理好后才能运行` : "配置完整，可以运行" })
    )
  );
  if (activeId && $(activeId)) $(activeId).focus();
}

async function saveTask() {
  state.draft = draftFromForm();
  try {
    const data = await api("/api/task/save", { method: "POST", body: { id: state.mode === "edit" ? state.detail.task.id : null, task: state.draft } });
    toast(state.mode === "new" ? `已创建任务“${data.task.name}”` : "已保存");
    state.mode = "view";
    await loadTasks();
    await selectTask(data.task.id);
  } catch (error) {
    toast(error.message, true);
  }
}

function cancelEdit() {
  state.mode = "view";
  if (state.selectedId && state.tasks.some((t) => t.id === state.selectedId)) selectTask(state.selectedId);
  else if (state.tasks.length) selectTask(state.tasks[0].id);
  else {
    renderTaskList();
    showWelcome();
  }
}

/* ---------- runtime ---------- */

async function openRuntime() {
  const data = await api("/api/runtime");
  state.runtime = data.runtime;
  state.runtimeChecks = data.checks;
  renderRuntimeForm();
  $("settings").showModal();
}

function renderRuntimeForm() {
  const rows = [];
  for (const key of ["python", "workers"]) {
    const check = state.runtimeChecks[key] || {};
    const id = `s-${key}`;
    const input = el("input", { id, value: state.runtime[key], type: key === "workers" ? "number" : "text", min: key === "workers" ? 1 : undefined });
    const control = key === "workers" ? input : el("div", { class: "row" }, input, el("button", { class: "plain", type: "button", text: "浏览", onclick: () => pick(input, "file", check.label) }));
    rows.push(el("label", { for: id, text: check.label || key }), control);
    const hint = key === "python" ? "需装有 GDAL、netCDF4、h5py、OpenCV、scikit-learn。" : "同时处理的场景数。LST 每个进程约占 5 GB 内存。";
    rows.push(el("div", { class: "hint" }, el("span", { class: check.ok ? "check-ok" : "check-bad", text: check.message || (check.ok ? "已找到" : "未找到") }), "　", hint));
  }
  $("settings-form").replaceChildren(...rows);
}

async function saveRuntime() {
  try {
    const data = await api("/api/runtime", { method: "POST", body: { runtime: { python: $("s-python").value, workers: Number($("s-workers").value) } } });
    state.runtime = data.runtime;
    state.runtimeChecks = data.checks;
    renderRuntimeForm();
    toast("已保存运行环境");
  } catch (error) {
    toast(error.message, true);
  }
}

/* ---------- path picker ---------- */

let pickerTarget = null;
let pickerMode = "dir";

async function pick(input, mode, label) {
  pickerTarget = input;
  pickerMode = mode;
  $("picker-title").textContent = `选择${label || "位置"}`;
  $("picker").showModal();
  let start = input.value;
  if (mode === "file" && start) start = start.replace(/[\\/][^\\/]*$/, "");
  await browse(start);
}

async function browse(path) {
  try {
    const data = await api(`/api/fs?path=${encodeURIComponent(path)}`);
    $("picker-path").value = data.path;
    $("picker-up").disabled = data.parent === null;
    $("picker-up").onclick = () => browse(data.parent || "");
    const items = data.entries.filter((e) => e.dir || pickerMode === "file");
    const choose = (entry) => (entry.dir ? browse(entry.path) : ($("picker-path").value = entry.path));
    $("picker-list").replaceChildren(
      ...(items.length
        ? items.map((entry) => el("div", { class: "pick", tabindex: 0, onclick: () => choose(entry), onkeydown: (e) => e.key === "Enter" && choose(entry) }, entry.dir ? "▸ " : "　", entry.name))
        : [el("div", { class: "empty", text: "这个目录是空的。" })])
    );
  } catch (error) {
    toast(error.message, true);
  }
}

/* ---------- boot ---------- */

async function poll() {
  try {
    await loadTasks();
    if (state.mode === "view" && state.selectedId) {
      const task = state.tasks.find((t) => t.id === state.selectedId);
      const shown = state.detail && state.detail.status;
      const changed = JSON.stringify(task && task.status && [task.status.state, task.status.counts, task.status.total]) !== JSON.stringify(shown && [shown.state, shown.counts, shown.total]);
      if (changed || (task && task.status && task.status.state === "running")) loadDetail(false);
    }
  } catch (error) {
    /* server restarting; keep polling */
  }
}

async function boot() {
  try {
    const types = await api("/api/types");
    state.types = types.types;
    state.labels = types.labels;
    await loadTasks();
    const remembered = localStorage.getItem("ls4t-task");
    const first = state.tasks.find((t) => t.id === remembered) || state.tasks[0];
    if (first) await selectTask(first.id);
    else showWelcome();
    setInterval(poll, 2000);
  } catch (error) {
    toast(`无法连接后端：${error.message}`, true);
  }
}

$("new-task").addEventListener("click", () => newTask());
$("open-settings").addEventListener("click", () => openRuntime().catch((e) => toast(e.message, true)));
$("close-settings").addEventListener("click", () => $("settings").close());
$("save-settings").addEventListener("click", saveRuntime);
$("picker-cancel").addEventListener("click", () => $("picker").close());
$("picker-ok").addEventListener("click", () => {
  if (pickerTarget) {
    pickerTarget.value = $("picker-path").value;
    pickerTarget.dispatchEvent(new Event("change"));
  }
  $("picker").close();
});
$("picker-path").addEventListener("keydown", (e) => e.key === "Enter" && browse(e.target.value));

boot();
