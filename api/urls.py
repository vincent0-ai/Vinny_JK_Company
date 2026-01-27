from django.urls import path
from .views import cancel_order, cancel_booking
from .views import (
    ServicesListCreateView, ServicesDetailView,
    GoodsListCreateView, GoodsDetailView,
    OrderCreateView, OrderListView, OrderDetailView,
    BookingCreateView, BookingListView, BookingDetailView
)

urlpatterns = [
    # Services
    path('services/', ServicesListCreateView.as_view()),
    path('services/<int:pk>/', ServicesDetailView.as_view()),

    # Goods
    path('goods/', GoodsListCreateView.as_view()),
    path('goods/<int:pk>/', GoodsDetailView.as_view()),

    # Orders
    path('orders/', OrderListView.as_view()),
    path('orders/create/', OrderCreateView.as_view()),
    path('orders/<int:pk>/cancel/', cancel_order),
    path('orders/<int:pk>/', OrderDetailView.as_view()),

    # Bookings
    path('bookings/', BookingListView.as_view()),
    path('bookings/create/', BookingCreateView.as_view()),
    path('bookings/<int:pk>/cancel/', cancel_booking),
    path('bookings/<int:pk>/', BookingDetailView.as_view()),
]
