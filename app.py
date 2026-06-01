from __future__ import annotations

import json
import os
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import unquote, urlparse

try:
    import yt_dlp
except ImportError:  # pragma: no cover - handled at runtime for first launch clarity
    yt_dlp = None

try:
    import imageio_ffmpeg
except ImportError:  # pragma: no cover - optional fallback
    imageio_ffmpeg = None


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DOWNLOAD_DIR = ROOT / "downloads"
MAX_BODY_BYTES = 32 * 1024


@dataclass
class Job:
    id: str
    url: str
    status: str = "queued"
    title: str = ""
    percent: float = 0.0
    speed: str = ""
    eta: str = ""
    message: str = ""
    output_dir: str = str(DOWNLOAD_DIR)
    files: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "status": self.status,
            "title": self.title,
            "percent": self.percent,
            "speed": self.speed,
            "eta": self.eta,
            "message": self.message,
            "outputDir": self.output_dir,
            "files": self.files,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


jobs: Dict[str, Job] = {}
jobs_lock = threading.Lock()


def now_update(job: Job) -> None:
    job.updated_at = time.time()


def parse_json_body(handler: SimpleHTTPRequestHandler) -> Dict[str, Any]:
    content_length = int(handler.headers.get("Content-Length", "0"))
    if content_length <= 0:
        return {}
    if content_length > MAX_BODY_BYTES:
        raise ValueError("Request body is too large.")
    raw = handler.rfile.read(content_length)
    return json.loads(raw.decode("utf-8"))


def json_response(handler: SimpleHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    data = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def error_response(handler: SimpleHTTPRequestHandler, message: str, status: int = 400) -> None:
    json_response(handler, {"error": message}, status)


def is_supported_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    return bool(parsed.netloc)


def compact_speed(value: Optional[float]) -> str:
    if not value:
        return ""
    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024
    return ""


def compact_eta(value: Optional[float]) -> str:
    if value is None:
        return ""
    seconds = int(value)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def collect_files(output_dir: Path, before: set[Path]) -> list[str]:
    if not output_dir.exists():
        return []
    after = {path for path in output_dir.iterdir() if path.is_file()}
    created = sorted(after - before, key=lambda item: item.stat().st_mtime)
    return [str(path) for path in created]


def ffmpeg_location() -> Optional[str]:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    if imageio_ffmpeg is None:
        return None
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def split_subtitle_langs(value: str) -> list[str]:
    langs = [part.strip() for part in value.split(",") if part.strip()]
    return langs or ["en.*", "en"]


def build_ydl_options(job: Job, output_dir: Path, payload: Dict[str, Any], before: set[Path]) -> Dict[str, Any]:
    include_auto_subs = bool(payload.get("autoSubtitles", True))
    subtitle_langs = str(payload.get("subtitleLangs") or "en.*,en").strip()
    subtitle_format = str(payload.get("subtitleFormat") or "srt/best").strip()
    max_height = int(payload.get("maxHeight") or 2160)
    embed_subtitles = bool(payload.get("embedSubtitles", False))

    # Prefer separate best video/audio up to the requested ceiling, which is how YouTube
    # commonly exposes 1440p and 2160p. Fall back to the highest single-file format.
    format_selector = (
        f"bv*[height<={max_height}]+ba/b[height<={max_height}]/"
        "bv*+ba/b"
    )

    def progress_hook(data: Dict[str, Any]) -> None:
        with jobs_lock:
            status = data.get("status")
            if status == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                downloaded = data.get("downloaded_bytes") or 0
                job.status = "downloading"
                job.percent = round((downloaded / total) * 100, 1) if total else job.percent
                job.speed = compact_speed(data.get("speed"))
                job.eta = compact_eta(data.get("eta"))
                job.message = "Downloading video and subtitles..."
            elif status == "finished":
                job.status = "processing"
                job.percent = max(job.percent, 99.0)
                job.speed = ""
                job.eta = ""
                job.message = "Merging and writing metadata..."
            now_update(job)

    postprocessors = []
    if subtitle_format.startswith("srt"):
        postprocessors.append({"key": "FFmpegSubtitlesConvertor", "format": "srt"})
    if embed_subtitles:
        postprocessors.append({"key": "FFmpegEmbedSubtitle"})

    return {
        "format": format_selector,
        "outtmpl": str(output_dir / "%(title).180B [%(id)s].%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "writesubtitles": True,
        "writeautomaticsub": include_auto_subs,
        "subtitleslangs": split_subtitle_langs(subtitle_langs),
        "subtitlesformat": subtitle_format,
        "embedsubtitles": embed_subtitles,
        "postprocessors": postprocessors,
        "progress_hooks": [progress_hook],
        "restrictfilenames": False,
        "windowsfilenames": True,
        "concurrent_fragment_downloads": 4,
        "ignoreerrors": False,
        "quiet": True,
        "no_warnings": False,
        "paths": {"home": str(output_dir)},
        "ffmpeg_location": ffmpeg_location(),
    }


def run_download(job_id: str, payload: Dict[str, Any]) -> None:
    with jobs_lock:
        job = jobs[job_id]
        job.status = "starting"
        job.message = "Preparing download..."
        now_update(job)

    if yt_dlp is None:
        with jobs_lock:
            job.status = "failed"
            job.message = "yt-dlp is not installed. Run: uv sync"
            now_update(job)
        return

    output_dir = DOWNLOAD_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    before = {path for path in output_dir.iterdir() if path.is_file()}

    with jobs_lock:
        job.output_dir = str(output_dir)
        now_update(job)

    options = build_ydl_options(job, output_dir, payload, before)
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(job.url, download=True)
            title = info.get("title") if isinstance(info, dict) else ""

        files = collect_files(output_dir, before)
        with jobs_lock:
            job.title = title or job.title
            job.status = "completed"
            job.percent = 100
            job.speed = ""
            job.eta = ""
            job.files = files
            job.message = "Download complete."
            now_update(job)
    except Exception as exc:  # yt-dlp raises several concrete exception types
        with jobs_lock:
            job.status = "failed"
            job.speed = ""
            job.eta = ""
            job.message = str(exc)
            job.files = collect_files(output_dir, before)
            now_update(job)


class DownloaderHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            json_response(
                self,
                {
                    "ok": True,
                    "ytDlpInstalled": yt_dlp is not None,
                    "ffmpegInstalled": ffmpeg_location() is not None,
                    "ffmpegLocation": ffmpeg_location(),
                    "downloadDir": str(DOWNLOAD_DIR),
                },
            )
            return

        if parsed.path.startswith("/api/jobs/"):
            job_id = unquote(parsed.path.rsplit("/", 1)[-1])
            with jobs_lock:
                job = jobs.get(job_id)
                if not job:
                    error_response(self, "Job not found.", HTTPStatus.NOT_FOUND)
                    return
                payload = job.as_dict()
            json_response(self, payload)
            return

        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/downloads":
            error_response(self, "Route not found.", HTTPStatus.NOT_FOUND)
            return

        try:
            payload = parse_json_body(self)
        except Exception as exc:
            error_response(self, f"Invalid JSON: {exc}", HTTPStatus.BAD_REQUEST)
            return

        url = str(payload.get("url") or "").strip()
        if not is_supported_url(url):
            error_response(self, "Enter a valid http(s) video URL.", HTTPStatus.BAD_REQUEST)
            return

        job_id = uuid.uuid4().hex
        job = Job(id=job_id, url=url)
        with jobs_lock:
            jobs[job_id] = job

        worker = threading.Thread(target=run_download, args=(job_id, payload), daemon=True)
        worker.start()
        json_response(self, job.as_dict(), HTTPStatus.ACCEPTED)


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), DownloaderHandler)
    print(f"Downloader running at http://{host}:{port}")
    print(f"Downloads will be saved to {DOWNLOAD_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
