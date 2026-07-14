# Working conventions (user directives, standing)

- **Evaluation standard**: frozen baseline; A/B on all 8 benchmark deliveries (or full 40
  for production claims); accept only significant GENERALIZED improvement; every change
  flag-gated with flags-off byte-identity PROVEN BY EXECUTION (cmp on real outputs, not
  reasoning); metrics read as a joint panel, never singly; same-camera collisions must stay 0.
  Primary axes: cross-camera agreement, distinct IDs vs ~13–15 roster, id-persistence,
  excess fragments, coloc; teleports are a noisy proxy (double-count occlusion re-acquisition
  — acceptable per the ID-constancy objective: occlusion teleports OK if the ID restores).
- **Composition principle**: judge fixes as composed stacks in pipeline order; don't drop a
  fix that hurts its own phase if later phases consume what it exposes.
- **Git**: NO AI/Claude co-authorship ever; short professional messages; user normally runs
  commits (they explicitly delegated one on 2026-07-14 — ask if unclear).
- **Monitors**: arm one at launch of EVERY long-running task, progress + failure coverage,
  report real wall-clock ETAs unprompted.
- **Mosaics**: render only when the user asks; roles shown ONLY in the roster panel (bottom
  right), never on player chips; body-paint identity overlay default ON.
- **Docs discipline**: fixes-log entry the moment a verdict lands (lab-notebook style);
  archived runs → docs/runs/ before deleting trees; open work lives ONLY in
  /remaining-work.md; wip/archive/ for executed plans.
- **User profile**: Quidich internship (PS-1); mentor meetings need clean docs + honest
  open-issues; the user reviews mosaics as final judge; prefers batch directives and
  timely unprompted progress updates.
- Laptop crashes historically (work in repo, sync often); it has been stable lately but
  don't leave long-running local state unsaved.
