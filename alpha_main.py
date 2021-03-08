'''
Purpose: Model the change in revenue assoicated with transitions to residential solar
User Inputs: Time horizon, solar growth rate, location, number of houses
    initial percent of houses that have solar installations, and the surface area of a residential roof
Modified: March 6, 2021 by NAR
'''
import matplotlib.pyplot as plt
from solar_model import Region

# specify time horizon and solar growth rate for simulation
tr = 10
sgr = 0.1

# Define parameters to instantiate Region object
lat = 40.5
lon = -80.233
loc = lat, lon
num_houses = 100
per_solar = 0.06
roof_area = 1850  # sqft

# Create Region object for each year in the time horizon and that years revenue
revenue_dict = dict()

# plt testing: revenue_dict = {1: 100000, 2: 90000, 3: 70000, 4: 40000, 5: 100}

for year in range(0, tr):
    region = Region(loc, num_houses, per_solar, roof_area)
    #print(region.annual_revenue)
    this_revenue = region.annual_revenue
    revenue_dict[year] = this_revenue
    per_solar = per_solar * (1 + sgr)

# Plot the regional electricity revenue vs time
ordered_years = sorted(revenue_dict.items())
years, revenue = zip(*ordered_years)
plt.plot(years, revenue)
plt.show()
