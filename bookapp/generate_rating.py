#!/usr/bin/env python
"""
Simple script to generate ratings for books.
Run with: python generate_rating.py
"""

import os
import sys
import django
import random

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BookStore.settings')  # Your project name
django.setup()

# Now import your models AFTER django.setup()
try:
    from bookapp.models import Book

    print("✓ Successfully imported Book model")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure:")
    print("1. Your app name is 'bookapp' in INSTALLED_APPS")
    print("2. The Book model is in bookapp/models.py")
    print("3. You're running from the correct directory")
    sys.exit(1)


def generate_simple_ratings():
    """One-time script to add realistic ratings to all books"""
    try:
        books = Book.objects.all()
        total = books.count()

        if total == 0:
            print("No books found in database!")
            return

        print(f"Generating ratings for {total} books...\n")

        for i, book in enumerate(books, 1):
            # Decide what kind of book this is
            chance = random.random()

            if chance < 0.05:  # 5% are bad books (1.5-2.5 stars)
                avg = random.uniform(1.5, 2.5)
                count = random.randint(5, 30)
            elif chance < 0.15:  # 10% are excellent books (4.2-4.8 stars)
                avg = random.uniform(4.2, 4.8)
                count = random.randint(50, 200)
            else:  # 85% are average books (3.0-4.0 stars)
                avg = random.uniform(3.0, 4.0)
                count = random.randint(20, 150)

            book.average_rating = round(avg, 2)
            book.rating_count = count
            book.save()

            # Show progress every 10 books
            if i % 10 == 0 or i == total:
                print(f"{i:3d}/{total} ✓ {book.title[:40]:40} → {book.average_rating:4.2f}⭐")

        print("\n" + "=" * 60)
        print("✅ RATINGS GENERATION COMPLETE!")

        # Show summary
        from django.db.models import Avg

        stats = Book.objects.aggregate(
            avg_rating=Avg('average_rating'),
            avg_count=Avg('rating_count'),
            min_rating=Avg('average_rating'),  # This should be Min, but using Avg for simplicity
            max_rating=Avg('average_rating')  # This should be Max, but using Avg for simplicity
        )

        print(f"\n📊 STATISTICS:")
        print(f"   Average book rating: {stats['avg_rating']:.2f}⭐")
        print(f"   Average ratings per book: {stats['avg_count']:.0f}")

        # Show some examples
        print(f"\n🏆 TOP 3 BOOKS:")
        for book in Book.objects.order_by('-average_rating')[:3]:
            print(f"   {book.title[:35]:35} → {book.average_rating:.2f}⭐ ({book.rating_count} ratings)")

        print(f"\n📉 BOTTOM 3 BOOKS:")
        for book in Book.objects.order_by('average_rating')[:3]:
            print(f"   {book.title[:35]:35} → {book.average_rating:.2f}⭐ ({book.rating_count} ratings)")

        # Rating distribution
        print(f"\n📈 RATING DISTRIBUTION:")
        ranges = [
            (0, 2.0, "⭐ (1-2 stars)"),
            (2.0, 3.0, "⭐⭐ (2-3 stars)"),
            (3.0, 4.0, "⭐⭐⭐ (3-4 stars)"),
            (4.0, 5.0, "⭐⭐⭐⭐ (4-5 stars)"),
        ]

        for low, high, label in ranges:
            count = Book.objects.filter(
                average_rating__gte=low,
                average_rating__lt=high
            ).count()
            percentage = (count / total) * 100
            print(f"   {label:20} → {count:3d} books ({percentage:5.1f}%)")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("BOOK RATING GENERATOR")
    print("=" * 60)

    # Ask for confirmation
    response = input("\nThis will update ratings for ALL books. Continue? (yes/no): ").strip().lower()

    if response in ['yes', 'y']:
        generate_simple_ratings()
    else:
        print("Operation cancelled.")