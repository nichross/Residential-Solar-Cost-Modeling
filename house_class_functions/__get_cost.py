import requests
import pandas as pd
from bs4 import BeautifulSoup

# call API
url = 'https://api.openei.org/utility_rates?version=3&format=csv&api_key=ggjYPgfPjgFWDYRaib5exrIMzmmdlNAhBNfIArPm&lat=40.5&lon=-80.233&sector=Residential'

# read in data and find url most recent residential data
station_data = pd.read_csv(url, header=0)
station_data['enddate'] = pd.to_datetime(station_data.enddate)
station_data = station_data[station_data.name.isin(['Residential Service'])]
target_row = station_data.loc[station_data['enddate'].idxmax()]
cost_url = str(target_row['uri']) + '#3__Energy'

page = requests.get(cost_url)
soup = BeautifulSoup(page.content, 'html.parser')
rate_table = soup.find(id='energy_rate_strux_table')
table_row = rate_table.find_all(class_='strux_view_row tier_bottom')
print(table_row)
