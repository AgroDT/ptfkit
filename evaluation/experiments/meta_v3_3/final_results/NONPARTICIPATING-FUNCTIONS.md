# Применимость функций ptfkit — v1.0

Независимый full-WRC/Ksat анализ использует 77 функций каталога, включая функции, чьи native-прогнозы участвуют в дискретных семействах. Point-target оценки охватывают ещё 18 функций. Ниже перечислены функции вне основного сравнения; это не означает их непригодности для собственных научных задач.

| Функция | Статус в v1.0 | Причина |
|---|---|---|
| `calc_ptf_ahuja1984` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: coefficient_b, exponent_n, theta_33, total_porosity. |
| `calc_ptf_aimrun2009` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: gmd. |
| `calc_ptf_bai2022` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: altitude, clay, depth, precipitation, sand, silt, slope. |
| `calc_ptf_bai2022_bulk_density` | other_target | Нет операционного WRC/Ksat target в данном анализе: bulk density. |
| `calc_ptf_beniaich2023_mlr1` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_beniaich2023_mlr2` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_beniaich2023_mlr3` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_beniaich2023_mlr4` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_beniaich2023_mlr5` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_beniaich2023_slr1` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_beniaich2023_slr2` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_beniaich2023_slr3` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_beniaich2023_slr4` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_beniaich2023_slr5` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_beniaich2023_slr6` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_bruand1994_bulk_volume_available_water` | other_target | Нет операционного WRC/Ksat target в данном анализе: available water / available water capacity. |
| `calc_ptf_bruand1994_bulk_volume_water_retention` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_volume. |
| `calc_ptf_bruand1994_clay_available_water` | other_target | Нет операционного WRC/Ksat target в данном анализе: available water / available water capacity. |
| `calc_ptf_bruand1994_clay_water_retention` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: clay_content. |
| `calc_ptf_chakraborty2011_eq6` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, clay, organic_carbon, sand, silt. |
| `calc_ptf_dharumarajan2019_infiltration` | other_target | Нет операционного WRC/Ksat target в данном анализе: infiltration. |
| `calc_ptf_dharumarajan2019_nkp` | user_decision_required | Физическая неоднозначность водной базы или формулы кривой требует решения; вариант не угадывается. |
| `calc_ptf_dharumarajan2019_nkp_clay` | user_decision_required | Физическая неоднозначность водной базы или формулы кривой требует решения; вариант не угадывается. |
| `calc_ptf_dharumarajan2019_skp` | user_decision_required | Физическая неоднозначность водной базы или формулы кривой требует решения; вариант не угадывается. |
| `calc_ptf_dharumarajan2019_skp_clay` | user_decision_required | Физическая неоднозначность водной базы или формулы кривой требует решения; вариант не угадывается. |
| `calc_ptf_dijkerman1988` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_dijkerman1988_available_water` | other_target | Нет операционного WRC/Ksat target в данном анализе: available water / available water capacity. |
| `calc_ptf_gunarathna2019_vwc10_set2` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: sand, silt. |
| `calc_ptf_gunarathna2019_vwc10_set3` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, sand, silt. |
| `calc_ptf_gunarathna2019_vwc10_set4` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: organic_carbon, sand, silt. |
| `calc_ptf_gunarathna2019_vwc1500_set3` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, sand. |
| `calc_ptf_gunarathna2019_vwc1500_set4` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: organic_carbon, sand. |
| `calc_ptf_gunarathna2019_vwc33_set2` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: sand, silt. |
| `calc_ptf_gunarathna2019_vwc33_set3` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, sand, silt. |
| `calc_ptf_gunarathna2019_vwc33_set4` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: organic_carbon, sand, silt. |
| `calc_ptf_hodnett2002` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, cation_exchange_capacity, clay, organic_carbon, ph, sand, silt. |
| `calc_ptf_jabro1992` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: silt. |
| `calc_ptf_kalumba2021_mlr_ksat` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: nitrogen, sand, stoniness. |
| `calc_ptf_kalumba2021_mlr_pf00` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, electrical_conductivity, elevation, nitrogen, ph, sand, silt, stoniness. |
| `calc_ptf_kalumba2021_mlr_pf10` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, electrical_conductivity, elevation, nitrogen, ph, sand, silt, stoniness. |
| `calc_ptf_kalumba2021_mlr_pf20` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, clay, depth, electrical_conductivity, elevation, nitrogen, ph, sand, silt, stoniness. |
| `calc_ptf_kalumba2021_mlr_pf28` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, clay, depth, electrical_conductivity, elevation, nitrogen, organic_matter, sand, silt, stoniness. |
| `calc_ptf_kalumba2021_mlr_pf34` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, clay, depth, electrical_conductivity, elevation, nitrogen, organic_matter, sand, silt, stoniness. |
| `calc_ptf_kalumba2021_mlr_pf42` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: clay, depth, electrical_conductivity, elevation, nitrogen, organic_matter, sand, silt, stoniness. |
| `calc_ptf_lal1979_group_i_lower_plastic_limit_from_clay` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_i_lower_plastic_limit_from_organic_carbon` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_i_lower_plastic_limit_from_sand` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_i_moisture_equivalent_from_clay` | other_target | Нет операционного WRC/Ksat target в данном анализе: moisture equivalent. |
| `calc_ptf_lal1979_group_i_moisture_equivalent_from_sand` | other_target | Нет операционного WRC/Ksat target в данном анализе: moisture equivalent. |
| `calc_ptf_lal1979_group_i_plasticity_index_from_clay` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_i_plasticity_index_from_organic_carbon` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_i_plasticity_index_from_sand` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_i_upper_plastic_limit_from_clay` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_i_upper_plastic_limit_from_organic_carbon` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_i_water_0bar_from_clay` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: clay. |
| `calc_ptf_lal1979_group_i_water_0bar_from_sand` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: sand. |
| `calc_ptf_lal1979_group_i_water_15bar_from_silt` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_lal1979_group_ii_lower_plastic_limit_from_clay` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_ii_lower_plastic_limit_from_sand` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_ii_lower_plastic_limit_from_silt` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_ii_moisture_equivalent_from_clay` | other_target | Нет операционного WRC/Ksat target в данном анализе: moisture equivalent. |
| `calc_ptf_lal1979_group_ii_moisture_equivalent_from_sand` | other_target | Нет операционного WRC/Ksat target в данном анализе: moisture equivalent. |
| `calc_ptf_lal1979_group_ii_moisture_equivalent_from_silt` | other_target | Нет операционного WRC/Ksat target в данном анализе: moisture equivalent. |
| `calc_ptf_lal1979_group_ii_plasticity_index_from_organic_carbon` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_ii_plasticity_index_from_silt` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_clay` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_organic_carbon` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_sand` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_silt` | other_target | Нет операционного WRC/Ksat target в данном анализе: plasticity properties. |
| `calc_ptf_lal1979_group_ii_water_03bar_from_water_01bar` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: water_01bar. |
| `calc_ptf_lal1979_group_ii_water_0bar_from_clay` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: clay. |
| `calc_ptf_lal1979_group_ii_water_0bar_from_sand` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: sand. |
| `calc_ptf_lal1979_group_ii_water_15bar_from_water_01bar` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: water_01bar. |
| `calc_ptf_li2007` | user_decision_required | Физическая неоднозначность водной базы или формулы кривой требует решения; вариант не угадывается. |
| `calc_ptf_myeni2021_fc` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_myeni2021_pwp` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_oosterveld1980_available_water` | other_target | Нет операционного WRC/Ksat target в данном анализе: wilting point. |
| `calc_ptf_oosterveld1980_field_capacity` | other_target | Нет операционного WRC/Ksat target в данном анализе: field capacity. |
| `calc_ptf_oosterveld1980_field_capacity_tension` | other_target | Нет операционного WRC/Ksat target в данном анализе: other. |
| `calc_ptf_oosterveld1980_wilting_point` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_ottoni2019_wm330` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: effective_porosity. |
| `calc_ptf_ottoni2019_wmssc` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: silt. |
| `calc_ptf_ottoni2019_wmsscbd` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: silt. |
| `calc_ptf_pidgeon1972_awc` | excluded_other_target | Другой физический target: AWC, extended AWC или осмотический потенциал. |
| `calc_ptf_pidgeon1972_awc_coarse_sand` | excluded_other_target | Другой физический target: AWC, extended AWC или осмотический потенциал. |
| `calc_ptf_pidgeon1972_awc_fine_sand` | excluded_other_target | Другой физический target: AWC, extended AWC или осмотический потенциал. |
| `calc_ptf_pidgeon1972_awc_sand_organic_matter` | excluded_other_target | Другой физический target: AWC, extended AWC или осмотический потенциал. |
| `calc_ptf_pidgeon1972_awc_very_fine_sand` | excluded_other_target | Другой физический target: AWC, extended AWC или осмотический потенциал. |
| `calc_ptf_pidgeon1972_eawc` | excluded_other_target | Другой физический target: AWC, extended AWC или осмотический потенциал. |
| `calc_ptf_pidgeon1972_eawc_coarse_sand_organic_matter` | excluded_other_target | Другой физический target: AWC, extended AWC или осмотический потенциал. |
| `calc_ptf_pidgeon1972_eawc_fine_sand_organic_matter` | excluded_other_target | Другой физический target: AWC, extended AWC или осмотический потенциал. |
| `calc_ptf_pidgeon1972_eawc_sand` | excluded_other_target | Другой физический target: AWC, extended AWC или осмотический потенциал. |
| `calc_ptf_pidgeon1972_eawc_sand_organic_matter` | excluded_other_target | Другой физический target: AWC, extended AWC или осмотический потенциал. |
| `calc_ptf_pidgeon1972_fc` | other_target | Нет операционного WRC/Ksat target в данном анализе: field capacity. |
| `calc_ptf_pidgeon1972_fc_sand` | other_target | Нет операционного WRC/Ksat target в данном анализе: field capacity. |
| `calc_ptf_pidgeon1972_fc_sand_organic_matter` | other_target | Нет операционного WRC/Ksat target в данном анализе: field capacity. |
| `calc_ptf_pidgeon1972_fc_vol_sand_organic_matter` | other_target | Нет операционного WRC/Ksat target в данном анализе: field capacity. |
| `calc_ptf_pidgeon1972_pwp` | other_target | Нет операционного WRC/Ksat target в данном анализе: wilting point. |
| `calc_ptf_pidgeon1972_pwp_sand` | other_target | Нет операционного WRC/Ksat target в данном анализе: wilting point. |
| `calc_ptf_pidgeon1972_pwp_sand_organic_matter` | other_target | Нет операционного WRC/Ksat target в данном анализе: wilting point. |
| `calc_ptf_puckett1985` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, clay, fine_sand, porosity, sand. |
| `calc_ptf_rawls1982_full_wrc` | conditional_only | Измеренная влажность этой же ОГХ требуется как predictor; исключена из независимого сравнения. |
| `calc_ptf_rawls1982_theta_1500` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_rawls1982_theta_33` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: organic_matter, sand, theta_1500. |
| `calc_ptf_rawls2003_soc_theta1500_gmdh` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: clay, sand, soil_organic_carbon. |
| `calc_ptf_rawls2003_soc_theta1500_tree` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: clay, sand, soil_organic_carbon. |
| `calc_ptf_rawls2003_soc_theta33_gmdh` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: clay, sand, soil_organic_carbon. |
| `calc_ptf_rawls2003_soc_theta33_tree` | point-target | Оценка на отдельных native-давлениях; не входит в full-WRC ranking. |
| `calc_ptf_saxton2006_conductivity` | other_target | Нет операционного WRC/Ksat target в данном анализе: unsaturated conductivity. |
| `calc_ptf_saxton2006_density` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: density_factor, normal_density, theta_33, theta_s. |
| `calc_ptf_saxton2006_gravel` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: gravel_weight_fraction, matric_density, plant_available_water, saturated_conductivity. |
| `calc_ptf_saxton2006_salinity` | excluded_other_target | Другой физический target: AWC, extended AWC или осмотический потенциал. |
| `calc_ptf_saxton2006_tension_dry` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. |
| `calc_ptf_saxton2006_tension_wet` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. |
| `calc_ptf_tiwary2014_bsr` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: cation_exchange_capacity, clay, emp, esp, excm, ph. |
| `calc_ptf_tiwary2014_igp` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: esp, sand. |
| `calc_ptf_vereecken1989_detailed` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, carbon, clay, geometric_mean_particle_size, geometric_standard_deviation, particle_1000_500, particle_100_50, particle_10_2, particle_2000_1000, particle_200_100, particle_20_10, particle_500_200, particle_50_20. |
| `calc_ptf_wang2012` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: altitude, sand, silt, soil_organic_carbon. |
| `calc_ptf_wang2022_h2` | user_decision_required | Физическая неоднозначность водной базы или формулы кривой требует решения; вариант не угадывается. |
| `calc_ptf_wang2022_h3` | user_decision_required | Физическая неоднозначность водной базы или формулы кривой требует решения; вариант не угадывается. |
| `calc_ptf_weber2020` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. |
| `calc_ptf_williams1992_function_2` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, clay, fine_sand, structure. |
| `calc_ptf_williams1992_function_3` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, structure, texture_class. |
| `calc_ptf_williams1992_function_4` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: clay, fine_sand, silt, texture_class. |
| `calc_ptf_williams1992_function_5` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, clay, fine_sand, silt, texture_class. |
| `calc_ptf_williams1992_function_6` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: clay, fine_sand, organic_matter, silt, texture_class. |
| `calc_ptf_williams1992_function_7` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: bulk_density, structure, texture_class. |
| `calc_ptf_williams1992_function_8` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: clay, fine_sand, silt, texture_class. |
| `calc_ptf_williams1992_table5` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. |
| `calc_ptf_wosten2001_class_parameters` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: soil_class. |
| `calc_ptf_wosten2001_hydraulic` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: alpha, conductivity_shape_parameter, n, saturated_conductivity, theta_r, theta_s. |
| `calc_ptf_wosten2001_sand_subsoil_table5` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: median_sand_size, silt. |
| `calc_ptf_wosten2001_sand_topsoil_table5` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: median_sand_size, silt. |
| `calc_ptf_zhao2016_m2_1` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: silt. |
| `calc_ptf_zhao2016_m2_2` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: silt. |
| `calc_ptf_zhao2016_m2_3` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: silt. |
| `calc_ptf_zhao2016_m2_4` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: silt. |
| `calc_ptf_zhao2016_m2_5` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: silt. |
| `calc_ptf_zhao2016_m2_6` | still_missing_predictor | Нет допустимого независимого расчёта с доступными входами и поддержкой давления. Не хватает: silt. |
