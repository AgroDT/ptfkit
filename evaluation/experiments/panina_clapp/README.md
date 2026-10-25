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
