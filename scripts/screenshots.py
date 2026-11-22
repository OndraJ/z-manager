"""Log in to a running instance and take full-page screenshots of the given paths.

Used by `make verify-shots`; needs Playwright (`uv run --with playwright`).
Reports HTTP errors and browser console errors so broken pages are noticed even
without looking at the images.

Usage: python scripts/screenshots.py --base URL --out DIR --user U --password P PATH...
"""

import argparse
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def file_name(path: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", path).strip("-")
    return f"{slug or 'home'}.png"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--width", type=int, default=1366)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    problems = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": 800})
        page.on(
            "console",
            lambda msg: msg.type == "error" and problems.append(f"console: {msg.text}"),
        )
        page.on(
            "response",
            lambda r: r.status >= 400 and problems.append(f"HTTP {r.status}: {r.url}"),
        )

        page.goto(f"{args.base}/login/")
        page.fill("#id_username", args.user)
        page.fill("#id_password", args.password)
        page.click("form button[type=submit]")
        page.wait_for_load_state("networkidle")

        for path in args.paths:
            page.goto(f"{args.base}{path}")
            page.wait_for_load_state("networkidle")
            target = args.out / file_name(path)
            page.screenshot(path=target, full_page=True)
            print(f"{path} -> {target}")
        browser.close()

    for problem in problems:
        print(f"PROBLEM {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
