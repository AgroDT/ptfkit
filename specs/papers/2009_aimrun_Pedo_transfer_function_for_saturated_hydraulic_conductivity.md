# Pedo-transfer function for saturated hydraulic conductivity of lowland paddy soils

W. Aimrun · M. S. M. Amin

Received: 2 July 2008 / Revised: 7 May 2009 / Accepted: 17 May 2009 / Published online: 2 June 2009
© Springer-Verlag 2009

**Abstract** In paddy field, soil saturated hydraulic conductivity ($K_s$) plays as an important component in the calculation of irrigation requirement of the water balance equation and also for irrigation efficiency. Several laboratory and field methods can be used to determine $K_s$. Laboratory and field determinations are usually time consuming, expensive and labour intensive. Pedo-transfer functions (PTF) serve to translate the basic information found in the soil survey into a form useful for broader applications through empirical regression of functional relationships, such as simulation modelling. Since PTFs have not been applied to paddy soils in the study area, a lot of field measurements will require high labour input to determine $K_s$ hence high cost. This study attempts to seek a simplified method for determining $K_s$ values based on common existing soil properties through PTF technique. Soil samples ($n = 408$ samples) were collected randomly depending on the soil series within the 2,300 ha Sawah Sempadan rice cultivation area. Both field work and laboratory work were carried out. The samples were then analysed for the following properties: dry bulk density ($D_b$), soil particle percentage (Sand-S, Silt-Si and Clay-C), organic matter (OM) and geometric mean diameter (GMD). The measured $K_s$ values were obtained by using the falling head method. The parameters were then used as inputs for developing a

$K_s$ model by regression analysis using Statistical Analysis System (SAS) package. Stepwise regression analysis was applied to determine the best fit model based on $R^2$ and significant level. The results of the study showed that there is a high spatial variability of the saturated hydraulic conductivity in the paddy area. The best regression model for estimating $K_s$ was based on C, $D_b$, OM and GMD with the dependent variable ($K_s$) in a form of natural logarithm. The model inputs introduced by stepwise regression are commonly available therefore, this model is useful to replace the conventional method.

**Keywords** Falling head method ·
Water balance equation · Irrigation requirement ·
Spatial variability · Stepwise regression analysis

## Introduction

Soil saturated hydraulic conductivity ($K_s$) is an important soil physical property, especially for determining infiltration rate, irrigation practice, drainage design, run off, groundwater recharge and in simulating leaching and other agricultural and hydrological processes. Several laboratory and field methods can be utilized to determine $K_s$. Unfortunately, laboratory and field determinations are usually time consuming, expensive and labour intensive.

A study has shown that determining the saturated hydraulic conductivity using Double ring infiltrometer method may require 120 min. Rainfall simulator, Guelph permeameter and Guelph infiltrometer may take 125, 65 and 60 min, respectively (Gupta et al. 1993). Some research results indicate that something in the order of 1,300 measurements would have to be made in a 10-ha field to accurately measure the saturated hydraulic

W. Aimrun (✉) · M. S. M. Amin
Smart Farming Technology Laboratory, Institute of Advanced Technology, 43400 Serdang, Selangor, Malaysia
e-mail: aimrun@gmail.com

M. S. M. Amin
Department of Biological and Agricultural Engineering,
Faculty of Engineering, Universiti Putra Malaysia,
43400 Serdang, Selangor, Malaysia

conductivity to within 10% of the mean value (Warrick and Nielsen 1980). Field soils, on the other hand, exhibit large spatial variabilities in their hydraulic properties, especially their hydraulic conductivity. This variability implies that a large number of field measurements may be required to characterise a given field or area (Jabro 1992).

Generally, the determination of soil saturated hydraulic conductivity is based on direct and indirect methods. The direct methods are laboratory and field methods such as Falling head, Auger hole and Guelph permeameter. The indirect method is estimation method such as simulation model and pedo-transfer functions (PTF). The purpose of the indirect method is to facilitate as good as possible an estimate of saturated hydraulic conductivity based upon its accuracy and efficiency.

When measured hydraulic conductivity is not available, it is a common practice to estimate hydraulic conductivity from routinely measured soil physical and chemical properties, such as particle size distribution, bulk density, organic matter content and so on (Rawls et al. 1982). These estimated functions are often referred to as PTF (Bouma 1992; Bouma and Van Lanen 1987). PTFs relate different basic soil characteristics or soil properties with one another or land qualities (Bouma 1989). They serve to translate the basic information found in the soil survey into a form useful for broader applications through empirical regression of functional relationships, such as simulation modelling (Wagenet et al. 1991).

Recently, PTF for saturated hydraulic conductivity have not been applied to paddy soils in the study area yet. A lot of field measurements will require high labour input hence

## Literature review

Several PTF to estimate the soil hydraulic properties have been published over the 1980s. To apply those existing algorithms or PTF in a target oriented field, the existing algorithms or PTF must be tested on the basis of measurement of local soils in order to prove repetitions and identify the best approaches. Various investigators have also evaluated PTF for estimating the water retention function (Tietje and Hennings 1993; Tietje and Tapkenhinrichs 1992).

Cosby et al. (1984) represented the equation for estimating the hydraulic conductivity:

$$K_s(\text{cm d}^{-1}) = 60.96 \times 10^{(-0.6+0.0126(S)-0.0064(C))} \quad (1)$$

Campbell (1985) calculates the parameter $b$ in Eq. 2 by using the geometric mean particle size (Shirazi and Boersma 1984) and the geometric standard deviation of the particle size distribution:

$$\begin{aligned} b &= (\text{GMPS})^{-0.5} + 0.2(\text{GSD}) \\ K_s(\text{cm d}^{-1}) &= 339(1.3/(D_b))^{1.36b} \exp(-6.9(C) - 3.7(\text{Si})) \end{aligned} \quad (2)$$

where $b$ is the parameter which relates the unsaturated hydraulic conductivity function to the water retention (Burdine 1953; Campbell 1974, 1985), GMPS is the geometric mean particle size (mm) and GSD is the geometric standard deviation of the particle size distribution. The formula would lead to extremely inaccurate result if the bulk density were very low ($D_b \ll 1$).

Saxton et al. (1986):

$$K_s(\text{cm d}^{-1}) = 24 \exp \left[ 12.012 - 7.55 \times 10^{-2}(\text{S}) + \frac{\left(-3.895 + 3.671 \times 10^{-2}(\text{S}) - 0.1103(\text{C}) + 8.7546 \times 10^{-4}(\text{C})^2\right)}{0.332 - 7.251 \times 10^{-4}(\text{S}) + 0.1276(\log \text{C})} \right] \quad (3)$$

high cost. This study will simplify the determination of saturated hydraulic conductivity, reduce time, cost and labour.

This paper presents results of a study to develop a saturated hydraulic conductivity model based on easily measured soil properties or pedo-transfer function technique based on available measured soil physical and chemical properties namely, soil organic matter (OM), sand (S), silt (Si), clay (C), dry bulk density ($D_b$) and geometric mean diameter (GMD).

Vereecken et al. (1990):

$$\begin{aligned} K_s(\text{cm d}^{-1}) &= \exp[20.62 - 0.96(\ln \text{C}) - 0.66(\ln \text{S}) \\ &\quad - 0.46(\ln \text{OM}) - 8.43(D_b)] \end{aligned} \quad (4)$$

Jabro (1992) used 350 samples of varying particle size distribution, bulk density data to predict the saturated hydraulic conductivity of soil by developing the linear regression model. He found that sand content in these soil samples did not play a significant role in predicting soil hydraulic conductivity. The model was developed with the

independent parameters of silt, clay and bulk density as the following:

$$\log K_s (\text{cm h}^{-1}) = 9.56 - 0.81 (\log \text{Si}) - 10.9 (\log \text{C}) - 4.64 (D_b) \quad (5)$$

The coefficient of multiple determination ($R^2$) of the model was significant and relatively high ($R^2 = 0.68$, $P < 0.0001$) and a high correlation coefficient ($r = 0.79$, $P < 0.0001$) was found between the field measured and model simulated hydraulic conductivity.

He supposed, however, to improve the model should be possible by including more input soil parameters or employing a longer set of data. Additional validation tests are needed for the model using various ranges of soils and different hydraulic conductivity measurement techniques.

Ali Hassan Shah et al. (1997) used six soil series of Pakistan to determine the correlation of $K_s$ with selected soil physical and chemical properties. They used a stepwise procedure to select the best regression models. The regression model was derived as the following:

$$K_s (\text{mm d}^{-1}) = 1010.63 + 2269.04 (\text{GMD}) - 534.95 (D_b) - 2.76 (\text{ESP})$$

where GMD is geometric mean diameter, and ESP is exchangeable sodium percentage.

## Materials and methods

This study was conducted in Tanjung Karang Rice Irrigation Project located on a flat coastal plain in the Integrated Agricultural Development Area (IADA Barat Laut Selangor), Malaysia. It is in the district of Kuala Selangor and Sabak Bernam at latitude 3°35'N and longitude 101°05'E which covers an area of about 20,000 ha extending over the length of 40 km along the coast with a width of 5 km on average. The main irrigation and drainage canals run parallel with the coast. Sawah Sempadan Irrigation Compartment with an area of 2,300 ha was chosen as the main study area.

Soil samples were collected based on the soil series within the rice growing area. There are five dominant soil series namely Jawa (*Sulfic Tropaquept*), Sedu (*Typic Sulfaquept*), Sempadan (*Sulfic Tropaquept*), Karang (*Typic Sulfaquept*) and Telok (*Typic Sulfaquept*). Fifty plots were selected randomly within the study area. In each of the 1.2 ha plot (200 m × 60 m), two sampling points were selected, one at 25 m from the irrigation water inlet and the other at 25 m from the drainage outlet. Another plot (lot no. 2162) was selected as the main experimental plot

where a drain separates the plot into two equal areas namely, areas A and B. A total of 36 samples were collected from A to B. Since the samples were taken from three soil layers as recommended by IRRI (1987), the total number of samples from 136 sampling points was 408 as shown in Fig. 1.

Two types of brass rings were used for collecting the soil samples. One with 70 mm diameter and 40 mm long was used to determine dry bulk density (Gardner 1986). And another with 100 mm diameter and 130 mm long was used for collecting the undisturbed soil sample for determining soil saturated hydraulic conductivity ($K_s$). The first type of brass ring was sealed in plastic bag and weighed immediately. The bigger rings were brought to the laboratory in order to measure the $K_s$ using falling head method (Klute and Dirksen 1986). The pipette method was used to determine soil texture.

Organic carbon content (OC) was obtained using back titration method (Walkley and Black 1934) and converted to organic matter content (OM). The geometric mean diameter (GMD) was calculated by the following equations as given by Shirazi and Boersma (1984):

$$\text{GMD} = \exp[a] \quad (7)$$

$$a = \sum m_i \ln d_i \quad (8)$$

where $m_i$ is the mass fraction of texture class $i$, and $d_i$ is the arithmetic mean diameter of class $i$. The arithmetic means used in this study were 1.025 mm ($d_i$ for sand particle size between 2 and 0.05 mm), 0.026 mm ($d_i$ for silt particle size between 0.05 and 0.002 mm) and 0.001 mm ($d_i$ for clay particle size <0.002 mm). The $d_i$ value can be derived by means of the particle size. For example, sand particle has the range of the particle size between 2 and 0.05 mm therefore, 2.05 divided by 2 is 1.025 mm.

In this study, PTF was developed based on statistical analysis using a functional relationship of linear regression with stepwise selection technique and with the criteria that the significant level is above 0.05 will be entered and remain. The adjusted $R^2$ and root mean square error (RMSE) were considered to select the best fit model. This analysis was performed using statistical Analysis System (SAS) version 8.02.

## Results and discussions

The soils of the paddy fields were found to have three distinct layers viz. topsoil, hardpan and subsoil. The layers at each site were determined by visual method based on the presence of the layer condition such as color and root abundance. The first layer (topsoil), which is up to 10 cm from the surface, presents many coarse roots and the soil

**Fig. 1** Sampling points identified by using differential global positioning system (DGPS) in Sawah Sempadan irrigation compartment

![img-0.jpeg](None)

**{"image_type": "diagram", "description": "The image is a schematic diagram of a field layout showing a grid of sampling points and various features within the field. The diagram includes the following elements:\n\n1. **Grid Layout**: The field is divided into a grid with rows and columns, with sampling points marked as dots at the intersections.\n\n2. **Legend**: Located in the top right corner, the legend explains the symbols used in the diagram:\n   - **Sampling Point**: Represented by a dot (•).\n   - **Canal**: Represented by a solid line.\n   - **Drain**: Represented by a dashed line.\n   - **Selected Lot**: Represented by a shaded area.\n\n3. **Field Features**:\n   - A canal runs vertically along the left side of the field.\n   - A drain runs vertically along the right side of the field.\n   - The selected lot is a shaded rectangular area in the center-right of the field.\n\n4. **Scale**: A horizontal scale at the bottom indicates distances in meters (0, 400, 800).\n\n5. **Text Information**:\n   - \"Lot No 2162 (A and B)\"\n   - \"36 Samples were collected\"\n\nThe diagram visually represents the spatial arrangement of sampling points and key hydrological features (canal and drain) within the field, along with the selected lot area where samples were collected."}**

color is black. The second layer (hardpan), usually between 10 and 30 cm from the surface, presents few tiny roots, black or dark brown with yellow mottles and drier than the first layer. Another way to determine the first and second layers was by using a hard stick to push into the soil profile by a certain force, passing through the second layer. The depth at which it was harder to penetrate was considered as the beginning of the hardpan layer. No roots were found in the subsoil layer with grey, brown or dark brown colored soils. The soil thickness of the top layer and the hardpan layer ranged from 10 to 20 cm and the subsoil layer depth varied from 20 to 40 cm below the soil surface. Out of 136 sampling points, 88 points (65%) have hardpan layer at 20 cm depth and 48 points (35%) have hardpan at 10 cm depth from the soil surface. Table 1 shows the results of the soil properties from 408 samples. The $K_s$ values ranged from $5.35 \times 10^{-4}$ to $8.77 \times 10^{-2}$ m d$^{-1}$ with a standard deviation of $9.47 \times 10^{-3}$ m d$^{-1}$, and $6.73 \times 10^{-3}$ m d$^{-1}$ mean. The mean value of the three soil layer depths showed that the $K_s$ values decreased with increasing soil layer depth.

From the results, it can be concluded that the soil water moves through the topsoil layer faster than that in the hardpan layer and the subsoil layer. This is because of the presence of many root channels which promote water movement through the topsoil layer (Klute and Dirksen 1986; Reynolds 1993).

The actual volume of the brass ring was calculated to determine the dry bulk density ($D_b$) of the soil samples. The $D_b$ which were obtained in this study, varied from 0.62 to 1.91 g cm$^{-3}$ with the mean value of 1.09 g cm$^{-3}$. The standard deviation was 0.19 g cm$^{-3}$. The mean $D_b$ values of each soil layer showed that the highest was the hardpan layer with the mean value of 1.19 g cm$^{-3}$ and the lowest was the topsoil layer with the mean value of 0.94 g cm$^{-3}$. The highest mean value of the hardpan layer was due to the compaction of the soil, whereas the lowest $D_b$ value of the topsoil layer was due to loose soil and abundant roots.

As indicated by the mean value of each layer, it was found that the soil of the top layer consisted of the most sand compared to the other layers and the subsoil layer had the least sand. The percentage of the sand content decreased with increasing soil depth. The percentage of silt (Si) ranged from 19.84 to 57.25%, with the mean value of 42.67%. The standard deviation was 9.27%. The results showed that the percentage of the Si decreased with increasing soil depth when the mean values for the topsoil, hardpan and subsoil were found to be 47.75, 44.25 and 36.00%, respectively. The percentage of clay (C) varied from 32.22 to 76.80%, with the mean value of 50.97%. The standard deviation was 10.43%. The mean value of the clay content for the three soil layers increased with increasing soil depth as 43.88, 50.21 and 58.81% for topsoil, hardpan and subsoil layers, respectively.

**Table 1** Soil properties of three soil layer depths at 136 sampling points with 408 samples

|  Soil properties |  | Min | Max | Mean | Variance  |
| --- | --- | --- | --- | --- | --- |
|  *K*_{s} (m d^{-1}) | L_{T} | 1.78 × 10^{-3} | 8.77 × 10^{-2} | 1.43 × 10^{-2} | 2.00 × 10^{-7}  |
|   |  L_{H} | 7.20 × 10^{-3} | 5.35 × 10^{-4} | 3.08 × 10^{-3} | 4.11 × 10^{-9}  |
|   |  L_{S} | 1.68 × 10^{-2} | 6.03 × 10^{-4} | 2.80 × 10^{-3} | 7.53 × 10^{-9}  |
|  *D*_{b} (g cm^{-3}) | L_{T} | 0.62 | 1.37 | 0.94 | 0.02  |
|   |  L_{H} | 0.79 | 1.91 | 1.19 | 0.03  |
|   |  L_{S} | 0.66 | 1.57 | 1.13 | 0.03  |
|  S (%) | L_{T} | 0.10 | 25.49 | 8.20 | 73.28  |
|   |  L_{H} | 0.32 | 15.40 | 5.48 | 33.04  |
|   |  L_{S} | 0.08 | 13.02 | 4.96 | 25.77  |
|  Si (%) | L_{T} | 23.55 | 57.25 | 47.75 | 60.03  |
|   |  L_{H} | 19.84 | 57.21 | 44.25 | 95.62  |
|   |  L_{S} | 24.45 | 50.98 | 36.00 | 29.83  |
|  C (%) | L_{T} | 32.22 | 68.63 | 43.88 | 83.99  |
|   |  L_{H} | 33.08 | 76.80 | 50.21 | 89.22  |
|   |  L_{S} | 44.72 | 75.43 | 58.81 | 41.69  |
|  OM (%) | L_{T} | 1.43 | 29.35 | 12.07 | 12.34  |
|   |  L_{H} | 0.26 | 18.90 | 8.55 | 9.34  |
|   |  L_{S} | 0.07 | 14.22 | 5.12 | 4.48  |
|  GMD (mm) | L_{T} | 0.003 | 0.023 | 0.010 | 0.000040  |
|   |  L_{H} | 0.002 | 0.015 | 0.007 | 0.000006  |
|   |  L_{S} | 0.002 | 0.008 | 0.005 | 0.000003  |

*L*$_{T}$ topsoil layer; *L*$_{H}$ hardpan layer; *L*$_{S}$ subsoil layer

The soil texture was classified based on the percentage of the sand, silt and clay contents using the soil textural triangle. Four textural classes out of 12 possible classes of the textural triangle classification were obtained. They were clay, clay loam, silty clay and silty clay loam. From 408 total number, 43.14% were clay (176 samples), 6.62% were clay loam (27 samples), 42.16% were silty clay (172 samples) and 8.09% were silty clay loam (33 samples). The distribution of soil textures on the standard textural triangle is shown in Fig. 2. The results indicate that the paddy soils contain high clay content.

Figure 3 shows the soil saturated hydraulic conductivity values which ranged from 1.68 × 10$^{-2}$ to 6.03 × 10$^{-4}$, 1.98 × 10$^{-2}$ to 5.35 × 10$^{-4}$, 2.20 × 10$^{-2}$ to 1.07 × 10$^{-3}$ and 8.77 × 10$^{-2}$ to 3.88 × 10$^{-3}$ m d$^{-1}$ for clay, silty clay, silty clay loam and clay loam, respectively.

The percentage of organic matter (OM) varied from 0.07 to 29.35%. The mean value and the standard deviation were 8.57 and 4.79%, respectively. The mean values at each layer showed that the percentage of the OM content decreased with increasing soil depth when the mean values were found to be 12.07, 8.55 and 5.12%, respectively. The highest OM content of the topsoil layer was due to the presence of root and some other organics (such as fibric, hemic and sapric).

The results from the calculation of the GMD for this study showed that it varied from 0.002 to 0.023 mm and

![img-1.jpeg](None)

**{"image_type": "plot", "description": "Dashed line plot showing the classification of soil textures based on the percentages of clay (< 2 µm), silt (2 - 50 µm), and sand (50 - 2000 µm). The plot is a ternary diagram with the following axes:\n- X-axis: % sand (50 - 2000 µm)\n- Y-axis (left): % clay (< 2 µm)\n- Y-axis (right): % silt (2 - 50 µm)\n\nKey soil texture classes are labeled within the plot, including:\n- Clay (top vertex, 100% clay)\n- Silt (bottom left vertex, 100% silt)\n- Sand (bottom right vertex, 100% sand)\n- Sandy clay (near clay vertex, high clay, low silt)\n- Silty clay (near clay vertex, high clay, high silt)\n- Sandy clay loam (mid-clay, low silt, high sand)\n- Clay loam (mid-clay, mid-silt, mid-sand)\n- Silty clay loam (mid-clay, high silt, low sand)\n- Sandy loam (low clay, low silt, high sand)\n- Loam (mid-clay, mid-silt, mid-sand)\n- Silt loam (low clay, high silt, low sand)\n- Sandy (near sand vertex, 100% sand)\n- Loamy sand (low clay, low silt, very high sand)\n\nApproximate key data points (coordinates in % clay, % silt, % sand):\n1. Clay: (100, 0, 0)\n2. Silty clay: (60, 40, 0)\n3. Sandy clay: (40, 0, 60)\n4. Clay loam: (35, 35, 30)\n5. Sandy clay loam: (25, 10, 65)\n6. Loam: (20, 40, 40)\n7. Sandy loam: (15, 15, 70)\n8. Silt loam: (10, 70, 20)\n9. Sand: (0, 0, 100)\n10. Loamy sand: (5, 5, 90)"}**

**Fig. 2** The distribution of soil texture in Sawah Sempadan rice growing area

the mean value was 0.007 mm, with the standard deviation and the variance of 0.005 and 0.000020 mm, respectively. The mean GMD values of each soil layer indicated that the highest GMD was the topsoil layer and the lowest was the subsoil. It showed that the GMD decreased with increasing soil depth, i.e. 0.010 (10 μm), 0.007 (7 μm) and 0.005 (5 μm) for topsoil, hardpan and subsoil, respectively.

![img-2.jpeg](None)

**{"image_type": "plot", "description": "The plot displays the relationship between clay content (x-axis, in percentage) and saturated hydraulic conductivity (Ksat, y-axis, in cm/s) for different soil textures. The x-axis ranges from 0% to 100% clay content, while the y-axis ranges from 0 to 0.10 cm/s. Key data points and trends:\n\n- At 0% clay (sand-dominated soil), Ksat is approximately 0.09 cm/s.\n- At ~10% clay (sandy clay), Ksat drops to ~0.03 cm/s.\n- At ~20% clay (silty clay), Ksat is ~0.015 cm/s.\n- At ~30% clay (clay loam), Ksat is ~0.005 cm/s.\n- At ~40% clay (clay), Ksat is ~0.001 cm/s.\n\nThe trend shows an exponential decrease in Ksat as clay content increases. The soil texture classifications (e.g., 'Clay Loam', 'Silty Clay Loam') are labeled near their respective data points."}**

Fig. 3 Soil saturated hydraulic conductivity ranks on soil textures for lowland paddy soils

### \(K_{s}\) model analysis

Six soil parameters were used as variable inputs into the SAS. They were dry bulk density  \( (D_{\mathrm{b}}) \) , organic matter (OM), silt (Si), clay (C), sand (S) and geometric mean diameter (GMD). Due to extreme  \( K_{s} \)  data were found where there were four data points that jumped out of range therefore, those extreme data points were excluded from the analysis and total n for the analysis was 404.

The first step of the statistical analysis procedures, a correlation procedure was used. Then, the stepwise regression method was used to perform the regression analysis. The stepwise model fit technique with adjusted  \( R^{2} \)  was carried out.

#### Before transformation

Correlation test showed that soil  \( K_{s} \)  has highly significant (at significant level,  \( \alpha = 0.01 \) ) to soil  \( D_{b} \) , OM, C, Si and GMD (Table 2). Soil  \( D_{b} \)  and clay showed that there are negatively correlated to soil  \( K_{s} \) . This indicates that high  \( D_{b} \)  and C will decrease  \( K_{s} \) . However, it showed that there is no significant to S. On the other hand, S content has no affect

on the  \( K_{s} \)  for paddy soil where it usually contains high C and low S contents.

Stepwise regression procedure method was then used to select the best model related to the input parameters with the model fit technique, where this procedure has taken into account the level of correlation, effect of multicollinearity and the ease of determination. This procedure also differs from alternative procedures in that it does not select a single model. It produces the best single-variable model, the best two-variable model and the best three-variable model, etc. The regression results showed that the independent variables were significant at P < 0.0001 with  \( R^{2} = 0.43 \)  (n = 404) and RMSE = 0.004270. The result showed that only  \( D_{b} \) , OM and C as important variables (as shown in Eq. 9).

\[
\begin{array}{l} K _ {\mathrm{s}} \left(\mathrm{m} \mathrm{d} ^ {- 1}\right) = 2. 3 8 \times 1 0 ^ {- 2} - 1. 1 9 5 \times 1 0 ^ {- 2} \left(D _ {\mathrm{b}}\right) + 3. 0 7 \\ \times 1 0 ^ {- 4} (\mathrm{OM}) - 1. 4 6 \times 1 0 ^ {- 4} (\mathrm{C}) \tag {9} \\ \end{array}
\]

The predicted and observed  \( K_{s} \)  were plotted on 1:1 line and fitted the data trendline on a linear basis (Fig. 4). It showed

![img-3.jpeg](None)

**{"image_type": "plot", "description": "The image is a scatter plot comparing predicted versus observed values of K_in (m d⁻¹). The x-axis represents the observed K_in values, ranging from approximately -0.010 to 0.025 m d⁻¹, while the y-axis represents the predicted K_in values, ranging from approximately -0.010 to 0.025 m d⁻¹. The data points are scattered around a diagonal line (y = x), indicating a linear relationship between predicted and observed values. The plot includes a legend with two types of markers: filled circles (S₁) and open circles (S₂). The coefficient of determination (R²) for the linear fit is 0.418, suggesting a moderate correlation between the predicted and observed values. Key observations include a cluster of data points near the origin and a spread of points along the diagonal line, with some deviation, particularly at higher values."}**

Fig. 4 Observed  \( K_{s} \)  versus predicted  \( K_{s} \)  plotted on 1:1 line for a model that produced before transformation

Table 2 Correlations of selected soil properties and \( {K}_{\mathrm{s}}\left( {n = {404}}\right) \)

|   | \(D_{\text{b}}\) | OM | C | Si | S | GMD | \(K_{\text{s}}\)  |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  \(D_{\text{b}}\) | 1 | -0.34** | 0.14** | -0.19** | 0.04ns§ | -0.12* | -0.52**  |
|  OM | -0.34** | 1 | -0.28** | 0.36** | -0.06ns | 0.13* | 0.47**  |
|  C | 0.14** | -0.28** | 1 | -0.77** | -0.47** | -0.77** | -0.40**  |
|  Si | -0.19** | 0.36** | -0.77** | 1 | -0.20** | 0.25** | 0.41**  |
|  S | 0.04ns | -0.06ns | -0.47** | -0.20** | 1 | 0.85** | 0.03ns  |
|  GMD | -0.12* | 0.13* | -0.77** | 0.25** | 0.85** | 1 | 0.27**  |
|  \(K_{\text{s}}\) | -0.52** | 0.47** | -0.40** | 0.41** | 0.03ns | 0.27** | 1  |

that the data distributed above 1:1 line more than that under it. This indicates that the model most likely produced over estimation. A linear trendline showed that it fitted to highly significant level at  \( R^{2}=0.418 \) . However, the prediction showed that many negative values were produced by using this model.

Since, the  \( R^{2} \)  is low and it produced negative values, the data transformation techniques were needed to transform the data into several mathematical forms, where data transformation procedure changes the actual values of the variables or create new variables. It created a new variable that contains the natural logarithm of an existing variable and it does not change the data value but restrict the number of cases used in the analysis (Marija 1999).

### Transformation technique

In this study, several mathematical forms were tried out (i.e. logarithm, exponential, square root, power, etc.) and the best model was in the forms of natural logarithm (ln). The results of the correlation showed that soil  \( K_{s} \)  has highly significant (at  \( \alpha = 0.01 \)  level) to  \( \ln D_{b} \) ,  \( \ln OM \) ,  \( \ln C \) ,  \( \ln Si \)  and  \( \ln GMD \)  (Table 3).  \( \ln D_{b} \)  and  \( \ln C \)  showed that there are negatively correlated to soil  \( K_{s} \)  and there is no significant to  \( \ln S \) . After transformation,  \( \ln D_{b} \)  and  \( \ln GMD \)  had a correlation coefficient higher than that in non-transformation while, some other still be the same and some decreased. In the regression process, however, both non-transformation and transformation were included into the stepwise to allow it to select the best fit model.

The stepwise regression results showed that the estimation model was significant at P < 0.0001 with  \( R^{2} = 0.46 \)  (n = 404) and RMSE = 0.004267. The result showed that  \( D_{b} \) , OM, C, ln OM, ln  \( D_{b} \)  and ln GMD were fitted into the model of ln  \( K_{s} \) , but S and ln S were excluded as can be shown in Eq. 10. The result of transformation showed that the  \( R^{2} \)  increased and the RMSE was slightly decreased. This supports that the transformation technique was able to fit better model of estimation.

![img-4.jpeg](None)

**{"image_type": "plot", "description": "The plot is a scatter plot comparing predicted hydraulic conductivity (K_v, in m d⁻¹) on the Y-axis to observed hydraulic conductivity (K_v, in m d⁻¹) on the X-axis. The data points are represented by open circles scattered around a 1:1 line (solid line), indicating perfect agreement between predicted and observed values. A linear regression line (dashed line) is also shown, with an R² value of 0.464, indicating a moderate correlation between the predicted and observed values. The trend suggests that the model tends to underpredict higher observed values, as the regression line lies below the 1:1 line for higher K_v values. Key observations include:\n- Most data points cluster near the lower end of the observed K_v range (0 to 0.010 m d⁻¹).\n- A few outliers exist at higher observed K_v values (up to 0.025 m d⁻¹).\n- The spread of data points increases with higher observed K_v values, indicating greater variability in predictions at higher conductivities."}**

Fig. 5 Observed  \( K_{s} \)  versus predicted  \( K_{s} \)  plotted on 1:1 line for a model that produced after transformation

\[
\begin{array}{l} \ln K _ {\mathrm{s}} (\mathrm{m} \mathrm{d} ^ {- 1}) = - 2. 3 6 8 + 3. 8 4 6 (D _ {\mathrm{b}}) + 0. 0 9 1 (\mathrm{OM}) \\ - 6. 2 0 3 (\ln D _ {\mathrm{b}}) - 0. 3 4 3 (\ln \mathrm{OM}) \\ - 2. 3 3 4 (\ln \mathrm{C}) - 0. 4 1 1 (\ln \mathrm{GMD}) \tag {10} \\ \end{array}
\]

Figure 5 shows the variability of the observed and predicted \( K_{\mathrm{s}} \) on 1:1 line for a model that produced after transformation. The best model predictor should runs on the line and if the data value runs above or below the line means the predictor is over or under estimation. A linear trendline showed that it fitted to highly significant level at \( R^2 = 0.464 \) where there was an increase as compared to non-transformation. The figure shows that in the larger observed \( K_{\mathrm{s}} \) values of higher than \( 1.50 \times 10^{-2} \, \mathrm{mm} \, \mathrm{d}^{-1} \), the predicted \( K_{\mathrm{s}} \) is scattered wider. This is due to high variability of soil condition in the plough layer with high root density, higher porosity, lower \( D_{\mathrm{b}} \), lower C content and higher OM content.

### Model comparison

Comparison of the derived model and some recommended model in the literature review such as Jabro's and Vereecken et al.'s models were done. This is due to the use of

Table 3 Correlations of selected soil properties and \( {K}_{\mathrm{s}} \) after transformation into natural logarithm

|   | \( \ln D_b \) | \( \ln OM \) | \( \ln C \) | \( \ln Si \) | \( \ln S \) | \( \ln GMD \) | \( K_s \)  |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  \( \ln D_b \) | 1 | -0.29** | 0.17** | -0.18** | 0.06ns\( ^§ \) | -0.08ns | -0.54**  |
|  \( \ln OM \) | -0.29** | 1 | -0.31** | 0.31** | 0.10 ns | 0.21** | 0.36**  |
|  \( \ln C \) | 0.17** | -0.31** | 1 | -0.75** | -0.55** | -0.91** | -0.40**  |
|  \( \ln Si \) | -0.18** | 0.31** | -0.75** | 1 | 0.02ns | 0.45** | 0.40**  |
|  \( \ln S \) | 0.06ns | 0.10ns | -0.55** | 0.02ns | 1 | 0.78** | 0.06ns  |
|  \( \ln GMD \) | -0.08ns | 0.21** | -0.91** | 0.45** | 0.78** | 1 | 0.28**  |
|  \( K_s \) | -0.54** | 0.36** | -0.40** | 0.40** | 0.06ns | 0.28** | 1  |

**Table 4** Comparison of the models

|  Name | Model $R^2$ | Predicted $K_s$ (m d$^{-1}$) |   |   | Significant level on 1:1 line (predicted versus measured)  |
| --- | --- | --- | --- | --- | --- |
|   |   |  Min | Max | Mean  |   |
|  Measured $K_s$ | – | $5.35 \times 10^{-4}$ | $8.77 \times 10^{-2}$ | $6.73 \times 10^{-3}$ | 1  |
|  (a) Derived model | 0.46 | $1.26 \times 10^{-3}$ | $2.33 \times 10^{-2}$ | $4.89 \times 10^{-3}$ | 0.464 ($n = 404$)  |
|  (b) Jabro 1992 | 0.68 | $9.14 \times 10^{-4}$ | 740.13 | 27.87 | 0.172 ($n = 404$)  |
|  (c) Vereecken et al. (1990) | na^{§} | $1.47 \times 10^{-3}$ | 1328.96 | 25.58 | 0.03ns^{§§} ($n = 404$)  |

$^{§}$ *na* Not available

$^{§§}$ *ns* Not significant

When: (a) Derived model: $\ln K_s = -2.368 + 3.846(D_b) + 0.091(OM) - 6.203(\ln D_b) - 0.343(\ln OM) - 2.334(\ln C) - 0.411(\ln GMD)$ (in m d$^{-1}$)

(b) Jabro 1992: $\log K_s = 9.56 - 0.81 (\log S_i) - 1.09 (\log C) - 4.64 (D_b)$ (in cm h$^{-1}$)

(c) Vereecken et al. (1990): $K_s = \exp[20.62 - 0.96 (\ln C) - 0.66 (\ln S) - 0.46 (\ln OM) - 8.43 (D_b)]$ (in cm d$^{-1}$)

almost the same variable inputs and the inputs are available in this study. Therefore, this study tried to compare the derived model to other available model where normally produced based on upper land soils.

The comparison result found the different between the derived model from this study and the measured $K_s$ (Table 4). The table showed that the derived model is the most acceptable model for predicting the $K_s$ for very clayey soil (such as lowland paddy soil) where the significant level on 1:1 line was higher, whilst other two models produced very high mean value as compared to the measured $K_s$.

## Summary and conclusion

The results of the study showed that the spatial variability of the saturated hydraulic conductivity in the paddy field varied highly. The saturated hydraulic conductivity varied from $5.35 \times 10^{-4}$ to $8.77 \times 10^{-2}$ m d$^{-1}$. The hardpan layer is the compacted soil layer whose function is to prevent water losses through the root zone and/or the desired depth. The results of the soil bulk density showed clearly the compaction of the soil. Where the hardpan or the compacted soil layer has the highest values compared to the others. This study showed that the best regression model for estimating the soil saturated hydraulic conductivity ($K_s$) needs four input parameters based on available soil properties. They are dry bulk density ($D_b$), organic matter (OM), clay (C) and geometric mean diameter (GMD). The best model of this study showed $R^2$ of 0.46 ($n = 404$ and $P < 0.0001$). The comparison result found that they are difference and the most acceptable model for predicting the $K_s$ for very clayey soil is the derived model from this study when it showed the highest significant level on 1:1 line. Therefore, the derived model can serve as a PTF for $K_s$ determination for lowland clayey paddy soil. This derived model is most useful for determining $K_s$

values for the hardpan layer where it is critical for irrigation, drainage and water management of the paddy field.

**Acknowledgments** The financial support from UPM-MACRES Precision Farming Engineering Research Grant is gratefully acknowledged. The authors highly appreciate all technical supports from Soil and Water Engineering Laboratory assistants. Special thanks to Mr. Ezrin Mohd Husin and all staff at SFTL, ITMA, UPM for their support and cooperation.

## References

Ali Hassan Shah, Lone MI, Stephen H Anderson (1997) Regression model to predict hydraulic conductivity from simple soil physical and chemical properties. 7th ICID international drainage workshop 'Drainage for the 21st Century', MalaysiaBouma J (1989) Using soil survey data for quantitative land evaluation. Adv Soil Sci 9:177–213Bouma J (1992) Effect of soil structure, tillage and aggregation upon soil hydraulic properties. In: Wagenet RJ et al (eds) Interacting processes in soil science. Lewis, Boca Raton, pp 1–36Bouma J, Van Lanen HAJ (1987) Transfer functions and threshold values: from soil characteristics to land qualities. In: Quantified land evaluation. Proc. ISSS/SSSA Workshop, Washington. ITC Publication, EnschedeBurdine NT (1953) Relative permeability calculations from pore size distribution data. Pet Trans Am Inst Min Eng 198:71–77Campbell GS (1974) A simple method for determining unsaturated conductivity from moisture retention data. Soil Sci Soc Am J 117:311–314Campbell GS (1985) Soil physics with basic development in soil science, 14. Elsevier, AmsterdamCosby BJ, Homberger GM, Clapp RB, Ginn TR (1984) A statistical exploration of the relationships of soil moisture characteristics to the physical properties of soils. Water Resour Res 20:682–690Gardner WH (1986) Water content. In: Klute A (ed) Methods of soil analysis, Part 1. Physical and mineralogical methods. Agronomy No. 9, 2nd edn. American Society of Agronomy, Soil Science Society of America, Madison, p 493–544Gupta RK, Rudra RP, Dickinson WT, Patni NK, Wall GW (1993) Comparison of saturated hydraulic conductivity measured by various field methods. Trans ASAE 36(1):51–55IRRI (1987) Physical measurements in flooded rice soils: the Japanese methodologies. International Rice Research Institute, Los Banos

Jabro JD (1992) Estimation of saturated hydraulic conductivity of soils from particle size distribution and bulk density data. Trans ASAE 35:557–560
Klute A, Dirksen C (1986) Hydraulic conductivity and diffusivity: laboratory methods. In: Klute A (ed) Methods of soil analysis, Part 1. Madison, 687–734; Am Soc Agron
Marija JN (1999) SPSS 9.0 guide to data analysis. Prentice-Hall, New Jersey 577
Rawls WJ, Brakensiek DL, Saxton KE (1982) Estimation of soil water properties. Trans ASAE 25:1316–1320
Reynolds WD (1993) Saturated hydraulic conductivity: field measurement. In: Carter MR (ed) Soil sampling and methods of analysis. Lewis, Boca Raton, pp 599–605
Saxton KE, Rawls WJ, Romberger JS, Papendick RI (1986) Estimating generalized soil water characteristics from texture. Soil Sci Soc Am J 50:1031–1036
Shirazi MA, Boersma L (1984) A unifying quantitative analysis of soil texture. Soil Sci Soc Am J 48:142–147
Tietje O, Hennings V (1993) Bewertung von Pedotransferfunktionen zur Schätzung der Wasserspammungskurve. Z Pflanzenernahr Bondenkd 156:447–455
Tietje O, Tapkenhinrichs M (1992) Evaluation of pedo-transfer functions. Soil Sci Soc Am J 57:1081–1095
Verecken H, Maes J, Feyen J (1990) Estimating unsaturated hydraulic conductivity from easily measured soil properties. Soil Sci Soc Am J 149:1–12
Wagenet RJ, Bouma J, Grossman RB (1991) Minimum data sets for use of soil survey information in soil interpretive models. In: Mausbach MJ, Wilding LP (eds) Spatial variabilities of soils and land forms. SSSA special publication no. 28, Madison
Walkley A, Black IA (1934) An examination of the degtjareff method for determining soil organic matter, and a proposed modification of the chromic acid titration method. Soil Sci 34:29–38
Warrick AW, Nielsen DR (1980) Spatial variability of soil physical properties in the field. In: Hillel D (ed) Application of soil physics. Academic Press, New York, pp 319–344