-- Create a mapping of breach db to db source.
CREATE TABLE IF NOT EXISTS breaches (
  breach_db text PRIMARY KEY,
  db_source text NOT NULL, -- Source of the dump (haveibeenpwned, databases.today, etc.)
  scrape_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, -- The date this data was scraped.
  is_public INT DEFAULT 0
);