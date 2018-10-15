import os
import sys
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)
from ..helper import generate_output_file_tif
from ..helper import generate_output_file_shp
from ..helper import generate_output_file_csv
from ..helper import create_zip_shapefiles
import my_calculation_module_directory.CM.CM_TUW23.run_cm as CM23


def calculation(output_directory, inputs_raster_selection, inputs_parameter_selection):

    """ def calculation()"""
    '''
    inputs:
        investment_start_year: year the investment starts.
        investment_last_year: year the investment starts.
        depreciation_time: depreciation time.
        accumulated_energy_saving: accumulated energy saving at the end of investment period.
        dh_connection_rate_first_year: share of demand covered by DH to the total demand in DH areas in the first year of investment [0:1].
        dh_connection_rate_last_year: share of demand covered by DH to the total demand in DH areas in the last year of investment [0:1].
        interest_rate: interest rate [0:1].
        grid_cost_ceiling: The cost in EUR/MWh that should not be exceeded.
        in_raster_gfa: gross floor area map for the selected zone.
        in_raster_hdm: heat density map for the selected zone.

    Outputs:
        out_raster_maxDHdem: max demand should be covered by DH during the investment period [MWh].
        out_raster_invest_Euro: distribution grid investment [EUR/MWh].
        out_raster_hdm_last_year: heat density map at the end of investment period.
        out_raster_dist_pipe_length: distribution grid pipeline length [m/m2].
        out_raster_coh_area_bool: shows both economic and non-economic coherent areas.
        out_raster_hdm_in_dh_reg_last_year: heat densities in the last year of investment within the coherent areas.
        out_raster_labels,
        out_shp_prelabel,
        out_shp_label,
        out_csv_solution
    '''
    # input parameters
    investment_start_year = inputs_parameter_selection["investment_start_year"]
    investment_last_year = inputs_parameter_selection["investment_last_year"]
    depreciation_time = inputs_parameter_selection["depreciation_time"]
    accumulated_energy_saving = inputs_parameter_selection["accumulated_energy_saving"]
    dh_connection_rate_first_year = inputs_parameter_selection["dh_connection_rate_first_year"]
    dh_connection_rate_last_year = inputs_parameter_selection["dh_connection_rate_last_year"]
    interest_rate = inputs_parameter_selection["interest_rate"]
    grid_cost_ceiling = inputs_parameter_selection["grid_cost_ceiling"]
    
    
    # input raster layers: (gfa:= gross floor area; hdm:= heat density map)
    in_raster_gfa = inputs_raster_selection["gfa_tot_curr_density"]
    in_raster_hdm = inputs_raster_selection["heat_tot_curr_density"]
    
    # output raster layers
    out_raster_maxDHdem = generate_output_file_tif(output_directory)
    out_raster_invest_Euro = generate_output_file_tif(output_directory)
    out_raster_hdm_last_year = generate_output_file_tif(output_directory)
    out_raster_dist_pipe_length = generate_output_file_tif(output_directory)
    out_raster_coh_area_bool = generate_output_file_tif(output_directory)
    out_raster_labels = generate_output_file_tif(output_directory)
    
    # output shapefiles
    out_shp_prelabel = generate_output_file_shp(output_directory)
    out_shp_label = generate_output_file_shp(output_directory)
    out_shp_edges = generate_output_file_shp(output_directory)
    out_shp_nodes = generate_output_file_shp(output_directory)
    
    # output csv files
    out_csv_solution = generate_output_file_csv(output_directory)

    output_summary = CM23.main(
            investment_start_year,
            investment_last_year,
            depreciation_time,
            accumulated_energy_saving,
            dh_connection_rate_first_year,
            dh_connection_rate_last_year,
            interest_rate,
            grid_cost_ceiling,
            in_raster_gfa,
            in_raster_hdm,
            out_raster_maxDHdem,
            out_raster_invest_Euro,
            out_raster_hdm_last_year,
            out_raster_dist_pipe_length,
            out_raster_coh_area_bool,
            out_raster_labels,
            out_shp_prelabel,
            out_shp_label,
            out_shp_edges,
            out_shp_nodes,
            out_csv_solution,
            output_directory
            )

    result = dict()
    out_shp_prelabel = create_zip_shapefiles(output_directory, out_shp_prelabel)
    out_shp_label = create_zip_shapefiles(output_directory, out_shp_label)
    out_shp_edges = create_zip_shapefiles(output_directory, out_shp_edges)
    out_shp_nodes = create_zip_shapefiles(output_directory, out_shp_nodes)
    result['name'] = 'CM District Heating Grid Investment'
    result["raster_layers"]=[{"name": "district heating coherent areas","path": out_raster_maxDHdem},
          {"name": "district heating coherent areas","path": out_raster_invest_Euro},
          {"name": "district heating coherent areas","path": out_raster_hdm_last_year},
          {"name": "district heating coherent areas","path": out_raster_dist_pipe_length},
          {"name": "district heating coherent areas","path": out_raster_coh_area_bool},
          {"name": "district heating coherent areas","path": out_raster_labels}]
    
    result["vector_layers"]=[{"name": "shapefile of coherent areas with their potential","path": out_shp_prelabel},
          {"name": "shapefile of coherent areas with their potential","path": out_shp_label},
          {"name": "shapefile of coherent areas with their potential","path": out_shp_edges},
          {"name": "shapefile of coherent areas with their potential","path": out_shp_nodes}]

    result["tabular"]=[{"name": "name of csv file","path": out_csv_solution}]
    result['indicator'] = output_summary

    return result
