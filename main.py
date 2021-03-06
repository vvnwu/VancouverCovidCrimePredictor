import pandas as pd
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split # Import train_test_split function
from sklearn import metrics #Import scikit-learn metrics module for accuracy calculation
from sklearn.metrics import confusion_matrix
from sklearn import tree

def create_model(df, feature_cols, feature_names, filename):
    # Binary Classification Tree
    #split dataset in features and target variable
    X = df[feature_cols] # Features
    y = df['CRIME_INCREASE'] # Target variable

    # Split dataset into training set and test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3) # 70% training and 30% test

    # Create Decision Tree classifer object
    clf = DecisionTreeClassifier(class_weight=None, criterion='gini', max_depth=None,
                max_features=None, max_leaf_nodes=None,
                min_samples_leaf=1,
                min_samples_split=2, min_weight_fraction_leaf=0.0,
                presort=False, random_state=None, splitter='best')

    # Train Decision Tree Classifer
    clf = clf.fit(X_train,y_train)

    #Predict the response for test dataset
    y_pred = clf.predict(X_test)

    # Model Accuracy
    print("Accuracy:",metrics.accuracy_score(y_test, y_pred))

    print(
    pd.DataFrame(
        confusion_matrix(y_test, y_pred),
        columns=['Predicted No Crime Increase', 'Predicted Crime Increase'],
        index=['True No Crime Increase', 'True Crime Increase']
    )
    )

    fn=feature_names

    cn=['No Crime Increase', 'Crime Increase']
    fig, axes = plt.subplots(nrows = 1,ncols = 1,figsize = (48, 24), dpi=600)

    tree.plot_tree(clf,
                feature_names = fn, 
                class_names=cn,
                max_depth=4,
                fontsize=16,
               filled = True);fig.savefig('exported/{}'.format(filename))
    plt.clf()


def analyze_df(df, name):
    print('================= DATASET: ' + name + ' =================')
    correlation = df.corr(method='spearman')
    crime_correlation = correlation['CRIME_INCREASE']
    crime_correlation = crime_correlation.drop(
        ['COVID_COUNT', 'PRECOVID_MEAN_COUNT', 'CRIME_INCREASE_PERCENT', 'CRIME_INCREASE'])
    crime_correlation = crime_correlation.abs()
    crime_correlation = crime_correlation.sort_values(ascending=False)

    feature_cols = crime_correlation.head(7)
    feature_names = feature_cols.index
    print(feature_cols)

    print('------------------ TOP 3 ATTR ------------------')
    create_model(df, feature_names[0:3], feature_names[0:3], name + "_decision_tree_top3_attributes.png")
    print('------------------ TOP 5 ATTR ------------------')
    create_model(df, feature_names, feature_names, name + "_decision_tree_top5_attributes.png")


def preprocess():
    # LOAD & PREPROCESSING
    # Some preprocessing was already done on Excel. The remaining pre-processing will be done here.
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

    crime_raw = crime_raw[['TYPE', 'NEIGHBOURHOOD', 'date', 'DAY']].groupby(
        ['TYPE', 'NEIGHBOURHOOD', pd.Grouper(key='date', freq='W-MON')]).count().reset_index()
    crime_raw.columns = ['TYPE', 'NEIGHBOURHOOD', 'DATE', 'COUNT']

    # calculate covid crime increase
    precovid_start = '2017-01-01'
    covid_start = '2020-03-11'

    precovid_mask = (crime_raw['DATE'] > precovid_start) & (crime_raw['DATE'] < covid_start)
    covid_mask = (crime_raw['DATE'] > covid_start)

    precovid_crime = crime_raw.loc[precovid_mask]
    precovid_crime['WEEK'] = precovid_crime['DATE'].dt.isocalendar().week
    precovid_crime = precovid_crime[['TYPE', 'NEIGHBOURHOOD', 'WEEK', 'COUNT']].groupby(
        ['TYPE', 'NEIGHBOURHOOD', 'WEEK']).mean().reset_index()
    precovid_crime.columns = ['TYPE', 'NEIGHBOURHOOD', 'WEEK', 'PRECOVID_MEAN_COUNT']

    covid_crime = crime_raw.loc[covid_mask]
    covid_crime['WEEK'] = covid_crime['DATE'].dt.isocalendar().week
    covid_crime.columns = ['TYPE', 'NEIGHBOURHOOD', 'DATE', 'COVID_COUNT', 'WEEK']

    crime = pd.merge(covid_crime, precovid_crime, how='left', left_on=['TYPE', 'NEIGHBOURHOOD', 'WEEK'],
                     right_on=['TYPE', 'NEIGHBOURHOOD', 'WEEK'])
    crime = crime.dropna()
    crime['CRIME_INCREASE_PERCENT'] = crime['COVID_COUNT'] - crime['PRECOVID_MEAN_COUNT']
    crime['CRIME_INCREASE_PERCENT'] = crime['CRIME_INCREASE_PERCENT'] / crime['PRECOVID_MEAN_COUNT']
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
    df = df.drop(['Total - Main mode of commuting for the employed labour force aged 15 years and over in private households with a usual place of work or no fixed workplace address - 25% sample data',
                  'Total - Total income groups in 2015 for the population aged 15 years and over in private households - 25% sample data',
                  '  Without total income',
                  '  With total income',
                  ' Total - Age groups and average age of the population - 100% data ',
                  'Total - Household total income groups in 2015 for private households - 25% sample data',
                  ], axis=1)
    df.iloc[:, 14:] = df.iloc[:, 14:].astype('float64')

    # Export merged data to csv
    df.to_csv(r'exported/merged_data.csv')
    return df


def main():

    df = preprocess()

    analyze_df(df, "All_Crime")

    for type in df['TYPE'].unique():
        type_df = df[df['TYPE'] == type]
        type = type.replace(" ", "_")
        type = type.replace("/", "_")
        analyze_df(type_df, type)

main()