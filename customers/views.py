"""
Customers App - Views

Customer management views for admin panel.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count
from django.shortcuts import redirect
from django.urls import reverse_lazy

from .models import CustomerProfile
from .forms import CustomerProfileForm
from users.permissions import AdminRequiredMixin, StaffRequiredMixin


class CustomerListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """Admin: List all customers with search."""
    
    model = CustomerProfile
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CustomerProfile.objects.select_related('user').annotate(
            order_count=Count('orders')
        ).order_by('-user__date_joined')
        
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(phone_number__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['total_customers'] = CustomerProfile.objects.count()
        return context


class CustomerDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """Admin: View customer details."""
    
    model = CustomerProfile
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object
        context['orders'] = customer.orders.select_related(
            'current_status', 'garment_type'
        ).order_by('-created_at')[:10]
        return context


class CustomerCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Admin: Create new customer."""
    
    model = CustomerProfile
    form_class = CustomerProfileForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:customer_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Customer'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Customer created successfully.')
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Admin: Edit customer."""
    
    model = CustomerProfile
    form_class = CustomerProfileForm
    template_name = 'customers/customer_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Customer'
        context['edit_customer'] = self.object
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Customer updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('customers:customer_detail', kwargs={'pk': self.object.pk})
