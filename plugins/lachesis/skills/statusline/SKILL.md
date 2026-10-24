---
name: statusline
description: Show how to add the Lachesis status line (model, effort, context, session cost, plan limits) to ~/.claude/settings.json, with the real installed path filled in.
model: haiku
effort: low
disable-model-invocation: true
---

Run this and show the user its output verbatim:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/lachesis-statusline" --setup
```

Then tell the user to merge the `statusLine` block into `~/.claude/settings.json`
themselves (plugins can't set it), or offer to do it if they ask. If they already have a
`statusLine`, point that out before replacing it.
