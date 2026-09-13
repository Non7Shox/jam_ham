from django.contrib import admin

from .models import Room, RoomImage, RoomType


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_count')
    search_fields = ('name',)

    @admin.display(description='Rooms')
    def room_count(self, obj):
        return obj.rooms.count()


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'room_number',
        'room_type',
        'price_per_night',
        'capacity',
        'is_active',
    )
    list_filter = ('room_type', 'is_active', 'capacity')
    search_fields = ('room_number', 'description')
    inlines = [RoomImageInline]


@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ('room', 'caption', 'order')
    list_filter = ('room__room_type',)
