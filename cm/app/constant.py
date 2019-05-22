
CELERY_BROKER_URL_DOCKER = 'amqp://admin:mypass@rabbit:5672/'
CELERY_BROKER_URL_LOCAL = 'amqp://localhost/'

CELERY_BROKER_URL = CELERY_BROKER_URL_DOCKER
CM_REGISTER_Q = 'rpc_queue_CM_register' # Do no change this value

CM_NAME = 'District Heating Grid Investment'
RPC_CM_ALIVE= 'rpc_queue_CM_ALIVE' # Do no change this value
RPC_Q = 'rpc_queue_CM_compute' # Do no change this value
CM_ID = 3 # CM_ID is defined by the enegy research center of Martigny (CREM)
PORT_LOCAL = int('500' + str(CM_ID))
PORT_DOCKER = 80
PORT = PORT_DOCKER
TRANFER_PROTOCOLE ='http://'

INPUTS_CALCULATION_MODULE = [
        {'input_name': 'First year of investment',
         'input_type': 'input',
         'input_parameter_name': 'investment_start_year',
         'input_value': 2018,
         'input_unit': 'none',
         'input_min': 2000,
         'input_max': 2200, 'cm_id': CM_ID
         },
         {'input_name': 'Last year of investment',
         'input_type': 'input',
         'input_parameter_name': 'investment_last_year',
         'input_value': 2030,
         'input_unit': 'none',
         'input_min': 2000,
         'input_max': 2200, 'cm_id': CM_ID
         },
         {'input_name': 'Depreciation time',
          'input_type': 'input',
          'input_parameter_name': 'depreciation_time',
          'input_value': 30,
          'input_unit': 'none',
          'input_min': 1,
          'input_max': 200, 'cm_id': CM_ID
          },
          {'input_name': 'Accumulated energy saving',
           'input_type': 'input',
           'input_parameter_name': 'accumulated_energy_saving',
           'input_value': 0.1,
           'input_unit': 'none',
           'input_min': 0,
           'input_max': 1, 'cm_id': CM_ID
           },
           {'input_name': 'DH market share at the beginning of the investment period',
            'input_type': 'input',
            'input_parameter_name': 'dh_connection_rate_first_year',
            'input_value': 0.3,
            'input_unit': 'none',
            'input_min': 0,
            'input_max': 1, 'cm_id': CM_ID
            },
            {'input_name': 'DH market share at the end of the investment period',
             'input_type': 'input',
             'input_parameter_name': 'dh_connection_rate_last_year',
             'input_value': 0.6,
             'input_unit': 'none',
             'input_min': 0,
             'input_max': 1, 'cm_id': CM_ID
             },
             {'input_name': 'Interest rate',
              'input_type': 'input',
              'input_parameter_name': 'interest_rate',
              'input_value': 0.05,
              'input_unit': 'none',
              'input_min': 0,
              'input_max': 1, 'cm_id': CM_ID
              },
              {'input_name': 'DH grid cost ceiling',
               'input_type': 'range',
               'input_parameter_name': 'grid_cost_ceiling',
               'input_value': 15,
               'input_unit': 'EUR/MWh',
               'input_min': 0,
               'input_max': 200,
               'cm_id': CM_ID
               },
               {'input_name': 'Construction cost constant - Inner city',
               'input_type': 'range',
               'input_parameter_name': 'c1_innercity',
               'input_value': 292.38,
               'input_unit': 'EUR/m',
               'input_min': 0,
               'input_max': 100000,
               'cm_id': CM_ID
               },
               {'input_name': 'Construction cost constant - Outer city',
               'input_type': 'range',
               'input_parameter_name': 'c1_outercity',
               'input_value': 218.78,
               'input_unit': 'EUR/m',
               'input_min': 0,
               'input_max': 100000,
               'cm_id': CM_ID
               },
               {'input_name': 'Construction cost constant - Park',
               'input_type': 'range',
               'input_parameter_name': 'c1_park',
               'input_value': 154.37,
               'input_unit': 'EUR/m',
               'input_min': 0,
               'input_max': 100000,
               'cm_id': CM_ID
               },
               {'input_name': 'Construction cost coefficient - Inner city',
               'input_type': 'range',
               'input_parameter_name': 'c2_innercity',
               'input_value': 2067.13,
               'input_unit': 'EUR/m2',
               'input_min': 0,
               'input_max': 100000,
               'cm_id': CM_ID
               },
               {'input_name': 'Construction cost coefficient - Outer city',
               'input_type': 'range',
               'input_parameter_name': 'c2_outercity',
               'input_value': 1763.5,
               'input_unit': 'EUR/m2',
               'input_min': 0,
               'input_max': 100000,
               'cm_id': CM_ID
               },
               {'input_name': 'Construction cost coefficient - Park',
               'input_type': 'range',
               'input_parameter_name': 'c2_park',
               'input_value': 1408.76,
               'input_unit': 'EUR/m2',
               'input_min': 0,
               'input_max': 100000,
               'cm_id': CM_ID
               },
               {'input_name': 'Full load hours',
               'input_type': 'range',
               'input_parameter_name': 'full_load_hours',
               'input_value': 3000,
               'input_unit': 'h',
               'input_min': 0,
               'input_max': 8760,
               'cm_id': CM_ID
               }
              ]


SIGNATURE = {
    "category": "Buildings",
    "cm_name": CM_NAME,
    "layers_needed": [
        "heat_tot_curr_density", "gfa_tot_curr_density"
    ],
    "type_layer_needed": [
        "heat","gross_floor_area"
    ],
    "cm_url": "Do not add something",
    "cm_description": "this computation module can be used for the economic assessment of DH potential and DH grid investment.",
    "cm_id": CM_ID,
    'inputs_calculation_module': INPUTS_CALCULATION_MODULE
}
