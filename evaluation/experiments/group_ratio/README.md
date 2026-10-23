# Exhaustive group-size diagnostic

This mathematical experiment uses supplied constant forecasts, never fabricated
outputs attributed to published PTFs. Run from the repository root with an
environment containing the current `ptfkit-eval` package:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/group_ratio/calibrate.py --high-group-size 1 --output local/group-ratio-equal.json
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/group_ratio/calibrate.py --high-group-size 3 --output local/group-ratio-unequal.json
```

Each independent group is low or high with probability 1/2. Low groups contain
one sample with target zero. High groups contain either one sample (control) or
three samples, all with target one. Low samples have pressures 1 and 100 kPa;
high samples have 1, 10, and 100 kPa. Targets and forecasts are constant along
pressure, so the exact log-pressure loss equals the squared error.

The fixed candidates predict zero and one. Inner validation selects one of
them, with the preregistered lexical tie break choosing `one`. The ensemble
learns a constant convex weight on these two forecasts. Three outer folds and
two inner folds leave each outer rule trained on two independent groups.
The experiment enumerates all eight original datasets and ten bootstrap
multiplicity vectors, weighted by their exact multinomial probabilities.
Copied samples retain their original source group, preventing copies from
being split across training and assessment.

For constant forecast c and high-group size h, the population sample risk is
`R(c) = [c² + h(1-c)²] / (1+h)`. The estimand is the expected risk of a rule
trained on two IID groups. It is neither the conditional risk of a final model
trained on all three groups nor an interval for that model. Averaging the three
outer rules' conditional population risks equally, then averaging over the
eight datasets, recovers this two-group training-law estimand.

| High-group size | Atomic population risk | Ensemble population risk | Expected sample-weighted outer loss, atomic | Expected sample-weighted outer loss, ensemble |
| --- | --- | --- | --- | --- |
| 1 | 1/2 | 3/8 | 1/2 | 3/8 |
| 3 | 3/8 | 11/32 | 3/7 | 429/1120 |

These values have independent finite-state oracles. With h=3, the four equally
probable two-group training states give ensemble forecasts 0, 3/4, 3/4, 1.
Their population risks average to 11/32; the atomic rule's forecasts are
0, 1, 1, 1, giving risk 3/8. For original datasets with zero or three high
groups, every outer error is zero. With one high group, the sample-weighted
atomic and ensemble outer losses are 1 and 33/40; with two high groups, they
are 1/7 and 11/56. Each mixed count has probability 3/8, giving the table.

Only multiplicities (1, 1, 1) support all three outer folds. Their exact
probability is 3!/3³ = 2/9. Every other draw remains `insufficient_evidence`;
there are no retries or omitted failures. Successful draws reproduce the
original data and have zero spread. Conditioning on those successful draws
would therefore hide both the 7/9 failure probability and uncertainty.

No confidence interval or coverage claim is produced. This is a computability
and estimand calibration diagnostic for a deliberately small population.
It does not establish bootstrap failure rates for larger datasets or qualify
an inference method. Other missing-target mechanisms, hard-switch discontinuities, larger training
sizes, and actual interval coverage remain separate work.

## Informative missing targets

The registered missing-target scenario keeps three samples in every high group
but removes all target comparisons for its third sample. Low groups remain
fully observed. The missingness mechanism therefore depends on group state.
The complete latent roster remains present for all coverage denominators;
neither fitting nor selection receives the missing target. The experiment's
population oracle still refers to all latent samples, including missing targets.
The minimum coverage is explicitly changed to 2/3 before selection.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/group_ratio/calibrate.py --high-group-size 3 --missing-high-sample --output local/group-ratio-missing.json
```

The four two-group training states now give ensemble forecasts 0, 2/3, 2/3, 1.
Their full-population risks average to 25/72. Atomic choices remain 0, 1, 1, 1,
so their population risk remains 3/8. For original datasets with one high group,
observed sample-weighted atomic/ensemble outer losses are 1 and 13/18. With two
high groups they are 1/5 and 13/45. Their expectations are therefore 9/20 and
91/240. These exceed the corresponding full-population risks by 3/40 and
23/720. Every dataset records the original and eligible sample counts separately.

All three scenarios now call the package's `resample_grouped_forecasts`, which
shares sample-occurrence materialization with native run retraining. Its public
sample map retains original source, sample, group and occurrence identities.
This helper applies explicit counts; it does not define a bootstrap law or
qualify an uncertainty interval. The experiment continues to account for all
failed draws and has complete bootstrap probability 2/9 in this scenario too.
