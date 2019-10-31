import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_log_error
from statsmodels.tsa.ar_model import AR
from xgboost import XGBRegressor
from datetime import datetime
from datetime import timedelta
from ortools.linear_solver import pywraplp

def read_csvs():
    dfs={}
    dfs['dem_for']=pd.read_csv('demand_forecast.csv')
    dfs['dem_pri']=pd.read_csv('demand_price.csv')
    dfs['del_cos']=pd.read_csv('delivery_cost.csv')
    dfs['pro_cos']=pd.read_csv('production_cost.csv')
    dfs['pro_cap']=pd.read_csv('production_capacity.csv')
    return dfs

def prepare_lp_variables(month,dfs):
    dem_for = dfs['dem_for']
    pro_cost = dfs['pro_cos']
    pro_cap = dfs['pro_cap']
    dem_price = dfs['dem_pri']
    products={}
    regions={}
    for i in range(1,82):
        products['P'+str(i)]={}
    for i in range(1,19):
        regions['R'+str(i)]={}
    lines={};
    lines['A1']={'Plant':'A','Line':1}
    lines['A2']={'Plant':'A','Line':2}
    lines['B1']={'Plant':'B','Line':1}
    lines['B2']={'Plant':'B','Line':2}
    lines['B3']={'Plant':'B','Line':3}
    lines['C1']={'Plant':'C','Line':1}
    # Get the monthly demand per product sku per region
    dem_for = dem_for[dem_for.Month==month].copy()
    ppd = dem_for.groupby(['Product_ID']).Demand.sum()
    for product_id in products.keys():
        products[product_id]['Demand']=ppd.loc[product_id]
    # Get the capacity for each line and product
    # Calculate the profit per MT of production at a particular line. For now we are ignoring
    # the shipping cost that depends on region of demand and are taking the max of the price
    # across region
    for line_name in lines.keys():
        line = lines[line_name]
        plant_name = line['Plant']
        line_id = line['Line']
        line['Capacity']={}
        line['Profit']={}
        for product_id in products.keys():
            line['Capacity'][product_id]=(pro_cap[(pro_cap.Plant==plant_name)&
                        (pro_cap.Line==line_id)&(pro_cap.Product==product_id)]).Capacity.values[0]
            line['Profit'][product_id] = get_profit(product_id,line_name,month,dfs)
            if line['Profit'][product_id]<0:
                line['Profit'][product_id]=0
    return products,lines

def prepare_test_variables():
    products={'P1':{'Demand':300},'P2':{'Demand':300},'P3':{'Demand':0}}
    lines={'A1':{'Plant':'A','Line':'1','Capacity':{'P1':5,'P2':8,'P3':5},
                 'Profit':{'P1':19,'P2':15,'P3':5}},
           'B2':{'Plant':'B','Line':'2','Capacity':{'P1':5,'P2':8,'P3':0},
                 'Profit':{'P1':21,'P2':17,'P3':5}}}
    return products,lines

def get_profit(product_id,line_id,month,dfs):
    dem_for=dfs['dem_for']
    del_cos=dfs['del_cos']
    dem_pri=dfs['dem_pri']
    pro_cos=dfs['pro_cos']
    plant_id=line_id[0]

    unit_prod_cost = pro_cos[(pro_cos.Product_ID==product_id) &
                       (pro_cos.Plant==plant_id)].Production_cost.values[0]
    if unit_prod_cost==0:
        return 0 #This product cannot be produced in this line.

    r_demand = dem_for[(dem_for.Month==month) &(dem_for.Product_ID==product_id)]
    r_demand.index = r_demand.Region
    r_price = dem_pri[(dem_pri.Product_ID==product_id)]
    r_price.index = r_price.Region
    r_del_cost = del_cos[(del_cos.Plant==plant_id)]
    r_del_cost.index = r_del_cost.Region
    revenue = np.sum(r_demand.Demand*r_price.Demand_price)
    quantity = np.sum(r_demand.Demand)
    del_cost = np.sum(r_demand.Demand*r_del_cost.Delivery_cost)
    prod_cost = quantity * unit_prod_cost
    if quantity==0:
        return 0
    return ((revenue-(prod_cost+del_cost))/quantity)    

def print_objective_summary(unknowns,products,lines):
    profit=0
    total_demand=0
    satisfied_demand=0
    usage={}
    for product_id in sorted(products.keys()):
        total_demand += products[product_id]['Demand']
    for unknown_id in sorted(unknowns.keys()):
        unknown = unknowns[unknown_id]
        uname = unknown.name()
        quantity = unknown.solution_value()
        product_id,line_id = uname.split('-')
        line = lines[line_id]
        product = products[product_id]
        profit += (line['Profit'][product_id]*quantity)
        satisfied_demand += quantity
        if line_id not in usage:
            usage[line_id]=0
        if(quantity > 0):
            usage[line_id] += (quantity/line['Capacity'][product_id])
    print('Total demand :',total_demand)
    print('Satisfied demand :',satisfied_demand)
    print('Total profit :',profit)
    print('Usage :',usage)

def solve_optimization_problem(products,lines):
    solver = pywraplp.Solver('LinearExample',pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
    unknowns={}
    constraints=[]
    #Add the variables of the linear program. These are placeholders for quantity of 
    #product manufactured in each line
    for product_id in sorted(products.keys()):
        product = products[product_id]
        for line_id in sorted(lines.keys()):
            line = lines[line_id]
            prod_lineid_str = product_id+"-"+line_id
            unknowns[prod_lineid_str] = solver.NumVar(0,float(28*(line['Capacity'][product_id])),
                                                      prod_lineid_str)

    # Add the constraints to ensure every line can operate only for 30 days in a month
    for line_id in sorted(lines.keys()):
        line = lines[line_id]
        constraint = solver.Constraint(0,20)
        for product_id in sorted(products.keys()):
            prod_lineid_str = product_id+"-"+line_id
            if line['Capacity'][product_id] > 0:
                constraint.SetCoefficient(unknowns[prod_lineid_str],(1/line['Capacity'][product_id]))
        constraints.append(constraint)

    # Add the constraint to limit the amount produced to monthly demand
    for product_id in sorted(products.keys()):
        product = products[product_id]
        constraint = solver.Constraint(0,product['Demand'])
        for line_id in sorted(lines.keys()):
            line = lines[line_id]
            prod_lineid_str = product_id+"-"+line_id
            constraint.SetCoefficient(unknowns[prod_lineid_str],1)
        constraints.append(constraint)

    #Objective
    objective = solver.Objective()
    for product_id in sorted(products.keys()):
        product = products[product_id]    
        for line_id in sorted(lines.keys()):
            line = lines[line_id]
            prod_lineid_str = product_id+"-"+line_id
            objective.SetCoefficient(unknowns[prod_lineid_str],line['Profit'][product_id])
    objective.SetMaximization()
    print('Number of variables =', solver.NumVariables())
    print('Number of constraints =', solver.NumConstraints())
    solver.Solve()
    print_objective_summary(unknowns,products,lines)
    return unknowns


def get_line_orders(unknowns):
    line_orders={'A1':[],'A2':[],'B1':[],'B2':[],'B3':[],'C1':[]}
    for unknown_id in unknowns:
        unknown = unknowns[unknown_id]
        if unknown.solution_value()==0:
            continue
        product_id,line_id = unknown_id.split('-')
        line_orders[line_id].append(product_id+'-'+str(unknown.solution_value()))
    return line_orders

dfs = read_csvs()
print('Finished reading csvs')
products,lines = prepare_test_variables()
products,lines = prepare_lp_variables(37,dfs)
print('Finished preparing variables')
quantities = solve_optimization_problem(products,lines)
line_orders = get_line_orders(quantities)



