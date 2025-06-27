-- Use the books_db database
USE books_db;

-- View all raw book records (JSON)
SELECT * FROM raw_books rb;

-- View all cleaned book records
SELECT * FROM cleaned_books cb;

-- View all authors
SELECT * FROM authors a;

-- View all book-author relationships
SELECT * FROM book_authors ba;

-- View all authors ordered by their ID
SELECT id, name FROM authors ORDER BY id ASC;

-- Show each book with its authors
SELECT cb.title AS book_title, 
       a.name AS author_name
FROM cleaned_books cb
JOIN book_authors ba ON cb.id = ba.book_id
JOIN authors a ON ba.author_id = a.id
ORDER BY cb.title ASC, a.name ASC;

-- Find the years with the most books published
SELECT first_publish_year, COUNT(*) AS books_published
FROM cleaned_books
GROUP BY first_publish_year
ORDER BY books_published DESC, first_publish_year ASC;

-- Count how many books each author has written
SELECT a.name AS author_name, COUNT(ba.book_id) AS books_written
FROM authors a
JOIN book_authors ba ON a.id = ba.author_id
GROUP BY a.id, a.name
ORDER BY books_written DESC, a.name ASC;

-- List all books with more than one author
SELECT cb.title, COUNT(ba.author_id) AS author_count
FROM cleaned_books cb
JOIN book_authors ba ON cb.id = ba.book_id
GROUP BY cb.id, cb.title
HAVING author_count > 1
ORDER BY author_count DESC, cb.title ASC;
