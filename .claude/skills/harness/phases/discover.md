# Phase: discover

Goal: build the plan on what is actually true - what the existing code does,
what has been published, what tools exist and how they behave, and what could
make the idea fail.

## 1. Choose the angles, and how deep to go

Look at the problem from each side it needs. Take the angles from
`INTENT.md`:

- an ambiguous point that facts could settle;
- a case that looks hard, or that you do not yet know how to verify;
- a term that may mean something specific in the field;
- what already exists: libraries, reference implementations, how others
  solved it (code, hybrid);
- what has been published: methods, the strongest results, baselines,
  datasets, how the field evaluates this (research, hybrid);
- how a library or tool behaves in the version that would be used;
- what this machine can and cannot run (`CLAUDE.local.md`).

Match the depth to the request. A small, well-understood task needs a few
facts checked, which takes minutes; a research question needs real reading.
Do not manufacture angles, and do not skip one the cases depend on.

## 2. Investigate, in parallel where the angles are independent

With two or more angles that do not depend on each other, run them side by
side: start one `scout` per angle in a single message, each with the request
verbatim, the one question it owns and what is outside it, and the file to
write (`.harness/analysis/<angle>.md`). Give each a bounded question sized to
the request, so that a small task gets a short answer. While they work, take
the angle that most needs your own judgment, or the quick checks, yourself.
A single angle, or something you can settle in a few minutes, you just do: an
agent would take longer than the check.

When scouts return, read their files critically. You make the decisions that
rest on these facts, so a claim that matters gets checked by you first-hand.

The rules of evidence, for you and for them:

- Check instead of recalling. Read the code, run the command, open the page.
  Software and papers change faster than memory.
- For a package: the registry for the current version, release date, Python
  support and licence; the documentation of the version that would be
  installed. Try the call the project would depend on, outside the project, in
  a temporary directory (`uv run --with <package> python -c "..."`), and keep
  the command and its output.
- For a paper or any source: open it. A search snippet is not a source. Cite
  only what you opened, and record what it says in its own terms. Where
  sources disagree, keep the disagreement.

Each angle ends as a note in `.harness/analysis/<angle>.md`: the answer, the
evidence behind it (URL, command and output, `file:line`), and what could not
be verified. Short notes for a small task are fine.

## 3. Synthesise, and argue against yourself

Write `.harness/SYNTHESIS.md`, in the language of the request:

- **What we now know**: the findings that shape the work, each pointing to its
  note and source.
- **Decisions**: the approach chosen, the alternatives rejected, and why.
- **What could make this fail**: make the strongest case against your own
  plan. Is the premise right, and is this already solved or known not to
  work? Can it be done and verified on this machine? Does the understanding in
  `INTENT.md` survive what you found? Which cases look hardest? For research:
  confounds, missing baselines, an evaluation that cannot tell the hypothesis
  from its alternative. For each point: what will be done about it, or why it
  is accepted.
- **Existing code**: where the work attaches and what must not change.

## 4. Feed it back into the understanding

Discovery often changes what the request should be taken to mean: a term turns
out to have a standard meaning, one reading turns out to be impossible, a case
nobody listed turns out to matter. Update `INTENT.md` and add a dated entry
under "Changes" with the reason.

If discovery shows the request cannot be met as understood (already solved,
impossible on this machine, built on a false premise), or that the readings
lead to results so different that guessing would waste the work, that is the
user's decision: set `status: waiting` with a `note:`, explain what was found,
and ask.

Add to the project's context file what must not be lost (the library and
version chosen, a trap found).

Set `phase: plan` and `next:` in `STATUS.md`, read `plan.md` and continue.
