from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    room = models.ForeignKey(
        'hotels.Room',
        on_delete=models.PROTECT,
        related_name='bookings',
    )
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'Booking #{self.pk} — {self.room} '
            f'({self.check_in} to {self.check_out})'
        )

    @property
    def nights(self):
        return (self.check_out - self.check_in).days

    @classmethod
    def calculate_total_price(cls, room, check_in, check_out):
        nights = (check_out - check_in).days
        if nights <= 0:
            return Decimal('0.00')
        return room.price_per_night * nights

    def clean(self):
        today = timezone.localdate()

        if not self.pk and self.check_in and self.check_in < today:
            raise ValidationError({'check_in': 'Check-in date cannot be in the past.'})

        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValidationError({'check_out': 'Check-out must be after check-in.'})

        if self.status == self.Status.CANCELLED:
            return

        if self.room_id and self.check_in and self.check_out:
            if not self.room.is_available(
                self.check_in,
                self.check_out,
                exclude_booking=self if self.pk else None,
            ):
                raise ValidationError(
                    'This room is not available for the selected dates.'
                )

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.calculate_total_price(
                self.room,
                self.check_in,
                self.check_out,
            )
        self.full_clean()
        super().save(*args, **kwargs)
