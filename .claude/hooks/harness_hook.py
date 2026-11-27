#!/usr/bin/env python3
"""The two hooks that let a harness project run without supervision.

The only state they read is a small text header the orchestrating session keeps
at the top of projects/<name>/.harness/STATUS.md:

    status: running | waiting | done
    session: <id of the session working on the project>
    phase: understand | discover | plan | build | verify | report
    next: <the very next thing to do, one line>

stop           A session whose project is `running` is sent back to work with
               its `next` line and the state of the checklist. It may stop
               when the project is `waiting` (the user must decide something)
               or `done`, while background work is pending, or after stopping
               several times with nothing changing. A `done` project is held
               while its checklist (.harness/PLAN.md) still has an open item
               or tooling installed for it (`- [installed] ...` lines in
               .harness/TOOLING.md) has not been removed.

session-start  Tells a new, resumed or compacted session which project it is
               working on and where to pick up, or lists unfinished projects.

Standard library only. Any error lets the session stop: a broken hook must
never trap it.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
PROJECTS = ROOT / "projects"
PHASES = ROOT / ".claude" / "skills" / "harness" / "phases"
IDLE_LIMIT = int(os.environ.get("HARNESS_IDLE_STOPS", "3"))


def read_status(project: Path) -> dict:
    """The `key: value` lines at the top of STATUS.md (up to the first blank line)."""
    fields: dict = {}
    try:
        lines = (project / ".harness" / "STATUS.md").read_text(errors="replace").splitlines()
    except OSError:
        return fields
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            if fields:
                break
            continue  # a title or blank lines before the header are fine
        key, sep, value = line.partition(":")
        if not sep or " " in key.strip():
            break
        fields[key.strip().lower()] = value.strip()
    return fields


def projects() -> list[tuple[Path, dict]]:
    if not PROJECTS.is_dir():
        return []
    found = []
    for project in sorted(PROJECTS.iterdir()):
        status = read_status(project) if project.is_dir() else {}
        if status:
            found.append((project, status))
    return found


def installed_tooling(project: Path) -> list[str]:
    """Things the harness installed for this project and has not removed yet."""
    try:
        text = (project / ".harness" / "TOOLING.md").read_text(errors="replace")
    except OSError:
        return []
    # Format examples inside HTML comments or code fences are not entries.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"^(```|~~~).*?^\1[^\n]*$", "", text, flags=re.DOTALL | re.MULTILINE)
    return [
        ln.strip()[2:].strip()
        for ln in text.splitlines()
        if ln.strip().lower().startswith("- [installed]")
    ]


ITEM = re.compile(r"^- \[( |x|X)\] (\S+) ?(.*)$")


def checklist(project: Path) -> list[tuple[bool, str, str]]:
    """The items under `## Checklist` in PLAN.md: (ticked, id, title)."""
    try:
        text = (project / ".harness" / "PLAN.md").read_text(errors="replace")
    except OSError:
        return []
    items, inside, fenced = [], False, False
    for line in text.splitlines():
        if line.startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("## "):
            inside = line[3:].strip().lower() == "checklist"
            continue
        match = ITEM.match(line) if inside else None
        if match:
            items.append((match.group(1) != " ", match.group(2), match.group(3).strip()))
    return items


def progress(project: Path) -> str:
    """One line on the checklist, or '' when there is none yet."""
    items = checklist(project)
    if not items:
        return ""
    still_open = [f"{ident} {title}".strip() for ticked, ident, title in items if not ticked]
    line = f"checklist {len(items) - len(still_open)}/{len(items)} ticked"
    return line + (f"; first open item: {still_open[0]}" if still_open else "; nothing open")


def newest_change(project: Path) -> float:
    newest = 0.0
    for path in (project / ".harness").rglob("*"):
        try:
            newest = max(newest, path.stat().st_mtime)
        except OSError:
            continue
    return newest


def idle_count(session: str, project: Path) -> int:
    """How many stops in a row found the project's records unchanged."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session)[:100]
    path = PROJECTS / ".sessions" / f"{safe}.json"
    marker = newest_change(project)
    try:
        previous = json.loads(path.read_text())
    except (OSError, ValueError):
        previous = {}
    same = previous.get("project") == project.name and previous.get("marker") == marker
    count = previous.get("idle", 0) + 1 if same else 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"project": project.name, "marker": marker, "idle": count}))
    return count


def set_waiting(project: Path, note: str) -> None:
    path = project / ".harness" / "STATUS.md"
    lines = path.read_text().splitlines()
    out, noted = [], False
    for line in lines:
        key = line.partition(":")[0].strip().lower()
        if key == "status":
            out.append("status: waiting")
        elif key == "note":
            out.append(f"note: {note}")
            noted = True
        else:
            out.append(line)
    if not noted:
        index = next((i for i, ln in enumerate(out) if ln.startswith("status:")), 0)
        out.insert(index + 1, f"note: {note}")
    path.write_text("\n".join(out) + "\n")


def guide(phase: str) -> Path:
    path = PHASES / f"{phase}.md"
    return path if path.is_file() else ROOT / ".claude" / "skills" / "harness" / "SKILL.md"


def describe(project: Path, status: dict) -> str:
    text = (
        f"projects/{project.name} - status {status.get('status', '?')}, "
        f"phase {status.get('phase', '?')}, next: {status.get('next', '(not recorded)')}"
    )
    done = progress(project)
    return f"{text} ({done})" if done else text


def stop(payload: dict) -> dict | None:
    session = payload.get("session_id")
    if not session:
        return None
    mine = [(p, s) for p, s in projects() if s.get("session") == session]
    for project, status in mine:
        state = status.get("status")
        leftovers = installed_tooling(project) if state == "done" else []
        unticked = (
            [f"{i} {t}".strip() for ticked, i, t in checklist(project) if not ticked]
            if state == "done"
            else []
        )
        if state != "running" and not leftovers and not unticked:
            continue
        if payload.get("background_tasks") or payload.get("session_crons"):
            return None  # waiting for work that will wake the session up again
        if idle_count(session, project) > IDLE_LIMIT:
            if state == "running":
                set_waiting(project, f"stopped {IDLE_LIMIT} times with nothing changing")
                message = (
                    f"[harness] projects/{project.name} set to `waiting`: the session "
                    f"stopped {IDLE_LIMIT} times with nothing changing. "
                    f"/harness-resume {project.name} continues it."
                )
            else:
                message = f"[harness] projects/{project.name} is marked done, but "
                if unticked:
                    message += f"{len(unticked)} checklist item(s) are still open: " + "; ".join(
                        unticked
                    )
                if leftovers:
                    message += (" and " if unticked else "") + (
                        "tooling installed for it was NOT removed: " + "; ".join(leftovers)
                    )
            return {"systemMessage": message}
        status_file = project / ".harness" / "STATUS.md"
        if unticked:
            reason = (
                f"[harness] projects/{project.name} is marked done, but its checklist "
                f"({project / '.harness' / 'PLAN.md'}) still has open items:\n- "
                + "\n- ".join(unticked)
                + "\nThe run is finished only when every item is ticked. Set `status: "
                "running`, then do each open item and tick it, or remove an item that "
                "is truly not needed with its reason under \"Changes\"."
            )
        elif leftovers:
            reason = (
                f"[harness] projects/{project.name} is done, but tooling installed for it "
                "is still present and must be removed before you stop:\n- "
                + "\n- ".join(leftovers)
                + f"\nRemove each one, confirm it is gone, and change its line in "
                f"{project / '.harness' / 'TOOLING.md'} from `[installed]` to `[removed]`."
            )
        else:
            reason = (
                f"[harness] {describe(project, status)}\n"
                "The project is not finished, so do not stop. Continue from `next` "
                f"without asking the user. Guide for this phase: {guide(status.get('phase', ''))} "
                f"(read it if it is not in your context); state: {status_file}.\n"
                "Stop only when (a) the result is delivered: set `status: done`; or "
                "(b) something only the user can decide blocks all progress: set "
                "`status: waiting` and a `note:` line saying what you need, then ask."
            )
        return {"decision": "block", "reason": reason}
    return None


def session_start(payload: dict) -> dict:
    session = payload.get("session_id")
    lines = [
        f"[harness] This repository runs requests as projects under {PROJECTS}/<name>/ "
        "(see CLAUDE.md). New work: the `harness` skill. Earlier work: `harness-resume`."
    ]
    for project, status in projects():
        leftovers = installed_tooling(project)
        if status.get("session") == session and status.get("status") == "running":
            lines.append(
                f"This session is working on {describe(project, status)}. Read "
                f"{project / '.harness' / 'STATUS.md'} and {guide(status.get('phase', ''))}, "
                "then continue without asking the user."
            )
        elif status.get("status") != "done":
            lines.append(f"Unfinished: {describe(project, status)}")
        if leftovers and status.get("status") == "done":
            lines.append(
                f"projects/{project.name} is done but tooling installed for it remains; "
                "tell the user and remove it: " + "; ".join(leftovers)
            )
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(lines),
        }
    }


def main() -> int:
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
        output = stop(payload) if event == "stop" else session_start(payload)
    except Exception as exc:  # noqa: BLE001 - never trap the session
        print(f"harness hook ({event}): {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if output is not None:
        print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
