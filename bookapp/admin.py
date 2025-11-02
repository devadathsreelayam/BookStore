from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .models import Author, Genre, Reader, Book, Cart, CartItem, WishlistItem, Wishlist, Order, OrderItem

# Hide the default Group model from admin
admin.site.unregister(Group)


class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name', 'book_count', 'photo_preview']
    list_filter = ['name']
    search_fields = ['name', 'bio']
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'bio']
        }),
        ('Media', {
            'fields': ['photo'],
            'classes': ['collapse']
        }),
    ]
    readonly_fields = ['photo_preview']

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Number of Books'

    def photo_preview(self, obj):
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo}" style="max-height: 100px; max-width: 100px;" />')
        return "No photo"
    photo_preview.short_description = 'Photo Preview'


class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_main_genre', 'book_count']
    list_filter = ['parent']
    search_fields = ['name']
    fieldsets = [
        ('Genre Information', {
            'fields': ['name', 'parent', 'description']
        }),
    ]

    def is_main_genre(self, obj):
        return obj.is_main_genre

    is_main_genre.short_description = 'Is Main Genre'
    is_main_genre.boolean = True

    def book_count(self, obj):
        return obj.books.count()

    book_count.short_description = 'Books in Genre'


class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'display_authors', 'publication_year', 'price', 'book_type', 'stock', 'is_available']
    list_filter = ['book_type', 'publication_year', 'genre', 'genre__parent']
    search_fields = ['title', 'isbn', 'authors__name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['price', 'stock']
    filter_horizontal = ['authors']
    fieldsets = [
        ('Basic Information', {
            'fields': ['isbn', 'title', 'authors', 'publication_year', 'genre']
        }),
        ('Pricing & Inventory', {
            'fields': ['price', 'book_type', 'stock']
        }),
        ('Content Details', {
            'fields': ['summary', 'cover_image', 'tags'],
            'classes': ['collapse']
        }),
        ('System Information', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def display_authors(self, obj):
        return ", ".join([author.name for author in obj.authors.all()])

    display_authors.short_description = 'Authors'

    def is_available(self, obj):
        return obj.stock > 0

    is_available.short_description = 'Available'
    is_available.boolean = True

    actions = ['restock_books', 'mark_as_digital', 'mark_as_physical']

    def restock_books(self, request, queryset):
        updated = queryset.update(stock=10)
        self.message_user(request, f'{updated} books restocked to 10 units.')

    restock_books.short_description = "Restock to 10 units"

    def mark_as_digital(self, request, queryset):
        updated = queryset.update(book_type='digital')
        self.message_user(request, f'{updated} books marked as digital only.')

    mark_as_digital.short_description = "Mark as digital only"

    def mark_as_physical(self, request, queryset):
        updated = queryset.update(book_type='physical')
        self.message_user(request, f'{updated} books marked as physical only.')

    mark_as_physical.short_description = "Mark as physical only"


class ReaderAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'full_name', 'date_of_birth', 'age', 'interests_count', 'date_joined']
    list_filter = ['date_of_birth', 'user__date_joined']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email', 'bio']
    readonly_fields = ['age', 'created_at', 'updated_at']
    filter_horizontal = ['interests']
    fieldsets = [
        ('User Account', {
            'fields': ['user']
        }),
        ('Personal Information', {
            'fields': ['date_of_birth', 'bio', 'avatar']
        }),
        ('Reading Preferences', {
            'fields': ['interests']
        }),
        ('System Information', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def username(self, obj):
        return obj.user.username

    username.short_description = 'Username'

    def email(self, obj):
        return obj.user.email

    email.short_description = 'Email'

    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or "Not provided"

    full_name.short_description = 'Full Name'

    def date_joined(self, obj):
        return obj.user.date_joined

    date_joined.short_description = 'Date Joined'

    def age(self, obj):
        return obj.age

    age.short_description = 'Age'

    def interests_count(self, obj):
        return obj.interests.count()

    interests_count.short_description = 'Interests'


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['added_at', 'total_price']
    fields = ['book', 'quantity', 'total_price', 'added_at']


class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'total_items_display', 'total_price_display']
    inlines = [CartItemInline]
    fieldsets = [
        ('Cart Information', {
            'fields': ['user', 'total_items_display', 'total_price_display']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def total_items_display(self, obj):
        return obj.total_items

    total_items_display.short_description = 'Total Items'

    def total_price_display(self, obj):
        return f"₹{obj.total_price}"

    total_price_display.short_description = 'Total Price'


class CartItemAdmin(admin.ModelAdmin):
    list_display = ['book', 'cart', 'quantity', 'total_price', 'added_at']
    list_filter = ['added_at', 'cart__user']
    search_fields = ['book__title', 'cart__user__username']
    readonly_fields = ['added_at', 'total_price_display']

    def total_price_display(self, obj):
        return f"₹{obj.total_price}"

    total_price_display.short_description = 'Total Price'


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    readonly_fields = ['added_at']
    fields = ['book', 'added_at']

class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'total_items_display']
    inlines = [WishlistItemInline]
    fieldsets = [
        ('Wishlist Information', {
            'fields': ['user', 'total_items_display']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def total_items_display(self, obj):
        return obj.total_items
    total_items_display.short_description = 'Total Items'

class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['book', 'wishlist', 'added_at']
    list_filter = ['added_at', 'wishlist__user']
    search_fields = ['book__title', 'wishlist__user__username']
    readonly_fields = ['added_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price_display']
    fields = ['book', 'book_type', 'quantity', 'price', 'total_price_display']

    def total_price_display(self, obj):
        return f"₹{obj.total_price}"

    total_price_display.short_description = 'Total'


class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'total_amount', 'order_status', 'payment_status', 'created_at',
                    'has_physical_books_display']
    list_filter = ['order_status', 'payment_status', 'created_at', 'has_physical_books']
    search_fields = ['order_id', 'user__username', 'user__email', 'tracking_number']
    readonly_fields = ['created_at', 'updated_at', 'total_items_display', 'is_digital_only_display']
    inlines = [OrderItemInline]
    fieldsets = [
        ('Order Information', {
            'fields': ['order_id', 'user', 'total_amount', 'total_items_display']
        }),
        ('Shipping & Delivery', {
            'fields': ['shipping_address', 'order_status', 'tracking_number', 'shipping_carrier', 'delivered_at']
        }),
        ('Payment', {
            'fields': ['payment_method', 'payment_status', 'paid_at']
        }),
        ('Order Type', {
            'fields': ['is_digital_only_display', 'has_physical_books_display'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def total_items_display(self, obj):
        return obj.total_items

    total_items_display.short_description = 'Total Items'

    def is_digital_only_display(self, obj):
        return obj.is_digital_only

    is_digital_only_display.short_description = 'Digital Only'
    is_digital_only_display.boolean = True

    def has_physical_books_display(self, obj):
        return obj.has_physical_books

    has_physical_books_display.short_description = 'Has Physical Books'
    has_physical_books_display.boolean = True


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'book', 'book_type', 'quantity', 'price', 'total_price_display']
    list_filter = ['book_type', 'order__order_status']
    search_fields = ['order__order_id', 'book__title']

    def total_price_display(self, obj):
        return f"₹{obj.total_price}"

    total_price_display.short_description = 'Total Price'


# Register models with default admin site
admin.site.register(Author, AuthorAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Reader, ReaderAdmin)

# Customize admin site header
admin.site.site_header = 'BookNook Administration'
admin.site.site_title = 'BookNook Admin'
admin.site.index_title = 'Book Management System'

# Register the cart models
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)

# Register the wishlist models
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(WishlistItem, WishlistItemAdmin)

# Register order models
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)