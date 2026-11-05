# Source-reviewed Clapp external check

The 24 complete raw texture candidates were audited against their original
publications. `evaluation/datasets/meta_v3_3.clapp-source-review.json` records
the source hashes and exact selected master identities.

| Source | Candidates | Decision |
| --- | ---: | --- |
| Badenko 2013 | 6 | USDA class not established by the reviewed experimental table |
| Bolotov 2014 | 3 | Russian texture groups / laser intervals do not establish the needed USDA class |
| Panina 2015, gray forest profile | 6 | Source-reported silt loam; supported by Clapp |
| Panina 2015, sod-podzolic profile | 6 | Source-reported silt; absent from Clapp's eleven classes |
| Moiseev 2018 | 3 | USDA class not established for the matched horizons |

[Panina's thesis, printed p. 88, Table 17](https://soil.msu.ru/attachments/article/2063/Panina_Disser.pdf)
reports international classes used with HYDRUS/ROSETTA. The
[USDA-hosted HYDRUS manual, section 3.8](https://www.ars.usda.gov/arsuserfiles/20361500/pdf_pubs/P2164.pdf)
identifies that classification as USDA. The named natural gray forest mineral
profile and its horizon descriptions support the reviewed material basis.
No class is inferred from Russian abbreviations or retention-curve behavior.
The first workbook horizon spans 0--10 cm; both source subintervals, 0--5 and
5--10 cm, have the same class. No particle-size or density values are averaged.

```sh
python evaluation/experiments/panina_clapp/run.py \
  --dataset local/meta-v3-3-canonical-export.json \
  --paper local/source-review/panina2015.pdf \
  --output local/panina-clapp-new-run
```

The output directory must be new. The builder verifies canonical/workbook/PDF
hashes, exact identities, master-row lineage, supported categories and reviewed
material. It preserves every selected pressure/water measurement and source
cell, adds the published categorical predictor with its PDF lineage, and
validates the resulting canonical dataset. Predictor origin is `measured`:
the input is the published observed soil class, directly transcribed, rather
than a locally calculated classification or an estimate from target curves.
The global workbook mapping and its blocked raw category binding are unchanged.

All six horizons share one profile identifier. The fixed Clapp model is not
calibrated, selected, or modified using these targets. The run produces native
predictions, lineage, eligibility, errors and an integrity-checked report.
The 56 retained points span approximately 6.78 to 257941 kPa; this does not
establish a validated pressure domain for the original PTF.

The result has six eligible horizons and 56 eligible points, with sample-equal
weighting and prediction-minus-observation errors:

| Metric | Volume fraction |
| --- | ---: |
| ME | 0.0288498422 |
| MAE | 0.0305541769 |
| RMSE | 0.0350360985 |
| Median absolute error | 0.0325632289 |

Cluster confidence intervals are withheld (`too_few_groups`), because there is
one independent profile. These are descriptive external-check results, not
population validation, national representativeness, or a model-ranking result.
The count/metric summary is versioned as
`evaluation/datasets/meta_v3_3.clapp-pilot-summary.json`; raw observations and
native run artifacts remain local. Separate-process reading, byte-identical
original-plan replay and persisted-plan prediction/cohort replay were verified.

On Windows, artifact publication now uses a normal destination-parent staging
directory, so published output inherits that parent's access controls. The
previous temporary-directory ACL could remain attached to the renamed output
under Python 3.13. Publication still uses exclusive staging and atomic rename;
failed writes remove their own staging without publishing a partial run.

## One-command workbook pilot

Run from the repository root in the prepared project environment:

```sh
mise run eval:pilot local/meta_v3.3.xlsx local/source-review/panina2015.pdf local/panina-pilot
```

The output directory must be new. The equivalent direct command is:

```sh
uv run --project targets/ptfkit-eval --no-sync python evaluation/experiments/panina_clapp/pilot.py \
  --workbook local/meta_v3.3.xlsx --paper local/source-review/panina2015.pdf \
  --output local/panina-pilot
```

This command normalizes the exact reviewed workbook, exports the canonical
volumetric dataset, applies the checksum-bound source overlay, executes the
existing fixed Clapp plan, fits all four registered reference families, and
writes `decision/summary.json` and `decision/report.md`. The report contains
separate PTF and per-horizon approximation tables. It checks the fitting
dataset, sample/family roster and original observations against the evaluated
dataset. Measurements, parameters and detailed intervals remain local.

`clapp/artifacts/` retains native predictions, eligibility/point decisions,
exclusions, coverage, maximal/common cohorts, metrics, the registered
profile-bootstrap plan and its insufficient-evidence result. The separate
`approximation-fits.json` retains all optimizer attempts, parameters, parameter
intervals, mean-curve intervals, conditional prediction intervals and support
diagnostics. The fitting policy reuses the measured-retention experiment's
original boxes, seed and three starts; workbook-stored parameters are unused.

The real six-horizon run accepted five of 24 fits: three van Genuchten--Mualem
and two van Genuchten m=1. Brooks--Corey produced five boundary failures and one
nonidentifiable fit; Clapp gradual air entry produced six nonidentifiable fits.
Five parameter interval sets exceed their fit boxes, three conditional
prediction interval sets exceed physical water bounds, and none of the five
mean-curve interval sets does. Intervals retain their original endpoints.
They are conditional local-linear Student-t approximations; residual assumptions
and interval coverage have not been validated for these observations.

This is still an **incomplete selection vertical slice**. The pilot executes
one atomic candidate on one profile. It reports `insufficient_evidence` for
selection stability, outer strategy performance, final atomic recommendation
and final ensemble recommendation. Clapp is not labelled a selected winner.
The complete PTF catalog has not been scored by this pilot; the separate
catalog readiness matrices remain diagnostic evidence, not eligibility grants.

The next focused source is Bolotov 2014. Its reviewed paper, printed pp. 37--38,
describes laser diffraction with ultrasonic preparation and sand fractions of
50--1000 micrometres. Its Russian texture names do not establish the required
USDA classes. Recover exact horizon-level USDA class evidence, then bind the
profile, depth and mineral-material evidence to workbook identities. Do not
infer classes from the published curves or convert the particle-size methods
by assumption. If this evidence is unavailable, the source remains blocked.
Even a successful class review would still require a justified population and
grouped split: three profiles within one source do not establish independent
source replication or by themselves unlock the intended nested assessment.
