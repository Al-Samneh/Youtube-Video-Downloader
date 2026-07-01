const form = document.querySelector("#downloadForm");
const health = document.querySelector("#health");
const urlInput = document.querySelector("#url");
const submitButton = document.querySelector("#submitButton");
const statusPanel = document.querySelector("#statusPanel");
const jobStatus = document.querySelector("#jobStatus");
const jobProgress = document.querySelector("#jobProgress");
const progress = document.querySelector("#progress");
const message = document.querySelector("#message");

let pollTimer = null;

function sendMessage(payload) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(payload, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }

      if (!response?.ok) {
        reject(new Error(response?.error || "Extension request failed."));
        return;
      }

      resolve(response.data);
    });
  });
}

function stopPolling() {
  if (!pollTimer) return;
  clearInterval(pollTimer);
  pollTimer = null;
}

function setHealth(label, state = "") {
  health.className = state;
  health.textContent = label;
}

function setBusy(isBusy, label) {
  submitButton.disabled = isBusy;
  submitButton.textContent = label;
}

function buildPayload() {
  const formData = new FormData(form);
  return {
    url: String(formData.get("url") || "").trim(),
    maxHeight: Number(formData.get("maxHeight")),
    subtitleLangs: formData.get("subtitleLangs"),
    subtitleFormat: "srt/best",
    autoSubtitles: formData.get("autoSubtitles") === "on",
    embedSubtitles: false,
  };
}

function renderJob(job) {
  statusPanel.hidden = false;
  const percent = Math.max(0, Math.min(100, Number(job.percent || 0)));
  jobStatus.textContent = job.status;
  jobProgress.textContent = `${percent.toFixed(percent % 1 ? 1 : 0)}%`;
  progress.value = percent;
  message.textContent = job.message || "";

  if (job.status === "completed" || job.status === "failed") {
    setBusy(false, "Send to downloader");
    stopPolling();
  }
}

async function pollJob(id) {
  try {
    renderJob(await sendMessage({ type: "job", id }));
  } catch (error) {
    message.textContent = error.message;
    setBusy(false, "Send to downloader");
    stopPolling();
  }
}

async function loadActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.url) {
    urlInput.value = tab.url;
  }
}

async function checkLocalApp() {
  try {
    const data = await sendMessage({ type: "health" });
    setHealth(data.ffmpegInstalled ? "Local app ready" : "ffmpeg missing", data.ffmpegInstalled ? "ready" : "warning");
  } catch {
    setHealth("Click download to start app", "warning");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  stopPolling();
  setBusy(true, "Starting app...");

  try {
    await sendMessage({ type: "ensure-local-app" });
    setBusy(true, "Sending...");
    const job = await sendMessage({ type: "start-download", payload: buildPayload() });
    renderJob(job);
    setBusy(true, "Downloading...");
    pollTimer = setInterval(() => pollJob(job.id), 1000);
    pollJob(job.id);
  } catch (error) {
    statusPanel.hidden = false;
    jobStatus.textContent = "failed";
    jobProgress.textContent = "0%";
    progress.value = 0;
    message.textContent = error.message;
    setBusy(false, "Send to downloader");
  }
});

loadActiveTab();
checkLocalApp();
