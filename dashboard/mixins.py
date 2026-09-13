from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'accounts:login'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(
                self.request,
                'You do not have access to the staff dashboard.',
            )
            return redirect('hotels:home')
        return super().handle_no_permission()
