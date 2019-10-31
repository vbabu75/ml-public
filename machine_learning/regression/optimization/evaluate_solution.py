import pandas as pd
import numpy as np
import common

def calculate_changeover_cost():
    man_seq = pd.read_csv('manufacture_sequence.csv')
    lines=['A1','A2','B1','B2','B3','C1']
    changeover_costs = {'A1':33536,'A2':15947,'B1':13333,'B2':13333,'B3':13333,'C1':54353.39}
    total_changeover_cost=0
    for line in lines:
        plant = line[0]
        line_no = int(line[1])
        line_seq = man_seq[(man_seq.Plant==plant) & (man_seq.Line==line_no)]
        curr_prod = None
        changes=0
        for index,row in line_seq.iterrows():
            product = row.Product_ID
            if product != curr_prod and not pd.isnull(product):
                if curr_prod != None:
                    changes += 1
                curr_prod = product
        total_changeover_cost += changes*changeover_costs[line]
    return total_changeover_cost

def calculate_production_cost():
    man_seq = pd.read_csv('manufacture_sequence.csv')  
    pro_cos = pd.read_csv('production_cost.csv')
    pro_cap = pd.read_csv('production_capacity.csv')
    
    lines=['A1','A2','B1','B2','B3','C1']
    total_prod_cost=0
    for line in lines:
        plant=line[0]
        line_no = int(line[1])
        line_seq = man_seq[(man_seq.Plant==plant) & (man_seq.Line==line_no)]
        for month in range(37,40):
            month_seq = line_seq[(line_seq.Month==month)]
            for product,days in month_seq.groupby('Product_ID').Product_ID.count().iteritems():
                capacity = pro_cap[(pro_cap.Plant==plant)&
                    (pro_cap.Line==line_no) &(pro_cap.Product==product)].Capacity.values[0]
                pot_prod = capacity*days
                cost_per_mt = pro_cos[(pro_cos.Product_ID==product) &
                                     (pro_cos.Plant==plant)].Production_cost.values[0]
                total_prod_cost += pot_prod*cost_per_mt
    return total_prod_cost

def calculate_delivery_cost():
    shi_reg = pd.read_csv('shipping_region.csv')
    del_cos = pd.read_csv('delivery_cost.csv')
    regions=[]
    for i in range(1,19):
        regions.append('R'+str(i))
    products=[]
    for i in range(1,82):
        products.append('P'+str(i))
    total_delivery_cost=0
    for plant in ['A','B','C']:
        for region in regions:
            region_shipments = shi_reg[(shi_reg.Plant==plant) &
                (shi_reg.Region==region)].Shipping_to_region_quantity.sum()
            del_cost = del_cos[(del_cos.Plant==plant) &
                              (del_cos.Region==region)].Delivery_cost.values[0]
            total_delivery_cost += (region_shipments*del_cost)
    return total_delivery_cost

def calculate_cost():
    fixed_cost=(33536+15947+13333+13333+13333+54353.39)*90
    changeover_cost=calculate_changeover_cost()
    production_cost=calculate_production_cost()
    delivery_cost=calculate_delivery_cost()
    return fixed_cost+changeover_cost+production_cost+delivery_cost

def calculate_revenue():
    dem_pri = pd.read_csv('demand_price.csv')
    shi_reg = pd.read_csv('shipping_region.csv')
    dem_for = pd.read_csv('demand_forecast.csv')
    regions=[]
    for i in range(1,19):
        regions.append('R'+str(i))
    products=[]
    for i in range(1,82):
        products.append('P'+str(i))
    total_revenue=0
    for region in regions:
        for product in products:
            dem_price = dem_pri[(dem_pri.Product_ID==product) &
                               (dem_pri.Region==region)].Demand_price.values[0]
            act_quantity = shi_reg[(shi_reg.Region==region)&
                                  (shi_reg.Product_ID==product)].Shipping_to_region_quantity.sum()
            dem_quantity = dem_for[(dem_for.Region==region)&(dem_for.Product_ID==product)].Demand.sum()
            total_revenue += dem_price*(min(act_quantity,dem_quantity))
    return total_revenue

def get_margin_percent():
    total_revenue = calculate_revenue()
    total_cost = calculate_cost()
    print("Revenue-",total_revenue,'Cost-',total_cost)
    return ((total_revenue-total_cost)*100)/total_cost
        