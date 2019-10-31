def generate_shipping_schedule(dfs):
    pro_cap = dfs['pro_cap']
    dem_for = dfs['dem_for']
    dem_pri = dfs['dem_pri']
    del_cos = dfs
    regions=[]
    product_ids=[]
    shipping_entries=[]
    lines = {'A':[1,2],'B':[1,2,3],'C':[1]}
    for region_id in range(1,19):
        regions.append('R'+str(region_id))
    for product_index in range(1,82):
        product_ids.append('P'+str(product_index))
    man_seq_df = pd.read_csv('manufacture_sequence.csv')
    for month in range(37,40):
        monthly_seq = man_seq_df[man_seq_df.Month==month]
        for plant in ['A','B','C']:
            plant_seq = monthly_seq[monthly_seq.Plant==plant]
            product_shipping_details={}
            for product in product_ids:
                #Get the total production of the product at this plant
                product_shipping_details[product]={}
                total_production=0
                for line in lines[plant]:
                    line_name=plant+str(line)
                    no_of_days = len(plant_seq[(plant_seq.Line==line) & (plant_seq.Product_ID==product)])
                    if no_of_days != 0:
                        line_capacity = pro_cap[(pro_cap.Plant==plant) & 
                            (pro_cap.Line==line) & (pro_cap.Product==product)].Capacity.values[0]
                        quantity_produced=no_of_days*line_capacity
                        total_production += quantity_produced
                #Identify most lucrative region to send and send product till finished
                demand = dem_for[(dem_for.Product_ID==product) &
                        (dem_for.Month==month) & (dem_for.Demand > 0)]
                region_dem_details=[]
                for region in demand.Region.values:
                    region_dem_details.append({'Region':region,
                        'Demand':demand[demand.Region==region].Demand.values[0]})
                for record in region_dem_details:
                    record['Profit']=get_profit(product,line_name,month,dfs)
                region_dem_details.sort(key=lambda x:x['Profit'],reverse=True)
                quantity_left = total_production
                index =0
                while quantity_left > 0:
                    if index == len(region_dem_details):
                        break
                    quantity_to_ship = min(quantity_left,region_dem_details[index]['Demand'])
                    product_shipping_details[product][region_dem_details[index]['Region']]=quantity_to_ship
                    region_dem_details[index]['Quantity_Shipped']=quantity_to_ship
                    quantity_left -= quantity_to_ship
                    index += 1                
            for region in regions:
                for product in product_ids:
                    ship_quantity=0
                    if product in product_shipping_details:
                        if region in product_shipping_details[product]:
                            ship_quantity = product_shipping_details[product][region]
                    shipping_entries.append([plant,region,product,month,ship_quantity])

    sedf = pd.DataFrame(shipping_entries)
    sedf.columns=['Plant','Region','Product_ID','Month','Shipping_to_region_quantity']
    sedf.to_csv('shipping_region.csv',index=False)
generate_shipping_schedule(dfs)