# Evaluation source review

Reviewed online on 2026-10-23 and 2026-10-24. This record separates published evidence from
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


### Partial Panina normalization

The later row review releases 116 positive-pF observations whose pressure-water
pairs uniquely identify original master records after the confirmed percentage
scaling. Each association is rechecked during normalization. Four ambiguous pairs
and all 12 saturation-axis rows remain explicit exclusions. This supersedes the
previous whole-block exclusion without endorsing its proposed saturation-axis
replacement or corrupted fitted-parameter identities. The full primary thesis
SHA256 is `eac3553c2a904c8c1a75f67437bc01b1005b3ebed45ada29e189017e8baafaa8`.

### Badenko 2013: original experimental table

[Badenko, Terleev, Mirschel and Nikonova (2013), Agrophysica 1(9), pp. 13-22](https://www.agrophys.ru/Media/Default/Page/Magazine%20Agrophysics/Agrophysica1(9)/Badenko.pdf)
describes pressure-membrane measurements on pp. 16-17. The table on p. 17 labels
volumetric water content in cm3/cm3 and pressure in kPa. All 108 water values
match the original wide table after the printed columns are reordered to
0, 15, 33, 122, 415 and 1520 kPa magnitudes. The reported table is experimental;
its hydrological-constant labels do not make those measurements derived targets.

Exhaustive row review releases 106 uniquely matched original points across
18 horizons. Long rows 1000 and 1086 share an identical pressure-water pair
between two master horizons and remain excluded. Existing nonmonotonic values
are retained and diagnosed separately. The full-curve crosswalk stays blocked.
The reviewed PDF SHA256 is
`96da74ac7a27a0f58511912fd6b7fc82b93ae05351739c2b28294866cd6fa29e`.

### Umarova 2008: original figure and retained points

[The Russian State Library catalog record](https://search.rsl.ru/ru/record/01003446835)
provides a freely readable 52-page original author abstract. Figure 5 on printed
p. 19 ([viewer page 20](https://viewer.rsl.ru/rsl01003446835?page=20)) labels
pF and volumetric water content in percent. The original viewer text layer
confirms both axes and the ten plotted horizons; Table 2 independently matches
the workbook's physical metadata. The hosted OCR transcription was used as a
search aid, with the original figure supplying the unit evidence.

All 81 retained long-sheet observations uniquely match original master points
after percentage scaling, across ten sample identities. Matching includes all
wide positions when checking uniqueness. The 22 declared zero placeholders
and seven populated wide points absent from the long table are not released.
The complete-curve rule and proposed source alias remain blocked; row-specific
canonical identities do not promote either claim.

### Sadovnikova and Smagin 2011: original figure and experimental repeats

[The journal-hosted original paper, pp. 17-20, Figure 1](https://ecokavkaz.ru/media/docs/2011/2/2011-2-2.pdf)
identifies the Krasnodar chernozem A horizon at 20-30 cm and the Moscow-region
low-moor peat T horizon at 10-20 cm. The figure labels dry-mass W percent and
absolute pressure in kPa on a logarithmic axis. Methods distinguish filled and
open experimental symbols as repeats; solid curves are van Genuchten fits.
The workbook's four master records preserve two point series for each soil.
They must remain dependent within those soils/source for statistical assessment.

All 63 literal wide/long pairs match uniquely after percentage scaling.
Row review releases 61, including legitimate peat water/dry-soil ratios above
one. Long rows 778 and 793 use the wide chernozem axis placeholder 0.01;
the figure does not establish that pressure, so both remain excluded without
inventing replacements. The source's raw pF label is interpreted as log10(kPa)
only under this reviewed rule. Complete-curve cached identities remain blocked.
The reviewed PDF SHA256 is
`b42c91b817f4eadd6844ba33827bbeffde950a8789a075206bbff955d8b1befd`.

### Moiseev, Terleev and Kholokhorenko 2018: experimental table versus statistics

[The journal-hosted original, pp. 80-82, Table 2](https://tvan.niishk.site/data/documents/7_1.pdf)
reports pF and volumetric-percent experimental water contents separately from
PSF model calculations. Soil names, locations, horizons and depths match the
three retained workbook records. All 23 experimental pressure-water pairs
match Table 2 exactly after percentage scaling. The later 2021 paper provides
a bibliographic lead but does not independently identify these workbook rows.

Three U/U-critical Mann-Whitney statistic pairs were copied into the workbook
as pressure-water observations. Long rows 1797, 1807 and 1816 are explicitly
excluded as `non_observation_table_value`, preserving their original values and
lineage. Rows 1795, 1805 and 1814 remain excluded for unsupported saturation
pressure axes. The proposed -1 replacements remain inactive. The row policy
releases only the 23 original experimental pairs, with exact master identities
and evidence cells. It does not promote PSF calculations or U statistics to
independent observations. Complete-curve reconstruction remains blocked.

The reviewed PDF SHA256 is
`1c6e59cb6c9b2a916a35b77e26af2731c17e21f95669714862839c11c3d11213`.

### Vasyukov 2012: water basis resolved, pressure reference still missing

[The author's university-hosted original issue, pp. 67-70](https://shelly.kpfu.ru/e-ksu/docs/F584517239/2012_3.pdf)
identifies the buried and modern Tayaba horizons. The original figure on p. 70
labels volumetric water as fractions. This resolves the water quantity and
scale for 28 workbook rows. The ordinate, however, identifies only a decimal
logarithm of soil-water potential, with no pressure or water-head reference
unit. The workbook's pF label alone cannot establish log10(cm water head).
The mapping records known volumetric fractions but leaves pressure representation
and convention unset, retaining all 28 exclusions. No axis or water value is
replaced. The reviewed complete-issue PDF SHA256 is
`be459392868c030466791d9ffa38ba7746c85480609b9d1764214bea032c2d1a`.

### Shvarov: original-author evidence warns against absolute-water interpretation

[Shvarov's earlier author abstract, Table 2, hosted OCR](https://earthpapers.net/gisterezis-zavisimosti-kapillyarno-sorbtsionnogo-potentsiala-vody-ot-vlazhnosti-pochvy)
has a printed imprint of 1984, while the host index dates it 1983. It reports
differences between adsorption/desorption equilibrium moisture in
percent, indexed by relative vapor pressure. Two complete five-value vectors
and their soil/horizon/depth metadata match workbook master rows 88 and 108.
These are hysteresis differences, not absolute retention water contents. The
earlier text corroborates this subset without replacing the workbook's 2008
source attribution. Other rows show discrepancies and are not automatically
reinterpreted, reversed, repaired, or released.

[The original 2008 publication](https://link.springer.com/article/10.1134/S1064229308100050)
has only an accessible abstract at the publisher; its exact tables remain
unreviewed. The 119 source-labelled rows retain a dedicated observation-
provenance blocker in addition to physical-unit blockers. Confirming units alone
must not release copied hysteresis differences as absolute-water targets.

### Shein and Mady: the 2019 follow-up does not identify the 2018 curves

The [publisher-hosted 2019 follow-up](https://bgt.cherkasgu.press/journals_n/1564396584.pdf),
DOI 10.13187/bgt.2019.1.59, is available through the publisher URL registered
in Crossref, although the OAJI copy returns HTTP 410. It describes field
moisture dynamics and HYDRUS-1D validation, rather than reproducing the
original 2018 retention curves. Its laboratory layer intervals differ from
the four workbook intervals. Aggregate particle-size, density and organic-
matter statistics cannot establish predictor values for individual records.
The modeled HYDRUS results cannot substitute for experimental observations.
The 25 source-labelled workbook observations therefore remain blocked pending
the original curves, their water units, branch and exact horizon identities.
The reviewed follow-up PDF SHA256 is
`9681681b4d9d0256cf531ee58f9b205e5f2540f5cb92b39647d25298c47d74bd`.

### Smagin 2009: distinguish short and extended publications

The [open 2009 chernozem paper, pp. 5-16](https://ecokavkaz.ru/media/docs/2009/4/2009-4-1.pdf)
contains humus-dynamics models but does not reproduce the three retention
curves required to identify workbook master rows 110-112. The
[2011 follow-up](https://ecokavkaz.ru/media/docs/2011/4/2011-4-2.pdf)
discusses water-retention loss, but that discussion does not establish the
axes or values of these workbook curves. Neither paper justifies releasing
the 24 source-labelled observations.

A longer, differently titled 2009 contribution in *Doklady po ekologicheskomu
pochvovedeniyu*, issue 12, no. 2, pp. 63-93, remains a bibliographic lead.
Do not conflate it with the reviewed 12-page paper. The current journal
contents omit the relevant 2009 issue; its 2006 methods contents link to
archived pages rather than directly to PDFs. Exact figure review is still
required before assigning water or pressure units.
The reviewed 2009 and 2011 PDFs have SHA256 values
`3fb987e3190c54fd6787c22247a8baf2d593b8fc4214931d06f58fce65597e83`
and `dcca5ed1b099150743911255e701f51852ca1c3e310b0016ce610b0bde8597c6`,
respectively.

### Sapozhnikov 1988: author abstract corroborates the experiment, not the axes

[Sapozhnikov's 1994 author abstract, hosted OCR](https://earthpapers.net/fizicheskie-parametry-plodorodiya-pochv-pri-antropogennyh-vozdeystviyah)
discusses long-term manure, NPK and bare-fallow treatments of typical
chernozem and cites the 1988 coauthored paper. Its methods include vapor
equilibration, capillarimetry and Voronin's experimental-calculation method.
The treatment discussion corroborates a source-recovery lead for the 12
workbook records, but does not reproduce their complete retention table or
establish the water scale and exact pressure coordinates. General use of pF
elsewhere in the abstract does not confirm the workbook's saturation
placeholder. No physical rule or proposed pressure replacement is activated.

The original 1988 figures/tables must also distinguish directly measured
points from experimental-calculation segments before any points are used as
independent evaluation targets. The abstract alone cannot assign those
categories to particular workbook rows. All 108 observations remain blocked.
The reviewed HTML snapshot SHA256 is
`8ce14ada02ef0be0af8873c5a096ccd175745528326e61e4ec5819b122c7b6e0`.

For the Smagin methods lead, the journal-linked archived 2006 article page
was recovered, but its linked PDF returned HTTP 404. Public archive capture
queries returned no matching successful PDF captures for that exact path or
the journal's 2009 bibliography directory. This closes that particular
download route; it does not establish that no public copy exists elsewhere.

### Shein, Shcheglov and Moskvin 2012: reconstructed curves need provenance review

The [publisher abstract](https://link.springer.com/article/10.1134/S1064229312040102)
identifies the Kamennaya Steppe study and explicitly describes calculated
retention parameters, including the Voronin method followed by van Genuchten
approximation. [Moskvin's original 2013 author abstract, hosted OCR](https://earthpapers.net/eksperimentalnoe-obespechenie-modeli-vodnogo-rezhima-chernozemov-kamennoy-stepi)
matches the field between shelterbelts 138 and 156 and describes how measured
hydrological and mechanical constants supply inferred pressure-water anchors.
It distinguishes that reconstruction from direct measurement of pressure-water
pairs. This supports the workbook's method description but does not make its
30 stored curve points independent retention measurements.

The original 2012 figures/tables remain necessary to identify the particular
series, water units, pressure coordinates and any directly measured subset.
No source rule, fitted-parameter convention or observation row is released.
The secondary workbook sheet also labels these curves cm3/cm3; this is useful
internal corroboration, not a replacement for the source review.
The reviewed 2013 HTML snapshot SHA256 is
`0ea4e1783dd77251e39d741f0deffce82fb5f9b5dc0dfb047e921ad8d17b89f2`.

### Chudinova and Sidorova: identified publication leads remain unreviewed

[Chudinova's 2009 publisher abstract](https://link.springer.com/article/10.1134/S1064229309040073)
identifies the three relevant soil classes and Ap horizons. The historically
cited public Russian PDF at `cryosol.ru/_ld/0/3_Pochved4_09Chud.pdf` returned
HTTP 403; no matching public archive capture was found. The abstract does not
resolve the 65 workbook observations or their six disputed initial axes.

Sidorova and Borisova's 2016 article, DOI 10.3103/S0147687416020071,
*The flow of moisture in the model sod-podzolic soil under mulch fir litter*,
is a candidate for the 17 source-labelled observations. It must be checked
against both master horizons before being adopted as their source; the title
and year alone do not establish that match. No unit or horizon correction is
made from this bibliographic lead.

The Sidorova/Borisova publisher page was subsequently read directly. It
identifies the Russian original as *Vestnik Moskovskogo Universiteta.
Pochvovedenie*, 2016, no. 2, pp. 25-32. The page offers subscription access
and an abstract, not the original retention figures. Its HTML snapshot SHA256
is `836bec3c8ea09c878870508e42fa8bff8273239b8c9a21132442548f5fd18ebf`.

### Remaining source-review queue

The current manifest and reconstruction audit identify 692 rows under 15
blocked physical source rules. This includes 48 Khaydapova rows currently
reported under identity mismatch; those need both physical and identity
review. The other 27 exclusions belong to the reviewed sources' explicit
row decisions or invalid-value checks. Counts below are workbook-labelled
rows, not promises of independent usable observations.

| Reconstruction rule | Rows | Evidence still required |
| --- | ---: | --- |
| `shvarov_2008` | 119 | Original 2008 tables; absolute water versus hysteresis differences; units and long-only records |
| `sapozhnikov_1988` | 108 | Original retention figures/tables; units; measured versus calculated segments |
| `pestonova_2007` | 81 | Original Figure 7 pressure-axis labels and saturation convention; dry-mass percent water confirmed |
| `chudinova_2009` | 65 | Original figures; water basis and six initial axis positions |
| `khaydapova_2001` | 54 | Original figures; physical units and exact row identities |
| `makarychev_2014_2` | 35 | Hydrological-constant meaning; any independently established pressure-water pairs |
| `shein_2011` | 30 | Water basis; salt-equilibrium axis, temperature and applicable potential |
| `shein_2012` | 30 | Original figures/tables; independent observations versus reconstructed curves; identities |
| `vasyukov_2012` | 28 | Reference unit of the logarithmic pressure-potential axis |
| `manucharova_2012` | 27 | Original table/figure column order, soil identities, units and missing-value treatment |
| `makarychev_2014_1` | 25 | Hydrological-constant meaning; any independently established pressure-water pairs |
| `shein_2018` | 25 | Original curves; water units, drying/wetting branch and exact depths |
| `sapozhnikov_1987` | 24 | Original retention figures/tables; water scale and pressure convention |
| `smagin_2009` | 24 | Exact extended publication and three treatment curves with axes |
| `sidorova_2016` | 17 | Original 2016 no. 2, pp. 25-32; both horizons and physical axes |

The Shein 2012 source and reconstruction rules now retain a dedicated
observation-provenance blocker. Together with Shvarov, this protects 149
source-labelled rows from release based on physical units alone.

### Pestonova 2007: original author abstract resolves the water basis

[The complete original author abstract, hosted OCR](https://earthpapers.net/mehanicheskaya-prochnost-pochvennoy-struktury-vzaimosvyaz-s-fizicheskimi-svoystvami-i-osnovnoy-gidrofizicheskoy-harakteri)
and [the free library viewer, page 23](https://viewer.rsl.ru/rsl01003058664?page=23)
identify the six retained horizons in Figure 7 (printed p. 21). The shared
moisture axes use W percent; methods define dry-soil-mass moisture and describe
centrifugation/desorption. Water semantics are now dry-mass percent.
The reviewed text layers do not preserve the pressure-axis labels, and browser
viewing returned a gateway error followed by a blank page. No pressure meaning
or saturation replacement is inferred. All 81 rows remain blocked.

The HTML snapshot SHA256 is
`2ae4a5b0ca84fcab027844c67e07e06071e31ed9933b7c1d6a83890f575dcd4e`;
the library's public Figure 7 word-coordinate response SHA256 is
`90e59ea093021924618a0250649c65e4d8762a7e9c2d91c43b50f07acbd4a8da`.
The library metadata explicitly permits free viewing of all 29 pages without
authorization, while download is unavailable; no download restriction was
bypassed. The next concrete step is visual review of that freely viewable
figure when rendering is available.

Before the user redirected work to technical implementation, the standard
free-page viewing endpoint successfully returned Figure 7. Its visible axes
confirm pF and W percent. The viewed JPEG SHA256 is
`8c21815a76bfb49480fd1e1e712695d012172eb26df5cf6cb2354a3e62474de4`.
A draft row audit found 72 unique positive-pressure candidates, six unsupported
saturation placeholders, two ambiguous pairs and one questionable water value
at master cell AD60. No source rule or row policy was changed for these
candidates. Any future release must review that discrepancy and retain explicit
exclusions; the current artifacts still contain 1,036 normalized observations.
## Local fit interval support review

The official [SciPy curve-fit reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html)
states that its covariance interpretation relies on local linearization and
can be inaccurate when that approximation fails. This supports retaining the
existing conditional interpretation rather than treating optimizer convergence
as evidence of valid uncertainty. It does not supply soil-specific parameter
bounds or justify residual independence for the workbook.

The new `diagnose_fit_uncertainty_support` API reports interval containment
separately from fit acceptance. Under the unchanged initial fitting policy,
67 of 133 accepted real-data fits have at least one parameter interval outside
its declared box; 12 have a mean interval outside [0, 1], and 44 a conditional
prediction interval outside [0, 1]. Counts overlap. Intervals remain unchanged;
no clipping, expanded boxes, or coverage qualification is introduced.
## Bounded parameter profile implementation

The official [JMP profile-likelihood details](https://www.jmp.com/support/help/en/19.2/jmp/statistical-details-for-profile-likelihood-confidence-limits.shtml)
describe fixing a parameter, minimizing over nuisance parameters, and finding
objective thresholds for interval endpoints. The new
`profile_retention_parameter` implements only explicit-grid nuisance refits.
It intentionally supplies no threshold or inferred confidence endpoints:
finite-sample coverage, active constraints, local minima, and residual model
assumptions still require separate qualification.

The numerical solver uses bounded trust-region least squares, as documented
in the [SciPy optimization tutorial](https://github.com/scipy/scipy/blob/main/doc/source/tutorial/optimize.rst).
Each grid point uses the accepted estimate followed by seeded uniform nuisance
starts. This profile restart policy is explicit and differs from logarithmic
scale restarts in the original fitting policy. All outcomes remain recorded;
the smallest converged SSE is not certified as a global minimum.
## Single-parameter extra-SSE grid threshold

The [JMP profile-likelihood reference](https://www.jmp.com/support/help/en/19.2/jmp/statistical-details-for-profile-likelihood-confidence-limits.shtml)
uses F-based extra-SSE goals with nuisance refitting. The implemented
single-constraint rule is derived as
`(SSEprofile-SSEmin)/(SSEmin/(n-p)) <= F(1,n-p; confidence)`.
The denominator retains all originally fitted parameters, including the
profiled parameter; fixing it during a nuisance solve does not add a residual
degree of freedom to the reference fit. The resulting threshold is applied
only to explicit nodes, without root interpolation or global guarantees.

This remains approximate nonlinear inference under iid Gaussian homoscedastic
errors. The threshold is not a calibrated finite-sample constrained procedure;
parameter-box contact, nonlinear geometry, and workbook residual assumptions
remain qualification work. The independent test uses the reciprocal symmetry
of F(1,1), whose median is one, rather than reproducing the SciPy quantile call.
## Gaussian bounded-mean coverage control

The [NIST confidence limits for a mean](https://itl.nist.gov/div898/handbook/eda/section3/eda352.htm)
provide an independent unbounded one-sample t control with n-1 residual degrees
of freedom. For a Gaussian mean at a single lower boundary, sign symmetry and
the t acceptance event give (1 + nominal level)/2 unconditional coverage for
the unadjusted bounded extra-SSE rule: half the samples fit the true boundary
exactly, and the positive half contributes nominal coverage. This is a derived
half-line result, not an exact statement for arbitrary finite parameter boxes.

The new `evaluation/experiments/profile_coverage` experiment evaluates finite
[0, 1] mean constraints and retains both boundary-fit counts, the unbounded t
control, and conditional/unconditional coverage denominators. It does not
establish coverage for nonlinear retention families or justify Gaussian,
homoscedastic independent errors in the workbook. Near-boundary conditioning
is deliberately reported separately from all-generated-sample evidence.
## Nonlinear retention coverage pilot scope

The new `evaluation/experiments/retention_coverage` pilot extends the existing
reviewed extra-SSE grid rule to the four registered families, without changing
its threshold or relaxing the fitting policy. Known synthetic saturation truth
is included in the inference grid, never in initial fit starts. Generative
curves use explicit van Genuchten, Brooks--Corey, and Clapp dry-branch equations;
Clapp's gradual wet branch is outside this particular generating grid.

At 50 repetitions per scenario, the experiment is a failure-accounting pilot,
not sufficient coverage evidence. Its 102 boundary fit rejections and ten
Brooks--Corey lower-objective profile counterexamples remain visible in the
denominators and raw records. Gaussian residuals, finite-box effects, sparse
pressure design, fit selection, and the distinction between conditional and
all-generated coverage remain essential limitations. No new source-derived
parameter ranges or confidence correction were inferred from these outcomes.
## Pressure-partition restart policy

`brooks_corey_pressure_partitions_v1` is an explicit engineering policy derived
from the registered piecewise Brooks--Corey equation, not a new source-derived
parameter range or a claimed global optimization method. It supplements the
original seeded starts with interior observed pressure knots and geometric
partition midpoints for air entry. Restart locations do not depend on observed
water content, fitting residuals, or synthetic truth. The original starts,
parameter bounds, optimizer limits per attempt, and acceptance gates remain.
Profile nuisance refits use the same added air-entry locations when applicable.

The nonlinear pilot can compare this policy with the original on identical
generated observations and seeds. A smaller objective or fewer profile
counterexamples is numerical evidence only; it does not validate finite-sample
coverage, justify bound widening, or authorize selecting a policy to maximize
observed coverage.
## Piecewise air-entry solver policy

The optional `brooks_corey_interval_solves_v1` policy partitions the original
air-entry box at observed pressure knots, following the branch structure of
the registered Brooks--Corey equation. It is an engineering optimizer policy,
not a source-derived equation or a statistical coverage correction. Closed
local intervals include every original air-entry value; every seeded nuisance
start is tried in each interval, in addition to original full-box solves.

Local interval limits are recorded separately from scientific parameter bounds.
Knot contact alone is not physical boundary failure, but local Jacobians at
knots do not establish the smoothness assumptions required by approximate fit
uncertainty. All acceptance and inference qualification limitations remain.
The paired synthetic pilot tests numerical stability under a fixed known
generator, not real-soil residual assumptions or national representativeness.
## Expanded simulation protocol and real-cohort readiness

[Morris, White and Crowther (2019)](https://doi.org/10.1002/sim.8086) motivates
the expanded study's explicit design, estimands, performance measures, and
Monte Carlo uncertainty reporting. Before execution, `expanded-plan.json`
fixed 34 cells and 6800 realizations spanning noise, grid density, saturation
boundary proximity, and Brooks--Corey air entry between pressure knots. The
one-sided exact binomial undercoverage test with Bonferroni 0.05/34 is this
project's declared decision rule, not a threshold prescribed by that paper.
Unflagged cells do not establish adequacy or real-soil coverage.

The count-only canonical/predictor join now shows that the 59 exported curve
identities have no sand input for any Gunarathna contract and no complete
Vereecken input set. Only Clapp has complete raw inputs on this cohort (24
texture values), all blocked by classification compatibility. Predictor
metadata review for other workbook rows alone cannot repair this cohort's
missing values. Canonical target material remains `unspecified`, so even a
future predictor-compatible subset still requires a reviewed target contract
before scoring. No source-derived properties or classification crosswalks were
inferred from successful curve fitting.
## Independent investigation of the coverage flag

The [NIST fitting reference](https://www.itl.nist.gov/div898/software/dataplot/refman1/ch3/fit.pdf)
supports the linear least-squares residual n-p and coefficient-inference
control used in the boundary follow-up. The analytic Jacobian and positive-sign
selection argument are explicit project derivations, not a new published
retention uncertainty procedure. Truth-initialized diagnostic solves never
replace public fits or enter the independent primary simulation policy.

The fixed 2000-realization follow-up did not reproduce the original strong
shortfall. The original joint-selected linear control shared all 85/99
coverage classifications with the nonlinear method, and a 100000-draw exact
linear control was consistent with nominal coverage. These findings support
sampling fluctuation as a possible explanation; they do not erase the original
adjusted flag or establish small-bias absence, global adequacy, or workbook
residual assumptions. Confidence thresholds and scientific bounds remain fixed.
## Clapp source audit: first eligible real subset

The 24 populated texture candidates span Badenko 2013 (six), Bolotov 2014
(three), Panina 2015 (twelve), and Moiseev 2018 (three). Russian abbreviations
were not translated into USDA classes. The first, second and fourth sources
remain unresolved for this contract (twelve candidates in total).

[Panina, printed p. 88, Table 17](https://soil.msu.ru/attachments/article/2063/Panina_Disser.pdf)
directly reports the supported class for the six gray forest horizons; Table 18
reports an unsupported class for the six sod-podzolic horizons. The
[USDA-hosted HYDRUS manual, section 3.8](https://www.ars.usda.gov/arsuserfiles/20361500/pdf_pubs/P2164.pdf)
establishes the USDA classification used by ROSETTA. The mineral-material
review and exact depth lineage are recorded in the source-review artifact.
The 0--10 cm workbook horizon is covered by two source subintervals with the
same class; no numeric predictor averaging is performed.

An external source-backed overlay now selects six horizons and 56 unchanged
measured targets. It leaves global workbook bindings blocked and retains one
profile group. Native fixed Clapp predictions give sample-equal MAE 0.0305542
and RMSE 0.0350361 volume fraction; cluster intervals are withheld for one
independent profile. This is a descriptive external check, not population or
pressure-domain validation. No PTF coefficient or unsupported class was added.

During publication, a Windows/Python 3.13 access-control defect was reproduced:
the final directory inherited the temporary directory's restricted ACL. The
[Python documentation](https://docs.python.org/3.13/library/os.html#os.mkdir)
documents special handling of mode 0o700 on Windows. Publication now stages
under the intended destination parent on Windows, preserving inherited access
controls, exclusive creation, atomic rename, and failure cleanup. Independent
process reads and installed-wheel replay verified the fix.
# Wosten class-parameter contract migration

The original [Alterra report 153](https://edepot.wur.nl/43272) was retrieved
and checksum-bound in `evaluation/datasets/wosten2001.measurement-review.json`.
Tables 3 and 4 were checked visually. The six class outputs now have explicit
measurement contracts. The target material `soil` covers the original mineral
and organic classes and remains distinct from other material identifiers.

The new retention adapter uses `m = 1 - 1/n`, is restricted to the reviewed
class-parameter function, and retains centimeter pressure-head units. Native
class-to-curve tests use published rounded values; an independent analytic
oracle distinguishes this variant from the reduced Vereecken model. Source
Table 4 values are model-computed references, not independent validation data.
No Dutch/USDA/Russian class crosswalk or uncertainty claim was introduced.
# Dharumarajan retention denominator review

The original [Current Science paper](https://www.currentscience.ac.in/Volumes/116/07/1237.pdf)
was retrieved and checksum-bound. Printed page 1239 and Tables 3-4 on printed
page 1242 were checked visually. The reported target pressures are explicit,
but percentage notation and the generic laboratory-protocol statement do not
establish a mass or volume denominator. Existing specification warnings
already record this ambiguity. Predictor preparation and particle-size
definitions also require a source-linked analytical protocol.

`evaluation/datasets/dharumarajan2019.measurement-review.json` records the four
affected retention functions and missing evidence. Their legacy gravimetric
quantity identifier is not a completed scientific contract. They remain
excluded from manifest-driven evaluation; the newly available gravimetric
benchmark does not justify inferring a denominator for them.
# Beniaich linear-regression measurement review

The [original article](https://www.frontiersin.org/journals/environmental-science/articles/10.3389/fenvs.2023.1090688/full)
and its PDF were reviewed. Sections 2.2-2.4 and Tables 5-6 establish the
gravimetric denominator, prepared fine-earth material, hydrometer protocol
and organic-matter processing. Review decisions and the PDF checksum are in
`evaluation/datasets/beniaich2023.measurement-review.json`. Eleven existing
linear regressions now have complete descriptors, with analytical methods
retained and no coefficient or status changes.

Only FC and PWP have explicit fixed-pressure support. Source capillary
saturation is not assigned a controlled zero-kPa condition. The real mass
cohort has no exact 33/1500-kPa observations, so the new contracts do not
create an external scoring cohort by themselves. A separate exact-pressure
audit records this limitation; nearby observations are not substituted.


## Saxton2006 and Cosby1984 follow-up

[Saxton and Rawls (2006)](https://www.ars.usda.gov/research/publications/publication/?seqNo115=178719)
was reviewed using parsed original article text and the existing prepared
specification. The corrected DOI is `10.2136/sssaj2005.0117`. No local PDF hash
or visual table inspection is claimed. Existing regression coefficients and
prepared corrections remain unchanged. Explicit fine-earth measurements,
pressure anchors, normal reference density and three source curve branches
are recorded in `evaluation/datasets/saxton2006.measurement-review.json`.

For [Cosby et al. (1984)](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/WR020i006p00682),
article transcription confirms that predictor compositions are texture-class
midpoints and reported dispersions are within-class standard deviations.
Logarithmic units/base and application equivalence remain unresolved; no Cosby
contract or native data binding was changed. The machine-readable review
preserves these limits rather than treating transcription as visual PDF review.


## HYBRAS class and mineral-horizon overlay

The local HYBRAS manual (SHA256
`0d1ae08d0962fa1157b8b1f3af71e539220fa99f77675984fd81096ecfcc81e0`)
was visually reviewed at PDF page 16, printed page 10. Figure 3 explicitly pairs
Portuguese texture labels and C/SC/CL/SCL/SL/LS/S/L/SiC/SiCL/SiL abbreviations
on the USDA triangle. The workbook's reported categories are translated by
this figure; no numeric texture-based reclassification is performed.
[NRCS Chapter 3](https://www.nrcs.usda.gov/sites/default/files/2022-09/SSM-ch3.pdf)
provides the mineral status of A/E/B master horizons. A strict single-master
subset is used; other labels require separate review. Mineral classification
is not proof of fine-earth preparation or absent gravel.

The [original Clapp article](https://scispace.com/pdf/empirical-equations-for-some-soil-hydraulic-properties-4hsglsjqwf.pdf)
was revisited for equations 1/3 and US calibration provenance. The verifier
inverts the wet parabola by bisection independently of the runtime's analytic
root. Original calibration excludes rocky soils; unknown HYBRAS gravel status
remains an applicability limitation of this external transfer experiment.


## Gunarathna specimen correction and Nebel sampling dependence

The author's dissertation in the
[Kagoshima repository](https://ir.kagoshima-u.ac.jp/records/14922), Chapter 6,
Section 6.2, printed page 96, reports distinct undisturbed retention and density
core geometries. Indexed primary text supports correcting the retention target
to bulk soil while retaining the analytical fine-earth texture denominator.
Direct PDF retrieval failed; no visual-table inspection or local PDF hash is
claimed. Regression coefficients remain unchanged.

The original
[Nebel2010 publisher PDF](https://www.rbcsjournal.org/wp-content/uploads/articles_xml/0100-0683-rbcs-S0100-06832010000300008/0100-0683-rbcs-S0100-06832010000300008.x29164.pdf)
was retrieved and reviewed at printed page 671. It describes 100 sampling points
on a 10-m grid in one hectare and discusses spatial dependence. Two HYBRAS
reference-pair groups share the exact same Parfitt citation, so their different
hashes do not establish study independence. Native input preparation and
original gravimetric-to-volumetric lineage remain separate review questions.
See the two machine-readable measurement reviews for hashes and limitations.
