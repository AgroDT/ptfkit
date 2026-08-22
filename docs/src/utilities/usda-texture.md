# USDA texture adapter

`ptfkit.usda_texture` converts one of the 12 basic USDA-NRCS fine-earth texture
classes into one deterministic, representative estimate of sand, silt, and clay
percentages. It is an input-data adapter, not a published pedotransfer function,
and its output is not a laboratory measurement.

The values come from the representative outputs in the USDA Natural Resources
Conservation Service [Soil Texture Calculator](https://www.nrcs.usda.gov/resources/education-and-teaching-materials/soil-texture-calculator),
artifact `USDA_Soil_Texture_Calculator.xlsm`. "Representative" means the single
composition selected by that workbook for a class. ptfkit does not calculate
independent range midpoints, normalize the result, or substitute a polygon
centroid.

## Supported classes

The exact canonical names are `sand`, `loamy sand`, `sandy loam`, `loam`,
`silt loam`, `silt`, `sandy clay loam`, `clay loam`, `silty clay loam`,
`sandy clay`, `silty clay`, and `clay`.

## Python usage

```python
from ptfkit.usda_texture import estimate_usda_texture_fractions

fractions = estimate_usda_texture_fractions('loam')
print(fractions.sand, fractions.silt, fractions.clay)
```

Strings are stripped, compared case-insensitively, and may use repeated
whitespace, hyphens, or underscores between words. For example,
`sandy_clay_loam`, `sandy-clay-loam`, and `Sandy Clay Loam` are equivalent.
The function does not use abbreviations or fuzzy matching. Subclasses and
fragment modifiers such as `fine sandy loam` and `gravelly loam` raise
`ValueError`; the error lists every accepted canonical class.

## Applicability and uncertainty

All uncertainty introduced by replacing an unknown measured composition with a
representative point propagates into any later calculation. A PTF may also use
particle-size boundaries, bases, or conventions incompatible with the USDA
fine-earth mass fractions. Never assume compatibility merely because a PTF has
arguments named `sand`, `silt`, or `clay`; verify its specification and source
evidence first.

No existing PTF is used in this example because this change does not add
compatibility claims to existing scientific specifications without explicit
source evidence.
