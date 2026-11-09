# Synthetic whole-group retraining sensitivity

This example has twelve synthetic sources, two samples per source and five
pressure observations per sample. It reuses the committed candidate definitions
from `../synthetic_retention/` and registers sixteen whole-source bootstrap
draws with seed 20261023. Its values demonstrate execution only; they are not
measurements, accuracy evidence or a source-exchangeability claim.

From the repository root:

```sh
mise run eval:sync
uv run --project targets/ptfkit-eval ptfkit-eval plan evaluation/examples/synthetic_retraining/run.json
uv run --project targets/ptfkit-eval ptfkit-eval run evaluation/examples/synthetic_retraining/run.json --output local/retraining-demo
uv run --project targets/ptfkit-eval ptfkit-eval report local/retraining-demo
```

Each draw samples twelve original source groups with replacement. Repeated
sources retain their source/profile identity, so all occurrences stay in the
same fold. Occurrence sample IDs are explicit bookkeeping, not independent
new soils. The run repeats inner candidate selection and convex fitting,
outer-training refits, and outer assessment on the resampled cohort. Fixed PTF
predictions and upstream scientific eligibility are cached without change.

The original-group gate is eight. Individual draws can have fewer distinct
groups; the registered selection/fitting gates decide whether each is computable.
Insufficient draws are retained, never retried. For this fixture and seed the
sixteen draws have 6 to 9 distinct groups and all sixteen support both strategies.

`selection-resampling.json` preserves every multiplicity, occurrence-to-original
sample/observation map, derived dataset checksum, repeated fit, choice and
assessment. Complete run directories can be replayed from portable snapshots.
The artifact can be large because it retains full nested evidence.

These are retraining sensitivity trajectories. There is no confidence level,
confidence interval, prediction interval or coverage guarantee. In particular,
an empirical range over successful draws must not be reported as an inferential
interval while ignoring failed draws. See the
[inference qualification note](../../../docs/src/contributing/ptfkit-eval-inference.md)
for the unresolved statistical requirements.
