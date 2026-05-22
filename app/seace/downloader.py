from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import requests


def download_file(url: str, destination_dir: str | Path) -> Path:
    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)
    filename = Path(urlparse(url).path).name or "documento_seace"
    target = destination / filename
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    target.write_bytes(response.content)
    return target
