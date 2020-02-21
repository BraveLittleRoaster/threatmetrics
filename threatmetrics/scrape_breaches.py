import requests
import sqlite3
import re
from bs4 import BeautifulSoup


class BreachScraper:

    def __init__(self):

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

    def init_neb_databases(self):

        print("[-] Loading Nebulous breaches into database...")
        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()

        with open('./nebulous_breaches.txt', 'r') as f:

            dumps = f.readlines()

        for dump in dumps:
            try:
                dump = dump.strip('\n').lower()
                data = dump.split(' ') # strip the date tags off of this for more accurate comparison.
                cur.execute('INSERT INTO breaches (breach_db, db_source) VALUES (?,?);', (data[0], 'nebulous'))
            except sqlite3.IntegrityError as tegrity:

                print("\t[!] Unique constraint error inserting data: {}".format(dump.strip('\n')))

        conn.commit()
        conn.close()
        print("[*] Finished loading Nebulous breaches. {} breaches loaded.".format(len(dumps)))

    def scrape_troyhunt(self):

        print("[-] Scraping dumps off of haveibeenpwned.com...")
        req = requests.get("https://haveibeenpwned.com/PwnedWebsites")
        html = req.content
        soup = BeautifulSoup(html, features="html.parser")
        all_a = soup.find_all("a")

        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()

        data = []

        for a in all_a:

            dump = a.get('id')  # he stores the db name in the id of this tag. This is more reliable than scraping <tr>
            if dump is None:
                pass  # ignore tags with no id
            elif dump == 'addAnotherNotification':
                pass # ignore this button.
            else:
                data.append(dump)

        print("[*] Scrape of haveibeenpwned.com complete. Found {} dumps.".format(len(data)))
        print("[-] Loading haveibeenpwned breaches into database...")
        for dump in data:
            try:
                cur.execute('INSERT INTO breaches (breach_db, db_source, is_public) VALUES (?,?,?);', (dump.lower(), 'haveibeenpwned', 1))
                print("\t[!] Found new database: {}".format(dump))
            except sqlite3.IntegrityError as tegrity:
                pass  # Ignore integrity errors.
                # print("\t[!] Unique constraint error inserting data: {}".format(dump.strip('\n')))

        conn.commit()
        conn.close()
        print("[*] Finished loading haveibeenpwned breaches into database.")

    def old_scrape_troyhunt(self):

        print("[-] Scraping dumps off of haveibeenpwned.com...")
        req = requests.get("https://haveibeenpwned.com/PwnedWebsites")
        html = req.content
        soup = BeautifulSoup(html, features="html.parser")
        all_headings = soup.find_all("h3", text=True)

        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()

        data = []

        for heading in all_headings:

            text = heading.get_text()
            text.strip('\n')
            data.append(text.strip('\n')) # some times it has two trailing newline chars.

        print("[*] Scrape of haveibeenpwned.com complete.")
        print("[-] Loading haveibeenpwned breaches into database...")
        for dump in data:
            try:
                cur.execute('INSERT INTO breaches (breach_db, db_source, is_public) VALUES (?,?,?);', (dump.lower(), 'haveibeenpwned', 1))
                print("\t[!] Found new database: {}".format(dump))
            except sqlite3.IntegrityError as tegrity:
                pass # Ignore integrity errors.
                #print("\t[!] Unique constraint error inserting data: {}".format(dump.strip('\n')))

        conn.commit()
        conn.close()
        print("[*] Finished loading haveibeenpwned breaches into database.")

    def scrape_databasestoday(self):

        print("[-] Scraping dumps off of databases.today...")
        req = requests.get("https://www.databases.today/search.php")
        html = req.content
        soup = BeautifulSoup(html, features="html.parser")
        all_trs = soup.find_all('tr')

        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()

        data = []

        for tr in all_trs:

            try:
                dump = tr.find_all('td')[0].get_text()
                detect_strange_format = dump.split(' (')
                if len(detect_strange_format) > 2:
                    cleaned = ' ('.join(detect_strange_format[:-1]) # strip the file size off, and joint the string back.
                else:
                    cleaned = re.sub('\((.*)\)', '', dump) # strip the file sizes off.

                data.append(cleaned.lower())

            except IndexError as e:
                pass # Ignore out of index errors for soups that contain null indexes.

        print("[*] Scrape of databases.today complete. Found {} dumps.".format(len(data)))
        print("[-] Loading databases.today breaches into database...")
        for dump_db in data:
            try:
                cur.execute('INSERT INTO breaches (breach_db, db_source, is_public) VALUES (?,?,?);', (dump_db, 'databasestoday', 1))
                print("\t[!] Found new database: {}".format(dump_db))
            except sqlite3.IntegrityError as tegrity:
                pass  # Ignore integrity errors.
                # print("\t[!] Unique constraint error inserting data: {}".format(dump.strip('\n')))

        conn.commit()
        conn.close()
        print("[*] Finished loading databases.today breaches into database.")

    def compare(self):

        conn = sqlite3.connect(self.db_file)
        cur = conn.cursor()
        update = conn.cursor() # create a secondary cursor to update the database with.
        cur.execute('SELECT breach_db FROM breaches WHERE db_source = "nebulous";')
        select_neb = cur.fetchall()

        neb_dbs = []

        for row in select_neb:
            neb_dbs.append(row[0])

        for dump in neb_dbs:
            query = '%{}%'.format(dump)
            cur.execute('SELECT * FROM breaches WHERE db_source != "nebulous" AND breach_db LIKE (?);', (query,))
            compare = cur.fetchall()
            if len(compare) > 0:
                print("\t[!] Found a match for public data: {}".format(dump))
                update.execute('UPDATE breaches SET is_public = 1 WHERE breach_db = ? AND db_source = "nebulous";', (dump,))

        conn.commit()
        conn.close()


def load():

    scrape = BreachScraper()
    scrape.init_neb_databases()
    scrape.scrape_troyhunt()
    scrape.scrape_databasestoday()
    scrape.compare()

if __name__ == "__main__":

    load()
