import pandas as pd
import cleanGdpData as gdp
import cleanSafetyData as safety
import cleanSocialSecurityContributionData as social
import cleanUnemploymentData as unemployment

def get_perceived_happiness_dataset():
    df = pd.read_csv('data/perceivedHappiness.csv')
    df.rename(columns={'Entity': 'Country', 'Life satisfaction in Cantril Ladder (World Happiness Report 2021)': 'Value'}, inplace=True)
    mask = (df['Year'] >= 2012) & (df['Year'] <= 2021)
    df = df[mask]
    return df

def get_countries_list(dataset):
    list_countries = dataset['Country'].unique()
    return list_countries

def intersection(list1, list2):
    list = [value for value in list1 if value in list2]
    return list

def get_missing_values(dataset, all_countries):
    dataset = drop_rows_not_in_countries(dataset, all_countries)
    list_countries = get_countries_list(dataset)
    min_year = 2012
    max_year = 2021
    for country in list_countries:
        for year in range (min_year, max_year + 1):
            row = dataset.loc[(dataset['Country'] == country) & (dataset['Year'] == year)]
            if (row.empty == True):
                boolean_before = True
                boolean_after = True
                year_after = year + 1
                year_before = year - 1
                while (boolean_before or boolean_after):
                    if (boolean_before):
                        row_before = dataset.loc[(dataset['Country'] == country) & (dataset['Year'] == year_before)]
                        if (not row_before.empty):
                            boolean_before = False
                        elif (year_before <= min_year):
                            boolean_before = False
                        else:
                            year_before-=1
                    if (boolean_after):
                        row_after = dataset.loc[(dataset['Country'] == country) & (dataset['Year'] == year_after)]
                        if (not row_after.empty):
                            boolean_after = False
                        elif (year_after >= max_year):
                            boolean_after = False
                        else:
                            year_after+=1
                if (row_before.empty and not row_after.empty):
                    new_value = row_after.iloc[0]['Value']
                if (not row_before.empty and row_after.empty):
                    new_value = row_before.iloc[0]['Value']
                if (not row_before.empty and not row_after.empty):
                    value_after = row_after.iloc[0]['Value']
                    value_before = row_before.iloc[0]['Value']
                    new_value = (value_before + value_after)/2
                if (row_before.empty and row_after.empty):
                    print('ERROR ERROR I REPEAT ERROR')
                new_row = pd.DataFrame({'Country': country, 'Year': year, 'Value': new_value},index=[0])
                dataset = pd.concat([new_row, dataset.loc[:]]).reset_index(drop=True)
    #verify
    """for country in list_countries:
        print(country)
        nbr_rows = len(dataset[dataset.Country == country])
        print(nbr_rows)"""

    return dataset


def drop_rows_not_in_countries(dataset, countries_list):
    dataset = dataset[dataset['Country'].isin(countries_list)]
    return dataset

def get_all_datasets():
    #perceived_happiness
    perceived_happiness_dataset = get_perceived_happiness_dataset()
    perceived_happiness_dataset.drop("Code", inplace=True, axis=1)

    #safety
    safety_dataset = safety.safety_out_of_10()
    safety_dataset.rename(columns={'Safety Index': 'Value'}, inplace=True)

    #gdp
    gdp_dataset = gdp.gdp_out_of_10()
    gdp_dataset.drop("Country Code", inplace=True, axis=1)
    gdp_dataset.drop("Value", inplace=True, axis=1)
    gdp_dataset.rename(columns={'GDP': 'Value'}, inplace=True)
    gdp_dataset['Year'] = gdp_dataset['Year'].astype(int)

    #social security contribution
    social_security_contribution_dataset = social.security_contribution_out_of_10()
    social_security_contribution_dataset.rename(columns={'Social Security Employer Contribution Index': 'Value'},
                                                inplace=True)
    social_security_contribution_dataset['Year'] = social_security_contribution_dataset['Year'].astype(int)
    social_security_contribution_dataset['Value'] = social_security_contribution_dataset['Value'].astype(float)

    #unemployment
    unemployment_dataset = unemployment.unemployment_out_of_ten()
    unemployment_dataset.rename(columns={'Unemployment Index': 'Value'}, inplace=True)


    #countries included in all datasets
    perceived_happiness_countries = get_countries_list(perceived_happiness_dataset)
    safety_countries = get_countries_list(safety_dataset)
    gdp_countries = get_countries_list(gdp_dataset)
    social_security_contribution_countries = get_countries_list(social_security_contribution_dataset)
    unemployment_countries = get_countries_list(unemployment_dataset)

    all_countries = intersection(intersection(intersection(intersection(perceived_happiness_countries,
                                                                        safety_countries), gdp_countries),
                                              social_security_contribution_countries), unemployment_countries)

    perceived_happiness_dataset = get_missing_values(perceived_happiness_dataset, all_countries)
    safety_dataset = get_missing_values(safety_dataset, all_countries)
    gdp_dataset = get_missing_values(gdp_dataset, all_countries)
    social_security_contribution_dataset = get_missing_values(social_security_contribution_dataset, all_countries)
    unemployment_dataset = get_missing_values(unemployment_dataset, all_countries)

    return perceived_happiness_dataset, safety_dataset, gdp_dataset, social_security_contribution_dataset, unemployment_dataset

get_all_datasets()