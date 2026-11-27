---
name: harness-resume
description: Continue an unfinished harness project in this session, or show where the projects stand. Use when the user wants to continue, resume or check on a project the harness started, after a session ended or was cleared, or when a project is waiting.
argument-hint: "[프로젝트 이름]"
---

# Resume a harness project

Your session id is `${CLAUDE_SESSION_ID}`.

1. **See what there is.** Each project keeps its state in the first lines of
   `projects/<name>/.harness/STATUS.md` (`status`, `session`, `phase`, `next`,
   sometimes `note`), and its progress in the checklist of
   `.harness/PLAN.md` (ticked and open items). Read them for every project in
   `projects/`. If the user only asked how things stand, report that in their
   language and stop here.
2. **Pick the project**: the name given as argument; otherwise the only
   unfinished one; if there are several, ask which.
3. **Look before continuing.**
   - `waiting`: the `note` says why. If it is a question for the user, put it
     to them and wait for the answer. If it is `reload plugins`, the plugins
     listed in `.harness/TOOLING.md` were installed for this project: they are
     active in a session started after the install, or once the user has typed
     `/reload-plugins`.
   - `waiting` with a note about stopping without progress: read the end of
     `STATUS.md` and the newest files under `.harness/evidence/` to see what
     it was stuck on, and say what you will do differently.
   - `done`: nothing to resume. New work on it starts with the `harness` skill.
4. **Take it over**: in `STATUS.md`, set `session: ${CLAUDE_SESSION_ID}` and
   `status: running`, and remove the `note` line. From now on the Stop hook
   keeps this session on the project.
5. **Load the context**: the project's `CLAUDE.md` (or `CLAUDE.local.md`),
   `.harness/INTENT.md` with the request in it, and `SYNTHESIS.md` and
   `PLAN.md` if they exist. You may have none of this in your context. The
   checklist in `PLAN.md` shows what is done: the first open item is where the
   work stands.
6. **Continue**: read `.claude/skills/harness/SKILL.md` for how a run works and
   `.claude/skills/harness/phases/<phase>.md` for the current phase, then carry
   on from the `next` line without asking the user.
