from datetime import date

from django import forms

from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('check_in', 'check_out')
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'check_out': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
        }

    def __init__(self, *args, room=None, user=None, **kwargs):
        self.room = room
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        today = date.today()

        if check_in and check_in < today:
            self.add_error('check_in', 'Check-in date cannot be in the past.')

        if check_in and check_out and check_out <= check_in:
            self.add_error('check_out', 'Check-out must be after check-in.')

        if self.room and check_in and check_out and not self.errors:
            if not self.room.is_available(check_in, check_out):
                raise forms.ValidationError(
                    'Sorry, this room is no longer available for those dates. '
                    'Please choose different dates or another room.'
                )

        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.user = self.user
        booking.room = self.room
        booking.status = Booking.Status.CONFIRMED
        booking.total_price = Booking.calculate_total_price(
            self.room,
            booking.check_in,
            booking.check_out,
        )
        if commit:
            booking.save()
        return booking
