from time import sleep
import pickle

from appdirs import AppDirs
from pathlib import Path
from getpass import getpass
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.common.exceptions import WebDriverException
from urllib.parse import urlparse, parse_qs

import logging

log = logging.getLogger(__name__)

CHROME_DRIVER_PATH = 'chromedriver'
XPATH_MAP_URL = '//div[starts-with(@data-mapurl,"https:")]'
XPATH_FILENAME = '//div[starts-with(@aria-label,"Filename")]'
XPATH_INFO_BUTTON = '//button[@title="Info"]'


class LocationExtract:
    def __init__(self, with_gui: bool = False):
        self.user: str = None
        self.pwd: str = None
        self.with_gui = with_gui
        self.driver: webdriver.Chrome = None
        app_dirs = AppDirs('gphotos-sync')
        self.cookie_file: Path = Path(
            app_dirs.user_cache_dir) / ".gphotos_cookies"
        if not self.cookie_file.parent.is_dir():
            self.cookie_file.parent.mkdir(parents=True)

    def get_credentials(self, user: str = None, pwd: str = None):
        self.user = user or input('Google Photos User Name: ')
        self.pwd = pwd or getpass()

    def authenticate(self, url: str):
        options = ChromeOptions()
        if not self.with_gui:
            options.headless = True
        self.driver = webdriver.Chrome(CHROME_DRIVER_PATH,
                                       chrome_options=options)
        self.driver.implicitly_wait(2)
        self.driver.get("https://www.google.com")

        if self.cookie_file.exists():
            cookies = pickle.load(open(str(self.cookie_file), 'rb'))
            for cookie in cookies:
                self.driver.add_cookie(cookie)

        self.driver.get(url)
        if str(self.driver.current_url).startswith(
                'https://accounts.google.com'):
            # we have been re-directed to Google Authentication
            if not self.with_gui:
                if self.user is None:
                    self.get_credentials()
                identifier = self.driver.find_element_by_id('identifierId')
                identifier.send_keys(self.user)
                id_next = self.driver.find_element_by_id('identifierNext')
                id_next.click()
                pwd = self.driver.find_element_by_name('password')
                pwd.send_keys(self.pwd)
                sleep(.1)
                pwd_next = self.driver.find_element_by_id('passwordNext')
                pwd_next.click()

            # wait for authentication (including two step) to be completed
            while self.driver.current_url != url:
                sleep(1)
        pickle.dump(self.driver.get_cookies(),
                    open(str(self.cookie_file), "wb"))

    def extract_location(self, url: str):
        location = None
        filename = None
        if self.driver is None:
            self.authenticate(url)
        else:
            self.driver.get(url)

        try:
            info_button = self.driver.find_element_by_xpath(XPATH_INFO_BUTTON)
            file = self.driver.find_elements_by_xpath(XPATH_FILENAME)
            if len(file) == 0:
                info_button.click()
                file = self.driver.find_element_by_xpath(XPATH_FILENAME)
                filename = file.text
            else:
                filename = file[0].text
            map_urls = self.driver.find_elements_by_xpath(XPATH_MAP_URL)

            if len(map_urls) == 0:
                log.warning('no location for %s', filename)
            else:
                location = map_urls[0].get_attribute("data-mapurl")
        except WebDriverException:
            log.warning('cannot fetch GPS info for %s', filename)

        if location:
            parsed = urlparse(location)
            params = parse_qs(parsed.query)
            location = params.get('center')
            if location:
                location = location[0]
            log.info('%s GPS location is %s', filename, location)
        return location

    @staticmethod
    def to_deg(value, loc):
        if value < 0:
            loc_value = loc[0]
        elif value > 0:
            loc_value = loc[1]
        else:
            loc_value = ""
        abs_value = abs(value)
        deg = int(abs_value)
        t1 = (abs_value-deg)*60
        minutes = int(t1)
        sec = round((t1 - minutes) * 60, 5)
        return deg, minutes, sec, loc_value

