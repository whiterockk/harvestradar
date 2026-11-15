"""Capture every page in an exact state at 1920 x 1080 (device scale factor 2 by default).

Usage: python scripts/capture.py [--url http://localhost:8501] [--out captures] [--scale 2]
Starts the app itself if nothing answers on --url. Uses ?capture=1 (animations frozen, hovers off).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = {
    "01_stress_map": "page=stress&crop=maize",
    "02_commodity": "page=commodity&crop=maize",
    "03_replay_2012": "page=replay&episode=us_drought_2012",
    "04_weekly_note": "page=note&crop=maize",
    "05_method": "page=method",
    "06_stress_map_cocoa": "page=stress&crop=cocoa",
    "07_replay_frost_2021": "page=replay&episode=brazil_frost_2021",
    "08_replay_cocoa": "page=replay&episode=cocoa_2023_2024",
}


def chromium_path() -> str | None:
    for p in sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux*/chrome")):
        return str(p)
    return os.environ.get("CHROMIUM_PATH")


def wait_up(url: str, timeout: float = 60) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            urllib.request.urlopen(url + "/_stcore/health", timeout=2)
            return True
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    return False


def start_app(port: int) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "src/harvestradar/app/streamlit_app.py"),
                             "--server.port", str(port), "--server.headless", "true"], cwd=ROOT,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8501")
    ap.add_argument("--out", default=str(ROOT / "captures"))
    ap.add_argument("--scale", type=float, default=2)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--wait", type=float, default=4.0)
    a = ap.parse_args()
    proc = None
    if not wait_up(a.url, 2):
        proc = start_app(int(a.url.rsplit(":", 1)[-1]))
        if not wait_up(a.url):
            sys.exit("app did not start")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=chromium_path())
            ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=a.scale)
            page = ctx.new_page()
            for name, q in SHOTS.items():
                if a.only and name not in a.only:
                    continue
                page.goto(f"{a.url}/?{q}&capture=1", wait_until="networkidle")
                page.wait_for_timeout(int(a.wait * 1000))
                page.screenshot(path=str(out / f"{name}.png"))
                print("captured", out / f"{name}.png")
            b.close()
    finally:
        if proc:
            proc.terminate()


if __name__ == "__main__":
    main()
