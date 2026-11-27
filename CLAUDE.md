# research-code-harness

This repository is a harness: it takes a request (software to build, a research
question, a feature for existing code) and carries it to a verified result
without supervision. It is not itself the project. Each request becomes its own
folder, `projects/<name>/`, named by the harness, and all work happens inside
it.

## What to do with a request

- **The user describes something to build, research, reproduce or extend**:
  invoke the `harness` skill with their words, unchanged. Do not start on the
  work directly.
- **The user wants to continue earlier work, or asks how it stands**: the
  `harness-resume` skill.
- **The user wants to change the harness itself** (anything outside
  `projects/`): ordinary development on this repository; see the last section.

## Working rules

These come from the person who owns this harness and hold for every project,
for the orchestrator and for every agent.

**1. Accuracy means doing what was actually asked.** The measure of the work is
whether the user's request was understood and that thing was built or found.
Their own words are the standard. Those words are usually short and may be
imprecise, so the first reading is not enough: think through what else the
request could mean, what a person asking it would take for granted, and which
concrete cases the result has to get right. A project's `.harness/INTENT.md`
holds that work (the request verbatim, the readings, the cases). Read it before
you start, and keep the request itself in view, not only its summary.

- Deliver what was asked and what the asker would obviously expect. Leave out
  what they did not ask for: a "small" tool stays small.
- Cover the cases, not only the easiest one.
- If you come to think the request is being read wrongly, or a case was missed,
  say so at once. Do not quietly work to a different goal.

**2. Understand before changing, and do not break what exists.** Before
modifying existing code, read what the change touches: callers, data in and
out, configuration, tests. A change must fit the existing pipeline without
conflict: follow its conventions, add rather than rewrite, and leave behaviour
you were not asked to change exactly as it was. Existing tests are run before
anything changes and after every step; if they fail after your change, the
change is wrong.

**3. One item at a time, on a checklist that stays true.** The plan is a
checklist in the project's `.harness/PLAN.md`. Work on the first open item
only. It is finished when its check ran and passed for real; then it is ticked
and committed, at once, and the next one starts. The list changes as the work
teaches you: items are added, changed or removed, with the reason noted. And a
tick is taken back when a later check shows the item has to be done again.
The run is over when every item is ticked.

**4. Verify for real.** Run the thing. Tests exercise the actual code path; a
mock may stand in for an external service, never for what is being tested.
Never weaken or skip a check to make it pass. A demo is launched and used: a
web UI in a real browser with screenshots you looked at, a command-line tool by
typing what a user would type. An experiment result is a file a script can
produce again. A source you cite is one you opened, and it says what you
attribute to it. What could not be verified is reported as not verified.

**5. Time is not a constraint; guessing is.** Nobody is waiting. Read the code
instead of assuming, run the command instead of predicting, look up the
documentation of the installed version instead of recalling an API. What you
pass on has something behind it: a `file:line`, a command and its output, a
result file, a URL you opened.

**6. Record only problems that actually happened.** When something really went
wrong (a run failed, an assumption was false, a review found a bug, the
environment got in the way), add an entry to the project's
`.harness/ISSUES.md` once you understand it, in the project's language:

```markdown
## <short title>
- where: <phase / step>
- symptom: <what was observed>
- cause: <the root cause>
- fix: <what was changed>
- status: resolved | open
```

The final report lists exactly these entries. No risks, hypotheticals or
generic caveats. When something fails, find out why before changing anything.

**7. Stay inside the project folder.** All work happens in `projects/<name>/`.
The harness's files, other projects, and the user's own checkout of existing
code are off limits. Python goes through uv from the project folder
(`uv add`, `uv run`); no `pip install`, no global installs, no `sudo`. Never
push, publish, or send project content to an outside service. Plugins and MCP
servers are installed only through the harness's tooling review, recorded in
`.harness/TOOLING.md`, and removed when the project ends.

**8. Shared context lives in files.** Agents do not share memory. The project's
own `CLAUDE.md` is the standing context for everyone working in that folder;
read it first, and add to it, briefly, what every later agent will need. The
records are in `.harness/`. Write your full result to the file you were asked
for; your final message is a short summary and that path. Documents for the
user are in the language of their request; code, comments and commit messages
are in English unless the existing code does otherwise.

## How a run is organised

```
understand -> discover -> plan -> build -> verify -> report
```

One session does the work from start to finish, following the `harness` skill
and its guide per phase in `.claude/skills/harness/phases/`. The work is not
split into roles: every handoff loses some of what the user meant. Three
agents in `.claude/agents/` come in where a second mind is the point, or where
independent work can run in parallel and so finish sooner:

- `intent-checker` - independent readings of the request at the start; checks
  the plan, and later the result, against the request itself.
- `reviewer` - checks finished work without having done it: reads it, runs it,
  uses it like a user (a real browser for a web UI), traces research claims.
- `scout` - parallel investigation in discovery: one per independent question,
  started together.

A project's state is two things on disk. The header of
`projects/<name>/.harness/STATUS.md` (`status`, `session`, `phase`, `next`)
says whether and where it is running. The checklist in `.harness/PLAN.md`
says what is done: one line per item, `- [ ] <ID> <title>` or
`- [x] <ID> <title>`, under the heading `## Checklist`, with details as
indented `key: value` bullets. That format is fixed so that people and tools
can follow the work from the file.

Two hooks read both: one sends a session back to work while its project is
`running` (and holds a project marked `done` that still has an open item or
installed tooling), the other re-orients a session after it starts, resumes or
is compacted.

## The CLAUDE.md files

Instructions are kept where they apply, not all in skills and prompts:

- **This file** (committed): the rules above, and lessons that hold for every
  project.
- **`CLAUDE.local.md`** here (not committed): facts about this machine. The
  harness creates it on a new machine and keeps it current.
- **`projects/<name>/CLAUDE.md`**: one project's context, written when the
  project is created and kept current during the work. For a working copy of
  the user's own repository it is `CLAUDE.local.md` instead, so nothing is
  added to their repository; their own `CLAUDE.md` applies as well.
- **A `CLAUDE.md` deeper inside a project** when one area has rules of its own
  (for example how experiments record their results).

## Lessons

Added by the harness at the end of a project, one line each, only when
something would change how a different future project should be run.

- 2026-11-27: Size words in a request are requirements. A request for a "작은"
  to-do app with four features was once expanded into thirteen success
  criteria (atomic writes, concurrency, XSS, lint). Reading more into a
  request than it says is as much a failure as missing something.

## Changing the harness itself

- `.claude/hooks/harness_hook.py` is the only code besides the browser driver.
  It must stay standard-library Python and must never trap a session: any
  error lets the session stop. Try a change by piping a payload to it, for
  example
  `echo '{"session_id":"x"}' | python3 .claude/hooks/harness_hook.py stop`.
- A session that is only developing the harness must not put its own id in a
  project's `STATUS.md`: the Stop hook would hold it.
- Skills and agent prompts are instructions for a capable reader: explain the
  reason behind a rule.
- Check a change to the run by running a small real request through it.
