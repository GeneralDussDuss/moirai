# Moirai

> The Fates spun, measured and cut every thread. Not even Zeus could overrule them.

A plugin pack for [Claude Code](https://claude.com/claude-code) that takes charge of the whole life of a session: how it starts, what it costs, when it stops, and whether you can trust what it says.

**[See the showcase →](https://generaldussduss.github.io/moirai/)** · a tour of the pack anyone can follow, no coding knowledge needed. ([Mirror](https://claude.ai/artifact/VW9pKYaw8vvo2nM76X3XpK))

> [!IMPORTANT]
> **Testers wanted.** Moirai is brand new (v0.1). It's tested by script and in daily use on one machine, and now it needs yours. Install it, work normally, and tell us what happens:
> - a plugin blocked or warned about something it shouldn't have (false alarm)
> - it missed something it should have caught
> - anything confusing, slow, noisy or broken
>
> The [testing guide](TESTING.md) has drills for pushing each plugin safely and a checklist for a good report. Then [open an issue](https://github.com/GeneralDussDuss/moirai/issues/new/choose) with what you ran and what the plugin said. Ideas for new plugins are just as welcome.

| Plugin | Myth | What it does |
|---|---|---|
| **[Clotho](plugins/clotho)** | spins the thread | Every session starts knowing where the work stands. A small per-project thread survives `/clear` and compaction, with automatic breadcrumbs and a `/clotho:wrap` handoff. |
| **[Lachesis](plugins/lachesis)** | measures the thread | Routes each step to the cheapest model that can do it well: a Haiku scout, a Sonnet worker, a usage audit that shows where your plan went, and a status line meter. |
| **[Atropos](plugins/atropos)** | cuts the thread | Stops runaway sessions: identical-call loops, the same failing command over and over, subagent overspawn, context bloat, and an optional spend cap. |
| **[Aletheia](plugins/aletheia)** | the spirit of truth | Checks claims against the transcript. No "all tests pass" without a test run after the last edit, no "pushed" without a push. |
| **[Cerberus](plugins/cerberus)** | guards the gate | Guards what the agent *does*: secrets leaving the machine, destructive commands, and prompt injection in fetched content. A tripwire, not a sandbox. |

## Install

```
/plugin marketplace add GeneralDussDuss/moirai
/plugin install clotho@moirai
/plugin install lachesis@moirai
/plugin install atropos@moirai
/plugin install aletheia@moirai
/plugin install cerberus@moirai
```

Install the whole set, or just the ones you want; each works on its own. They're plain Python 3 (stdlib only), with no dependencies and no network calls. Every hook fails open: if anything breaks inside a plugin, your session carries on.

## Tests

```
for p in plugins/*; do "$p/tests/run"; done
```

## Feedback

Every report makes the Fates sharper. False alarms matter most: a plugin that nags gets uninstalled, so if one gets in your way, [tell us](https://github.com/GeneralDussDuss/moirai/issues/new/choose). Paste what the plugin said, the command or claim involved, and which plugin version you run (`/plugin` lists them). `/cerberus:log`, `/atropos:status` and `/aletheia:audit` show what each one caught.

## License

MIT
