import random

import pandas as pd
import json
from collections import defaultdict
from datetime import datetime


def read_excel_data(excel_file_path, sheet_name=0):
    """Read book data from Excel file"""
    try:
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        print(f"Successfully read Excel with {len(df)} rows and columns: {list(df.columns)}")
        return df.to_dict('records')
    except Exception as e:
        print(f"Excel reading failed: {e}")
        return []


def clean_book_data(books_data):
    """Clean and convert data types"""
    cleaned_data = []

    for book in books_data:
        cleaned_book = {}

        # Text fields
        cleaned_book['Book title'] = str(book.get('Book title', '')).strip()
        cleaned_book['Author'] = str(book.get('Author', '')).strip()
        cleaned_book['Genre'] = str(book.get('Genre', '')).strip()
        cleaned_book['Sub genre'] = str(book.get('Sub genre', '')).strip()
        cleaned_book['Tags'] = str(book.get('Tags', '')).strip()
        cleaned_book['ISBN'] = str(book.get('ISBN', '')).strip()
        cleaned_book['Summary'] = str(book.get('Summary', '')).strip()
        cleaned_book['Image URL'] = str(book.get('Image URL', '')).strip()

        # Numeric fields with conversion
        try:
            cleaned_book['Year'] = int(book.get('Year', 0))
        except (ValueError, TypeError):
            cleaned_book['Year'] = 0

        try:
            price_str = str(book.get('Price', 0)).replace('₹', '').replace('$', '').replace(',', '').strip()
            cleaned_book['Price'] = float(price_str)
        except (ValueError, TypeError):
            cleaned_book['Price'] = 0.0

        cleaned_data.append(cleaned_book)

    return cleaned_data


def normalize_book_data_from_excel(excel_file_path, sheet_name=0):
    """Normalize book data from Excel file with proper genre hierarchy"""

    # Read data from Excel
    raw_data = read_excel_data(excel_file_path, sheet_name)

    if not raw_data:
        print("No data found in Excel file!")
        return None

    # Clean the data
    cleaned_data = clean_book_data(raw_data)

    print(f"Processing {len(cleaned_data)} books...")

    # Initialize storage for normalized data
    normalized = {
        'authors': defaultdict(dict),
        'genres': defaultdict(dict),  # This will store both main genres and subgenres
        'books': [],
        'book_authors': [],
    }

    # Track unique values
    author_name_to_id = {}
    genre_hierarchy = defaultdict(set)  # {main_genre: set(subgenres)}
    genre_name_to_id = {}

    # Counters for IDs
    author_id = 1
    genre_id = 1

    # First pass: Collect all unique genres and their subgenres
    print("Analyzing genre hierarchy...")
    for book_data in cleaned_data:
        main_genre = book_data.get('Genre', 'Unknown Genre').strip()
        sub_genre = book_data.get('Sub genre', 'General').strip()

        if main_genre and sub_genre:
            genre_hierarchy[main_genre].add(sub_genre)

    # Create genre mapping with proper hierarchy
    print("\nGenre Hierarchy Found:")
    for main_genre, subgenres in genre_hierarchy.items():
        print(f"  {main_genre}:")
        for subgenre in subgenres:
            print(f"    - {subgenre}")

    # Create main genres first (parent = None)
    for main_genre in genre_hierarchy.keys():
        if main_genre not in genre_name_to_id:
            normalized['genres'][genre_id] = {
                'id': genre_id,
                'name': main_genre,
                'parent_id': None,
                'is_main_genre': True
            }
            genre_name_to_id[main_genre] = genre_id
            genre_id += 1

    # Create subgenres with correct parent relationships
    for main_genre, subgenres in genre_hierarchy.items():
        parent_id = genre_name_to_id[main_genre]
        for subgenre in subgenres:
            subgenre_key = f"{main_genre}_{subgenre}"
            if subgenre_key not in genre_name_to_id:
                normalized['genres'][genre_id] = {
                    'id': genre_id,
                    'name': subgenre,
                    'parent_id': parent_id,
                    'is_main_genre': False
                }
                genre_name_to_id[subgenre_key] = genre_id
                genre_id += 1

    # Second pass: Process books and authors
    used_isbns = set()

    for book_data in cleaned_data:
        # Skip if essential data is missing
        if not book_data.get('Book title') or not book_data.get('Author'):
            print(f"Skipping book with missing title or author: {book_data.get('Book title', 'Unknown')}")
            continue

        # Check for valid ISBN
        isbn = book_data.get('ISBN', '').strip()
        if not isbn:
            print(f"Skipping book with missing ISBN: {book_data['Book title']}")
            continue

        # Check for duplicate ISBN
        if isbn in used_isbns:
            print(f"Skipping duplicate ISBN: {isbn} - {book_data['Book title']}")
            continue

        used_isbns.add(isbn)

        # Process Author
        author_name = book_data['Author']
        if author_name not in author_name_to_id:
            normalized['authors'][author_id] = {
                'id': author_id,
                'name': author_name,
                'bio': f"Author of {book_data['Book title']}"
            }
            author_name_to_id[author_name] = author_id
            author_id += 1

        # Process Genre and Subgenre - Find correct genre ID
        main_genre = book_data.get('Genre', 'Unknown Genre').strip()
        sub_genre = book_data.get('Sub genre', 'General').strip()

        # Find the correct genre ID for this book's subgenre
        subgenre_key = f"{main_genre}_{sub_genre}"
        genre_id_for_book = genre_name_to_id.get(subgenre_key)

        if not genre_id_for_book:
            # Fallback: use main genre if subgenre not found
            print(f"Warning: Subgenre '{sub_genre}' not found for genre '{main_genre}'. Using main genre.")
            genre_id_for_book = genre_name_to_id.get(main_genre, 1)  # Default to first genre

        # Process Tags (convert to list)
        tags_text = book_data.get('Tags', '')
        if tags_text:
            tags_list = [tag.strip() for tag in tags_text.split(',')]
        else:
            tags_list = []

        # Add Book
        normalized['books'].append({
            'isbn': isbn,
            'title': book_data['Book title'],
            'publication_year': book_data['Year'],
            'price': book_data['Price'],
            'summary': book_data.get('Summary', ''),
            'cover_image': book_data.get('Image URL', ''),
            'tags': tags_list,
            'genre_id': genre_id_for_book  # Changed from subgenre_id to genre_id
        })

        # Add book-author relationship
        normalized['book_authors'].append({
            'book_isbn': isbn,
            'author_id': author_name_to_id[author_name]
        })

    return normalized


def generate_django_models():
    """Generate Django model code with simplified genre structure"""

    models_code = """
from django.db import models
from django.db.models import JSONField

class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='author_photos/', blank=True, null=True)

    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subgenres')
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    @property
    def is_main_genre(self):
        return self.parent is None

    @property
    def display_name(self):
        if self.parent:
            return f"{self.parent.name} › {self.name}"
        return self.name

class Book(models.Model):
    BOOK_TYPES = [
        ('digital', 'Digital'),
        ('physical', 'Physical'),
        ('both', 'Both'),
    ]

    # Using ISBN as primary key
    isbn = models.CharField(max_length=20, primary_key=True)

    title = models.CharField(max_length=300)
    authors = models.ManyToManyField(Author, related_name='books')
    publication_year = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    summary = models.TextField(blank=True)
    cover_image = models.URLField(blank=True)
    tags = JSONField(default=list, blank=True)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, related_name='books')  # Changed from subgenre to genre
    book_type = models.CharField(max_length=10, choices=BOOK_TYPES, default='both')
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def main_genre(self):
        # If this book has a subgenre, get its parent
        if self.genre and self.genre.parent:
            return self.genre.parent
        return self.genre

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-publication_year', 'title']
"""

    return models_code


def generate_fixtures(normalized_data):
    """Generate Django fixtures from normalized data"""

    fixtures = {
        'authors': [],
        'genres': [],
        'books': []
    }

    current_time = datetime.now().isoformat()

    # Authors fixtures
    for author_id, author_data in normalized_data['authors'].items():
        fixtures['authors'].append({
            'model': 'bookapp.author',
            'pk': author_data['id'],
            'fields': {
                'name': author_data['name'],
                'bio': author_data.get('bio', ''),
            }
        })

    # Genres fixtures - both main genres and subgenres
    for genre_id, genre_data in normalized_data['genres'].items():
        fixtures['genres'].append({
            'model': 'bookapp.genre',
            'pk': genre_data['id'],
            'fields': {
                'name': genre_data['name'],
                'parent': genre_data['parent_id'],
            }
        })

    # Books fixtures
    for book_data in normalized_data['books']:
        # Get author IDs for this book
        author_ids = []
        for ba in normalized_data['book_authors']:
            if ba['book_isbn'] == book_data['isbn']:
                author_ids.append(ba['author_id'])

        fixtures['books'].append({
            'model': 'bookapp.book',
            'pk': book_data['isbn'],
            'fields': {
                'title': book_data['title'],
                'authors': author_ids,
                'publication_year': book_data['publication_year'],
                'price': str(book_data['price']),
                'summary': book_data['summary'],
                'cover_image': book_data['cover_image'],
                'tags': book_data['tags'],
                'genre': book_data['genre_id'],  # Changed from subgenre to genre
                'book_type': 'both',
                'stock': random.choice([0, 0, 5, 10, 10, 15, 20, 25, 30, 40, 50]),
                'created_at': current_time,
                'updated_at': current_time,
            }
        })

    return fixtures


def main():
    # Replace with your actual Excel file path
    excel_file_path = 'book_dataset.xlsx'  # Change this to your Excel file path
    sheet_name = 0  # or 'Sheet1'

    # Normalize the data from Excel
    normalized_data = normalize_book_data_from_excel(excel_file_path, sheet_name)

    if not normalized_data:
        print("Failed to normalize data. Exiting.")
        return

    # Generate Django models code
    models_code = generate_django_models()

    # Generate fixtures
    fixtures = generate_fixtures(normalized_data)

    # Save models to file
    with open('models.py', 'w') as f:
        f.write(models_code)

    # Save fixtures to JSON files
    with open('authors_fixture.json', 'w') as f:
        json.dump(fixtures['authors'], f, indent=2)

    with open('genres_fixture.json', 'w') as f:
        json.dump(fixtures['genres'], f, indent=2)

    with open('books_fixture.json', 'w') as f:
        json.dump(fixtures['books'], f, indent=2)

    # Print summary
    print("\n" + "=" * 50)
    print("NORMALIZATION COMPLETE!")
    print("=" * 50)
    print(f"Authors: {len(normalized_data['authors'])}")
    print(f"Genres (Total): {len(normalized_data['genres'])}")

    # Count main genres vs subgenres
    main_genres = sum(1 for g in normalized_data['genres'].values() if g['parent_id'] is None)
    subgenres = len(normalized_data['genres']) - main_genres
    print(f"  - Main Genres: {main_genres}")
    print(f"  - Subgenres: {subgenres}")

    print(f"Books: {len(normalized_data['books'])}")

    print("\nGenerated files:")
    print("- models.py (Django models)")
    print("- authors_fixture.json")
    print("- genres_fixture.json")
    print("- books_fixture.json")

    # Show sample data with correct genre hierarchy
    print("\nSample Books with Genre Hierarchy:")
    for book in normalized_data['books'][:3]:
        author_id = next(ba['author_id'] for ba in normalized_data['book_authors'] if ba['book_isbn'] == book['isbn'])
        author_name = normalized_data['authors'][author_id]['name']

        genre_data = normalized_data['genres'][book['genre_id']]
        if genre_data['parent_id']:
            parent_genre = normalized_data['genres'][genre_data['parent_id']]['name']
            genre_display = f"{parent_genre} › {genre_data['name']}"
        else:
            genre_display = genre_data['name']

        print(f"  '{book['title']}' by {author_name}")
        print(f"    Genre: {genre_display}")


if __name__ == "__main__":
    main()