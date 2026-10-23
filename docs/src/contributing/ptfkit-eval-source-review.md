# Evaluation source review

Reviewed online on 2026-10-23. This record separates published evidence from
ptfkit design decisions. It complements the inference derivations and the
workbook-specific evidence in the handoff; it does not approve unresolved
measurement contracts or replace the missing original workbook papers.

## Training uncertainty

| Primary source | Evidence checked | Consequence for ptfkit |
| --- | --- | --- |
| [Bengio and Grandvalet (2004), abstract and main result](https://www.jmlr.org/papers/v5/grandvalet04a.html) | No universally unbiased K-fold CV variance estimator under unrestricted distributions; fold error correlations matter. | Do not use an independent-fold standard error for overlapping CV. This is not an impossibility theorem for bounded-loss confidence procedures. |
| [Bates, Hastie, and Tibshirani, Sections 1 and 2](https://arxiv.org/pdf/2104.00673) | Fitted-dataset risk and average training-dataset risk are different targets; their formal OLS results have specific assumptions. | Name the target and effective training size. Do not generalize the OLS result into a universal claim about every PTF selector. Their statistical nested-CV construction does not qualify our inner tuning loop. |
| [Hoeffding (1963)](https://doi.org/10.1080/01621459.1963.10500830) | Concentration for independent bounded random variables. | Use independent original groups or independent blocks at the appropriate level, with prior bounds. The informative-size ratio, training-failure mass and simultaneous policy allocation are our separately documented derivations. |

[Varma and Simon (2006), Background and Conclusion](https://link.springer.com/article/10.1186/1471-2105-7-91)
explicitly treat parameter search as part of the training algorithm and repeat
that complete algorithm inside external validation. Their classification
experiments support the isolation requirement, not our group-population ratio
or bounded-loss confidence guarantee. The finite-grid block experiment now
executes inner fitting and outer refitting through the public selector, rather
than supplying manually invented learned-model losses. Its exact informative-
size/failure law remains our own application-specific calculation.

The independent-block construction is documented in
`evaluation/experiments/training_law_risk/README.md`. Published bounded-mean
concentration does not establish that our datasets are IID, that administrative
identifiers are value-independent, or that losses satisfy population bounds.
Exact finite experiments check the implemented construction on specified laws;
they do not establish those assumptions for the workbook.

## Hydraulic evaluation and corrected measurement semantics

[Weynants, Vereecken, and Javaux (2009), Materials and Methods](https://acsess.onlinelibrary.wiley.com/doi/full/10.2136/vzj2008.0062)
use an independent forest dataset with multiple horizons per profile. Their
reported evaluation restricts that dataset to the training predictor ranges.
This supports preserving profile membership and explicitly labelling
inside-domain results. It does not demonstrate independence of horizons or
performance outside those ranges. Their direct hydraulic-data coefficient
fitting also distinguishes fitting uncertainty from external prediction error.
These observations motivate evaluator design; they are not a reproduction of
that study or evidence about the workbook's measurement conventions.

The publisher links a
[2017 erratum by Weihermueller et al.](https://acsess.onlinelibrary.wiley.com/doi/full/10.2136/vzj2008.0062er).
Its corrections to Tables 3 and 6 specify organic carbon in mass percent, bulk
density in g/cm3, and texture fractions on a fine-earth mass basis with a 2 mm
upper boundary. A future Weynants adapter or specification review must check
this correction rather than relying on the uncorrected unit presentation.
This correction belongs to the 2009 model; it does not authorize changing the
existing Vereecken 1989 contract or interpreting an undocumented workbook column.
There is currently no Weynants source specification in `specs/functions/`.

[Vereecken et al. (2010), validation and metadata sections](https://acsess.onlinelibrary.wiley.com/doi/full/10.2136/vzj2010.0045)
provide a methodological review, not a primary measurement record for our
workbook. They distinguish independent-data evaluation from development-set
performance and discuss experimental protocol and scale compatibility. Their
cross-study comparisons cannot be used as numeric acceptance thresholds for
our differently weighted losses. Source-specific measurement evidence remains
necessary before external scoring.

## Decisions and outstanding evidence

- Keep conditional fitted-rule risk, training-average risk, prediction intervals
  and fitted-parameter uncertainty as separate outputs.
- Preserve original source/profile groups and all training failures. Neither
  bootstrap copies nor pressure points create independent training datasets.
- Register eligibility, pressure domain, loss, bounds and candidate roster
  before assessment; retain excluded and outside-domain records explicitly.
- Check linked corrections when reviewing each PTF publication. The Weynants
  finding is a review note, not an implementation or a promoted source rule.
- Sapozhnikov 1988 and Kokareva 2007 remain unresolved as recorded in the
  handoff. This review did not recover their original measurement methods.
- Native whole-selector block reruns, run-policy registration and complete
  block provenance are now implemented for the bounded independent-block
  construction. Scientific sampling and population assumptions remain external.

`allocate_independent_training_blocks` now supplies the identity-only allocation
substrate. It requires exactly the preregistered number of original groups,
preserves every sample once, and rejects unresolved profile identities. It does
not itself run a learner or confer scientific independence on source/profile labels.
The separate native adapter now performs complete training-only selector reruns
and retains every failed training and unavailable successful-test loss.


## Structured validation and prediction scope

[Roberts et al. (2017)](https://doi.org/10.1111/ecog.02881) review structured
cross-validation and include simulation/case analyses. Their discussion shows
why validation blocks must reflect dependence and the intended interpolation or
extrapolation task. Blocking can alter predictor-space coverage; arbitrary
blocking is not a proof of the desired prediction target. For ptfkit, this
supports explicit source/profile roles and inside/outside-domain reporting.
It does not establish IID publication groups or qualify our risk intervals on
the workbook. The bounded independent-block policies still require a separately
justified population law and value-independent allocation. Synthetic examples
supply their own explicit laws; real-source labels alone supply neither fact.


## Point-score functionals and aggregation

[Gneiting (2011), Making and Evaluating Point Forecasts](https://doi.org/10.1198/jasa.2011.r10138)
provides original theoretical characterizations as well as a literature review
and a forecasting simulation. The [author preprint](https://arxiv.org/abs/0912.0902)
was inspected, including section 1.1 and its definition of an average score.
Absolute and squared errors assess different forecasting objectives; weighting
also affects what is assessed. RMSE is a monotone transformation of average
squared error. This supports preregistering each score and its averaging unit.
It does not prove our independent-block confidence construction or establish
that a log-loss-trained ptfkit selector is optimal for MAE.

The point-risk adapter keeps log-pressure selection fixed and evaluates two
separate sample-balanced scores. For sample i with n_i eligible common points,
L_i = sum_j |error_ij| / n_i or sum_j error_ij**2 / n_i. Its population target
averages these per-sample losses, rather than pooling all pressure rows.
The MSE interval can be transformed by an increasing square root to cover the
square root of training-average MSE. This is our mathematical consequence,
not a claim from the paper about expected per-training RMSE. In general,
sqrt(E_T MSE_T) differs from E_T sqrt(MSE_T). No interval for the latter is
currently emitted. Missing points and unsuccessful training remain distinct.


## Nonlinear gates and the meaning of mixture output

[Jacobs, Jordan, Nowlan and Hinton (1991)](https://doi.org/10.1162/neco.1991.3.1.79)
introduce adaptive mixtures of experts. The [author-hosted text](https://people.eecs.berkeley.edu/~jordan/papers/mixtures-of-experts.pdf)
was inspected, especially equations 1-3 and the normalized gating outputs.
The paper distinguishes squared error of a blended output from a stochastic
expert selection objective and from mixture likelihood. Its training algorithm
also adapts expert networks. These are different statistical models.

The ptfkit pressure sigmoid is a deterministic convex blend of fixed atomic
forecasts, selected by finite-grid log-pressure loss. It does not implement the
paper's stochastic expert switch, mixture likelihood, learned expert coefficients
or soil-covariate network. Input-only evaluation and locked outer parameters
remain explicit contracts; the publication supplies architectural context, not
scientific calibration or interval coverage for our implementation. Pressure
monotonicity and parameter uncertainty still require their own checks.

## Clapp-Hornberger curve convention

[Clapp and Hornberger (1978)](https://doi.org/10.1029/WR014i004p00601)
was inspected in a [scan of the original four-page article](https://scispace.com/pdf/empirical-equations-for-some-soil-hydraulic-properties-4hsglsjqwf.pdf).
Equations 1 and 3 join a power curve to a near-saturation parabola. The stated
positive-parabola condition is W_i > b/(b+1). At the registered W_i=0.92,
this gives b<11.5 for the complete curve, including when evaluating a dry point.
The representative suction uses the antilog of the mean log suction, rather
than the arithmetic-mean column. No source-specification change was needed.

The Methods section describes desorption measurements on a mass basis at five
controlled tensions, density-based conversion and head in centimeters. These
facts describe the original population, not the external workbook's methods.
The paper makes no hysteresis correction, and its between-soil variability is
not a confidence interval for an individual prediction or a tuned ensemble.

Review also motivated numeric controls derived from the same equations:
dimensionless pressure ratios and a rationalized parabolic root preserve scale
invariance. Those algebraic changes are implementation reasoning, not additional
scientific assumptions or evidence of external-data eligibility.


## Real-workbook pressure-label corrections

[Bolotov et al. (2014), chestnut soils](https://www.asau.ru/vestnik/2014/9/036-041.pdf),
printed pp. 38-40, Figures 4-6, reports positive pressure in kPa and volumetric
water content in cm3/cm3. The 12 workbook curves match the three four-horizon
profiles. Their axis range -0.592095 to 3.05 reconstructs the plotted pressure
range only as log10(kPa), despite the raw `pF` cell label. Applying the standard
pF conversion would lower every pressure by a factor of about 10.197. The
mapping preserves the raw label and declares the reviewed physical representation.
All 168 positions match between sheets, including one explicit null. Twelve
confirmed full-curve crosswalks repair the permuted long-sheet sample numbering;
167 numeric observations are normalized. The source also specifies laser PSD
with a 50-1000 micrometer sand interval and combustion-derived carbon; those
facts do not satisfy the currently registered sieve/Walkley-Black input contracts.

[Makarychev et al. (2014), orchard chernozem](https://www.asau.ru/vestnik/2014/12/035-039.pdf),
printed pp. 37-38, Figure 2 and its table, explicitly reports centrifuge drainage
against volumetric content and positive kPa. Its four workbook curves reproduce
the figure, including the near-0.25 to 1070 kPa axis range as log10(kPa).
Four confirmed complete-curve crosswalks and unchanged water scaling unlock all
56 observations. This is a source-specific correction, not a global reinterpretation
of workbook pF. Source specifications and generated PTFs are unaffected.

The local reviewed PDF SHA256 digests are
`e05eef190ba57a0f2b6118676314baf0716c6da5538f2a10d96cb6432ae1d1cd`
(Bolotov) and
`29a6bc81352f6a6656c512c4dc382e5a00e65c87cd5353598858d7d97eb0e5ac`
(Makarychev). Only count summaries and scientific mapping evidence are versioned.


[Makarychev and Lebedeva's primary monograph (2021)](https://www.asau.ru/news/social-work?fileid=24217&task=getfile),
pp. 15-16 and 63-64, Figures 31-33, independently corroborates the workbook's
2018-labelled arboretum block. Gravimetric W is plotted in percent; six pF levels
reproduce the positive kPa grid. Six birch, five grass and five retained oak
horizons match the plotted profiles. Confirmed factor-of-100 scaling and 16
complete-curve crosswalks unlock 96 observations as mass fractions. The original
2018 bibliographic entry remains unidentified; the later monograph supplies the
physical evidence, without relabelling the workbook's source year. Its local
SHA256 is `8e4b497d96df4e9f1bc74c778883918e09f3ec40173fdd34a318e795e8d9298d`.


[Gummatov's original author abstract (1992)](https://earthpapers.net/prostranstvenno-vremennaya-izmenchivost-gidrofizicheskih-harakteristik-seroy-lesnoy-pochvy)
was read as hosted OCR. Methods specify the capillary/hygroscopic potential
levels in MPa, and Figures 1 and 4 label water content g/g. Site, years,
treatments and horizons identify the workbook blocks. Confirmed full-curve
crosswalks preserve their identities. The rounded pF grid remains unchanged
for 1991 (190 observations); the 1992 block's exact MPa levels resolve its
mis-capitalized `mPa` label (10 observations). The reported negative potentials
are represented by the workbook's positive magnitudes.

[Panina's university-hosted thesis (2015)](https://soil.msu.ru/attachments/article/2063/Panina_Disser.pdf),
pp. 64-68 and Figures 9-10, confirms volumetric-percent retention plots. However,
its workbook's 132-point multiset has only 126 unique row matches and mixes
curves among 27 cached identity groups. The plotted saturation axis also does
not justify the proposed wide 0.001 to long -1 replacement. Units alone therefore
do not release these rows. Table 7 also appears to contain internally inconsistent
parameter headings; its stored fits remain separate from observations.

[Makarychev, Bitsoshvili and Lebedeva (2014)](https://www.asau.ru/vestnik/2014/6/061-066.pdf)
reports thermal properties at named hydrological constants, not a retention
pressure grid. This lead does not establish the physical pressure represented
by the workbook's PGK label, so the corresponding blocked rule remains inactive.
