# Independent investigation of the boundary coverage flag

The expanded study's van Genuchten--Mualem boundary cell remains flagged at
85/99 covered assessed regions. This follow-up investigates numerical and
sampling explanations without erasing the original result or tuning a
confidence threshold.

`boundary-followup-plan.json` fixes five independent blocks of 400 nonlinear
realizations and a separate 100000-draw linear control before execution. The
noise, true parameters, pressure grid, public fit/profile policies, nominal
level, and inference gates remain unchanged. The primary follow-up estimand is
nonlinear coverage conditional on an assessed region. Its one prespecified
one-sided test uses alpha 0.05. Block summaries and linear comparisons are
diagnostics, not additional prespecified rejection decisions.

```sh
python evaluation/experiments/retention_coverage/boundary_followup.py \
  --source local/retention-expanded-6800/van_genuchten_mualem_v1__dense__saturation_0.3__sigma_0.002.json \
  --output local/retention-boundary-followup
```

The original cell checksum is verified. The output directory must be new;
all independent fit/profile records and each block's counts are retained.
The original public fits are never replaced by diagnostic solves.

The independent curve/Jacobian implementation differentiates the published
equation analytically. A truth-initialized, tighter-tolerance solve audits
every original full-fit objective and every available nuisance profile at
the true saturation. Truth initialization is diagnostic only and is not
introduced into the public fitting policy or independent primary repetitions.

A fixed-design Gaussian linear control uses that Jacobian, the same original
noise vectors, QR least squares, and a Student-t coefficient interval. The
[NIST fitting reference](https://www.itl.nist.gov/div898/software/dataplot/refman1/ch3/fit.pdf)
provides the residual n-p and coefficient-inference basis. This linear
model has its own known true zero coefficient deviations; its error vectors
are shared with the nonlinear model but its response model is linear. The
positive saturation-deviation subset is an exact sign-selection control,
not a reproduction of all physical and numerical retention acceptance gates.
Joint-selection counts prevent comparing different subsets as if identical.

Independent tests check analytic derivative values and exact hand-calculated
linear designs with and without column coupling. They detect coefficient
selection errors, wrong residual degrees of freedom, and row/column covariance
factor confusion. No coverage guarantee for real observations follows from
these controls.

## Results

The analytic audits converged for all 200 original full fits and all 200
truth-fixed nuisance solves. None improved the public full-fit or available
profile SSE by more than 1e-10. On the original joint-selected cohort, both
the nonlinear method and exact linear control covered 85/99, with zero
classification disagreements. The larger linear-selected cohort covered
87/101; its different denominator must remain explicit.

The independent fixed series produced:

| Procedure / population | Covered / assessed | Estimate | Exact 95% simulation-probability interval |
| --- | ---: | ---: | ---: |
| Nonlinear, assessed regions | 937 / 992 | 94.46% | [92.84%, 95.80%] |
| Linear, positive coefficient deviation | 933 / 991 | 94.15% | [92.50%, 95.53%] |
| Large linear control, all draws | 94979 / 100000 | 94.98% | [94.84%, 95.11%] |
| Large linear control, positive deviation | 47536 / 50005 | 95.06% | [94.87%, 95.25%] |

The primary independent undercoverage test gave p=0.2343 at the prespecified
alpha 0.05. This did not reproduce the original substantial coverage shortfall.
Among 986 jointly selected independent realizations there were three coverage
classification disagreements. These controls are consistent with finite
simulation fluctuation as an explanation of the original signal; they do not
prove global adequacy, small-bias absence, or real-data coverage. The original
adjusted flag remains in the expanded-study report, and no threshold, box,
acceptance gate, or optimizer policy was altered to improve coverage.

`boundary-followup-summary.json` contains the count-only results and provenance.
Regenerate its verified report with:

```sh
python evaluation/experiments/retention_coverage/verify_boundary_followup.py \
  --directory local/retention-boundary-followup \
  --source local/retention-expanded-6800/van_genuchten_mualem_v1__dense__saturation_0.3__sigma_0.002.json \
  --output local/boundary-followup-verified.json
```

Verification checks the fixed plan, generator and diagnostic script hashes,
the original cell and unchanged public fitting implementation, all 2000
generated error vectors, paired counts and pooled primary inference, complete
fit/profile records for the first 400 realizations, and the full 100000-draw
linear-control result. Remaining blocks are checked for their generated inputs
and derived counts; their optimizations are not described as fully replayed.
