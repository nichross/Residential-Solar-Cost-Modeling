# Residential-Solar-Cost-Modeling
This code creates a python model for the effect of residential solar installation on energy grid prices




The model includes a House class object that takes as parameters information about geographic location and solar adoption. 
The class contains eight private functions:


The get_station function returns the TMY station for the house's city

The get_station function returns the latitude and longitude associated with the TMY3 station for the house's city

The energy_demand function pulls the energy usage data associated with the closest TMY3 weather station. This data is collected by the Office of Energy Efficiency 
& Renewable Energy. 

The solar_supply function pulls solar radiation data associated with the closest TMY3 weather station and uses this data to calculate the potential output of a 
1 sqft solar panel. This data is collected by the National Renewable Energy Labortaory.

The real_demand function substracts the output of the solar_supply function from the output of the energy_demand function.

The grid_cost function pulls enery pricing data from a nearby energy utility. This data is collected by the Energy Information Administration.

The solar_savings function multiplies the solar_supply by the grid_cost output less an estimated cost of solar panel maintainence.

The real_cost function multiplies the EnergyDemand output by the GridCost output and subtracts the SolarSavings output to find the real cost to the household. 



The class contains two public functions:

The savings_in_range function finds the savings for a house over a given date range

The cost_in_range function finds the total energy expenses for a house over a given date range



