import sqlite3
from colorama import Fore
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class FirefoxScraper(object):

    def __init__(self, **kwargs):
        # https://pastebin.com/raw/AD300fRL
        self._v = kwargs.get("verbose")
        self.db_file = './breaches.db'
        self.sql_file = './setup.sql'
        self.init_database(self.db_file, self.sql_file)
        self.url = "https://monitor.firefox.com/breaches"

    def init_database(self, db_file, sql_file):

        print("[-] Initializing Database...")
        with open(sql_file, 'r') as f:
            sql = f.read()

        conn = sqlite3.connect(db_file)
        db = conn.cursor()
        db.execute(sql)
        conn.commit()
        conn.close()
        print("[*] Database initialized successfully.")

    def scrape(self):
        results = set()
        # Connect to the DB
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        # Init firefox webdriver
        print(f"[-] Spawning webdriver for monitor.firefox.com...")
        browser = webdriver.Firefox()
        browser.get(self.url)
        # Wait for "Show All" button to load.
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.ID, "show-hidden-breaches"))
        )
        # Click the button and wait for the table to load.
        button = browser.find_element_by_id("show-hidden-breaches")
        button.click()
        # Sleep and give us a little wiggle room on loading so we don't miss some of the HTML loading.
        time.sleep(3)
        html = browser.page_source
        # Close the browser, we don't need it anymore.
        print(f"[-] Closing webdriver for monitor.firefox.com...")
        browser.close()

        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("div", {"id": "all-breaches"})

        for card in table.find_all_next("a", {"class": "breach-card three-up ab drop-shadow send-ga-ping"}):

            breach = card.find("span", {"class": "breach-title"}).text
            results.add(breach)
            if self._v:
                print(f"[-] Found breach: {breach}")
            try:
                cur.execute('INSERT INTO breaches (breach_db, db_source) VALUES (?,?);',
                            (breach, "monitor.firefox.com")
                )
            except sqlite3.IntegrityError as tegrity:
                pass

        print(f"{Fore.LIGHTGREEN_EX}[+] Scraped a total of {len(results)} breaches on monitor.firefox.com!")
        conn.commit()
        conn.close()


if __name__ == "__main__":

    scraper = FirefoxScraper()
    scraper.scrape()