# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.49"]
# ///
"""Drive a real headless Chromium through a scenario and keep the evidence.

    uv run browse.py --out DIR --url http://127.0.0.1:8000/
    uv run browse.py --out DIR --script scenario.json

A scenario is a JSON list of steps, each `{"action": ..., ...}`:

    goto          url
    click         selector
    fill          selector, value
    type          selector, text            (real keystrokes)
    press         key [, selector]
    select        selector, value
    check         selector
    uncheck       selector
    hover         selector
    upload        selector, files
    wait_for      selector [, state=visible]
    wait          ms
    expect_text   text [, selector]         text is visible
    expect_no_text text
    expect_url    contains
    expect_count  selector, count
    expect_value  selector, value
    eval          expression                result is stored in the report
    screenshot    name [, full_page=true]

Selectors are Playwright selectors: CSS, `text=Save`, `role=button[name="Save"]`.
Any step accepts `timeout_ms`.

Written to DIR: `result.json` (every step, console errors, uncaught page
errors, failed requests), one PNG per screenshot step plus `final.png` (or
`failure.png`), and `page.txt` with the visible text at the end.

Exit code 0 when every step succeeded, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import playwright
from playwright.sync_api import Error, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeout


def use_working_node() -> None:
    """Playwright ships its own Node binary. On machines where that binary
    cannot start (a missing system library such as libatomic), use the Node
    that is on PATH instead."""
    if os.environ.get("PLAYWRIGHT_NODEJS_PATH"):
        return
    bundled = Path(playwright.__file__).parent / "driver" / "node"
    try:
        works = (
            subprocess.run(
                [str(bundled), "--version"], capture_output=True, timeout=20, check=False
            ).returncode
            == 0
        )
    except (OSError, subprocess.TimeoutExpired):
        works = False
    if works:
        return
    system_node = shutil.which("node")
    if not system_node:
        sys.exit(
            "[browse] Playwright's bundled Node.js cannot start on this machine and "
            "no `node` is on PATH. Install Node.js, or the missing system library "
            "(run the bundled binary to see which: " + str(bundled) + ")."
        )
    os.environ["PLAYWRIGHT_NODEJS_PATH"] = system_node


def launch(pw, headed: bool):
    try:
        return pw.chromium.launch(headless=not headed)
    except Error as exc:
        if "Executable doesn't exist" not in str(exc):
            raise
        print("[browse] installing Chromium for Playwright (first run)...", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return pw.chromium.launch(headless=not headed)


def run_step(page, step: dict, out: Path, default_timeout: int, shots: list[str]):
    action = step["action"]
    timeout = step.get("timeout_ms", default_timeout)
    selector = step.get("selector")

    if action == "goto":
        response = page.goto(
            step["url"], timeout=timeout, wait_until=step.get("wait_until", "load")
        )
        return f"HTTP {response.status}" if response else "no response"
    if action == "click":
        page.locator(selector).first.click(timeout=timeout)
    elif action == "fill":
        page.locator(selector).first.fill(step["value"], timeout=timeout)
    elif action == "type":
        page.locator(selector).first.press_sequentially(step["text"], timeout=timeout)
    elif action == "press":
        if selector:
            page.locator(selector).first.press(step["key"], timeout=timeout)
        else:
            page.keyboard.press(step["key"])
    elif action == "select":
        page.locator(selector).first.select_option(step["value"], timeout=timeout)
    elif action == "check":
        page.locator(selector).first.check(timeout=timeout)
    elif action == "uncheck":
        page.locator(selector).first.uncheck(timeout=timeout)
    elif action == "hover":
        page.locator(selector).first.hover(timeout=timeout)
    elif action == "upload":
        page.locator(selector).first.set_input_files(step["files"], timeout=timeout)
    elif action == "wait_for":
        page.locator(selector).first.wait_for(state=step.get("state", "visible"), timeout=timeout)
    elif action == "wait":
        page.wait_for_timeout(step["ms"])
    elif action == "expect_text":
        if selector:
            target = page.locator(selector).filter(has_text=step["text"]).first
        else:
            target = page.get_by_text(step["text"]).first
        target.wait_for(state="visible", timeout=timeout)
    elif action == "expect_no_text":
        page.get_by_text(step["text"]).first.wait_for(state="hidden", timeout=timeout)
    elif action == "expect_url":
        page.wait_for_url(lambda url: step["contains"] in url, timeout=timeout)
        return page.url
    elif action == "expect_count":
        locator = page.locator(selector)
        deadline = timeout
        while True:
            count = locator.count()
            if count == step["count"]:
                return f"{count} element(s)"
            if deadline <= 0:
                raise AssertionError(
                    f"expected {step['count']} element(s) for {selector!r}, found {count}"
                )
            page.wait_for_timeout(100)
            deadline -= 100
    elif action == "expect_value":
        actual = page.locator(selector).first.input_value(timeout=timeout)
        if actual != step["value"]:
            raise AssertionError(f"expected value {step['value']!r}, found {actual!r}")
    elif action == "eval":
        return json.dumps(page.evaluate(step["expression"]), ensure_ascii=False, default=str)
    elif action == "screenshot":
        path = out / f"{step['name']}.png"
        page.screenshot(path=str(path), full_page=step.get("full_page", True))
        shots.append(str(path))
        return str(path)
    else:
        raise ValueError(f"unknown action {action!r}")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", required=True, help="directory for evidence")
    parser.add_argument("--url", help="just open this URL and capture it")
    parser.add_argument("--script", help="JSON file with the scenario steps")
    parser.add_argument("--viewport", default="1280x800")
    parser.add_argument("--timeout-ms", type=int, default=10000)
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    parser.add_argument(
        "--fail-on-console-error",
        action="store_true",
        help="treat console errors and uncaught exceptions as a failure",
    )
    args = parser.parse_args()
    if bool(args.url) == bool(args.script):
        parser.error("give exactly one of --url or --script")

    steps = (
        [{"action": "goto", "url": args.url}]
        if args.url
        else json.loads(Path(args.script).read_text())
    )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    width, height = (int(v) for v in args.viewport.lower().split("x"))

    report: dict = {
        "ok": True,
        "steps": [],
        "console_errors": [],
        "page_errors": [],
        "failed_requests": [],
        "screenshots": [],
    }
    use_working_node()
    with sync_playwright() as pw:
        browser = launch(pw, args.headed)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.on(
            "console",
            lambda m: report["console_errors"].append(m.text) if m.type == "error" else None,
        )
        page.on("pageerror", lambda e: report["page_errors"].append(str(e)))
        page.on(
            "requestfailed",
            lambda r: report["failed_requests"].append(f"{r.method} {r.url}: {r.failure}"),
        )
        page.on(
            "response",
            lambda r: (
                report["failed_requests"].append(f"{r.request.method} {r.url}: HTTP {r.status}")
                if r.status >= 400
                else None
            ),
        )
        for index, step in enumerate(steps, 1):
            entry = {"index": index, **step, "ok": True}
            try:
                detail = run_step(page, step, out, args.timeout_ms, report["screenshots"])
                if detail is not None:
                    entry["detail"] = detail
            except (Error, PlaywrightTimeout, AssertionError, KeyError, ValueError) as exc:
                entry["ok"] = False
                entry["error"] = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"
                report["ok"] = False
            report["steps"].append(entry)
            if not entry["ok"]:
                break
        last = out / ("final.png" if report["ok"] else "failure.png")
        try:
            page.screenshot(path=str(last), full_page=True)
            report["screenshots"].append(str(last))
            report["final_url"] = page.url
            report["title"] = page.title()
            (out / "page.txt").write_text(page.inner_text("body"))
        except Error as exc:
            report["capture_error"] = str(exc).splitlines()[0]
        browser.close()

    if args.fail_on_console_error and (report["console_errors"] or report["page_errors"]):
        report["ok"] = False
    report["steps_run"] = len(report["steps"])
    report["steps_total"] = len(steps)
    (out / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))

    for entry in report["steps"]:
        mark = "ok  " if entry["ok"] else "FAIL"
        target = entry.get("selector") or entry.get("url") or entry.get("text") or ""
        print(
            f"[{mark}] {entry['index']:>2} {entry['action']} {target} {entry.get('error', '')}".rstrip()
        )
    for key in ("console_errors", "page_errors", "failed_requests"):
        for item in report[key]:
            print(f"[{key[:-1]}] {item}")
    print(f"{'PASS' if report['ok'] else 'FAIL'}: evidence in {out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
