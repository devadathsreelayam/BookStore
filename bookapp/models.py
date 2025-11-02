from django.contrib.auth.models import User
from django.db import models
from django.db.models import JSONField
from datetime import datetime

from django.db.models import F, Sum


class Author(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    photo = models.URLField(blank=True, null=True)  # Changed from ImageField to URLField

    def __str__(self):
        return self.name

    @property
    def photo_url(self):
        """Return photo URL or a placeholder if none exists"""
        if self.photo:
            return self.photo
        return 'https://placehold.co/200x200/6c757d/white?text=No+Photo'


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
            return f"{self.parent.name} > {self.name}"
        return self.name


class Book(models.Model):
    BOOK_TYPES = [
        ('digital', 'Digital'),
        ('physical', 'Physical'),
        ('both', 'Both'),
    ]

    isbn = models.CharField(max_length=20, primary_key=True)

    title = models.CharField(max_length=300)
    authors = models.ManyToManyField(Author, related_name='books')
    publication_year = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    summary = models.TextField(blank=True)
    cover_image = models.URLField(blank=True)
    tags = JSONField(default=list, blank=True)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, related_name='books')
    book_type = models.CharField(max_length=10, choices=BOOK_TYPES, default='both')
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def main_genre(self):
        if self.genre and self.genre.parent:
            return self.genre.parent
        return self.genre

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-publication_year', 'title']


class Reader(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(null=True, blank=True)
    interests = models.ManyToManyField(Genre, limit_choices_to={'parent__isnull': True}, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='reader_avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def age(self):
        if self.date_of_birth:
            today = datetime.today()
            return today.year - self.date_of_birth.year - (
                    (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_items(self):
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0

    @property
    def total_price(self):
        total = self.items.aggregate(
            total=Sum(F('quantity') * F('book__price'))
        )['total'] or 0
        return total

    def clear(self):
        self.items.all().delete()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.book.title}"

    @property
    def total_price(self):
        return self.book.price * self.quantity

    class Meta:
        unique_together = ['cart', 'book']  # Prevent duplicate items


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist of {self.user.username}"

    @property
    def total_items(self):
        return self.items.count()

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.book.title} in {self.wishlist.user.username}'s wishlist"

    class Meta:
        unique_together = ['wishlist', 'book']  # Prevent duplicate items


class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order_id = models.CharField(max_length=20, unique=True, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')

    # Order details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    payment_method = models.CharField(max_length=50, default='Credit Card')

    # Status tracking
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True)
    shipping_carrier = models.CharField(max_length=50, blank=True)

    # Physical book
    has_physical_books = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.order_id} - {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = self.generate_order_id()

        self.has_physical_books = any(
            item.book.book_type in ['physical', 'both']
            for item in self.items.all()
        )

        super().save(*args, **kwargs)

    def generate_order_id(self):
        import random
        import string
        return 'ORD' + ''.join(random.choices(string.digits, k=7))

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def is_digital_only(self):
        return all(item.book.book_type == 'digital' for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)  # Price at time of order
    book_type = models.CharField(max_length=10, choices=Book.BOOK_TYPES)  # Format chosen

    def __str__(self):
        return f"{self.quantity} x {self.book.title}"

    @property
    def total_price(self):
        return self.price * self.quantity