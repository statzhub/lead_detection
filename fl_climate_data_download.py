# weather_station_code - city_name
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time, os
from collections import defaultdict

url = "https://climatecenter.fsu.edu/climate-data-access-tools/downloadable-data"
download_dir = "C:/CS490/statzhub/Datasets"

Firefox_options = Options()
Firefox_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "download.directory_upgrade": True, # create dir if default doesn't exist
    "safebrowsing.enabled": True   # avoid downloading file being blocked for safety reason
})


driver = webdriver.Firefox()

driver.get(url)
time.sleep(3)

# close cookie banner
try:
    driver.find_element(By.CSS_SELECTOR, "button.osano-cm-accept").click()
except NoSuchElementException:
    print("No cookie banner found.")

station_select = Select(driver.find_element(By.NAME, "down_station"))
stations = [o.get_attribute("value") for o in station_select.options if o.get_attribute("value")]

# store city_name-station_code in a dictionary
city_stationCode = defaultdict(list)
for option in station_select.options:
    stationCode = option.get_attribute("value")
    city = option.text.strip()
    city_stationCode[city].append(stationCode)

print(city_stationCode)


def select_year_safely(year_select_name, target_year):
    year_select = Select(driver.find_element(By.NAME, year_select_name))
    available_years = [opt.text for opt in year_select.options if opt.text.isdigit()]
    if target_year in available_years:
        year_select.select_by_visible_text(target_year)
    else:
        closest_year = max(int(year) for year in available_years if int(year) <= int(target_year))
        year_select.select_by_visible_text(str(closest_year))

def get_station_data(station_name):
    station_select = Select(
        driver.find_element(By.NAME, "down_station"))  # redirect all dropdown windows and avoid stale
    print(f"Downloading station: {station_name}")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "down_station"))
    )

    station_select.select_by_value(station_name)
    time.sleep(0.5)

    variable_select = Select(driver.find_element(By.NAME, "down_time"))
    variable_select.select_by_visible_text("January")
    variable_select = Select(driver.find_element(By.NAME, "down_day"))
    variable_select.select_by_visible_text("1")
    select_year_safely("down_year", "2019")

    variable_select = Select(driver.find_element(By.NAME, "down_time_end"))
    variable_select.select_by_visible_text("December")
    variable_select = Select(driver.find_element(By.NAME, "down_day_end"))
    variable_select.select_by_visible_text("31")
    select_year_safely("down_year_end", "2024")

    variable_select = Select(driver.find_element(By.NAME, "down_variable"))
    variable_select.select_by_visible_text("All")

    # download the csv file
    driver.find_element(By.NAME, "down_Submit").click()

    new_path = os.path.join(download_dir, f"{station_name}.csv")

    driver.get(url)
    time.sleep(5)


def __main__():
    for station in stations:
        get_station_data(station)

__main__()








