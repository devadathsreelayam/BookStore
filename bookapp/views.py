from datetime import timedelta, datetime

from django.db.models import Q, Sum, Count
from django.forms import modelform_factory
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.defaulttags import now
from django.utils import timezone

from bookapp.forms import UserRegistrationForm
from bookapp.models import Book, Author, Reader, Genre, CartItem, Cart, WishlistItem, Wishlist, Order, OrderItem


def home(request):
    """Home page view"""
    return render(request, 'home.html')


def auth_page(request):
    """Combined login/register page"""
    return render(request, 'auth.html')


@login_required
def logout_view(request):
    """Logout view"""
    if request.user.is_authenticated:
        logout(request)

    return redirect('home')


def login_view(request):
    """Login view"""
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # authenticate() returns user object if valid, None if invalid
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # This actually logs the user in and creates the session
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            # Check for 'next' parameter and redirect accordingly
            next_url = request.POST.get('next') or request.GET.get('next')

            if user.is_staff:
                return redirect(next_url or 'admin_order_dashboard')

            return redirect(next_url or 'book_catalog')
        else:
            # Show error message for invalid credentials
            messages.error(request, 'Invalid username or password.')

    next_param = request.GET.get('next', '')
    context = {
        'active_tab': 'login',
        'next_param': next_param,
    }

    return render(request, 'auth.html', context)


def register(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Create reader profile
            reader = Reader.objects.create(
                user=user,
                date_of_birth=form.cleaned_data['date_of_birth'],
                bio=form.cleaned_data['bio']
            )

            # Add selected interests
            interests = request.POST.get('interests', '').split(',')
            if interests:
                genre_objects = Genre.objects.filter(name__in=interests, parent__isnull=True)
                reader.interests.set(genre_objects)

            login(request, user)
            messages.success(request, 'Welcome to BookNook! Your reading journey begins now.')
            return redirect('book_catalog')

        else:
            # Form is invalid, it will be passed back with errors and data
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()

    return render(request, 'auth.html', {'form': form, 'active_tab': 'register'})


def book_catalog(request):
    """Book catalog with search and filters"""
    books = Book.objects.all()

    # Get filter parameters
    search_query = request.GET.get('q', '')
    genre_filter = request.GET.get('genre', '')
    author_filter = request.GET.get('author', '')
    format_filter = request.GET.get('format', '')
    sort_by = request.GET.get('sort', '')

    # Apply filters
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(authors__name__icontains=search_query) |
            Q(tags__icontains=search_query) |
            Q(summary__icontains=search_query)
        ).distinct()

    if genre_filter:
        books = books.filter(genre__name__icontains=genre_filter)

    if author_filter:
        books = books.filter(authors__name__icontains=author_filter)

    if format_filter == 'ebook':
        books = books.filter(book_type__in=['digital', 'both'])
    elif format_filter == 'physical':
        books = books.filter(book_type__in=['physical', 'both'])

    # Apply sorting
    if sort_by == 'newest':
        books = books.order_by('-created_at')
    elif sort_by == 'price_low':
        books = books.order_by('price')
    elif sort_by == 'price_high':
        books = books.order_by('-price')
    elif sort_by == 'title':
        books = books.order_by('title')
    else:
        books = books.order_by('-publication_year', 'title')

    # Get unique values for filters
    all_genres = Book.objects.values_list('genre__name', flat=True).distinct()
    all_authors = Author.objects.values_list('name', flat=True).distinct()

    context = {
        'books': books,
        'all_genres': all_genres,
        'all_authors': all_authors,
        'search_query': search_query,
        'selected_genre': genre_filter,
        'selected_author': author_filter,
        'sort_by': sort_by,
    }
    return render(request, 'book_catalog.html', context)


def book_detail(request, isbn):
    """Book detail page"""
    book = get_object_or_404(Book, isbn=isbn)

    # Calculate eBook price (75% of paperback)
    ebook_price = int(float(book.price) * 0.75) if book.price else 0

    # Get other books by the same author(s)
    same_author_books = Book.objects.filter(
        authors__in=book.authors.all()
    ).exclude(isbn=isbn).distinct()[:6]  # Limit to 6 books

    is_in_wishlist = WishlistItem.objects.filter(book_id=isbn, wishlist__user=request.user).exists()
    is_in_cart = CartItem.objects.filter(book_id=isbn, cart__user=request.user).exists()

    context = {
        'book': book,
        'same_author_books': same_author_books,
        'ebook_price': ebook_price,
        'is_in_wishlist': is_in_wishlist,
        'is_in_cart': is_in_cart,
    }
    return render(request, 'book_detail.html', context)


def get_or_create_cart(request):
    """Get or create cart for authenticated user"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    return None


@login_required
def add_to_cart(request, isbn):
    """Add book to cart"""
    book = get_object_or_404(Book, isbn=isbn)
    cart = get_or_create_cart(request)

    if book.book_type == 'digital':
        messages.warning(request, 'eBooks cannot be added to cart. Please use "Buy & Download" instead.')
        return redirect('book_detail', isbn=isbn)

    if book.stock == 0:
        messages.error(request, 'This book is out of stock.')
        return redirect('book_detail', isbn=isbn)

    # Add or update cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        book=book,
        book_type='physical',  # Explicitly set to physical
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f'Updated quantity of "{book.title}" in cart.')
    else:
        messages.success(request, f'Added "{book.title}" to cart.')

    return redirect('cart_detail')


def remove_from_cart(request, item_id):
    """Remove item from cart"""
    if not request.user.is_authenticated:
        return redirect('login')

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    book_title = cart_item.book.title
    cart_item.delete()

    messages.success(request, f'Removed "{book_title}" from cart.')
    return redirect('cart_detail')


def update_cart_quantity(request, item_id):
    """Update item quantity in cart"""
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

        if quantity <= 0:
            cart_item.delete()
            messages.success(request, f'Removed "{cart_item.book.title}" from cart.')
        else:
            if quantity > cart_item.book.stock:
                messages.error(request, f'Only {cart_item.book.stock} copies available.')
                return redirect('cart_detail')

            cart_item.quantity = quantity
            cart_item.save()
            # messages.success(request, f'Updated quantity of "{cart_item.book.title}".')

        # If AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            cart = get_or_create_cart(request)
            return JsonResponse({
                'success': True,
                'item_total': cart_item.total_price,
                'cart_total_items': cart.total_items,
                'cart_total_price': cart.total_price,
            })

    return redirect('cart_detail')


def reset_book_quantity(request, item_id):
    pass


def cart_detail(request):
    """Display cart contents"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to view your cart.')
        return redirect('login')

    cart = get_or_create_cart(request)
    # Force fresh query to get updated quantities and prices
    cart_items = cart.items.select_related('book').all()

    # Recalculate totals to ensure they're fresh
    cart_total_items = sum(item.quantity for item in cart_items)
    cart_total_price = sum(item.quantity * item.book.price for item in cart_items)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'cart_total_items': cart_total_items,
        'cart_total_price': cart_total_price,
    }
    return render(request, 'cart.html', context)


def clear_cart(request):
    """Clear all items from cart"""
    if not request.user.is_authenticated:
        return redirect('login')

    cart = get_or_create_cart(request)
    cart.clear()

    messages.success(request, 'Cart cleared successfully.')
    return redirect('cart_detail')


def get_or_create_wishlist(request):
    """Get or create wishlist for authenticated user"""
    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        return wishlist
    return None


def add_to_wishlist(request, isbn):
    """Add book to wishlist"""
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Please login to add to wishlist.'})
        messages.warning(request, 'Please login to add items to wishlist.')
        return redirect('login')

    book = get_object_or_404(Book, isbn=isbn)
    wishlist = get_or_create_wishlist(request)

    # Check if already in wishlist
    if WishlistItem.objects.filter(wishlist=wishlist, book=book).exists():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Book already in wishlist.'})
        messages.info(request, 'This book is already in your wishlist.')
        return redirect('book_detail', isbn=isbn)

    # Add to wishlist
    WishlistItem.objects.create(wishlist=wishlist, book=book)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Book added to wishlist!'})

    messages.success(request, f'Added "{book.title}" to wishlist.')
    return redirect('wishlist_detail')


def remove_from_wishlist(request, item_id):
    """Remove item from wishlist"""
    if not request.user.is_authenticated:
        return redirect('login')

    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=request.user)
    book_title = wishlist_item.book.title
    wishlist_item.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Book removed from wishlist!'})

    messages.success(request, f'Removed "{book_title}" from wishlist.')
    return redirect('wishlist_detail')


def move_to_cart(request, item_id):
    """Move wishlist item to cart"""
    if not request.user.is_authenticated:
        return redirect('login')

    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist__user=request.user)
    book = wishlist_item.book

    # Add to cart
    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        book=book,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # Remove from wishlist
    wishlist_item.delete()

    messages.success(request, f'Moved "{book.title}" to cart.')
    return redirect('wishlist_detail')


def wishlist_detail(request):
    """Display wishlist contents"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to view your wishlist.')
        return redirect('login')

    wishlist = get_or_create_wishlist(request)
    wishlist_items = wishlist.items.select_related('book').all()

    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items,
    }
    return render(request, 'wishlist.html', context)


def clear_wishlist(request):
    """Clear all items from wishlist"""
    if not request.user.is_authenticated:
        return redirect('login')

    wishlist = get_or_create_wishlist(request)
    wishlist.items.all().delete()

    messages.success(request, 'Wishlist cleared successfully.')
    return redirect('wishlist_detail')


def toggle_wishlist_ajax(request, isbn):
    """Toggle wishlist status via AJAX - for card view"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Please login to manage wishlist.'})

    try:
        book = get_object_or_404(Book, isbn=isbn)
        wishlist = get_or_create_wishlist(request)

        # Check if already in wishlist
        wishlist_item = WishlistItem.objects.filter(wishlist=wishlist, book=book).first()

        if wishlist_item:
            # Remove from wishlist
            wishlist_item.delete()
            action = 'removed'
            message = f'Removed "{book.title}" from wishlist.'
            in_wishlist = False
        else:
            # Add to wishlist
            WishlistItem.objects.create(wishlist=wishlist, book=book)
            action = 'added'
            message = f'Added "{book.title}" to wishlist.'
            in_wishlist = True

        return JsonResponse({
            'success': True,
            'message': message,
            'action': action,
            'in_wishlist': in_wishlist
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error updating wishlist.'
        })


def check_wishlist_status(request):
    """Check wishlist status for multiple books"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'wishlist_status': []})

    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        isbns = data.get('isbns', [])

        wishlist = get_or_create_wishlist(request)
        wishlist_items = WishlistItem.objects.filter(
            wishlist=wishlist,
            book__isbn__in=isbns
        ).select_related('book')

        # Create status list
        status_list = []
        for isbn in isbns:
            in_wishlist = any(item.book.isbn == isbn for item in wishlist_items)
            status_list.append({
                'isbn': isbn,
                'in_wishlist': in_wishlist
            })

        return JsonResponse({
            'success': True,
            'wishlist_status': status_list
        })

    return JsonResponse({'success': False, 'wishlist_status': []})


@login_required
def order_list(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'orders': orders
    }
    return render(request, 'orders/order_list.html', context)


@login_required
def order_detail(request, order_id):
    """Display order details"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    context = {
        'order': order
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
def create_order(request):
    """Create order from cart - show confirmation and process order"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('book').all()

    if not cart_items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart_detail')

    # Check stock for physical books
    for item in cart_items:
        if item.book.book_type in ['physical', 'both'] and item.quantity > item.book.stock:
            messages.error(request, f'Only {item.book.stock} copies of "{item.book.title}" available.')
            return redirect('cart_detail')

    if request.method == 'POST':
        try:
            shipping_address = request.POST.get('shipping_address', '').strip()
            payment_method = request.POST.get('payment_method', '').strip()

            # Validate required fields
            if not shipping_address and any(item.book.book_type in ['physical', 'both'] for item in cart_items):
                messages.error(request, 'Shipping address is required for physical books.')
                return render(request, 'orders/order_confirm.html', {
                    'cart': cart,
                    'cart_items': cart_items
                })

            if not payment_method:
                messages.error(request, 'Please select a payment method.')
                return render(request, 'orders/order_confirm.html', {
                    'cart': cart,
                    'cart_items': cart_items
                })

            # Create order
            order = Order.objects.create(
                user=request.user,
                total_amount=cart.total_price,
                shipping_address=shipping_address,
                payment_method=payment_method
            )

            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    book=cart_item.book,
                    quantity=cart_item.quantity,
                    price=cart_item.book.price,
                    book_type=cart_item.book.book_type
                )

                # Update stock for physical books
                if cart_item.book.book_type in ['physical', 'both']:
                    cart_item.book.stock -= cart_item.quantity
                    cart_item.book.save()

            # Clear cart
            cart.clear()

            messages.success(request, f'Order #{order.order_id} created successfully!')
            return redirect('order_detail', order_id=order.order_id)

        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
            return redirect('cart_detail')

    # GET request - show order confirmation page
    context = {
        'cart': cart,
        'cart_items': cart_items
    }
    return render(request, 'orders/order_confirm.html', context)


@login_required
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if order.order_status not in ['pending', 'confirmed']:
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('order_detail', order_id=order_id)

    if request.method == 'POST':
        order.order_status = 'cancelled'
        order.save()

        # Restore stock for physical books
        for item in order.items.all():
            if item.book.book_type in ['physical', 'both']:
                item.book.stock += item.quantity
                item.book.save()

        messages.success(request, f'Order #{order.order_id} has been cancelled.')
        return redirect('order_list')

    context = {
        'order': order
    }
    return render(request, 'orders/order_cancel.html', context)


def author_list(request):
    """Display all authors"""
    authors = Author.objects.all().order_by('name')

    # Optional: Filter by first letter
    letter_filter = request.GET.get('letter', '')
    if letter_filter:
        authors = authors.filter(name__istartswith=letter_filter)

    # Get alphabet for filtering
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    context = {
        'authors': authors,
        'alphabet': alphabet,
        'selected_letter': letter_filter,
    }
    return render(request, 'authors/author_list.html', context)


def author_detail(request, author_id):
    """Display author details and their books"""
    author = get_object_or_404(Author, id=author_id)
    books = author.books.all().order_by('-publication_year')

    context = {
        'author': author,
        'books': books,
    }
    return render(request, 'authors/author_detail.html', context)


def new_arrivals(request):
    """Display books added in the last 7 days"""
    # Calculate date 7 days ago
    seven_days_ago = timezone.now() - timedelta(days=7)

    # Get books created in the last 7 days, ordered by newest first
    new_books = Book.objects.filter(
        created_at__gte=seven_days_ago
    ).order_by('-created_at')[:10]  # Limit to 10 most recent

    # Count total new arrivals (without limit)
    total_new_arrivals = Book.objects.filter(
        created_at__gte=seven_days_ago
    ).count()

    context = {
        'new_books': new_books,
        'total_new_arrivals': total_new_arrivals,
        'seven_days_ago': seven_days_ago.date(),
    }
    return render(request, 'new_arrivals.html', context)


@login_required
def purchase_ebook(request, isbn):
    """Handle eBook purchase and download"""
    from .utils import generate_ebook_pdf

    book = get_object_or_404(Book, isbn=isbn)

    if book.book_type not in ['digital', 'both']:
        messages.error(request, 'This book is not available as an eBook.')
        return redirect('book_detail', isbn=isbn)

    try:
        # Generate the eBook PDF
        pdf_file = generate_ebook_pdf(book)

        # Create response with PDF
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{book.title.replace(" ", "_")}_ebook.pdf"'

        # Show success message
        messages.success(request, f'Thank you for purchasing "{book.title}"! Your eBook is downloading.')

        return response

    except Exception as e:
        messages.error(request, 'Error generating eBook. Please try again.')
        return redirect('book_detail', isbn=isbn)


@login_required
def preview_ebook(request, isbn):
    """Generate a preview PDF for the eBook"""
    from .utils import generate_preview_pdf

    book = get_object_or_404(Book, isbn=isbn)

    if book.book_type not in ['digital', 'both']:
        messages.error(request, 'Preview not available for this book.')
        return redirect('book_detail', isbn=isbn)

    try:
        # Generate preview PDF (similar to full eBook but with preview limitations)
        pdf_file = generate_preview_pdf(book)

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{book.title.replace(" ", "_")}_preview.pdf"'

        return response

    except Exception as e:
        messages.error(request, 'Error generating preview.')
        return redirect('book_detail', isbn=isbn)


# For admin
def staff_required(user):
    return user.is_staff


@user_passes_test(staff_required)
def admin_book_management(request):
    """Admin book management dashboard"""
    books = Book.objects.all().order_by('-created_at')

    # Quick stats
    total_books = books.count()
    low_stock_books = books.filter(stock__lt=5, book_type__in=['physical', 'both']).count()
    out_of_stock_books = books.filter(stock=0, book_type__in=['physical', 'both']).count()

    # Handle POST requests
    if request.method == 'POST':
        response = handle_admin_actions(request, books)
        if response:
            return response

    context = {
        'books': books,
        'total_books': total_books,
        'low_stock_books': low_stock_books,
        'out_of_stock_books': out_of_stock_books,
    }
    return render(request, 'admin/book_management.html', context)


def handle_admin_actions(request, books):
    """Handle all admin actions from the book management page"""
    action = request.POST.get('action')

    if not action:
        return None

    if action == 'update_image':
        return handle_image_update(request)

    elif action in ['restock_custom', 'toggle_availability']:
        return handle_bulk_actions(request, action)

    return None


def handle_image_update(request):
    """Handle individual image updates via AJAX"""
    book_isbn = request.POST.get('book_isbn')
    new_image_url = request.POST.get('image_url')

    if book_isbn and new_image_url:
        try:
            book = Book.objects.get(isbn=book_isbn)
            book.cover_image = new_image_url
            book.save()
            return JsonResponse({'success': True, 'message': 'Image updated successfully'})
        except Book.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Book not found'})

    return JsonResponse({'success': False, 'message': 'Invalid data'})


def handle_bulk_actions(request, action):
    """Handle bulk actions for multiple books"""
    book_isbns = request.POST.getlist('book_ids')

    if not book_isbns:
        messages.error(request, 'No books selected.')
        return None

    if action == 'restock_custom':
        return handle_restock_action(request, book_isbns)

    elif action == 'toggle_availability':
        return handle_toggle_availability(request, book_isbns)

    return None


def handle_restock_action(request, book_isbns):
    """Handle restock actions (both bulk and individual)"""
    custom_stock = request.POST.get('custom_stock', 10)

    try:
        stock_value = int(custom_stock)
        if stock_value < 0:
            messages.error(request, 'Stock value cannot be negative.')
            return None

        # Handle individual book restock (from quick restock modal)
        # The individual restock sends the book ISBN as both book_isbn and in book_ids list
        if not book_isbns:
            # Fallback: check if it's a single book restock
            single_book_isbn = request.POST.get('book_isbn')
            if single_book_isbn:
                book_isbns = [single_book_isbn]

        if not book_isbns:
            messages.error(request, 'No books selected for restocking.')
            return None

        books_updated = Book.objects.filter(isbn__in=book_isbns).update(stock=stock_value)
        messages.success(request, f'Restocked {books_updated} books to {stock_value} units.')

    except ValueError:
        messages.error(request, 'Invalid stock value.')

    return None


def handle_toggle_availability(request, book_isbns):
    """Toggle availability for selected books"""
    books_to_update = Book.objects.filter(isbn__in=book_isbns)
    updated_count = 0

    for book in books_to_update:
        # Only toggle physical books
        if book.book_type in ['physical', 'both']:
            book.stock = 0 if book.stock > 0 else 10
            book.save()
            updated_count += 1

    messages.success(request, f'Updated availability for {updated_count} books.')
    return None


@user_passes_test(staff_required)
def admin_book_detail(request, isbn):
    """Admin book detail view for both viewing and editing"""
    book = get_object_or_404(Book, isbn=isbn)

    # Create a model form with specific fields
    BookForm = modelform_factory(
        Book,
        fields=[
            'title', 'authors', 'publication_year', 'price',
            'summary', 'cover_image', 'genre', 'book_type', 'stock'
        ],
        labels={
            'title': 'Book Title',
            'authors': 'Authors',
            'publication_year': 'Publication Year',
            'price': 'Price (₹)',
            'summary': 'Summary',
            'cover_image': 'Cover Image URL',
            'genre': 'Genre',
            'book_type': 'Book Type',
            'stock': 'Stock Quantity'
        },
        help_texts={
            'stock': 'Stock only applies to physical books',
            'book_type': 'Digital books ignore stock quantity',
            'cover_image': 'URL to book cover image'
        }
    )

    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f'Book "{book.title}" updated successfully!')
            return redirect('admin_book_detail', isbn=book.isbn)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookForm(instance=book)

    # Get related data for the template
    all_authors = Author.objects.all().order_by('name')
    all_genres = Genre.objects.all().order_by('name')

    context = {
        'book': book,
        'form': form,
        'all_authors': all_authors,
        'all_genres': all_genres,
        'is_editing': request.method == 'POST'
    }

    return render(request, 'admin/book_detail.html', context)


@user_passes_test(staff_required)
def admin_book_add(request):
    """Admin book add view for creating new books"""

    # Create a model form with all required fields
    BookForm = modelform_factory(
        Book,
        fields=[
            'isbn', 'title', 'authors', 'publication_year', 'price',
            'summary', 'cover_image', 'genre', 'book_type', 'stock'
        ],
        labels={
            'isbn': 'ISBN *',
            'title': 'Book Title *',
            'authors': 'Authors *',
            'publication_year': 'Publication Year *',
            'price': 'Price (₹) *',
            'summary': 'Summary',
            'cover_image': 'Cover Image URL',
            'genre': 'Genre',
            'book_type': 'Book Type *',
            'stock': 'Stock Quantity'
        },
        help_texts={
            'isbn': 'Unique ISBN identifier for the book',
            'stock': 'Stock only applies to physical books (default: 0)',
            'book_type': 'Digital books ignore stock quantity',
            'cover_image': 'URL to book cover image'
        }
    )

    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            # Set created_at and updated_at
            book.created_at = datetime.now()
            book.updated_at = datetime.now()
            book.save()
            form.save_m2m()  # Save many-to-many relationships (authors)

            messages.success(request, f'Book "{book.title}" added successfully!')
            return redirect('admin_book_detail', isbn=book.isbn)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookForm(initial={'stock': 0, 'book_type': 'both'})

    # Get related data for the template
    all_authors = Author.objects.all().order_by('name')
    all_genres = Genre.objects.all().order_by('name')

    context = {
        'form': form,
        'all_authors': all_authors,
        'all_genres': all_genres,
        'is_adding': True
    }

    return render(request, 'admin/book_detail.html', context)


@user_passes_test(staff_required)
def admin_author_management(request):
    """Admin author management dashboard"""
    authors = Author.objects.all().order_by('name')

    # Quick stats
    total_authors = authors.count()
    authors_with_photos = authors.exclude(photo__isnull=True).exclude(photo='').count()

    # Handle bulk actions or individual updates
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_photo':
            author_id = request.POST.get('author_id')
            new_photo_url = request.POST.get('photo_url')
            if author_id and new_photo_url:
                author = get_object_or_404(Author, id=author_id)
                author.photo = new_photo_url
                author.save()
                return JsonResponse({'success': True, 'message': 'Photo updated successfully'})
            return JsonResponse({'success': False, 'message': 'Invalid data'})

    context = {
        'authors': authors,
        'total_authors': total_authors,
        'authors_with_photos': authors_with_photos,
    }
    return render(request, 'admin/author_management.html', context)


@user_passes_test(staff_required)
def admin_author_detail(request, author_id):
    """Admin author detail view for both viewing and editing"""
    author = get_object_or_404(Author, id=author_id)

    # Create a model form
    AuthorForm = modelform_factory(
        Author,
        fields=['name', 'bio', 'photo'],
        labels={
            'name': 'Author Name *',
            'bio': 'Biography',
            'photo': 'Photo URL'
        },
        help_texts={
            'photo': 'URL to author photo',
            'bio': 'Brief biography of the author'
        }
    )

    if request.method == 'POST':
        form = AuthorForm(request.POST, instance=author)
        if form.is_valid():
            form.save()
            messages.success(request, f'Author "{author.name}" updated successfully!')
            return redirect('admin_author_detail', author_id=author.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AuthorForm(instance=author)

    context = {
        'author': author,
        'form': form,
        'is_editing': request.method == 'POST'
    }

    return render(request, 'admin/author_detail.html', context)


@user_passes_test(staff_required)
def admin_author_add(request):
    """Admin author add view for creating new authors"""

    AuthorForm = modelform_factory(
        Author,
        fields=['name', 'bio', 'photo'],
        labels={
            'name': 'Author Name *',
            'bio': 'Biography',
            'photo': 'Photo URL'
        },
        help_texts={
            'photo': 'URL to author photo',
            'bio': 'Brief biography of the author'
        }
    )

    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            author = form.save()
            messages.success(request, f'Author "{author.name}" added successfully!')
            return redirect('admin_author_detail', author_id=author.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AuthorForm()

    context = {
        'form': form,
        'is_adding': True
    }

    return render(request, 'admin/author_detail.html', context)


@user_passes_test(staff_required)
def admin_order_dashboard(request):
    """Admin order dashboard with date range filtering"""

    # Date range handling
    default_start = (datetime.now() - timedelta(days=7)).date()
    default_end = datetime.now().date()

    start_date = request.GET.get('start_date', default_start)
    end_date = request.GET.get('end_date', default_end)

    # Convert string dates to date objects
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except:
            start_date = default_start

    if isinstance(end_date, str):
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except:
            end_date = default_end

    # Adjust end_date to include the entire day
    end_date_with_time = datetime.combine(end_date, datetime.max.time())

    # Base queryset for the date range
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    # Summary statistics
    total_orders = orders.count()
    total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_items_sold = OrderItem.objects.filter(
        order__in=orders
    ).aggregate(Sum('quantity'))['quantity__sum'] or 0

    # Order status breakdown
    status_breakdown = orders.values('order_status').annotate(
        count=Count('order_id'),
        revenue=Sum('total_amount')
    ).order_by('order_status')

    # Payment status breakdown
    payment_breakdown = orders.values('payment_status').annotate(
        count=Count('order_id'),
        revenue=Sum('total_amount')
    ).order_by('payment_status')

    # Book type breakdown
    book_type_breakdown = OrderItem.objects.filter(
        order__in=orders
    ).values('book_type').annotate(
        count=Count('id'),
        total_quantity=Sum('quantity'),
        revenue=Sum('price')
    ).order_by('book_type')

    # Recent orders (last 10)
    recent_orders = orders.select_related('user').prefetch_related('items').order_by('-created_at')[:10]

    # Top selling books
    top_books = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'book__title', 'book__isbn'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum('price')
    ).order_by('-total_sold')[:10]

    # Daily revenue trend (last 7 days)
    daily_revenue = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).extra(
        {'date': "date(created_at)"}
    ).values('date').annotate(
        revenue=Sum('total_amount'),
        orders=Count('order_id')
    ).order_by('date')

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_items_sold': total_items_sold,
        'status_breakdown': status_breakdown,
        'payment_breakdown': payment_breakdown,
        'book_type_breakdown': book_type_breakdown,
        'recent_orders': recent_orders,
        'top_books': top_books,
        'daily_revenue': daily_revenue,
        'start_date': start_date,
        'end_date': end_date,
        'default_start': default_start,
        'default_end': default_end,
        'hide_reader_links': True,
    }

    return render(request, 'admin/order_dashboard.html', context)