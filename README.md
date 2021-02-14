# Residential-Solar-Cost-Modeling
This code models the effect of residential solar installation on energy grid prices


The model creates a House class object that takes as parameters information about geographic location and solar adoption. 


The class contains six private functions:

The EnergyDemand function pulls the energy usage data associated with the closest TMY3 weather station. This data is collected by the Office of Energy Efficiency 
& Renewable Energy. 

The SolarSupply function pulls solar radiation data associated with the closest TMY3 weather station and uses this data to calculate the potential output of a 
1 sqft solar panel. This data is collected by the National Renewable Energy Labortaory.

The RealDemand function substracts the output of the SolarSupple function from the output of the EnergyDemand function.

The GridCost function pulls enery pricing data from a nearby energy utility. This data is collected by the Energy Information Administration.

The SolarSavings function multiplies the SolarSupply by the GridCost output less an estimated cost of solar panel maintainence.

The RealCost function multiplies the EnergyDemand output by the GridCost output and subtracts the SolarSavings output to find the real cost to the household. 


The class contains two public functions:

The SavingsInRange function finds the savings for a house over a given date range

The CostInRange function find the total energy expenses for a house over a given date range



