const API_BASE = "http://127.0.0.1:8765";
const NATIVE_HOST = "com.samneh.youtube_download";

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || "Request failed.");
  }

  return payload;
}

function sendNativeMessage(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendNativeMessage(NATIVE_HOST, message, (response) => {
      if (chrome.runtime.lastError) {
        const errorMessage = chrome.runtime.lastError.message || "";
        if (errorMessage.includes("Specified native messaging host not found")) {
          reject(new Error("Native helper is not installed. Run: uv run python native/install_host.py, then restart Chrome."));
          return;
        }

        reject(new Error(errorMessage));
        return;
      }

      if (!response?.ok) {
        reject(new Error(response?.error || "Native helper failed."));
        return;
      }

      resolve(response);
    });
  });
}

async function ensureLocalApp() {
  try {
    return await requestJson("/api/health");
  } catch {
    const response = await sendNativeMessage({ type: "start" });
    return response.health;
  }
}

async function handleMessage(message) {
  switch (message?.type) {
    case "health":
      return requestJson("/api/health");
    case "ensure-local-app":
      return ensureLocalApp();
    case "start-download":
      await ensureLocalApp();
      return requestJson("/api/downloads", {
        method: "POST",
        body: JSON.stringify(message.payload),
      });
    case "job":
      return requestJson(`/api/jobs/${encodeURIComponent(message.id)}`);
    default:
      throw new Error("Unknown extension message.");
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  handleMessage(message)
    .then((data) => sendResponse({ ok: true, data }))
    .catch((error) => sendResponse({ ok: false, error: error.message }));

  return true;
});
