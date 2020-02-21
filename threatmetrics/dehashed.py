import sqlite3
from colorama import Fore
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class DehashedScraper(object):

    def __init__(self, **kwargs):
        # https://pastebin.com/raw/AD300fRL
        self._v = kwargs.get("verbose")
        self.db_file = './breaches.db'
        self.sql_file = './setup.sql'
        self.init_database(self.db_file, self.sql_file)
        self.url = "https://dehashed.com/breach"

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
        print(f"[-] Spawning webdriver for dehashed.com...")
        browser = webdriver.Firefox()
        browser.get(self.url)
        # Wait for CloudFlare to redirect.
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table-responsive"))
        )
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        # Close the browser, we don't need it anymore.
        print(f"[-] Closing webdriver for dehashed.com...")
        browser.close()
        table = soup.find("table", {"class": "table table-striped"})
        for tr in table.find_all_next("tr"):
            breach = tr.find_next("td", {"class": "align-middle"}).text.replace(" Database Breach", "")
            results.add(breach)
            if self._v:
                print(f"[-] Found breach: {breach}")
            try:
                cur.execute('INSERT INTO breaches (breach_db, db_source) VALUES (?,?);',
                            (breach, "dehashed.com"))
            except sqlite3.IntegrityError as tegrity:
                pass
        conn.commit()
        conn.close()
        print(f"{Fore.LIGHTGREEN_EX}[+] Scraped a total of {len(results)} breaches on dehashed.com!")


if __name__ == "__main__":

    scraper = DehashedScraper()
    scraper.scrape()
