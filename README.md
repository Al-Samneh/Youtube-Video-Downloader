# YouTube Video Downloader

A local web app that downloads a YouTube video at the best quality available up to 4K and saves subtitles when available.

## Setup

```bash
uv sync
```

The app installs a bundled `ffmpeg` helper through `imageio-ffmpeg`, so 4K audio/video merging should work without extra setup. A system `ffmpeg` is still fine if you already have one installed.

On macOS with Homebrew:

```bash
brew install ffmpeg
```

## Run

```bash
uv run python app.py
```

Open:

```text
http://127.0.0.1:8765
```

Downloaded files are saved in `downloads/`.

Use this only for videos you own or have permission to download.
