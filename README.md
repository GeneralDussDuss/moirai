# Moirai

> The Fates spun, measured and cut every thread. Not even Zeus could overrule them.

A plugin pack for [Claude Code](https://claude.com/claude-code) that takes charge of the whole life of a session: how it starts, what it costs, when it stops, and whether you can trust what it says.

| Plugin | Myth | What it does |
|---|---|---|
| **[Clotho](plugins/clotho)** | spins the thread | Every session starts knowing where the work stands. A small per-project thread survives `/clear` and compaction, with automatic breadcrumbs and a `/clotho:wrap` handoff. |
| **[Atropos](plugins/atropos)** | cuts the thread | Stops runaway sessions: identical-call loops, the same failing command over and over, subagent overspawn, context bloat, and an optional spend cap. |
| **[Argus](plugins/argus)** | the hundred-eyed watchman | Checks claims against the transcript. No "all tests pass" without a test run after the last edit, no "pushed" without a push. |
| **[Cerberus](plugins/cerberus)** | guards the gate | Guards what the agent *does*: secrets leaving the machine, destructive commands, and prompt injection in fetched content. A tripwire, not a sandbox. |

## Install

```
/plugin marketplace add badussy/moirai
/plugin install clotho@moirai
/plugin install atropos@moirai
/plugin install argus@moirai
/plugin install cerberus@moirai
```

Install the whole set, or just the ones you want; each works on its own. They're plain Python 3 (stdlib only), with no dependencies and no network calls. Every hook fails open: if anything breaks inside a plugin, your session carries on.

## Tests

```
for p in plugins/*; do "$p/tests/run"; done
```

## License

MIT
