from django.urls import path

from .views import (
    BookingCreateView,
    BookingSuccessView,
    CancelBookingView,
    MyBookingsView,
)

app_name = 'bookings'

urlpatterns = [
    path('my-bookings/', MyBookingsView.as_view(), name='my_bookings'),
    path('rooms/<int:room_pk>/book/', BookingCreateView.as_view(), name='book_room'),
    path('<int:pk>/success/', BookingSuccessView.as_view(), name='booking_success'),
    path('<int:pk>/cancel/', CancelBookingView.as_view(), name='cancel_booking'),
]
