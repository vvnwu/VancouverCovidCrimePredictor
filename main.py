import pandas as pd

# LOAD & PREPROCESSING
# aggregate mobility data by week
mobility_raw = pd.read_csv("data/Processed Data/vancouver-mobility-data.csv")
mobility_raw['date'] = pd.to_datetime(mobility_raw['date'])
mobility_raw['WEEK'] = mobility_raw['date'].dt.isocalendar().week
mobility = mobility_raw[['WEEK',
                         'retail_and_recreation_percent_change_from_baseline',
                         'grocery_and_pharmacy_percent_change_from_baseline',
                         'parks_percent_change_from_baseline',
                         'transit_stations_percent_change_from_baseline',
                         'workplaces_percent_change_from_baseline',
                         'residential_percent_change_from_baseline']].groupby(['WEEK']).agg(['mean'])

# aggregate crime data by week
crime_raw = pd.read_csv("data/Raw Data/crimedata_csv_all_years.csv")
crime_raw['YEAR'] = crime_raw['YEAR'].astype(str)
crime_raw['MONTH'] = crime_raw['MONTH'].astype(str)
crime_raw['DAY'] = crime_raw['DAY'].astype(str)
crime_raw['date'] = crime_raw['YEAR'] + '-' + crime_raw['MONTH'] + '-' + crime_raw['DAY']
crime_raw['date'] = pd.to_datetime(crime_raw['date'])

crime_raw = crime_raw[['TYPE', 'NEIGHBOURHOOD', 'date', 'DAY']].groupby(['TYPE','NEIGHBOURHOOD', pd.Grouper(key='date', freq='W-MON')]).count().reset_index()
crime_raw.columns = ['TYPE', 'NEIGHBOURHOOD', 'DATE', 'COUNT']

# calculate covid crime increase
precovid_start = '2017-01-01'
covid_start = '2020-03-11'

precovid_mask = (crime_raw['DATE'] > precovid_start) & (crime_raw['DATE'] < covid_start)
covid_mask = (crime_raw['DATE'] > covid_start)

precovid_crime = crime_raw.loc[precovid_mask]
precovid_crime['WEEK'] = precovid_crime['DATE'].dt.isocalendar().week
precovid_crime = precovid_crime[['TYPE', 'NEIGHBOURHOOD', 'WEEK', 'COUNT']].groupby(['TYPE','NEIGHBOURHOOD', 'WEEK']).mean().reset_index()
precovid_crime.columns = ['TYPE', 'NEIGHBOURHOOD', 'WEEK', 'PRECOVID_MEAN_COUNT']

covid_crime = crime_raw.loc[covid_mask]
covid_crime['WEEK'] = covid_crime['DATE'].dt.isocalendar().week
covid_crime.columns = ['TYPE', 'NEIGHBOURHOOD', 'DATE', 'COVID_COUNT', 'WEEK']

crime = pd.merge(covid_crime, precovid_crime, how='left', left_on=['TYPE', 'NEIGHBOURHOOD', 'WEEK'], right_on=['TYPE', 'NEIGHBOURHOOD', 'WEEK'])
crime = crime.dropna()
crime['CRIME_INCREASE_PERCENT'] = crime['COVID_COUNT'] - crime['PRECOVID_MEAN_COUNT']
crime['CRIME_INCREASE_PERCENT'] = crime['CRIME_INCREASE_PERCENT']/crime['PRECOVID_MEAN_COUNT']
crime['CRIME_INCREASE'] = crime['CRIME_INCREASE_PERCENT'] > 0


# transpose census data & normalize counts (convert to proportions)
census_commute = pd.read_csv("data/Processed Data/census-2016-commute-to-work-by-neighbourhood.csv")
census_commute = census_commute.transpose()
census_commute.columns = census_commute.iloc[1]
census_commute = census_commute.drop(census_commute.index[1])
census_commute = census_commute.drop(census_commute.index[0])
census_commute = census_commute.reset_index()
census_commute.iloc[:, 2:] = census_commute.iloc[:, 2:].div(census_commute.iloc[:, 1], axis=0)

census_age = pd.read_csv("data/Processed Data/census-2016-population-by-age-by-neighbourhood.csv")
census_age = census_age.transpose()
census_age.columns = census_age.iloc[1]
census_age = census_age.drop(census_age.index[1])
census_age = census_age.drop(census_age.index[0])
census_age = census_age.reset_index()
census_age.iloc[:, 1] = census_age.iloc[:, 1].str.replace(',', '', regex=False)
census_age.iloc[:, 1:] = census_age.iloc[:, 1:].astype('int64')
census_age.iloc[:, 2:] = census_age.iloc[:, 2:].div(census_age.iloc[:, 1], axis=0)

census_household = pd.read_csv("data/Processed Data/census-2016-household-income-by-neighbourhood.csv")
census_household = census_household.transpose()
census_household.columns = census_household.iloc[1]
census_household = census_household.drop(census_household.index[1])
census_household = census_household.drop(census_household.index[0])
census_household = census_household.reset_index()
census_household.iloc[:, 2:] = census_household.iloc[:, 2:].div(census_household.iloc[:, 1], axis=0)

census_income = pd.read_csv("data/Processed Data/census-2016-income-by-neighbourhood.csv")
census_income = census_income.transpose()
census_income.columns = census_income.iloc[1]
census_income = census_income.drop(census_income.index[1])
census_income = census_income.drop(census_income.index[0])
census_income = census_income.reset_index()
census_income.iloc[:, 2:] = census_income.iloc[:, 2:].div(census_income.iloc[:, 1], axis=0)

# clean neighbourhood names
crime['NEIGHBOURHOOD'] = crime['NEIGHBOURHOOD'].str.strip()
crime['NEIGHBOURHOOD'] = crime['NEIGHBOURHOOD'].str.upper()
crime['NEIGHBOURHOOD'] = crime['NEIGHBOURHOOD'].str.replace(' ', '-', regex=False)

census_commute['index'] = census_commute['index'].str.strip()
census_commute['index'] = census_commute['index'].str.upper()
census_commute['index'] = census_commute['index'].str.replace(' ', '-', regex=False)

census_income['index'] = census_income['index'].str.strip()
census_income['index'] = census_income['index'].str.upper()
census_income['index'] = census_income['index'].str.replace(' ', '-', regex=False)

census_age['index'] = census_age['index'].str.strip()
census_age['index'] = census_age['index'].str.upper()
census_age['index'] = census_age['index'].str.replace(' ', '-', regex=False)

census_household['index'] = census_household['index'].str.strip()
census_household['index'] = census_household['index'].str.upper()
census_household['index'] = census_household['index'].str.replace(' ', '-', regex=False)

# merge census, mobility and crime data
df = pd.merge(crime, mobility, how='left', left_on=['WEEK'], right_on=['WEEK'])
df = pd.merge(df, census_commute, how='left', left_on=['NEIGHBOURHOOD'], right_on=['index'])
df = pd.merge(df, census_income, how='left', left_on=['NEIGHBOURHOOD'], right_on=['index'])
df = pd.merge(df, census_age, how='left', left_on=['NEIGHBOURHOOD'], right_on=['index'])
df = pd.merge(df, census_household, how='left', left_on=['NEIGHBOURHOOD'], right_on=['index'])
df = df.dropna()
df = df.drop(['index_x', 'index_y'], axis=1)
df.iloc[:, 14:] = df.iloc[:, 14:].astype('float64')

# calculate parameters with greatest correlation to determining crime increase
correlation = df.corr(method='spearman')
crime_correlation = correlation['CRIME_INCREASE']
crime_correlation = crime_correlation.drop(['COVID_COUNT', 'PRECOVID_MEAN_COUNT', 'CRIME_INCREASE_PERCENT', 'CRIME_INCREASE'])
crime_correlation = crime_correlation.abs()
crime_correlation = crime_correlation.sort_values(ascending=False)
