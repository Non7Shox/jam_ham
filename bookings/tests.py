from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from bookings.models import Booking
from hotels.models import Room, RoomType


class AvailabilityTests(TestCase):
    def setUp(self):
        self.room_type = RoomType.objects.create(name='Standard')
        self.room = Room.objects.create(
            room_number='101',
            room_type=self.room_type,
            price_per_night=Decimal('100.00'),
            capacity=2,
        )
        self.user = User.objects.create_user(username='guest', password='pass1234')
        self.check_in = date.today() + timedelta(days=5)
        self.check_out = self.check_in + timedelta(days=3)

    def test_room_available_when_no_bookings(self):
        self.assertTrue(self.room.is_available(self.check_in, self.check_out))

    def test_room_unavailable_when_overlapping_booking(self):
        Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=self.check_in,
            check_out=self.check_out,
            status=Booking.Status.CONFIRMED,
            total_price=Decimal('300.00'),
        )
        self.assertFalse(self.room.is_available(self.check_in, self.check_out))

    def test_cancelled_booking_does_not_block_availability(self):
        Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=self.check_in,
            check_out=self.check_out,
            status=Booking.Status.CANCELLED,
            total_price=Decimal('300.00'),
        )
        self.assertTrue(self.room.is_available(self.check_in, self.check_out))

    def test_available_between_queryset(self):
        other_room = Room.objects.create(
            room_number='102',
            room_type=self.room_type,
            price_per_night=Decimal('100.00'),
            capacity=2,
        )
        Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=self.check_in,
            check_out=self.check_out,
            status=Booking.Status.CONFIRMED,
            total_price=Decimal('300.00'),
        )
        available = Room.objects.available_between(self.check_in, self.check_out)
        self.assertIn(other_room, available)
        self.assertNotIn(self.room, available)


class BookingFlowTests(TestCase):
    def setUp(self):
        self.room_type = RoomType.objects.create(name='Deluxe')
        self.room = Room.objects.create(
            room_number='201',
            room_type=self.room_type,
            price_per_night=Decimal('150.00'),
            capacity=2,
        )
        self.user = User.objects.create_user(username='booker', password='pass1234')
        self.check_in = date.today() + timedelta(days=10)
        self.check_out = self.check_in + timedelta(days=2)

    def test_booking_page_requires_login(self):
        url = reverse('bookings:book_room', kwargs={'room_pk': self.room.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_create_booking(self):
        self.client.login(username='booker', password='pass1234')
        url = reverse('bookings:book_room', kwargs={'room_pk': self.room.pk})
        response = self.client.post(url, {
            'check_in': self.check_in.isoformat(),
            'check_out': self.check_out.isoformat(),
        })
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.get()
        self.assertEqual(booking.total_price, Decimal('300.00'))
        self.assertEqual(response.status_code, 302)
