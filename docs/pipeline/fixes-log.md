# Fixes log (moved)

The A/B campaign ledger has been combined into the single authoritative methods log at
[`../methods_log.md`](../methods_log.md).

That file carries the master status table (every method, its A/B result, pros and cons, status, and
whether it is on or off by default), this session's work, and Part D, which condenses the v6 to v8.1 fix
campaign that used to live here (F0 to F15, the waves W1 to W10, the roles solver, the detector
bake-off, W9 union-lift, and the 40-delivery production record).

The full original per-fix narrative (969 lines, historical, with paths accurate as of each dated entry)
is preserved in git history:

```
git log --follow docs/pipeline/fixes-log.md
git show <rev>:docs/pipeline/fixes-log.md
```
