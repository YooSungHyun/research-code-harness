# Phase: verify

Goal: show, for real, that the finished result handles every case and is what
the user asked for. This phase is the `V` items at the end of the checklist,
worked like any other items: one at a time, ticked when they pass.

Each work item passed its own check. These items ask the larger questions:
does the whole thing work when used the way a person would use it, in every
case that matters, and is it what was meant?

## The verification items

**Run everything from a clean state.** The regression commands and the full
test suite, from the project folder, the way the README tells a user to. Save
the output under `.harness/evidence/<ID>/`.

**Independent review and real use.** Start a `reviewer` with the request
verbatim, the harness root, the project folder, what to review (everything
since the starting commit) and the evidence folder
`.harness/evidence/<ID>/`. It reads the changes, runs them, and uses the
result as a user would: a web UI is driven in a real browser (`ego-browser`
where it is installed, the bundled Playwright driver otherwise) with
screenshots; a command-line tool is run in a terminal; research claims are
traced to results and opened sources. Give it the work, not your account of
it. When it returns, open the screenshots yourself before accepting a pass.

**Every case verified.** Write `.harness/VERIFICATION.md` with one row per
case in `INTENT.md`:

| Case | How it was verified | Evidence | Result |
|---|---|---|---|

Fill each row from something that was actually run or opened: a test, a
result file, the reviewer's screenshots or transcript, a source. A case that
could not be verified for real gets the result "not verified" and the reason;
never fill a row from reasoning.

**The result against the request.** Start an `intent-checker`, job "check the
result", with the request verbatim and the project folder; it writes
`.harness/intent/result-check.md`. It reads the request first, uses the result
the way the user would, and reports what is missing, what is there that nobody
asked for, what was read differently, and which cases were not really
verified.

Tick each item when its check holds, with a `done` line naming the evidence,
and commit as in `build.md`.

## When a verification fails

A failed run, a blocking review finding or a failed request check is a real
defect, and the checklist has to say so:

1. Record it in `.harness/ISSUES.md` (status `open`).
2. In `PLAN.md`, untick the work items that have to be done again, with a
   `reopened` line each (the reviewer and the intent-checker name the items
   they think are affected; decide yourself whether they are right). If no
   existing item covers the defect, add one, with a check that would have
   caught it.
3. Untick every verification item whose result will no longer describe the
   code after the fix. Leave the failed one open.
4. Note it under "Changes", set `phase: build`, and work the open items in
   order as in `build.md`. Mark the issue `resolved` when it is.
5. The verification items then come up again in their turn. A review or a
   request check that is repeated is done by a fresh agent.

Something that was built and not asked for is a defect too: add an item to
remove it, unless removing it would break what was asked.

Do not edit code outside an open item; every change belongs to an item that
is then checked and ticked.

When every item on the checklist is ticked: set `phase: report` and `next:` in
`STATUS.md`, read `report.md` and continue.
