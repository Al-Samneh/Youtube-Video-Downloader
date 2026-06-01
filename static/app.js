const form = document.querySelector("#downloadForm");
const dependencyStatus = document.querySelector("#dependencyStatus");
const submitButton = document.querySelector("#submitButton");
const jobPanel = document.querySelector("#job");
const jobTitle = document.querySelector("#jobTitle");
const jobState = document.querySelector("#jobState");
const progressFill = document.querySelector("#progressFill");
const progressText = document.querySelector("#progressText");
const speedText = document.querySelector("#speedText");
const etaText = document.querySelector("#etaText");
const message = document.querySelector("#message");
const files = document.querySelector("#files");

let pollTimer = null;

function setDependencyStatus(health) {
  dependencyStatus.classList.remove("ready", "warning");

  if (!health.ytDlpInstalled) {
    dependencyStatus.textContent = "Run uv sync to install yt-dlp";
    dependencyStatus.classList.add("warning");
    return;
  }

  if (!health.ffmpegInstalled) {
    dependencyStatus.textContent = "ffmpeg missing; 4K merges may fail";
    dependencyStatus.classList.add("warning");
    return;
  }

  dependencyStatus.textContent = "Ready for 4K + subtitles";
  dependencyStatus.classList.add("ready");
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    setDependencyStatus(await response.json());
  } catch {
    dependencyStatus.textContent = "Backend is not responding";
    dependencyStatus.classList.add("warning");
  }
}

function renderFiles(paths) {
  files.innerHTML = "";
  if (!paths || paths.length === 0) return;

  for (const path of paths) {
    const row = document.createElement("div");
    row.className = "file-row";
    row.textContent = path;
    files.append(row);
  }
}

function renderJob(job) {
  jobPanel.hidden = false;
  jobTitle.textContent = job.title || job.url || "Preparing...";
  jobState.textContent = job.status;

  const percent = Math.max(0, Math.min(100, Number(job.percent || 0)));
  progressFill.style.width = `${percent}%`;
  progressText.textContent = `${percent.toFixed(percent % 1 ? 1 : 0)}%`;
  speedText.textContent = job.speed || "";
  etaText.textContent = job.eta ? `ETA ${job.eta}` : "";
  message.textContent = job.message || "";
  renderFiles(job.files);

  if (job.status === "completed" || job.status === "failed") {
    submitButton.disabled = false;
    submitButton.textContent = "Download";
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function pollJob(id) {
  try {
    const response = await fetch(`/api/jobs/${id}`);
    const job = await response.json();
    renderJob(job);
  } catch {
    message.textContent = "Lost connection to the backend.";
    submitButton.disabled = false;
    submitButton.textContent = "Download";
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearInterval(pollTimer);

  const formData = new FormData(form);
  const payload = {
    url: formData.get("url"),
    maxHeight: Number(formData.get("maxHeight")),
    subtitleLangs: formData.get("subtitleLangs"),
    subtitleFormat: formData.get("subtitleFormat"),
    autoSubtitles: formData.get("autoSubtitles") === "on",
    embedSubtitles: formData.get("embedSubtitles") === "on",
  };

  submitButton.disabled = true;
  submitButton.textContent = "Starting...";
  files.innerHTML = "";

  try {
    const response = await fetch("/api/downloads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Download failed to start.");
    }

    renderJob(data);
    submitButton.textContent = "Downloading...";
    pollTimer = setInterval(() => pollJob(data.id), 1000);
    pollJob(data.id);
  } catch (error) {
    jobPanel.hidden = false;
    jobTitle.textContent = "Download did not start";
    jobState.textContent = "failed";
    progressFill.style.width = "0%";
    progressText.textContent = "0%";
    speedText.textContent = "";
    etaText.textContent = "";
    message.textContent = error.message;
    submitButton.disabled = false;
    submitButton.textContent = "Download";
  }
});

checkHealth();
