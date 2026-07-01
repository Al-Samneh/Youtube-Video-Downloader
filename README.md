# Samneh's YouTube Download

A local YouTube downloader with a companion Chrome extension.

The Python app runs on your machine and handles downloads through `yt-dlp`. The Chrome extension is a lightweight controller that sends the current YouTube video URL to the local app.

Use this only for videos you own, videos you created, or videos you otherwise have permission to download.

## Features

- Local web UI for starting and tracking downloads.
- Chrome popup for sending the active YouTube tab to the local downloader.
- YouTube page button on watch pages.
- 4K/2160p quality option when available.
- Subtitle download with automatic captions fallback.
- Local-only API at `http://127.0.0.1:8765`.

## Setup

```bash
uv sync
```

The project uses `imageio-ffmpeg` as a bundled ffmpeg fallback. A system ffmpeg install is also supported.

On macOS with Homebrew:

```bash
brew install ffmpeg
```

## Run the Local App

```bash
uv run python app.py
```

Open:

```text
http://127.0.0.1:8765
```

Downloaded files are saved in `downloads/`.

## Install the Chrome Extension

1. Start the local app with `uv run python app.py`.
2. Open Chrome and go to `chrome://extensions`.
3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select this repository's `extension` folder.
6. Open a YouTube video page.
7. Use the extension popup or the **Download with Samneh** button on the page.

## Project Structure

```text
app.py
static/
  index.html
  app.js
  styles.css
extension/
  manifest.json
  background.js
  content-script.js
  popup.html
  popup.css
  popup.js
  icons/
scripts/
  validate_project.py
downloads/
```

## Validation

```bash
uv run python -m py_compile app.py
uv run python scripts/validate_project.py
```

## Notes

The extension does not download files by itself. It requires the local app to be running and only sends URLs to the local API.
