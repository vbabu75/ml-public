import pandas as pd
import numpy as np

def read_csvs():
    dfs={}
    dfs['dem_for']=pd.read_csv('demand_forecast.csv')
    dfs['mod_dem_for']=pd.read_csv('modified_demand_forecast.csv')
    dfs['dem_pri']=pd.read_csv('demand_price.csv')
    dfs['del_cos']=pd.read_csv('delivery_cost.csv')
    dfs['pro_cos']=pd.read_csv('production_cost.csv')
    dfs['pro_cap']=pd.read_csv('production_capacity.csv')
    dfs['cha_day']=pd.read_csv('changeover_days.csv')
    dfs['cha_cos']=pd.read_csv('changeover_cost.csv')
    dfs['fix_cos']=pd.read_csv('fixed_cost.csv')
    return dfs

def get_profit(product_id,line_id,month,dfs):
    dem_for=dfs['dem_for']
    del_cos=dfs['del_cos']
    dem_pri=dfs['dem_pri']
    pro_cos=dfs['pro_cos']
    cha_day=dfs['cha_day']
    plant_id=line_id[0]
    cha_costs={'A1':33536,'A2':15947,'B1':13333,'B2':13333,'B3':13333,'C1':54353}

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
    #cha_days = cha_day.groupby('From')['Days'].mean()[product_id]
    #cha_cost = cha_costs[line_id]*cha_days*0.15
    prod_cost = quantity * unit_prod_cost
    if quantity==0:
        return 0
    profit = (revenue-(prod_cost+del_cost))/quantity
    if profit < 0:
        pass
        #print("PROFIT IS LESS THAN ZERO ",product_id,line_id,month)
    return profit

if __name__ == '__main__':
    dfs = read_csvs()
    print(get_profit('P9','A1',37,dfs)) #262
