from __future__ import annotations

from pathlib import Path


MANIFEST_PATH = (
    Path.home()
    / "Library/Application Support/Google/Chrome/NativeMessagingHosts/com.samneh.youtube_download.json"
)


def main() -> None:
    if MANIFEST_PATH.exists():
        MANIFEST_PATH.unlink()
        print(f"Removed native messaging host: {MANIFEST_PATH}")
    else:
        print("Native messaging host is not installed.")


if __name__ == "__main__":
    main()
