# Samneh's YouTube Download

A local YouTube downloader with a companion Chrome extension.

The Python app runs on your machine and handles downloads through `yt-dlp`. The Chrome extension is a lightweight controller that sends the current YouTube video URL to the local app. With the optional native helper installed, the extension can start the local app when you click download.

Use this only for videos you own, videos you created, or videos you otherwise have permission to download.

## Features

- Local web UI for starting and tracking downloads.
- Chrome popup for sending the active YouTube tab to the local downloader.
- Optional one-click local app startup through Chrome Native Messaging.
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

1. Open Chrome and go to `chrome://extensions`.
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select this repository's `extension` folder.
5. Copy the extension ID shown by Chrome.
6. Install the native helper:

   ```bash
   uv run python native/install_host.py
   ```

7. Paste the extension ID when prompted.
8. Restart Chrome and reload the extension.
9. Open a YouTube video page.
10. Use the extension popup or the **Download with Samneh** button on the page.

The native helper lets the extension start the local app automatically. Without it, start the app manually with:

```bash
uv run python app.py
```

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
native/
  host.py
  install_host.py
  uninstall_host.py
scripts/
  validate_project.py
downloads/
```

## Validation

```bash
uv run python -m py_compile app.py
uv run python -m py_compile native/host.py native/install_host.py native/uninstall_host.py
uv run python scripts/validate_project.py
```

## Notes

The extension does not download files by itself. It sends URLs to the local API. The native helper only starts the local Python app; downloads still happen locally through `yt-dlp`.
