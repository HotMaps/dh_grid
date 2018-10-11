import os
import sys
import numpy as np
import networkx as nx
import pyomo.environ as en
from pyomo.opt import SolverFactory
from pyomo.opt import TerminationCondition
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.
                                                       abspath(__file__))))
if path not in sys.path:
    sys.path.append(path)


def optimize_dist(threshold, cost_matrix, pow_range_matrix, distance_matrix,
                  demand_coherent_area, dist_cost_coherent_area, obj_case=1,
                  full_load_hours=3000, max_pipe_length=4000,
                  logFile_path=None):
    '''
    Number of coherent areas: n
    demand_coherent_area (n x 1) [MWh]: demand in each coherent area
    dist_cost_coherent_area (n x 1) [EUR]: distribution cost of each coherent
                                           area
    transmision_line_cost (n x n) [EUR/m]: constant value for the cost of
                                   transmission line
    '''
    if len(demand_coherent_area) == 0:
        term_cond = False
        dh = np.zeros(6)
        edge_list = []
        return term_cond, dh, np.array(edge_list)
    if len(demand_coherent_area) == 1:
        term_cond = True
        dh = np.zeros(7)
        dh[0] = 1
        covered_demand = demand_coherent_area
        dist_inv = demand_coherent_area * dist_cost_coherent_area
        dist_spec_cost = dist_inv/covered_demand
        trans_inv = 0
        trans_spec_cost = 0
        trans_line_length = 0
        dh[1: 7] = covered_demand, dist_inv, dist_spec_cost, trans_inv, \
                    trans_spec_cost, trans_line_length
        edge_list = []
        return term_cond, dh, np.array(edge_list)
    G = np.argmax(demand_coherent_area)
    n = demand_coherent_area.shape[0]
    nr_cost_steps = len(cost_matrix)
    last_cost_step = nr_cost_steps - 1
    fix_to_zero_index = np.argwhere(distance_matrix >= max_pipe_length)
    m = en.ConcreteModel()

    # ##########################################################################
    # ########## Sets:
    # ##########################################################################
    m.index_row = en.RangeSet(0, n-1)
    m.index_col = en.RangeSet(0, n-1)
    m.index_cap = en.RangeSet(0, last_cost_step)

    # ##########################################################################
    # ########## Parameters:
    # ##########################################################################
    m.th = en.Param(m.index_row, initialize=threshold)
    m.cap_up = en.Param(initialize=np.sum(demand_coherent_area) -
                        demand_coherent_area[G])

    def demand(m, i):
        return demand_coherent_area[i]
    m.q = en.Param(m.index_row, initialize=demand)

    def distribution_cost(m, i):
        return dist_cost_coherent_area[i]
    m.dist_cost = en.Param(m.index_row, initialize=distribution_cost)

    def l_length(m, i, j):
        return distance_matrix[i, j]
    m.line_length = en.Param(m.index_row, m.index_col, initialize=l_length)

    def trans_cost_steps(m, i):
        return cost_matrix[i]
    m.cost_steps = en.Param(m.index_cap, initialize=trans_cost_steps)

    def trans_pow_step_ranges(m, i):
        return pow_range_matrix[i]
    m.pow_step_ranges = en.Param(m.index_cap, initialize=trans_pow_step_ranges)

    # ##########################################################################
    # ########## Variables:
    # ##########################################################################
    m.q_bool = en.Var(m.index_row, domain=en.Binary, initialize=1)
    m.l_bool = en.Var(m.index_row, m.index_col, domain=en.Binary, initialize=0)
    m.cost_range_bool = en.Var(m.index_row, m.index_col, m.index_cap,
                               domain=en.Binary, initialize=0)
    m.line_capacity = en.Var(m.index_row, m.index_col, domain=en.Reals,
                             initialize=0)
    m.line_cost = en.Var(m.index_row, m.index_col, domain=en.Reals,
                         initialize=0)
    # set the largest demand zone to be part of the result
    m.q_bool[G].fix(1)

    for i in m.index_row:
        for j in m.index_col:
            m.cost_range_bool[i, j, 0].fix(0)

    for i in range(fix_to_zero_index.shape[0]):
        s, t = fix_to_zero_index[i, :]
        m.l_bool[s, t].fix(0)
        m.line_capacity[s, t].fix(0)

    # ##########################################################################
    # ########## Constraints:
    # ##########################################################################

    def overall_cost_rule(m):
        return sum(m.line_cost[i, j] * m.line_length[i, j]
                   for i in m.index_row for j in m.index_col) <= \
                   sum(m.q_bool[i]*m.q[i]*(m.th[i]-m.dist_cost[i])
                       for i in m.index_row)
    m.overall_cost = en.Constraint(rule=overall_cost_rule)

    def max_edge_number_rule(m):
        return sum(m.l_bool[i, j] for i in m.index_row
                   for j in m.index_col) == sum(m.q_bool[i]
                                                for i in m.index_row) - 1
    m.max_edge_number = en.Constraint(rule=max_edge_number_rule)

    def edge_connectivity_rule(m, i):
        if i == G:
            return 0 == sum(m.l_bool[j, i] for j in m.index_row)
        else:
            return m.q_bool[i] <= sum(m.l_bool[j, i] for j in m.index_row)
    m.edge_connectivity = en.Constraint(m.index_row,
                                        rule=edge_connectivity_rule)
#     m.edge_connectivity_0 = en.Constraint(expr=1 <= sum(m.l_bool[G, j]
#                                           for j in m.index_col))

    def edge_connectivity_2_rule(m, i, j):
        if i == G:
            return en.Constraint.Skip
        else:
            return m.l_bool[i, j] <= sum(m.l_bool[h, i]
                                         for h in m.index_row if h != j)
    m.edge_connectivity_2 = en.Constraint(m.index_row, m.index_col,
                                          rule=edge_connectivity_2_rule)

    def edge_active_rule(m, i, j):
        return 2*(m.l_bool[i, j] + m.l_bool[j, i]) <= m.q_bool[i] + m.q_bool[j]
    m.edge_active = en.Constraint(m.index_row, m.index_col,
                                  rule=edge_active_rule)

    def self_loop_rule(m, i):
        return m.l_bool[i, i] == 0
    m.self_loop = en.Constraint(m.index_row, rule=self_loop_rule)

    def uni_directed_edge_rule(m, i, j):
        return m.l_bool[i, j] + m.l_bool[j, i] <= 1
    m.uni_directed_edge = en.Constraint(m.index_row, m.index_col,
                                        rule=uni_directed_edge_rule)

    def capacity_lower_bound_rule(m, i, j):
        return m.line_capacity[i, j] >= (m.l_bool[i, j]*m.q[j])/full_load_hours
    m.capacity_lower_bound = en.Constraint(m.index_row, m.index_col,
                                           rule=capacity_lower_bound_rule)

    def capacity_upper_bound_rule(m, i, j):
        return m.line_capacity[i, j] <= \
            (sum(m.q[h] for h in m.index_row if (h != G and h != i)) -
             sum(m.l_bool[h, i] * m.q[h]
                 for h in m.index_row if h != G))/full_load_hours
    m.capacity_upper_bound = en.Constraint(m.index_row, m.index_col,
                                           rule=capacity_upper_bound_rule)

    def force_cap_to_zero_rule(m, i, j):
        return m.line_capacity[i, j] - m.l_bool[i, j]*m.cap_up <= 0
    m.force_cap_to_zero = en.Constraint(m.index_row, m.index_col,
                                        rule=force_cap_to_zero_rule)

    def capacity_flow_rule(m, i):
        if i == G:
            return sum(m.line_capacity[G, h] for h in m.index_col) == \
                sum(m.q_bool[h]*m.q[h]
                    for h in m.index_row if h != G)/full_load_hours
        else:
            return sum(m.line_capacity[h, i] for h in m.index_row) - \
                sum(m.line_capacity[i, h] for h in m.index_col) == \
                m.q_bool[i]*m.q[i]/full_load_hours
    m.capacity_flow = en.Constraint(m.index_row, rule=capacity_flow_rule)

    def self_loop_capacity_rule(m, i):
        return m.line_capacity[i, i] == 0
    m.self_loop_capacity = en.Constraint(m.index_row,
                                         rule=self_loop_capacity_rule)

    def spec_line_cost_rule(m, i, j):
        return m.line_cost[i, j] == sum(m.cost_range_bool[i, j, k] *
                                        (m.cost_steps[k] - m.cost_steps[k-1])
                                        for k in m.index_cap if k > 0)
    m.spec_line_cost = en.Constraint(m.index_row, m.index_col,
                                     rule=spec_line_cost_rule)

    def cost_range_limit_rule(m, i, j, k):
        return m.cost_range_bool[i, j, k] <= m.l_bool[i, j]
    m.cost_range_limit = en.Constraint(m.index_row, m.index_col, m.index_cap,
                                       rule=cost_range_limit_rule)

    def cost_range_limit_2_rule(m, i, j, k):
        if k == 0 or k == last_cost_step:
            return en.Constraint.Skip
        else:
            return m.cost_range_bool[i, j, k+1] <= m.cost_range_bool[i, j, k]
    m.cost_range_limit_2 = en.Constraint(m.index_row, m.index_col, m.index_cap,
                                         rule=cost_range_limit_2_rule)

    def cost_range_limit_3_rule(m, i, j):
        return 0 <= m.line_capacity[i, j] - \
            sum((m.pow_step_ranges[k] - m.pow_step_ranges[k-1]) *
                m.cost_range_bool[i, j, k+1]
                for k in m.index_cap if (k > 0 and k < last_cost_step))
    m.cost_range_limit_3 = en.Constraint(m.index_row, m.index_col,
                                         rule=cost_range_limit_3_rule)

    def cost_range_limit_4_rule(m, i, j):
        return 0 <= sum((m.pow_step_ranges[k] - m.pow_step_ranges[k-1]) *
                        m.cost_range_bool[i, j, k]
                        for k in m.index_cap if k > 0) - m.line_capacity[i, j]
    m.cost_range_limit_4 = en.Constraint(m.index_row, m.index_col,
                                         rule=cost_range_limit_4_rule)

    m.ccConstraints = en.ConstraintList()

    def obj_rule_1(m):
        # OBJ1: Revenue-Oriented Prize Collection
        return sum(m.th[i]*m.q_bool[i]*m.q[i] for i in m.index_row) - \
            sum(m.line_cost[i, j] * m.line_length[i, j]
                for i in m.index_row for j in m.index_col)

    def obj_rule_2(m):
        # OBJ2: Profit-Oriented Prize Collection
        return sum((m.th[i]-m.dist_cost[i])*m.q_bool[i]*m.q[i]
                   for i in m.index_row) - \
                   sum(m.line_cost[i, j] * m.line_length[i, j]
                       for i in m.index_row for j in m.index_col)
    if obj_case == 1:
        m.obj = en.Objective(rule=obj_rule_1, sense=en.maximize)
    elif obj_case == 2:
        m.obj = en.Objective(rule=obj_rule_2, sense=en.maximize)
    else:
        raise ValueError('Objective method is selected wrongly! Please enter '
                         '"1" for Revenue-Oriented Prize Collection or "2" '
                         'for Profit-Oriented Prize Collection')

    solver = SolverFactory('gurobi', solver_io='python')
    solver.options["MIPGap"] = 1e-4
    solver.options["BarConvTol"] = 1e-8
    # solver.options["SolTimeLimit"] = 1200


    def convertYsToNetworkx():
        """Convert the m's Y variables into a networkx object."""
        ans = nx.Graph()
        edges = [(i, j) for i in m.index_row
                 for j in m.index_col if (en.value(m.l_bool[i, j]) == 1)]
        ans.add_edges_from(edges)
        return ans


    def createConstForCC(m, cc):
        cc = dict.fromkeys(cc)
        return sum(m.l_bool[i, j] for i in m.index_row
                   for j in m.index_col
                   if ((i in cc) and (j in cc))) <= len(cc) - 1

    done = False
    results = None
    while not done:
        # Solve once and add subtour elimination constraints if necessary
        # Finish when there are no more subtours
        results = solver.solve(m, logfile=path + "/Outputs/log.txt", report_timing=True, tee=True)
        # print(value(m.obj))
        graph = convertYsToNetworkx()
        ccs = list(nx.connected_component_subgraphs(graph))
        for cc in ccs:
            m.ccConstraints.add(createConstForCC(m, cc))
        number_of_nodes = sum(m.q_bool[i] for i in m.index_row)
        if len(ccs) == 0:
            done = True
        elif ccs[0].number_of_nodes() == number_of_nodes:
            done = True
    term_cond = results.solver.termination_condition == TerminationCondition.optimal
    print('term_cond: ', term_cond)
    '''
    ##################
    # save variable values to a csv file 
    var_names = [name(v) for v in m.component_objects(Var)]
    list_of_vars = [value(v[index]) for v in m.component_objects(Var) for index in v]
    df = pd.DataFrame()
    result_series = pd.Series(list_of_vars, index=var_names)
    result_series.to_csv(outCSV)
    if done:
        results.write()
        print('obejctive = ', value(m.obj))
    ###################
    '''
    edge_list = []
    dist_inv = 0
    trans_inv = 0
    covered_demand = 0
    trans_line_length = 0
    dh = np.zeros(n+6)
    for i in range(n):
        dh[i] = en.value(m.q_bool[i])
        covered_demand += demand_coherent_area[i] * en.value(m.q_bool[i])
        dist_inv += dh[i]*demand_coherent_area[i] * dist_cost_coherent_area[i]
    for i in range(n):
        for j in range(n):
            if en.value(m.l_bool[i, j]) == 1:
                trans_inv += en.value(m.line_cost[i, j]) * \
                                en.value(m.line_length[i, j])
                trans_line_length += en.value(m.line_length[i, j])
                edge_list.append([i, j, en.value(m.line_capacity[i, j])])
    # meter to km
    trans_line_length /= 1000
    dist_spec_cost = dist_inv/covered_demand
    trans_spec_cost = trans_inv/covered_demand
    dh[n: n+6] = covered_demand, dist_inv, dist_spec_cost, trans_inv, \
        trans_spec_cost, trans_line_length
    return term_cond, dh, np.array(edge_list)
