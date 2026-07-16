# SOME STEADY-STATE SOLUTIONS OF THE UNSATURATED MOISTURE FLOW EQUATION WITH APPLICATION TO EVAPORATION FROM A WATER TABLE

W. R. GARDNER

U. S. Department of Agriculture¹

Received for publication April 12, 1957

There is increasing indication that the flow of water in the liquid phase in a soil which is not saturated may be described by the equation

$$\frac{\partial \theta}{\partial t} = \nabla \cdot k \nabla \phi \tag{1}$$

where $\theta$ is the water content on a volume basis, $t$ is the time, $k$ is the capillary conductivity, and $\phi$ is a potential function (1, 5, 7). This potential is the sum of pressure potential or suction potential, $\psi$, and a gravitational potential $\rho g z$, where $\rho$ is the density of water, $z$ the vertical coordinate, and $g$ the gravitational force per unit mass. It is convenient to express the potential gradient relative to the gravitational force, so the potential may be taken as $\phi = \frac{\psi}{\rho g} + z = -S + z$ where $S$ is the suction head. The dimensions of $k$ are chosen accordingly. Thus, with the density of water assumed to be 1 g./cc., equation (1) becomes, in e.g.s. units,

$$\frac{\partial \theta}{\partial t} = -\nabla \cdot k \nabla S + \frac{\partial k}{\partial z} \tag{2}$$

If the soil is homogeneous, equation (1) may be written in the form of a diffusion equation:

$$\frac{\partial \theta}{\partial t} = \nabla \cdot D \nabla \theta + \frac{\partial k}{\partial z} \tag{3}$$

It can be seen that the diffusivity $D$ is related to the capillary conductivity by the expression $D = -k dS/d\theta$. In order to solve equations (2) or (3) for any given boundary conditions the relations

¹ Contribution from the U. S. Salinity Laboratory, Soil and Water Conservation Research Branch, Agricultural Research Service, U. S. Department of Agriculture, Riverside, California, in cooperation with the 17 western states and the Territory of Hawaii.

between $\theta$, $S$, and $k$ must be known. Because these relations are complicated, numerical methods of solution such as those given by Klute (4) and Philip (6) will often be required. Data on the relation between $k$ and $S$ for several soils obtained by the pressure plate outflow method (2) indicate this relation may be approximated by an analytical expression, making it possible to obtain approximate analytical solutions of the flow equations which will be of use in understanding unsaturated flow phenomena. This is especially true for the steady-state case.

For two- and three-dimensional problems it is helpful to make the transformation:

$$U = \int_{S_0}^{S} k(S) dS \tag{4}$$

The lower limit of the integral can be chosen arbitrarily as convenient. With this transformation, equations (2) and (3) become:

$$\frac{\partial U}{\partial t} = D \nabla^2 U + D \left(\frac{\partial k}{\partial U}\right) \left(\frac{\partial U}{\partial z}\right) \tag{5}$$

For some purposes it may be possible to treat $D$ and $\partial k/\partial U$ as constants in equation (5), making analytical solutions of non-steady-state problems possible. For the steady-state case, $\partial U/\partial t = 0$ and the diffusivity $D$ then factors out. If the gravitational term is negligible, equation (5) reduces to Laplace's equation, for which solutions are readily obtainable for a large variety of boundary conditions. When the gravitational term is not negligible, $U(x, y, z)$ can usually be separated into the product of functions of $x$, $y$, and $z$ alone:

$$U(x, y, z) = X(x) Y(y) Z(z) \tag{6}$$

Substituting (6) into (5) and separating the variable gives:

$$\frac{\partial^2 X}{\partial x^2} = \alpha X \tag{7a}$$

$$\frac{\partial^2 Y}{\partial y^2} = \gamma Y \tag{7b}$$

$$\frac{\partial^2 Z}{\partial z^2} + \left(\frac{\partial k}{\partial U}\right)\left(\frac{\partial Z}{\partial z}\right) + (\alpha + \gamma)Z = 0 \tag{7c}$$

where $\alpha$ and $\gamma$ are arbitrary constants to be evaluated from the boundary conditions. Solutions of (7a) and (7b) are readily obtainable. Solution of equation (7c) will require numerical methods except when the relations between $k$ and $S$ are of certain types. One relation for which an analytical solution is possible is:

$$k(S) = a \exp(-cS) \tag{8}$$

where $a$ and $c$ are constants. In this case $\partial k / \partial U = C$, a constant, and the solution of (7c) is not difficult. For a limited range of values of the suction, equation (8) can be fitted empirically to much of the capillary conductivity data presently available, but it does not hold to well over a wide range of values.

When steady-state flow is in one direction only, it is more convenient to work with equation (2) in terms of the suction head. Setting $\partial \theta / \partial t = 0$ and integrating once:

$$k \left(\frac{dS}{dz} - 1\right) = q \tag{9}$$

where $q$ is a constant and represents the flux. Solving for $z$ yields

$$z = \int \frac{dS}{1 + q/k} \tag{10}$$

Equations (9) and (10) are for vertical flow. If flow is horizontal the term in parentheses in equation (9) is merely $dS/dz$, since the gravitational term drops out.

Equation (10) can be integrated for certain relations between $k$ and $S$. Solutions have been reported by Richards (9) for $k = aS + b$, by Wind (11) for $k = aS^{-2/3}$, and by Remson and Fox (8) for $k = aS^{-1}$. A more general function which seems to fit the available data very well is:

$$k = a / (S^n + b) \tag{11}$$

where $a$, $n$, and $b$ are constants. In general, the coarser the texture of the soil, the larger the value of $n$. For most soils investigated to date,

values of $n$ equal to 2 or 3 give the best fit. Equation (10) can be integrated using equation (11) for values of $n$ equal to 1, 3/2, 2, 3, and 4. Let $\alpha = q/a$ and $\beta = \alpha b + 1$. Normally, $b$ will be small so that $\beta$ can usually be taken equal to 1. For horizontal flow, however, the gravitational term is absent and $\beta = \alpha b$. The solutions of (10) are, for vertical flow:

CASE I: $n = 1$.

$$z = \frac{1}{\alpha} \ln(\alpha S + \beta) + K \tag{12}$$

CASE II: $n = 3/2$.

$$z = \frac{2}{\alpha} \left\{ \frac{1}{6\gamma} \ln \left( \frac{\gamma^2 - \gamma \sqrt{S} + S}{(\gamma + \sqrt{S})^2} \right) \right.$$

$$\left. + \frac{1}{\gamma \sqrt{3}} \tan^{-1} \left( \frac{2\sqrt{S} - \gamma}{\gamma \sqrt{3}} \right) \right\} + K \tag{13}$$

$$\gamma^3 = \beta/\alpha$$

CASE III: $n = 2$.

$$z = \frac{1}{\sqrt{\alpha}\beta} \tan^{-1} \sqrt{\frac{\alpha}{\beta}} S + K \tag{14}$$

CASE IV: $n = 3$.

$$z = \frac{1}{\alpha} \left\{ \frac{1}{6\gamma^2} \ln \left( \frac{(\gamma + S)^2}{(\gamma^2 - \gamma S + S^2)} \right) \right.$$

$$\left. + \frac{1}{\gamma^2 \sqrt{3}} \tan^{-1} \frac{(2S - \gamma)}{\gamma \sqrt{3}} \right\} + K \tag{15}$$

$$\gamma^3 = \beta/\alpha$$

CASE V: $n = 4$.

$$z = \frac{1}{\alpha} \left\{ \frac{1}{4\rho^2 \sqrt{2}} \ln \left( \frac{S^2 + \rho S \sqrt{2} + \rho^2}{S^2 - \rho S \sqrt{2} + \rho^2} \right) \right.$$

$$\left. + \frac{1}{2\rho^2 \sqrt{2}} \tan^{-1} \left( \frac{\rho S \sqrt{2}}{\rho^2 - S^2} \right) \right\} + K \tag{16}$$

$$\rho^4 = \beta/\alpha$$

CASE VI: $k = a \exp(-cS)$.

$$z = S - \frac{1}{c} \ln(a + q \exp(cS)) + K \tag{17}$$

In each case $K$ is a constant of integration to be evaluated from the boundary conditions.

# EVAPORATION FROM A SOIL IN THE PRESENCE OF A WATER TABLE

A steady-state flow problem of interest and importance is the upward movement of water from a water table and subsequent evaporation at the soil surface. Taking the origin of the coordinate system at the water table, the lower boundary condition becomes S = 0 when z = 0. The flux q, which is the same at every depth, is equal to the evaporation rate. When the upper boundary condition is specified, the flux and the suction distribution are uniquely determined from the solution of equation (10). In figure 1, q/a is plotted as a function of the suction at the soil surface for CASE IV (n = 3), assuming a depth to water table of 180 cm. With the exception of CASE I, the solutions for the other cases are similar in shape, and the conclusions drawn from figure 1 are applicable to the other solutions. When the evaporation rate is low and is limited by external conditions, a large increase in the evaporation rate causes only a small increase in the suction at the soil surface. Evaporation under such conditions is virtually independent of the depth to the water table and the capillary conductivity of the soil. The range of external conditions for which this is the case depends upon the depth to the water table. The shallower the water table the greater the range over which evaporation is controlled by external conditions. If the potential rate of evaporation due to external factors is increased (thus increasing the suction at the soil surface), the rate at which water moves upward and evaporates increases until a limit is approached. This limiting value is approached

![img-0.jpeg](None)

**{"image_type": "plot", "description": "The plot shows the relationship between suction at the soil surface (X-axis, labeled 'SUCTION AT SOIL SURFACE - BARS') and the ratio q/q₀ (Y-axis, labeled 'q/q₀ - CM CM⁻¹'). The X-axis ranges from 0 to 2.0 bars, and the Y-axis ranges from 0 to approximately 3.0 × 10⁻⁷ cm cm⁻¹. The curve indicates that as suction increases, q/q₀ initially rises sharply and then plateaus, stabilizing around a value of 3.0 × 10⁻⁷ cm cm⁻¹. The plot is labeled with a water table depth of 150 cm. Key observations include:\n\n- At 0 bars suction, q/q₀ is near 0.\n- A rapid increase in q/q₀ occurs between 0 and 0.4 bars suction.\n- The curve flattens and approaches a maximum value of ~3.0 × 10⁻⁷ cm cm⁻¹ beyond 1.0 bar suction.\n\nApproximate key data points extracted from the plot:\n- (0.0, ~0.0)\n- (0.2, ~1.0 × 10⁻⁷)\n- (0.4, ~2.0 × 10⁻⁷)\n- (0.6, ~2.5 × 10⁻⁷)\n- (0.8, ~2.8 × 10⁻⁷)\n- (1.0, ~3.0 × 10⁻⁷)\n- (1.2, ~3.0 × 10⁻⁷)\n- (1.4, ~3.0 × 10⁻⁷)\n- (1.6, ~3.0 × 10⁻⁷)\n- (2.0, ~3.0 × 10⁻⁷)"}**

FIG. 1. Relative evaporation rate as a function of upper boundary condition when the depth to water table is 180 cm. and k = a/(S² + b)

while the suction at the soil surface is still relatively low, being well below the wilting point and within the range over which equation (11) is valid. This limiting value is a function of the depth to the water table and the capillary conductivity only. CASE I is an exception for which there is no limiting evaporation rate. To date, however, no soil has been found for which CASE I holds at the higher suction values. Omitting this one case, if we allow S to approach infinity when z = d = the depth to the water table, the maximum evaporation rate due to movement of water in the liquid phase can be determined. In the limit it is a satisfactory approximation to take β equal to 1, and we get:

$$n = 3/2 \quad E_{1\text{lim}} = 3.77 \, a \, d^{-3/2} \tag{18}$$

$$n = 2 \quad E_{1\text{lim}} = 2.46 \, a \, d^{-2} \tag{19}$$

$$n = 3 \quad E_{1\text{lim}} = 1.76 \, a \, d^{-3} \tag{20}$$

$$n = 4 \quad E_{1\text{lim}} = 1.52 \, a \, d^{-4} \tag{21}$$

$$k = a \exp(-cS) \quad E_{1\text{lim}} = \frac{a}{\exp(cd) - 1} \tag{22}$$

# EFFECT OF VAPOR MOVEMENT

The equations given above deal with the movement of soil water in the liquid phase only. Under isothermal conditions, if the water content is above the wilting point, any vapor pressure gradient present in the soil will be sufficiently small that movement in the vapor phase can be neglected. In the case of evaporation from a soil, however, if the potential evaporation rate due to the external evaporative conditions is appreciably greater than the rate at which water can be transmitted from the water table to the soil surface, the soil near the surface will dry out. A vapor pressure gradient will be set up near the soil surface, causing movement of water in the vapor phase and thus allowing the soil to dry below the surface. Under these conditions the movement of water in the vapor phase must be taken into account. Philip (7) has treated polyphase movement in greater detail, but some simplifying assumptions are possible in this instance. As shown by the solution of equation (10), the moisture content will increase very rapidly with increasing depth near the soil surface. This moisture content gradient is sufficiently steep that it is possible, to a good degree of approximation, to divide the soil profile into

two regions. In the lower region water movement is virtually entirely in the liquid phase and equations (13) to (22) will apply. The region at the soil surface will be too dry to permit any appreciable water movement in the liquid phase and only vapor movement need be considered. It is a good approximation at the boundary between these two regions to assume the soil suction to be large enough to maintain evaporation at the limiting rate, yet not so large as to reduce significantly the vapor pressure below the saturation vapor pressure of water at the temperature of the soil at that point. Since the flux through both regions must be the same we can write:

$$q = \frac{A}{(d - \delta)^n} = \frac{D_v(p_1 - p_2)}{\delta} \tag{23}$$

where $A$ and $n$ are constants as given in equations (13) through (22), $D_v$ is the coefficient for diffusion of vapor through the soil, $p_1$ is the saturation vapor pressure of the soil water, $p_2$ is the vapor pressure at the soil surface, and $\delta$ is the thickness of the soil layer through which vapor movement is occurring. Using a value for $D_v$ given by Van Bavel (10) and values of $A$ obtained by the outflow method (2), it can be shown that $\delta$ will be very small compared with $d$. The denominator in the first term in equation (23) can be expanded in a binomial series and all but the first two terms dropped. Solving for $\delta$ gives:

$$\delta = \frac{D_v(p_1 - p_2)d^n}{A + nD_v(p_1 - p_2)d^{n-1}} \tag{24}$$

When this expression is substituted back into equation (23) we get

$$E = \frac{A + nD_v(p_1 - p_2)}{d^n} \tag{25}$$

It can be seen from equation (25) that the drying of the surface and the consequent vapor movement tends to increase the rate of evaporation. This increase is taken into account by the second term in the numerator of equation (25). Except for this term (25) is the same as equations (13) through (21). Thus the functional dependence of the maximum evaporation rate upon depth to water table is unchanged by the inclusion of vapor movement. It is estimated that this increase in evaporation rate, when vapor movement is taken into account, will seldom exceed 20 per cent of

the maximum evaporation possible by liquid movement and will usually be less.

The influence of heat input and vapor pressure at the soil surface upon evaporation can be studied using equation (25). Temperature will affect movement of water in the liquid state to only a limited extent since the effect of temperature upon viscosity is only moderate. If temperature changes were to cause a large change in the suction at the upper boundary of the liquid flow region, the evaporation rate would not be affected appreciably. The vapor pressure of water, however, is influenced markedly by temperature. This effect is taken into account by using the appropriate values for $p_1$ and $D_v$ in the right-hand side of equation (25). Since $\delta$ is small compared with $d$, and large variations in the suction at the upper boundary of the liquid-flow region have little influence upon the evaporation rate, diurnal fluctuations in temperature and vapor pressure at the soil surface can be expected to have little effect upon the evaporative process as far as the average evaporation rate and suction distribution are concerned.

The influence upon the evaporation rate by dissolved salts at the point where evaporation is occurring may be treated in a similar fashion. This effect should also be of minor importance.

# EFFECT OF A SURFACE MULCH

The effect of a surface mulch upon steady-state evaporation can be treated in a simple manner. For this purpose a mulch is defined as a medium which transports water in the vapor phase only. If $L$ is the thickness of the mulch and $r$ is the ratio of the vapor diffusion coefficient of the soil to that of the mulch we write instead of (23):

$$E = \frac{A}{(d - \delta)^n} = \frac{D_v(p_1 - p_2)}{rL + \delta} \tag{26}$$

where $p_2$ now refers to the vapor pressure at the upper surface of the mulch and the other symbols retain their previous meanings. The thickness $\delta$ of the layer of soil through which water moves in the vapor phase can be obtained by expanding (26) as was done in the case when the mulch was not present. As the thickness of the mulch is increased, the evaporation rate decreases, and $\delta$ will decrease to zero. Beyond this point evaporation is limited entirely by the mulch and we can write

$$E = \frac{D_v(p_1 - p_2)}{rL} = \frac{D_m(p_1 - p_2)}{L} \quad (27)$$

where $D_v/r = D_m$, the vapor diffusion coefficient for the mulch. In this instance, which is expected to be the more important, the evaporation rate is inversely proportional to the thickness of the mulch. Diffusion of vapor through a layer of still air at the soil surface would be handled in a similar manner.

# DISCUSSION

The rate of accumulation of soluble salts due to upward movement of a saline groundwater can be obtained by multiplying the evaporation rate by the salt concentration of the groundwater. Even though the evaporation rate may be small, a significant quantity of salts may accumulate over a long period of time. If a crop is present, the above results may be used by taking as the upper boundary the bottom of the root zone. The average suction at this point serves as the upper boundary condition. The amount of water and soluble salts moving up from a water table into the root zone can then be calculated from equations (12) through (17).

The solutions of the steady-state problem can be of great assistance in understanding the drying of soils. While quantitative comparison cannot be made, the general conclusions concerning the relative importance of vapor movement and effects of a surface mulch obtained for the steady-state case should hold qualitatively for the transient case. Starting from saturation the drying rate will at first be limited by external conditions and will be constant if these conditions remain constant. As soon as the surface of the soil becomes sufficiently dry, the evaporation rate will be limited by the rate of water movement to the surface in the liquid phase. As the surface dries further, vapor movement will become possible but will be relatively unimportant, particularly since diurnal fluctuations in temperature may cause the direction of vapor movement to be reversed. It should thus be possible to treat the drying of a soil as a problem in primarily unsaturated flow.

Laboratory studies of the steady-state evaporation process are described in another paper (3).

# SUMMARY

A transformation is given which makes possible the exact solution of some steady-state unsatu-

rated-flow problems and approximate solution of some transient problems. Solutions of the steady-state problem in one dimension are given for several different relations between capillary conductivity and soil suction.

Steady-state evaporation from a soil in which there is a water table is examined. The maximum evaporation rate is shown to be related to the capillary conductivity and depth to water table in a simple fashion. It is concluded that movement of water in the vapor phase is relatively unimportant in this connection. The influence of a surface mulch is also considered.

# REFERENCES

(1) CHILDS, E. C. 1956 Recent advances in the study of water movement in unsaturated soil. Trans. Intern. Congr. Soil Sci. 6th Congr. 39: 265-274.
(2) GARDNER, W. R. 1956 Calculation of capillary conductivity from pressure plate outflow data. Soil Sci. Soc. Amer. Proc. 20: 317-320.
(3) GARDNER, W. R., AND FIREMAN, M. 1957 Laboratory studies of evaporation from soil columns in the presence of a water table. Soil Sci. In press.
(4) KLUTE, A. 1952 A numerical method for solving the flow equation for water in unsaturated materials. Soil Sci. 73: 105-116.
(5) KLUTE, A. 1952 Some theoretical aspects of the flow of water in unsaturated soils. Soil Sci. Soc. Amer. Proc. 16: 144-148.
(6) PHILIP, J. R. 1955 Numerical solution of equations of the diffusion type with diffusivity concentration-dependent. Trans. Faraday Soc. 51: 885-892.
(7) PHILIP, J. R. 1955 The concept of diffusion applied to soil water. Proc. Nat. Acad. Sci. (India) Allahabad. 24 (A, part I): 93-104.
(8) REMSON, I., AND FOX, G. S. 1955 Capillary losses from ground water. Trans. Am. Geophys. Union 36: 304-310.
(9) RICHARDS, L. A. 1931 Capillary conduction of liquids through porous mediums. Physics 1: 318-333.
(10) VAN BAVEL, C. H. M. 1952 Gaseous diffusion and porosity in porous media. Soil Sci. 73: 91-104.
(11) WIND, G. P. 1955 A field experiment concerning capillary rise of moisture in a heavy clay soil. Neth. J. Agr. Sci. 3: 60-69.