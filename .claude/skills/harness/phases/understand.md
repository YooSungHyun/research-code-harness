# Phase: understand

Goal: a project folder, and a settled, written understanding of what the user
is asking for, reached by more than one reading of their words.

Paths are relative to the harness root unless they start with `.harness/`
(then they are inside the project folder).

## 1. This machine

Read `CLAUDE.local.md` in the harness root: facts about this machine that every
project needs (hardware, what is installed, known traps). If it does not
exist, this is a new machine. Create it from what these report, as a short
list of facts:

```bash
uname -srm; nproc; free -g | sed -n 2p; df -h . | tail -1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "no GPU"
uv --version; uv python list --only-installed; git --version; node --version 2>/dev/null
command -v ego-browser || echo "ego-browser: not installed"
echo "display: ${DISPLAY:-none}"
```

## 2. Starting point and type

Look at what exists (`ls projects/`) and decide which this is:

- **New**: nothing to build on.
- **More work on an earlier project** in `projects/`: same folder. Move its
  earlier records (`.harness/*` except `history/`) into
  `.harness/history/<n>/` and start fresh records. It counts as existing code.
- **An existing repository** the user names (a path or a git URL): it gets its
  own working copy, so the user's checkout is never touched.

Then the type, which decides what has to be looked into and how the result is
verified:

- `research` - the result is knowledge: a survey, an analysis, an answer to a
  question, an experiment design.
- `code` - the result is working software.
- `hybrid` - a question answered by building and measuring, such as
  implementing a paper's method and evaluating it.

If the request does not make the type clear, it goes into the questions in
step 6.

## 3. Name the project and create its folder

Choose the name yourself: short, lowercase, words joined by dashes, saying
what the thing is (`todo-webapp`, `rag-eval-survey`). Do not ask the user for
it. Everything from here on happens inside `projects/<name>/`.

**New project** (Python 3.12 unless the work needs another version):

```bash
uv init --bare --no-workspace --vcs none --name <name> --python 3.12 projects/<name>
cd projects/<name> && git init -q -b main
```

That gives a uv project (`pyproject.toml`) and nothing else, on purpose. The
layout of the code and the development tools it needs follow from the request
and are decided in the plan; a package skeleton laid down now would be
structure nobody asked for. Add a `.gitignore` (`.venv/`, `__pycache__/`,
`.pytest_cache/`, `.ruff_cache/`, `.env`, and whatever the work generates).

**Existing repository**:

```bash
git -C <repo> worktree add -b harness/<name> <harness root>/projects/<name>     # a local repository
git clone <url> projects/<name> && git -C projects/<name> checkout -b harness/<name>   # a URL
printf '.harness/\nCLAUDE.local.md\n' >> "$(git -C projects/<name> rev-parse --git-path info/exclude)"
```

The last line keeps the harness's records out of the user's repository. If
the repository has uncommitted changes, they are not in the working copy; note
that. Do not set up or change its environment yet.

**Then, in every case**, create `.harness/` with `STATUS.md` (the four header
lines from the skill, `phase: understand`), and the project's context file:
`CLAUDE.md` in the project folder, or `CLAUDE.local.md` if the repository is
the user's (leave any `CLAUDE.md` of theirs as it is; it is loaded too, and
its rules apply).

```markdown
# <title>

## Request
> <the user's words, verbatim>

## Working here
- Type: <research | code | hybrid>. Started from commit <sha> on <date>.
- Python goes through uv from this folder: `uv run ...`, `uv add ...`.
- Run / test / lint: <fill in when these exist; only commands that work>

## Notes
<what must not be lost: conventions, traps. How things are now, not a
history.>
```

For a new project, commit the scaffold (`git add -A && git commit -q -m "chore: scaffold"`)
and put that commit's hash in the file.

## 4. Existing code: read it yourself, all of what matters, first

If there is existing code, read it before interpreting the request: what a
request means inside an existing system depends on what is there, and work
added without understanding the system conflicts with it. Do this reading
yourself; you are the one who will change the code.

- The overall shape: README and docs, build and dependency files, layout, the
  entry points (commands, services, job definitions, `__main__`, scheduled
  tasks), the tests and how they run, CI configuration, recent history. The
  repository's own `CLAUDE.md` or `AGENTS.md`, if any: those are its owner's
  rules.
- The paths the request will touch, from entry point to output. Read the
  functions on those paths in full, with their callers (search for every use)
  and the tests that cover them. Do not infer what a function does from its
  name.
- How it is really run and tested: run it. Find the exact commands that pass
  on the untouched code today. If some tests already fail, note which and how.
- What a newcomer would break: shared state, ordering assumptions between
  pipeline stages, schemas and file formats other parts read, configuration
  keys, names other code imports, generated files, anything loaded
  dynamically or by name.

Write what you established to `.harness/analysis/codebase.md`, every statement
with its `file:line`: how to run and test it; the pipeline the request touches,
stage by stage; what the terms of the request correspond to in the code (and
where they could correspond to more than one thing); where new work should
attach and which existing example to follow; what must not change and who
depends on it; concrete conflict risks. Copy the "must not change" list and
the commands that pass today into the project's context file.

## 5. Several readings of the request

Your reading of the request is one reading, and you cannot see its blind spot
from inside it. Write your own reading down first, in a few lines in
`STATUS.md`, so that it is on record before you see the others. Then start
three `intent-checker` agents in a single message, job "read the request",
each given the request verbatim (and, for existing code, the path of
`codebase.md`) and nothing else: not your reading, not each other's files.

- lens **literal** -> `.harness/intent/reading-literal.md`
- lens **purpose** -> `.harness/intent/reading-purpose.md`
- lens **misreading** -> `.harness/intent/reading-misreading.md`

While they run, do the tooling review: read `tooling.md` in this folder and
follow it.

## 6. Compare the readings, then ask once

Read the three files side by side, with your own reading as the fourth.

- Where all agree, the meaning is solid.
- Where they differ, the request is ambiguous at that point. For each such
  point decide:
  - one reading is clearly right in context -> take it, and write down why;
  - several readings can all be served at little cost -> serve them all;
  - the readings lead to materially different results and you cannot tell
    which is meant -> that is a question for the user.
- Merge the cases into one list. Keep a case if the user would be surprised to
  find it unhandled; drop it if they would be surprised that time was spent
  on it. Size words in the request ("small", "simple", "quick", "prototype",
  "thorough", "all") move this line; respect them.

Then, if you can interact with the user, call `AskUserQuestion` once with at
most four questions, your recommendation first in each:

1. the type, if open;
2. the ambiguities of the third kind, most consequential first;
3. tooling that needs their approval (see `tooling.md`).

Ask only what would change the work, and skip the call if nothing would. If
`AskUserQuestion` is unavailable (a headless run) or the request carried
`--auto`, decide everything yourself.

## 7. Write INTENT.md

`.harness/INTENT.md`, in the language of the request:

```markdown
# Intent - <title>

## Request
> <verbatim, followed by the questions asked and the user's answers, verbatim>

## In short
<what is being asked for, in one paragraph of plain words>

## Type
<research | code | hybrid> - <why>

## Asked
- <requirement> - "<the words of the request it comes from>"

## Implied
- <expectation> - <why someone asking this would take it for granted>

## Ambiguous
- <point>: could mean A or B. Taken as A because <reason>. B: <also served |
  the user chose | set aside because ...>

## Not asked
- <things a builder might add that are out of scope here>

## Cases
| # | Situation | Correct outcome | Follows from | Verified by |
|---|---|---|---|---|
| C1 | ... | ... | <words of the request, or the implied expectation> | <test / experiment / demo / source> |

## Changes
<dated entries when a later phase changes this understanding, with the reason>
```

Every later phase works from this file together with the request. It is not
frozen: when later work shows that a reading was wrong or a case was missed,
change it and add an entry under "Changes".

Then add this section to the project's context file, so that the
understanding is loaded automatically by anyone working in the folder:

```markdown
## How the request is understood
@.harness/INTENT.md
```

## 8. Say what you understood, and move on

Tell the user in a few lines, in their language, how the request was
understood: the project name and folder, the type, the main cases, and any
reading you chose for them. Do not wait for a reply; this is so they can
interrupt if it is wrong.

Set `phase: discover` and `next:` in `STATUS.md`, then read `discover.md` in
this folder and continue.
