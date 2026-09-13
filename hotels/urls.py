from django.urls import path

from .views import HomeView, RoomDetailView

app_name = 'hotels'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('rooms/<int:pk>/', RoomDetailView.as_view(), name='room_detail'),
]
