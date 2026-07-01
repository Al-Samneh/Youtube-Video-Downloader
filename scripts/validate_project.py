from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTENSION_DIR = ROOT / "extension"
EXPECTED_EXTENSION_ID = "kcgjfiidlebnkcndbkafmgfdjgpcmabk"


def fail(message: str) -> None:
    raise SystemExit(f"Validation failed: {message}")


def require_file(path: Path) -> None:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")


def validate_extension() -> None:
    manifest_path = EXTENSION_DIR / "manifest.json"
    require_file(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if manifest.get("manifest_version") != 3:
        fail("extension manifest must use Manifest V3")

    if not manifest.get("key"):
        fail(f"extension manifest must include the stable key for {EXPECTED_EXTENSION_ID}")

    for icon_path in manifest.get("icons", {}).values():
        require_file(EXTENSION_DIR / icon_path)

    for icon_path in manifest.get("action", {}).get("default_icon", {}).values():
        require_file(EXTENSION_DIR / icon_path)

    for script in manifest.get("content_scripts", []):
        for script_path in script.get("js", []):
            require_file(EXTENSION_DIR / script_path)

    background = manifest.get("background", {}).get("service_worker")
    if background:
        require_file(EXTENSION_DIR / background)

    popup = manifest.get("action", {}).get("default_popup")
    if popup:
        require_file(EXTENSION_DIR / popup)


def main() -> None:
    require_file(ROOT / "app.py")
    require_file(ROOT / "static" / "index.html")
    require_file(ROOT / "static" / "app.js")
    require_file(ROOT / "static" / "styles.css")
    require_file(ROOT / "native" / "host.py")
    require_file(ROOT / "native" / "install_host.py")
    require_file(ROOT / "native" / "uninstall_host.py")
    validate_extension()
    print("Project validation passed.")


if __name__ == "__main__":
    main()
