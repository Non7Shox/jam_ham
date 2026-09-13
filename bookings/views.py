from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, View

from hotels.models import Room

from .forms import BookingForm
from .models import Booking


class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_confirm.html'
    success_url = reverse_lazy('bookings:my_bookings')

    def dispatch(self, request, *args, **kwargs):
        self.room = get_object_or_404(Room.objects.active(), pk=kwargs['room_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['room'] = self.room
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        check_in = self.request.GET.get('check_in')
        check_out = self.request.GET.get('check_out')
        if check_in:
            initial['check_in'] = check_in
        if check_out:
            initial['check_out'] = check_out
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['room'] = self.room
        form = context.get('form') or self.get_form()
        if form.is_bound and form.is_valid():
            nights = (form.cleaned_data['check_out'] - form.cleaned_data['check_in']).days
            context['nights'] = nights
            context['total_price'] = Booking.calculate_total_price(
                self.room,
                form.cleaned_data['check_in'],
                form.cleaned_data['check_out'],
            )
        elif not form.is_bound:
            check_in = self.request.GET.get('check_in')
            check_out = self.request.GET.get('check_out')
            if check_in and check_out:
                from datetime import datetime

                try:
                    ci = datetime.strptime(check_in, '%Y-%m-%d').date()
                    co = datetime.strptime(check_out, '%Y-%m-%d').date()
                    if co > ci:
                        context['nights'] = (co - ci).days
                        context['total_price'] = Booking.calculate_total_price(
                            self.room, ci, co
                        )
                except ValueError:
                    pass
        return context

    def form_valid(self, form):
        if not self.room.is_available(form.cleaned_data['check_in'], form.cleaned_data['check_out']):
            form.add_error(
                None,
                'Sorry, this room became unavailable while you were booking. '
                'Please choose different dates or another room.',
            )
            return self.form_invalid(form)
        self.object = form.save()
        messages.success(self.request, 'Your booking has been confirmed!')
        return redirect('bookings:booking_success', pk=self.object.pk)

    def get_success_url(self):
        return reverse('bookings:booking_success', kwargs={'pk': self.object.pk})


class BookingSuccessView(LoginRequiredMixin, View):
    def get(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, user=request.user)
        from django.shortcuts import render

        return render(request, 'bookings/booking_success.html', {'booking': booking})


class MyBookingsView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/my_bookings.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return (
            Booking.objects.filter(user=self.request.user)
            .select_related('room', 'room__room_type')
            .order_by('-check_in')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        bookings = context['bookings']
        context['upcoming_bookings'] = [
            b for b in bookings
            if b.status != Booking.Status.CANCELLED and b.check_out >= today
        ]
        context['past_bookings'] = [
            b for b in bookings
            if b.status == Booking.Status.CANCELLED or b.check_out < today
        ]
        return context


class CancelBookingView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, user=request.user)
        today = timezone.localdate()

        if booking.status == Booking.Status.CANCELLED:
            messages.info(request, 'This booking is already cancelled.')
        elif booking.check_in < today:
            messages.error(request, 'Past bookings cannot be cancelled.')
        else:
            booking.status = Booking.Status.CANCELLED
            booking.save(update_fields=['status'])
            messages.success(request, 'Your booking has been cancelled.')

        return redirect('bookings:my_bookings')
