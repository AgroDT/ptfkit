# Exact hard-switch identification diagnostic

This experiment runs the actual nested learned-selector core on mathematical
curves with independently known population risks. It attributes no invented
predictions to published PTFs. Run from the repository root with the current
`ptfkit-eval` package installed:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/switch_instability/calibrate.py --high-group-size 1 --output local/switch-instability-equal.json
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/switch_instability/calibrate.py --high-group-size 3 --output local/switch-instability-unequal.json
```

Each independent source group has state A or B with probability 1/2. State A
contains one sample; B contains either one or three samples. All samples have
the exact pressure grid (1, 10, 100) kPa. Targets in A are (3/4, 1/4, 1/4);
targets in B are (3/4, 3/4, 1/4). The constant atomic curves predict 3/4 (`left`)
and 1/4 (`right`). A learned switch uses `left` at and below its boundary and
`right` above it. The registered boundary grid is (5, 10) kPa. Thus 5 exactly
matches A and 10 exactly matches B. The loss is sample-balanced trapezoidal
squared error on log10 pressure over [1, 100] kPa. Only already supplied eligible
forecast records enter selection; no native PTF execution or scientific source
eligibility is inferred by this experiment.

There are three outer folds and two inner folds, with at least one training and
validation group. Every inner fit sees one independent group and uniquely
identifies its boundary. An outer refit sees two groups; its best-minus-second
loss separation must exceed the preregistered 1e-12 gate. Atomic choices use
the registered lexical tie break (`left`). A tied learned boundary has no
default and remains `unidentifiable_boundary`.

All eight original datasets and ten probability-weighted bootstrap multiplicity
vectors per dataset are enumerated. Bootstrap copies retain their original
source/profile identities through `resample_grouped_forecasts`. No copies of
one group can inflate the independent-group count or enter opposite folds.
Artifacts retain full original and repeated selection evidence, sample lineage,
per-strategy statuses and failed-fit reasons. A successful atomic strategy never
silently changes a failed ensemble strategy into a complete result.

## Independent loss and risk oracles

At pressures (1, 10, 100), normalized trapezoid weights are (1/4, 1/2, 1/4).
A middle-pressure mismatch contributes (1/2)² / 2 = 1/8. The atomic error table is:

| Target state | `left` | `right` | Switch 5 | Switch 10 |
| --- | --- | --- | --- | --- |
| A | 3/16 | 1/16 | 0 | 1/8 |
| B | 1/16 | 3/16 | 1/8 | 0 |

For B-group size h, sample-weighted population state probabilities are
1/(1+h) and h/(1+h). The oracle averages over the four equally probable
two-group training states AA, AB, BA, BB. It never estimates an unknown target
from the same test errors being assessed.

With h=1, AB and BA tie. The training procedure therefore fails with probability
1/2; an unconditional ensemble risk is undefined under its registered failure
policy. On successful training states AA/BB its conditional mean risk is 1/16.
The quantity E[risk times the indicator of successful fitting] is 1/32. This
is reported as `risk_mass_on_success`, never as an unconditional model risk.
Atomic selection always succeeds and has population risk 1/8.

For a three-group dataset, every outer ensemble refit succeeds only when all
three states agree, probability 1/4. Those datasets have zero observed ensemble
outer loss. Conditioning on complete datasets would therefore report zero loss
despite positive population risk. In each mixed dataset two outer fits fail and
the remaining fit selects the opposite boundary from the held-out state.
The full strategy has no complete unconditional outer mean; failed folds are
neither dropped nor assigned zero error.

With h=3, mixed two-group training sets have three B samples and one A sample,
so boundary 10 wins uniquely. The four training states give switch boundaries
(5, 10, 10, 10), and their population risk averages to 3/64. Atomic choices are
(`right`, `left`, `left`, `left`), giving mean population risk 7/64. Original
datasets with zero/three B groups have ensemble loss zero and atomic loss 1/16.
With one B group, ensemble/atomic outer losses are 1/8 and 3/16; with two B
groups they are 1/56 and 9/112. Since each mixed count has probability 3/8,
expected sample-weighted outer losses are 3/56 and 13/112. Each exceeds its
corresponding training-law population risk by 3/448.

## Bootstrap computability and limits

Only multiplicities (1, 1, 1), probability 3!/3³ = 2/9, support all three outer
folds. Other draws retain insufficient-group evidence. In equal-sized mixed
datasets even the supported draw retains the boundary-tie failures, so its
ensemble completion probability is zero. Averaged over the original datasets,
the equal-size ensemble has complete bootstrap probability 1/18. The atomic
strategy has probability 2/9 throughout, and both unequal-size strategies also
have probability 2/9 throughout. Complete draws repeat the original data and
cannot supply an uncertainty interval from their spread.

This diagnostic qualifies no confidence interval or coverage claim. Its
explicit target is the risk and failure law of a rule trained on two IID
groups, rather than a final rule trained on all three groups. Finite-grid
identification failures, selective completion and informative group sizes are
separate obstacles; none is repaired by retrying or discarding failed draws.
