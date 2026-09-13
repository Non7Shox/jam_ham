from decimal import Decimal

from django.core.management.base import BaseCommand

from hotels.models import Room, RoomType


class Command(BaseCommand):
    help = 'Load sample room types and rooms for development.'

    def handle(self, *args, **options):
        types_data = [
            {
                'name': 'Standard',
                'description': 'Comfortable room with essential amenities.',
                'rooms': [
                    ('101', Decimal('89.00'), 2, 'Cozy standard room with city view.'),
                    ('102', Decimal('89.00'), 2, 'Standard room with queen bed and workspace.'),
                ],
            },
            {
                'name': 'Deluxe',
                'description': 'Spacious room with premium furnishings.',
                'rooms': [
                    ('201', Decimal('129.00'), 3, 'Deluxe king room with lounge area.'),
                    ('202', Decimal('135.00'), 3, 'Deluxe room with balcony and mini bar.'),
                ],
            },
            {
                'name': 'Suite',
                'description': 'Luxury suite with separate living area.',
                'rooms': [
                    ('301', Decimal('199.00'), 4, 'Executive suite with panoramic views.'),
                    ('302', Decimal('219.00'), 4, 'Presidential suite with jacuzzi tub.'),
                ],
            },
        ]

        created_rooms = 0
        for type_data in types_data:
            room_type, _ = RoomType.objects.get_or_create(
                name=type_data['name'],
                defaults={'description': type_data['description']},
            )
            for number, price, capacity, description in type_data['rooms']:
                _, created = Room.objects.get_or_create(
                    room_number=number,
                    defaults={
                        'room_type': room_type,
                        'price_per_night': price,
                        'capacity': capacity,
                        'description': description,
                        'is_active': True,
                    },
                )
                if created:
                    created_rooms += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Sample data ready. {created_rooms} new room(s) created.'
            )
        )
