from django.urls import path
from .views import cancel_order, cancel_booking
from .views import (
    ServicesListCreateView, ServicesDetailView,
    ProductListCreateView, ProductDetailView,
    OrderCreateView, OrderListView, OrderDetailView,
    BookingCreateView, BookingListView, BookingDetailView,
    confirm_booking, complete_booking,
    bookings_summary, booking_revenue, daily_bookings, monthly_bookings, weekly_bookings,
    CartCreateView, CartDetailView, add_to_cart, UpdateCartItemView,
    initiate_mpesa_payment, mpesa_callback, initiate_stripe_payment
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
    path('orders/create/', OrderCreateView.as_view()),
    path('orders/<int:pk>/cancel/', cancel_order),
    path('orders/<int:pk>/', OrderDetailView.as_view()),

    # Bookings
    path('bookings/', BookingListView.as_view()),
    path('bookings/create/', BookingCreateView.as_view()),
    path('bookings/<int:pk>/confirm/', confirm_booking),
    path('bookings/<int:pk>/complete/', complete_booking),
    path('bookings/<int:pk>/cancel/', cancel_booking),
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
]
