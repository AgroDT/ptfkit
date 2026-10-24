# Nonlinear retention profile coverage pilot

This experiment exercises all four registered retention families under a
correctly specified synthetic model. It is a pilot for failure-aware coverage
accounting, not a qualification of retention uncertainty on real measurements.

```sh
python evaluation/experiments/retention_coverage/calibrate.py \
  --repetitions 50 --seed 20261024 \
  --output local/retention-profile-coverage.json
```

The output must be new. Each family uses an interior saturation truth of 0.5
and a lower-box-boundary truth of 0.3. Synthetic observations use independent
Gaussian noise with standard deviation 0.002 on the recorded pressure grid.
The first three generative equations are explicit van Genuchten and
Brooks--Corey formulas. Clapp uses saturation and dry power-branch points, with
no positive pressure sampling its gradual wet branch. This is therefore a
limited control for that family, not validation of its entire pressure range.

Every noisy realization is counted. Physically invalid volume fractions are
recorded and withheld without clipping, smoothing, or replacement draws.
Each valid realization runs the unchanged bounded multistart fit policy.
Boundary, identifiability, and other fit failures remain in detailed records.
Accepted fits receive a saturation profile whose grid includes both bounds,
the fitted estimate, and the known true value. This eliminates interpolation
error for the coverage event without treating the true value as training input.
Fits never receive that true value as an optimizer start.

Profile assessments retain incomplete calculations and lower-objective
counterexamples as unavailable. There is no rescue refit, retry-until-success,
or automatic bound widening in this pilot. A coverage frequency must use the
reported `assessed` denominator; `fitted` and `generated` denominators answer
different questions. In particular, `covered/generated` is the probability of
returning a covering region, including abstention, rather than conditional
coverage among returned regions. A missing count is zero.

The artifact retains all fit/profile/region records, generator parameters,
seed, environment, and script hash. Fifty repetitions per scenario give weak
Monte Carlo precision (roughly three percentage points standard error near
95%, before failures reduce the denominator). These runs cannot establish
nominal coverage or transfer to real-data residual distributions. The pilot
extends the previously reviewed extra-SSE method and Gaussian mean control;
it does not introduce a new confidence threshold.

The fixed 50-repetition pilot produced:

| Family | Saturation truth | Fitted / generated | Assessed | Covered |
| --- | ---: | ---: | ---: | ---: |
| van Genuchten--Mualem | 0.5 | 50 / 50 | 50 | 49 |
| van Genuchten--Mualem | 0.3 | 21 / 50 | 21 | 21 |
| van Genuchten m=1 | 0.5 | 50 / 50 | 50 | 47 |
| van Genuchten m=1 | 0.3 | 24 / 50 | 24 | 24 |
| Brooks--Corey | 0.5 | 50 / 50 | 44 | 41 |
| Brooks--Corey | 0.3 | 27 / 50 | 23 | 21 |
| Clapp gradual air entry | 0.5 | 50 / 50 | 50 | 45 |
| Clapp gradual air entry | 0.3 | 26 / 50 | 26 | 21 |

All 102 fit failures were boundary solutions. Ten Brooks--Corey profiles found
a lower objective and withheld the region assessment (six interior, four at the
boundary truth). No coverage estimate should hide these ten unavailable
assessments. Clapp's 45/50 interior and 21/26 selected-boundary coverage also
motivate larger, prespecified calibration runs; this small pilot does not
establish coverage failure or adequacy for a family.

Add `--pressure-restarts` to compare the explicit
`brooks_corey_pressure_partitions_v1` restart policy. It appends starts at each
observed pressure knot strictly inside the air-entry box and geometric
midpoints of every resulting pressure partition. Other initial parameters
remain at the declared initial start. The original seeded starts remain first.
Only pressure coordinates determine these starts, and parameter bounds and
acceptance gates are unchanged. Nuisance profiles use the same added locations
when air entry is free. This is an engineering restart policy, not a global
optimization certificate or a change to the Brooks--Corey equation.

With the same seed, the generator draws exactly the same noisy observations
under either policy; this permits a paired optimizer comparison. Keep both
artifacts and all failures rather than choosing a policy from coverage alone.

The paired 400-realization comparison replayed byte-for-byte and verified
identical generated observations against the original artifact. Among the 100
Brooks--Corey fits, 18 reduced best converged SSE by more than 1e-10; none
increased it beyond numerical tolerance. Profile counterexamples were not
eliminated: seven interior and two boundary-truth assessments were withheld,
versus six and four under the original policy. Assessed/covered counts became
43/40 and 25/22, respectively. More profile starts can expose counterexamples
that the original profile solver missed. The policy therefore remains optional
and unqualified; these results do not establish optimality or better coverage.

Add `--interval-solves` instead of `--pressure-restarts` for
`brooks_corey_interval_solves_v1`. This preserves the original full-box solves,
then repeats every seeded start within every closed air-entry interval formed
by the observed pressure knots and original box endpoints. Each local attempt
records `air_entry_interval`. Other parameter boxes remain unchanged; local
interval edges do not become scientific parameter bounds or trigger physical
boundary rejection on their own. Profiles use the same interval solves when
air entry is free. Profiled air-entry values remain fixed and need no partition
solve. The two optional policies cannot be requested together.

On the same 400 realizations, interval solves removed all Brooks--Corey
lower-objective profile counterexamples in this pilot. Interior truth had
50 accepted/assessed fits and 47 covering regions; boundary truth had 25
accepted/assessed fits, 25 boundary failures, and 21 covering regions. The
original policy accepted 27 boundary-truth fits, so two formerly accepted
solutions now correctly resolve to boundary failures. The original policy and
results remain available. The 21/25 selected-boundary coverage is still not
nominal 95% evidence, and the finite local solves do not certify global optima.
