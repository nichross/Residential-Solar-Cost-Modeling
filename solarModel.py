'''
Purpose: Create a class structure to model residential solar units in a region
Modified: March 20, 2021 by NAR
'''
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta

# House only packages (PySam) - also need requests module -
import PySAM.ResourceTools as tools  # MOVE BACK TO FILES FOLDER
import PySAM.Singleowner as so
import PySAM.Pvwattsv7 as pv


# Define a function to convert solar set asides percentages to solar penetration rates
def ssa_to_solar_pen(ssa):
    st_sales = 145580383000
    region_pop = 300286
    st_pop = 12801989
    per_res = 0.8
    avg_consum = 10402
    num_houses = 138058
    solar_pen = st_sales * (region_pop/st_pop) * ssa * per_res * (1/avg_consum) * (1/num_houses)
    return solar_pen

# Define a Region class
class Region:
    def __init__(self, loc, solar_pen):
        self.loc = loc
        self.solar_pen = solar_pen
        self.num_houses = self.get_num_houses()
        self.usage_data = self.get_usage_data()
        self.wholesale_prices = self.get_wholesale_prices()
        self.utility_prices = self.get_utility_prices()
        self.fixed_prices = self.get_fixed_prices()
        self.households = self.create_households()
        self.region_data = self.get_region_data()
        self.annual_profit = self.region_data['profit'].sum()
        self.annual_demand = self.region_data['total_demand'].sum()
        self.utility_price = self.region_data['utility_prices'].unique()[0]

    def get_num_houses(self):
        # Import census data as pandas df
        df = pd.read_csv('census_household_data.csv', header=0)

        # Create dictionary for city at location
        usage_file_dict = {(40.5, -80.233): 'pittsburgh',
                           (38.867, -77.033): 'washington dc'}

        # Get city at location
        city = usage_file_dict[self.loc]

        # Get the number of houses in the city
        num_houses = df.loc[(df['city'] == city) & (df['year'] == 2019), 'households'].iloc[0]

        # Return number of houses
        return num_houses

        # Return smaller number of houses for testing
        #return 100

    def get_usage_data(self):
        # Create dictionary for datafiles at locations
        usage_file_dict = {(40.5, -80.233): 'USA_PA_Pittsburgh-Allegheny.County.AP.725205_TMY3_BASE.csv',
                           (38.867, -77.033): 'USA_VA_Arlington-Ronald.Reagan.Washington.Natl.AP.724050_TMY3_BASE.csv'}

        # Get datafile for Region's location
        filename = usage_file_dict[self.loc]

        # import data
        dataset = pd.read_csv(filename, header=0)

        # modify date-time data to match standard format (Note: data is from 2013, 2019 is used for formatting)
        dataset['Date/Time'] = dataset['Date/Time'].replace(to_replace='  ', value='/2019 ', regex=True)
        dataset['Date/Time'] = dataset['Date/Time'].replace(to_replace='24:00:00', value='00:00:00', regex=True)
        dataset['Date/Time'] = pd.to_datetime(dataset['Date/Time'])
        dataset.loc[dataset['Date/Time'].dt.time == datetime.time(0, 0, 0), 'Date/Time'] = dataset['Date/Time'] + timedelta(days=1)
        dataset.loc[dataset['Date/Time'].dt.year == 2020, 'Date/Time'] = dataset['Date/Time'] - timedelta(days=365)
        dataset = dataset.sort_values(by='Date/Time').reset_index()

        # Calculate total electricity usage per hour
        dataset['usage'] = dataset.loc[:, dataset.columns.str.contains('Electricity')].sum(axis=1)

        # Return the hourly electricity usage
        elec_usage = dataset[['Date/Time', 'usage']]
        elec_usage.columns = ['time', 'usage']

        # return df with time and electricity usage
        return elec_usage

    def get_wholesale_prices(self):
        # Import wholesale price data as pandas df
        df = pd.read_csv('ice_wholesale_2019.csv', header=0)

        # Create dictionary for wholesale supplier at location
        usage_file_dict = {(40.5, -80.233): 'PJM WH Real Time Peak'}

        # Get wholesale supplier
        supplier = usage_file_dict[self.loc]

        # Filter for PJM trade dates and average prices (for Pittsburgh)
        pjm_data = df.loc[(df['Price hub'] == supplier)]
        pjm_time_price = pjm_data.loc[:, ['Trade date', 'Wtd avg price $/MWh']]
        pjm_time_price.loc[:, 'Trade date'] = pd.to_datetime(pjm_time_price.loc[:, 'Trade date'])
        pjm_time_price.reset_index(drop=True, inplace=True)
        pjm_time_price.columns = ['time', 'trade_price']

        # Create a pandas df containing all hours in the year
        times = pd.date_range(start='1/1/2019', end='1/1/2020', freq='H', closed='left')
        wholesale_prices = pd.DataFrame(data=times, columns=['time'])

        # Merge datasets
        wholesale_prices = pd.merge(left=wholesale_prices, right=pjm_time_price, how='left', on='time')

        # Get a list of trade prices
        trade_prices = pjm_time_price['trade_price'].tolist()

        # Populate hourly df with appropiate prices
        wholesale_prices['nan_check'] = wholesale_prices['trade_price'].isnull()
        trade_price_ct = 0
        for row in range(len(wholesale_prices)):
            if wholesale_prices.loc[row, 'nan_check']:
                wholesale_prices.loc[row, 'trade_price'] = trade_prices[trade_price_ct]
            elif trade_price_ct == len(trade_prices) - 1:
                wholesale_prices.loc[row, 'trade_price'] = trade_prices[trade_price_ct]
            else:
                trade_price_ct += 1
                wholesale_prices.loc[row, 'trade_price'] = trade_prices[trade_price_ct]

        # Create subset with only time and wholesale price
        wholesale_prices = wholesale_prices[['time', 'trade_price']]

        # Return dataframe times and wholesale prices
        return wholesale_prices

    def get_utility_prices(self):
        # Read in electricity data
        df = pd.read_csv('utility_data.csv', header=0)

        # Index for desired electricity rate
        utility_price = df.loc[(df['Location'] == str(self.loc)) & (df['Service Type'] == 'Standard Offer') & (
                    df['Rate Name'] == 'Other'), 'Rate ($/kWh)'].iloc[0]

        # Create a pandas df containing all hours in the year
        times = pd.date_range(start='1/1/2019', end='1/1/2020', freq='H', closed='left')
        utility_prices = pd.DataFrame(data=times, columns=['time'])
        utility_prices['utility_price'] = utility_price

        # Return df with times and utility prices
        return utility_prices

    def get_fixed_prices(self):
        # Read in electricity data
        df = pd.read_csv('utility_data.csv', header=0)

        # Index for fixed rate ($/mo) convert to ($/hr)
        fixed_price_mo = df.loc[(df['Location'] == str(self.loc)) & (df['Service Type'] == 'Standard Offer') & (
                    df['Cost Type'] == 'Fixed'), 'Fixed Rate ($/mo)'].iloc[0]
        fixed_price_hr = (fixed_price_mo * 12) / 365

        # Calculate the total fixed prices from all houses ($/hr)
        total_fixed_price = fixed_price_hr * self.num_houses

        # Create a pandas df containing all hours in the year
        times = pd.date_range(start='1/1/2019', end='1/1/2020', freq='H', closed='left')
        fixed_prices = pd.DataFrame(data=times, columns=['time'])
        fixed_prices['fixed_price'] = total_fixed_price

        # Return df with times and fixed prices
        return fixed_prices

    def create_households(self):
        # Create list to hold house instances
        households = list()

        # Create solar houses
        solar_houses = int(self.num_houses * self.solar_pen)
        for i in range(0, solar_houses):
            house = House(self.loc, True, self.usage_data)
            households.append(house)

        # Create non-solar houses
        non_solar_houses = self.num_houses - solar_houses
        for i in range(0, non_solar_houses):
            house = House(self.loc, False, self.usage_data)
            households.append(house)

        # Return list of houses
        return households

    def get_region_data(self):
        # Create dataframe containing time, wholesale price, utility price, and fixed price
        times = self.wholesale_prices['time'].tolist()
        wholesale_prices = self.wholesale_prices['trade_price'].tolist()
        utility_prices = self.utility_prices['utility_price'].tolist()
        fixed_prices = self.fixed_prices['fixed_price'].tolist()
        data = {'times': times,
                'wholesale_prices': wholesale_prices,
                'utility_prices': utility_prices,
                'fixed_prices': fixed_prices}
        region_data = pd.DataFrame(data)

        # Add the demand for each house to the dataframe
        total_demand = np.zeros(len(region_data))
        for house in self.households:
            house_demand = house.elec_demand.loc[:, 'elec_demand']
            total_demand += house_demand
        region_data['total_demand'] = total_demand.tolist()

        # Adjust wholesale price to ($/kWh)
        region_data['wholesale_prices'] = region_data['wholesale_prices'] / 1000
        region_data['profit'] = (region_data['total_demand'] * (region_data['utility_prices'] - region_data['wholesale_prices']) + region_data['fixed_prices'])

        # Return region data frame
        return region_data


# Define a House subclass of Region class
class House:
    def __init__(self, loc, has_solar, usage_data):
        self.loc = loc
        self.has_solar = has_solar
        self.usage_data = usage_data
        self.elec_prod = self.get_elec_prod()
        self.elec_demand = self.get_elec_demand()

    def get_elec_prod(self):
        # Check for solar capacity
        if not self.has_solar:
            return None

        '''
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
            generator = pv.default('PVWattsResidential')
            generator.SolarResource.assign({'solar_resource_file': nsrdb_fp})

            # --- Initialize Financial Model --- Not using here
            financial = so.from_existing(generator, 'PVWattsSingleOwner')

            # --- Execute Models ---
            # print('PVWatts V7 - Single Owner Results')
            generator.execute()

            # Make list of hours in a year
            hour_list = pd.date_range(start='1/1/2019', end='1/1/2020', freq='H', closed='left')

            # Get hourly electricity production
            hourly_output = generator.Outputs.gen

            # Create electricity production dataframe
            data = {'time': hour_list, 'elec_prod': hourly_output}
            elec_prod = pd.DataFrame(data=data)

            
            # return electricity production
            return elec_prod
            '''
        # Call stored data
        elec_prod = pd.read_csv('solar_prod_pittsburgh.csv')

        # Change time data type to datetime
        elec_prod['time'] = pd.to_datetime(elec_prod['time'])

        return elec_prod

    def get_elec_demand(self):
        # Check for solar capacity (will be 2 attributes)
        if self.elec_prod is None:
            self.usage_data.columns = ['time', 'elec_demand']
            return self.usage_data

        # Merge production and usage dataframes
        elec_demand = pd.merge(left=self.usage_data, right=self.elec_prod, how='inner', on='time')

        # Calculate net demand
        elec_demand['elec_demand'] = elec_demand['usage'] - elec_demand['elec_prod']

        # Check for excess electricity production and dissipate (set to 0)
        elec_demand.loc[elec_demand['elec_demand'] <= 0, 'elec_demand'] = 0

        # Create a subset with only time and demand
        elec_demand = elec_demand[['time', 'elec_demand']]

        return elec_demand

'''
Test Code

# Define parameters to instantiate Region object
lat = 40.5
lon = -80.233
loc = lat, lon
solar_pen = 0.06

# Create region
region = Region(loc, solar_pen)

'''