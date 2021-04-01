'''
Purpose: Model the change in revenue assoicated with transitions to residential solar
User Inputs: Time horizon, solar growth rate, location, number of houses
    initial percent of houses that have solar installations, and the surface area of a residential roof
Modified: March 6, 2021 by NAR
'''
import matplotlib.pyplot as plt
from solarModel import Region, ssa_to_solar_pen
import csv
import pandas as pd

# specify time horizon for simulation (Pittsburgh 2020-2030
time_horizon = 10

# Specify starting solar set aside (from state renewable portfolio standard RPS)
ssa_i = 0.005

# Convert ssa's to penetration rates
solar_pen_i = ssa_to_solar_pen(ssa_i)

# Specify target solar set aside (For Pittsburgh - low: old RPS growth 0.01, med: DE RPS 0.03, high: NJ RPS 0.06)
ssa_t = 0.01

# Create list of annual target penetration rates
pen_list = list()
now_pen = ()
for year in range(time_horizon+1):
    now_pen = ((ssa_t - ssa_i) / time_horizon) * year + ssa_i
    pen_list.append(now_pen)

# Specify location
lat = 40.5
lon = -80.233
loc = lat, lon

# Create and fill lists for year and associated profit
profits = list()
years = list()
houses = list()
solar_houses = list()
demand = list()
prices = list()
year = 0
for solar_pen in pen_list:
    # Append year to list
    years.append(year)
    year += 1
    # Create region
    region = Region(loc, solar_pen)
    # Append profit to list
    now_profit = region.annual_profit
    profits.append(now_profit)
    # Append number of houses to list
    now_houses = region.num_houses
    houses.append(now_houses)
    # Append number of solar houses to list
    solar_houses.append(now_houses*solar_pen)
    # Append demand to list
    now_demand = region.annual_demand
    demand.append(now_demand)
    # Utility price
    price = region.utility_price
    prices.append(price)

# Create dataframe
data = {'year': years,
        'profit': profits,
        'number_houses': houses,
        'solar_houses': solar_houses,
        'demand': demand,
        'price': prices}
time_data = pd.DataFrame(data)
time_data['profit_loss'] = time_data['profit'].iloc[0] - time_data['profit']
time_data['fixed_increase_all_houses'] = time_data['profit_loss'] / time_data['number_houses']
time_data['fixed_increase_solar_houses'] = time_data['profit_loss'] / time_data['solar_houses']
time_data['variable_increase'] = time_data['profit_loss'] / time_data['demand']
time_data['variable_increase'] = time_data['variable_increase'] / time_data['price']

# Write years and profits list to csv file
with open('results_1_ssa.csv', mode='w') as simulation_data:
    simulation_writer = csv.writer(simulation_data, delimiter=',')
    simulation_writer.writerow(years)
    simulation_writer.writerow(time_data['fixed_increase_all_houses'].tolist())
    simulation_writer.writerow(time_data['fixed_increase_solar_houses'].tolist())
    simulation_writer.writerow(time_data['variable_increase'].tolist())
