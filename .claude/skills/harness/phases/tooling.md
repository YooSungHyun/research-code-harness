# Tooling review

Do this once in the `understand` phase, and again if the plan settles on a
technology this review did not know about. It answers one question: would this
project be done better with Claude Code tooling that is not already available
(a plugin, an MCP server, a skill, a language server)?

Be sceptical by default. Every plugin adds instructions, processes and other
people's code to the session, so "nothing needed" is the common answer and a
good one. A dependency added to the project with `uv add` is often better than
a plugin.

## 1. What would actually help

From the request and the kind of work, list the capabilities the project needs
beyond reading, writing and running code: looking up current documentation for
a library, code intelligence for a language, driving a browser, querying a
particular service or database, searching papers. Only capabilities with a
concrete use in this project.

## 2. What is already there

- `claude plugin list --json` - installed plugins, their scope, enabled or not
- `claude mcp list` - configured MCP servers
- the skills and agents of this session, and the harness's own
  (`.claude/skills/`, `.claude/agents/`), including browser checking
- command-line tools on the machine (`command -v ...`); `CLAUDE.local.md`
  lists what is known

A need that is already covered needs nothing new.

## 3. What exists for the gaps

`claude plugin list --available --json` lists every available plugin with its
description. It is large: filter it with a short script instead of printing
it. `claude plugin details <name>@<marketplace>` shows what a plugin contains
and what it costs in context.

Weigh each candidate: what exactly it adds for this project; what it brings
along (hooks, background processes, MCP servers, credentials, context it
occupies); who publishes it; whether it works on this machine. A plugin can
run arbitrary code with the user's privileges, so the source matters:

- the official Anthropic marketplace (`claude-plugins-official`) and
  marketplaces the user has already added may be installed without asking;
- anything else needs the user's approval: put it in the one round of
  questions in the `understand` phase, with the reason it is worth asking.

## 4. Write TOOLING.md

`.harness/TOOLING.md`, in the language of the request: the needs and where
each will be used; what already covers which need; what you decided to
install and why, with the exact install and removal commands; what you
considered and rejected, a line each. End it with:

```markdown
## Installed by the harness
(nothing installed)
```

## 5. Install, record, reload

Install with local scope, so nothing outside this repository changes:

```bash
claude plugin install <name>@<marketplace> --scope local
claude mcp add --scope local <name> ...
```

After each install, replace `(nothing installed)` with one line per item:

```
- [installed] plugin <name>@<marketplace> (local) - remove: claude plugin uninstall <name>@<marketplace> -s local
```

Record only what you installed. What was on the machine before is not yours to
remove. Everything recorded here is removed in the `report` phase, and a hook
holds the session at the end until every `[installed]` line has become
`[removed]`.

A plugin installed during a session is not available in that session or to
agents started from it. So if you installed anything: set `status: waiting`
with `note: reload plugins`, tell the user what was installed and why, and ask
them to type `/reload-plugins` and then tell you to continue. When they do,
set `status: running` again. In a headless run, stop there; the run continues
with `harness-resume` in a new session.
