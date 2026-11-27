# Phase: report

Goal: tell the user what they got, how it was shown to work, and what actually
went wrong on the way; then leave the machine as it was found.

Every item on the checklist in `.harness/PLAN.md` is ticked when this phase
starts. If one is not, go back to it first.

## 1. Write the report

`.harness/REPORT.md`, in the language of the request, for someone who was not
watching:

- **Outcome**: what was built or found, and whether it is what was asked.
  Lead with this.
- **Against the request**: go through the request and the cases in
  `INTENT.md`. For each: met or not, and the evidence by path (a log, a
  screenshot, a result file). Include how each ambiguous point was read. A
  case without evidence is not met.
- **Findings** (research, hybrid): each with the result file or opened source
  behind it. Negative results as plainly as positive ones.
- **How to run it**: paths, and commands that work when pasted. Run each one
  once more before writing it down.
- **Problems that actually occurred**: the entries of `.harness/ISSUES.md`,
  all of them and nothing else - symptom, cause, fix, status. If the file has
  no entries, say that no problems occurred. No might-have-beens.
- **Still open**: only what was really observed - a case not met or not
  verified, an open issue. If nothing, say so. No generic caveats.

Everything in the report must be true of the final state and traceable to the
evidence.

## 2. Remove what was installed

For every `[installed]` line in `.harness/TOOLING.md`: run its removal
command, confirm it is gone (`claude plugin list --json`, `claude mcp list`),
and change the line to `[removed]` with the date and the command that
confirmed it. Remove a marketplace only if the harness added it. Things that
were on the machine before the project started stay.

The Stop hook holds the session until no `[installed]` line is left.

## 3. Keep what was learned

- **The project's context file**: rewrite it for whoever opens this folder
  next, with or without the harness: what the project is, how to run and test
  it, how it is laid out, its conventions, what must not change. Keep the
  request and the import of `INTENT.md`.
- **The harness's `CLAUDE.md`**, section "Lessons": add a line only for
  something that would change how a future, different project should be run
  (how this user wants requests read, a kind of mistake to avoid). Most
  projects add nothing.
- **The harness's `CLAUDE.local.md`**: add or correct facts about this machine
  that came up (something missing, a port in use, a tool that behaves
  unexpectedly).

## 4. Close

Commit the final state in the project folder (for a new project,
`git add -A && git commit -q -m "chore: report"`; a working copy of the user's
repository has nothing more to commit, since the harness's records are
excluded there).

Set `status: done` in `STATUS.md`. (A hook holds the session if the checklist
still has an open item or tooling is still installed.)

Then tell the user, in their language, in a message that stands on its own:

1. The outcome in a sentence or two, and whether it matches what they asked.
2. Where it is and how to run or read it: the project folder, the command, the
   report.
3. How the request was read where it was ambiguous.
4. What was verified and how.
5. The problems that actually occurred and how each was resolved. If none were
   recorded, say that none occurred.
6. Anything still open, plainly.

Keep it short; the report has the detail.
