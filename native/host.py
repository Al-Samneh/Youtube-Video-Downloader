#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
API_HEALTH_URL = "http://127.0.0.1:8765/api/health"
LOG_DIR = ROOT / "logs"
LOG_PATH = LOG_DIR / "samneh-youtube-download.log"


def read_message() -> dict:
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        raise SystemExit(0)
    if len(raw_length) != 4:
        raise ValueError("Invalid native message length.")

    message_length = struct.unpack("<I", raw_length)[0]
    return json.loads(sys.stdin.buffer.read(message_length).decode("utf-8"))


def write_message(payload: dict) -> None:
    encoded = json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def health(timeout: float = 1.0) -> dict | None:
    try:
        with urlopen(API_HEALTH_URL, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError):
        return None


def start_app() -> dict:
    current_health = health()
    if current_health:
        return current_health

    uv_path = shutil.which("uv")
    if not uv_path:
        raise RuntimeError("uv is not installed or is not on PATH.")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_PATH.open("ab")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    subprocess.Popen(
        [uv_path, "run", "python", "app.py"],
        cwd=ROOT,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        current_health = health(timeout=0.5)
        if current_health:
            return current_health
        time.sleep(0.25)

    raise RuntimeError(f"Local app did not start. Check {LOG_PATH}.")


def handle_message(message: dict) -> dict:
    message_type = message.get("type")
    if message_type == "health":
        current_health = health()
        return {"ok": bool(current_health), "health": current_health}
    if message_type == "start":
        return {"ok": True, "health": start_app()}

    raise ValueError("Unknown native helper message.")


def main() -> None:
    try:
        write_message(handle_message(read_message()))
    except Exception as exc:
        write_message({"ok": False, "error": str(exc)})


if __name__ == "__main__":
    main()
