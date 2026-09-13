from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'room',
        'check_in',
        'check_out',
        'status',
        'total_price',
        'created_at',
    )
    list_filter = ('status', 'check_in', 'check_out', 'created_at', 'room__room_type')
    search_fields = ('user__username', 'user__email', 'room__room_number')
    date_hierarchy = 'check_in'
    readonly_fields = ('created_at', 'total_price')
    raw_id_fields = ('user', 'room')
    list_editable = ('status',)
    actions = ('mark_confirmed', 'mark_cancelled')

    @admin.action(description='Mark selected bookings as confirmed')
    def mark_confirmed(self, request, queryset):
        updated = queryset.exclude(status=Booking.Status.CANCELLED).update(
            status=Booking.Status.CONFIRMED
        )
        self.message_user(request, f'{updated} booking(s) marked as confirmed.')

    @admin.action(description='Mark selected bookings as cancelled')
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status=Booking.Status.CANCELLED)
        self.message_user(request, f'{updated} booking(s) marked as cancelled.')
