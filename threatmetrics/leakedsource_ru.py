import requests
import sqlite3
from colorama import Fore
from bs4 import BeautifulSoup
from fake_useragent import FakeUserAgent


class LeakedsourceScraper(object):

    def __init__(self, **kwargs):

        self._v = kwargs.get("verbose")
        self.db_file = './breaches.db'
        self.sql_file = './setup.sql'
        self.url = "https://leakedsource.ru/databases/"
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
        results = set()
        # Connect to the db.
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        # Setup User-Agent
        ua = FakeUserAgent()
        headers = {
            "User-Agent": ua.firefox
        }
        print(f"[-] Fetching databases for leakedsource.ru...")
        req = requests.get(self.url, headers=headers)

        soup = BeautifulSoup(req.content, 'html.parser')
        table = soup.find("table", {"class": "table table-inverse table-bordered"})

        for tr in table.find_all_next("tr"):
            breach = tr.find_next("td").text
            results.add(breach)
            try:
                cur.execute('INSERT INTO breaches (breach_db, db_source) VALUES (?,?);', (breach, "leakedsource.ru"))
            except sqlite3.IntegrityError as tegrity:
                pass

        print(f"{Fore.LIGHTGREEN_EX}[+] Scraped a total of {len(results)} breaches on leakedsource.ru!{Fore.RESET}")

        conn.commit()
        conn.close()


if __name__ == "__main__":

    scraper = LeakedsourceScraper()
    scraper.scrape()
