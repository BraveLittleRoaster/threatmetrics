import requests
import sqlite3
from colorama import Fore
from bs4 import BeautifulSoup
from fake_useragent import FakeUserAgent


class LeakLookupScraper(object):

    def __init__(self, **kwargs):

        self._v = kwargs.get("verbose")
        self.db_file = './breaches.db'
        self.sql_file = './setup.sql'
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

    def scrape_leaklookup(self):

        leaklookup_dbs = set()
        # Broilerplate Metrics to Return
        metrics = {
            "reported_dbs": None,
            "reported_records": None,
            "scraped_dbs": []
        }

        # Connect to the database.
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()

        ua = FakeUserAgent()
        headers = {
            "User-Agent": ua.firefox
        }
        leak_db_url = "http://leak-lookup.com/databases"
        print(f"[-] Connecting to leak-lookup.com...")
        req = requests.get(leak_db_url, headers=headers)

        soup = BeautifulSoup(req.content, 'html.parser')

        breach_metrics = soup.find_all("div", {"class": "col-sm-6"})
        for metric in breach_metrics:
            value = metric.find("h3").text
            value = value.rstrip(' ')  # remove trailing whitespace
            value = value.replace(',', '')  # remove commas
            if int(value) >= 1000000:
                metrics['reported_records'] = value
            else:
                metrics['reported_dbs'] = value

        db_table = soup.find("table", {"id": "allListings"})
        if db_table:
            print(f"[+] Found database table.")
            for db in db_table.find_all_next("tr"):
                database = db.find_all_next('td')[1].text
                if self._v:
                    print(f"{Fore.LIGHTCYAN_EX}[+] Found database: {database}!")
                leaklookup_dbs.add(database)

        else:
            print(f"{Fore.RED}[!] Error: Could not find databases list on leak-lookup.com!{Fore.RESET}")

        print(f"{Fore.LIGHTGREEN_EX}[+] Scraped a total of {len(leaklookup_dbs)}/{metrics['reported_dbs']} reported leaked databases on leak-lookup.com, totaling {metrics['reported_records']} records.{Fore.RESET}")
        print(f"[-] Inserting {len(leaklookup_dbs)} metrics into breached database.")
        for metric in leaklookup_dbs:

            metrics['scraped_dbs'].append(metric)
            try:
                cur.execute('INSERT INTO breaches (breach_db, db_source) VALUES (?,?);', (metric, 'leak-lookup.com'))
            except sqlite3.IntegrityError as tegrity:
                pass  # Ignore the integrity warnings
                if self._v:
                    print(f"{Fore.YELLOW}[!] Unique constraint error inserting {metric} into db. It must already exist.")

        conn.commit()
        conn.close()
        return metrics


if __name__ == "__main__":

    met = LeakLookupScraper()
    metrics = met.scrape_leaklookup()
    print(f"[+] Got metrics: {metrics}")
