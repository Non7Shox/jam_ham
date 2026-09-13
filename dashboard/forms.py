from django import forms
from django.contrib.auth import get_user_model
from bookings.models import Booking
from hotels.models import Room, RoomType
from accounts.models import Profile

User = get_user_model()


class AdminBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['user', 'room', 'check_in', 'check_out', 'status', 'total_price']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'check_in': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'check_out': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Auto-calculated if blank'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['total_price'].required = False
        self.fields['room'].queryset = Room.objects.all().order_by('room_number')
        self.fields['user'].queryset = User.objects.all().order_by('username')


class AdminRoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'price_per_night', 'capacity', 'description', 'image', 'is_active']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 101'}),
            'room_type': forms.Select(attrs={'class': 'form-control'}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AdminRoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Executive Suite'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
        }


class AdminUserForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 555-0199'}),
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to keep unchanged'}),
        help_text='Leave blank to keep existing password when editing.',
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            profile, _ = Profile.objects.get_or_create(user=self.instance)
            self.fields['phone_number'].initial = profile.phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)

        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.save()

        return user
