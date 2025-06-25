import requests
import logging

logging.basicConfig(level=logging.WARNING)

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
        response = requests.get(self.base_url)
        if response.status_code == 200:
            data = response.json()
            print("Total results:", data.get('numFound', 0))
            return data.get('docs', [])  # Return list of book records
        else:
            print("Failed to retrieve books")
            return []

class BookCleaner:
    def __init__(self, raw_books):
        self.raw_books = raw_books
        self.cleaned_books = []

    def clean(self):
        for book in self.raw_books:
            try:
                # Ensure book is a dictionary and has required fields
                # Extract required fields with fallback values
                title = book.get('title', 'Unknown Title')
                authors = book.get('author_name', ['Unknown Author'])
                year = book.get('first_publish_year', 'Unknown Year')

                # Skip incomplete records
                if not title or not authors or not year:
                    continue

                # Format and clean the book data
                cleaned_book = {
                    "title": title.strip(),
                    "authors": ", ".join([a.strip() for a in authors]),
                    "first_publish_year": year
                }

                self.cleaned_books.append(cleaned_book)  # Add to cleaned list
                
            except (AttributeError,TypeError) as e:
                # Handle any exceptions during cleaning
                # Log the error and skip the record
                logging.warning(f"Skipping record: {e}")
                continue

        return self.cleaned_books

if __name__ == "__main__":
    # Initialize fetcher with API parameters
    fetcher = BookFetcher(
        query="*",
        fields="title,author_name,first_publish_year",
        sort="rating asc",
        limit=100
    )

    raw_data = fetcher.fetch_books()  # Fetch raw book data

    cleaner = BookCleaner(raw_data)
    cleaned_books = cleaner.clean()   # Clean the fetched data