from __future__ import annotations

import json
import os
import re
from pathlib import Path


HOST_NAME = "com.samneh.youtube_download"
DEFAULT_EXTENSION_ID = "kcgjfiidlebnkcndbkafmgfdjgpcmabk"
ROOT = Path(__file__).resolve().parents[1]
HOST_PATH = ROOT / "native" / "host.py"
MANIFEST_DIR = Path.home() / "Library/Application Support/Google/Chrome/NativeMessagingHosts"
MANIFEST_PATH = MANIFEST_DIR / f"{HOST_NAME}.json"
EXTENSION_ID_PATTERN = re.compile(r"^[a-p]{32}$")


def read_extension_id() -> str:
    extension_id = os.environ.get("EXTENSION_ID", "").strip()
    if extension_id:
        return extension_id

    return DEFAULT_EXTENSION_ID


def main() -> None:
    extension_id = read_extension_id()
    if not EXTENSION_ID_PATTERN.match(extension_id):
        raise SystemExit("Invalid extension ID. It should be 32 lowercase letters from a-p.")

    HOST_PATH.chmod(0o755)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "name": HOST_NAME,
                "description": "Starts Samneh's YouTube Download local app.",
                "path": str(HOST_PATH),
                "type": "stdio",
                "allowed_origins": [f"chrome-extension://{extension_id}/"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Installed native messaging host: {MANIFEST_PATH}")
    print(f"Allowed Chrome extension ID: {extension_id}")
    print("Restart Chrome, then reload the extension.")


if __name__ == "__main__":
    main()
