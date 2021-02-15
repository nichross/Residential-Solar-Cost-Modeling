# Residential-Solar-Cost-Modeling
This code creates a python model for the effect of residential solar installation on energy grid prices <br /><br /><br /><br /><br />


The model includes a **class object "House"** that takes as parameters information about geographic location and solar adoption.<br /><br />


The House class contains **two public functions**:

The savings_in_range function finds the savings for a house over a given date range

The cost_in_range function finds the total energy expenses for a house over a given date range<br /><br />


The House class contains **nine private functions**:

The get_station function returns the TMY station for the house's city.

The get_coords function returns the latitude and longitude associated with the TMY3 station for the house's city.

The real_cost function returns an array containing hourly energy cost for the household.

The solar_savings function returns the hourly savings from solar installation.

The real_savings function calls the get_cost, get_station, and solar_savings then returns the hourly savings from solar installation. 

The no_solar_cost function returns hourly energy expense for the household.

The energy_demand function returns the energy usage data associated with the closest TMY3 weather station. This data is collected by the Office of Energy Efficiency & Renewable Energy. 

The solar_supply function returns solar radiation data associated with the closest TMY3 weather station. This data is collected by 
the National Renewable Energy Labortaory.

The get_cost function returns the price of energy from a nearby utility. This data is collected by the Energy Information Administration







