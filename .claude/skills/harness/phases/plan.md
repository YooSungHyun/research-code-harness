# Phase: plan

Goal: a design, and a checklist of small items that each say which cases they
serve and how they will be checked for real. The checklist is then worked
through one item at a time, and it is expected to change on the way.

## 1. Write PLAN.md

Write `.harness/PLAN.md` yourself, in the language of the request. Plan for
what was asked, at the size it was asked: no items for things the request
neither asks for nor implies.

```markdown
# Plan - <title>

## Design
<The approach in a paragraph and why this one. Software: the parts, what each
is responsible for, how data moves; for existing code, exactly where the new
work attaches, which existing pattern it follows, what stays untouched.
Research: the question, the method, the baseline, the metric, the data, and
what result would count against the hypothesis.>

## Coverage
| Case | Items | Verified by |
|---|---|---|
| C1 | S1, S3 | <test / experiment result / demo scenario / source> |

## Regression
<The command(s) run after every item to show that what worked still works.>

## Demo scenarios
<For anything a person uses: what the user does, and what they should then
see. One scenario per way of using it that the cases imply.>

## Checklist

- [ ] S1 <imperative title>
  - cases: C1, C2
  - do: <what to do, in which files, following which existing pattern>
  - check: `<command that fails before this is done and passes after>`
- [ ] S2 <...>
  - cases: C3
  - do: <...>
  - check: `<...>`
- [ ] V1 Run everything from a clean state
  - check: `<the regression commands and the full test suite>`
- [ ] V2 Independent review and real use (reviewer)
  - cases: <the cases a user would meet>
  - check: `.harness/evidence/V2/notes.md` ends with `VERDICT: pass`
- [ ] V3 Every case verified, with evidence
  - check: every row of `.harness/VERIFICATION.md` has evidence and a result
- [ ] V4 Result checked against the request (intent-checker)
  - check: `.harness/intent/result-check.md` ends with `VERDICT: pass`

## Changes
<One line per change to the checklist after it was first written:
- YYYY-MM-DD added|changed|removed|reopened <ID>: <reason>>
```

### The checklist format is a contract

People and tools follow the work from this section, so keep it exact:

- An item is one line at the start of a line: `- [ ] <ID> <title>` while open,
  `- [x] <ID> <title>` when finished. Nothing else on that line.
- `<ID>` is a letter and a number: `S` for work items, `V` for verification
  items. An id is never reused. An item added later takes the next free
  number, or a suffix when it belongs between two (`S2a`).
- Details are indented bullets under the item, as `key: value`. Keys: `cases`,
  `do`, `check`, and later `done`, `reopened`, `note`.
- The first open item is the one being worked on. The order of the list is the
  order of the work.

### Rules for items

- **Small**: one concern, finished in one sitting, with a check you can run.
  Many small items beat a few large ones.
- **Every item leaves the project working.** The regression commands must pass
  before the first item: for existing code, on the untouched code (if some
  existing tests already fail, name them, leave them out, and say why). A new
  project starts as a bare uv project, so the first item lays out the code in
  whatever shape fits the request, adds the development tools the checks need
  (`uv add --dev ...`), and includes a first real test (pytest exits non-zero
  when it collects nothing).
- **A check proves the item**: it fails before the work is done and passes
  after. Usually the item's own tests; for an experiment, the script that
  produces the result file plus a check of that file; for a document, a check
  that it exists with the required parts. Deterministic, no prompts, no server
  left running.
- **Verification items close the list.** Always the four above, adapted to the
  type: the review in V2 covers code, real use (a web UI in a real browser),
  and for research the tracing of every claim to a result or an opened source.
  In a long plan, or where a mistake would be expensive to discover late, put
  an extra review item (`V..`) after the risky group of items as well.
- **Sized to this machine** (`CLAUDE.local.md`).

## 2. Check the plan against the request

Start an `intent-checker`, job "check the plan", with the request verbatim and
the project folder; it writes `.harness/intent/plan-check.md`. It reads the
request before the plan and reports what is missing, what was added that
nobody asked for, what is read differently, and which cases have no check that
could fail.

On `VERDICT: fail`, fix the plan (and `INTENT.md` first, with an entry under
its "Changes", if the finding shows the understanding is wrong), then have a
fresh `intent-checker` check it again.

## 3. Existing code: record the starting point

Before anything is changed, run the regression commands on the untouched code
and write `.harness/baseline.md`: each command, its exit code, and the summary
line of its output. They must pass. Without a passing baseline nobody can tell
later whether the new work broke something.

## 4. Before starting

If the plan settles on a technology the tooling review did not know about,
follow `tooling.md` again. Put the regression commands and the run and test
commands into the project's context file. For a new project, commit the plan
(`git add -A && git commit -q -m "plan"`), so that every later tick shows up
in the history.

Set `phase: build` and `next: <first item>` in `STATUS.md`, read `build.md`
and continue.
