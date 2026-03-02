from django.urls import path
from .views import cancel_order, cancel_booking, mark_order_delivered
from .views import (
    ServicesListCreateView, ServicesDetailView,
    ProductListCreateView, ProductDetailView,
    create_order, OrderListView, OrderDetailView,
    BookingCreateView, BookingListView, BookingDetailView, create_booking,
    confirm_booking, complete_booking,
    bookings_summary, booking_revenue, daily_bookings, monthly_bookings, weekly_bookings,
    CartCreateView, CartDetailView, add_to_cart, UpdateCartItemView,
    initiate_mpesa_payment, mpesa_callback, initiate_stripe_payment,
    GalleryListCreateView, GalleryDetailView, admin_dashboard_stats
)

urlpatterns = [
    # Services
    path('services/', ServicesListCreateView.as_view()),
    path('services/<int:pk>/', ServicesDetailView.as_view()),

    # Products
    path('products/', ProductListCreateView.as_view()),
    path('products/<int:pk>/', ProductDetailView.as_view()),

    # Orders
    path('orders/', OrderListView.as_view()),
    path('orders/create/', create_order),
    path('orders/<int:order_id>/cancel/', cancel_order),
    path('orders/<int:order_id>/deliver/', mark_order_delivered),
    path('orders/<int:pk>/', OrderDetailView.as_view()),

    # Bookings
    path('bookings/', BookingListView.as_view()),
    path('bookings/create/', create_booking),
    path('bookings/<int:booking_id>/confirm/', confirm_booking),
    path('bookings/<int:booking_id>/complete/', complete_booking),
    path('bookings/<int:booking_id>/cancel/', cancel_booking),
    path('bookings/<int:pk>/', BookingDetailView.as_view()),
    #booking summary
    path('bookings/summary/', bookings_summary),
    path('bookings/revenue/', booking_revenue),
    path('bookings/daily/', daily_bookings),
    path('bookings/monthly/', monthly_bookings),
    path('bookings/weekly/', weekly_bookings),

    # Cart
    path('cart/create/', CartCreateView.as_view(), name='cart-create'),
    path('cart/<uuid:id>/', CartDetailView.as_view(), name='cart-detail'),
    path('cart/<uuid:cart_id>/items/', add_to_cart, name='add-to-cart'),
    path('cart/items/<int:pk>/', UpdateCartItemView.as_view(), name='update-cart-item'),

    # Payments
    path('payment/mpesa/initiate/<int:order_id>/', initiate_mpesa_payment, name='initiate-mpesa'),
    path('payment/mpesa/callback/', mpesa_callback, name='mpesa-callback'),
    path('payment/stripe/initiate/<int:order_id>/', initiate_stripe_payment, name='initiate-stripe'),
    
    # Gallery
    path('gallery/', GalleryListCreateView.as_view(), name='gallery-list'),
    path('gallery/<int:pk>/', GalleryDetailView.as_view(), name='gallery-detail'),

    # Admin Dashboard Stats
    path('admin/dashboard-stats/', admin_dashboard_stats, name='admin-dashboard-stats'),
]
