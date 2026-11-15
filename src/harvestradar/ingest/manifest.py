"""Provenance of every downloaded file: data/manifest.json (source, URL, date, licence, SHA-256)."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import time
from pathlib import Path

import requests

from harvestradar.paths import DATA, ROOT

MANIFEST = DATA / "manifest.json"
USER_AGENT = "HarvestRadar/0.1 (research prototype)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"files": {}}


def record(path: Path, source: str, url: str, licence: str, note: str = "") -> None:
    m = _load()
    full = Path(path).resolve()
    try:
        rel = str(full.relative_to(ROOT))
    except ValueError:
        rel = str(full.relative_to(DATA.resolve().parent)) if full.is_relative_to(DATA.resolve().parent) else str(full)
    m["files"][rel] = {
        "source": source,
        "url": url,
        "licence": licence,
        "collected_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha256(Path(path)),
        "bytes": Path(path).stat().st_size,
        **({"note": note} if note else {}),
    }
    m["files"] = dict(sorted(m["files"].items()))
    MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def record_group(key: str, source: str, url: str, licence: str, count: int, note: str = "") -> None:
    """For sources fetched as many small files (e.g. one NASA POWER request per grid cell)."""
    m = _load()
    m.setdefault("groups", {})[key] = {
        "source": source,
        "url": url,
        "licence": licence,
        "collected_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": count,
        **({"note": note} if note else {}),
    }
    MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def download(url: str, dest: Path, retries: int = 4, timeout: int = 120, params: dict | None = None) -> Path:
    """GET with retries and exponential backoff. Writes atomically."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with requests.get(url, params=params, timeout=timeout, stream=True,
                              headers={"User-Agent": USER_AGENT}) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                tmp.replace(dest)
                return dest
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"download failed after {retries} attempts: {url}: {last}")
