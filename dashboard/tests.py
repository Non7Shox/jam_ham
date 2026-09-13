from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking
from hotels.models import Room, RoomType

User = get_user_model()


class DashboardFullCRUDTestCase(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffadmin',
            email='staff@hotel.com',
            password='password123',
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username='regularguest',
            email='guest@hotel.com',
            password='password123',
            is_staff=False,
        )
        self.room_type = RoomType.objects.create(
            name='Luxury Suite', description='High end suite'
        )
        self.room = Room.objects.create(
            room_number='101',
            room_type=self.room_type,
            price_per_night=Decimal('250.00'),
            capacity=2,
            is_active=True,
        )
        today = timezone.localdate()
        self.booking = Booking.objects.create(
            user=self.regular_user,
            room=self.room,
            check_in=today,
            check_out=today + timedelta(days=2),
            status=Booking.Status.PENDING,
            total_price=Decimal('500.00'),
        )

    # --- Overview & Permissions ---
    def test_dashboard_permission(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)

        self.client.login(username='staffadmin', password='password123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)

    # --- Bookings CRUD ---
    def test_bookings_list_view(self):
        self.client.login(username='staffadmin', password='password123')
        response = self.client.get(reverse('dashboard:bookings_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.booking, response.context['bookings'])

    def test_booking_create_view(self):
        self.client.login(username='staffadmin', password='password123')
        today = timezone.localdate()
        url = reverse('dashboard:booking_create')
        data = {
            'user': self.regular_user.pk,
            'room': self.room.pk,
            'check_in': (today + timedelta(days=5)).strftime('%Y-%m-%d'),
            'check_out': (today + timedelta(days=7)).strftime('%Y-%m-%d'),
            'status': 'confirmed',
            'total_price': '500.00',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Booking.objects.count(), 2)

    def test_booking_update_view(self):
        self.client.login(username='staffadmin', password='password123')
        url = reverse('dashboard:booking_edit', kwargs={'pk': self.booking.pk})
        data = {
            'user': self.regular_user.pk,
            'room': self.room.pk,
            'check_in': self.booking.check_in.strftime('%Y-%m-%d'),
            'check_out': self.booking.check_out.strftime('%Y-%m-%d'),
            'status': 'confirmed',
            'total_price': '600.00',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')

    def test_booking_delete_view(self):
        self.client.login(username='staffadmin', password='password123')
        url = reverse('dashboard:booking_delete', kwargs={'pk': self.booking.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Booking.objects.filter(pk=self.booking.pk).count(), 0)

    # --- Rooms & Room Types CRUD ---
    def test_rooms_list_view(self):
        self.client.login(username='staffadmin', password='password123')
        response = self.client.get(reverse('dashboard:rooms_list'))
        self.assertEqual(response.status_code, 200)

    def test_room_create_view(self):
        self.client.login(username='staffadmin', password='password123')
        url = reverse('dashboard:room_create')
        data = {
            'room_number': '102',
            'room_type': self.room_type.pk,
            'price_per_night': '199.00',
            'capacity': 2,
            'description': 'Cozy deluxe room',
            'is_active': True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Room.objects.filter(room_number='102').count(), 1)

    def test_room_update_view(self):
        self.client.login(username='staffadmin', password='password123')
        url = reverse('dashboard:room_edit', kwargs={'pk': self.room.pk})
        data = {
            'room_number': '101',
            'room_type': self.room_type.pk,
            'price_per_night': '300.00',
            'capacity': 3,
            'description': 'Updated suite description',
            'is_active': True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.room.refresh_from_db()
        self.assertEqual(self.room.price_per_night, Decimal('300.00'))

    def test_room_type_create_view(self):
        self.client.login(username='staffadmin', password='password123')
        url = reverse('dashboard:room_type_create')
        data = {'name': 'Penthouse', 'description': 'Top floor suite'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoomType.objects.filter(name='Penthouse').count(), 1)

    # --- Users & Staff CRUD ---
    def test_users_list_view(self):
        self.client.login(username='staffadmin', password='password123')
        response = self.client.get(reverse('dashboard:users_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_create_view(self):
        self.client.login(username='staffadmin', password='password123')
        url = reverse('dashboard:user_create')
        data = {
            'username': 'newstaff',
            'first_name': 'New',
            'last_name': 'Staff',
            'email': 'newstaff@hotel.com',
            'phone_number': '+1 555-9988',
            'is_staff': True,
            'is_active': True,
            'password': 'password123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        u = User.objects.get(username='newstaff')
        self.assertTrue(u.is_staff)
        self.assertEqual(u.profile.phone_number, '+1 555-9988')

    def test_user_update_view(self):
        self.client.login(username='staffadmin', password='password123')
        url = reverse('dashboard:user_edit', kwargs={'pk': self.regular_user.pk})
        data = {
            'username': 'regularguest',
            'first_name': 'Updated',
            'last_name': 'GuestName',
            'email': 'updated@hotel.com',
            'phone_number': '+1 555-1234',
            'is_staff': False,
            'is_active': True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.first_name, 'Updated')
        self.assertEqual(self.regular_user.profile.phone_number, '+1 555-1234')

    def test_user_delete_view(self):
        self.client.login(username='staffadmin', password='password123')
        url = reverse('dashboard:user_delete', kwargs={'pk': self.regular_user.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.filter(pk=self.regular_user.pk).count(), 0)
