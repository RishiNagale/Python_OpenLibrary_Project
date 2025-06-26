# Open Library Book Analysis

## Overview

This project is about fetching and analyzing the top 100 books from [Open Library](https://openlibrary.org). The main tasks include fetching, cleaning, storing in SQL, and visualizing the data.

## Plan

- Use Open Library API to get title, author(s), and first publish year.
- Use 4 Python classes:
  - `BookFetcher` – to fetch book data using API.
  - `BookCleaner` – to clean and format the data.
  - `BookDatabase` – to store cleaned data into a SQL database.
  - `BookVisualizer` – to create a count plot of books by first publish year.

## Progress Log

| Date       | Work Done                                                                                             | Next Steps                                                        |
|------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| 2025-06-23 | - Explored Open Library API and checked available endpoints. <br> - Planned class structure. <br> - Created GitHub repo and added initial README. | - Start working on `BookFetcher` class. <br> - Finalize API endpoint and test response. |
| 2025-06-25 | - Implemented `BookFetcher` class to fetch top 100 books sorted by rating.<br> - Implemented `BookCleaner` class to clean and format book data.<br> - Tested both classes successfully with print preview. | - Implement `BookDatabase` to store cleaned data.<br> - Begin planning `BookVisualizer` class. |
| 2025-06-26 | - Implemented `BookDatabase` class for normalized SQL storage.<br> - Added logging and improved data cleaning.<br> - Planned `BookVisualizer` implementation. | - Implement `BookVisualizer` class.<br> - Finalize and test data visualization. |
