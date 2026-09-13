from django.views.generic import DetailView, ListView

from .forms import DateRangeSearchForm
from .models import Room


class HomeView(ListView):
    model = Room
    template_name = 'hotels/home.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        qs = Room.objects.active().select_related('room_type')
        self.search_form = DateRangeSearchForm(self.request.GET or None)

        if self.search_form.is_valid():
            check_in = self.search_form.cleaned_data['check_in']
            check_out = self.search_form.cleaned_data['check_out']
            guests = self.search_form.cleaned_data['guests']
            qs = qs.available_between(check_in, check_out).filter(capacity__gte=guests)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not hasattr(self, 'search_form'):
            self.search_form = DateRangeSearchForm(self.request.GET or None)
        context['search_form'] = self.search_form
        context['search_applied'] = (
            self.request.GET and self.search_form.is_valid()
        )
        return context


class RoomDetailView(DetailView):
    model = Room
    template_name = 'hotels/room_detail.html'
    context_object_name = 'room'

    def get_queryset(self):
        return Room.objects.active().select_related('room_type').prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = DateRangeSearchForm(self.request.GET or None)
        return context
