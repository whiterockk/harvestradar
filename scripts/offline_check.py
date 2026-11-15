"""Offline check: start the app, open every page (and play the map), record every network request,
fail if any request leaves localhost. Fonts, images, map, Plotly and scripts must all be local.

Usage: python scripts/offline_check.py [--url http://localhost:8502]
"""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from capture import SHOTS, chromium_path, start_app, wait_up  # noqa: E402

LOCAL = {"localhost", "127.0.0.1", "0.0.0.0", "::1", ""}


def main() -> None:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8502")
    a = ap.parse_args()
    proc = None
    if not wait_up(a.url, 2):
        proc = start_app(int(a.url.rsplit(":", 1)[-1]))
        if not wait_up(a.url):
            sys.exit("app did not start")
    external, total, fonts = [], 0, set()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=chromium_path())
            ctx = b.new_context(viewport={"width": 1920, "height": 1080})

            def on_request(req):
                nonlocal total
                total += 1
                u = urlparse(req.url)
                if u.scheme in ("data", "blob", "about", "chrome-extension"):
                    return
                if u.hostname not in LOCAL:
                    external.append(req.url)
                if req.url.endswith(".woff2"):
                    fonts.add(req.url.rsplit("/", 1)[-1])

            ctx.on("request", on_request)
            page = ctx.new_page()
            for name, q in SHOTS.items():
                page.goto(f"{a.url}/?{q}", wait_until="networkidle")
                page.wait_for_timeout(2500)
                for fr in page.frames:  # press play in the map iframes
                    btn = fr.query_selector("button.play")
                    if btn:
                        btn.click()
                page.wait_for_timeout(1500)
                print(f"checked {name}")
            b.close()
    finally:
        if proc:
            proc.terminate()
    print(f"{total} requests, {len(external)} external, fonts loaded: {sorted(fonts)}")
    if external:
        for u in sorted(set(external)):
            print("EXTERNAL:", u)
        sys.exit(1)
    print("OFFLINE CHECK PASSED: 0 external requests")


if __name__ == "__main__":
    main()
