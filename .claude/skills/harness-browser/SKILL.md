---
name: harness-browser
description: How to launch a web application and verify it in a real browser with evidence - ego-browser when it is installed, a bundled Playwright driver otherwise. Use when a web UI or demo has to be opened, clicked through and screenshotted to confirm it really works.
---

# Verify a web UI in a real browser

Looking at code or at an HTTP 200 does not show that a UI works. Open it in a
browser, do what a user would do, and look at what the browser shows.

Paths below are relative to the harness repository root (the orchestrator gives
you its absolute path).

## 1. Start the application yourself, on a free port

This machine may be shared, and other people's servers may already be
listening. Never assume a port is free and never assume the server answering on
a port is yours.

```bash
PORT=$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1])")
cd <project dir> && uv run <start command using $PORT> > .harness/evidence/demo/server.log 2>&1 &
SERVER_PID=$!
for i in $(seq 1 100); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.3; done
kill -0 $SERVER_PID   # still alive? if not, read server.log: it failed to start
```

- Start it the way the project's README tells a user to. If that does not
  work, that is a finding, not something to work around.
- Stop it when you are done with `kill $SERVER_PID`. Kill only the process id
  you started. Never kill by port or by name.
- A long-running server started with the Bash tool needs `run_in_background`;
  keep its process id.

## 2. Choose the browser

```bash
command -v ego-browser
```

### ego-browser is installed

ego-browser drives ego lite, a real browser the user also uses (macOS and
Windows only). Run `ego-browser skill` first and follow the guide it prints; it
is the authority on the commands for the installed version. The guide ends with
a line starting `[ego-browser:skill] end of guide`. If that line is missing, the
output was cut off: write it to a file (`ego-browser skill > <file>`) and read
it in parts.

Use it to open `http://127.0.0.1:$PORT/...`, perform the scenario, and save
screenshots into the evidence directory. It shares the user's browser profile:
do not clear cookies, cache or storage, and stay on the application under test.

### Otherwise: the bundled Playwright driver

```bash
uv run .claude/skills/harness-browser/scripts/browse.py \
   --out <project dir>/.harness/evidence/demo/<scenario-id> \
   --script <scenario.json>
```

It runs headless Chromium (installing it on first use), so it works on a server
with no display. A scenario is a JSON list of steps:

```json
[
  {"action": "goto", "url": "http://127.0.0.1:PORT/"},
  {"action": "fill", "selector": "#title", "value": "Buy milk"},
  {"action": "click", "selector": "role=button[name=\"Add\"]"},
  {"action": "expect_text", "selector": "#list", "text": "Buy milk"},
  {"action": "expect_count", "selector": "#list li", "count": 1},
  {"action": "screenshot", "name": "after-add"}
]
```

Actions: `goto`, `click`, `fill`, `type`, `press`, `select`, `check`,
`uncheck`, `hover`, `upload`, `wait_for`, `wait`, `expect_text`,
`expect_no_text`, `expect_url`, `expect_count`, `expect_value`, `eval`,
`screenshot`. Selectors are Playwright selectors (CSS, `text=...`,
`role=button[name="..."]`). Run the script with `--help` for every field.

It writes `result.json` (each step, console errors, uncaught page errors,
failed requests), a PNG per `screenshot` step plus `final.png` or
`failure.png`, and `page.txt` with the visible text. Exit code 0 means every
step and expectation held. `--fail-on-console-error` also fails on console
errors and uncaught exceptions; `--url <url>` just opens a page and captures
it.

Write the scenario from the user's point of view, from the scenario's
description in the plan: the actions a person would take, then expectations
about what they would see. Put a `screenshot` after each meaningful state
change. Find selectors by reading the page (the application's templates, or a
first `--url` run and `page.txt`), not by guessing.

## 3. Look at the evidence

Passing expectations are necessary, not sufficient. For every scenario:

1. Open each screenshot with the Read tool and look at it. Is this what the
   scenario's `expected` describes? Is the page laid out sensibly, with no
   error banner, no empty area where content should be, no unstyled or broken
   rendering?
2. Read `result.json`: any console error, uncaught exception or failed request
   needs an explanation. One caused by the application is a defect.
3. Read the server log for tracebacks.

## 4. Write the notes

In the evidence directory, `notes.md`: the scenario and its expected result,
how the application was started (the exact command), what you did, what you
observed (referring to the screenshots by file name), anything wrong, and the
verdict: `pass` only if the real application, really running, did what the
scenario expects and nothing else was broken. If you could not run it for real,
the verdict is `fail` with the reason; do not substitute reasoning for the run.
