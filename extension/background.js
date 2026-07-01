const API_BASE = "http://127.0.0.1:8765";

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

async function handleMessage(message) {
  switch (message?.type) {
    case "health":
      return requestJson("/api/health");
    case "start-download":
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
