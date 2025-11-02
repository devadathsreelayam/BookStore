// Smart Navbar Behavior
document.addEventListener('DOMContentLoaded', function() {
    const navbar = document.getElementById('mainNavbar');
    let lastScrollTop = 0;
    const navbarHeight = navbar.offsetHeight;

    initializeWishlistHearts();
    initializeToasts();
    initializeNavbarScroll(navbar, lastScrollTop, navbarHeight);
    initializeSmoothScrolling();
    updateCartCount();
    initializePageLoad();
});

function initializeToasts() {
    const toastElList = document.querySelectorAll('.toast');
    const toastList = [...toastElList].map(toastEl => {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
        return toast;
    });

    // Auto-remove toasts from DOM after they hide
    toastElList.forEach(toastEl => {
        toastEl.addEventListener('hidden.bs.toast', function() {
            this.remove();
        });
    });
}

function initializeNavbarScroll(navbar, lastScrollTop, navbarHeight) {
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > lastScrollTop && scrollTop > navbarHeight) {
            // Scrolling down - hide navbar
            navbar.classList.add('navbar-hidden');
        } else {
            // Scrolling up - show navbar
            navbar.classList.remove('navbar-hidden');
        }

        if (scrollTop > 100) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }

        lastScrollTop = scrollTop;
    });
}

function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function updateCartCount() {
    const cartCount = document.querySelector('.cart-count');
    if (cartCount) {
        // Placeholder for future cart implementation
    }
}

function initializePageLoad() {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.3s ease';
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
}

// Wishlist functionality
function initializeWishlistHearts() {
    const wishlistHearts = document.querySelectorAll('.wishlist-heart');

    // First, check server state for all hearts
    checkWishlistStates().then(() => {
        // Then initialize click handlers
        wishlistHearts.forEach(heart => {
            initializeWishlistHeart(heart);
        });
    });
}

function initializeWishlistHeart(heart) {
    // Add click event
    heart.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const bookIsbn = this.dataset.bookIsbn;
        toggleWishlist(bookIsbn, this);
    });
}

function checkWishlistStates() {
    // Check server for wishlist status of all books on page
    const bookIsbns = Array.from(document.querySelectorAll('.wishlist-heart'))
        .map(heart => heart.dataset.bookIsbn)
        .filter(isbn => isbn); // Remove undefined

    if (bookIsbns.length === 0) return Promise.resolve();

    return fetch('/wishlist/check-status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({isbns: bookIsbns})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            data.wishlist_status.forEach(status => {
                const heart = document.querySelector(`.wishlist-heart[data-book-isbn="${status.isbn}"]`);
                if (heart) {
                    updateWishlistHeart(heart, status.in_wishlist);
                }
            });
        }
    })
    .catch(error => {
        console.error('Error checking wishlist status:', error);
    });
}

function toggleWishlist(bookIsbn, heartElement) {
    fetch('/wishlist/toggle-ajax/' + bookIsbn + '/', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            updateWishlistHeart(heartElement, data.in_wishlist);
            showToast(data.message, data.in_wishlist ? 'success' : 'info');
        } else {
            showToast(data.message, 'warning');
            // Revert heart state if failed
            updateWishlistHeart(heartElement, !heartElement.classList.contains('active'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error updating wishlist', 'danger');
        // Revert heart state if error
        updateWishlistHeart(heartElement, !heartElement.classList.contains('active'));
    });
}

function updateWishlistHeart(heart, inWishlist) {
    const heartIcon = heart.querySelector('i');

    if (inWishlist) {
        heart.classList.add('active');
        heartIcon.classList.remove('text-muted');
        heartIcon.classList.add('text-danger');
    } else {
        heart.classList.remove('active');
        heartIcon.classList.remove('text-danger');
        heartIcon.classList.add('text-muted');
    }
}

// Toast functionality
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();

    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" 
             id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas ${getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: duration });

    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });

    toast.show();
}

function getToastIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'danger': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    return icons[type] || 'fa-bell';
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}