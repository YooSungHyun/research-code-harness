# Phase: build

Goal: work through the checklist in `.harness/PLAN.md` one item at a time,
each item run and checked for real before it is ticked, and the list kept true
to what you learn on the way.

## The loop

Repeat until no `S` item is open.

### 1. Take the first open item

Set `next:` in `STATUS.md` to it. One item at a time, in order: do not start
another before this one is ticked and committed.

### 2. Do it

- **Read before changing.** The files you will touch, their callers, their
  tests, the conventions in use. For existing code, your notes in
  `.harness/analysis/codebase.md` say where to attach and what must not
  change. Before using a library call you are not certain of, look up the
  documentation of the installed version (`uv pip show <name>`).
- **Make the smallest change that satisfies the item**, in the style of the
  code around it. Add dependencies with `uv add`. Do not refactor, rename or
  improve things the item does not ask for.
- **Write tests that would notice if it were wrong**: they call the real code
  and assert on real behaviour, for the cases this item serves, including
  their edges.

An **experiment** item needs more care, because a wrong number looks exactly
like a right one. Fix the design before running anything (hypothesis, metric,
baseline, data and split, seeds, what outcome would count against the
hypothesis). Write it as a script run with `uv run`, configuration in one
place, every seed set, results written to files. Time a tiny run before the
real one and size it to this machine. Sanity-check before believing: does the
baseline give the number it should, does a result that looks too good survive
a shuffled-label control? No tuning on test data, no picking the best run;
several seeds are all reported. A result against the hypothesis is reported as
exactly that.

A **research document** item follows the rules of evidence from discovery:
cite only sources you opened, state what they say in their own terms, and
open each cited URL once more before finishing.

### 3. Run the check, for real

Run the item's `check` and then the regression commands, exactly as written in
the plan, and read the output. When something fails, read all of it and find
the cause before changing anything. If a regression command fails, your change
broke something that worked: fix the change. Never weaken a check to get
through it; if a check is itself wrong, change it in the plan and note that
under "Changes".

Record what really went wrong, once understood, in `.harness/ISSUES.md` (the
format is in the harness `CLAUDE.md`): a run that failed for a real reason, an
assumption that was false, an environment problem. Not a typo you fixed in
passing.

### 4. Look over the change

`git status` and `git diff`: debug output, commented-out code, hard-coded
paths, secrets, files that should not be there. If you change anything, run
the checks again.

### 5. Tick it, and commit

In `PLAN.md`, change the item's `- [ ]` to `- [x]` and add a line under it:

```
  - done: <YYYY-MM-DD> <one-line result of the check>
```

Then commit the work together with the tick:

```bash
git add -A && git commit -q -m "[<ID>] <title>"
```

Tick the moment the check has passed: not earlier, not at the end of the
session, never several at once. The file is how anyone watching follows the
work.

### 6. Look at what is left

Before the next item, read the remaining list with what you now know:

- Something turned out to be needed that no item covers: add an item.
- An open item is wrong, too big, or in the wrong place: change it, split it,
  move it.
- An open item is no longer needed: remove it.

Write each change under "Changes" in `PLAN.md` with its reason. Changes to how
the work is cut up need nobody's approval. A change to what the user will get
(a case added or dropped, a reading changed) is different: update `INTENT.md`
first, with an entry under its "Changes", and add a `V` item for a fresh
`intent-checker` to check the plan again.

If you learned something that must not be lost (a command, a convention, a
trap), add a line to the Notes in the project's context file.

## When an item has to be done again

When a later item, a review or a verification shows that a ticked item is
wrong:

1. Change its `- [x]` back to `- [ ]` and add under it
   `  - reopened: <YYYY-MM-DD> <what was found, and by what>`.
   Keep its earlier `done` line; the history stays readable.
2. Untick every verification item whose result no longer describes the code
   as it will be after the fix.
3. Note it under "Changes", and record the defect in `.harness/ISSUES.md`.

A reopened item is then simply the first open item again.

## When an item will not pass

- Twice with the same symptom: stop patching. Reproduce the failure in
  isolation and find the cause before changing more.
- Still failing: step back from the code to the plan. Is the item too big,
  impossible to check, or built on something that turned out false? Then
  change the plan, not the check.
- If the obstacle is something only the user can resolve (credentials, access,
  hardware, two goals that exclude each other): set `status: waiting` with a
  `note:`, and tell the user exactly what was tried and what is needed.

When every `S` item is ticked: set `phase: verify` and `next:` in `STATUS.md`,
read `verify.md` and continue.
