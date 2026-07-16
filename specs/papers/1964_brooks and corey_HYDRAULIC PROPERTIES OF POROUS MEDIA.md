# HYDRAULIC PROPERTIES OF POROUS MEDIA

by

R. H. Brooks and A. T. Corey

March 1964

![img-0.jpeg](None)

**{"image_type": "image", "description": "NO_DATA"}**

HYDROLOGY PAPERS

COLORADO STATE UNIVERSITY

Fort Collins, Colorado

Several departments at Colorado State University have substantial research and graduate programs oriented to hydrology. These Hydrology Papers are intended to communicate in a fast way the current results of this research to the specialists interested in these activities. The papers will supply most of the background research data and results. Shorter versions will usually be published in the appropriate scientific and professional journals.

This research was a cooperative effort between the Agricultural Research Service, Soil and Water Conservation Research Division, and the Agricultural Engineering Department, Colorado State University. Funding for part of this research through the Agricultural Engineering Department resulted from a National Science Foundation Grant.

# EDITORIAL BOARD

Dr. Arthur T. Corey, Professor, Agricultural Engineering Department
Dr. Robert E. Dils, Professor, College of Forestry and Range Management
Dr. Vujica M. Yevdjevich, Professor, Civil Engineering Department

# HYDRAULIC PROPERTIES OF POROUS MEDIA

by

R. H. Brooks

and

A. T. Corey

HYDROLOGY PAPERS

COLORADO STATE UNIVERSITY

FORT COLLINS, COLORADO

March 1964

No. 3

# ABSTRACT

Following the Burdine approach, a theory is presented that develops the functional relationships among saturation, pressure difference, and the permeabilities of air and liquid in terms of hydraulic properties of partially saturated porous media. Procedures for determining these hydraulic properties from capillary pressure - desaturation curves are described. Air and liquid permeabilities as a function of saturation and capillary pressure are predicted from the experimentally determined hydraulic properties.

The theory also describes the requirements for similitude between any two flow systems in porous media occupied by two immiscible fluid phases when the nonwetting phase is static and the flow of the wetting phase is described by Darcy's law. The requirements for similitude are expressed in terms of the hydraulic properties of porous media.

# TABLE OF CONTENTS

|   | Page  |
| --- | --- |
|  Abstract | ii  |
|  Notations and Definitions | v  |
|  Introduction | 1  |
|  Background | 2  |
|  Darcy's equation | 2  |
|  Saturation defined | 2  |
|  Capillary pressure defined | 2  |
|  Relative permeability defined | 3  |
|  Burdine's equations | 3  |
|  Effective saturation defined | 3  |
|  Corey's approximations for relative permeability | 3  |
|  Theory | 4  |
|  Effective saturation as a function of capillary pressure | 4  |
|  Pore-size distribution index, λ | 4  |
|  Bubbling pressure P_{b} defined | 4  |
|  Relative permeability as a function of λ | 4  |
|  Experimental Techniques | 6  |
|  Saturation as a function of capillary pressure | 6  |
|  Air permeability as a function of saturation and capillary pressure | 6  |
|  Porous media used in experiments | 9  |
|  Comparison of Experimental Results with Theory | 11  |
|  Determination of P_{b} and λ | 11  |
|  Air permeability as a function of capillary pressure | 11  |
|  Liquid permeability as a function of capillary pressure | 11  |
|  Permeability as a function of saturation | 15  |
|  Similitude Requirements | 16  |
|  Richard's equation | 16  |
|  Richard's equation in terms of scaled variables | 16  |
|  Similitude criteria | 16  |
|  Model requirements | 17  |
|  Significance of Hysteresis | 18  |
|  References | 20  |
|  Appendix I. Theoretical basis for the Burdine equations | 21  |
|  Appendix II. Method of determining residual saturation | 24  |
|  Appendix III. Experimental data | 25  |

# LIST OF FIGURES AND TABLES

Figures

Page

1. Capillary pressure head as a function of saturation for porous materials
of varying pore-size distributions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5

2. Effective saturation as a function of capillary pressure head for porous
materials of varying pore-size distributions . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 5

3. Diagram of flow system and pressure control system for air permeability cell . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7

4. Construction details of air permeability cell . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8

5. Theoretical curves and experimental data of capillary pressure head
as a function of nonwetting phase relative permeability . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12

6. Predicted wetting phase relative permeability as a function of capillary
pressure head compared with experimental data. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12

7. Theoretical curves and experimental data of nonwetting phase relative
permeability as a function of saturation for unconsolidated materials . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 13

8. Theoretical curves and experimental data for relative permeabilities of the
nonwetting (nw) and wetting (w) phases as a function of saturation for
two consolidated sandstones . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 14

9. Wetting phase relative permeability as a function of capillary pressure on
the imbibition and drainage cycles . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 19

Tables

1. (Appendix III) Data from Air Permeability Cell for Unconsolidated Samples . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25

2. (Appendix III) Data from Liquid Permeameter Columns for Unconsolidated
Samples . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26

3. (Appendix III) Data from Liquid Permeameter for Consolidated Rock Cores . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27

4. (Appendix III) Data from Air Permeameter for Consolidated Rock Cores . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27

e - A subscript meaning "effective".

φ - Porosity--the volume of pore space expressed as a fraction of bulk volume of the porous medium--dimensions: none.

φe - Effective porosity--φ(1 - Sr)--dimensions: none.

h - The elevation of a point in a porous medium above a datum--dimensions: L.

k - Shape factor--a dimensionless parameter which depends on the geometry of pore space but not on size--dimensions: none.

K - The maximum permeability to a particular fluid phase when only one phase occupies the media--dimensions: L². It is sometimes called "intrinsic permeability". With porous media that are stable in the presence of the fluids occupying them, K is a function of the geometry of the media. It is not a function of the viscosity or specific weight of the fluid.

Ke - Effective permeability--the permeability of a porous medium to a particular fluid phase when the medium is occupied by more than one fluid phase--dimensions: L².

Kr - Ke/K

Kx - The component of K in the x-direction--dimensions: L².

L - Length--distance between two points in a porous medium--dimensions: L.

Le - Effective length--distance traversed by differential fluid elements in moving between two points in a porous medium--dimensions: L.

Lx - Length--the distance between two points in a porous medium in the x-direction--dimensions: L.

R - Hydraulic radius--for tubes of uniform cross section, the cross-sectional area divided by the wetted perimeter. For tubes of non-uniform cross-section, the average hydraulic radius is assumed to be the volume of the tube divided by its internal surface area--dimensions: L.

nw - A subscript meaning "non-wetting phase". A non-wetting fluid phase is a fluid that does not directly contact the solid surfaces in the presence of another fluid which wets the surface. In an air-water system, for example, water is usually the wetting and air the non-wetting phase.

P - Pressure--usually a measure of the compressive force of fluid at a point and in the case of a static fluid it usually is the average intensity of the surface force acting on the fluid element as a point. In the case of a wetting fluid in porous media where adsorptive forces act, the meaning is expanded to the quantity which is measured by a tensiometer at atmospheric pressure--dimensions: FL⁻².

P* - Piezometric pressure--the quantity P + γh. --dimensions: FL⁻².

Pb - Bubbling pressure--approximately the minimum Pc on the drainage cycle at which a continuous non-wetting phase exists in a porous medium. For a more rigorous definition

see section on experimental methods--dimensions: FL⁻².

Pc - Capillary pressure--the pressure difference (Pnw - Pw)--dimensions: FL⁻².

q - Volume flux--the maximum component of the volume rate of discharge of a flowing fluid per unit area of the bulk medium. In an isotropic medium the area referred to is a cross-section perpendicular to the potential gradient producing the flow--dimensions: LT⁻¹.

qx - Component of q in the x-direction--dimensions: LT⁻¹.

r - A radial distance--dimension: L--also a subscript meaning "ratio" or "residual".

S - Saturation--the ratio of the volume of wetting fluid to the volume of interconnected pore space in a bulk element of the medium--dimensions: none.

Se - Effective saturation--given by (S - Sr)/(1 - Sr)--dimensions: none.

Sr - The residual saturation--a saturation at which the theory assumes that Kew is zero and Kenw is a maximum. The method of determining Sr is given in Appendix II.

T - Tortuosity--the ratio (Le/L)²--dimensions: none.

u - A component of fluid velocity in the direction x--dimensions: LT⁻¹.

ū - Mean value of u --the average value of u over a cross-section of fluid perpendicular to x--dimensions: LT⁻¹.

V - The total velocity vector--the vector sum of u, v, and w the components of fluid velocity in the x, y, and z coordinate directions respectively--dimensions: LT⁻¹.

v - Volume--dimensions: L³.

w - A subscript meaning wetting phase. A fluid that wets the solid surfaces of the media. In an air-water system, water is the wetting phase.

γ - Specific weight of fluid--weight per unit volume of fluid--dimensions: FL⁻³.

Δ - Denotes a difference.

∇ - Denotes the gradient operator.

∇. - Denotes the gradient operator with respect to scaled coordinate distances.

div - Denotes the divergence operator.

Div. - Denotes the divergence operator with respect to scaled coordinate distances.

ε - The exponent in the equation: Krw = Se^ε.

η - The exponent in the equation: Krw = (Pb/Pc)^η.

λ - The exponent in the equation: Se = (Pb/Pc)^λ, called the pore-size distribution index.

μ - Dynamic viscosity--dimensions: FL²T⁻¹.

μ² - Square microns--a unit of permeability--dimensions: L².

σ - Interfacial tension--dimensions: FL⁻¹.

# HYDRAULIC PROPERTIES OF POROUS MEDIA 1/

R. H. Brooks and A. T. Corey 2/

# INTRODUCTION

Irrigation and drainage engineers are faced with the problem of getting water into or out of soil. In either case, the flow phenomenon involved is flow through partially saturated porous media. When water enters a soil, air must be replaced; and when water is removed, air must enter. The flow, therefore, involves two largely immiscible fluids: air and water.

Most of the literature describing flow of two immiscible fluids is found in journals concerned with petroleum technology or with soil physics. Because the language in some of the literature is unfamiliar and because much of it is qualitative in nature, drainage and irrigation engineers have not made use of the available information concerning two-phase flow. In the design of drainage and irrigation systems, engineers (with rare exceptions) have made the simplifying assumptions that soil is either completely saturated with water or it is completely unsaturated and that resistance to flow of air (associated with the movement of water into and out of soil) is negligible. Such

assumptions are in most cases far from realistic. In real cases, there exist functional relationships among the saturation, the pressure difference between air and water, and the permeabilities of air and water. The purpose of this paper is to describe these functional relationships and the properties of porous media which affect them. The experimental evidence presented indicates that these functional relationships (for isotropic media) can be described in terms of two pertinent soil parameters. One of these parameters is called the "bubbling pressure" which is related to the maximum pore-size forming a continuous network of flow channels within the medium. The other parameter is called the "pore-size distribution index" which evaluates the distribution of sizes of the flow channels within a particular porous medium.

Theory is presented which develops the functional relationships among saturation, the pressure difference, and the permeabilities of air and water in terms of the bubbling pressure and the distribution index. The theory also describes the requirements for similitude between any two flow systems in porous media occupied by two immiscible fluid phases when the nonwetting phase is static and the flow of the wetting phase is described by Darcy's law. The requirements for similitude are also expressed in terms of the bubbling pressure and the pore-size distribution index.

Methods of measuring the bubbling pressure and the pore-size distribution index are presented, and the problem of selecting suitable porous media for use in laboratory models is discussed.

1/ Contribution from the Soil and Water Conservation Research Division, Agricultural Research Service, USDA, and the Agricultural Engineering Dept., Colorado State University.

2/ Research Agricultural Engineer, USDA, and Professor, Agricultural Engineering, Colorado State University, Fort Collins, Colorado, respectively.

In the two-fluid system discussed herein, the fluids are assumed to be immiscible. They are referred to as the nonwetting and wetting phases. Even though the discussion is confined to a gas-liquid system, the theory applies to any two-fluid system in which the fluids are immiscible.

A convenient way to determine which phase is the wetting phase is to consider the two fluids in a capillary tube. At the interface of the two fluids, the curvature is always concave toward the wetting fluid. For example, in a mercury-air system, the air is the wetting phase; whereas in an air-water system, the air is the nonwetting phase. In the experiments conducted for this paper the two fluids were air and oil.

It is assumed that Darcy's equation applies to flow of both the gas and liquid phases occupying a porous medium. For this assumption to be valid, both phases must form continuous networks within the medium and any isolated bubbles of gas must be regarded as part of the porous matrix. Darcy's equation is written as

$$q _ { x } = - \frac { K _ { x } } { \mu } \left[ \frac { \Delta P } { L _ { x } } + \frac { \gamma \Delta h } { L _ { x } } \right] \tag { 1 }$$

in which $q_x$ is the component of volume flux in the x-direction, $\gamma$ is the specific weight of the fluid, $\mu$ is the viscosity, $\Delta h$ and $\Delta P$ are the difference in elevation and pressure respectively over the distance $L_x$ in the x-direction, and $K_x$ is the permeability in the x-direction. The volume flux $q_x$ is the volume of fluid (liquid or gas) passing a unit cross-sectional area of the porous medium perpendicular to the x-direction in a unit of time. The permeability $K_x$ has dimensions of length squared and it is sometimes called "intrinsic permeability". For a stable, homogeneous, isotropic medium with pores containing only one fluid, permeability is a constant and is considered a property of the medium.

When two immiscible fluids occupy the pores of a porous matrix, the permeability to one fluid phase is called "effective permeability," $K_e$. For a homogeneous isotropic medium containing a fluid of constant and uniform density,

$$q = - \frac { K _ { e } } { \mu } \nabla P ^ { * } \tag { 2 }$$

where $q$ is the largest component of flux (which is in the direction of $\nabla P^*$ and $P^*$ is the quantity $P + \gamma h$. In general, the effective permeability will depend on the fraction of the total pore space occupied by one fluid phase. The subscript e to the coefficient K indicates that the permeability is not necessarily that of a medium occupied by only one fluid. Usually the effective permeability will be smaller than K, the permeability when only one fluid occupies the medium. The ratio $K_e/K$ is called "relative permeability" and varies from 0 to 1.0. The fraction of the total pore space occupied by the wetting phase is defined as saturation S. It is considered here as a quantity which can vary from point to point within the medium. It is given by the relation

$$S = \frac { \Delta v \text { (fluid) } } { \Delta v \text { (pores) } } \tag { 3 }$$

where $\Delta v$ (fluid) is the volume of fluid occupying a portion of the pore volume, $\Delta v$ (pores), of a small volume element, $\Delta V$, of the medium.

In general, the functional relationship, $K_e = f(S)$, is not single-valued but is affected by hysteresis. The value of $K_e$ will be different if a given value of S is obtained by starting with a dry medium and increasing the liquid saturation than if the same value of S is obtained by removing liquid from an initially vacuum-saturated medium. Hysteresis affects both the liquid and the gas permeabilities.

Another assumption of this analysis is that the liquid and gaseous fluid phases are separated by curved interfaces, concave with respect to the liquid. This assumption is valid at relatively high liquid saturations in a medium containing at least some pores large enough that the liquid permeability is substantial. It is not always valid for saturations less than field capacity or for porous media having only extremely small pores, e.g., the spaces between clay platelets.

When liquid is separated from a gas by an interface, a pressure difference exists across the interface. This pressure difference is called capillary pressure $P_c$ and is related to the interfacial tension and curvature of the interface by the equation

$$P _ { c } = \sigma \left[ \frac { 1 } { r _ { 1 } } + \frac { 1 } { r _ { 2 } } \right] = P _ { \text {gas} } - P _ { \text {liquid} } \tag { 4 }$$

where $\sigma$ is the interfacial tension, $r_1$ and $r_2$ are major and minor radii of curvatures at a point on the interface. In all cases considered here, the solid matrix is wet by the liquid so that the liquid (except that in films under the influence of adsorptive forces) is at a pressure less than the pressure of the gas, and $P_c$ is, therefore, positive.

The value of $P_c$ depends on saturation and on the geometry of the pore space in which the interface occurs, being larger in small spaces than in large spaces for a given saturation. When a gas displaces a liquid from a porous medium (by gradually increasing $P_c$), the first liquid displaced is that occupying the largest pores in contact with the gas. As $P_c$ is increased further, the interfaces retreat to successively smaller spaces. The saturation is, therefore, a function of $P_c$, and $K_e$ is also a function of $P_c$, both being affected by hysteresis.

This paper is concerned primarily with desorption or drainage of liquid from media, thereby avoiding the hysteresis problem. However, a short discussion is presented at the end of the paper on the subject of hysteresis.

If engineers are to deal with the flow of water above the water table in connection with either irrigation or drainage of soils, a knowledge of the func-

tional relationship among effective permeability, saturation and capillary pressure is essential. This paper develops these functional relationships using a model of porous media developed by investigators [3, 4, 11, 19] in the petroleum industry. Specifically, the analysis presented here is an extension of the work of Burdine [3].

According to the analysis of Burdine, the relative permeability, $K_e/K_w$, is approximated by the relation:

$$K_{rw} = \left(\frac{S - S_r}{1 - S_r}\right)^2 \frac{\int_0^S \frac{dS}{P_c^2}}{\int_0^1 \frac{dS}{P_c^2}} \tag{5}$$

where $S_r$ is the residual saturation, sometimes called irreducible saturation in the petroleum literature. The permeability is assumed to approach zero at this finite saturation. Corey called the quantity $(S - S_r)/(1 - S_r)$ the effective saturation, $S_e$. By making a change of variable from $S$ to $S_e$ in the integrals of the above equation, the relative wetting phase permeability becomes

$$K_{rw} = (S_e)^2 \frac{\int_0^{S_e} \frac{dS_e}{P_c^2}}{\int_0^1 \frac{dS_e}{P_c^2}}. \tag{6}$$

Similarly, for the nonwetting phase

$$K_{rnw} = (1 - S_e)^2 \frac{\int_{S_e}^1 \frac{dS_e}{P_c^2}}{\int_0^1 \frac{dS_e}{P_c^2}}. \tag{7}$$

For the details of the Burdine development leading up to equations (6) and (7), the reader is referred to Appendix I. The ratio of integrals given in equations (6) and (7) can be evaluated graphically or numerically. It can also be evaluated analytically, if a suitable algebraic expression for $S_e = f(P_c)$ can be written.

Corey [5] found that for a large number of consolidated porous rock, the ratio of integrals on the right of equations (6) and (7) is approximately equal to $S_e^2$ and $(1 - S_e)^2$ respectively. He therefore proposed (as a convenient approximation) the equations:

$$K_{rw} \approx S_e^4, \tag{8}$$

$$K_{rnw} \approx (1 - S_e)^2 (1 - S_e^2). \tag{9}$$

The approximate equations of Corey have considerable utility because the only parameter needed

for their solution is the residual saturation. Because of their convenience, the equations of Corey are often used in the petroleum industry for making engineering calculations in regard to solution-gas drive petroleum reservoirs. A comparison of their validity and convenience with respect to other methods of estimating $K_{rw}$ was made by Loomis and Crowell [12].

The approximations given by Corey imply that effective saturation, $S_e$, is a linear function of $1/P_c^2$, i.e.

$$S_e = \left(\frac{c}{P_c}\right)^2 \text{ for } P_c \ge c \tag{10}$$

where $c$ is some constant. For most porous media, equation (10) is not strictly correct. The authors have plotted several hundred capillary pressure-desaturation curves using data from consolidated rock samples and found only a few samples in which the linear relationship was essentially true. However, when Corey's approximations were compared with experimental data of $K_{rw}$ and $S_e$ from some of these same rock samples, the comparison was favorable. Evidently, the relative permeabilities as a function of $S_e$ are not very sensitive to changes in the actual shape of the capillary pressure curve.

According to equation (6) for a completely uniform pore-size distribution, the value of the exponent in Corey's equation (8) would be 3,0. Averjanov [1] and Irmay [8] proposed equations similar to equation (8) in which values of 3,5 and 3,0 respectively were used as the exponent in their equations. Both of these investigators applied their equations to unconsolidated sands having a single-grain structure. Evidently, unconsolidated sands have a narrow range of pore sizes that are not absolutely uniform but which are more nearly uniform than most soils or consolidated rocks.

Theoretically, Corey's approximations are valid only for a particular pore-size distribution. If equation (10) is substituted into equation (8), the result is

$$K_{rw} = \left(\frac{c}{P_c}\right)^8, \tag{11}$$

but for media with relatively uniform pores the exponent in equation (11) is much larger than 8 and theoretically could increase without bound. Evidently, permeability is a very sensitive function of capillary pressure. Obviously, equation (11) cannot be valid for all porous media because permeability and saturation are not unique functions of capillary pressure, as Corey's equations imply, but depend upon the size and arrangement of the pores. Thus, a general relationship between saturation and capillary pressure is needed that will apply to a wide range of media. Such a relationship will allow equations (6) and (7) to be integrated and provide general relationships among the variables (permeability, saturation, and capillary pressure) for both the wetting and nonwetting phases. If the relationships among the variables can be shown to agree with experimental data, the Burdine approach will be greatly strengthened. Also, permeability can be predicted not only as a function of saturation but as a function of capillary pressure as well.

The basis for the theory of this section is the observation from a large number of experimental data that

$$S _ { e } = \left( \frac { P _ { b } } { P _ { c } } \right) ^ { \lambda } \text { for } P _ { c } \geq P _ { b } \tag { 1 2 }$$

where $\lambda$ and $P_b$ are characteristic constants of the medium. It will be shown later that $\lambda$ is a number which characterizes the pore-size distribution and $P_b$ is a measure of the maximum pore-size forming a continuous network of flow channels within the medium.

Equation (12) was discovered by plotting $\log S_e$ as a function of $\log P_c/\gamma$ on the drainage cycle. The result (for all media investigated to date) is a straight line with a negative slope $\lambda$ for $P_c/\gamma \geq P_b/\gamma$. Figure 2 shows examples of this kind of plot for several media. The parameter $P_b/\gamma$ is defined by the intercept where the straight line meets the ordinate representing $S_e = 1.0$ and it is called the bubbling pressure of the medium.

To determine $S_e$ for the particular values of $P_c/\gamma$, it is necessary to have precise capillary pressure desaturation data such as that shown in figure 1. Also, the residual saturation $S_r$ must be known to compute $S_e$. The procedure for determining $S_r$ is explained in detail in Appendix II. For the purpose of this paper, the definition of residual saturation is implicit in the method of its determination, but it is roughly analogous to the non-drainable water content referred to by drainage engineers. The negative of the slope of the curve of $S_e$ as a function of $P_c/\gamma$ is designated as $\lambda$, and it is called the pore-size distribution index of the medium.

If equation (12) is substituted into equation (6) and the indicated integrations are performed, the relative permeability of the wetting phase becomes

$$K _ { r w } = ( S _ { e } ) \frac { 2 + 3 \lambda } { \lambda } = ( S _ { e } ) ^ { \epsilon } \tag { 1 3 }$$

or

$$K _ { r w } = \left( \frac { P _ { b } } { P _ { c } } \right) ^ { \eta } \text { for } P _ { c } \geq P _ { b } \tag { 1 4 }$$

where $\eta = 2 + 3\lambda$ and $\epsilon = (2 + 3\lambda)/\lambda$.

Similarly, for the nonwetting phase

$$K _ { r n w } = ( 1 - S _ { e } ) ^ { 2 } ( 1 - S _ { e } \frac { 2 + \lambda } { \lambda } ) \tag { 1 5 }$$

or

$$K _ { r n w } = \left[ 1 - \left( \frac { P _ { b } } { P _ { c } } \right) ^ { \lambda } \right] ^ { 2 } \left[ 1 - \left( \frac { P _ { b } } { P _ { c } } \right) ^ { 2 + \lambda } \right] \tag { 1 6 }$$

for $P_c \geq P_b$.

Equations (12) - (16) present the theory regarding the interrelationships among the variables $P_c$, $S_e$, $K_{rw}$, and $K_{rnw}$. By experimentally determining the parameters $P_b$, $\lambda$, and $K$, the effective permeabilities to either the wetting or non-wetting fluid phase at any effective saturation or capillary pressure may be predicted.

It is expected that this theory is valid only for isotropic media and possibly only for the drainage cycle. It should, however, be valid for any pore-size distribution since equation (12) has been found to hold for media having a wide range of pore-size distributions.

Theoretically, $\lambda$ could have any positive value greater than zero, being small for media having a wide range of pore sizes and large for media with a relatively uniform pore size. It seems logical, therefore, to designate the exponent $\lambda$ as the pore-size distribution index.

Equations (13) and (14) have been expressed in terms of the exponents $\epsilon$ and $\eta$ as it is possible to determine these exponents experimentally without any knowledge of the capillary pressure desaturation curve. It is interesting to note that if the lower limit of $\lambda$ is zero, the theoretical lower limit of $\eta$ is 2.

In applying this theory, it should be recognized that values of $S_e$ and $K_{ew}$ may exist at $P_c < P_b$, but the theory does not hold for $P_c < P_b$. The significance of the parameter $P_b$ is discussed in more detail in the following sections. It should also be recognized that values of $S < S_r$ can exist but that the theory cannot apply in this range of saturations and may become inaccurate at saturations very close to $S_r$.

The theory makes the simplifying assumptions that $K_{ew}$ is zero and $K_{enw}$ is a maximum at $S_r$. Neither is actually true. It is a fact, however, that when the curves of $K_{ew}$ as a function of $S$ are extrapolated, $K_{ew}$ appears to approach zero at the finite saturation $S_r$.

Still another limitation of the theory is that it assumes that the porous matrix will not undergo any change in geometry as it changes from a full saturated condition to a value of $S$ approaching $S_r$.

![img-1.jpeg](None)

**{"image_type": "plot", "description": "Das Diagramm zeigt die Beziehung zwischen dem Sättigungsgrad (S) in Prozent und der Saugspannung (pF) für verschiedene Bodenarten. Die X-Achse stellt die Saugspannung (pF) dar, während die Y-Achse den Sättigungsgrad (S) in Prozent angibt. Es werden vier Bodenarten verglichen:\n\n1. Vulkanischer Boden (Kurve 1, durchgezogene Linie mit gefüllten Kreisen)\n2. Grober Sand (Kurve 2, gestrichelte Linie mit offenen Kreisen)\n3. Feiner Sand (Kurve 3, gepunktete Linie mit offenen Kreisen)\n4. Toniger Schluff-Lehm (Kurve 4, durchgezogene Linie mit offenen Kreisen)\n\nSchlüsselbeobachtungen:\n- Vulkanischer Boden (1) zeigt die höchste Saugspannung bei niedrigem Sättigungsgrad und behält einen höheren Sättigungsgrad bei höheren pF-Werten im Vergleich zu den anderen Böden.\n- Grober Sand (2) hat die niedrigste Saugspannung bei jedem Sättigungsgrad und verliert schnell an Sättigung bei steigendem pF.\n- Feiner Sand (3) und toniger Schluff-Lehm (4) liegen dazwischen, wobei der tonige Schluff-Lehm bei niedrigen pF-Werten eine höhere Sättigung beibehält, aber bei höheren pF-Werten schneller abnimmt als der feine Sand.\n\nUngefähre Schlüsselwerte (abgelesen aus dem Diagramm):\n- Vulkanischer Boden (1): S ≈ 90% bei pF ≈ 1.5, S ≈ 50% bei pF ≈ 2.5, S ≈ 20% bei pF ≈ 3.5\n- Grober Sand (2): S ≈ 80% bei pF ≈ 1.0, S ≈ 30% bei pF ≈ 2.0, S ≈ 10% bei pF ≈ 3.0\n- Feiner Sand (3): S ≈ 85% bei pF ≈ 1.5, S ≈ 40% bei pF ≈ 2.5, S ≈ 15% bei pF ≈ 3.5\n- Toniger Schluff-Lehm (4): S ≈ 95% bei pF ≈ 1.5, S ≈ 60% bei pF ≈ 2.5, S ≈ 25% bei pF ≈ 3.5"}**

![img-2.jpeg](None)

**{"image_type": "plot", "description": "Das Diagramm zeigt die Beziehung zwischen der relativen Permeabilität (k_rw) und der Sättigung des wässrigen Phasenanteils (S_w) für drei verschiedene Gesteinstypen: Fragmentierte Matrix, Berea Sandstein und Hygiene Sandstein. \n\n- Die X-Achse stellt die Sättigung des wässrigen Phasenanteils (S_w) dar, die von 0 bis 1 reicht.\n- Die Y-Achse zeigt die relative Permeabilität (k_rw), die von 0 bis 100 skaliert ist.\n\nDrei Kurven sind dargestellt:\n1. Kurve (1) für die Fragmentierte Matrix: Diese Kurve zeigt einen steilen Abfall der relativen Permeabilität bei niedrigen Sättigungswerten und nähert sich asymptotisch 0 bei Sättigungswerten nahe 0.5.\n2. Kurve (2) für den Berea Sandstein: Diese Kurve zeigt einen moderaten Abfall der relativen Permeabilität, die bei Sättigungswerten nahe 0.6 auf etwa 10 abfällt und dann langsam weiter abnimmt.\n3. Kurve (3) für den Hygiene Sandstein: Diese Kurve zeigt den langsamsten Abfall der relativen Permeabilität, die bei Sättigungswerten nahe 0.7 auf etwa 20 abfällt und dann langsam weiter abnimmt.\n\nSchlüssel-Datenpunkte (ungefähre Werte):\n- Fragmentierte Matrix (1): S_w ≈ 0.1 → k_rw ≈ 80; S_w ≈ 0.3 → k_rw ≈ 20; S_w ≈ 0.5 → k_rw ≈ 0\n- Berea Sandstein (2): S_w ≈ 0.2 → k_rw ≈ 60; S_w ≈ 0.4 → k_rw ≈ 30; S_w ≈ 0.6 → k_rw ≈ 10\n- Hygiene Sandstein (3): S_w ≈ 0.3 → k_rw ≈ 70; S_w ≈ 0.5 → k_rw ≈ 40; S_w ≈ 0.7 → k_rw ≈ 20"}**

Figure 1. Capillary pressure head as a function of saturation for porous materials of varying pore-size distributions.

![img-3.jpeg](None)

**{"image_type": "plot", "description": "The image is a semi-logarithmic plot showing the relationship between the ratio of particle diameter (D) to clay content (C) on the x-axis (logarithmic scale, ranging from 1 to 500) and the hydraulic conductivity (K) on the y-axis (linear scale, ranging from 0.001 to 1 cm/s). The plot includes four distinct curves, each representing different soil types:\n\n1. **Volcanic Sand** (Curve 1): Shows the highest hydraulic conductivity values, with K decreasing as D/C increases. Key points include:\n   - At D/C ≈ 1, K ≈ 0.7 cm/s\n   - At D/C ≈ 10, K ≈ 0.1 cm/s\n   - At D/C ≈ 100, K ≈ 0.01 cm/s\n\n2. **Glass Beads** (Curve 2): Displays intermediate hydraulic conductivity values, with a steeper decline compared to Volcanic Sand. Key points include:\n   - At D/C ≈ 1, K ≈ 0.3 cm/s\n   - At D/C ≈ 10, K ≈ 0.03 cm/s\n   - At D/C ≈ 100, K ≈ 0.003 cm/s\n\n3. **Fine Sand (G.E. No. 13)** (Curve 3): Shows lower hydraulic conductivity values, with a gradual decline. Key points include:\n   - At D/C ≈ 1, K ≈ 0.07 cm/s\n   - At D/C ≈ 10, K ≈ 0.007 cm/s\n   - At D/C ≈ 100, K ≈ 0.0007 cm/s\n\n4. **Touchet Silt Loam (G.E. No. 3)** (Curve 4): Exhibits the lowest hydraulic conductivity values, with a very steep decline. Key points include:\n   - At D/C ≈ 1, K ≈ 0.007 cm/s\n   - At D/C ≈ 10, K ≈ 0.0007 cm/s\n   - At D/C ≈ 100, K ≈ 0.00007 cm/s\n\nThe plot demonstrates that as the ratio of particle diameter to clay content (D/C) increases, the hydraulic conductivity (K) decreases exponentially for all soil types. The curves are labeled with their respective λ (lambda) values, indicating the rate of decline in hydraulic conductivity:\n- Volcanic Sand: λ = 2.29\n- Glass Beads: λ = 3.70\n- Fine Sand: λ = 730\n- Touchet Silt Loam: λ = 1.82"}**

![img-4.jpeg](None)

**{"image_type": "plot", "description": "The image is a semi-logarithmic plot (logarithmic y-axis, linear x-axis) showing the relationship between the variable 'k' (on the y-axis, labeled as 'k' with units not specified) and 'd₅₀' (on the x-axis, labeled as 'd₅₀ in cm'). The plot includes three distinct curves representing different types of sandstone:\n\n1. Curve (1) labeled 'Fragmented' (open circles): Shows a steep decline in 'k' as 'd₅₀' increases, with a slope of approximately -2.89.\n2. Curve (2) labeled 'Berea Sandstone' (triangles): Displays a moderate decline in 'k' with increasing 'd₅₀', with a slope of approximately -3.69.\n3. Curve (3) labeled 'Hyde Park Sandstone' (squares): Exhibits the least steep decline in 'k' as 'd₅₀' increases, with a slope of approximately -6.17.\n\nKey observations:\n- All three curves show a negative correlation between 'k' and 'd₅₀', indicating that as the particle size (d₅₀) increases, the variable 'k' decreases.\n- The rate of decrease varies among the three sandstone types, with 'Fragmented' sandstone showing the fastest decline and 'Hyde Park Sandstone' the slowest.\n- The y-axis ranges from 0.001 to 10, and the x-axis ranges from 0.1 cm to 100 cm.\n\nApproximate key data points (extracted from the plot):\n- For 'Fragmented' (1):\n  - At d₅₀ ≈ 0.1 cm, k ≈ 10\n  - At d₅₀ ≈ 1 cm, k ≈ 1\n  - At d₅₀ ≈ 10 cm, k ≈ 0.1\n- For 'Berea Sandstone' (2):\n  - At d₅₀ ≈ 0.1 cm, k ≈ 5\n  - At d₅₀ ≈ 1 cm, k ≈ 0.5\n  - At d₅₀ ≈ 10 cm, k ≈ 0.05\n- For 'Hyde Park Sandstone' (3):\n  - At d₅₀ ≈ 0.1 cm, k ≈ 2\n  - At d₅₀ ≈ 1 cm, k ≈ 0.2\n  - At d₅₀ ≈ 10 cm, k ≈ 0.02"}**

Figure 2. Effective saturation as a function of capillary pressure head for porous materials of varying pore-size distributions.

To date, the authors have investigated mostly unconsolidated media in verifying the theory because it has been easier to create unconsolidated media which are isotropic than to find consolidated porous rocks which are isotropic. The authors have developed ways to measure S, Pc, and Kenw simultaneously with sufficient precision on the unconsolidated samples. To date, it has been necessary to measure Kew as a function of Pc by separate experiments, because methods of measuring Kew and Kenw simultaneously with sufficient precision for unconsolidated media have not yet been developed. One method that has been described in the literature by Corey [6] results in defective measurements of Kenw in the high saturation (low Kenw) range.

Precise curves of S as a function of Pc were obtained with a device such that the entire sample was held at a uniform capillary pressure from top to bottom. Ordinarily in a liquid-gas system, the difference in specific weight of the two fluids will produce a greater Pc at the top of a sample than at the bottom (under static conditions).

To overcome this difficulty, all the curves for unconsolidated media shown in figure 1 were determined by maintaining a pressure difference in the air phase exactly equal to the difference in the static liquid pressure between the top and bottom of the sample. It was convenient to measure the gas permeability simultaneously by measuring the flow of air that resulted from the greater air pressure at the bottom of the sample. The flow diagram is presented in figure 3 and the cell used for containing the unconsolidated sample is shown in figure 4.

By-passing of air along the boundaries was prevented by providing a rubber sleeve which was held against the outer circumference of the sample with a pneumatic pressure from 5 - 20 psi depending upon the texture of the sample. Liquid was removed through a hollow ceramic cylinder which was filled with liquid and connected to a calibrated glass tube for measuring the outflow. The media samples occupied the annular space between the hollow ceramic cylinder and the rubber sleeve.

A pair of pressure control reservoirs controlled the liquid pressure in the medium. A flexible plastic tube connected the top of the upper reservoir to the outflow end of the horizontal measuring tube. Another flexible plastic tube connected the bottom of the upper reservoir to the bottom of the lower reservoir, the top of the lower reservoir being open to the atmosphere. The liquid pressure in the medium was decreased in increments by lowering the lower reservoir, the pressure being measured with respect to atmospheric pressure by the difference in liquid elevations in the upper and lower reservoirs at equilibrium. A correction was made for the capillarity of the outflow measuring tube and for its position relative to the sample container.

The capillary pressure was determined by the difference in pressure between the air and the liquid

in the medium. The saturations of the samples were determined by noting the accumulated outflow from the medium at each increment of capillary pressure (after outflow stopped) and subtracting this from the total liquid contained in the fully saturated samples.

The pressure of the air at the bottom of the samples was maintained greater than atmospheric by an amount equal to the static liquid pressure difference between the bottom and top of the samples. The air pressure at the bottom of the samples was controlled by a precision pressure regulator, the air pressure at the top of the samples being atmospheric.

The resulting upward flow of air was measured with one of several soap-film flowmeters of different sizes, depending on the amount of discharge. These flowmeters measure the volume flux directly and require no calibration other than the initial calibration of the tube containing the soap film. The calibrated soap-film tubes are encased in evacuated and sealed glass shells so that temperature fluctuations in the room had little affect on the measurements.

In order to prevent errors in measurement of saturation due to liquid being removed as vapor in the flowing air, the air entering the media was pre-saturated with the vapor of the liquid used in the medium.

Measurement of liquid relative permeability as a function of capillary pressure was accomplished in separate experiments using an apparatus similar to that employed by Scott and Corey [18]. The columns varied in length and were considerably shorter than those employed by Scott and Corey in order that they could be packed in a homogeneous and reproducible manner using a mechanical packer patterned after a design by Jackson et. al. [9]. In one case (the granulated mixture) the column was packed by a method similar to that suggested by Reeve and Brooks [16].

The column method permits steady downward flow with the wetting phase at practically constant pressure along the length of the test section of the columns. The capillary pressure was, therefore, nearly constant during a particular measurement. A series of tensiometer rings sensed the pressure by contact around the circumference of the columns and did not interfere in any way with the flow section.

The columns were first vacuum saturated. The maximum wetting phase permeability was then determined by downward flow at a pressure slightly less than the pressure of the surrounding air, but not enough less to permit air to invade the columns. The capillary pressure was then increased in increments by decreasing the pressure of the wetting fluid at the top and bottom of the columns. This was possible because the wetting fluid entered and left the columns through porous barriers that remained completely saturated throughout the experiments.

When Pc was increased beyond a critical value, air penetrated the columns through joints in the plastic walls of the columns. After the penetration of air stopped and the flow reached a steady state as

![img-5.jpeg](None)

**{"image_type": "diagram", "description": "The diagram illustrates an experimental setup for measuring soil properties, specifically involving air and liquid flow through a soil sample. Key components and their connections are as follows:\n\n1. **Compressed Air Source**: Supplies air at 60 psi.\n2. **Coarse Regulator**: Reduces the air pressure from the compressed air source.\n3. **Fine Regulator**: Further refines the air pressure to a precise level.\n4. **Trap**: Removes moisture or impurities from the air before it proceeds.\n5. **Presaturator**: Saturates the air with moisture to maintain specific humidity conditions.\n6. **Air Inflow**: The regulated and presaturated air flows into the soil sample.\n7. **Soil Sample**: The central component where air and liquid interactions are studied. It is enclosed in a sleeve to control pressure.\n8. **Tensiometer - Outflow Barrier**: Measures soil water tension and acts as a barrier for outflow.\n9. **Sleeve Pressure**: Applied to the sleeve enclosing the soil sample to control the pressure conditions.\n10. **Calibrated Liquid Flowmeter**: Measures the flow rate of liquid through the soil sample.\n11. **Soap Film Air Flowmeter**: Measures the flow rate of air exiting the system.\n12. **Air Outflow to Atmosphere**: The path through which air exits the system after measurement.\n13. **Air Pressure Manometer**: Monitors the air pressure within the system.\n\nThe diagram shows the flow of air from the compressed air source through regulators, a trap, and a presaturator before entering the soil sample. Liquid flow is also measured using a calibrated liquid flowmeter. The setup allows for precise control and measurement of air and liquid interactions within the soil sample."}**

Figure 3. Diagram of flow system and pressure control system for air permeability cell.

![img-6.jpeg](None)

**{"image_type": "diagram", "description": "The image is a top view diagram of a circular structure with concentric circles and labeled points. Key features include:\n\n- A central point labeled '1'.\n- A series of concentric circles around point '1', with the outermost circle labeled '5'.\n- Points labeled '2', '3', '4', and '5' are marked on the concentric circles, with '2' and '3' closer to the center and '4' and '5' further out.\n- Two vertical lines labeled 'A' on either side of the diagram, indicating a symmetrical axis.\n- The diagram includes dashed lines connecting points '2', '3', '4', and '5' to the central point '1', forming a radial pattern.\n- The text 'TOP VIEW' is centered below the diagram.\n\nThe diagram appears to represent a radial or circular arrangement of points, possibly for a mechanical, electrical, or structural layout."}**

![img-7.jpeg](None)

**{"image_type": "diagram", "description": "The image is a technical diagram labeled 'SECTION A-A' showing a cross-sectional view of a mechanical or structural assembly. The diagram includes the following labeled components:\n\n1. A central vertical shaft or spindle.\n2. A housing or frame supporting the shaft.\n3. A gear or pulley system (labeled 15) connected to the shaft.\n4. A lever or arm (labeled 17) attached to the shaft, likely for manual operation or adjustment.\n5. A base or platform (labeled 14) supporting the entire assembly.\n6. Additional structural elements (e.g., 16, 18, 19) providing support or housing for internal components.\n7. A handwheel or knob (labeled 13) for fine adjustment or locking.\n\nThe diagram appears to depict a mechanical system, possibly a valve, pump, or similar device, with rotational and possibly linear motion components. The labels correspond to specific parts of the assembly, and the connections between components suggest a functional relationship for operation or control."}**

![img-8.jpeg](None)

**{"image_type": "diagram", "description": "The image is a technical diagram labeled 'FRONT VIEW' showing a structural framework with multiple vertical and horizontal members. Key components include:\n\n1. Vertical members (labeled with numbers such as 1, 2, 3, 4, 5, 6, 7, 8, 9, 10) connected by horizontal and diagonal braces.\n2. The central vertical member (labeled 2) is the primary structural element, with other members branching off or connecting to it.\n3. The diagram includes dimensions or spacing indicators (e.g., ε₂) between certain vertical members.\n4. The connections between members appear to be rigid or fixed, as indicated by the detailed joint representations.\n\nThis diagram likely represents a load-bearing frame, truss, or scaffolding system used in construction or engineering. The precise labeling and structural layout suggest it is part of a technical drawing for assembly or analysis."}**

Parts and Materials for
Air Permeability--Capillary Pressure Cell

|  Part No. | Name | Size | No. req'd | Material  |
| --- | --- | --- | --- | --- |
|  1. | Sleeve Pressure Tap | 1/8" tube--1/8" MPT | 1 | Brass (Swagelok)  |
|  2. | Rubber Sleeve | 2-1/2 ID x 1/32" wall x 4" | 1 | Hycar tubing, Durometer 35  |
|  3. | Head Bolt | 1/4"-20 x 2-1/2" | 6 | Steel  |
|  4. | Upper Head Plate | 4-3/4" dia. x 1/2" thick | 1 | Plastic  |
|  5. | Lower Head Plate | 4-3/4" dia. x 1/2" thick | 1 | Plastic  |
|  6. | Air Outflow Tap | 1/4" tube-1/4" - 28 M. T. | 1 | Brass  |
|  7. | Air Inflow Tap | 1/4" tube-1/4" - 28 M. T. | 1 | Brass  |
|  8. | Manometer Tap | 1/8" tube--5-40 M. T. | 2 | Brass  |
|  9. | Liquid Outflow Tap | 3/16" tube-3/8"-18 M. T. | 1 | Steel (air tight connection with Part 16)  |
|  10. | Ceramic Barrier to Air | 3.25 cm. OD x 1.5 mm wall x 5.5 cm. | 1 | Ceramic (Selas 015) bubbling pressure = 15 PSI  |
|  11. | Retainer Ring | 6.8 cm. OD x 0.5 mm wall x 0.4 cm. | 2 | Steel  |
|  12. | Fiber Glass Disk | 7.0 cm. dia. x 0.6 mm | 2 | Fiberglass  |
|  13. | O Ring | 2-7/8"ID x 1/8" wall 11/16" ID x 3/32" wall | 2 2 | Neoprene Neoprene  |
|  14. | Lower Tensiometer Screw | 1/4"-20 x 1" | 1 | Brass  |
|  15. | Upper Tensiometer Nut | 3/8"-16 NC | 1 | Brass  |
|  16. | Tensiometer-liquid Outflow Assembly | 3.25 cm. OD x 5.5 cm. | 1 | Plastic and Ceramic  |
|  17. | Sleeve Cylinder | 2-3/4" ID x 1/4" wall x 2-1/8" | 1 | Plastic  |
|  18. | Head Bolt Ring | 4-3/4" OD x 2-3/4" ID x 1/2" | 1 | Plastic (cemented to Part 17)  |
|  19. | Head Bolt Spacer | 3/8" OD x 1/16" wall x 1/2" | 6 | Steel tube  |

MPT = Male pipe thread
MT = Male thread

Figure 4. Construction details of air permeability cell.

indicated by the steadiness of the discharge and the readings from manometers attached to the tensiometer rings, the discharge was measured and the effective permeability determined. The process was repeated over the desired range of Pc.

In order to compare the nonwetting phase permeabilities with the wetting phase permeabilities, the air permeability cell was packed with a medium at a porosity as near as possible to that obtained with the same material with the column packer. The columns used for the wetting phase permeability measurements, however, did not have a pressurized sleeve. In one case, with a silt loam soil, the air permeameter cell with its pressurized sleeve caused the medium to compress to a final porosity substantially less than that obtained with the column packer. This would probably happen with any highly compressible soil when it is saturated. In the case of the granular materials used in this investigation, it was usually possible to obtain nearly the same porosities in the air permeameter cell as in the sleeveless columns.

In all cases the wetting fluid was a hydrocarbon liquid* and the nonwetting fluid was air. The hydrocarbon was selected instead of water primarily because soil structure is much more stable in the presence of the hydrocarbon than in the presence of water. The hydrocarbon also has more consistent wetting properties, and its surface tension is not changed as readily by contaminants. The relationship between the capillary pressure head for water and oil in a stable medium was experimentally found to be

$$\left(\frac{P_c}{\gamma}\right)_w = 2 \left(\frac{P_c}{\gamma}\right)_o \tag{17}$$

where the subscript w and o designate water and oil, respectively.

The unconsolidated media used in this investigation consisted of materials having a structure relatively stable in the presence of the hydrocarbon liquid. Although a large number of materials were investigated in preliminary stages of the investigation, a complete set of data was obtained on only five of the unconsolidated media. These media, however, represented a very wide range of hydraulic characteristics. A description of the five materials on which more or less complete data were obtained is as follows:

1. Volcanic sand--This material comes from a wind-blown deposit along Crab Creek in Washington State. It consists of dark-colored aggregates which can be broken down into finer particles by pressure. It is not known to what degree these aggregates are themselves permeable, but they undoubtedly have some permeability. At any rate, this sand has a degree of structure and has both primary and secondary porosity.

2. Fine sand--This sand was supplied by the Hanford Laboratories of General Electric Company at Richland, Washington, and apparently contains some volcanic minerals. It contains a wide range of particle sizes, ranging down to silt size. Most of the particles are angular and not as rounded as most river bed sands.

3. Glass beads--The beads were purchased from the Minnesota Mining and Manufacturing Company and designated as size 130-5005. This material is an example of media having a very narrow range of pore sizes. It is not much different in this respect, however, from many clean river bed sands.

4. Fragmented mixture--This medium was obtained by mixing aggregates created by crushing oven-dried clay and a consolidated sandstone with the volcanic sand. The aggregates were crushed until all passed through a #32 sieve. This material was created to simulate a soil having a well aggregated structure with secondary as well as primary porosity. The aggregates were much more stable, however, than those found in ordinary soils.

5. Touchet silt loam--This soil comes from the Columbia River basin and was also supplied by the Hanford Laboratory. It is extremely fine textured in that it contains practically no coarse sand, but it is somewhat unusual in that it contains a smaller amount of clay than would be expected in such a fine-textured soil. It is, in fact, nearly pure silt mixed with some extremely fine sand. It contains enough clay, however, to create a structure with secondary porosity.

In addition to the five unconsolidated media, two consolidated sandstone cores were investigated. One of these, Berea Sandstone, was cut perpendicular to the bedding planes. In the dry state and in the fully saturated state the stratification was not visible. After saturating the material completely with liquid and then desaturating to a value of S of about 0.80 to 0.90, the strata became plainly visible. At this average saturation, the finer-textured strata were still fully saturated and darker than the partially desaturated coarser-textured strata. The finer and coarser strata alternate in position in a more or less regular pattern, the individual strata being about 1/8 inch thick.

The other sandstone investigated, Hygiene from the Pierre Formation in Colorado, contains no visible bedding. It contains a substantial amount of clay and thus has a rather high value of Sr (0.577). It has an unusually narrow pore-size distribution for a material having such a high residual saturation. The significant hydraulic properties of the seven media described above are tabulated in Tables 1 - 4 in Appendix III.

Because the theory on which equation (15) is based assumes that Krnw = 1 at S = Sr, Knw is defined in this paper in a somewhat arbitrary manner; i.e., the value of Knw used in the denominator of the ratio Krnw was obtained by extrapolating Knw vs. Pc/γ to large values of Pc/γ. At values of S less than Sr, the values of Krnw may be greater than 1; but since the theory does not apply to this range of saturations, the variation of Krnw in this range was not investigated in detail. Where the data are available, however, they are tabulated in the tables.

Another reason for defining Krnw in this way was that in the case of the unconsolidated media, it was not practical to determine the actual maximum

* Soltrol "C" core test fluid. Phillips Petroleum Company, Special Products Division, Bartlesville, Oklahoma.

air permeability, $K_{nw}$. It was possible to determine the air permeability before the media were saturated in the air permeability cell, but this was usually not the maximum value of air permeability as determined after the samples had been vacuum saturated and then desaturated. This value of $K_{nw}$ often exceeded the air permeability value of dry media even before S was reduced to $S_r$. Evidently, the process of saturating and then drying caused the pulling together of fine material into aggregates and the creation of larger pores.

The samples could not be brought to a satura-

tion of $S_r$ in a reasonable time by increasing the negative pressure of the outflow tube. They could, of course, have been dried further by evaporation, but this would have foiled the material balance calculation of the saturation. Experiments with unconsolidated media were actually terminated at $S > S_r$. The samples were removed from the cell and the volume of liquid remaining in the sample was measured gravimetrically. This volume of liquid was added to the volume removed during the experiment to obtain the volume at a saturation of 1.0 so that material balance computations of saturations at other values of $P_c/\gamma$ could be made.

The first step in checking the theory represented by equations (13), (14), (15), and (16) was the determination of the parameters $P_b$ and $\lambda$ from the data shown in figure 1. The data were replotted as figure 2 in which $S_e$ is shown as a function of $P_c/\gamma$. These curves were obtained after successive approximations of the residual saturation $S_r$ as described in Appendix II.

The negative of the slope of the straight line portion of a curve, e.g., those shown in figure 2, is designated as $\lambda$ and is called the "pore-size distribution index". The extrapolation of the straight line to the ordinate representing $S_e = 1.0$ gives the value of the parameter $P_b$ which is called the "bubbling pressure". This particular value of capillary pressure is called bubbling pressure because it was found experimentally that for homogeneous and isotropic media, it is very close to the capillary pressure at which the first gas flow can be observed. The bubbling pressure apparently represents the smallest capillary pressure at which a continuous gas phase exists. At smaller values of $P_c$, the theory does not appear to be valid for either the wetting or the nonwetting permeabilities.

Having determined the parameters $P_b$ and $\lambda$, equation (16) was solved to obtain relative permeabilities to air as a function of $P_c/\gamma$. The solutions of equation (16) are shown in figure 5 as solid lines. The data points represent measured values. It can be seen from the figures that the measured values of air relative permeability are in reasonably close agreement with the theoretical curves in every case except for the Berea Sandstone. Undoubtedly the failure of the theory in the latter case is a result of the anisotropy of this medium. Because air flow across bedding planes is restricted by the layers having the highest individual bubbling pressures, the measured values of $K_{rnw}^*$ are less than the theoretical values at corresponding values of $P_c$. This phenomenon has been described elsewhere by Corey and Rathjens [7].

In the case of the unconsolidated media, the experimental procedure provided no direct comparison of measured values of $K_{rw}$ with theoretical curves of $K_{rw}$ as a function of $P_c$. This was because the theoretical curves were computed from the parameters $\lambda$ and $P_b$ which were obtained in a separate experiment. In general, the packing and the resultant values of $\phi$ and $P_b/\gamma$ are difficult to reproduce with precision, especially in a totally different kind of container.

Figure 6, however, shows measured values of $K_{rw}$ as a function of $P_c/\gamma$. The solid curves are computed from equation (14) using values of $\lambda$ and $P_b/\gamma$ obtained with the air permeability cell. In most cases the agreement between measured and com-

puted values of $K_{rw}$ is good. In the case of the Touchet silt loam, the computed curve is displaced toward higher values of $P_c/\gamma$ at corresponding values of $K_{rw}$. In the case of the Fragmented Mixture, it is displaced slightly toward lower values of $P_c/\gamma$.

Evidently, in the case of the Touchet silt loam, the pressurized sleeve of the air permeability cell caused this soil to be compressed more (and thus have smaller pores) than was the case for the same soil when packed by the automatic packer in the rigid columns used for the $K_{rw}$ measurements.

It is noteworthy, however, that the slopes of the measured curves on the log-log plot of $K_{rw}$ as a function of $P_c/\gamma$ are essentially the same as for the calculated curves. In other words, the measured values of $\eta$ are in close agreement with the relationship $\eta = 2 + 3\lambda$ even though $\lambda$ was determined in a separate experiment. Evidently, the pore-size distribution index is less sensitive to packing differences than are the values of $\phi$ and $P_b$.

For the consolidated sandstone, the agreement with respect to both $P_b$ and $\lambda$ is excellent as is shown in curves 2 and 3 on figure 6b. The anisotropy of Berea Sandstone has a less noticeable effect on $K_{rw}$ than on $K_{rnw}$.

A comparison of measured values of $K_{rnw}$ as a function of S with theoretical curves is shown in figure 7 for unconsolidated media. The theoretical curves were computed from equation (15). The agreement between measured and computed values of $K_{rnw}$ is reasonably close. There is, however, a tendency for the measured values of $K_{rnw}$ to be displaced toward smaller values than the predicted curves at the mid-range of S.

The authors suspect that the reason for this displacement is a result of a failure of the theory caused by the assumption that $K_{enw}$ is a maximum at $S = S_r$ and that $K_{rnw} = 1$ at $S = S_r$. As previously explained, a value of $K_{nw}$ was chosen so that measured values of $K_{rnw}$ would extrapolate to a value of 1 at $S_r$. The measured curve, therefore, is fitted to the theoretical curve at this point. It would be possible to choose a value of $K_{nw}$ such that the measured curve would fit the theory at the midpoint. In this case the measured values would cross the theoretical curve.

It might be possible in the future to perfect the theory in such a way as to account for the fact that $K_{enw}$ is not a maximum at $S_r$ but this remains to be done.

It is also possible that the results shown in figure 7 are affected by a failure to achieve complete

![img-9.jpeg](None)

**{"image_type": "plot", "description": "The image is a plot showing the relationship between the void ratio (e) and the effective consolidation pressure (σ'v) for different soil types. The X-axis represents the effective consolidation pressure (σ'v) in kg/cm², ranging from 0 to 1.0. The Y-axis represents the void ratio (e), ranging from 0 to 1.5.\n\nFour curves are plotted, each representing a different soil type:\n1. Curve (1): Volcanic Soil (solid circles)\n2. Curve (2): Gloss Beads (open circles)\n3. Curve (3): Touchet Silt Loam (solid triangles)\n4. Curve (4): Touchet Silt Loam (open triangles)\n\nKey observations:\n- Curve (1) (Volcanic Soil) shows the highest void ratio at lower pressures but decreases sharply as pressure increases.\n- Curve (2) (Gloss Beads) maintains a relatively low and stable void ratio across the pressure range.\n- Curve (3) (Touchet Silt Loam, solid triangles) and Curve (4) (Touchet Silt Loam, open triangles) show intermediate behavior, with Curve (4) having a slightly higher void ratio than Curve (3) at lower pressures.\n\nApproximate key data points for each curve (e, σ'v):\n- Curve (1): (1.4, 0.05), (1.0, 0.2), (0.6, 0.5), (0.4, 0.8), (0.2, 1.0)\n- Curve (2): (0.4, 0.05), (0.35, 0.2), (0.3, 0.5), (0.25, 0.8), (0.2, 1.0)\n- Curve (3): (0.8, 0.05), (0.6, 0.2), (0.45, 0.5), (0.35, 0.8), (0.25, 1.0)\n- Curve (4): (1.0, 0.05), (0.7, 0.2), (0.5, 0.5), (0.4, 0.8), (0.3, 1.0)"}**

![img-10.jpeg](None)

**{"image_type": "plot", "description": "The image is a plot showing the relationship between the variable κ_hyd (x-axis, ranging from 0 to 1) and the variable d (y-axis, ranging from 0 to 150). The plot includes three distinct curves labeled as:\n\n1. (1) Fragmented Mixture (solid line with open circles)\n2. (2) Berea Sandstone (dashed line with filled circles)\n3. (3) Nugget Sandstone (dotted line with open squares)\n\nKey observations:\n- Curve (1) Fragmented Mixture shows a linear increase in d as κ_hyd increases.\n- Curve (2) Berea Sandstone shows a nonlinear increase, with d rising more steeply at higher κ_hyd values.\n- Curve (3) Nugget Sandstone also shows a nonlinear increase, but with a steeper rise compared to Curve (2) at higher κ_hyd values.\n\nApproximate key data points for each curve (κ_hyd, d):\n- Fragmented Mixture (1): (0, 0), (0.2, 20), (0.4, 40), (0.6, 60), (0.8, 80), (1.0, 100)\n- Berea Sandstone (2): (0, 0), (0.2, 10), (0.4, 30), (0.6, 60), (0.8, 100), (1.0, 140)\n- Nugget Sandstone (3): (0, 0), (0.2, 15), (0.4, 40), (0.6, 80), (0.8, 120), (1.0, 150)"}**

Figure 5. Theoretical curves and experimental data of capillary pressure head as a function of nonwetting phase relative permeability.

![img-11.jpeg](None)

**{"image_type": "plot", "description": "The image is a semi-logarithmic plot (logarithmic y-axis) showing the relationship between the void ratio (e) and the effective stress (σ') in cm² for different soil types. The x-axis represents the effective stress (σ') in cm², ranging from 0.1 to 100. The y-axis represents the void ratio (e), ranging from 0.001 to 10.\n\nKey observations and data points:\n- The plot includes four distinct curves, each representing a different soil type:\n  1. Volcanic Sand (labeled as (1))\n  2. Glass Beads (labeled as (2))\n  3. Fine Sand (labeled as (3), E. No. 5)\n  4. Touchet Silt Loam (labeled as (4), E. No. 3)\n\n- The curves show a general trend of decreasing void ratio with increasing effective stress, indicating soil consolidation.\n\n- Approximate key data points for each soil type (void ratio, effective stress in cm²):\n  - Volcanic Sand (1):\n    - (e ≈ 1.5, σ' ≈ 0.1)\n    - (e ≈ 0.5, σ' ≈ 1)\n    - (e ≈ 0.2, σ' ≈ 10)\n  - Glass Beads (2):\n    - (e ≈ 1.2, σ' ≈ 0.1)\n    - (e ≈ 0.4, σ' ≈ 1)\n    - (e ≈ 0.15, σ' ≈ 10)\n  - Fine Sand (3):\n    - (e ≈ 1.0, σ' ≈ 0.1)\n    - (e ≈ 0.3, σ' ≈ 1)\n    - (e ≈ 0.1, σ' ≈ 10)\n  - Touchet Silt Loam (4):\n    - (e ≈ 0.8, σ' ≈ 0.1)\n    - (e ≈ 0.25, σ' ≈ 1)\n    - (e ≈ 0.08, σ' ≈ 10)\n\n- The plot includes annotations for specific void ratios at certain points:\n  - e = 8.9 (near the top of the plot)\n  - e = 23.9 (near the top of the plot)\n  - e = 7.5 (near the top of the plot)\n  - e = 3.1 (near the middle of the plot)\n\n- The curves are labeled with numbers (1) to (4) corresponding to the soil types listed in the legend."}**

![img-12.jpeg](None)

**{"image_type": "plot", "description": "The image is a plot showing the relationship between the hydraulic conductivity (K in cm/s) and the void ratio (e) for different types of materials. The X-axis represents the void ratio (e), ranging from 0.001 to 100 cm. The Y-axis represents the hydraulic conductivity (K) in cm/s, ranging from 0.0001 to 1.0 cm/s.\n\nKey observations and data points:\n- The plot includes three distinct curves representing different materials:\n  1. Fragmented Mixture (labeled as (1))\n  2. Berea Sandstone (labeled as (2))\n  3. Hygiene Sandstone and Pierre Formation (labeled as (3))\n\n- For the Fragmented Mixture:\n  - At void ratio e ≈ 10, K ≈ 0.1 cm/s\n  - At void ratio e ≈ 1, K ≈ 0.01 cm/s\n  - At void ratio e ≈ 0.1, K ≈ 0.001 cm/s\n\n- For Berea Sandstone:\n  - At void ratio e ≈ 10, K ≈ 0.01 cm/s\n  - At void ratio e ≈ 1, K ≈ 0.001 cm/s\n  - At void ratio e ≈ 0.1, K ≈ 0.0001 cm/s\n\n- For Hygiene Sandstone and Pierre Formation:\n  - At void ratio e ≈ 10, K ≈ 0.001 cm/s\n  - At void ratio e ≈ 1, K ≈ 0.0001 cm/s\n  - At void ratio e ≈ 0.1, K ≈ 0.00001 cm/s\n\nThe plot indicates that as the void ratio decreases, the hydraulic conductivity decreases for all materials. The Fragmented Mixture exhibits the highest hydraulic conductivity across the range of void ratios, followed by Berea Sandstone, and then Hygiene Sandstone and Pierre Formation, which show the lowest hydraulic conductivity."}**

Figure 6. Predicted wetting phase relative permeability as a function of capillary pressure head compared with experimental data.

![img-13.jpeg](None)

**{"image_type": "plot", "description": "The image is a plot showing the relationship between the ratio of hydraulic conductivity (k) to initial hydraulic conductivity (k₀) on the Y-axis and the ratio of volumetric water content (θ) to initial volumetric water content (θ₀) on the X-axis. The X-axis ranges from 0 to 1, and the Y-axis ranges from 0 to 1. The curve demonstrates a decreasing trend, indicating that as the volumetric water content ratio (θ/θ₀) decreases, the hydraulic conductivity ratio (k/k₀) also decreases. Key data points approximated from the plot are:\n- (θ/θ₀ = 1.0, k/k₀ = 1.0)\n- (θ/θ₀ ≈ 0.8, k/k₀ ≈ 0.6)\n- (θ/θ₀ ≈ 0.6, k/k₀ ≈ 0.3)\n- (θ/θ₀ ≈ 0.4, k/k₀ ≈ 0.15)\n- (θ/θ₀ ≈ 0.2, k/k₀ ≈ 0.05)\n- (θ/θ₀ = 0.0, k/k₀ = 0.0)\nThe plot is labeled 'Volcanic Sand' at the top, suggesting the data pertains to volcanic sand samples."}**

![img-14.jpeg](None)

**{"image_type": "plot", "description": "The image is a plot titled 'Glass Beads'. The X-axis is labeled 'θ' and ranges from 0 to 10. The Y-axis is labeled 'θ / x 0.5' and ranges from 0 to 1.0. The plot shows a curve that starts at the top left (θ / x 0.5 ≈ 1.0 when θ ≈ 0) and decreases exponentially as θ increases, approaching 0 as θ approaches 10. The data points (represented by open circles) closely follow the curve, indicating a strong fit. Key observations include:\n- At θ ≈ 1, θ / x 0.5 ≈ 0.7\n- At θ ≈ 3, θ / x 0.5 ≈ 0.4\n- At θ ≈ 5, θ / x 0.5 ≈ 0.25\n- At θ ≈ 7, θ / x 0.5 ≈ 0.15\n- At θ ≈ 9, θ / x 0.5 ≈ 0.05\n\nThe trend suggests an inverse relationship between θ and θ / x 0.5, likely following an exponential decay model."}**

![img-15.jpeg](None)

**{"image_type": "plot", "description": "Das Diagramm zeigt eine Kurve, die die Beziehung zwischen der Porosität (y-Achse, beschriftet mit 'n') und dem Verhältnis von Porenzahl zu Porosität (x-Achse, beschriftet mit 'e/(1+e)') für feinen Sand (G.E. No. 1) darstellt. Die y-Achse reicht von 0 bis 0,5, während die x-Achse von 0 bis 1 skaliert ist. Die Kurve zeigt einen abnehmenden, nicht-linearen Trend: Mit zunehmendem Verhältnis von Porenzahl zu Porosität nimmt die Porosität ab. Es sind keine spezifischen Datenpunkte markiert, aber der allgemeine Verlauf der Kurve ist glatt und kontinuierlich."}**

![img-16.jpeg](None)

**{"image_type": "plot", "description": "The image is a plot showing the relationship between two variables, labeled as 's' on the X-axis and 'e' on the Y-axis. The X-axis ranges from 0 to 1.0, and the Y-axis ranges from 0 to approximately 3.5. The plot depicts a downward-sloping curve, indicating an inverse relationship between 's' and 'e'. Key data points approximated from the curve are:\n- At s = 0.0, e ≈ 3.5\n- At s = 0.1, e ≈ 3.0\n- At s = 0.2, e ≈ 2.5\n- At s = 0.3, e ≈ 2.0\n- At s = 0.4, e ≈ 1.5\n- At s = 0.5, e ≈ 1.0\n- At s = 0.6, e ≈ 0.7\n- At s = 0.7, e ≈ 0.4\n- At s = 0.8, e ≈ 0.2\n- At s = 0.9, e ≈ 0.1\n- At s = 1.0, e ≈ 0.0\n\nThe plot is titled 'Toeplitz Silt Loam (G.E. No. 3)' and includes a small inset labeled '(d)' in the bottom-left corner."}**

![img-17.jpeg](None)

**{"image_type": "plot", "description": "The image is a plot titled 'Fragmented Mixture' showing the relationship between two variables, S (on the x-axis) and k (on the y-axis). The x-axis ranges from 0 to 1, and the y-axis ranges from 0 to 1. The plot depicts a decreasing trend where k decreases as S increases. Key data points approximated from the plot are:\n- At S = 0, k ≈ 1.0\n- At S ≈ 0.2, k ≈ 0.8\n- At S ≈ 0.4, k ≈ 0.6\n- At S ≈ 0.6, k ≈ 0.4\n- At S ≈ 0.8, k ≈ 0.2\n- At S = 1.0, k ≈ 0.0\n\nThe curve suggests an inverse relationship between S and k, likely following a nonlinear (possibly exponential or polynomial) decay."}**

Figure 7. Theoretical curves and experimental data of nonwetting phase relative permeability as a function of saturation for unconsolidated porous materials.

![img-18.jpeg](None)

**{"image_type": "plot", "description": "The plot shows the relationship between the variable S (x-axis) and the variable k_r (y-axis) for Berea Sandstone. The x-axis ranges from 0 to 1.0, and the y-axis ranges from 0 to 1.0. The plot includes two curves:\n\n1. A curve labeled (n, w_k) that starts at (0, 1.0) and decreases non-linearly to (1.0, 0).\n2. A curve labeled (w_k) that starts at (0, 0) and increases non-linearly to (1.0, 1.0).\n\nKey observations:\n- The two curves intersect at approximately S = 0.5 and k_r ≈ 0.5.\n- The curve (n, w_k) represents a decreasing trend, while the curve (w_k) represents an increasing trend.\n- Data points (open circles) are plotted along the (n, w_k) curve, showing experimental or simulated values.\n\nAxes labels:\n- X-axis: S (dimensionless, ranging from 0 to 1.0)\n- Y-axis: k_r (dimensionless, ranging from 0 to 1.0)"}**

![img-19.jpeg](None)

**{"image_type": "plot", "description": "The plot shows a relationship between two variables, S (x-axis) and R (y-axis). The x-axis ranges from 0 to 1, and the y-axis ranges from 0 to 1. The curve has a distinct V-shape with a sharp minimum at S ≈ 0.5 and R ≈ 0. The curve is labeled with two points: (n,w) near the left branch and (w) near the right branch. The left side of the plot (S < 0.5) is labeled 'Hygiene,' and the right side (S > 0.5) is labeled 'Sandstone.' The trend indicates that R decreases sharply as S approaches 0.5 from either side, reaching a minimum at S = 0.5, and then increases symmetrically on both sides. Key approximate data points include: (0, 1), (0.25, 0.5), (0.5, 0), (0.75, 0.5), and (1, 1)."}**

Figure 8. Theoretical curves and experimental data for relative permeabilities of the nonwetting (nw) and wetting (w) phases as a function of saturation for two consolidated sandstones.

isotropy and to eliminate boundary effects entirely in the air permeability cell.

It is practically certain that boundary conditions did affect the measurement of $K_w$ in the column permeameters used for unconsolidated media. This is evident because the value of $K_w$ was often higher than the maximum values of $K_{nw}$ measured in the air permeameter even when the porosity of the medium was the same. If the reverse had been true, the result could have been attributed to gas slippage. But the higher value of $K_w$ can only be attributed to a lesser resistance along the boundary in the rigid column as compared to the cell with the pressurized sleeve.

An unrealistically high value of $K_w$ should not affect the measured values of $\eta$ but would affect the absolute values of $K_{rw}$.

In the case of the consolidated sandstones, it was possible to check equations (13), (14), (15), and (16) on exactly the same medium because in this case there was no chance of a change in $P_c/\gamma = f(S)$ for the two experiments. The results are shown in figure 8. The measurements, in the case of the Hygiene Sandstone, are in nearly perfect agreement with the theory for both the nonwetting and wetting relative permeability curves.

For Berea Sandstone, however, the values of $K_{rnw}$ are much smaller than predicted. They are, in fact, zero at values of S corresponding to capillary pressures much larger than the predicted

bubbling pressure. This is undoubtedly a result of anisotropy since finer-textured layers block the flow of air.

Evidently, the $K_{rw}$ curves are much less sensitive to this kind of anisotropy because the $K_{rw}$ curve is in reasonably close agreement with the predicted curve.

It will be noted from figure 2 that materials with secondary porosity have smaller values of $\lambda$ (and thus smaller values of $\eta$) than materials without secondary porosity. This can be seen most distinctly by the contrast in the slope of the curve for volcanic sand and that for glass beads shown in figure 2. The practical significance of this phenomenon is discussed in the section to follow.

The authors have made measurements of $K_{rw}$ as a function of $P_c/\gamma$ for one sample of fragmented clay (see Table #2--Fragmented Lamberg Clay, Appendix III) which has a value of $\eta$ of 3.6, indicating a value of $\lambda$ of 0.53. They have also computed values of $\eta$ from capillary pressure versus saturation curves which were only slightly greater than 2.0, the theoretical lower limit.* The lowest predicted values of $\eta$ were obtained on samples of very fine-grained consolidated rocks containing much clay but having some larger pores because of cracks and vugular spaces.

* Unpublished private report: "Evaluation of Capillary-Pressure Field Data" by A. T. Corey. Petroleum Research Corp., Denver, Colorado.

# SIMILITUDE REQUIREMENTS

Miller and Miller [13] have described the requirements for similitude of isotropic porous systems containing two immiscible fluid phases (air and water) in which the air pressure is considered to be constant but both air and water are continuous phases. In this case, flow of only the liquid phase is considered.

The same assumptions made by Miller and Miller are accepted in the following analysis. This analysis is in many respects the same as theirs but it is restricted to the drainage cycle in order to avoid the complication of hysteresis. In addition, the theoretical functional relationships among $P_c$, $S_e$, $K_{rw}$, and $K_{rnw}$ are used to simplify the resulting expressions for the criteria of similitude.

An equation describing the flow and macroscopic distribution of the liquid is derived by combining Darcy's law with the equation of continuity applicable to flow in porous media. The continuity equation is

$$\text{div } q = -\phi_e \frac{\partial S_e}{\partial t} \tag{18}$$

where $\phi_e$ is the "effective porosity". The effective porosity is similar if not identical to the "drainable porosity" commonly employed by drainage engineers and is used here in order to be consistent with the use of the effective saturation $S_e$. The effective porosity, $\phi_e$, is related to $\phi$ by the relation:

$$\phi_e = (1 - S_r) \phi \tag{19}$$

The result of combining Darcy's law with equation (18) is

$$\text{div} \left[ \frac{\gamma K_e}{\mu} \nabla \left( \frac{P}{\gamma} + Z \right) \right] = \phi_e \frac{\partial S_e}{\partial t} \tag{20}$$

which is essentially the equation first derived by L. A. Richards [17].

Equation (20) is next written in a dimensionless form by scaling the variables appearing in the equation. The variables can be scaled by choosing standard units of permeability, length, pressure and time which are known to be significant characteristics of the system. The standard units are designated as $K_o$, $L_o$, $P_o$, and $t_o$ respectively. The standard unit $K_o$ is simply the fully saturated (maximum) permeability $K$ of the medium under consideration. Using the standard units as scaling factors, equation (20) becomes

$$\frac{t_o K_o \gamma}{L_o \mu \phi_e} \text{ Div.} \left[ K_r \nabla \cdot \left( \frac{P}{P_o} + \frac{Z \gamma}{P_o} \right) \right] = \frac{\partial S_e}{\partial (t/t_o)} \tag{21}$$

where the dots after the divergence and gradient operator symbols indicate that the operations are performed with respect to scaled coordinate lengths.

Equation (21) can be simplified by choosing appropriate system parameters as the standard

units $P_o$, $L_o$, and $t_o$. An obvious choice for $P_o$ is the bubbling pressure $P_b$. If $P_b$ is chosen as the standard unit of pressure, it is necessary to use $P_b/\gamma$ as the standard unit of length. Similarly, the appropriate standard unit of time is $\phi_e P_b \mu / K \gamma^2$. Scaled variables of pressure, length, and time are obtained by dividing the unscaled variables by their respective standard units.

Substituting the standard units into equation (21) gives

$$\text{Div.} \left[ K_r \nabla \cdot (P_o + Z_o) \right] = \frac{\partial S_e}{\partial t} \tag{22}$$

where the dots designate scaled variables or operators with respect to scaled variables.

Equation (22) will yield identical particular solutions in terms of scaled variables provided that:

1. Geometric similitude exists.
2. The boundary and initial conditions in terms of scaled variables are identical.
3. The functional relationships among \( K_{r} \), \( S_{e} \), and \( P_{c} / P_{b} \) are identical for both systems.

The macroscopic boundary conditions can be identical only if corresponding lengths which are characteristic of the macroscopic size of the system are identical multiples of the length $P_b/\gamma$. If two systems are geometrically similar in a macroscopic sense, it is necessary to choose only one characteristic length "L" and the size requirement is satisfied if the ratio $P_b/\gamma L$ is identical for any two systems under consideration.

From the theory and experimental verification presented in the preceding sections, it is evident that the last requirement is satisfied if the pore-size distribution indexes $\lambda$ are identical. It will be noted that $\lambda$ is a function of the microscopic geometry of the porous media. Use of $\lambda$ as a criterion of similitude eliminates the need for explicit consideration of other microscopic geometric variables such as were suggested by Miller and Miller [13]. Furthermore, $P_b$ is a function not only of the size of the pores but also of the interfacial forces, contact angle, shape, etc. Use of $P_b/\gamma$ as a unit of length eliminates the necessity of explicit consideration of the similitude with respect to these variables.

The foregoing analysis indicates that a valid model involving flow of liquid in a partially saturated porous medium requires the following:

1. The medium must have the same pore-size distribution index, \(\lambda\).
2. The macroscopic boundaries of the model must have a shape and orientation similar to the prototype.

3. The size of the model must be such that $\gamma L/P_b$ is the same as for the prototype.

4. The initial conditions in terms of scaled time, i.e., $t K \gamma^2/P_b \mu \phi_e$ must be the same for model as for the prototype.

If the prototype involves steady state flow only, the last of these requirements can be eliminated. If the saturation in any part of a system increases as well as decreases with time, it is possible that additional requirements may enter. It is possible, also, that if the system contains a discontinuous gas phase, the requirements listed may not be sufficient for similitude, especially if a region of increasing liquid saturation exists.

There is a possibility, however, that even when hysteresis is a factor, $\lambda$ may be sufficient to describe the pertinent microscopic geometric properties. This possibility is discussed in the section dealing with hysteresis.

One difficult aspect of creating a valid model is finding a porous medium having the appropriate value of $\lambda$ and at the same time having a sufficiently small value of $P_b/\gamma$ such that the model can be of a practical size. It is easy to find coarse sands or gravels having a small value of $P_b/\gamma$ but as indicated earlier and as discussed by Rahman [15], these will have a narrow range of pore sizes (large $\lambda$) regardless of the range of grain sizes used. Unfortunately, most prototype media of engineering interest have smaller values of $\lambda$. One possibility of overcoming this difficulty would be the use of stable aggregates such as crushed sandstone or naturally occurring volcanic soil.

As can be seen from the values of $\lambda$ tabulated in Appendix III (Table 2), these materials have pore-size distribution indexes in the same range as soil with structure. They can have, moreover, values of $P_b$ as small as desired.

It should be noted that equation (20) could have been written in terms of S and $\phi$, rather than $S_e$ and $\phi_e$. If the variables are expressed in

terms of S and $\phi$, however, the parameter $S_r$ becomes an explicit rather than an implicit factor in similitude. The curves of $K_r$ and $K_{r\pi W}$ as a function of S as well as $\phi$ for the model would have to be identical to those for the prototype. Use of the variables $S_e$ and $\phi_e$ reduce the difficulty of meeting the similitude requirements. It is easier to find media having similar functional relationships between relative permeability and $S_e$ than between relative permeability and S because $S_r$ is eliminated as a factor affecting the shape of the curves. Expressing the liquid content of the media as a percentage of dry weight or a percentage of bulk volume makes the requirements even more difficult to satisfy than the use of S.

A model designed in accordance with the theory presented here must be restricted in its application to systems that do not reach saturations less than $S_r$ because the theory is applicable only to saturations greater than $S_r$.

If the problem under investigation is not explicitly concerned with the conditions in the partially saturated zone, the pertinent characteristics of the behavior of the system may not be extremely sensitive to $\lambda$. This might be true, for example, if the partially saturated zone is very narrow compared to the fully saturated zone. In the latter case, it might be possible to ignore $\lambda$ in choosing a medium for a model, but it would still be necessary to consider $P_b/\gamma L$.

When conditions in the partially saturated zone are of explicit concern, it is not possible to ignore $\lambda$. In the latter case, glass beads or clean sands are not suitable materials for modeling systems involving flow in soils with structure. This is clear from the results shown in the preceding section.

For a further discussion of the practical significance of the parameters $P_b/\gamma$ and $\lambda$, specifically in the field of drainage engineering, the reader is referred to a paper by the authors [2] dealing with this subject.

# SIGNIFICANCE OF HYSTERESIS

The preceding discussion has dealt almost entirely with systems in which it is assumed that the saturation of the medium either remains constant or decreases with time. Systems involving an increasing liquid saturation are of equal engineering importance. Unfortunately, the functional relationships among $P_c$, $S$, $K_{rw}$, and $K_{rnw}$ are usually not the same on a cycle of increasing $S$ as on a cycle of decreasing $S$. The reason for this has been discussed by Miller and Miller [13].

A question that needs to be answered is whether the criteria of similitude suggested in the preceding section are sufficient when hysteresis may be involved. In order to gain some insight into this problem, the authors made an investigation of $K_{rw}$ as a function of $P_c$ on the imbibition as well as the drainage cycle. One of the coauthor's students, Larry G. King, has made many measurements of $K_{rw}$ as a function of $P_c$ on the imbibition cycle for his doctorate thesis [10] which is concerned with imbibition. An example of his data is presented in figure 9.

A detailed description of how these data were obtained is given in the thesis by King. Briefly, a soil column similar to those used by the authors was initially packed with dry soil. Relative liquid permeabilities as a function of capillary pressure first were obtained on the imbibition cycle until the saturation apparently reached a maximum. The measurements were then obtained as the column was drained. Afterwards, the column was vacuum-saturated and measurements were made as the column was drained from the completely saturated state. In other experiments, King first vacuum saturated the column and after making measurements on the drainage cycle resaturated the column by imbibition.

There are several noteworthy observations that can be made from King's data, i. e.,

1. The slope of the curves of $K_{rw}$ as a func-

tion of $P_c$ are practically the same for both the drainage and imbibition cycle.

2. When a medium is resaturated or drained from a state which is neither completely dry nor fully saturated with liquid, the curves do not follow an intermediate path between the drainage or imbibition curves. Instead (after a short transition) the curves jump from one to the other of the two possible paths.

3. The values of $K_{ew}$ on the imbibition cycle tend to approach a maximum of about 0.45 - 0.50 of that obtained when the medium is vacuum saturated. At this state, the nonwetting phase is air, and it is apparently able to diffuse away with time. The authors have observed a slow increase in $K_{ew}$ with time at a constant value of $P_c$, the rate of increase being more rapid for fine material than for sands. In time, the media become full saturated with liquid by imbibition.

4. At values of $P_c > P_b$, the permeabilities on the drainage cycle are a minimum of one order of magnitude greater than on the imbibition cycle.

From the foregoing observations it would seem that a possibility does exist that the criteria of similitude presented in the preceding section will sometimes be adequate for systems involving hysteresis. At least, this may be true for systems not involving a discontinuous gaseous phase. The possibility will be greatly enhanced if it can be shown that a definite relationship exists among $\lambda$, $P_b$, and the ratio of the permeability on the drainage cycle to that on the imbibition cycle at particular values of $P_c$. Such a relationship, however, remains to be demonstrated.

![img-20.jpeg](None)

**{"image_type": "plot", "description": "The image is a semi-logarithmic plot showing the relationship between relative permeability (K_r) on the Y-axis (logarithmic scale) and capillary pressure (P_c) in millibars (mb) on the X-axis (linear scale). The plot is for Loveland Fine Sand with parameters η = 15.0 and P_b = 16.5 mb.\n\nKey observations:\n- The Y-axis (K_r) ranges from 0.001 to 1.0.\n- The X-axis (P_c) ranges from approximately 1 mb to over 100 mb.\n- The curve shows a sharp decline in relative permeability as capillary pressure increases beyond ~10 mb.\n- At low capillary pressures (below ~10 mb), relative permeability remains close to 1.0.\n- Key data points (approximate):\n  - P_c ≈ 1 mb, K_r ≈ 1.0\n  - P_c ≈ 5 mb, K_r ≈ 0.5\n  - P_c ≈ 10 mb, K_r ≈ 0.1\n  - P_c ≈ 20 mb, K_r ≈ 0.01\n  - P_c ≈ 50 mb, K_r ≈ 0.001\n\nThe plot indicates that relative permeability decreases rapidly with increasing capillary pressure in Loveland Fine Sand."}**

Figure 9. Wetting phase relative permeability as a function of capillary pressure on the imbibition and drainage cycles.

# REFERENCES

1. Averjanov, S. F., About permeability of subsurface soils in case of incomplete saturation. Engineering Collection Vol.VII, 1950, as quoted by P. Ya. Polubarinova Kochina; The Theory of Ground Water Movement. English translation by J. M. Roger DeWiest, 1962, Princeton University Press.

2. Brooks, R. H. and Corey, A. T., Hydraulic properties of porous media and their relation to drainage design, submitted for publication in ASAE transactions.

3. Burdine, N. T., Relative permeability calculations from pore-size distribution data. Trans. AIME, 1952.

4. Carman, P. C., Fluid flow through granular beds. Trans. Inst. Chem. Eng. (London) Vol. 15, 1937.

5. Corey, A. T., The interrelation between gas and oil relative permeabilities. Producer's Monthly, Vol. XIX, No. 1, Nov., 1954.

6. Corey, A. T., Measurement of water and air permeability in unsaturated soil. Soil Science Society of America Proceedings, Vol. 21, No. 1 January-February, 1957.

7. Corey, A. T. and Rathjens, C. H., Effect of stratification on relative permeability. Tech. Note No. 393, Journal of Petroleum Technology, December, 1956.

8. Irmay, S. On the hydraulic conductivity of unsaturated soils. Trans., AGU, Vol. 35, No. 3, June, 1954, p. 463-67.

9. Jackson, R. D., Reginato, R. J.; and Reeves, W. E.; A mechanized device for packing soil columns. U.S.D.A., ARS 41-52, April, 1962.

10. King, L. G., Imbibition of fluids by porous media. A Ph.D. thesis in process, Colorado State University.

11. Kozeny, J., Stz. ber. Akad. Wiss. Wien, Abt. IIa, 136, 1927, as quoted in reference 17.

12. Loomis, A. G., and Crowell, D. C., Relative permeability studies: 1. Gas-oil systems. Producer's Monthly, Vol. 22, No. 11, Sept., 1958.

13. Miller, E. E., and Miller, R. D., Physical theory for capillary flow phenomena. J. Appl. Physics, Vol. 27, 1956.

14. Naar, J. and Wygal, R. J, Structure and properties of unconsolidated aggregates. A manuscript supplied by the Gulf Research and Development Company and submitted for publication to Trans. of the Faraday Society, April 17, 1962.

15. Rahman, Q. H., Permeability and capillary pressure in sands. A masters thesis submitted to the SEATO Graduate School of Engineering, Bangkok, Thailand, 1961.

16. Reeve, R. C., and Brooks, R. H., Equipment for subsampling and packing fragmental soil samples for air and water permeability tests. Soil Sci. Society of Amer. Proc., Vol. 17, 1953.

17. Richards, L. A., Capillary conduction of liquids through porous mediums, Physics 1, 1931.

18. Scott, V. H., and Corey, A. T., Pressure distribution during steady flow in unsaturated sands. Soil Science Society of America Proceedings, Vol. 25, No. 4, July-August, 1961.

19. Wyllie, M. R. J. and Gardner, G. H. F. The generalized Kozeny-Carman Equation. World Oil, March and April, 1958.

20. Wyllie, M. R. J. and Spangler, M. B. Application of electrical resistivity measurements to problem of fluid flow in porous media. Bulletin of the American Association of Petroleum Geologists, Vol. 36, No. 2, February, 1952.

The theory presented below is a variation of theory published in petroleum engineering literature [3, 5, 19, 20]*. It is realized that most irrigation and drainage engineers do not have easy access to this literature. This synopsis is included here, therefore, for the convenience of the readers.

The assumption is made that fluid compressibility and inertia are not significant factors affecting the flow so that the equation of Navier-Stokes reduces to a statement that the gradient of piezometric pressure P* is balanced by the viscous drag. For a Newtonian viscous fluid, this relationship is given by

$$\underline{\nabla} P^* = \mu \nabla^2 \underline{V} \tag{1}$$

where $\underline{V}$ is the total velocity vector. Equation (1) can be solved for particular boundary conditions, e. g., 1-dimensional flow through straight tubes, flow between infinite flat parallel plates, and film flow over an infinite flat plate. The solution of equation (1) for each of these particular boundary conditions will be presented to show how the solutions vary with the shape of the boundary.

Flow through a small diameter tube is considered first. For this geometry it is more convenient to express the quantity $\nabla^2 \underline{V}$ in cylindrical coordinates, i. e.,

$$\underline{\nabla} P^* = \mu \left[ \frac{1}{r} \frac{\partial}{2r} \left( r \frac{\partial V}{\partial r} \right) + \frac{\partial}{\partial \theta} \left( \frac{1}{r} \frac{\partial V}{\partial \theta} \right) + \frac{\partial}{\partial x} \left( r \frac{\partial V}{\partial x} \right) \right]. \tag{2}$$

where r is measured from the centerline of the tube toward the boundary. If the flow is steady, there is no variation in $\underline{V}$ along the tube in the direction x. The last term on the right of equation (2) is, therefore, zero. Because of symmetry, the term involving $\frac{\partial \underline{V}}{\partial \theta}$ is also zero so that finally

$$\underline{\nabla} P^* = \mu \left[ \frac{1}{r} \frac{d}{dr} \left( r \frac{du}{dr} \right) \right] \tag{3}$$

where u is the component of velocity along the tube. Because the flow is laminar, there is no component of $\underline{V}$ perpendicular to x.

Since there is no flow perpendicular to the boundary, $\nabla P^*$ likewise has no component perpendicular to the boundary. This implies that the equipotential lines are planes perpendicular to the axis of the tube. The gradient of P*, therefore, does not depend on r and can be treated as a constant. The variables, u and r, are separable and after integrating once, the relationship

$$\frac{r^2}{2\mu} \nabla P^* = r \frac{du}{dr} + C \tag{4}$$

is obtained. In order for equation (4) to be valid at the centerline where r = 0, the value of C is zero since $\frac{du}{dr}$ cannot be infinitely large. Therefore,

$$\frac{r}{2\mu} \nabla P^* = \frac{du}{dr} \tag{5}$$

After separating the variables, integrating and using the condition that $\frac{du}{dr}$ is finite (which implies the velocity of the fluid approaches the velocity of the boundary at the boundary) then

$$u = \frac{\nabla P^*}{4\mu} (r_t^2 - r^2) \tag{6}$$

where $r_t$ is the radius of the tube.

Integrating the discharge over the entire cross-sectional area of a tube of radius $r_t$ and dividing by the cross-sectional area gives the equation of Poiseuille for the mean velocity, i. e.,

$$\overline{u} = - \frac{r_t^2}{8\mu} \nabla P^* \tag{7}$$

Solving equation (1) for 1-dimensional flow in a flow in a film over a flat plate gives

$$\overline{u} = - \frac{d^2}{3\mu} \nabla P^* \tag{8}$$

where d is the thickness of the film. Similarly,

$$\overline{u} = - \frac{b^2}{12\mu} \nabla P^* \tag{9}$$

for 1-dimensional flow between parallel flat plates where b is the spacing of the plates.

It will be noted that equations (7), (8), and (9) are of a similar form in that $\overline{u}$ is proportional to $\nabla P^*$, and to the square of a length dimension characterizing the size of the flow section. The volume flux is inversely proportional to viscosity and a numerical constant.

By induction, then, an analogous equation applying to straight tubes of uniform cross section of any shape is

$$\overline{u} = - \frac{R^2}{k\mu} \nabla P^* \tag{10}$$

where R is a length characterizing the size of the tube, and k is a numerical constant depending on the shape of the cross section and the dimension chosen to characterize the size.

In applying equation (10) to tubes of irregular shape, the question arises as to what length dimension should be used to characterize the size of the tubes. One possibility is the hydraulic radius, R. It is defined as the cross-sectional area divided by the wetted perimeter.

If equations (7), (8), and (9) are rewritten in terms of R, only the numerical constant is changed. Poiseuille's equation becomes

$$\overline{u} = - \frac{R^2}{2\mu} \nabla P^* \tag{11}$$

and equations (8) and (9) become

$$\overline{u} = - \frac{R^2}{3\mu} \nabla P^* \tag{12}$$

The variation in the constant k is evidently, greatly reduced.

It is reasonable to suppose that (from a hydrodynamic viewpoint) flow in a thin film is about as different from flow in a circular tube as it is possible to obtain. One might conclude, therefore, that the shape factor for irregular cross sections (e.g. the pore space in a porous solid) should be somewhere between 2 and 3. This conclusion would not be valid, however, if the cross section has an extreme "eccentricity". Consider, for example, a cross section as shown in Figure 1. Note that the perimeter of the

![img-21.jpeg](None)

**{"image_type": "diagram", "description": "A simple schematic diagram showing a curved pipe or tube with a slight bend. The diagram consists of a single line forming a loop with one end extending straight and the other end curving back. No additional labels, annotations, or text are present."}**

Figure 1. An Example of a Tube Cross-Section with Extreme Eccentricity.

long extension of the cross section is great but the area is small and the contribution to flow of this part of the area is, relatively, even smaller.

The difficulty is that the distribution of velocity in one part of the cross section is like that in a relatively large tube whereas in the extension, it is like that between closely spaced plates. The large part of the eccentric cross section, therefore, would act as a tube with k ≈ 2 whereas the extension would act as a tube with k ≈ 3. The larger part, however, has a much larger hydraulic radius than the extension. Note that in equation (10), R is squared and k is to the first power. One cannot, therefore, use R for the entire cross section and an average of k to obtain a valid estimate of u̅.

It is much more reasonable to regard the eccentric cross section shown in figure 1 as two separate cross sections. The error resulting from applying an average k of about 2.5 for each cross-section will not be great, but it is necessary to use separate values of R. An alternative method (which will give exactly the same result) is to consider the entire cross section as a whole, using an average k and a mean value of R², designated as R̅².

The tubes considered in developing equation (10) were straight. There is no difficulty in extending the analysis to other than straight tubes provided that the actual length of the tubes can be measured and the direction that any fluid element is moving at any particular location is known. There is an error in such an analysis if the normal acceleration resulting from flow around bends is disregarded. This error is small, however, if the tangential velocity is very small.

If it is desired to determine u̅ as a function of the potential difference between the ends of a tortuous tube and the direct distance between the two ends, the tortuosity will have two effects. The first effect is with respect to u̅. If the direction between the two ends of the tube is defined as the x direction, then u̅ varies from point to point because the direction of the axis of the tube varies, i.e., the component of velocity in the x direction varies even though the magnitude of the velocity remains constant. If |v| is the magnitude of the average tangential velocity, the mean value

of the x component is given by

$$\overline{u} = |\underline{v}| \frac{L}{L_e} \tag{13}$$

where L is the direct distance between the ends of the tube and Lₑ is the length of the tortuous tube. The quantity |v| in equation (13) is analogous to u̅ in equation (10).

The second effect of the tortuosity of the tube is with respect to ∇P*. If it is desired to express the driving force as ∇P*/L, it must be noted that

$$|\overline{\nabla P^*}| = \frac{\nabla P^*}{L} \left(\frac{L}{L_e}\right) \tag{14}$$

where |∇P*| is the absolute value of the mean gradient of P*. An equation relating u̅ to ∇P*/L in a tortuous tube (analogous to equation 10) is, therefore, given by

$$\overline{u} = - \frac{\overline{R^2}}{k\mu(L_e/L)^2} \frac{\nabla P^*}{L} \tag{15}$$

where the quantity (Lₑ/L)² has been called tortuosity and designated by the symbol T.

It is evident that for porous solids of a given porosity the greater the eccentricity of the pore space, the larger will be R̅². This is equivalent to saying that R̅² will be greater for porous solids, having secondary porosity as well as primary porosity, other things being equal. This can be visualized most easily by considering a porous solid containing an abundance of clay. If somehow all of the solid matter could be concentrated into one solid portion of the cross section and the remaining section was free to conduct fluids, the value of K would obviously be much greater than if the clay particles were evenly distributed over the cross section.

Furthermore, the value of R̅² for the non-wetting phase, on the other hand will increase as the saturation increases. The relationship between R̅² for the wetting phase and S can be deduced from a curve of S as a function of Pc; e.g. as shown in figure 1 of the text.

The principle is based on the assumption that a connected cross section of an irregular-shaped tube can be regarded as composed of a large number of sub-sections each having a discrete R. The values of R² of each sub-section are summed and the mean value of R̅² is obtained. The entire pore space filled with the wetting phase is then regarded as a single tube of irregular shape (but uniform cross-sectional area) having an average shape factor k and mean value of hydraulic radius R̅².

Another key assumption of this theory is that to a close approximation,

$$P_c dA = \sigma d(\pi p) \cos \theta \tag{16}$$

where Pc is the capillary pressure at a particular

saturation S, dA is the area of the portion of the cross section of the pore space that would desaturate if S undergoes a change dS at the capillary pressure P_c, d(wp) is the corresponding change in perimeter of the desaturated area at the soil-wetting phase interface, and θ is the angle of contact of the wetting phase at the solid interface. It is further assumed that θ and σ remain constant over the range of saturations considered.

The hydraulic radius of the area dA is, therefore, given by

$$R = \frac{dA}{d(wp)} = \frac{\sigma \cos \theta}{P_c} \tag{17}$$

The mean value of R² for the wetting phase at the saturation S (designated as R̅_w²) is given by

$$\overline{R_w^2} = \frac{\sigma^2 \cos^2 \theta}{S} \int_0^S \frac{dS}{P_c^2} \tag{18}$$

similarly, for the non-wetting phase,

$$\overline{R_{nw}^2} = \frac{\sigma^2 \cos^2 \theta}{1 - S} \int_S^1 \frac{dS}{P_c^2} \tag{19}$$

Although the integral in equation (18) is over the interval of S from 0 to S, for practical purposes it could often just as well be taken over the interval from S_r to S. The value of the integral from 0 to S_r is very small because P_c is very large over this region.

According to Carman [4], the tortuosity of fully saturated porous solids which are isotropic and granular in nature is about 2. Other kinds of porous media may have other values of tortuosity. If, for example, the medium is composed of clay particles oriented perpendicular to the direction of flow, T will be much larger than 2. If the clay is oriented parallel to the flow, T will be smaller than 2.

The variation of tortuosity with S was studied experimentally by Burdine [3] and later analytically by Wyllie and Gardner [19]. Burdine obtained an empirical expression for T (S) in the form

$$\left[ \frac{T_{1,0}}{T_S} \right]_w = \left[ \frac{S - S_r}{1 - S_r} \right]^2 \tag{20}$$

where the subscript w indicates that the relationship applies to the wetting phase. In other words, the quantity L/L_e varies linearly from zero at S = S_r to

1.0 at S = 1.0. This finding was verified by Corey [5] and was later derived by Wyllie and Gardner [19] using a mathematical model of porous solids somewhat different from the model employed here.

The corresponding relationship found by Burdine for the nonwetting phase is

$$\left[ \frac{T_{1,0}}{T_S} \right]_{nw} = \left[ 1 - \frac{S - S_r}{S_c - S_r} \right]^2 \tag{21}$$

where S_c is called the "critical saturation". At

S > S_c, the nonwetting phase is discontinuous.

Corey [5] found for isotropic media that replacing S_c by 1.0 did not materially change the calculated permeabilities for saturations less than S_c.

The volume flux, q, in a porous medium of having a porosity φ is related to the velocity u̅ in the pores by q = u̅ φ S. Thus equation (15) becomes

$$q = \frac{\phi S \overline{R^2}}{k \mu T^2} \frac{v P^*}{L} \tag{22}$$

Noting the similarity between equation (22) and Darcy's Law, it would seem that

$$K_{ew} = \frac{\phi S \overline{R_w^2}(S)}{k T_w^2(S)} \tag{23}$$

in which it is assumed that φ and k are independent of S. Assuming that R̅_w²(S) and T_w(S) are as given by equations (18) and (20) respectively, the equation for the relative permeability of the wetting phase is given by

$$K_{nw} = \left[ \frac{S - S_r}{1 - S_r} \right]^2 \frac{\int_0^S \frac{dS}{P_c^2}}{\int_0^1 \frac{dS}{P_c^2}} \tag{24}$$

similarly, for the nonwetting phase,

$$K_{rnw} = \left[ 1 - \frac{S - S_r}{S_c - S_r} \right]^2 \frac{\int_S^1 \frac{dS}{P_c^2}}{\int_0^1 \frac{dS}{P_c^2}} \tag{25}$$

Equations (24) and (25) are known as Burdine's equations for relative permeability.

In Burdine's equations, the parameters σ², cos²θ, k, and φ cancel. It is possible therefore, that the theory with respect to relative permeability is more precise than with respect to permeability, per se.

It is certainly true that Burdine's theory is of more practical use in determining the dependence of relative permeability on saturation than it is for determining permeabilities. The permeabilities of porous media when occupied fully by only one fluid are easily measured directly. The direct measurement of relative permeability curves is a much more difficult and time-consuming process.

Burdine's equations, however, are applicable only for fairly isotropic media as one would suspect from the manner of their derivation. Anisotropy causes marked departures from the isotropic case as has been described by Corey and Rathjens [7]. The effect of anisotropy depends upon the orientation of the discontinuities in texture. Bedding planes perpendicular to flow tend to decrease the maximum saturation S_c at which the nonwetting phase will flow, and bedding planes parallel to flow tend to increase S_c. Such planes also cause inflection in both K_nw and K_rnw curves.

# Method of Determining Residual Saturation

To determine the pore-size distribution index, λ, it is necessary to plot log Sₑ versus log P꜀ which necessitates determining the residual saturation Sᵣ. Since the saturation, S, is related to Sₑ by the relation

$$S_{e} = \frac{S - S_{r}}{1 - S_{r}} \quad \text{for } S_{r} < S \leq 1.0 \tag{1}$$

it is necessary to have measured values of S as a function of P꜀/γ to determine Sᵣ.

An approximate value of Sᵣ is obtained by selecting a value of S at which the curve of P꜀/γ versus S appears to approach a vertical asymptote as shown in figure 1. With this estimate of Sᵣ, tentative values of log Sₑ are computed and plotted as a function of log P꜀/γ. Usually, the plot will not be a straight line, but an intermediate portion of the computed values will fall on a straight line as shown in figure 2.

A second estimate of Sᵣ is then obtained such that a value of Sₑ, in the high capillary pressure range which does not lie on the straight line, will fall on the straight line as shown in figure 2. The second estimate of Sᵣ is usually adequate, and all of the points will lie sufficiently close to a straight line when the points are recomputed using the new value of Sᵣ. If this is not the case, the process is repeated until a value of Sᵣ is obtained that results in a straight line for most values of P꜀/γ > Pᵦ/γ.

At large values of P꜀/γ where the curve becomes asymptotic to some value of S, Sₑ is very sensitive to the value of Sᵣ chosen, i.e., a small change in Sᵣ makes the change in Sₑ look big on a log-log plot. Therefore, values of Sₑ at this end of the curve that do not lie exactly on the straight line should not be given much consideration in selecting a value of Sᵣ.

![img-22.jpeg](None)

**{"image_type": "plot", "description": "The image is a plot showing the relationship between the variable S (x-axis) and the first estimate of S₁ (y-axis) in centimeters. The x-axis ranges from 0 to 1, while the y-axis ranges from 0 to 150 cm. The plot depicts a curve that starts at a high value (~150 cm) when S is near 0.1, then decreases sharply as S increases to around 0.3. After this point, the curve continues to decline but at a slower rate, approaching a value of approximately 20 cm as S approaches 1.0. The plot includes data points marked with circles along the curve. The trend indicates an inverse relationship between S and the first estimate of S₁, where the first estimate of S₁ decreases rapidly at lower values of S and then levels off as S increases."}**

Fig. 1 Capillary pressure head as a function of saturation

![img-23.jpeg](None)

**{"image_type": "plot", "description": "The image is a semi-logarithmic plot showing the relationship between the effective saturation (S_e) and the capillary pressure (P_c/γ) for fine sand (labeled as GE #13).\n\n- **X-axis (horizontal):** Capillary pressure (P_c/γ) in cm, ranging from 10 to 150.\n- **Y-axis (vertical):** Effective saturation (S_e), ranging from 0.01 to 1.0 on a logarithmic scale.\n\n**Key observations and data points:**\n1. The plot shows a decreasing trend of S_e with increasing P_c/γ, indicating that as capillary pressure increases, effective saturation decreases.\n2. Two estimates of residual saturation (S_r) are provided:\n   - **First estimate (S_r = 0.15):** Indicated by a horizontal dashed line at S_e = 0.15.\n   - **Second estimate (S_r):** Obtained by fitting a computed point on the straight line, calculated as S_r = S_e - (S_e - S_e) (exact formula not fully legible but implies a linear fitting method).\n3. The plot includes computed values of S_e (open circles) and a fitted curve (solid line) representing the trend.\n4. The curve shows a sharp decline in S_e beyond P_c/γ ≈ 40 cm, transitioning from a relatively flat region to a steep drop.\n\n**Approximate key data points (extracted from the plot):**\n- At P_c/γ ≈ 10 cm, S_e ≈ 0.95\n- At P_c/γ ≈ 20 cm, S_e ≈ 0.85\n- At P_c/γ ≈ 40 cm, S_e ≈ 0.50\n- At P_c/γ ≈ 60 cm, S_e ≈ 0.20\n- At P_c/γ ≈ 80 cm, S_e ≈ 0.10\n- At P_c/γ ≈ 100 cm, S_e ≈ 0.05\n- At P_c/γ ≈ 120 cm, S_e ≈ 0.02"}**

Fig. 2 Effective saturation as a function of capillary pressure head

TABLE 1

Data from Air Permeability Cell

for Unconsolidated Samples

|  Volcanic Sand |   |   |   | Fine Sand (G. E. #13) |   |   |   | Fragmented Mixture (granulated clay + fragmented sandstone + volcanic sand)  |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  φ = 0.351 |   | P_{b}/γ = 16.0 cm. |   | φ = 0.377 |   | P_{b}/γ = 41.0 cm. |   | φ = 0.443 |   | P_{b}/γ = 17.2 cm.  |   |
|  K_{nw} = 18.0 μ^{2} |   | S_{r} = 0.157 |   | K_{nw} = 2.5 μ^{2} |   | S_{r} = 0.167 |   | K_{nw} = 11.3 μ^{2} |   | S_{r} = 0.276  |   |
|  λ = 2.29 |   | φ_{e} = 0.296 |   | λ = 3.7 |   | φ_{e} = 0.314 |   | λ = 2.89 |   | φ_{e} = 0.321  |   |
|  P_{c}/γ (cm.) | S | K_{enw} (μ^{2}) | K_{rnw} | P_{c}/γ (cm.) | S | K_{enw} (μ^{2}) | K_{rnw} | P_{c}/γ (cm.) | S | K_{enw} (μ^{2}) | K_{rnw}  |
|  6.9 | 1.00 |  |  | 12.8 | 0.990 |  |  | 10.9 | 0.991 |  |   |
|  8.6 | 1.00 |  |  | 27.8 | 0.980 |  |  | 13.0 | 0.978 |  |   |
|  10.5 | 1.00 |  |  | 30.8 | 0.962 |  |  | 14.1 | 0.969 |  |   |
|  12.0 | 0.990 |  |  | 31.8 | 0.950 | 0.00234 | 0.000935 | 15.0 | 0.962 |  |   |
|  13.5 | 0.986 |  |  | 34.8 | 0.926 | 0.00700 | 0.00280 | 16.0 | 0.951 |  |   |
|  14.5 | 0.980 |  |  | 36.8 | 0.901 | 0.0115 | 0.00460 | 17.0 | 0.924 | 0.021 | 0.00182  |
|  15.5 | 0.974 |  |  | 39.8 | 0.855 | 0.0298 | 0.0119 | 18.4 | 0.871 | 0.173 | 0.0150  |
|  16.0 | 0.948 | 0.0112 | 0.00062 | 42.8 | 0.788 | 0.0808 | 0.032 | 23.6 | 0.562 | 3.14 | 0.278  |
|  17.0 | 0.895 | 0.0720 | 0.0040 | 45.8 | 0.716 | 0.150 | 0.060 | 30.5 | 0.415 | 6.56 | 0.581  |
|  17.2 | 0.875 | 0.123 | 0.0068 | 48.8 | 0.627 | 0.259 | 0.104 | 37.7 | 0.348 | 8.90 | 0.788  |
|  21.0 | 0.638 | 2.10 | 0.117 | 52.8 | 0.503 | 0.486 | 0.194 | 53.7 | 0.303 | 10.4 | 0.920  |
|  24.8 | 0.479 | 5.20 | 0.289 | 57.7 | 0.393 | 0.886 | 0.354 |  |  |  |   |
|  36.9 | 0.277 | 12.1 | 0.672 | 64.8 | 0.314 | 1.39 | 0.556 |  |  |  |   |
|  67.7 | 0.188 | 17.0 | 0.944 | 71.7 | 0.273 | 1.74 | 0.696 |  |  |  |   |
|  136.6 | 0.158 | 17.8 | 0.990 | 74.4 | 0.262 | 1.84 | 0.735 |  |  |  |   |
|   |  |  |  | 92.1 | 0.217 | 2.20 | 0.880 |  |  |  |   |
|   |  |  |  | 150.1 | 0.174 | 2.47 | 0.989 |  |  |  |   |

|  Glass Beads ("3M" #130-5005) |   |   |   | Touchet Silt Loam (G. E. # 3) |   |   |   | Fragmented Fox Hill (1) Sandstone  |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  φ = 0.370 |   | P_{b}/γ = 29.0 cm. |   | φ = 0.485 |   | P_{b}/γ = 75.0 cm. |   | φ = 0.47 |   | P_{b}/γ = 10.3  |   |
|  K_{nw} = 6.30 μ^{2} |   | S_{r} = 0.085 |   | K_{nw} = 0.60 μ^{2} |   | S_{r} = 0.270 |   | K_{nw} = 30.0 μ^{2} |   | S_{r} = 0.30  |   |
|  λ = 7.3 |   | φ_{e} = 0.338 |   | λ = 1.82 |   | φ_{e} = 0.349 |   | λ = 1.92 |   | φ_{e} = 0.329  |   |
|  P_{c}/γ (cm.) | S | K_{enw} (μ^{2}) | K_{rnw} | P_{c}/γ (cm.) | S | K_{enw} (μ^{2}) | K_{rnw} | P_{c}/γ (cm.) | S | K_{enw} (μ^{2}) | K_{rnw}  |
|  3.6 | 1.00 |  |  | 7.8 | 1.00 |  |  | 3.9 | 1.00 |  |   |
|  5.9 | 0.995 |  |  | 12.8 | 1.00 |  |  | 5.9 | 1.00 |  |   |
|  11.8 | 0.989 |  |  | 17.8 | 1.00 |  |  | 7.6 | 0.972 |  |   |
|  17.8 | 0.985 |  |  | 22.8 | 1.00 |  |  | 8.7 | 0.956 | 0.0144 | 0.000480  |
|  23.8 | 0.980 |  |  | 32.8 | 0.998 |  |  | 10.0 | 0.860 | 0.600 | 0.0200  |
|  26.9 | 0.971 |  |  | 42.8 | 0.995 |  |  | 12.4 | 0.776 | 3.20 | 0.107  |
|  28.8 | 0.938 | 0.022 | 0.00352 | 52.8 | 0.992 |  |  | 15.3 | 0.663 | 4.88 | 0.163  |
|  29.3 | 0.912 | 0.060 | 0.00950 | 62.8 | 0.984 |  |  | 17.8 | 0.554 | 9.20 | 0.365  |
|  30.4 | 0.764 | 0.209 | 0.0332 | 67.8 | 0.978 |  |  | 21.5 | 0.465 | 15.7 | 0.523  |
|  31.0 | 0.681 | 0.352 | 0.056 | 72.5 | 0.967 |  |  | 25.6 | 0.416 | 20.0 | 0.667  |
|  32.1 | 0.579 | 0.630 | 0.100 | 77.8 | 0.946 | 0.00360 | 0.00060 | 28.9 | 0.397 | 22.0 | 0.734  |
|  32.7 | 0.465 | 1.140 | 0.181 | 82.3 | 0.892 | 0.0069 | 0.00115 | 33.8 | 0.375 | 23.4 | 0.780  |
|  33.9 | 0.337 | 2.03 | 0.322 | 87.7 | 0.821 | 0.0157 | 0.0262 | 46.6 | 0.339 | 25.4 | 0.846  |
|  35.7 | 0.269 | 2.79 | 0.443 | 97.8 | 0.719 | 0.0506 | 0.0844 | 58.0 | 0.331 | 27.0 | 0.900  |
|  39.0 | 0.190 | 4.09 | 0.649 | 107.6 | 0.641 | 0.105 | 0.175 |  |  |  |   |
|  43.8 | 0.130 | 5.24 | 0.831 | 123.0 | 0.562 | 0.185 | 0.308 |  |  |  |   |
|  53.5 | 0.099 | 6.15 | 0.976 | 142.6 | 0.492 | 0.264 | 0.440 |  |  |  |   |
|  150.4 | 0.097 | 6.26 | 0.995 | 177.0 | 0.424 | 0.359 | 0.600 |  |  |  |   |
|   |  |  |  | 207.2 | 0.383 | 0.418 | 0.695 |  |  |  |   |

# TABLE 2

Data from Liquid Permeameter Columns

for Unconsolidated Samples

|  Volcanic Sand φ = 0.365 P_{b}/γ = 16.8 cm. K_{w} = 11.0 μ² η = 9.0 |   |   |   | Fine Sand (G. E. #13) φ = 0.360 P_{b}/γ = 41.0 cm. K_{w} = 2.85 μ² η = 14.6 |   |   |   | Touchet Silt Loam (G. E. #3) φ = 0.469 P_{b}/γ = 64.0 cm. K_{w} = 0.500 μ² η = 5.6  |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  P_{c}/γ (cm.) | K_{ew} (μ²) | K_{rw} | S | P_{c}/γ (cm.) | K_{ew} (μ²) | K_{rw} | S | P_{c}/γ (cm.) | K_{ew} (μ²) | K_{rw} | S  |
|  6.3 | 11.0 | 1.00 |  | 17.3 | 2.85 | 1.00 |  | 6.10 | 0.500 | 1.00 |   |
|  8.8 | 11.0 | 1.00 |  | 22.0 | 2.85 | 1.00 |  | 6.20 | 0.497 | 1.00 |   |
|  11.9 | 10.75 | 0.980 |  | 25.2 | 2.85 | 1.00 |  | 32.2 | 0.470 | 0.940 |   |
|  13.3 | 9.75 | 0.885 |  | 32.9 | 2.85 | 1.00 |  | 60.0 | 0.364 | 0.728 |   |
|  18.0 | 5.56 | 0.506 |  | 36.9 | 2.62 | 0.92 |  | 72.1 | 0.298 | 0.595 |   |
|  22.2 | 1.26 | 0.114 |  | 41.6 | 2.03 | 0.713 |  | 83.9 | 0.138 | 0.276 |   |
|  29.7 | 0.064 | 0.0058 |  | 44.7 | 1.075 | 0.378 |  | 92.9 | 0.069 | 0.138 |   |
|  40.0 | 0.00545 | 0.00050 |  | 50.9 | 0.128 | 0.045 |  | 101.7 | 0.0325 | 0.065 |   |
|   |  |  |  | 54.9 | 0.0434 | 0.0152 | 0.334 | 124.4 | 0.014 | 0.028 |   |
|   |  |  |  |  |  |  |  | 149.4 | 0.0050 | 0.010 |   |

|  Glass Beads ("3M" #130-5505) φ = .383 P_{b}/γ = 29 cm. K_{w} = 10.5 μ² η = 20 |   |   |   | Fragmented Mixture (granulated clay + fragmented sandstone + volcanic sand) φ = .441 P_{b}/γ = 18.5 cm. K_{w} = 15.0 μ² η = 10.9 |   |   |   | Fragmented Fox Hill (2) Sandstone φ = 0.503 P_{b}/γ = 20.5 cm. K_{w} = 16.1 μ² η = 9.3  |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  P_{c}/γ (cm.) | K_{ew} (μ²) | K_{rw} | S | P_{c}/γ (cm.) | K_{ew} (μ²) | K_{rw} | S | P_{c}/γ (cm.) | K_{w} (μ²) | K_{rw} | S  |
|  10.7 | 10.4 | 1.00 |  | 7.6 | 15.0 | 1.00 |  | 7.85 | 16.1 | 1.0 |   |
|  16.4 | 10.4 | 1.00 |  | 10.2 | 14.9 | 0.993 |  | 11.3 | 16.1 | 1.0 |   |
|  24.8 | 10.6 | 1.00 |  | 12.3 | 14.75 | 0.983 |  | 13.8 | 15.55 | 0.967 |   |
|  28.1 | 9.94 | 0.945 |  | 16.6 | 14.2 | 0.946 |  | 15.4 | 13.1 | 0.815 |   |
|  29.0 | 8.08 | 0.770 |  | 18.7 | 11.8 | 0.786 |  | 17.7 | 11.7 | 0.728 |   |
|  30.0 | 4.80 | 0.457 |  | 22.4 | 1.56 | 0.104 |  | 22.2 | 7.74 | 0.48 |   |
|  30.5 | 2.67 | 0.254 |  | 24.3 | 0.721 | 0.048 |  | 27.2 | 1.68 | 0.104 |   |
|  31.2 | 1.485 | 0.141 |  | 24.2 | 0.672 | 0.045 |  | 31.0 | 0.32 | 0.021 |   |
|  32.8 | 0.523 | 0.0498 |  | 27.5 | 0.189 | 0.0125 |  | 37.5 | 0.057 | 0.0036 |   |
|  32.9 | 0.363 | 0.0346 |  | 34.2 | 0.0191 | 0.00127 | 0.376 | 43.1 | 0.0187 | 0.0012 | 0.358  |
|  37.1 | 0.0925 | 0.0088 |  |  |  |  |  |  |  |  |   |
|  37.2 | 0.057 | 0.0054 |  |  |  |  |  |  |  |  |   |
|  38.6 | 0.042 | 0.0040 |  |  |  |  |  |  |  |  |   |
|  42.6 | 0.0170 | 0.0016 |  |  |  |  |  |  |  |  |   |
|  43.0 | 0.0104 | 0.0010 | 0.117 |  |  |  |  |  |  |  |   |

|  Fragmented Lamberg Clay K_{w} = 2.2 μ² P_{b}/γ = 17.5 cm. η = 3.6 |   |   |   | Sand (G. E. #2) K_{w} = 3.05 μ² P_{b}/γ = 38 cm. η = 10.0 |   |   |   | Sand (USSL #3445) K_{w} = 1.48 μ² P_{b}/γ = 43 cm. η = 10.1  |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  P_{c}/γ (cm.) | K_{ew} (μ²) | K_{rw} | S | P_{c}/γ (cm.) | K_{ew} (μ²) | K_{rw} | S | P_{c}/γ (cm.) | K_{ew} (μ²) | K_{rw} | S  |
|  4.50 | 2.20 | 1.00 |  | 4.8 | 3.05 | 1.000 |  | 29.2 | 1.480 | 1.00 |   |
|  7.02 | 2.11 | 0.96 |  | 14.6 | 3.03 | 0.993 |  | 43.6 | 1.100 | 0.743 |   |
|  18.10 | 1.225 | 0.544 |  | 21.9 | 2.39 | 0.784 |  | 52.4 | 0.218 | 0.147 |   |
|  37.4 | 0.142 | 0.0645 |  | 28.8 | 2.14 | 0.705 |  | 66.2 | 0.0188 | 0.0127 |   |
|  38.5 | 0.130 | 0.0590 |  | 37.1 | 1.385 | 0.454 |  | 67.6 | 0.0184 | 0.0124 |   |
|  69.5 | 0.0145 | 0.007 |  | 42.9 | 0.783 | 0.257 |  | 73.6 | 0.0072 | 0.0049 |   |
|   |  |  |  | 46.6 | 0.430 | 0.141 |  |  |  |  |   |
|   |  |  |  | 51.1 | 0.160 | 0.0525 |  |  |  |  |   |
|   |  |  |  | 60.5 | 0.0334 | 0.01095 |  |  |  |  |   |

TABLE 3

Data from Liquid Permeameter for

Consolidated Rock Cores

|  Berea Sandstone (Core perpendicular to bedding planes) |   |   |   | Hygiene Sandstone from Pierre formation (No visible bedding planes)  |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  φ = 0.206 |   | P_{b}/γ = 42.0 cm. |   | φ = 0.250 |   | P_{b}/γ = 54.0 cm.  |   |
|  K_{w} = 0.481 μ^{2} |   | η = 11.1 |   | K_{w} = 0.178 μ^{2} |   | η = 14.1  |   |
|  P_{c}/γ (cm.) | S | K_{ew} (μ^{2}) | K_{rnw} | P_{c}/γ (cm.) | S | K_{ew} (μ^{2}) | K_{rnw}  |
|  11.5 | 1.00 | 0.484 | 1.00 | 13.3 | 1.00 | 0.178 | 1.00  |
|  20.5 | 1.00 | 0.481 | 1.00 | 18.4 | 1.00 | 0.178 | 1.00  |
|  31.9 | 0.990 | 0.469 | 0.976 | 27.4 | 1.00 | 0.177 | 1.00  |
|  35.9 | 0.985 | 0.458 | 0.955 | 44.9 | 0.995 | 0.175 | 0.985  |
|  43.7 | 0.926 | 0.333 | 0.695 | 51.3 | 0.975 | 0.161 | 0.904  |
|  48.0 | 0.778 | 0.095 | 0.197 | 54.1 | 0.960 | 0.135 | 0.814  |
|  50.2 | 0.706 | 0.0475 | 0.0990 | 56.6 | 0.920 | 0.0950 | 0.530  |
|  62.4 | 0.476 | 0.00450 | 0.00930 | 59.3 | 0.865 | 0.047 | 0.265  |
|  88.4 | 0.345 |  |  | 62.1 | 0.817 | 0.026 | 0.144  |
|  116.9 | 0.313 |  |  | 67.7 | 0.756 | 0.0077 | 0.043  |
|   |  |  |  | 75.1 | 0.690 | 0.0020 | 0.0110  |
|   |  |  |  | 85.2 | 0.643 |  |   |
|   |  |  |  | 100.6 | 0.604 |  |   |

TABLE 4

Data from Air Permeameter for

Consolidated Rock Cores

|  Berea Sandstone (Core cut perpendicular to visible bedding planes) |   |   |   | Hygiene Sandstone from Pierre Formation (No visible bedding planes)  |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  φ = 0.206 |   | P_{b}/γ = 43 cm. |   | φ = 0.250 |   | P_{b}/γ = 54 cm.  |   |
|  K_{nw} = 0.348 μ^{2} |   | S_{r} = 0.299 |   | K_{nw} = 0.128 μ^{2} |   | S_{r} = 0.577  |   |
|  λ = 3.69 |   | φ_{e} = 0.144 |   | λ = 4.17 |   | φ_{e} = 0.106  |   |
|  P_{c}/γ (cm.) | S | K_{enw} (μ^{2}) | K_{rnw} | P_{c}/γ (cm.) | S | K_{enw} (μ^{2}) | K_{rnw}  |
|  dry | 0.00 | 0.496 | 1.42 | dry | 0.000 | 0.171 |   |
|  51.0 | 0.687 | 0.00190 | 0.00545 | 57.0 | 0.905 | 0.00126 | 0.00985  |
|  51.5 | 0.663 | 0.00352 | 0.0101 | 57.8 | 0.890 | 0.00300 | 0.0234  |
|  52.4 | 0.643 | 0.00437 | 0.0126 | 59.0 | 0.865 | 0.00580 | 0.0453  |
|  54.0 | 0.610 | 0.00825 | 0.0237 | 62.0 | 0.813 | 0.0150 | 0.117  |
|  56.6 | 0.556 | 0.0284 | 0.0816 | 64.4 | 0.785 | 0.0217 | 0.169  |
|  57.5 | 0.540 | 0.0407 | 0.117 | 67.5 | 0.757 | 0.0294 | 0.230  |
|  59.3 | 0.513 | 0.0648 | 0.186 | 70.8 | 0.723 | 0.0450 | 0.352  |
|  62.5 | 0.473 | 0.104 | 0.299 | 75.1 | 0.690 | 0.0600 | 0.469  |
|  67.5 | 0.434 | 0.148 | 0.425 | 85.2 | 0.643 | 0.0820 | 0.640  |
|  74.3 | 0.392 | 0.213 | 0.611 | 100.6 | 0.604 | 0.104 | 0.813  |
|  85.0 | 0.350 | 0.287 | 0.825 |  |  |  |   |
|  117.0 | 0.318 | 0.330 | 0.948 |  |  |  |   |
|   | 0.244 | 0.425 | 1.22 |  |  |  |   |
|   | 0.175 | 0.469 | 1.35 |  |  |  |   |

|  Key Words: Theory, Saturation, Porous Media, Capillary Pressure, Air Permeability, Liquid Permeability, Similitude Requirements, Nonwetting, Wetting, Darcy's Law Abstract: Following the Burdine approach, a theory is presented that develops the functional relationships among saturation, pressure difference, and the permeabilities of air and liquid in terms of hydraulic properties of partially saturated porous media. Procedures for determining these hydraulic properties from capillary pressure - desaturation curves are described. Air (Abstract continued on reverse side) Reference: Brooks, R. H., and Corey, A. T., Colorado State University, Hydrology Papers No. 3 (March 1964) "Hydraulic Properties of Porous Media" | Key Words: Theory, Saturation, Porous Media, Capillary Pressure, Air Permeability, Liquid Permeability, Similitude Requirements, Nonwetting, Wetting, Darcy's Law Abstract: Following the Burdine approach, a theory is presented that develops the functional relationships among saturation, pressure difference, and the permeabilities of air and liquid in terms of hydraulic properties of partially saturated porous media. Procedures for determining these hydraulic properties from capillary pressure - desaturation curves are described. Air (Abstract continued on reverse side) Reference: Brooks, R. H., and Corey, A. T., Colorado State University, Hydrology Papers No. 3 (March 1964) "Hydraulic Properties of Porous Media"  |
| --- | --- |
|  Key Words: Theory, Saturation, Porous Media, Capillary Pressure, Air Permeability, Liquid Permeability, Similitude Requirements, Nonwetting, Wetting, Darcy's Law Abstract: Following the Burdine approach, a theory is presented that develops the functional relationships among saturation, pressure difference, and the permeabilities of air and liquid in terms of hydraulic properties of partially saturated porous media. Procedures for determining these hydraulic properties from capillary pressure - desaturation curves are described. Air (Abstract continued on reverse side) Reference: Brooks, R. H., and Corey, A. T., Colorado State University, Hydrology Papers No. 3 (March 1964) "Hydraulic Properties of Porous Media" | Key Words: Theory, Saturation, Porous Media, Capillary Pressure, Air Permeability, Liquid Permeability, Similitude Requirements, Nonwetting, Wetting, Darcy's Law Abstract: Following the Burdine approach, a theory is presented that develops the functional relationships among saturation, pressure difference, and the permeabilities of air and liquid in terms of hydraulic properties of partially saturated porous media. Procedures for determining these hydraulic properties from capillary pressure - desaturation curves are described. Air (Abstract continued on reverse side) Reference: Brooks, R. H., and Corey, A. T., Colorado State University, Hydrology Papers No. 3 (March 1964) "Hydraulic Properties of Porous Media"  |

and liquid permeabilities as a function of saturation
and capillary pressure are predicted from experimentally
determined hydraulic properties. The theory also describes the requirements for similitude between any two
flow systems in porous media when occupied by two immiscible fluid phases when the nonwetting phase is static
and the flow of the wetting phase is described by Darcy's
law. The requirements for similitude are also expressed
in terms of the hydraulic properties of porous media.

and liquid permeabilities as a function of saturation
and capillary pressure are predicted from experimentally
determined hydraulic properties. The theory also describes the requirements for similitude between any two
flow systems in porous media when occupied by two immiscible fluid phases when the nonwetting phase is static
and the flow of the wetting phase is described by Darcy's
law. The requirements for similitude are also expressed
in terms of the hydraulic properties of porous media.

and liquid permeabilities as a function of saturation
and capillary pressure are predicted from experimentally
determined hydraulic properties. The theory also describes the requirements for similitude between any two
flow systems in porous media when occupied by two immiscible fluid phases when the nonwetting phase is static
and the flow of the wetting phase is described by Darcy's
law. The requirements for similitude are also expressed
in terms of the hydraulic properties of porous media.

and liquid permeabilities as a function of saturation
and capillary pressure are predicted from experimentally
determined hydraulic properties. The theory also describes the requirements for similitude between any two
flow systems in porous media when occupied by two immiscible fluid phases when the nonwetting phase is static
and the flow of the wetting phase is described by Darcy's
law. The requirements for similitude are also expressed
in terms of the hydraulic properties of porous media.

# PREVIOUSLY PUBLISHED PAPERS

# Colorado State University Hydrology Papers

No. 1. "Fluctuations of Wet and Dry Years, Part I, Research Data Assembly and Mathematical Models," by Vujica M. Yevdjevich, July 1963.

No. 2. "Evaluation of Solar Beam Irradiation as a Climatic Parameter of Mountain Watersheds," by Richard Lee, August 1963.

# Colorado State University Fluid Mechanics Papers

No. 1. "A Resistance Thermometer for Transient Temperature Measurements," by J. L. Chao and V. A. Sandborn, March 1964.

No. 2. "Measurement of Turbulence in Water by Electrokinetic Transducers," by J. E. Cermak and L. V. Baldwin, April 1964.