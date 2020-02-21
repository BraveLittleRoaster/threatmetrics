import requests
import sqlite3
from colorama import Fore
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool
from fake_useragent import FakeUserAgent
import tqdm


class BreachawareScraper:

    def __init__(self, **kwargs):

        self._v = kwargs.get("verbose")
        self._threads = 100
        self.db_file = './breaches.db'
        self.sql_file = './setup.sql'
        self.init_database(self.db_file, self.sql_file)
        self.url = "https://breachaware.com/breaches?page={}"
        self.results = set()

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

    def get_max_pages(self):

        # Setup User-Agent
        ua = FakeUserAgent()
        headers = {
            "User-Agent": ua.firefox
        }

        print(f"[-] Fetching max page number for breachaware.com...")
        req = requests.get(self.url.format(self.url.format('1')), headers=headers, timeout=30)
        soup = BeautifulSoup(req.content, 'html.parser')

        pagination = soup.find("ul", {"class": "pagination"})
        all_pages = pagination.find_all_next("a", {"class": "page-link"})
        max_pages = all_pages[-2].text  # Second to last element will be the last page. Last element is the next button.

        return int(max_pages)

    def scrape(self, page_no):

        # Setup User-Agent
        ua = FakeUserAgent()
        headers = {
            "User-Agent": ua.firefox
        }
        if self._v:
            print(f"[-] Fetching page {page_no} breachaware.com...")
        req = requests.get(self.url.format(page_no), headers=headers, timeout=30)

        soup = BeautifulSoup(req.content, "html.parser")
        table = soup.find("table", {"class": "table table-striped"})
        for tr in table.find_all_next("tr", {"class": "clickable-row"}):

            breach = tr.find_all_next("td", {"class": "align-middle"})[1]
            domain = breach.find("code")
            if domain:
                if "Domain:" in domain.text:
                    domain = domain.text.replace("Domain: ", "")
                    domain = domain.replace("\t", "")
                    domain = domain.replace("\n", "")
                    if self._v:
                        print(f"[-] Found a breach: {domain}")
                    self.results.add(domain)
                else:
                    breach = breach.text.replace(" ", "")
                    breach = breach.replace("\t", "")
                    breach = breach.replace("\n", "")
                    if self._v:
                        print(f"[-] Found a breach: {breach}")
                    self.results.add(breach)
            else:
                """Need to catch this all jank like because there are a lot of <code> tags that contain 
                repeat entries values, like 'Combo List'"""
                breach = breach.text.replace(" ", "")
                breach = breach.replace("\t", "")
                breach = breach.replace("\n", "")
                if self._v:
                    print(f"[-] Found a breach: {breach}")
                self.results.add(breach)

        return True

    def run_scraper(self):
        # Connect to the db.
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()

        p = Pool(processes=self._threads)

        max_pages = self.get_max_pages()
        print(f"[-] Spawning threads for scraping a total of {max_pages} pages...")
        for _ in tqdm.tqdm(p.imap_unordered(self.scrape, range(1, max_pages + 1)), total=max_pages):
            pass
        print(f"{Fore.LIGHTGREEN_EX}[+] Scraped a total of {len(self.results)} breaches on breachaware.com!{Fore.RESET}")
        for result in self.results:

            try:
                cur.execute('INSERT INTO breaches (breach_db, db_source) VALUES (?,?);', (result, "breachaware.com"))
            except sqlite3.IntegrityError:
                pass
        conn.commit()
        conn.close()


if __name__ == "__main__":

    scrape = BreachawareScraper()
    max = scrape.run_scraper()
