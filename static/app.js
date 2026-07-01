const selectors = {
  form: "#downloadForm",
  dependencyStatus: "#dependencyStatus",
  submitButton: "#submitButton",
  jobPanel: "#job",
  jobTitle: "#jobTitle",
  jobState: "#jobState",
  progressFill: "#progressFill",
  progressText: "#progressText",
  speedText: "#speedText",
  etaText: "#etaText",
  message: "#message",
  files: "#files",
};

const ui = Object.fromEntries(
  Object.entries(selectors).map(([key, selector]) => [key, document.querySelector(selector)])
);

let pollTimer = null;

function setSubmitState(disabled, label) {
  ui.submitButton.disabled = disabled;
  ui.submitButton.textContent = label;
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || "Request failed.");
  }

  return payload;
}

function stopPolling() {
  if (!pollTimer) return;
  clearInterval(pollTimer);
  pollTimer = null;
}

function setDependencyStatus(health) {
  ui.dependencyStatus.classList.remove("ready", "warning");

  if (!health.ytDlpInstalled) {
    ui.dependencyStatus.textContent = "Run uv sync to install yt-dlp";
    ui.dependencyStatus.classList.add("warning");
    return;
  }

  if (!health.ffmpegInstalled) {
    ui.dependencyStatus.textContent = "ffmpeg missing; 4K merges may fail";
    ui.dependencyStatus.classList.add("warning");
    return;
  }

  ui.dependencyStatus.textContent = "Ready for 4K + subtitles";
  ui.dependencyStatus.classList.add("ready");
}

async function checkHealth() {
  try {
    setDependencyStatus(await requestJson("/api/health"));
  } catch {
    ui.dependencyStatus.textContent = "Backend is not responding";
    ui.dependencyStatus.classList.add("warning");
  }
}

function renderFiles(paths) {
  ui.files.innerHTML = "";
  if (!paths || paths.length === 0) return;

  for (const path of paths) {
    const row = document.createElement("div");
    row.className = "file-row";
    row.textContent = path;
    ui.files.append(row);
  }
}

function renderJob(job) {
  ui.jobPanel.hidden = false;
  ui.jobTitle.textContent = job.title || job.url || "Preparing...";
  ui.jobState.textContent = job.status;

  const percent = Math.max(0, Math.min(100, Number(job.percent || 0)));
  ui.progressFill.style.width = `${percent}%`;
  ui.progressText.textContent = `${percent.toFixed(percent % 1 ? 1 : 0)}%`;
  ui.speedText.textContent = job.speed || "";
  ui.etaText.textContent = job.eta ? `ETA ${job.eta}` : "";
  ui.message.textContent = job.message || "";
  renderFiles(job.files);

  if (job.status === "completed" || job.status === "failed") {
    setSubmitState(false, "Start download");
    stopPolling();
  }
}

async function pollJob(id) {
  try {
    renderJob(await requestJson(`/api/jobs/${id}`));
  } catch {
    ui.message.textContent = "Lost connection to the backend.";
    setSubmitState(false, "Start download");
    stopPolling();
  }
}

function buildPayload() {
  const formData = new FormData(ui.form);
  return {
    url: String(formData.get("url") || "").trim(),
    maxHeight: Number(formData.get("maxHeight")),
    subtitleLangs: formData.get("subtitleLangs"),
    subtitleFormat: formData.get("subtitleFormat"),
    autoSubtitles: formData.get("autoSubtitles") === "on",
    embedSubtitles: formData.get("embedSubtitles") === "on",
  };
}

ui.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  stopPolling();
  setSubmitState(true, "Starting...");
  ui.files.innerHTML = "";

  try {
    const job = await requestJson("/api/downloads", {
      method: "POST",
      body: JSON.stringify(buildPayload()),
    });

    renderJob(job);
    setSubmitState(true, "Downloading...");
    pollTimer = setInterval(() => pollJob(job.id), 1000);
    pollJob(job.id);
  } catch (error) {
    ui.jobPanel.hidden = false;
    ui.jobTitle.textContent = "Download did not start";
    ui.jobState.textContent = "failed";
    ui.progressFill.style.width = "0%";
    ui.progressText.textContent = "0%";
    ui.speedText.textContent = "";
    ui.etaText.textContent = "";
    ui.message.textContent = error.message;
    setSubmitState(false, "Start download");
  }
});

checkHealth();
