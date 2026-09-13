from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard Overview
    path('', views.AdminDashboardView.as_view(), name='index'),

    # Bookings CRUD
    path('bookings/', views.AdminBookingListView.as_view(), name='bookings_list'),
    path('bookings/create/', views.AdminBookingCreateView.as_view(), name='booking_create'),
    path('bookings/<int:pk>/edit/', views.AdminBookingUpdateView.as_view(), name='booking_edit'),
    path('bookings/<int:pk>/delete/', views.AdminBookingDeleteView.as_view(), name='booking_delete'),
    path('booking/<int:pk>/status/', views.UpdateBookingStatusView.as_view(), name='update_booking_status'),

    # Rooms & Room Types CRUD
    path('rooms/', views.AdminRoomListView.as_view(), name='rooms_list'),
    path('rooms/create/', views.AdminRoomCreateView.as_view(), name='room_create'),
    path('rooms/<int:pk>/edit/', views.AdminRoomUpdateView.as_view(), name='room_edit'),
    path('rooms/<int:pk>/delete/', views.AdminRoomDeleteView.as_view(), name='room_delete'),
    path('room-types/create/', views.AdminRoomTypeCreateView.as_view(), name='room_type_create'),
    path('room/<int:pk>/toggle/', views.ToggleRoomStatusView.as_view(), name='toggle_room_status'),

    # Guests & Users CRUD
    path('users/', views.AdminUserListView.as_view(), name='users_list'),
    path('users/create/', views.AdminUserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.AdminUserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.AdminUserDeleteView.as_view(), name='user_delete'),

    # Quick Actions
    path('quick-booking/', views.QuickBookingView.as_view(), name='quick_booking'),
]
