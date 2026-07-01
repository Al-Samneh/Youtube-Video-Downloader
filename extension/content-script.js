const BUTTON_ID = "samnehs-youtube-download-button";

function isWatchUrl() {
  const url = new URL(window.location.href);
  const host = url.hostname.replace(/^www\./, "");

  if (host === "youtu.be") {
    return url.pathname.length > 1;
  }

  return (
    host.endsWith("youtube.com") &&
    ((url.pathname === "/watch" && url.searchParams.has("v")) || url.pathname.startsWith("/shorts/"))
  );
}

function setButtonState(button, label, state = "idle") {
  button.textContent = label;
  button.dataset.state = state;
}

function startDownload(button) {
  setButtonState(button, "Sending...", "busy");

  chrome.runtime.sendMessage(
    {
      type: "start-download",
      payload: {
        url: window.location.href,
        maxHeight: 2160,
        subtitleLangs: "en.*,en",
        subtitleFormat: "srt/best",
        autoSubtitles: true,
        embedSubtitles: false,
      },
    },
    (response) => {
      if (chrome.runtime.lastError || !response?.ok) {
        setButtonState(button, "Start local app", "error");
        return;
      }

      setButtonState(button, "Sent to Samneh", "done");
      window.setTimeout(() => setButtonState(button, "Download with Samneh"), 2600);
    }
  );
}

function injectButton() {
  const existing = document.getElementById(BUTTON_ID);
  if (!isWatchUrl()) {
    existing?.remove();
    return;
  }

  if (existing) return;

  const button = document.createElement("button");
  button.id = BUTTON_ID;
  button.type = "button";
  button.textContent = "Download with Samneh";
  button.title = "Send this YouTube video to Samneh's local downloader";
  button.style.cssText = [
    "position: fixed",
    "right: 22px",
    "bottom: 22px",
    "z-index: 2147483647",
    "border: 0",
    "border-radius: 999px",
    "padding: 12px 16px",
    "background: #d9222a",
    "color: #fff",
    "box-shadow: 0 10px 28px rgba(0, 0, 0, 0.28)",
    "cursor: pointer",
    "font: 700 14px/1.2 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  ].join(";");
  button.addEventListener("click", () => startDownload(button));
  document.documentElement.append(button);
}

injectButton();
window.setInterval(injectButton, 1000);
