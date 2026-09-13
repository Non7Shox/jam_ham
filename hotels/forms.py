from datetime import date

from django import forms


class DateRangeSearchForm(forms.Form):
    check_in = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Check-in',
    )
    check_out = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Check-out',
    )
    guests = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        label='Guests',
    )

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        today = date.today()

        if check_in and check_in < today:
            self.add_error('check_in', 'Check-in date cannot be in the past.')

        if check_in and check_out:
            if check_out <= check_in:
                self.add_error(
                    'check_out',
                    'Check-out must be after check-in.',
                )

        return cleaned_data
