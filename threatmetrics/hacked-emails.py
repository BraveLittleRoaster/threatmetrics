import requests
import sqlite3
from colorama import Fore
from bs4 import BeautifulSoup
from fake_useragent import FakeUserAgent
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class HackedemailsScraper(object):

    def __init__(self, **kwargs):

        self._v = kwargs.get("verbose")
        self.db_file = './breaches.db'
        self.sql_file = './setup.sql'
        self.url = "https://hacked-emails.com/confirmed/"
        self.init_database(self.db_file, self.sql_file)

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

        ua = FakeUserAgent()
        headers = {
            "User-Agent": ua.firefox
        }

        req = requests.get(self.url, headers=headers, timeout=30)

        soup = BeautifulSoup(req.content, 'html.parser')
        print(req.content)
        table = soup.find("table", {"id": "DataTables_Table_0"})
        if "DataTables_Table_0" in req.content.decode('utf-8'):
            print("Its there...")

        if table:
            odd_rows = table.findAllNext("tr", {"class": "odd"})
            even_rows = table.findAllNext("tr", {"class": "even"})

            for row in odd_rows:
                print(row.find_next("a"))

            for row in even_rows:
                print(row.find_next("a"))

        else:
            print(f"{Fore.RED}[!] Could not find table! Exiting.{Fore.RESET}")

    def selenium_scrape(self):
        results = set()
        # Connect to the DB
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        # Init firefox webdriver
        print(f"[-] Spawning webdriver for hacked-emails.com...")
        browser = webdriver.Firefox()
        browser.get(self.url)
        # Wait for CloudFlare to redirect.
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.ID, "DataTables_Table_0"))
        )
        # Scroll to the bottom of the page to load the table
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.ID, "DataTables_Table_0_wrapper"))
        )
        # Wait for data to populate
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "odd"))
        )
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "even"))
        )
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find("table", {"class": "table table-hover table-responsive dataTable no-footer"})
        # Close the browser, we don't need it anymore.
        print(f"[-] Closing webdriver for dehashed.com...")
        browser.close()

        if table:
            
            odd_rows = table.findAllNext("tr", {"class": "odd"})
            even_rows = table.findAllNext("tr", {"class": "even"})

            for row in odd_rows:
                breach = row.find_next("a").text
                results.add(breach)
                try:
                    cur.execute('INSERT INTO breaches (breach_db, db_source) VALUES (?,?);',
                                (breach, 'hacked-emails.com'))
                except sqlite3.IntegrityError as tegrity:
                    pass
                if self._v:
                    print(f"[-] Found breach: {breach}")

            for row in even_rows:
                breach = row.find_next("a").text
                results.add(breach)
                try:
                    cur.execute('INSERT INTO breaches (breach_db, db_source) VALUES (?,?);',
                                (breach, 'hacked-emails.com'))
                except sqlite3.IntegrityError as tegrity:
                    pass
                if self._v:
                    print(f"[-] Found breach: {breach}")

            conn.commit()
            conn.close()

            print(f"{Fore.LIGHTGREEN_EX}[+] Scraped a total of {len(results)} breaches on hacked-emails.com!{Fore.RESET}")

        else:
            conn.close()
            print(f"{Fore.RED}[!] Could not find table! Exiting.{Fore.RESET}")



if __name__ == "__main__":

    scraper = HackedemailsScraper()
    scraper.selenium_scrape()
