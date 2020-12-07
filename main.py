
import pandas as pd


# load data
census = pd.read_csv("data/Raw Data/98-400-X2016114_English_CSV_data.csv")
crime_raw = pd.read_csv("data/Raw Data/crimedata_csv_all_years.csv")
mobility_raw = pd.read_csv("data/Processed Data/vancouver-mobility-data.csv")
# PREPROCESSING
# aggregate time data
mobility_raw['date'] = pd.to_datetime(mobility_raw['date'])
mobility = mobility_raw[['date',
                         'retail_and_recreation_percent_change_from_baseline',
                         'grocery_and_pharmacy_percent_change_from_baseline',
                         'parks_percent_change_from_baseline',
                         'transit_stations_percent_change_from_baseline',
                         'workplaces_percent_change_from_baseline',
                         'residential_percent_change_from_baseline']].groupby([pd.Grouper(key='date', freq='W-MON')]).agg(['mean'])

crime_raw['YEAR'] = crime_raw['YEAR'].astype(str)
crime_raw['MONTH'] = crime_raw['MONTH'].astype(str)
crime_raw['DAY'] = crime_raw['DAY'].astype(str)
crime_raw['date'] = crime_raw['YEAR'] + '-' + crime_raw['MONTH'] + '-' + crime_raw['DAY']
crime_raw['date'] = pd.to_datetime(crime_raw['date'])

crime = crime_raw[['TYPE', 'date', 'NEIGHBOURHOOD', 'DAY']].groupby(['TYPE','NEIGHBOURHOOD', pd.Grouper(key='date', freq='W-MON')]).count().reset_index()
crime = crime[(crime['date']>'2017-01-01')]

