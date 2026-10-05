"""Fetch versioned frontend dependencies; committed copies support offline use."""

from pathlib import Path
import re
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
ASSETS = {
    "static/vendor/bootstrap/bootstrap.min.css": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
    "static/vendor/bootstrap/bootstrap.bundle.min.js": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
    "static/vendor/bootstrap/LICENSE": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/LICENSE",
    "static/vendor/chartjs/chart.umd.js": "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.js",
    "static/vendor/chartjs/LICENSE.md": "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/LICENSE.md",
}

if __name__ == "__main__":
    for name, url in ASSETS.items():
        with urlopen(url, timeout=45) as response:
            content = response.read()
        if name.endswith((".css", ".js")):
            # Avoid references to optional source maps that are not bundled.
            content = re.sub(rb"/\*# sourceMappingURL=.*?\*/", b"", content)
            content = re.sub(rb"//# sourceMappingURL=[^\r\n]*", b"", content)
            content = content.rstrip() + b"\n"
        target = ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        print(f"Saved {name} ({len(content):,} bytes)")
