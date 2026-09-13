from django.contrib import admin
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking
from hotels.models import Room


admin.site.site_header = 'Grand Horizon Hotel administration'
admin.site.site_title = 'Grand Horizon admin'
admin.site.index_title = 'Dashboard'


def dashboard_context():
    today = timezone.localdate()
    active_statuses = [Booking.Status.PENDING, Booking.Status.CONFIRMED]
    live_bookings = Booking.objects.filter(status__in=active_statuses)

    occupied_today = (
        live_bookings.filter(check_in__lte=today, check_out__gt=today)
        .values('room_id')
        .distinct()
        .count()
    )
    rooms_active = Room.objects.filter(is_active=True).count()

    pending_url = reverse('admin:bookings_booking_changelist') + '?status__exact=pending'
    confirmed_url = reverse('admin:bookings_booking_changelist') + '?status__exact=confirmed'
    cancelled_url = reverse('admin:bookings_booking_changelist') + '?status__exact=cancelled'
    checkins_url = (
        reverse('admin:bookings_booking_changelist')
        + f'?check_in__exact={today.isoformat()}'
    )
    checkouts_url = (
        reverse('admin:bookings_booking_changelist')
        + f'?check_out__exact={today.isoformat()}'
    )
    rooms_url = reverse('admin:hotels_room_changelist')

    recent_bookings = (
        Booking.objects.select_related('user', 'room', 'room__room_type')
        .order_by('-created_at')[:8]
    )
    arrivals_today = live_bookings.filter(check_in=today).select_related(
        'user', 'room'
    )
    departures_today = live_bookings.filter(check_out=today).select_related(
        'user', 'room'
    )

    confirmed_revenue = (
        Booking.objects.filter(status=Booking.Status.CONFIRMED).aggregate(
            total=Sum('total_price')
        )['total']
        or 0
    )

    return {
        'dashboard': {
            'cards': [
                {
                    'label': 'Active rooms',
                    'value': rooms_active,
                    'url': rooms_url,
                    'hint': f'{Room.objects.count()} total',
                },
                {
                    'label': 'Occupied today',
                    'value': occupied_today,
                    'url': rooms_url,
                    'hint': f'{max(rooms_active - occupied_today, 0)} free',
                },
                {
                    'label': 'Pending bookings',
                    'value': Booking.objects.filter(status=Booking.Status.PENDING).count(),
                    'url': pending_url,
                    'hint': 'Need review',
                },
                {
                    'label': 'Confirmed bookings',
                    'value': Booking.objects.filter(status=Booking.Status.CONFIRMED).count(),
                    'url': confirmed_url,
                    'hint': f'Revenue ${confirmed_revenue}',
                },
                {
                    'label': 'Check-ins today',
                    'value': live_bookings.filter(check_in=today).count(),
                    'url': checkins_url,
                    'hint': today.strftime('%b %d, %Y'),
                },
                {
                    'label': 'Check-outs today',
                    'value': live_bookings.filter(check_out=today).count(),
                    'url': checkouts_url,
                    'hint': today.strftime('%b %d, %Y'),
                },
                {
                    'label': 'Cancelled',
                    'value': Booking.objects.filter(status=Booking.Status.CANCELLED).count(),
                    'url': cancelled_url,
                    'hint': 'All time',
                },
            ],
            'recent_bookings': recent_bookings,
            'arrivals_today': arrivals_today,
            'departures_today': departures_today,
            'today': today,
        }
    }


_original_index = admin.site.index


def _dashboard_index(request, extra_context=None):
    extra_context = extra_context or {}
    extra_context.update(dashboard_context())
    return _original_index(request, extra_context)


admin.site.index = _dashboard_index
