from django.db import models


class RoomType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class RoomQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def available_between(self, check_in, check_out):
        """Return active rooms with no overlapping non-cancelled bookings."""
        from bookings.models import Booking

        overlapping_room_ids = Booking.objects.filter(
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).values_list('room_id', flat=True)

        return self.active().exclude(pk__in=overlapping_room_ids)


class Room(models.Model):
    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.PROTECT,
        related_name='rooms',
    )
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='rooms/', blank=True)
    is_active = models.BooleanField(default=True)

    objects = RoomQuerySet.as_manager()

    class Meta:
        ordering = ['room_number']

    def __str__(self):
        return f'Room {self.room_number} ({self.room_type.name})'

    def is_available(self, check_in, check_out, exclude_booking=None):
        """Check whether this room is free for the given date range."""
        from bookings.models import Booking

        if check_out <= check_in:
            return False

        qs = Booking.objects.filter(
            room=self,
            status__in=[Booking.Status.PENDING, Booking.Status.CONFIRMED],
            check_in__lt=check_out,
            check_out__gt=check_in,
        )
        if exclude_booking is not None:
            qs = qs.exclude(pk=exclude_booking.pk)
        return not qs.exists()

    @property
    def primary_image(self):
        if self.image:
            return self.image
        first_extra = self.images.first()
        return first_extra.image if first_extra else None


class RoomImage(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to='rooms/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'pk']

    def __str__(self):
        return f'Image for {self.room}'
