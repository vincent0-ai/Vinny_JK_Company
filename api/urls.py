from django.urls import path
from .views import cancel_order, cancel_booking
from .views import (
    ServicesListCreateView, ServicesDetailView,
    ProductListCreateView, ProductDetailView,
    OrderCreateView, OrderListView, OrderDetailView,
    BookingCreateView, BookingListView, BookingDetailView,
    confirm_booking, complete_booking,
    bookings_summary, booking_revenue, daily_bookings, monthly_bookings, weekly_bookings
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
]
