# Estimating soil hydraulic properties of Fengqiu County soils in the North China Plain using pedo-transfer functions

Y. Li a,*, D. Chen a, R.E. White a, A. Zhu b,c, J. Zhang b,c

a School of Resource Management, Faculty of Land and Food Resources, The University of Melbourne, Parkville 3010, Victoria, Australia

b State Experimental Station of Agro-Ecosystem in Fengqiu, Institute of Soil Science, The Chinese Academy of Sciences, Nanjing 210008, PR China

c State Key Laboratory of Soil and Sustainable Agriculture, Institute of Soil Science, The Chinese Academy of Sciences, Nanjing 210008, PR China

Received 1 December 2005; received in revised form 24 November 2006; accepted 27 November 2006

Available online 11 January 2007

## Abstract

The unsaturated soil hydraulic characteristics, including soil water retention curve and hydraulic conductivity, are the crucial input data for simulating soil water and solute transport through the unsaturated zone at regional scales using GIS, and are expensive to measure. These properties are frequently predicted with pedo-transfer functions (PTFs) using the routinely measured soil properties (e.g. soil texture, soil bulk density, and soil organic matter content).

In this study, 63 soil water retention curves and 36 saturated soil hydraulic conductivities of seven soil profiles collected in Fengqiu County in the North China Plain were measured. Soil texture, bulk density and soil organic matter of these soil samples were also measured. The van Genuchten model describing soil water retention was used to fit the measured data for quantifying the soil hydraulic parameters. The PTFs were developed by multiple regression between soil hydraulic parameter data and basic soil properties. The double cross-validation of these PTFs is also discussed in this paper. The locally-developed PTFs from this study were compared with several existing PTFs in predicting the soil hydraulic parameters.

The developed PTFs were used in the regional simulation of a wheat and maize cropping agroecosystem in Fengqiu County for the 1998–1999 rotation year, and can explain 33% of spatial variation of the observed crop yields in 409 villages.

© 2006 Elsevier B.V. All rights reserved.

Keywords: Soil water retention curve; Saturated soil hydraulic conductivity; Basic soil properties; Pedo-transfer functions; Multiple regression; Application

## 1. Introduction

A spatially distributed model of water and nutrient management (WNMM) has been developed to study the impact of intensive cropping systems on water resource quality in the North China Plain (Li, 2002). Because dynamic water flow and nitrate transport through the soil vadose zone are modelled in WNMM, it requires that the soil hydraulic properties be known at regional scales. The hydraulic properties include the soil water retention curve (SWRC), which presents the relationship between the volumetric water content (θ) and the soil water pressure head (h), and the hydraulic conductivity curve, which

relates the conductivity (K) to the soil water pressure head (h) or the water content.

When the temporal and spatial variability of the region is considered, the required measurements of unsaturated soil hydraulic properties are tremendous, time-consuming, and very expensive. Therefore, it is necessary to develop a set of so-called pedo-transfer functions (PTFs) to estimate the unsaturated soil hydraulic properties from more easily measured or basic soil properties in the attribute database of a digital soil survey map, in which soil hydraulic properties are not always available. Bouma and van Lanen (1987) first described the equations for relating different land characteristics and soil properties as the term PTFs even though there were many attempts in this field before. For the recent development of PTFs and their application, we refer to reviews by Rawls et al. (1991), van Genuchten and Leij (1992), Pachepsky et al. (1999) and Wösten et al. (2001).

* Corresponding author. Tel.: +61 3 83447583; fax: +61 3 83444665.

E-mail addresses: yong.li@unimelb.edu.au (Y. Li), delichen@unimelb.edu.au (D. Chen), robertw@unimelb.edu.au (R.E. White), anzhu@mail.issas.ac.cn (A. Zhu), jbhang@mail.issas.ac.cn (J. Zhang).

In developing PTFs, soil texture (including sand, silt and clay contents), bulk density and organic matter content are the most used predictors in the literatures, and additional factors (soil particle size and distribution indices) are rarely applied because of lack of availability in the soil databases (Wösten et al., 2001). Furthermore, as summarized by Nemes et al. (2003), most of PTFs are developed to estimate the soil water retention (points at a series of matric potentials or parameters of analytical water retention equations) and saturated hydraulic conductivity. A small number of PTFs were proposed for the estimation of unsaturated hydraulic conductivity, e.g. Wagner et al. (2001). Methods for predicting soil hydraulic characteristic using PTFs are grouped by Tietje and Tapkenhinrichs (1993) into three types: (i) estimation of the water contents at certain matric potentials (Husz, 1967; Renger, 1971; Gupta and Larson, 1979; Rawls et al., 1982; Puckett et al., 1985; Imam et al., 1999; Kar et al., 2004), (ii) estimation of soil water retention relation with a physical–conceptual model approach (Arya and Paris, 1981; Haverkamp and Parlange, 1986; Tyler and Wheatcraft, 1989; Baumer, 1992; van den Berg et al., 1997; Tomasella and Hodnett, 1998; Tomasella et al., 2003), and (iii) estimation of parameters of algebraic retention functions for describing $\theta(h)$ and $K(\theta)$ or $K(h)$ (Pachepsky et al., 1982; Cosby et al., 1984; Rawls and Brakensiek, 1985; Nicolaeva et al., 1986; Wösten and van Genuchten, 1988; Rawls and Brakensiek, 1989; Vereecken et al., 1989, 1990; Schaap et al., 1998; Minasny et al., 1999; Wösten et al., 1999; Tomasella et al., 2003). The third method is widely used to directly predict hydraulic model parameters for describing soil water retention and hydraulic conductivity properties. PTFs are usually

expressed as linear or nonlinear regression equations or, more recently, distributed as computer codes resulting from artificial neutron network analysis (Pachepsky et al., 1996; Tamari et al., 1996; Schaap and Leij, 1998; Minasny et al., 1999; Schaap et al., 2001; Nemes et al., 2003).

If van Genuchten models (van Genuchten, 1980) for soil water retention and soil hydraulic conductivity, based on the statistical pore-size distribution model of Mualem (1976), are applied in modelling, the parameters representing the soil hydraulic conductivity curve can be the same or directly derived from the soil water retention parameters, except for the saturated soil hydraulic conductivity ($K_s$). This eliminates the need for the direct measurement or indirect estimation of the hydraulic conductivity curve if $K_s$ is known. Hence, the van Genuchten models of soil water retention and unsaturated soil hydraulic conductivity are considered in this study.

Because existing PTFs for estimating soil water retention curve and soil hydraulic conductivity in the literature are not always applicable in other regions with acceptable accuracy (Tietje and Tapkenhinrichs, 1993; Kern, 1995; Tietje and Hennings, 1996; Cornelis et al., 2001; Wagner et al., 2001; Nemes et al., 2003), we based this study on a data set covering measured basic soil properties, soil water retention curves and the saturated hydraulic conductivity of representative Fengqiu County soils in the North China Plain. The objective was to derive our own PTFs for estimating the soil water retention parameters and saturated hydraulic conductivity. The adjusted coefficients of determination and double cross-validation were used to evaluate the predictive capabilities of the derived PTFs, which will be deployed to the digital soil map of Fengqiu

![img-0.jpeg](None)

**{"image_type": "map", "description": "The image is a geographical map of Fengqiu County, showing its administrative divisions and key locations. The map includes the following labeled points: Huangde, Zhanggang, Wangcun, Hegang, Pandian, Jinglinggong, and Sunzhuang. The map also features a scale bar indicating distances of 0 to 5 kilometers, and a compass rose showing the cardinal directions (North, East, South, West). The map outlines the county's boundary and highlights the relative positions of the labeled locations within the county."}**

Fig. 1. The sampling sites of seven soil profiles in Fengqiu County.

County to build the spatial distribution of the soil water retention curve and saturated hydraulic conductivity. The performance of the derived PTFs was also compared with that of several existing PTFs.

## 2. Materials and methods

Fengqiu County soils are mainly classified as two types: Ochric Aquic Cambisol and Ustic Sandic Entisol according to the Chinese Soil Taxonomy System (Research group of Chinese Soil Taxonomy System, 1995). Ochric Aquic Cambisols dominate the soil distribution in whole Fengqiu County, covering 98% more of the total soil area, and Ustic Sandic Entisol accounts for about 2%.

Sixty three undisturbed 100-cm³ soil cores were collected from 7 representative soil subtype profiles in Fengqiu County (9 cores in each profile from soil surface to 2 m deep) (Fig. 1). The soil water retention data were measured on 100-cm³ soil samples using a pressure membrane apparatus at the suctions of 0, 10, 30, 50, 100, 300, 500, and 1500 kPa (Klute, 1986). Eight-point retention data were fitted to the equation of van Genuchten (1980):

$$\theta = \theta_r + \frac{\theta_s - \theta_r}{(1 + |\alpha h|^n)^m} \tag{1}$$

where $\theta$ denotes the soil volumetric water content (cm³ cm⁻³), $\theta_r$ and $\theta_s$ are the soil residual and saturated volumetric water contents (cm³ cm⁻³), respectively, $h$ is the soil water pressure head (cm), and $\alpha$ is in cm⁻¹, $n$ and $m$ are parameters defining the SWRC's shape. The unknown parameters ($\theta_r$, $\theta_s$, $\alpha$, $n$ and $m$) were obtained using the nonlinear least-squares optimisation program RETC (van Genuchten et al., 1991) from measured soil water retention data. The dry bulk density was measured by oven-drying soil samples at 105 °C for 24 h. The organic matter content was estimated from the organic carbon content determined by the Walkey–Black method, using a constant 1.724 for transformation. The particle-size distribution was obtained by the pipette method for particles with a diameter less than 0.002 mm (clay fraction), 0.02–0.002 mm (silt fraction), and 0.02–2 mm (sand fraction). The soil texture was determined by the international soil texture classification. Because of limited budget for this

Table 1
Value range and sample distribution of basic soil properties

|  Variables | Minimum | Maximum | Mean | Std. Error  |
| --- | --- | --- | --- | --- |
|  63 samples for SWRC  |   |   |   |   |
|  Soil organic matter (SOM, %) | 0.12 | 1.54 | 0.65 | 0.05  |
|  Sand fraction (SAND, %) | 6.26 | 93.03 | 50.23 | 3.53  |
|  Silt fraction (SILT, %) | 1.74 | 82.20 | 38.72 | 3.05  |
|  Clay fraction (CLAY, %) | 0.54 | 31.75 | 9.06 | 0.82  |
|  Bulk density (BD, g cm⁻³) | 1.20 | 1.61 | 1.42 | 0.01  |
|  36 samples for Ks  |   |   |   |   |
|  Soil organic matter (SOM, %) | 0.12 | 1.54 | 0.65 | 0.07  |
|  Sand fraction (SAND, %) | 8.98 | 93.03 | 53.28 | 4.46  |
|  Silt fraction (SILT, %) | 1.74 | 79.50 | 35.86 | 3.83  |
|  Clay fraction (CLAY, %) | 0.54 | 27.12 | 8.86 | 1.01  |
|  Bulk density (BD, g cm⁻³) | 1.20 | 1.59 | 1.42 | 0.01  |

Table 2
Texture-grouped soil properties of 63 samples for SWRC

|  Texture group | Number | SOM (%) | BD (g cm⁻³) | POᵃ (cm³ cm⁻³) | Measured θᵣᵇ (cm³ cm⁻³)  |
| --- | --- | --- | --- | --- | --- |
|  Sand | 9 | 0.20±0.01 | 1.47±0.02 | 0.466±0.008 | 0.460±0.011  |
|  Loamy sand | 3 | 0.13±0.01 | 1.41±0.03 | 0.487±0.009 | 0.477±0.003  |
|  Sand loam | 18 | 0.67±0.08 | 1.45±0.02 | 0.474±0.007 | 0.483±0.008  |
|  Silty loam | 24 | 0.78±0.08 | 1.38±0.02 | 0.498±0.006 | 0.519±0.005  |
|  Silty clay loam | 7 | 0.96±0.09 | 1.42±0.03 | 0.483±0.010 | 0.480±0.019  |
|  Silty clay | 2 | 0.67±0.05 | 1.43±0.04 | 0.481±0.013 | 0.479±0.061  |

experiment, only two replicates for each sampling point were taken. Therefore, the measures for each sampling point were expressed in average, without additional standard deviation or error information. Considering its high spatial variability in the field, the Kₛ was measured on selected 36 soil layers or sampling points from the same seven soil profiles using the method of Cook and Broeren (1995) with 6 replicates. Table 1 summarises the soil basic properties in this study.

Once the parameters for Eq. (1) were developed the correlation and multiple regression analyses from the SPSS package (Norusis, 1994) were carried out to formulate the PTFs of these parameters as well as Kₛ, based on the basic soil properties. The predictive capabilities of the PTFs were assessed using the adjusted R² value:

$$R_{\text{adj}}^2 = 1 - (1 - R^2) \left[ \frac{N-1}{N-M-1} \right] \tag{2}$$

where N is the number of observations, M is the number of independent variables in the PTF, and R² is the coefficient of determinations, given by

$$R^2 = 1 - \frac{\text{SSE}}{\text{SSQ}} = \frac{\text{SSR}}{\text{SSQ}} = 1 - \frac{\sum_{i=1}^{N} (y_i - \hat{y}_i)^2}{\sum_{i=1}^{N} (y_i - \bar{y}_i)^2} = \frac{\sum_{i=1}^{N} (\hat{y}_i - \bar{y}_i)^2}{\sum_{i=1}^{N} (y_i - \bar{y}_i)^2} \tag{3}$$

with

$$\bar{y} = \frac{1}{N} \sum_{i=1}^{N} y_i \tag{4}$$

yᵢ and ŷᵢ are the 'measured' and predicted hydraulic model parameters under investigation, SSQ is the total sum of squares,

Table 3
Texture-grouped soil properties of 36 samples for Kₛ

|  Texture group | Number | SOM (%) | BD (g cm⁻³) | Kₛ  |
| --- | --- | --- | --- | --- |
|  Sand | 4 | 0.21±0.02 | 1.45±0.01 | 45.21±8.04  |
|  Loamy sand | 3 | 0.13±0.01 | 1.41±0.02 | 21.50±0.68  |
|  Sand loam | 12 | 0.67±0.10 | 1.45±0.02 | 9.85±3.24  |
|  Silty loam | 13 | 0.81±0.12 | 1.37±0.02 | 19.96±4.35  |
|  Silty clay loam | 3 | 1.02±0.14 | 1.43±0.05 | 20.89±6.10  |
|  Silty clay | 1 | 0.62 | 1.39 | 7.85  |

The mean and standard error of the fitted retention parameters

|  Texture groups | Number | θ_{s} | α | n | R^{2}  |
| --- | --- | --- | --- | --- | --- |
|  Sand | 9 | 0.458±0.011 | 0.1403±0.0269 | 1.322±0.023 | 0.986±0.007  |
|  Loamy sand | 3 | 0.468±0.001 | 0.0047±0.0006 | 1.358±0.010 | 0.987±0.001  |
|  Sandy loam | 18 | 0.484±0.008 | 0.0320±0.0065 | 1.349±0.046 | 0.976±0.005  |
|  Silty loam | 24 | 0.478±0.008 | 0.0120±0.0020 | 1.305±0.026 | 0.954±0.006  |
|  Silty clay loam | 7 | 0.430±0.019 | 0.0054±0.0034 | 1.290±0.037 | 0.915±0.007  |
|  Silty clay | 2 | 0.430±0.056 | 0.0025±0.0007 | 1.228±0.028 | 0.900±0.020  |
|  All | 63 | 0.477±0.006 | 0.0346±0.0070 | 1.318±0.017 | 0.960±0.004  |

SSR is the regression sum of squares (explained by the PTFs), and SSE is the residual sum of squares of error. Adjusted $R^2$ measures the proportion of the variation that can be accounted for by the regression models.

In order to validate the developed PTFs, we applied the double cross-validation method (Green and Carroll, 1978) to evaluate predictions and stability of the PTFs. To use this method, the complete set of observations was randomly split in two equal subsets. Regression analysis was carried out on each of these subsets using the independent variables retained from the entire data. Subsequently, the regression equation derived from one set was applied to another, and *vice versa*, while the coefficient of determination of two regression analyses as well as the coefficients of Pearson correlation between predicted and observed hydraulic parameters for the two subsets were calculated.

### 3. Results and discussion

#### 3.1. Variations of the soil properties

The 63 soil samples for SWRC are grouped into six textural classes according to the international soil texture classification, in which the loam classes account for 78% of total samples (Table 2). There are twelve samples in sand classes, but only two in the clay class. Therefore, soil samples are mainly coarse-textured. As seen in Table 2, as soil texture increases, soil organic matter (SOM) increases except the silty clay class, but there is no obvious trend for bulk density (BD) and soil total porosity (PO). For the measured $\theta_s$, it increases as soil texture reaches silty loam class, then it starts to decrease with soil texture increasing. Basically, PO is slightly greater than measured $\theta_s$, except for the silty loam class. If a soil particle density greater than the average value of 2.65 is used, which may be true for these low SOM and river sedimentary soils in the North China Plain, PO will be apparently greater than measured $\theta_s$.

Because 36 soil samples for $K_s$ were taken within the sites of 63 soil samples for SWRC, it is not surprising that the texture

distribution pattern of 36 soil samples is similar to the 63 soil samples, even the relationships of SOM and BD vs. soil texture (Table 3). Within the six texture classes, the sand class has the highest $K_s$ of 45 cm d$^{-1}$; loamy sand, silty loam and silty clay loam classes have the similar $K_s$ of around 20 cm d$^{-1}$, in the middle range; sand loam and silty clay classes have the lowest $K_s$ of 8–10 cm d$^{-1}$.

![img-1.jpeg](None)

**{"image_type": "plot", "description": "The image is a plot showing the relationship between soil water content (cm³/cm³) and h (cm) for sand soil. The X-axis (h) is logarithmic, ranging from 1 to 100,000 cm. The Y-axis represents soil water content, ranging from 0.0 to 0.5 cm³/cm³. The plot shows a decreasing trend in soil water content as h increases, with a high coefficient of determination (R² = 0.99), indicating a strong fit to the data. Key data points approximate as follows:\n- At h ≈ 1 cm, soil water content ≈ 0.45 cm³/cm³\n- At h ≈ 10 cm, soil water content ≈ 0.30 cm³/cm³\n- At h ≈ 100 cm, soil water content ≈ 0.15 cm³/cm³\n- At h ≈ 1,000 cm, soil water content ≈ 0.05 cm³/cm³\n- At h ≈ 10,000 cm, soil water content ≈ 0.02 cm³/cm³"}**

![img-2.jpeg](None)

**{"image_type": "plot", "description": "The image is a plot showing the relationship between soil water content (in cm³/cm³) and suction head (h, in cm) for a sandy loam soil. The x-axis (suction head, h) is logarithmic, ranging from 10 to 100,000 cm. The y-axis (soil water content) ranges from 0.0 to 0.5 cm³/cm³. The plot depicts a decreasing trend in soil water content as the suction head increases, following a curve that fits a model with R² = 0.99. Key data points approximate as follows:\n- At h ≈ 10 cm, soil water content ≈ 0.48 cm³/cm³\n- At h ≈ 100 cm, soil water content ≈ 0.40 cm³/cm³\n- At h ≈ 1,000 cm, soil water content ≈ 0.25 cm³/cm³\n- At h ≈ 10,000 cm, soil water content ≈ 0.10 cm³/cm³\n- At h ≈ 100,000 cm, soil water content ≈ 0.02 cm³/cm³"}**

![img-3.jpeg](None)

**{"image_type": "plot", "description": "The image is a scatter plot with a fitted curve showing the relationship between soil water content (y-axis, in cm³/cm³) and depth (h, in cm, x-axis, logarithmic scale) for a silty clay loam soil. The plot title indicates an R² value of 0.94, suggesting a strong fit of the model to the data. The x-axis ranges from 1 to 100,000 cm, and the y-axis ranges from 0.0 to 0.6 cm³/cm³. The data points (blue circles) show a decreasing trend in soil water content with increasing depth. Key approximate data points extracted from the plot:\n- At h ≈ 1 cm, soil water content ≈ 0.50 cm³/cm³\n- At h ≈ 10 cm, soil water content ≈ 0.45 cm³/cm³\n- At h ≈ 100 cm, soil water content ≈ 0.35 cm³/cm³\n- At h ≈ 1,000 cm, soil water content ≈ 0.25 cm³/cm³\n- At h ≈ 10,000 cm, soil water content ≈ 0.15 cm³/cm³\n- At h ≈ 100,000 cm, soil water content ≈ 0.05 cm³/cm³\n\nThe trend indicates that soil water content decreases exponentially with depth."}**

Fig. 2. The soil water retention curves described by Eq. (5): (A) sand with SAND=91.21%, SILT=2.35%, CLAY=4.44%, SOM=0.24%, and BD=1.45 g cm$^{-3}$; (B) sandy loam with SAND=76.61%, SILT=20.19%, CLAY=1.20%, SOM=0.17%, and BD=1.51 g cm$^{-3}$; and (C) Silty clay loam with SAND=25.23%, SILT=56.51%, CLAY=16.26%, SOM=0.65%, and BD=1.32 g cm$^{-3}$. Note that open circles denote the measured data, and the solid lines present the fitted curves.

Table 5
Correlation matrix of soil hydraulic parameters via basic soil properties

|   |   | SAND | SILT | CLAY | SOM | BD | ln(SAND) | ln(SILT) | ln(CLAY) | ln(SOM) | ln(BD)  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  θ_{s} | Pearson Correlation | 0.020 | 0.086 | -0.407^{a} | -0.071 | -0.465^{a} | 0.203 | 0.180 | -0.244 | -0.048 | -0.471^{a}  |
|   |  Sig.^{b} (2-tailed) | 0.874 | 0.504 | 0.001 | 0.581 | 0 | 0.111 | 0.158 | 0.054 | 0.708 | 0  |
|   |  N^{c} | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63  |
|  α | Pearson Correlation | 0.573^{a} | -0.575^{a} | -0.331^{a} | -0.316^{d} | 0.060 | 0.484^{a} | -0.699^{a} | -0.287^{d} | -0.395^{a} | 0.061  |
|   |  Sig. (2-tailed) | 0 | 0 | 0.008 | 0.012 | 0.641 | 0 | 0 | 0.023 | 0.001 | 0.633  |
|   |  N | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63  |
|  n | Pearson Correlation | 0.128 | -0.057 | -0.338^{a} | -0.349^{a} | 0.302^{d} | 0.069 | -0.090 | -0.570^{a} | -0.366^{a} | 0.306^{d}  |
|   |  Sig. (2-tailed) | 0.319 | 0.659 | 0.007 | 0.005 | 0.016 | 0.589 | 0.482 | 0 | 0.003 | 0.015  |
|   |  N | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63  |
|  ln^{a}(θ_{s}) | Pearson Correlation | 0.044 | 0.064 | -0.428^{a} | -0.075 | -0.454^{a} | 0.229 | 0.16 | -0.262^{d} | -0.058 | -0.46^{a}  |
|   |  Sig. (2-tailed) | 0.731 | 0.619 | 0 | 0.557 | 0 | 0.071 | 0.209 | 0.038 | 0.649 | 0  |
|   |  N | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63  |
|  ln(α) | Pearson Correlation | 0.682^{a} | -0.667^{a} | -0.456^{a} | -0.260^{d} | -0.098 | 0.684^{a} | -0.651^{a} | -0.345^{a} | -0.312^{d} | -0.104  |
|   |  Sig. (2-tailed) | 0 | 0 | 0 | 0.04 | 0.444 | 0 | 0 | 0.006 | 0.013 | 0.417  |
|   |  N | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63  |
|  ln(n) | Pearson Correlation | 0.135 | -0.064 | -0.344^{a} | -0.362^{a} | 0.309^{d} | 0.074 | -0.106 | -0.565^{a} | -0.378^{a} | 0.313^{d}  |
|   |  Sig. (2-tailed) | 0.29 | 0.617 | 0.006 | 0.004 | 0.014 | 0.565 | 0.407 | 0 | 0.002 | 0.013  |
|   |  N | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63 | 63  |
|  K_{s} | Pearson Correlation | -0.050 | 0.110 | -0.080 | -0.170 | -0.290 | -0.170 | 0.010 | -0.32 | -0.140 | -0.29  |
|   |  Sig. (2-tailed) | 0.535 | 0.641 | 0.335 | 0.784 | 0.091 | 0.974 | 0.061 | 0.421 | 0.324 | 0.086  |
|   |  N | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36  |
|  ln(K_{s}) | Pearson Correlation | -0.010 | 0.040 | -0.120 | -0.070 | -0.370^{d} | -0.110 | -0.200 | -0.160 | -0.220 | -0.37^{d}  |
|   |  Sig. (2-tailed) | 0.971 | 0.824 | 0.497 | 0.668 | 0.028 | 0.511 | 0.246 | 0.360 | 0.198 | 0.027  |
|   |  N | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36  |

### 3.2. Parameterisation of the soil water retention curve

The 63 measured soil water retention data were fitted to Eq. (1) with the restriction of m=1-1/n and n>1. However, the value of soil residual water content (θ$_{s}$) derived from nonlinear regression analysis is not reasonable since some θ$_{s}$ values of 63 soil retention curves exceed 0.20 or even more than 0.30 cm$^{3}$ cm$^{-3}$. The high soil residual water content was concerned. After carefully checking the raw retention data, it could be explained by the non-equilibrium measurement of soil water content in the 1500 kPa-pressure chamber, which was too close to the water content at pressure of 500 kPa. The last point of soil water retention curve was removed and replaced by air-dry water content corresponding to the soil water pressure head of approximate 22,000 kPa (White, 1997) instead. The second parameterisation results showed that only nine of 63 samples had the term of θ$_{s}$ in their soil water retention equation formula in which θ$_{s}$ ranged from 0.002 cm$^{3}$ cm$^{-3}$ to 0.100 cm$^{3}$ cm$^{-3}$. θ$_{s}$ is set to be zero if the fitted θ$_{s}$ is less than 0.001 cm$^{3}$ cm$^{-3}$ as estimated by RETC. Based on the above pre-analysis on the best equation to fit the SWRC, the original van Genuchten model (1980) without θ$_{s}$ of SWRC:

$$\theta = \frac{\theta_s}{(1 + |\alpha h|^n)^{(1-1/n)}} \tag{5}$$

was chosen to better describe the soil water retention characteristic of Fengqiu County soils. The mean and standard error

of the retention parameters in Eq. (5) of the third parameterisation are listed in Table 4. Apparently, the adjusted R$^{2}$ values for nonlinear regression given in Table 4 indicate that Eq. (5) is able to describe the coarse textured soils better than the fine textured soils in Fengqiu County. There is no other consistent pattern in the variation of θ$_{s}$, α, and n according to soil texture. Fig. 2 shows the measured and fitted retention curves of a sand, a sandy loam and a silty clay loam, respectively. It also gives visual information about the goodness of fitting the measured

Table 6
PTFs for estimating soil hydraulic parameters of the van Genuchten models as a function of basic soil properties

|  Model Parameters | Regression equations | SSR | SSE | R^{2}_{adj}  |
| --- | --- | --- | --- | --- |
|  ln(θ_{s}) | -1.531+0.212*ln(SAND)+0.006*SILT-0.051*SOM-0.566*ln(BD) | 0.355 | 0.206 | 0.61  |
|  ln(α) | -67.408-0.040*SILT-0.670*ln(SILT)-2.189*SOM+1.410*ln(SOM)+78.400*BD-121.331*ln(BD) | 120.0 | 76.12 | 0.57  |
|  n | 1.488+0.002*ln(SILT)+0.013*CLAY-0.248*ln(CLAY)+0.048*ln(SOM)+0.451*ln(BD) | 0.642 | 0.524 | 0.51  |
|  ln(K_{s}) | 13.262-1.914*ln(SAND)-0.974*ln(SILT)-0.058*CLAY-1.709*ln(SOM)+2.885*SOM-8.026*ln(BD) | 25.94 | 10.13 | 0.66  |

retention data to Eq. (5) for the soil samples with different textures listed in Table 4.

The poor prediction for the SWRC parameters of the clay-textured soil using Eq. (5) could be explained by several reasons. For example, the laboratory measurements are not done very well because the clay soil always releases water very slowly when drying during the measurement. This results in overestimating soil water contents at high pressure heads. Other reasons mentioned by van Genuchten (1980) regarding this same problem do not apply here. Is this because of $\theta_r$ being set to be zero? If $\theta_r$ is flexible, some of the predicted value of $\theta_r$ will be overestimated as mentioned earlier. In addition, $\theta_r$ of clay-textured soils is always underestimated by RETC in this study. Conceptually, $\theta_r$ is very low at huge pressure head condition even though clay $\theta_r$ is considered greater than sand $\theta_r$. It seems that the poor prediction for the SWRC parameters of clay-textured soils results from the inability of van Genuchten SWRC model to match the experimental soil water retention data because it assumes unimodal pore-size distributions underlying all soils. Durner (1994) introduced the concept of multimodal pore-size distributions in estimating soil hydraulic properties, e.g. $\theta(h)$ and $K(h)$, but this approach increases the complexity of the expressions of soil hydraulic properties and does not comply with the ultimate purpose of developing robust PTFs in this study, which is based on the universal national soil survey

database. Furthermore, according to van Genuchten (1980), limited data at low water contents leave some doubt about the accuracy of the fitness, and $\theta_r$ needs to be estimated by other independent procedure.

3.3. Correlation analysis of soil hydraulic parameters vs. basic soil properties

In order to develop the fundamental relationships between soil hydraulic parameters and the basic soil properties, the correlation analysis of SPSS package was applied, and the statistical results are shown in Table 5.

For the soil hydraulic parameters, it is found that a high correlation exists between $\theta_s$ and CLAY and BD, as well as between $\alpha$ and SAND, SILT, CLAY, and SOM. The $n$ parameter has significant correlation with CLAY, SOM, and BD. It is seen that there is no significant correlation between $K_s$ and basic soil properties. When the logarithmical transformation of $K_s$ is considered during the correlation analysis, BD becomes significantly related to $K_s$. From Table 5, it can be seen that in most cases the natural logarithmical transformation of variables increases the correlation with other variables considered. Therefore, $\theta_s$, $\alpha$ and $K_s$ would be better transformed logarithmically. The distributions of $\ln(\theta_s)$, $\ln(\alpha)$ and $\ln(K_s)$ are closer to the normal distribution compared with the non-transformed values, and give higher correlations with different

![img-4.jpeg](None)

**{"image_type": "plot", "description": "This is a scatter plot comparing measured values of ln(θ) (x-axis) with predicted values of ln(θ) (y-axis). The x-axis ranges from approximately -1.1 to -0.5, and the y-axis ranges from approximately -1.1 to -0.5. The data points are scattered around a diagonal line (y = x), indicating a positive correlation between measured and predicted values. Key observations include:\n\n1. Most data points cluster near the diagonal line, suggesting good agreement between measured and predicted values.\n2. There is some spread of points away from the line, indicating variability or potential outliers.\n3. The trend suggests that as measured ln(θ) increases, predicted ln(θ) also increases, following a roughly linear relationship.\n\nApproximate key data points (measured ln(θ), predicted ln(θ)):\n- (-1.05, -1.05)\n- (-0.95, -0.95)\n- (-0.85, -0.85)\n- (-0.75, -0.75)\n- (-0.65, -0.65)"}**

![img-5.jpeg](None)

**{"image_type": "plot", "description": "This is a scatter plot comparing measured values of ln(α) (natural logarithm of α) on the X-axis to predicted values of ln(α) on the Y-axis. Both axes are labeled with 'ln(α)' and appear to use the same scale. The plot includes a diagonal line representing the 1:1 relationship (y = x), indicating perfect agreement between measured and predicted values. The data points are scattered around this line, suggesting a general correlation between the measured and predicted values. The trend shows that as the measured ln(α) increases, the predicted ln(α) also increases, though some deviation from the 1:1 line is observed. Key observations include:\n\n- Most data points cluster near the 1:1 line, indicating reasonable prediction accuracy.\n- A few outliers are present, particularly at lower measured ln(α) values, where predictions deviate more significantly.\n- The spread of points suggests variability in prediction performance across the range of ln(α) values.\n\nApproximate key data points (measured ln(α), predicted ln(α)):\n- (-10, -9.5)\n- (-5, -4.8)\n- (0, 0.2)\n- (5, 4.9)\n- (10, 9.8)"}**

![img-6.jpeg](None)

**{"image_type": "plot", "description": "This is a scatter plot comparing predicted values of 'n' (y-axis) against measured values of 'n' (x-axis). The x-axis is labeled 'Measured n' and ranges from 1.0 to 2.0, while the y-axis is labeled 'Predicted n' and ranges from 0.5 to 3.5. The data points are represented by black squares and gray circles, with a diagonal reference line (y = x) indicating perfect agreement between predicted and measured values. Most data points cluster around the reference line, suggesting a strong correlation between predicted and measured values. Key observations include:\n\n- A cluster of points near the lower end of the measured range (1.0 to 1.5) with predicted values mostly between 1.0 and 2.0.\n- Some outliers are present, particularly at higher predicted values (above 2.5) for measured values around 1.5.\n- The trend indicates that as measured 'n' increases, predicted 'n' also tends to increase, following the reference line closely for most data points."}**

![img-7.jpeg](None)

**{"image_type": "plot", "description": "This is a scatter plot comparing measured values (X-axis) and predicted values (Y-axis) of a variable in Kelvin (K). The X-axis is labeled 'Measured ln(K)' and the Y-axis is labeled 'Predicted ln(K)'. The data points are distributed around a diagonal line (y = x), indicating a positive correlation between measured and predicted values. Key observations include:\n\n1. Most data points cluster near the diagonal line, suggesting good agreement between measured and predicted values.\n2. There is some scatter, particularly at higher values, indicating variability or potential outliers.\n3. The trend suggests that as the measured ln(K) increases, the predicted ln(K) also increases linearly.\n\nApproximate key data points (measured ln(K), predicted ln(K)):\n- (0, 0)\n- (1, 1)\n- (2, 2)\n- (3, 3)\n- (4, 4)\n- (5, 5)\n\nThe plot demonstrates a strong linear relationship between measured and predicted values, with the diagonal line representing perfect agreement."}**

Fig. 3. Measured vs. predicted A) $\ln(\theta_s)$, B) $\ln(\alpha)$, C) $n$ and D) $\ln(K_s)$ by PTFs of this study (●), Vereecken et al. (1989, 1990) (□), ROSETTA (△) and HYPRES (◇). The straight line in each plot is the 1:1 line.

Table 7
Summary of the double cross-validation test for the developed PTFs

|  Model Parameters | Subsets | Regression equations | R²adj | r²  |
| --- | --- | --- | --- | --- |
|  ln(θs) | A | -1.641+0.228*ln(SAND)+0.007*SILT-0.028*SOM-0.560*ln(BD) | 0.55 | 0.59  |
|   |  B | -1.339+0.190*ln(SAND)+0.005*SILT-0.057*SOM-0.719*ln(BD) | 0.63 | 0.54  |
|  ln(α) | A | 1.028-0.066*SILT-0.291*ln(SILT)-7.251*SOM+4.044*ln(SOM)+10.830*BD-29.816*ln(BD) | 0.74 | 0.56  |
|   |  B | -108.438-0.021*SILT-1.088*ln(SILT)-0.192*SOM+0.324*ln(SOM)+121.195*BD-181.381*ln(BD) | 0.50 | 0.59  |
|  n | A | 1.184+0.037*ln(SILT)+0.008*CLAY-0.172*ln(CLAY)+0.022*ln(SOM)+0.892*ln(BD) | 0.45 | 0.47  |
|   |  B | 1.647+0.013*ln(SILT)+0.018*CLAY-0.269*ln(CLAY)+0.052*ln(SOM)+0.017*ln(BD) | 0.49 | 0.45  |
|  ln(Ks) | A | 16.753-2.333*ln(SAND)-1.303*ln(SILT)-0.074*CLAY-1.688*ln(SOM)+3.605*SOM-11.106*ln(BD) | 0.74 | 0.62  |
|   |  B | 10.039-1.884*ln(SAND)-0.802*ln(SILT)-0.065*CLAY-2.210*ln(SOM)+3.653*SOM-3.270*ln(BD) | 0.58 | 0.61  |

For ln(θs), ln(α) and n, subsets A and B have 31 samples and 32 samples, respectively. For ln(Ks), both subsets A and B have 18 samples.

soil properties (Vereecken et al., 1989; Goncalves et al., 1997). The above correlation analysis is performed to detect the linear relationships among the variables, and is used to advise the PTFs structure.

3.4. PTFs for soil water retention parameters

The derivation of PTFs for soil water retention parameters was performed for the 63 soil samples through multiple regression using the basic soil properties, including their logarithmically-transformed values and their interaction terms. Because the sample size was not large enough, the multiple regression analysis was not carried out in textural groups. A backward method regression (Norusis, 1994) selected variables at 0.10 significance level for entry in the regression model, while a 0.05 significance level was applied to retain the

variables in the model. The final multiple regression equations and statistical information, under the assumption of no further statistical improvement, are given in Table 6. The inclusion of interaction terms of basic soil properties were considered as increasing the PTFs complexity rather than improving statistical significance. The performance of all PTFs was assessed by the values of R²adj.

The logarithmic form of saturated water content (θs) was positively related to SAND and SILT, and negatively related to BD and SOM. The regression explained about 61% of the variance by these arguments. As discussed in the correlation analysis, the α parameter for SWRC is presented in the logarithmic form in its regression equation, which explains 57% of the variance for ln(α). The value of ln(α) is mainly estimated by SILT, SOM and BD. The equation for n consists of SILT, CLAY, SOM, and BD as predictors, and explains 51% of the variance in n. It means that SAND is not an important variable to predict the value of n. Hence, as seen from the values of R²adj, among these three parameters, n is the poorest estimated by PTFs. The goodness of measured vs. predicted ln(θs), ln(α) and n is shown in Fig. 3, respectively. The information of regression standardised residuals against regression standardised predicted values of ln(θs), ln(α) and n from multiple regression analysis also indicates that most of the regression standardised residuals lie randomly between -2 and +2, and thus there is no significant correlation between standardised residual and standardised predicted value. Therefore, the PTFs for predicting ln(θs), ln(α) and n satisfy the assumption of linearity and statistical non-bias, and are regarded as reliable.

Compared to other studies, our results show that the PTFs for predicting soil water retention parameters of Fengqiu County soils are worse than those reported by Vereecken et al. (1989) for Belgian soils, Wösten and van Genuchten (1988) for Dutch soils, Rajkai et al. (1996) for Swedish soils, and Goncalves et al. (1997) for Portuguese soils even though we only have a total of 63 soil samples, but slightly better than Tomasella et al. (2003) for Brazilian soils. It is possible that the particle-size distribution is insufficient and not detailed enough to identify the individual contribution of soil particles to the soil water retention characteristics. Another reason could be that the studied soil textures are quite similar, very close to sandy loam. This suggests to us that the PTFs have to be used with caution when extrapolation of PTFs using basic soil properties is performed.

Table 8
Comparison of the performance of different PTFs on the complete SWRC data set for Fengqiu County soils

|  PTFs | ln(θs) |   |   | ln(α) |   |   | n |   |   | ln(Ks)  |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|   |  SSE | r | p | SSE | r | p | SSE | r | p | SSE | r | p  |
|  This study | 0.21 | 0.80 | <0.001 | 76 | 0.78 | <0.001 | 0.52 | 0.74 | <0.001 | 10 | 0.85 | <0.001  |
|  Vereecken et al. (1989, 1990) | 1.64 | 0.30 | <0.05 | 161 | 0.71 | <0.001 | 10.32 | 0.24 | n.s. | 280 | 0.54 | <0.001  |
|  ROSETTA (Schaap et al., 2001) | 2.84 | 0.16 | n.s.^{a} | 150 | 0.50 | <0.001 | 26.97 | 0.05 | n.s. | 140 | 0.37 | <0.05  |
|  HYPRES (Wösten et al., 1999) | 1.14 | 0.55 | <0.001 | 457 | 0.67 | <0.001 | 1.26 | 0.47 | <0.001 | 90 | 0.08 | n.s.  |

r denotes the coefficient of Pearson correlation, and p is the probability. Note that the mass fraction has been transformed to the US system when PTFs of Vereecken et al. (1989, 1990), ROSETTA and HYPRES are applied.

$^{a}$ n.s. denotes not significant.

### 3.5. PTFs for saturated soil hydraulic conductivity

Total 36 soil samples were used to develop the PTFs for saturated hydraulic conductivity using a backward multiple regression method, as described for the soil water retention parameters. Table 6 lists the regression results based on the basic soil properties.

It is seen from Table 6 that $K_s$ was logarithmical transformed for better normal distribution and better regression output. The PTF equation for estimating $K_s$ is composed of all the basic soil properties, and explains about 66% of variance. The fact that more than 97% of the regression standardised residuals lie randomly between -2 and +2 from this multiple regression analysis indicates that there is no significant correlation between standardised residual and standardised predicted value. Hence, it implies that this PTF for predicting $\ln(K_s)$ satisfies the assumption of linearity statistically, and is reliable.

### 3.6. Validation of PTFs

The double cross-validation test for the above developed PTFs in terms of estimating $\ln(\theta_s)$, $\ln(\alpha)$, $n$ and $\ln(K_s)$ was carried out, and the results were summarized in Table 7. As seen in Table 7, the signs of the subset regression equations were stable, but the degree of significance changed, which was probably caused by the relatively small sample size. The coefficients of determination for the regression equations

developed for the subsets ($R^2_{adj}$) were similar to those obtained for PTFs for the complete set. In addition, the square of the Pearson correlation coefficients between predicted and measured parameters, defined as cross-validity coefficients ($r^2$), relative to each of the two subsets used for the cross-validation were not significantly different at the 0.05 level.

### 3.7. Comparison with existing PTFs

Three sets of existing PTFs: Vereecken et al. (1989, 1990), ROSETTA (Schaap et al., 2001) and HYPRES (Wösten et al., 1999) were applied to the complete SWRC data set of Fengqiu County soils, and their performance in estimating the soil hydraulic parameters were compared to that of the PTFs derived in this study (Table 8 and Fig. 3). As seen in Table 8, none of the three existing PTFs did a better job than PTFs of this study in estimating $\ln(\theta_s)$, $\ln(\alpha)$, $n$ and $\ln(K_s)$ at all, but briefly based on $r$ and $p$, HYPRES performed slightly better than Vereecken et al. (1989, 1990) and ROSETTA was the worst. In particular, all of the three existing PTFs provided better prediction for $\ln(\alpha)$ than that for $\ln(\theta_s)$, $n$ and $\ln(K_s)$, but with varying accuracy. Among them, only HYPRES had the capability to predict $n$, and ROSETTA and HYPRES failed to estimate $\ln(\theta_s)$ and $\ln(K_s)$, respectively.

The limitation of applying PTFs developed from one region to other regions is obvious through the comparison analysis in this paper.

![img-8.jpeg](None)

**{"image_type": "map", "description": "The image is a parameter map of Fengqiu County displaying the Ks values (cm/day) of the fourth soil layer (60-80 cm depth). The map uses a color-coded legend to represent different ranges of Ks values:\n\n- Light yellow: 5.02 - 8.29\n- Light green: 8.29 - 12.28\n- Light blue: 12.28 - 17.64\n- Light gray: 17.64 - 26.14\n- Dark red: 26.14 - 32.35\n\nThe map shows spatial variation in Ks values across the county, with darker red areas indicating higher Ks values and lighter colors indicating lower Ks values. The map also includes a scale bar (0 to 4 km) and a north directional arrow. A water body is marked in the southeastern part of the county."}**

Fig. 4. Spatial distribution of saturated soil water conductivity ($K_s$, cm d$^{-1}$) of the fourth soil layer (60–80 cm) estimated by using locally-developed pedo-transfer functions in Fengqiu County of the North China Plain.

![img-9.jpeg](None)

**{"image_type": "map", "description": "The image consists of two maps of Fengqiu County comparing observed and predicted crop yields (wheat + maize) for the years 1998-1999. Both maps use a color gradient to represent crop yield ranges in kilograms per hectare per year, with the following legend:\n\n- 3000-6000 (red)\n- 6000-7500 (orange)\n- 7500-9000 (yellow)\n- 9000-11000 (light green)\n- 11000-13000 (green)\n- 13000-15000 (dark green)\n- 15000-17000 (blue)\n\n**Observed Map:**\n- Displays actual surveyed crop yield data.\n- Blank areas indicate villages without surveyed crop yield data or invalid crop yield data.\n\n**Predicted Map:**\n- Displays predicted crop yields based on a model.\n- Blank areas represent non-agricultural lands.\n\nBoth maps include a scale bar (0 to 10 kilometers) and a north arrow for orientation. The title of the image is \"Observed and Predicted Crop Yields (Wheat + Maize) in Fengqiu County for 1998-1999.\""}**

Fig. 5. Observed and predicted crop yields (wheat and maize) in Fengqiu County for the 1998–1999 rotation year.

### 3.8. Application of PTFs

The parameters for soil water retention and saturated hydraulic conductivity are the intermediate characteristics needed to compute other information with more practical meaning, e.g. water balance and crop yield. A number of studies used soil water simulation models to evaluate the performance of estimated soil hydraulic properties through the simulation of air–crop–soil agroecosystems (Wösten et al., 1995; Espino et al., 1996; van Alphen et al., 2001; Nemes et al., 2003).

The PTFs derived from this study were used in Fengqiu County in the North China Plain to estimate parameters of soil hydraulic properties for van Genuchten (1980) models in order to simulate water balance and interaction with C and N cycling in a wheat–maize cropping agroecosystem using the Water and Nitrogen Management Model WNMM (Li, 2002) at the county scale from October 1998 to September 1999. The spatial soil information, including SAND, SILT, CLAY, SOM and BD, was derived from the soil map and soil survey report produced in the second national soil survey of China in the early 1980s. Fig. 4 demonstrates an example, the estimated spatial distribution of the saturated soil hydraulic conductivity at 60–80 cm soil depth of Fengqiu County soils using locally-developed PTFs. The spatial distribution of crops was based on the latest landuse map. A comprehensive field survey was carried out in the fall of 1999, covering all the information of agricultural practices for the 1998–1999 rotation

year in 605 individual villages. For detailed information of the WNMM simulation regarding mechanism of WNMM, settings of initial conditions in the agroecosystem and simulation outputs, we refer to the paper of Li et al. (in press). Because of lack of spatially measured soil water content at the county scale, the surveyed crop

![img-10.jpeg](None)

**{"image_type": "plot", "description": "The plot is a scatter plot with a linear regression line showing the relationship between observed crop yields (x-axis, in kg/hectare/year) and predicted crop yields (y-axis, in kg/hectare/year).\n\n- **X-axis**: Observed Crop Yields (kg/hectare/year), ranging from 6000 to 16000.\n- **Y-axis**: Predicted Crop Yields (kg/hectare/year), ranging from 6000 to 16000.\n- **Trend**: The data points show a positive linear relationship, indicating that as observed crop yields increase, predicted crop yields also increase. The regression equation is provided as `y = 0.63x + 4286`, where `y` is the predicted yield and `x` is the observed yield. The coefficient of determination (R²) is 0.33, suggesting a moderate fit of the model to the data.\n\nKey data points (approximate):\n- At observed yield ~8000 kg/hectare/year, predicted yield ~9000 kg/hectare/year.\n- At observed yield ~10000 kg/hectare/year, predicted yield ~10500 kg/hectare/year.\n- At observed yield ~12000 kg/hectare/year, predicted yield ~12000 kg/hectare/year.\n- At observed yield ~14000 kg/hectare/year, predicted yield ~13500 kg/hectare/year."}**

Fig. 6. Linear regression between the observed and predicted crop yields (wheat and maize) by WNMM in Fengqiu County for the 1998–1999 rotation year.

yields in 605 villages were alternatively used to assess the performance of the derived PTFs. As seen in Fig. 5, the village-averaged pattern of spatial variation of grain yields of wheat and maize predicted by WNMM is similar to that of the surveyed crop grain yields, with a determining coefficient $R^2$ of 0.33 ($P<0.001$) for 409 valid study villages (Fig. 6). The performance of PTFs in using WNMM predicting crop yield in Fengqiu County is acceptable when considering other variations caused by damages of diseases and insects, soil salinity and deficiency of other nutrients, e.g. phosphorus.

#### 4. Conclusions

The van Genuchten model (1980) without a residual water content term was selected as the optimal equation to describe the soil water retention characteristic of Fengqiu County soils.

PTFs for estimating soil hydraulic characteristics were derived from basic soil properties (particle-size distribution, soil organic matter, and bulk density). Among the three parameters of Eq. (5), the saturated water content ($\theta_s$) was best predicted through the entire soil data set, while prediction of the value of $n$ was the poorest, according to the assessment of $R_{adj}^2$ of the developed regression equations. The developed regression models for estimating $\ln(\theta_s)$, $\ln(\alpha)$, $n$ and $\ln(K_s)$ were tested for their stability and predictability by the double cross-validation method. It was found that the signs of the regression coefficients and the determination coefficients were stable.

The PTFs obtained from this study appear superior in predicting the soil hydraulic parameters, compared to three existing PTFs: Vereecken et al. (1989, 1990), ROSETTA and HYPRES. This confirms the limitation of applying PTFs developed from one region to other regions.

The PTFs derived in this study were used to estimate soil hydraulic properties for the simulation of a wheat and maize cropping agroecosystem in Fengqiu County for the 1998–1999 rotation year. The simulation result of crop yield is comparable to the field observations ($R^2=0.33$, $n=409$, $p<0.01$).

To improve the performance of PTFs, more information on soil properties such as soil structure may be required to reconstruct PTFs.

#### Acknowledgments

This study was funded by the Australian Centre for International Agricultural Research (Project LWR/96/164) and the Knowledge Innovation Program of the Chinese Academy of Sciences (Grant No.kzcx2-yw-406).

#### References

Arya, L.M., Paris, J.F., 1981. A physicoempirical model to predict the soil moisture characteristic from particle-size distribution and bulk density data. Soil Science Society of America Journal 45, 1023–1030.
Baumer, O.M., 1992. Predicting unsaturated hydraulic parameters. In: van Genuchten, M.Th., et al. (Ed.), Proceedings of the International Workshop on Indirect Methods for Estimating the Hydraulic Properties of Unsaturated Soils. Riverside, CA, 11–13 Oct. University of California, Riverside, CA, pp. 341–354.

Bouma, J., van Lanen, H.A.J., 1987. Transfer functions and threshold values: from soil characteristics to land qualities. In: Beck, K.J., et al. (Ed.), Quantified Land Evaluation. International Institute for Aerospace Survey and Earth Sciences. ITC Publication, vol. 6. Enschede, the Netherlands, pp. 106–110.
Cook, F.J., Broeren, A., 1995. Six methods for determining sorptivity and hydraulic conductivity with disk permeameters. Soil Science 157, 2–11.
Cornelis, V.M., Ronsyn, J., van Meirvenne, M., Hartmann, R., 2001. Evaluation of pedotransfer functions for prediction the soil moisture retention curve. Soil Science Society of America Journal 65 (3), 638–648.
Cosby, B.J., Hornberger, G.M., Clapp, R.B., Ginn, T.R., 1984. A statistical exploration of the relationship of soil moisture characteristic to the physical properties of soils. Water Resources Research 20, 682–690.
Durner, W., 1994. Hydraulic conductivity estimation for soils with heterogeneous pore structure. Water Resources Research 30, 211–223.
Espino, A., Mallants, D., Vanclooster, M., Feyen, J., 1996. Cautionary notes on the use of pedotransfer functions for estimating soil hydraulic properties. Agricultural Water Management 29, 235–253.
Goncalves, M.C., Pereira, L.S., Leij, F.J., 1997. Pedo-transfer functions for estimating unsaturated hydraulic properties of Portuguese soils. European Journal of Soil Science 48, 387–400.
Green, P.E., Carroll, J.D., 1978. Analysing Multivariate Data. John Wiley & Sons, New York.
Gupta, S.C., Larson, W.F., 1979. Estimating soil water characteristic from particle-size distribution, organic matter percent, and bulk density. Water Resources Research 15, 1633–1635.
Haverkamp, R., Parlange, J.Y., 1986. Predicting the water retention curve from particle-size distribution: 1. Sandy soils without organic matter. Soil Science 142, 325–339.
Husz, G., 1967. The determination of pF-curves from texture using multiple regression. Zeitschrift für Pflanzenernährung und Bodenkunde 116 (2), 23–29.
Imam, B., Sorooshian, S., Mayr, T., Schaap, M.G., Wösten, J.H.M., Scholes, R.J., 1999. Comparison of pedotransfer functions to compute water holding capacity using the van Genuchten model in inorganic soils — report to IGBP-DIS soil data Tasks. IGBP-DIS Working Paper No. 22, IGBP-DIS, Toulouse, Cedex, France.
Kar, G., Singh, R., Verma, H.N., 2004. Spatial variability studies of soil hydrophysical properties using GIS for sustainable crop planning of a water shed of eastern India and its testing in a rainfed rice area. Australian Journal of Soil Research 42, 369–379.
Kern, J.S., 1995. Evaluation of soil water retention models based on basic soil physical properties. Soil Science Society of America Journal 59, 1134–1141.
Klute, A., 1986. Water Retention: Laboratory methods. In: A. Klute et al. (Editors), Methods of soil analysis: Part 1, Physical and mineralogical methods, 2nd edition. Agronomy Monograph No. 9, American Society of Agronomy and Soil Science Society of America, Madison, Wisconsin, pp. 635–662.
Li, Y., 2002. A spatially referenced model for identifying optimal strategies for managing water and fertilizer nitrogen under intensive cropping in the North China Plain, Ph.D thesis, 257 p., The University of Melbourne, Australia.
Li, Y., White, R.E., Chen, D., Zhang, J.B., Li, B.G., Zhang, Y.M., Huang, Y.F., Edis, R., in press. A spatially referenced Water and Nitrogen Management Model (WNMM) for (irrigated) intensive cropping systems in the North China Plain. Ecological Modelling.
Minasny, B., McBratney, A.B., Bristow, K.L., 1999. Comparison of different approaches to the development of pedotransfer functions for water retention curves. Geoderma 93, 225–253.
Mualem, Y., 1976. A new model for predicting the hydraulic conductivity of unsaturated porous media. Water Resources Research 12 (3), 513–521.
Nemes, A., Schaap, M.G., Wösten, J.H.M., 2003. Functional evaluation of pedotransfer functions derived from different scales of data collection. Soil Science Society of America Journal 67, 1093–1102.
Nicolaeva, S.A., Pachepsky, Ya.A., Shcherbakov, R.A., Shcheglov, A.I., 1986. Modelling of moisture regime for ordinary chernozem. Pochovedenie 6, 52–59.
Norusis, J.M., 1994. SPSS professional statistics 6.1. SPSS Inc., Chicago, Ill.

Pachepsky, Ya.A., Shcherakov, R.A., Varallyay, G., Rajkai, K., 1982. Statistical analysis of water retentions with other physical properties of soils. Pochvovedenie 2, 42–52.

Pachepsky, Ya.A., Timlin, A.D., Varallyay, G.V., 1996. Artificial neural networks to estimate soil water retention from easily measurable data. Soil Science Society of America Journal 60, 727–733.

Pachepsky, Ya.A., Rawls, W.J., Timlin, D.J., 1999. The current status of pedotransfer functions: Their accuracy, reliability, and utility in field-and regional-scale modelling. In: Corwin, D.L., et al. (Ed.), Assessment of Non-point Source Pollution in the Vadose Zone. Geophysical Monograph, vol. 108. American Geophysical Union, Washington, DC, pp. 223–234.

Puckett, W.E., Dane, J.H., Hajek, B.F., 1985. Physical and mineralogical data to determine soil hydraulic properties. Soil Science Society of America Journal 49, 831–836.

Rajkai, K., Kabos, S., van Genuchten, M.Th., Jansson, P.E., 1996. Estimation of water retention characteristics from the bulk density and particle-size distribution of Swedish soils. Soil Science 161 (12), 832–845.

Rawls, W.J., Brakensiek, D.L., 1985. Predictions of soil water properties from hydrologic modelling. In: Jones, E., Ward, T.J. (Eds.), Watershed Management. Eighties Proceedings of Symposium of ASCE, Denver, CO. ASCE, New York, pp. 293–299.

Rawls, W.J., Brakensiek, D.L., 1989. Estimation of soil water retention and hydraulic properties. In: Morelseytoux, H.J. (Ed.), Unsaturated Flow in Hydrologic Modelling. Theory and Practice. Kluwer Academic Publishers, Dordrecht, pp. 275–300.

Rawls, W.J., Brakensiek, D.L., Saxton, K.E., 1982. Estimation of soil water properties. Transactions of the ASAE 108, 1316–1320.

Rawls, W.J., Gish, T.J., Brakensiek, D.L., 1991. Estimating soil water retention from soil physical properties and characteristics. Advances of Soil Science 16, 213–234.

Renger, M., 1971. The estimation of pore size distribution from texture, organic matter and bulk density. Zeitschrift für Kulturtechnik und Flurbereinigung 130, 53–67.

Research Group of Chinese Soil Taxonomy System, 1995. Chinese Soil Taxonomy System. China Agricultural Science and Technology Press, Beijing.

Schaap, M.G., Leij, F.J., 1998. Database-related accuracy and uncertainty of pedotransfer functions. Soil Science 163 (10), 765–779.

Schaap, M.G., Leij, F.J., van Genuchten, M.Th., 1998. Neural network analysis for hierarchical prediction of soil hydraulic properties. Soil Science Society of America Journal 62, 847–855.

Schaap, M.G., Leij, F.J., van Genuchten, M.Th., 2001. ROSETTA: A computer program for estimating soil hydraulic parameters with hierarchical pedotransfer functions. Journal of Hydrology 251 (3–4), 163–176.

Tamari, S., Wösten, J.H.M., Ruiz-Suarea, J.C., 1996. Testing an artificial neural network for predicting soil hydraulic conductivity. Soil Science Society of America Journal 60, 771–774.

Tietje, O., Hennings, V., 1996. Accuracy of the saturated hydraulic conductivity prediction by pedo-transfer functions compared to the variability within FAO textural classes. Geoderma 69, 71–84.

Tietje, O., Tapkenhinrichs, M., 1993. Evaluation of pedo-transfer functions. Soil Science Society of America Journal 57, 1088–1095.

Tomasella, J., Hodnett, M.G., 1998. Estimating soil water retention characteristics from limited data in Brazilian Amazonia. Soil Science 163, 190–202.

Tomasella, J., Pachepsky, Ya.A., Crestana, S., Rawls, W.J., 2003. Comparison of two techniques to develop pedotransfer functions for water retention. Soil Science Society of America Journal 67, 1085–1092.

Tyler, S.W., Wheatcraft, S.W., 1989. Application of fractal mathematics to soil water retention estimation. Soil Science Society of America Journal 53, 987–996.

van Alphen, B.J., Booltink, H.W.G., Bouma, J., 2001. Combining pedotransfer functions with physical measurement to improve the estimation of soil hydraulic properties. Geoderma 103, 133–147.

van den Berg, M., Klant, E., van Reeuwijk, L.P., Sombrock, G., 1997. Pedotransfer functions for the estimation of moisture retention characteristics of Ferrasols and related soils. Geoderma 78, 161–180.

van Genuchten, M.Th., 1980. A close-form equation for predicting the hydraulic conductivity of unsaturated soils. Soil Science Society of America Journal 44, 892–898.

van Genuchten, M.Th., Leij, F.J., 1992. On estimating the hydraulic properties of unsaturated soils. In: van Genuchten, M.Th. (Ed.), Proceedings of International Workshop on Indirect Methods for Estimating the Hydraulic Properties of Unsaturated Soils, Riverside, CA, 11–13 Oct 1989. University of California, Riverside, CA, pp. 1–14.

van Genuchten, M.Th., Leij, F.J., Yates, S.R., 1991. The RETC code for quantifying the hydraulic functions of unsaturated soils. EPA/600/2-91/065. U.S. Environmental Protection Agency, Ada, OK.

Vereecken, H., Maes, J., Feyen, J., Darins, P., 1989. Estimating the soil moisture retention characteristic from texture, bulk density, and carbon content. Soil Science 148, 389–403.

Vereecken, H., Maes, J., Feyen, J., 1990. Estimating unsaturated hydraulic conductivity from easily measured soil properties. Soil Science 149, 1–12.

Wagner, B., Tarnawski, V.R., Hennings, V., Müller, U., Wessolek, G., Plagge, R., 2001. Evaluation of pedotransfer functions for unsaturated soil hydraulic conductivity using an independent data set. Geoderma 102, 275–297.

White, R.E., 1997. Principles and Practice of Soil Science: The Soil as a Natural Resource, 3rd edition. Blackwell Science Ltd, Melbourne, Australia, p. 101.

Wösten, J.H.M., van Genuchten, M.Th., 1988. Using texture and other soil properties to predict the unsaturated soil hydraulic functions. Soil Science Society of America Journal 52, 1762–1770.

Wösten, J.H.M., Finke, P.A., Jansen, M.J.W., 1995. Comparison of class and continuous pedotransfer functions to generate soil hydraulic characterises. Geoderma 66, 227–237.

Wösten, J.H.M., Lilly, A., Nemes, A., Le Bas, C., 1999. Development and use of a database of hydraulic properties of European soils. Geoderma 90, 169–185.

Wösten, J.H.M., Pachepsky, Ya.A., Rawls, W.J., 2001. Pedotransfer functions: bridging the gap between available basic soil data and missing soil hydraulic characteristics. Journal of Hydrology (Amsterdam) 251, 123–150.