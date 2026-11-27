---
name: harness
description: Take a request - software to build, a research question or paper topic to investigate, a feature to add to existing code - and carry it to a verified result without supervision. Works out what the request really means first (several readings, the cases it implies), then investigates, plans as a checklist, works through it one item at a time with real verification, and reports - all inside a project folder it names and creates. Use when the user describes something they want built, researched, reproduced or extended.
when_to_use: User says things like "이런 거 만들어줘", "이 주제 연구해줘", "이 논문 구현해줘", "기존 코드에 이 기능 추가해줘", "build ...", "research whether ...", "add this feature to <repo>".
argument-hint: <만들거나 연구할 내용>
---

# Harness: from a request to a verified result

**The request, in the user's words:**

$ARGUMENTS

Keep these words exactly as they are. They go into the project's records
verbatim, because each retelling of a request loses a little of what was
meant. One exception: a leading `--auto` is a flag for this harness (decide
everything yourself, ask nothing) and not part of the request; leave it out of
the verbatim text.

Your session id is `${CLAUDE_SESSION_ID}`.

## What "accurate" means here

The result is accurate if it is what the user meant. Their words are the
standard, but those words are usually short and sometimes imprecise. So the
run starts by working out what the request asks, what it implies, where it
could mean more than one thing, and which concrete cases a correct result has
to handle. The work is then done for those cases and verified for those
cases, and at the end the result is checked against the request itself, not
against anyone's summary of it.

Two ways to get this wrong, both common: reading the request so narrowly that
obvious expectations are missed, and reading so much into it that the user
gets things they never asked for. A "small" tool stays small.

## You do the work

This is one agent's job from start to finish: you read the request and the
existing code, investigate, plan, write the code or the document, run it, and
report. Doing it in one mind is what keeps the user's meaning intact; every
handoff to another agent loses some of it. Do not split the work into roles.

Other agents come in at two kinds of places only: where a mind that did not do
the work is the whole point, and where independent pieces of work can run side
by side, because that is where more agents make the run faster instead of
lossier:

| Agent | When | Why not you |
|---|---|---|
| `intent-checker` | three at the start, each reading the request through a different lens; one after the plan; one on the finished result | you cannot see past your own reading of the request |
| `reviewer` | at the review items of the checklist: reads what changed, runs it, uses it like a user (a real browser for a web UI) | you made it, so you share its assumptions |
| `scout` | in discovery, whenever there are several independent questions to look into: one scout per question, all started together | done side by side, the investigation takes as long as its slowest question instead of the sum of them |

Start agents that do not depend on each other in a single message, so they
run at the same time, and use the wait for work only you can do. Give each
agent the request verbatim, the project folder, exactly what to do and the
file to write. It loads the harness `CLAUDE.md` and the project's
`CLAUDE.md` on its own. Do not tell it what you expect it to find, and do not
give a reviewing agent your account of the work: give it the work.

## The run

Everything happens inside one folder, `projects/<name>/`, which you name and
create. Read the guide for a phase when you reach it:
`${CLAUDE_SKILL_DIR}/phases/<phase>.md`.

| Phase | What happens | What it leaves in the project |
|---|---|---|
| `understand` | name and create the project; read existing code; several readings of the request; ask the user once; review tooling | `CLAUDE.md`, `.harness/INTENT.md`, `.harness/TOOLING.md` |
| `discover` | look at the problem from the angles it needs, as deep as its size warrants | `.harness/analysis/*.md`, `.harness/SYNTHESIS.md` |
| `plan` | the design and a checklist of items, each tied to cases and to a real check; the plan is checked against the request | `.harness/PLAN.md` |
| `build` | work through the checklist one item at a time: do, run the check, tick, commit | commits, ticks in `PLAN.md`, `.harness/ISSUES.md` |
| `verify` | the verification items at the end of the checklist: every case for real, independent review and demo, the result against the request | `.harness/VERIFICATION.md`, `.harness/evidence/` |
| `report` | report; installed tooling removed; lessons kept | `.harness/REPORT.md` |

## The checklist is the plan

`.harness/PLAN.md` holds a checklist, and that checklist is the real state of
the work, kept in a fixed form so that a person or a tool can follow progress
from the file alone:

- One item at a time, in order: the first unticked item is the one being
  worked on. Tick it (`- [ ]` to `- [x]`) the moment its check has passed, not
  later and never several at once.
- It changes as you learn. After every item and after every review, look at
  what is left: add items, change them, remove them, and note each change in
  the plan's "Changes" section with its reason.
- A tick can be taken back. When a later check shows a finished item is wrong
  or has to be done again, untick it and say why. Untick as well any
  verification item whose result no longer describes the current state.
- The run is finished only when every item is ticked.

The exact format is in the `plan` guide.

## STATUS.md keeps the run alive

`projects/<name>/.harness/STATUS.md` begins with four lines that the harness's
hooks read:

```
status: running
session: ${CLAUDE_SESSION_ID}
phase: understand
next: <the very next thing to do, one line>
```

- While `status` is `running`, a Stop hook sends this session back to work
  with the `next` line and the state of the checklist. That is what lets the
  run finish unattended, so keep `phase` and `next` current.
- Set `status: waiting` and add a `note:` line only when something that only
  the user can decide blocks all progress. Then ask, and stop.
- Set `status: done` when the report is delivered and every item is ticked.
- After a context compaction or in a new session, a hook points you back to
  this file. Below the four lines, keep short notes on what has been decided,
  so that you can pick up from the files alone.

## The project's CLAUDE.md is its memory

`projects/<name>/CLAUDE.md` is loaded automatically by anyone working in that
folder, you after a compaction and every agent you start. Keep in it what
must not be lost: the request, how it is understood (it imports `INTENT.md`),
the commands that work, the conventions, what must not change. Things learned
that apply beyond this project go into the harness's own `CLAUDE.md` (lessons)
or `CLAUDE.local.md` (facts about this machine) at the end.

## Asking the user

Once, in the `understand` phase, everything in a single round. After that the
run does not ask: whatever is open, decide it and record the decision and its
reason in `INTENT.md`. The exception is a `waiting` state as described above.

Now read `${CLAUDE_SKILL_DIR}/phases/understand.md` and begin.
