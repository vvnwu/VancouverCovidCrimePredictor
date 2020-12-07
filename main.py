
import pandas as pd


# load data
census = pd.read_csv("data/Raw Data/98-400-X2016114_English_CSV_data.csv")
crime_raw = pd.read_csv("data/Raw Data/crimedata_csv_all_years.csv")
mobility = pd.read_csv("data/Raw Data/2020_CA_Region_Mobility_Report.csv")
# PREPROCESSING
# aggregate time data
mobility['date'] = pd.to_datetime(mobility['date'])
# mobility = df.

crime_raw['YEAR'] = crime_raw['YEAR'].astype(str)
crime_raw['MONTH'] = crime_raw['MONTH'].astype(str)
crime_raw['DAY'] = crime_raw['DAY'].astype(str)
crime_raw['date'] = crime_raw['YEAR'] + '-' + crime_raw['MONTH'] + '-' + crime_raw['DAY']
crime_raw['date'] = pd.to_datetime(crime_raw['date'])

crime = crime_raw[['']]


