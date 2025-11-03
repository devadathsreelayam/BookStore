from django.urls import path
from . import views

urlpatterns = [
    # Core pages
    path('', views.home, name='home'),

    # Authentication
    path('auth/', views.auth_page, name='auth_page'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),


    # Catalog and book details
    path('catalog/', views.book_catalog, name='book_catalog'),
    path('book/<str:isbn>/', views.book_detail, name='book_detail'),


    # eBook URLs
    path('ebook/purchase/<str:isbn>/', views.purchase_ebook, name='purchase_ebook'),
    path('ebook/preview/<str:isbn>/', views.preview_ebook, name='preview_ebook'),


    # Cart URLs
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<str:isbn>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),


    # Wishlist URLs
    path('wishlist/', views.wishlist_detail, name='wishlist_detail'),
    path('wishlist/add/<str:isbn>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/move-to-cart/<int:item_id>/', views.move_to_cart, name='move_to_cart'),
    path('wishlist/clear/', views.clear_wishlist, name='clear_wishlist'),
    path('wishlist/toggle-ajax/<str:isbn>/', views.toggle_wishlist_ajax, name='toggle_wishlist_ajax'),
    path('wishlist/check-status/', views.check_wishlist_status, name='check_wishlist_status'),


    # Order URLs
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<str:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    # Generic patterns last
    path('orders/<str:order_id>/', views.order_detail, name='order_detail'),
    path('order/<str:order_id>/payment/', views.order_payment_gateway, name='order_payment_gateway'),
    path('order/payment/success/', views.handle_order_payment_success, name='order_payment_success'),
    path('order/<str:order_id>/payment/cancel/', views.cancel_payment, name='cancel_payment'),
    path('orders/', views.order_list, name='order_list'),


    # Author Related URLs
    path('authors/', views.author_list, name='author_list'),
    path('authors/<int:author_id>/', views.author_detail, name='author_detail'),

    # New arrivals
    path('new-arrivals/', views.new_arrivals, name='new_arrivals'),


    # Admin URLs
    path('admin-books/add/', views.admin_book_add, name='admin_book_add'),
    path('admin-books/<str:isbn>/', views.admin_book_detail, name='admin_book_detail'),
    path('admin-books/', views.admin_book_management, name='admin_book_management'),


    # Admin author management
    path('admin-authors/add/', views.admin_author_add, name='admin_author_add'),
    path('admin-authors/<int:author_id>/', views.admin_author_detail, name='admin_author_detail'),
    path('admin-authors/', views.admin_author_management, name='admin_author_management'),
    path('admin-dash/', views.admin_order_dashboard, name='admin_order_dashboard'),
]