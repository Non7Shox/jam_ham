import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, TemplateView, View

from bookings.models import Booking
from hotels.models import Room, RoomType
from accounts.models import Profile

from .forms import (
    AdminBookingForm,
    AdminRoomForm,
    AdminRoomTypeForm,
    AdminUserForm,
)
from .mixins import StaffRequiredMixin

User = get_user_model()


# ==========================================
# 1. OVERVIEW DASHBOARD VIEW
# ==========================================

class AdminDashboardView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        # Filtering parameters
        search_query = self.request.GET.get('q', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        room_type_filter = self.request.GET.get('room_type', '').strip()

        # Base Querysets
        active_statuses = [Booking.Status.PENDING, Booking.Status.CONFIRMED]
        live_bookings = Booking.objects.filter(status__in=active_statuses)
        all_bookings = Booking.objects.select_related('user', 'room', 'room__room_type')
        all_rooms = Room.objects.select_related('room_type').prefetch_related('images')

        # KPI Metrics Calculations
        total_rooms_count = Room.objects.count()
        active_rooms_count = Room.objects.filter(is_active=True).count()

        # Occupied rooms today
        occupied_room_ids = set(
            live_bookings.filter(check_in__lte=today, check_out__gt=today)
            .values_list('room_id', flat=True)
        )
        occupied_today_count = len(occupied_room_ids)
        available_today_count = max(active_rooms_count - occupied_today_count, 0)
        occupancy_rate = (
            round((occupied_today_count / active_rooms_count) * 100, 1)
            if active_rooms_count > 0
            else 0
        )

        # Pending room bookings today
        pending_room_ids = set(
            Booking.objects.filter(
                status=Booking.Status.PENDING, check_in__lte=today, check_out__gt=today
            ).values_list('room_id', flat=True)
        )

        # Revenue Metrics
        total_revenue = (
            Booking.objects.filter(status=Booking.Status.CONFIRMED).aggregate(
                total=Sum('total_price')
            )['total']
            or Decimal('0.00')
        )

        # Current Month Revenue
        start_of_month = today.replace(day=1)
        monthly_revenue = (
            Booking.objects.filter(
                status=Booking.Status.CONFIRMED,
                created_at__date__gte=start_of_month,
            ).aggregate(total=Sum('total_price'))['total']
            or Decimal('0.00')
        )

        # Today's Check-ins & Check-outs
        arrivals_today = live_bookings.filter(check_in=today).select_related(
            'user', 'room', 'room__room_type'
        )
        departures_today = live_bookings.filter(check_out=today).select_related(
            'user', 'room', 'room__room_type'
        )

        # Status counts
        pending_count = Booking.objects.filter(status=Booking.Status.PENDING).count()
        confirmed_count = Booking.objects.filter(status=Booking.Status.CONFIRMED).count()
        cancelled_count = Booking.objects.filter(status=Booking.Status.CANCELLED).count()

        # Filtered Recent Bookings Table
        filtered_bookings = all_bookings
        if search_query:
            filtered_bookings = filtered_bookings.filter(
                Q(user__username__icontains=search_query)
                | Q(user__first_name__icontains=search_query)
                | Q(user__last_name__icontains=search_query)
                | Q(user__email__icontains=search_query)
                | Q(room__room_number__icontains=search_query)
                | Q(id__icontains=search_query)
            )
        if status_filter in [
            Booking.Status.PENDING,
            Booking.Status.CONFIRMED,
            Booking.Status.CANCELLED,
        ]:
            filtered_bookings = filtered_bookings.filter(status=status_filter)
        if room_type_filter:
            filtered_bookings = filtered_bookings.filter(
                room__room_type_id=room_type_filter
            )

        recent_bookings = filtered_bookings.order_by('-created_at')[:15]

        # Room Status Cards Grid setup
        room_list = []
        for room in all_rooms:
            if not room.is_active:
                current_status = 'inactive'
                status_label = 'Maintenance'
                status_class = 'status-inactive'
            elif room.id in occupied_room_ids:
                current_status = 'occupied'
                status_label = 'Occupied'
                status_class = 'status-occupied'
            elif room.id in pending_room_ids:
                current_status = 'pending'
                status_label = 'Reserved (Pending)'
                status_class = 'status-pending'
            else:
                current_status = 'available'
                status_label = 'Available'
                status_class = 'status-available'

            active_booking = (
                live_bookings.filter(
                    room=room, check_in__lte=today, check_out__gt=today
                )
                .select_related('user')
                .first()
            )

            room_list.append(
                {
                    'object': room,
                    'status': current_status,
                    'status_label': status_label,
                    'status_class': status_class,
                    'active_booking': active_booking,
                }
            )

        # Monthly Revenue Trend Data for Chart.js (Last 6 months)
        months_labels = []
        months_revenue = []
        for i in range(5, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=i * 30)
            month_start = month_date.replace(day=1)
            if month_start.month == 12:
                next_month = month_start.replace(year=month_start.year + 1, month=1)
            else:
                next_month = month_start.replace(month=month_start.month + 1)

            month_name = month_start.strftime('%b %Y')
            rev = (
                Booking.objects.filter(
                    status=Booking.Status.CONFIRMED,
                    created_at__date__gte=month_start,
                    created_at__date__lt=next_month,
                ).aggregate(total=Sum('total_price'))['total']
                or Decimal('0.00')
            )
            months_labels.append(month_name)
            months_revenue.append(float(rev))

        # Room Type Breakdown for Pie Chart
        room_types = RoomType.objects.annotate(
            room_count=Count('rooms', filter=Q(rooms__is_active=True))
        )
        type_labels = [rt.name for rt in room_types]
        type_counts = [rt.room_count for rt in room_types]

        context.update(
            {
                'today': today,
                'search_query': search_query,
                'status_filter': status_filter,
                'room_type_filter': room_type_filter,
                'total_revenue': total_revenue,
                'monthly_revenue': monthly_revenue,
                'occupancy_rate': occupancy_rate,
                'total_rooms_count': total_rooms_count,
                'active_rooms_count': active_rooms_count,
                'occupied_today_count': occupied_today_count,
                'available_today_count': available_today_count,
                'checkins_today_count': arrivals_today.count(),
                'checkouts_today_count': departures_today.count(),
                'pending_count': pending_count,
                'confirmed_count': confirmed_count,
                'cancelled_count': cancelled_count,
                'total_bookings_count': Booking.objects.count(),
                'arrivals_today': arrivals_today,
                'departures_today': departures_today,
                'recent_bookings': recent_bookings,
                'rooms': room_list,
                'room_types': RoomType.objects.all(),
                'all_users': User.objects.filter(is_active=True).order_by('username'),
                'active_rooms_qs': Room.objects.filter(is_active=True).order_by(
                    'room_number'
                ),
                'booking_form': AdminBookingForm(),
                'chart_labels': json.dumps(months_labels),
                'chart_revenue': json.dumps(months_revenue),
                'pie_labels': json.dumps(type_labels),
                'pie_counts': json.dumps(type_counts),
            }
        )

        return context


# ==========================================
# 2. BOOKINGS CRUD VIEWS
# ==========================================

class AdminBookingListView(StaffRequiredMixin, ListView):
    model = Booking
    template_name = 'dashboard/bookings_list.html'
    context_object_name = 'bookings'
    paginate_by = 20

    def get_queryset(self):
        qs = Booking.objects.select_related('user', 'room', 'room__room_type').order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        room_type = self.request.GET.get('room_type', '').strip()

        if q:
            qs = qs.filter(
                Q(user__username__icontains=q)
                | Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
                | Q(user__email__icontains=q)
                | Q(room__room_number__icontains=q)
                | Q(id__icontains=q)
            )
        if status in [Booking.Status.PENDING, Booking.Status.CONFIRMED, Booking.Status.CANCELLED]:
            qs = qs.filter(status=status)
        if room_type:
            qs = qs.filter(room__room_type_id=room_type)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'search_query': self.request.GET.get('q', ''),
                'status_filter': self.request.GET.get('status', ''),
                'room_type_filter': self.request.GET.get('room_type', ''),
                'room_types': RoomType.objects.all(),
                'booking_form': AdminBookingForm(),
                'total_count': Booking.objects.count(),
                'pending_count': Booking.objects.filter(status=Booking.Status.PENDING).count(),
                'confirmed_count': Booking.objects.filter(status=Booking.Status.CONFIRMED).count(),
                'cancelled_count': Booking.objects.filter(status=Booking.Status.CANCELLED).count(),
            }
        )
        return context


class AdminBookingCreateView(StaffRequiredMixin, View):
    def post(self, request):
        form = AdminBookingForm(request.POST)
        if form.is_valid():
            try:
                booking = form.save()
                messages.success(request, f'Successfully created Booking #{booking.pk}.')
            except Exception as e:
                messages.error(request, f'Could not create booking: {e}')
        else:
            messages.error(request, f'Form validation errors: {form.errors}')

        redirect_to = request.POST.get('next') or 'dashboard:bookings_list'
        return redirect(redirect_to)


class AdminBookingUpdateView(StaffRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        form = AdminBookingForm(request.POST, instance=booking)
        if form.is_valid():
            try:
                booking = form.save()
                messages.success(request, f'Successfully updated Booking #{booking.pk}.')
            except Exception as e:
                messages.error(request, f'Error updating booking: {e}')
        else:
            messages.error(request, f'Form validation errors: {form.errors}')

        redirect_to = request.POST.get('next') or 'dashboard:bookings_list'
        return redirect(redirect_to)


class AdminBookingDeleteView(StaffRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        booking_id = booking.pk
        booking.delete()
        messages.success(request, f'Booking #{booking_id} has been permanently deleted.')
        redirect_to = request.POST.get('next') or 'dashboard:bookings_list'
        return redirect(redirect_to)


class UpdateBookingStatusView(StaffRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)
        new_status = request.POST.get('status')
        if new_status in [
            Booking.Status.PENDING,
            Booking.Status.CONFIRMED,
            Booking.Status.CANCELLED,
        ]:
            booking.status = new_status
            try:
                booking.save(update_fields=['status'])
                messages.success(
                    request,
                    f'Booking #{booking.pk} status updated to "{booking.get_status_display()}".',
                )
            except Exception as e:
                messages.error(request, f'Failed to update booking status: {e}')
        else:
            messages.error(request, 'Invalid status requested.')

        redirect_to = request.POST.get('next') or 'dashboard:index'
        return redirect(redirect_to)


# ==========================================
# 3. ROOMS & SUITES CRUD VIEWS
# ==========================================

class AdminRoomListView(StaffRequiredMixin, ListView):
    model = Room
    template_name = 'dashboard/rooms_list.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        qs = Room.objects.select_related('room_type').prefetch_related('images').order_by('room_number')
        q = self.request.GET.get('q', '').strip()
        room_type = self.request.GET.get('room_type', '').strip()

        if q:
            qs = qs.filter(Q(room_number__icontains=q) | Q(description__icontains=q))
        if room_type:
            qs = qs.filter(room_type_id=room_type)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'search_query': self.request.GET.get('q', ''),
                'room_type_filter': self.request.GET.get('room_type', ''),
                'room_types': RoomType.objects.all(),
                'room_form': AdminRoomForm(),
                'room_type_form': AdminRoomTypeForm(),
                'total_rooms_count': Room.objects.count(),
                'active_rooms_count': Room.objects.filter(is_active=True).count(),
                'inactive_rooms_count': Room.objects.filter(is_active=False).count(),
            }
        )
        return context


class AdminRoomCreateView(StaffRequiredMixin, View):
    def post(self, request):
        form = AdminRoomForm(request.POST, request.FILES)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'Room {room.room_number} created successfully!')
        else:
            messages.error(request, f'Form validation errors: {form.errors}')

        return redirect('dashboard:rooms_list')


class AdminRoomUpdateView(StaffRequiredMixin, View):
    def post(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        form = AdminRoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'Room {room.room_number} updated successfully!')
        else:
            messages.error(request, f'Form validation errors: {form.errors}')

        return redirect('dashboard:rooms_list')


class AdminRoomDeleteView(StaffRequiredMixin, View):
    def post(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        room_number = room.room_number
        try:
            room.delete()
            messages.success(request, f'Room {room_number} deleted successfully.')
        except Exception as e:
            messages.error(
                request,
                f'Cannot delete Room {room_number} because existing bookings reference it: {e}',
            )

        return redirect('dashboard:rooms_list')


class AdminRoomTypeCreateView(StaffRequiredMixin, View):
    def post(self, request):
        form = AdminRoomTypeForm(request.POST)
        if form.is_valid():
            rt = form.save()
            messages.success(request, f'Room Category "{rt.name}" created!')
        else:
            messages.error(request, f'Form validation errors: {form.errors}')

        return redirect('dashboard:rooms_list')


class ToggleRoomStatusView(StaffRequiredMixin, View):
    def post(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        room.is_active = not room.is_active
        room.save(update_fields=['is_active'])
        status_name = 'Active' if room.is_active else 'In Maintenance'
        messages.success(
            request, f'Room {room.room_number} status set to {status_name}.'
        )
        redirect_to = request.POST.get('next') or 'dashboard:rooms_list'
        return redirect(redirect_to)


# ==========================================
# 4. GUESTS & USERS CRUD VIEWS
# ==========================================

class AdminUserListView(StaffRequiredMixin, ListView):
    model = User
    template_name = 'dashboard/users_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        qs = User.objects.select_related('profile').annotate(
            booking_count=Count('bookings')
        ).order_by('-date_joined')

        q = self.request.GET.get('q', '').strip()
        role = self.request.GET.get('role', '').strip()

        if q:
            qs = qs.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(profile__phone_number__icontains=q)
            )
        if role == 'staff':
            qs = qs.filter(is_staff=True)
        elif role == 'guest':
            qs = qs.filter(is_staff=False)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                'search_query': self.request.GET.get('q', ''),
                'role_filter': self.request.GET.get('role', ''),
                'user_form': AdminUserForm(),
                'total_users_count': User.objects.count(),
                'staff_users_count': User.objects.filter(is_staff=True).count(),
                'guest_users_count': User.objects.filter(is_staff=False).count(),
            }
        )
        return context


class AdminUserCreateView(StaffRequiredMixin, View):
    def post(self, request):
        form = AdminUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User account "{user.username}" created successfully!')
        else:
            messages.error(request, f'Form validation errors: {form.errors}')

        return redirect('dashboard:users_list')


class AdminUserUpdateView(StaffRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = AdminUserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User account "{user.username}" updated successfully!')
        else:
            messages.error(request, f'Form validation errors: {form.errors}')

        return redirect('dashboard:users_list')


class AdminUserDeleteView(StaffRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, 'You cannot delete your own active admin session account!')
            return redirect('dashboard:users_list')

        username = user.username
        user.delete()
        messages.success(request, f'User account "{username}" has been deleted.')
        return redirect('dashboard:users_list')


class QuickBookingView(StaffRequiredMixin, View):
    def post(self, request):
        user_id = request.POST.get('user_id')
        room_id = request.POST.get('room_id')
        check_in_str = request.POST.get('check_in')
        check_out_str = request.POST.get('check_out')
        status = request.POST.get('status', Booking.Status.CONFIRMED)

        try:
            user = get_object_or_404(User, pk=user_id)
            room = get_object_or_404(Room, pk=room_id)
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()

            booking = Booking(
                user=user,
                room=room,
                check_in=check_in,
                check_out=check_out,
                status=status,
            )
            booking.save()

            messages.success(
                request,
                f'Successfully created Booking #{booking.pk} for {user.username} (Room {room.room_number}).',
            )
        except Exception as e:
            messages.error(request, f'Error creating booking: {e}')

        return redirect('dashboard:index')
