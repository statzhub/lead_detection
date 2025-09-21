from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import configparser


class Scroofer:
    """
    This is the scraper for the Hillsborough roofing permits data.
    """

    def __init__(self):
        # Read the config first.
        self.config = configparser.ConfigParser()
        self.config.read("scoof.ini")
        # Set up to use firefox, can be changed to chrome/edge
        self.browser = webdriver.Firefox()
        self.connect()

    def connect(self) -> bool:
        site_url = self.config["Site"]["name"]
        self.browser.get(site_url)
        return True

    def _fill_form_(self) -> None:
        # Look for the permit type dropdown
        type_selector = self.config["Search Form"]["type_selector"]
        inp = self.browser.find_element(By.NAME, type_selector)
        # create the dropdown interactor
        select = Select(inp)
        permit_type = self.config["Search Form"]["type"]
        select.select_by_visible_text(permit_type)
        #set start date
        start_date_id = self.config["Search Form"]["start_date_id"]
        start_date = self.config["Search Form"]["start_date"]
        self.browser.execute_script("""
            document.getElementById(arguments[0]).value = arguments[1];
        """, start_date_id, start_date)
        # set end date
        end_date_id = self.config["Search Form"]["end_date_id"]
        end_date = self.config["Search Form"]["end_date"]
        self.browser.execute_script("""
                    document.getElementById(arguments[0]).value = arguments[1];
                """, end_date_id, end_date)

    def clean_js(self, js) -> str:
        return js.replace("javascript:", "", 1)

    def search(self) -> None:
        """This method performs the initial search"""
        self._fill_form_()
        button_id = self.config["Search Form"]["search_button"]
        submit_button = self.browser.find_element(By.ID, button_id)

        # NOTE: The submit button is obscured using <imask>,
        # so we need to trigger the javascript directly.

        js_to_execute = submit_button.get_attribute("href")
        # the href needs to be cleaned
        if js_to_execute and js_to_execute.startswith("javascript:"):
            self.browser.execute_script(self.clean_js(js_to_execute))
        else:
            raise AttributeError("Did not find js in submit_button")

        self.check_pages()

    def check_pages(self) -> None:
        table_id = self.config["Table"]["table_id"]
        next_button_text = self.config["Table"]["next_button_text"]
        data = {}
        while True:
            try:
                #wait for table to appear from search
                table = WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.ID, table_id))
                )
                #used to get number of headers or columns
                header = table.find_elements(By.TAG_NAME, "th")
                #loop through each row to store their data
                for row in table.find_elements(By.TAG_NAME, "tr"):
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if not cols or len(cols) != len(header):
                        continue
                    row_data = [col.text for col in cols]
                    #index is currently hardcoded to the ID column for Hillsborough County
                    data[row_data[2]] = row_data
                #find the element of the next button
                next = self.browser.find_element(By.PARTIAL_LINK_TEXT, str(next_button_text))
                #clean href
                js_to_execute = next.get_attribute("href")
                if js_to_execute and js_to_execute.startswith("javascript:"):
                    self.browser.execute_script(self.clean_js(js_to_execute))
                    #wait for table to change to table of next page
                    WebDriverWait(self.browser, 10).until(EC.staleness_of(table))
                else:
                    raise AttributeError("Did not find js in submit_button")
            except Exception:
                #no table is found or next button is no longer enabled
                break