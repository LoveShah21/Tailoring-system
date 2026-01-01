"""
Delivery App - Views

Delivery scheduling and tracking views.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone

from .models import Delivery, DeliveryZone
from .forms import DeliveryForm, DeliveryUpdateForm
from users.permissions import StaffRequiredMixin
from orders.models import Order


class DeliveryListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all deliveries."""
    
    model = Delivery
    template_name = 'delivery/delivery_list.html'
    context_object_name = 'deliveries'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Delivery.objects.select_related(
            'order__customer__user', 'delivery_zone', 'delivery_staff'
        ).order_by('-scheduled_delivery_date')
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(delivery_status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_status'] = self.request.GET.get('status', '')
        context['pending_count'] = Delivery.objects.filter(delivery_status='SCHEDULED').count()
        return context


class DeliveryDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View delivery details."""
    
    model = Delivery
    template_name = 'delivery/delivery_detail.html'
    context_object_name = 'delivery'


class DeliveryCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Schedule a new delivery."""
    
    model = Delivery
    form_class = DeliveryForm
    template_name = 'delivery/delivery_form.html'
    success_url = reverse_lazy('delivery:delivery_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Schedule Delivery'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Delivery scheduled.')
        return super().form_valid(form)


class DeliveryUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Update delivery status."""
    
    model = Delivery
    form_class = DeliveryUpdateForm
    template_name = 'delivery/delivery_update.html'
    
    def form_valid(self, form):
        if form.instance.delivery_status == 'DELIVERED':
            form.instance.delivery_confirmed_date = timezone.now()
            form.instance.delivery_confirmed_by = self.request.user
        messages.success(self.request, 'Delivery updated.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('delivery:delivery_detail', kwargs={'pk': self.object.pk})


class DeliveryZoneListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all delivery zones."""
    
    model = DeliveryZone
    template_name = 'delivery/zone_list.html'
    context_object_name = 'zones'
