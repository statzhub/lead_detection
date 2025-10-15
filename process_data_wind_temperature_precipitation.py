# weather_station_code - city_name
import pandas as pd
import requests
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time, os
from collections import defaultdict

# change code to city
# get code_city pairs from: https://fawn.ifas.ufl.edu/data/fawnpub/daily_summaries/BY_STATION/
def code_to_city():
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
        texts = texts.rstrip('/')
        # print(texts)
        city, code = texts.split('_')
        code_city_pair[code] = city

    # store it in csv file for future use
    df = pd.DataFrame(list(code_city_pair.items()), columns=['Code', 'City'])
    df.to_csv("Datasets/code_city.csv", index=False)





def scrap_city_code_from_web():
    b = 0



# find cities in this county in this dataset
def find_county_city(county):
    c = 0


# Download weather data
# download data from {start_year}-1-1 to {end_year}-12-31
# from this website: https://fawn.ifas.ufl.edu/data/fawnpub/daily_summaries/BY_YEAR/
# 1997-2012 data are .csv.zip files, 2013-2020 data are .zip files, 2021-2025 are .csv files
# each year's data is like "{year}_daily.csv"
def download_data_from_year(start_year, end_year):
    i = 0


# gather data in all
# only keep "Temp @ 2m (C) Max", "Temp @ 2m (C) Min", "Temp @ 2m (C) Avg", "Rainfall Amount (in) Sum(precip)", "Wind Speed (mph) Avg", "Wind Speed (mph) Max", "Wind Direction (deg) Avg"
# change data from day to week

def process_weather_data(original_data):
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
    total_df.to_csv("Datasets/week_weather_data.csv", index=False)
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


def __main__():
    # use 2021_daily.csv as an example
    df = pd.read_csv("Datasets/2021_daily.csv")
    # process_weather_data(df)

    code_to_city()
    target_counties = ["Miami-Dade", "Hillsborough"]


__main__()

