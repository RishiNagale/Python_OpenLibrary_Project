import requests
import logging
import json
import pymysql
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
load_dotenv()

# Set up logging for warnings and info
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- BookFetcher ---
class BookFetcher:
    def __init__(self, query, fields, sort, limit):
        # Construct the API URL with query parameters
        self.query = query
        self.fields = fields
        self.sort = sort
        self.limit = limit
        self.base_url = f"https://openlibrary.org/search.json?q={query}&fields={fields}&sort={sort}&limit={limit}"

    def fetch_books(self):
        # Send GET request to the Open Library API
        logging.info("Fetching books from Open Library API...")
        response = requests.get(self.base_url)
        if response.status_code == 200:
            data = response.json()
            raw_data = data.get('docs', [])
            logging.info(f"Fetched {len(raw_data)} books from API.")
            return raw_data  # Return list of book records
        else:
            logging.error("Failed to retrieve books from Open Library API.")
            return []

# --- BookCleaner ---
class BookCleaner:
    def __init__(self, raw_books):
        self.raw_books = raw_books
        self.cleaned_books = []

    # Cleans raw book data and returns a list of cleaned book dictionaries, suitable for SQL insertion.
    def clean(self):
        logging.info("Cleaning raw book data...")
        for book in self.raw_books:
            try:
                title = book.get('title')
                authors = book.get('author_name')
                year = book.get('first_publish_year')

                # Skip records missing essential fields
                if not title or not authors or not year:
                    logging.warning("Skipping record due to missing title, authors, or year.")
                    continue

                cleaned_authors = []
                for a in authors:
                    # Remove leading 'etc.' or 'and'
                    a = re.sub(r'^(etc\.?|and)\s+', '', a, flags=re.IGNORECASE)
                    # Split on ' and ', ',', '&' (case-insensitive)
                    split_authors = re.split(r'\s+and\s+|,|&', a, flags=re.IGNORECASE)
                    for name in split_authors:
                        name = name.strip()
                        # Ignore empty names and 'etc.'
                        if name and not re.match(r'^etc\.?$', name, re.IGNORECASE):
                            cleaned_authors.append(name)

                # Skip if no valid authors found
                if not cleaned_authors:
                    logging.warning(f"Skipping record '{title}' due to no valid authors after cleaning.")
                    continue

                cleaned_book = {
                    "title": title.strip(),
                    "authors": cleaned_authors,
                    "first_publish_year": year
                }

                self.cleaned_books.append(cleaned_book)  # Add to cleaned list

            except (AttributeError, TypeError) as e:
                logging.warning(f"Skipping record due to error: {e}")
                continue

        logging.info(f"Cleaned {len(self.cleaned_books)} books.")
        return self.cleaned_books

# --- BookDatabase ---
class BookDatabase:
    def __init__(self, host, user, password, db_name):
        self.host = host
        self.user = user
        self.password = password
        self.db_name = db_name

        print("Connecting to MySQL server...")
        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password
        )
        print("Connected to MySQL server.")

        self.create_database_if_not_exists()
        self.reconnect_with_database()
        self.create_tables()

    def create_database_if_not_exists(self):
        # Create the database if it doesn't exist
        with self.connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")
        self.connection.commit()
        print(f"Database '{self.db_name}' ensured (created if not existed).")

    def reconnect_with_database(self):
        # Reconnect to the specific database
        self.connection.close()
        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.db_name
        )
        print(f"Connected to database '{self.db_name}'.")

    def create_tables(self):
        # Create all required tables if they don't exist
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_books (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    raw_json JSON
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cleaned_books (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    first_publish_year INT NOT NULL,
                    UNIQUE KEY unique_book (title, first_publish_year)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS authors (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS book_authors (
                    book_id INT,
                    author_id INT,
                    PRIMARY KEY (book_id, author_id),
                    FOREIGN KEY (book_id) REFERENCES cleaned_books(id) ON DELETE CASCADE,
                    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
                )
            """)
        self.connection.commit()
        print("Tables 'raw_books', 'cleaned_books', 'authors', and 'book_authors' are ready.")

    def insert_raw_books(self, raw_books):
        # Insert raw book records as JSON
        with self.connection.cursor() as cursor:
            for book in raw_books:
                cursor.execute(
                    "INSERT INTO raw_books (raw_json) VALUES (%s)",
                    (json.dumps(book),)
                )
        self.connection.commit()
        print(f"Inserted {len(raw_books)} raw books into 'raw_books' table.")

    def insert_cleaned_books(self, cleaned_books):
        # Insert cleaned books and normalized authors data
        with self.connection.cursor() as cursor:
            for book in cleaned_books:
                # Insert book (ignore duplicates)
                cursor.execute(
                    "INSERT IGNORE INTO cleaned_books (title, first_publish_year) VALUES (%s, %s)",
                    (book["title"], book["first_publish_year"])
                )
                # Get book id
                cursor.execute(
                    "SELECT id FROM cleaned_books WHERE title=%s AND first_publish_year=%s",
                    (book["title"], book["first_publish_year"])
                )
                result = cursor.fetchone()
                if result is None:
                    logging.error(f"Book not found in cleaned_books: {book['title']} ({book['first_publish_year']})")
                    continue
                book_id = result[0]

                # Insert authors and link to book
                for author_name in book["authors"]:
                    cursor.execute(
                        "INSERT IGNORE INTO authors (name) VALUES (%s)",
                        (author_name,)
                    )
                    cursor.execute(
                        "SELECT id FROM authors WHERE name=%s",
                        (author_name,)
                    )
                    author_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT IGNORE INTO book_authors (book_id, author_id) VALUES (%s, %s)",
                        (book_id, author_id)
                    )
        self.connection.commit()
        print(f"Inserted {len(cleaned_books)} cleaned books and authors into normalized tables.")

    def close(self):
        self.connection.close()
        print("Database connection closed.")

# --- BookVisualizer ---
class BookVisualizer:
    def __init__(self, host, user, password, db_name):
        # Connect to the same MySQL database
        self.connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )

    def plot_books_by_year(self):
        # Query to get the count of books by first publish year
        query = """
            SELECT first_publish_year, COUNT(*) as book_count
            FROM cleaned_books
            GROUP BY first_publish_year
            ORDER BY first_publish_year
        """
        df = pd.read_sql(query, self.connection)

        if df.empty:
            print("No data available to plot.")
            return

        # Only plot years with data (no fill for missing years)
        plt.figure(figsize=(16, 8))
        plt.bar(df['first_publish_year'].astype(str), df['book_count'], color='skyblue', width=0.8)
        plt.xlabel("First Publish Year")
        plt.ylabel("Number of Books")
        plt.title("Number of Books by First Publish Year")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def close(self):
        self.connection.close()

if __name__ == "__main__":
    # Create the DB handler and let it handle DB and table creation
    db = BookDatabase(
        host="localhost",
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        db_name="books_db"
    )

    # Fetch raw data from OpenLibrary API
    fetcher = BookFetcher(query="*", fields="title,author_name,first_publish_year", sort="rating asc", limit=100)
    raw_books = fetcher.fetch_books() # Fetch raw book data
    db.insert_raw_books(raw_books)

    # Clean the fetched data and insert into normalized tables
    cleaner = BookCleaner(raw_books)
    cleaned_books = cleaner.clean()
    db.insert_cleaned_books(cleaned_books)

    # Visualize the data
    visualizer = BookVisualizer(
        host="localhost",
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        db_name="books_db"
    )
    visualizer.plot_books_by_year()
    visualizer.close()

    db.close() # Close the database connection