from time import sleep
import pickle
from appdirs import AppDirs
from pathlib import Path
from getpass import getpass
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.common.exceptions import WebDriverException

import logging

log = logging.getLogger(__name__)

CHROME_DRIVER_PATH = 'chromedriver'
XPATH_MAP_URL = '//div[starts-with(@data-mapurl,"https:")]'
XPATH_FILENAME = '//div[starts-with(@aria-label,"Filename")]'


class LocationExtract:
    def __init__(self):
        self.user: str = None
        self.pwd: str = None
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
        if self.user is None:
            self.get_credentials()
        options = ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(CHROME_DRIVER_PATH,
                                       chrome_options=options)
        self.driver.implicitly_wait(1)
        self.driver.get("https://www.google.com")

        if self.cookie_file.exists():
            cookies = pickle.load(open(str(self.cookie_file), 'rb'))
            for cookie in cookies:
                self.driver.add_cookie(cookie)

        self.driver.get(url)
        if str(self.driver.current_url).startswith(
                'https://accounts.google.com'):
            # assume we have been re-directed to Google Authentication
            self.driver.find_element_by_id('identifierId').send_keys(self.user)
            self.driver.find_element_by_id('identifierNext').click()
            self.driver.find_element_by_name('password').send_keys(self.pwd)
            sleep(.1)
            self.driver.find_element_by_id('passwordNext').click()
            if '2-step' in self.driver.page_source:
                # wait for two step authentication to be completed
                while self.driver.current_url != url:
                    sleep(1)
        pickle.dump(self.driver.get_cookies(),
                    open(str(self.cookie_file), "wb"))

    def extract_location(self, url: str):
        location = None
        if self.driver is None:
            self.authenticate(url)
        else:
            self.driver.get(url)

        try:
            info_button = self.driver.find_element_by_xpath(
                '//button[@title="Info"]')
            map_urls = self.driver.find_elements_by_xpath(XPATH_MAP_URL)
            if len(map_urls) == 0:
                info_button.click()
                map_urls = self.driver.find_elements_by_xpath(XPATH_MAP_URL)
            file = self.driver.find_element_by_xpath(XPATH_FILENAME).text
        except (WebDriverException, IndexError):
            log.warning('cannot fetch filename')
            raise
        try:
            log.debug('reading location for %s', file)
            if len(map_urls) == 0:
                log.warning('no location for %s', file)
            else:
                location = map_urls[0].get_attribute("data-mapurl")
                log.warning(location)
        except WebDriverException:
            log.warning('no location info for %s',
                        file.text)

        return location
