# Priority source reconstruction, 2026-10-25

No additional function/sample/target combination is authorized by this review.
Workbook transfer identities are established; experimental measurement contracts
remain incomplete. The workbook and detailed audit artifacts remain local.

| Source | Exact cross-sheet row IDs | Nonempty reported water vectors | Observation release |
| --- | ---: | ---: | ---: |
| Nikulina 2001 dissertation | 28 | 12 | 0 |
| Medko 2012 dissertation | 44 | 40 | 0 |
| Fomin 2023 | 6 | 5 | 0 |

All 78 IDs have identical ordered vectors after separating the explicitly
headed particle-size columns. These counts include coordinate and empty rows;
they are not independent sample/profile counts. Numerical matches cannot
substitute for IDs. The audit retains disagreements and ambiguous IDs rather
than choosing the closest curve.

## Nikulina

Directly reported workbook evidence: the dissertation sheet alternates vectors
labelled `m water h` and `Q`. The sheet header defines Q as volumetric water but
allows both percent and fraction representations. This does not determine the
literal source-specific scale. There are 14 head-labelled and 14 Q-labelled
rows, including two empty vectors of each type. Adjacency does not establish
which experimental head vector belongs to which water vector.

The water vectors occupy dissertation columns AJ:CQ and master columns X:CF.
The separately headed particle bins start at dissertation CR and master CG.
Reading the whole numeric row as retention data would include texture data.
Some master rows additionally repeat the final particle fraction in column CW.
These trailing cells are retained as separate predictors, never WRC points.

The particle-size headers report 1–0.25, 0.25–0.05, 0.05–0.01,
0.01–0.005, 0.005–0.001 and below 0.001 mm. These bins do not establish the
below-0.002-mm fraction required by a USDA clay contract. No redistribution
within a reported bin or conversion of a Russian texture class is authorized.
The density columns do not themselves supply units or measurement protocols.
Carbon and humus have separate percent-labelled columns; no conversion between
them is inferred. Horizon/depth and land-use labels are preserved with their
literal row IDs, without inferring independent profiles.

Exactly derived evidence: the 28 row IDs and ordered retention vectors agree
between the two workbook representations. Two water vectors have the same
value multiset in a different order. This flags possible reuse, but does not
prove that complete pressure/water curves or experimental samples coincide.

Unresolved: original curve identity, head/water binding, absolute water scale,
head sign, measurement method, repeated-coordinate interpretation, profile
identity and predictor protocols. Repeated coordinates are never averaged.

The [RSL access record](https://viewer.rsl.ru/api/v1/document/rsl01000338321/info)
reports 138 pages, `isAvailable: false` and `accessLevel: restricted`.
The locally retained response documents the access limitation; bibliographic
agreement does not resolve the missing experimental tables.

## Medko

Exactly derived workbook evidence: 44 row IDs and vectors agree between master
and dissertation views. Four explicitly reviewed coordinate rows delimit the
representation; 40 other rows carry water vectors, replicate labels, depths
and sample-preparation descriptions. The repeated coordinate vector is not a
duplicate soil curve. No repeated water-value multiset occurs among these 40
vectors. Different vectors do not prove experimental independence.

The available author-abstract transcription distinguishes repacked samples,
intact cores of several dimensions, laboratory tensiostats, saturated-salt
equilibration and field drying. It also describes Voronin reconstruction of
the middle curve. Fitted saturation parameters are reported volumetrically.
These descriptions are experiment-level evidence, not permission to treat
every workbook coordinate as a directly measured point. No point is released
using fitted parameters or a source-wide method assignment.

Unresolved: exact original curves and replicate crosswalk, coordinate-block
binding, water scale, pressure convention, measured versus reconstructed
points, profile independence and same-sample predictor protocols.

The [RSL access record](https://viewer.rsl.ru/api/v1/document/rsl01005423835/info)
reports 120 pages and restricted, unavailable full text. The abstract
transcription is retained locally as a lead; readable original figures and
methods remain necessary for point-level authorization.

## Fomin

Exactly derived workbook evidence: one coordinate row and five distinct water
vectors match between the master and soil-specific wide view by unique literal
IDs, with all 11 positions in the same order. No vector permutation or exact
duplicate is present between these views. The accompanying density cells stay
bound to those same IDs. This resolves the cross-sheet transfer check.

Unresolved: original experimental core identities, the workbook/paper depth
difference, branch and replicate, water denominator and scale, the first-axis
saturation marker, and matric versus total potential for vapor-equilibrated
points. The related paper's horizon means cannot be transplanted into cores.
The five workbook vectors are candidates, not five confirmed independent curves.

## Following source priority

The benchmark now ranks source-review ceilings after excluding combinations
requiring new public measurement contracts or adapters. The largest conditional
ceiling in the current roster is Shvarov 2008: 567 combinations across 21 master
rows and 27 functions. This is a ceiling conditional on all scientific gaps
being resolvable, not an expected gain or authorization for those functions.

Further review identified the
[primary publisher record](https://link.springer.com/article/10.1134/S1064229308100050)
for Shvarov and Koreneva (2008). It confirms the publication and subject but
exposes subscription preview content. It does not provide the exact table
crosswalk or absolute-water/pressure contracts. Earlier matched hysteresis
difference vectors remain unsuitable as absolute-water targets. This lead is
recorded in `source-followup.json`; no additional observations are released.

The remaining sources retain their source-specific evidence requirements in
`source-followup.json` and the existing mapping. A missing adapter, unresolved
manifest contract or absent canonical target is not evidence of permanent
scientific incompatibility. The full review remains incomplete; additional
primary experimental evidence is required before extending real-data scoring.
