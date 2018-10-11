import os
import sys
import numpy as np
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.
                                                       abspath(__file__))))
if path not in sys.path:
    sys.path.append(path)
from CM.CM_TUW23.f2_investment import dh_demand
from CM.CM_TUW23.f3_coherent_areas import distribuition_costs
from CM.CM_TUW23.f4_pre_optimization import pre_opt
from CM.CM_TUW23.f9_results_summary import summary


def main(investment_start_year, investment_last_year, depreciation_time,
         accumulated_energy_saving, dh_connection_rate_first_year,
         dh_connection_rate_last_year, interest_rate, grid_cost_ceiling,
         in_raster_gfa, in_raster_hdm, out_raster_maxDHdem,
         out_raster_invest_Euro, out_raster_hdm_last_year,
         out_raster_dist_pipe_length, out_raster_coh_area_bool,
         out_raster_labels, out_shp_prelabel, out_shp_label, out_shp_edges,
         out_shp_nodes, out_csv_solution, output_directory):
    """
    Default parameters:
        full_load_hours: In this work, as default value, we consider full load
            hours of 3000h for the DH system.
        grid_factor: grid factor of 1.05 shows the ratio of total grid costs to
            distribtion grid costs and is set based on previously run
            sensitivity analyses as well as other studies in the literature.
        pixT: pixel threshold in MWh/ha
        DH_threshold: DH area threshold in GWh/year just for filtering all the low demand
            pixels.
        c1 and c2: are based on Swedish experience and are taken from
            literature.
        trans_line_cap_cost: transmission line cost: power[MW], transmission
            line cost[EUR/m]
    """
    full_load_hours = 3000
    grid_factor = 1.05
    pixT = 10*np.arange(1, 135, 0.1)
    DH_threshold = 1
    c1 = [292.38, 218.78, 154.37]
    c2 = [2067.13, 1763.5, 1408.76]
    trans_line_cap_cost = np.array([[0, 0], [0.2, 195], [0.3, 206], [0.6, 220], [1.2, 240],
                        [1.9, 261], [3.6, 288], [6.1, 323], [9.8, 357],
                        [20,  426], [45,  564], [75,  701], [125, 839],
                        [190, 976], [19000, 97600]])
    dist_grid_cost = grid_cost_ceiling/grid_factor
    
    # f2: calculate pixel based values
    f2_output_layers = [out_raster_maxDHdem, out_raster_invest_Euro,
                        out_raster_hdm_last_year, out_raster_dist_pipe_length]
    dh_demand(c1, c2, in_raster_gfa, in_raster_hdm, investment_start_year,
              investment_last_year, accumulated_energy_saving,
              dh_connection_rate_first_year, dh_connection_rate_last_year,
              depreciation_time, interest_rate, f2_output_layers)
    # f3: Determination of coherent areas based on the grid cost threshold.
    distribuition_costs(pixT, DH_threshold, dist_grid_cost,
                        out_raster_hdm_last_year, out_raster_maxDHdem,
                        out_raster_invest_Euro, out_raster_coh_area_bool,
                        out_raster_labels)
    # f4: pre-steps for providing input to the optimization function including
    # calling various functions for calculating distance between coherent
    # areas, optimization module, illustrating the transmission lines,
    # polygonize the coherent areas.
    (covered_demand, dist_inv, dist_spec_cost, trans_inv, trans_spec_cost,
     trans_line_length), dist_pipe_len, heat_dem_1st, \
     heat_dem_last, n_coh_areas, \
     n_coh_areas_selected = pre_opt(depreciation_time, interest_rate,
                                    grid_cost_ceiling, trans_line_cap_cost,
                                    full_load_hours, in_raster_hdm,
                                    out_raster_coh_area_bool,
                                    out_raster_hdm_last_year,
                                    out_raster_dist_pipe_length,
                                    out_raster_maxDHdem, out_raster_labels,
                                    out_raster_invest_Euro, out_shp_prelabel,
                                    out_shp_label, out_shp_edges,
                                    out_shp_nodes, out_csv_solution,
                                    output_directory, polygonize_region=True)
    # f9: returns the summary of results in a dictionary format
    output_summary = summary(covered_demand, dist_inv, dist_spec_cost,
                             trans_inv, trans_spec_cost, trans_line_length,
                             dist_pipe_len, heat_dem_1st, heat_dem_last,
                             n_coh_areas, n_coh_areas_selected)
    return output_summary
