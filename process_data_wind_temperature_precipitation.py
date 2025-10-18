# weather_station_code - city_name
import pandas as pd
import numpy as np
import requests
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time, os
from collections import defaultdict

# get code_city pairs from: https://fawn.ifas.ufl.edu/data/fawnpub/daily_summaries/BY_STATION/
# store in "Datasets/code_city.csv" file
def get_code_city_pairs():
    url = "https://fawn.ifas.ufl.edu/data/fawnpub/daily_summaries/BY_STATION/"
    driver = webdriver.Firefox()

    driver.get(url)
    time.sleep(3)
    a_tags = driver.find_elements(By.TAG_NAME, "a")
    a_texts = []
    for a in a_tags:
        href = a.get_attribute("href")  # 获取 href 属性
        if href:
            a_texts.append(href)

    cleaned_texts = [t for t in a_texts if t not in ('https://fawn.ifas.ufl.edu/data/fawnpub/daily_summaries/')]
    prefix = "https://fawn.ifas.ufl.edu/data/fawnpub/daily_summaries/BY_STATION/"
    cleaned_texts = [t.replace(prefix, "") for t in cleaned_texts]

    # only keep city-code pairs
    cleaned_texts = [t for t in cleaned_texts if t not in ('?C=N;O=D', '?C=M;O=A', '?C=S;O=A', '?C=D;O=A')]
    print(cleaned_texts)

    code_city_pair = {}
    for texts in cleaned_texts:
        texts = texts.rstrip('/').replace("%20"," ")
        # print(texts)
        city, code = texts.split('_')
        code_city_pair[code] = city

    # store it in csv file for future use
    df = pd.DataFrame(list(code_city_pair.items()), columns=['Code', 'City'])
    df.to_csv("Datasets/code_city.csv", index=False)

# find all cities in these county, store in "Datasets/county_city.csv" file
def get_cities_from_counties():
    fl_zipcodes = pd.read_csv("Datasets/fl_zipcodes.csv")
    # find all cities in the counties
    filtered_df = fl_zipcodes[["county_name", "city"]]
    filtered_df = filtered_df.drop_duplicates()
    filtered_df.to_csv("Datasets/county_city.csv", index=False)

df_cc = pd.read_csv("Datasets/code_city.csv")
code_city = dict(zip(df_cc["Code"], df_cc["City"].str.upper()))
# change code to city
def code_to_city(code):
    return code_city.get(code,np.nan)

city_code = dict(zip(df_cc["City"].str.upper(), df_cc["Code"]))
# change city to code
def city_to_code(city):
    return city_code.get(city,np.nan)

df_cd = pd.read_csv("Datasets/county_city.csv")
city_county = dict(zip(df_cd["city"].str.upper(), df_cd["county_name"].str.upper()))
# get all cities' weather data from these counties
def get_county_data(counties, year):
    # get all weather station cities from these counties
    filtered_df_cd = df_cd[df_cd["county_name"].isin(counties)]

    # find weather station data of this city
    cities_df = set(filtered_df_cd["city"])
    cities_station = set(df_cc["City"].str.upper())

    common_cities = cities_df & cities_station
    common_cities_code = [city_to_code(c) for c in common_cities]

    # return the data frame of those data
    # County, City, Code, Weatherdata(MaxTemp...)
    # TODO: need to change this to a loop for get recent 5 years data, rather than only in year 2021
    weather_data_df = pd.read_csv(f"Datasets/{year}_week_weather_data.csv")
    cleaned_weather_data = weather_data_df[weather_data_df["StationID"].isin(common_cities_code)]
    cleaned_weather_data = cleaned_weather_data.copy()
    cleaned_weather_data.loc[:, "City"] = cleaned_weather_data["StationID"].map(code_city)
    cleaned_weather_data.loc[:, "County"] = cleaned_weather_data["City"].map(city_county)
    return cleaned_weather_data

# TODO: Download weather data
# download data from {start_year}-1-1 to {end_year}-12-31
# from this website: https://fawn.ifas.ufl.edu/data/fawnpub/daily_summaries/BY_YEAR/
# 1997-2012 data are .csv.zip files, 2013-2020 data are .zip files, 2021-2025 are .csv files
# each year's data is like "{year}_daily.csv"
def download_data_from_year(start_year, end_year):
    i = 0


# gather data in all
# only keep "Temp @ 2m (C) Max", "Temp @ 2m (C) Min", "Temp @ 2m (C) Avg", "Rainfall Amount (in) Sum(precip)", "Wind Speed (mph) Avg", "Wind Speed (mph) Max", "Wind Direction (deg) Avg"
# change data from day to week
def process_part_weather_data(original_data, output_name):
    cols_keep = [
        "StationID",
        "Date Time",
        "Temp @ 2m (C) Max",
        "Temp @ 2m (C) Min",
        "Temp @ 2m (C) Avg",
        "Rainfall Amount (in) Sum",
        "Wind Speed (mph) Avg",
        "Wind Speed (mph) Max",
        "Wind Direction (deg) Avg"
    ]
    filtered_data = original_data[cols_keep]
    # print(filtered_data)

    # change column name from original to:
    filtered_data = filtered_data.rename(columns ={
        "Temp @ 2m (C) Min": "min_temp",
        "Temp @ 2m (C) Avg": "avg_temp",
        "Temp @ 2m (C) Max": "max_temp",
        "Wind Speed (mph) Avg": "avg_wind",
        "Wind Speed (mph) Max": "max_wind",
        "Rainfall Amount (in) Sum": "precip_total"
    })

    all_processed_data = []
    # get all stationId, change data from day to week based on id, store in a csv file
    stationIds = filtered_data["StationID"].unique()
    for stationId in stationIds:
        this_year_data = filtered_data[filtered_data["StationID"]==stationId]
        processed_data = change_weather_info_day_week(this_year_data)
        all_processed_data.append(processed_data)

    total_df = pd.concat(all_processed_data, ignore_index=True)
    total_df.to_csv(output_name, index=False)

    # also include county name and city name
    return total_df

# change weather data from day to week
def change_weather_info_day_week(df_input):
    df = df_input.copy()
    # remove all blank space in the beginning and end
    df.columns = df.columns.str.strip()

    # change date to week
    df["Date Time"] = pd.to_datetime(df["Date Time"])
    df["YEAR"] = df["Date Time"].dt.year
    df["day_year"] = df["Date Time"].dt.dayofyear
    df["WEEK"] = ((df["day_year"] - 1) // 7) + 1

    week_data = (df.groupby(["StationID", "YEAR", "WEEK"], as_index=False)
    .agg(
        week_max_temp = ("max_temp", "max"),
        week_min_temp = ("min_temp", "min"),
        week_avg_temp = ("avg_temp", "mean"),
        week_precip_total = ("precip_total", "sum"),
        week_avg_wind = ("avg_wind", "mean"),
        week_max_wind = ("max_wind", "max"),
    ))
    return week_data

# Scrape hail, hurricane, and tornado
def scrape_storm_data():
    url = "https://www.ncei.noaa.gov/stormevents/choosedates.jsp?statefips=12%2CFLORIDA#"

# check all data from this
def filter_hail_tornado_hurricane(county, df, year):
    df_filtered = df[df["EVENT_TYPE"].isin(["Tornado", "Hail", "Hurricane (typhoon)", "Hurricane"])]
    df_filtered = df_filtered[["CZ_NAME_STR","BEGIN_LOCATION","BEGIN_DATE","EVENT_TYPE"]]

    # from BEGIN_DATE, get year and week of this year, change it to 2 columns
    df_filtered["Date"] = pd.to_datetime(df_filtered["BEGIN_DATE"], format="%m/%d/%Y")

    df_filtered["YEAR"] = df_filtered["Date"].dt.year
    df_filtered["WEEK"] = ((df_filtered["Date"].dt.dayofyear - 1) // 7) + 1
    # TODO: just count by counties whether this week has tornado, hail or hurricane

    # add tornado, hail, and hurricane columns, and initialize them with 0
    df_filtered["County"] = county.upper()
    df_filtered = df_filtered[["County", "YEAR", "WEEK", "EVENT_TYPE"]]
    df_filtered["Tornado"] = 0
    df_filtered["Hail"] = 0
    df_filtered["Hurricane"] = 0

    event_counts = (
        df_filtered
        .groupby(["County", "YEAR", "WEEK", "EVENT_TYPE"])
        .size()  # count how many times it occurs
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["Tornado", "Hail", "Hurricane"]:
        if col not in event_counts.columns:
            event_counts[col] = 0
    event_counts = event_counts[["County", "YEAR", "WEEK", "Tornado", "Hail", "Hurricane"]]
    # TODO: need to change that output name for future use
    event_counts.to_csv(f"{county}_hth_{year}.csv", index=False)
    return event_counts

def merge_weather_data(df_weather, df_event):
    merged = pd.merge(
        df_weather,
        df_event,
        on=["County", "YEAR", "WEEK"],
        how="left"
    )
    merged[["Tornado", "Hail", "Hurricane"]] = merged[["Tornado", "Hail", "Hurricane"]].fillna(0).astype(int)

    return merged


def __main__():
    # use 2021_daily.csv as an example
    # df = pd.read_csv("Datasets/2024_daily.csv")
    # # # TODO: hardcode the result file name to 2021_week_weather_data.csv, need to change when there's a loop
    # process_part_weather_data(df,"Datasets/2024_week_weather_data.csv")
    # print(code_to_city(260))
    # get_cities_from_counties()

    target_counties = ["Hillsborough"]

    merged_df = pd.DataFrame()
    for y in ["2021", "2022", "2023", "2024"]:
        yd = get_county_data(target_counties,y)
        yd.to_csv(f"Datasets/Hillsborough_{y}.csv", index=False)
        merged_df = pd.concat([merged_df, yd], ignore_index=True)

    merged_df.to_csv(f"Datasets/Hillsborough_2021_to_2024.csv", index=False)

    df = pd.read_csv("Datasets/Hillsborough_storm_data_search_results.csv")
    hth = filter_hail_tornado_hurricane("Hillsborough", df,"2021_2024")

    (merge_weather_data(merged_df,hth)
     .to_csv("Datasets/Total_Hillsborough_2021_2024.csv",index=False))

    #
    # df = pd.read_csv("Datasets/Miami_dade_storm_data_search_results.csv")
    # # print(filter_hail_tornado_hurricane("Miami-Dade", df))
    # # print(merge_weather_data(get_county_data(target_counties), filter_hail_tornado_hurricane("Miami-Dade", df)))
    #
    # merge_weather_data(get_county_data(target_counties), filter_hail_tornado_hurricane("Datasets/Miami-Dade", df)).to_csv("Datasets/Total_Miami_2021.csv", index=False)

# TODO: need to loop through the year and get the recent 5 year weather data from the same county in one csv file

__main__()

