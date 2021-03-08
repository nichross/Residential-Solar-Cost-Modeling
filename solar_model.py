'''
Purpose: Create a class structure to model residential solar units in a region
Modified: March 6, 2021 by NAR
'''
import pandas as pd
import datetime
from datetime import timedelta

# House only packages (PySam) - also need requests module -
import PySAM.ResourceTools as tools  # MOVE BACK TO FILES FOLDER
import PySAM.Singleowner as so
import PySAM.Pvwattsv7 as pv


# Define a Region class
class Region:
    def __init__(self, loc, num_houses, per_solar, roof_area):
        self.loc = loc
        self.num_houses = num_houses
        self.per_solar = per_solar
        self.roof_area = roof_area
        self.elec_usage = self.get_elec_usage()
        self.elec_price = self.get_elec_price()
        self.households = self.create_households()
        self.annual_revenue = self.get_annual_revenue()

    def get_elec_usage(self):
        # usage files saved locally
        # assuming base load usage (low or high are also options)

        # Create dictionary for datafiles at locations
        usage_file_dict = {(40.5, -80.233): 'USA_PA_Pittsburgh-Allegheny.County.AP.725205_TMY3_BASE.csv'}

        # Get datafile for Region's location
        filename = usage_file_dict[self.loc]

        # import data
        dataset = pd.read_csv(filename, header=0)

        # modify date-time data to match standard format
        dataset['Date/Time'] = dataset['Date/Time'].replace(to_replace='  ', value='/2013 ', regex=True)
        dataset['Date/Time'] = dataset['Date/Time'].replace(to_replace='24:00:00', value='00:00:00', regex=True)
        dataset['Date/Time'] = pd.to_datetime(dataset['Date/Time'])
        dataset.loc[dataset['Date/Time'].dt.time == datetime.time(0, 0, 0), 'Date/Time'] = dataset['Date/Time'] + timedelta(days=1)
        dataset = dataset.set_index('Date/Time')

        # Calculate total electricity usage per hour
        dataset['Total_Electricity'] = dataset.loc[:, dataset.columns.str.contains('Electricity')].sum(axis=1)

        # Return the hourly electricity usage
        elec_usage = dataset['Total_Electricity']
        return elec_usage

    def get_elec_price(self):
        # Read in electricity data
        df = pd.read_csv('utility_data.csv', header=0)

        # Index for desired electricity rate
        elec_price = df.loc[(df['Location'] == str(self.loc)) & (df['Service Type'] == 'Delivery') & (df['Period'] == 1), 'Rate ($/kWh)'].iloc[0]
        return elec_price

    def create_households(self):
        # Create list to hold house instances
        households = list()

        # Create solar houses
        solar_houses = int(self.num_houses * self.per_solar)
        for i in range(0, solar_houses):
            house = House(self.loc, True, self.roof_area, self.elec_usage)
            households.append(house)

        # Create non-solar houses
        non_solar_houses = self.num_houses - solar_houses
        for i in range(0, non_solar_houses):
            house = House(self.loc, False, self.roof_area, self.elec_usage)
            households.append(house)

        # Return list of houses
        return households

    def get_annual_revenue(self):
        # Initialize annual revenue
        annual_revenue = 0

        # Add annual revenue for each house to the annual revenue
        for house in self.households:
            revenue = house.annual_elec_demand * self.elec_price
            annual_revenue += revenue

        # Return annual revenue
        return annual_revenue


# Define a House subclass of Region class
class House:
    def __init__(self, loc, has_solar, roof_area, elec_usage):
        self.loc = loc
        self.has_solar = has_solar
        self.roof_area = roof_area
        self.elec_usage = elec_usage
        self.elec_prod = self.get_elec_prod()
        self.annual_elec_demand = self.get_elec_demand()

    def get_elec_prod(self):
        # Check for solar capacity
        if self.has_solar == False:
            return None

        # My api key and login
        sam_api_key = 'norE6CWLlbzF33Sueavpd0bQkdGkS5WcWCb3jR8p'
        sam_email = 'naross@andrew.cmu.edu'

        # Extract latitude and longitude
        lat, lon = self.loc

        # --- Initialize Solar Resource Fetcher with minimum parameters ---
        # See function documentation for full parameter list
        nsrdbfetcher = tools.FetchResourceFiles(
            tech='solar',
            nrel_api_key=sam_api_key,
            nrel_api_email=sam_email)

        # --- List of (lon, lat) tuples or Shapely points ---
        lon_lats = [(lon, lat)]
        nsrdbfetcher.fetch(lon_lats)

        # --- Get resource data file path ---
        nsrdb_path_dict = nsrdbfetcher.resource_file_paths_dict
        nsrdb_fp = nsrdb_path_dict[lon_lats[0]]
        if nsrdb_fp is not None:

            # --- Initialize Generator ---
            # Change to Residential or None
            generator = pv.default('PVWattsSingleOwner')
            generator.SolarResource.assign({'solar_resource_file': nsrdb_fp})

            # Look at possible outputs
            # help(generator.Outputs)

            # --- Initialize Financial Model --- Not using here
            financial = so.from_existing(generator, 'PVWattsSingleOwner')

            # --- Execute Models ---
            #print('PVWatts V7 - Single Owner Results')
            generator.execute()

            # Make list of hours in a year
            hour_list = pd.date_range(start="2013-01-01", end="2013-12-31 23:00:00", freq='H')

            # Get hourly electricity production
            hourly_output = generator.Outputs.gen

            # Create electricity production dataframe
            elec_prod = pd.DataFrame(data=hourly_output, index=hour_list, columns=['hourly output'])

            # return electricity production
            return elec_prod

        else:
            print('Solar resource file does not exist. Skipping solar simulations.')

    def get_elec_demand(self):
        # Check for solar capacity
        if self.elec_prod is None:
            dataset = self.elec_usage.to_frame()
            annual_elec_demand = dataset['Total_Electricity'].sum()
            return annual_elec_demand

        # Get electriciy usage and electricity production in single dataframe
        dataset = self.elec_usage.to_frame()
        #print(dataset)
        hourly_prod = self.elec_prod['hourly output'].tolist()
        #print(hourly_prod)
        dataset['hourly output'] = hourly_prod
        #print(dataset)

        # Subtract electricity produced from electricity used
        dataset['Electricity Demand'] = dataset['Total_Electricity'] - dataset['hourly output']
        #print(dataset)

        # Zero out negative values
        dataset.loc[dataset['Electricity Demand'] <= 0, 'Electricity Demand'] = 0
        #print(dataset)

        # See other sums
        #total_elec_used = dataset['Total_Electricity'].sum()
        #print(total_elec_used)
        #total_elec_prod = dataset['hourly output'].sum()
        #print(total_elec_prod)

        # Add electricity demand to get annual demand
        annual_elec_demand = dataset['Electricity Demand'].sum()
        return annual_elec_demand


"""
Incremental Development Code

lat = 40.5
lon = -80.233
loc = lat, lon
num_houses = 10
per_solar = 0.06
roof_area = 1850  # sqft


region = Region(loc=loc, num_houses=num_houses, per_solar=per_solar, roof_area=roof_area)
region_households = region.households
first_house = region_households[0]
house_demand = first_house.annual_elec_demand
annual_elec_revenue = region.annual_revenue
print(annual_elec_revenue) """
