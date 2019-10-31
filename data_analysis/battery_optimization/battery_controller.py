# ==============================================================================
#    THIS CLASS WILL BE IMPLEMENTED BY COMPETITORS
# ==============================================================================
import numpy as np
import sys
from ortools.linear_solver import pywraplp
class BatteryContoller(object):
    """ The BatteryContoller class handles providing a new "target state of charge"
        at each time step.

        This class is instantiated by the simulation script, and it can
        be used to store any state that is needed for the call to
        propose_state_of_charge that happens in the simulation.

        The propose_state_of_charge method returns the state of
        charge between 0.0 and 1.0 to be attained at the end of the coming
        quarter, i.e., at time t+15 minutes.

        The arguments to propose_state_of_charge are as follows:
        :param site_id: The current site (building) id in case the model does different work per site
        :param timestamp: The current timestamp inlcuding time of day and date
        :param battery: The battery (see battery.py for useful properties, including current_charge and capacity)
        :param actual_previous_load: The actual load of the previous quarter.
        :param actual_previous_pv_production: The actual PV production of the previous quarter.
        :param price_buy: The price at which electricity can be bought from the grid for the
          next 96 quarters (i.e., an array of 96 values).
        :param price_sell: The price at which electricity can be sold to the grid for the
          next 96 quarters (i.e., an array of 96 values).
        :param load_forecast: The forecast of the load (consumption) established at time t for the next 96
          quarters (i.e., an array of 96 values).
        :param pv_forecast: The forecast of the PV production established at time t for the next
          96 quarters (i.e., an array of 96 values).

        :returns: proposed state of charge, a float between 0 (empty) and 1 (full).
    """
    def propose_state_of_charge(self,
                                site_id,
                                timestamp,
                                battery,
                                actual_previous_load,
                                actual_previous_pv_production,
                                price_buy,
                                price_sell,
                                load_forecast,
                                pv_forecast):
        if hasattr(self, 'count'):
            self.count += 1
        else:
            self.count = 1
        solver = pywraplp.Solver('SolverSimpleSystem',pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)

        initialBattery=battery.current_charge*battery.capacity
        batteryCapacity=battery.capacity
        chargingLimit=battery.charging_power_limit/4
        dischargingLimit=-(battery.discharging_power_limit/4)
        chargingEfficiency=battery.charging_efficiency
        dischargeEfficiency=battery.discharging_efficiency

        nTimeIntervals=int(np.ceil(((((battery.capacity-initialBattery)/battery.charging_power_limit)/battery.charging_efficiency)*4)+
                         (((battery.capacity/(-battery.discharging_power_limit))/battery.discharging_efficiency)*4)))+3
        # nTimeIntervals=int(np.ceil((((battery.capacity/battery.charging_power_limit)/battery.charging_efficiency)*4)+
        #                  (((battery.capacity/(-battery.discharging_power_limit))/battery.discharging_efficiency)*4)))+2     

        GtoBSrcs=[]
        GtoBDsts=[]
        BtoFSrcs=[]
        BtoFDsts=[]
        BtoGSrcs=[]
        BtoGDsts=[]
        GtoFs=[]
        PtoBSrcs=[]
        PtoBDsts=[]
        PtoGs=[]
        ConsArr=[]

        objective = solver.Objective()

        target_battery = (initialBattery/batteryCapacity)

        for i in range(nTimeIntervals):
            GtoBSrcs.append(solver.NumVar(0,solver.infinity(),"GtoBSrc"+str(i+1)))
            GtoBDsts.append(solver.NumVar(0,solver.infinity(),"GtoBDst"+str(i+1)))
            BtoFSrcs.append(solver.NumVar(0,solver.infinity(),"BtoFSrc"+str(i+1)))
            BtoFDsts.append(solver.NumVar(0,solver.infinity(),"BtoFDst"+str(i+1)))
            BtoGSrcs.append(solver.NumVar(0,solver.infinity(),"BtoGSrc"+str(i+1)))
            BtoGDsts.append(solver.NumVar(0,solver.infinity(),"BtoGDst"+str(i+1)))
            GtoFs.append(solver.NumVar(0,solver.infinity(),"GtoF"+str(i+1)))
            PtoBSrcs.append(solver.NumVar(0,solver.infinity(),"PtoBSrcs"+str(i+1)))   
            PtoBDsts.append(solver.NumVar(0,solver.infinity(),"PtoBDsts"+str(i+1)))   
            PtoGs.append(solver.NumVar(0,solver.infinity(),"PtoG"+str(i+1)))

            real_consumption = max(load_forecast[i]-pv_forecast[i],0)

            # Facility requirement should be met from either the grid or the battery
            constraint = solver.Constraint(real_consumption,real_consumption)
            constraint.SetCoefficient(BtoFDsts[i],1)
            constraint.SetCoefficient(GtoFs[i],1)
            ConsArr.append(constraint)

            # Excess PV production should go to battery or to grid
            if pv_forecast[i] > load_forecast[i]:
                excess_pv = pv_forecast[i]-load_forecast[i]
                constraint = solver.Constraint(excess_pv,excess_pv)
                constraint.SetCoefficient(PtoBSrcs[i],1)
                constraint.SetCoefficient(PtoGs[i],1)        
                ConsArr.append(constraint)
            else:
                constraint = solver.Constraint(0,0)
                constraint.SetCoefficient(PtoBSrcs[i],1)
                constraint.SetCoefficient(PtoGs[i],1)
                ConsArr.append(constraint)        

            # Battery can only give what it has from the past
            constraint = solver.Constraint(-solver.infinity(),initialBattery)
            constraint.SetCoefficient(BtoFSrcs[i],1)
            constraint.SetCoefficient(BtoGSrcs[i],1)
            constraint.SetCoefficient(GtoBDsts[i],-1)
            constraint.SetCoefficient(PtoBDsts[i],-1)       
            for j in range(i):
                constraint.SetCoefficient(BtoFSrcs[j],1)
                constraint.SetCoefficient(BtoGSrcs[j],1)
                constraint.SetCoefficient(GtoBDsts[j],-1)
                constraint.SetCoefficient(PtoBDsts[j],-1)        
            ConsArr.append(constraint)

            # Maximum battery can give in one step
            constraint = solver.Constraint(0,dischargingLimit)
            constraint.SetCoefficient(BtoFSrcs[i],1)
            constraint.SetCoefficient(BtoGSrcs[i],1)
            ConsArr.append(constraint)      

            # Maximum battery can take is upto 100%
            constraint = solver.Constraint(-solver.infinity(),(batteryCapacity-initialBattery))
            constraint.SetCoefficient(GtoBDsts[i],1)
            constraint.SetCoefficient(PtoBDsts[i],1)
            constraint.SetCoefficient(BtoFSrcs[i],-1)
            constraint.SetCoefficient(BtoGSrcs[i],-1)
            for j in range(i):
                constraint.SetCoefficient(BtoFSrcs[j],-1)
                constraint.SetCoefficient(BtoGSrcs[j],-1)
                constraint.SetCoefficient(GtoBDsts[j],1)
                constraint.SetCoefficient(PtoBDsts[j],1)        
            ConsArr.append(constraint) 

            # Maximum battery can take for one step
            constraint = solver.Constraint(0,chargingLimit)
            constraint.SetCoefficient(GtoBSrcs[i],1)
            constraint.SetCoefficient(PtoBSrcs[i],1)
            ConsArr.append(constraint)     

            # Battery only receives .chargingEfficiency% of what is given by the grid
            constraint = solver.Constraint(0,0)
            constraint.SetCoefficient(GtoBSrcs[i],chargingEfficiency)
            constraint.SetCoefficient(GtoBDsts[i],-1)

            # Battery only receives .chargingEfficiency% of what is given by PV
            constraint = solver.Constraint(0,0)
            constraint.SetCoefficient(PtoBSrcs[i],chargingEfficiency)
            constraint.SetCoefficient(PtoBDsts[i],-1)    

            # Facility only receives .dischargingEfficiency% of what is given by the battery
            constraint = solver.Constraint(0,0)
            constraint.SetCoefficient(BtoFSrcs[i],dischargeEfficiency)
            constraint.SetCoefficient(BtoFDsts[i],-1)   

            # Grid only receives .dischargingEfficiency% of what is given by the battery
            constraint = solver.Constraint(0,0)
            constraint.SetCoefficient(BtoGSrcs[i],dischargeEfficiency)
            constraint.SetCoefficient(BtoGDsts[i],-1)       

            objective.SetCoefficient(GtoBSrcs[i],price_buy[i])
            objective.SetCoefficient(GtoFs[i],price_buy[i])    
            objective.SetCoefficient(BtoGSrcs[i],-price_sell[i])
            objective.SetCoefficient(PtoGs[i],-price_sell[i])

        objective.SetMinimization()
        retval = solver.Solve()
        retval = (initialBattery/batteryCapacity)
        retval += ((GtoBDsts[0].solution_value()+PtoBDsts[0].solution_value()-
                    BtoGSrcs[0].solution_value()-BtoFSrcs[0].solution_value())/batteryCapacity)  
        return retval
