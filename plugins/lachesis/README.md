# Lachesis

The Fate who measures the thread. Lachesis gives each task the model it deserves: the
expensive model keeps the thinking, a Haiku scout does the reading, a Sonnet worker does the
executing, and an audit shows where your usage actually went.

Most of a session's cost is not thinking. It is the main conversation re-reading its own
context on every step. Lachesis loads a short routing policy into every session, ships the
helpers it routes to, and measures the result.

## What's in it

| Piece | What it does |
|---|---|
| `policy.md` + SessionStart hook | Loads the routing policy into every session, including after `/clear` and compaction. Edit it to tune the routing. |
| `lachesis:scout` | Haiku, low effort, read-only. Lookups that take 3+ reads; returns a short answer with `file:line` references. |
| `lachesis:worker` | Sonnet, medium effort. Well-briefed execution with a done-check. |
| `/lachesis:quick <ask>` | Runs one turn on Haiku. Your own model returns on the next message. |
| `/lachesis:cheap <task>` | Runs one turn on Sonnet. |
| `/lachesis:audit [--days N]` | Prices and classifies every call in your transcripts and explains where usage went. |
| `/lachesis:statusline` | Prints the snippet that adds the status line to your settings. |
| `bin/lachesis-statusline` | Status line: model, effort, context, session cost, 5h/7d plan use. |

## Install

```
/plugin marketplace add <owner>/moirai
/plugin install lachesis@moirai
```

## Status line

Plugins cannot register a status line, so this one step is manual. Run:

```
/lachesis:statusline
```

It prints a `statusLine` block with the real installed path of `bin/lachesis-statusline`.
Merge it into `~/.claude/settings.json`:

```json
{
  "statusLine": { "type": "command", "command": "/path/printed/by/the/skill/bin/lachesis-statusline" }
}
```

You get `Opus · medium · ctx 120k · $4.21 · 5h 42% · 7d 18%`. Context turns yellow past
150k and red past 250k; plan limits turn yellow at 70% and red at 90%. Fields Claude Code
doesn't send are left out. The path points into the plugin's install directory, so if a
plugin update moves it, run `/lachesis:statusline` again.

## How the audit works

`bin/lachesis-audit` (also behind `/lachesis:audit`) reads your Claude Code transcripts in
`~/.claude/projects` (or `$CLAUDE_CONFIG_DIR/projects`), including subagents, and:

- prices every API call at list rates from a built-in model table (edit `PRICES` at the top
  of the script when rates change);
- splits cost into context re-reads, cache writes, uncached input and output;
- classifies what each expensive-model call did (read, edit, answer, delegate);
- finds runs of 3+ cheap-looking calls that a Haiku scout or Sonnet worker could have done,
  and short turns that `/lachesis:quick` would cover, with an estimated saving;
- ranks what bloated your context, weighted by how many steps re-read it.

```
bin/lachesis-audit --days 7            # last week
bin/lachesis-audit --project myrepo    # transcript folders containing "myrepo"
bin/lachesis-audit --json              # machine-readable
```

Costs are list-price estimates for comparing models, not a bill. On a subscription they
show where plan headroom goes. Everything runs locally; nothing is uploaded.

## What Claude Code allows

- Only you can switch the main session's model; hooks can't. That's why Lachesis routes
  work to helpers instead.
- A subagent's `model` frontmatter beats `CLAUDE_CODE_SUBAGENT_MODEL`; a per-call `model`
  on the Agent tool beats both.
- A skill's `model` applies for the rest of that turn only.
- The status line is the only place that exposes cost, context and plan-limit fields.

## Notes

- Python 3 stdlib only; no network calls. The hook fails open.
- `policy.md` is loaded into every session, so it costs context everywhere. Keep it short.
- Works well with [Clotho](../clotho): the policy suggests `/clotho:wrap` before `/clear`
  when Clotho is installed.

## Tests

```
plugins/lachesis/tests/run
```
