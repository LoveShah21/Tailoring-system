"""
Inventory App - Views

Inventory management views for admin.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse

from .models import Fabric, StockTransaction, LowStockAlert
from .forms import FabricForm, StockInForm, StockOutForm
from .services import InventoryService
from users.permissions import StaffRequiredMixin


class FabricListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all fabrics in inventory."""
    
    model = Fabric
    template_name = 'inventory/fabric_list.html'
    context_object_name = 'fabrics'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Fabric.objects.filter(is_deleted=False).order_by('name')
        
        # Search
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(color__icontains=search) |
                Q(pattern__icontains=search)
            )
        
        # Low stock filter
        low_stock = self.request.GET.get('low_stock')
        if low_stock == '1':
            queryset = queryset.filter(quantity_in_stock__lte=F('reorder_threshold'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['low_stock_filter'] = self.request.GET.get('low_stock', '')
        context['total_fabrics'] = Fabric.objects.filter(is_deleted=False).count()
        context['low_stock_count'] = Fabric.objects.filter(
            is_deleted=False,
            quantity_in_stock__lte=F('reorder_threshold')
        ).count()
        context['total_value'] = InventoryService.get_stock_value()
        return context


class FabricDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View fabric details and transactions."""
    
    model = Fabric
    template_name = 'inventory/fabric_detail.html'
    context_object_name = 'fabric'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = self.object.transactions.select_related(
            'recorded_by', 'order'
        ).order_by('-transaction_date')[:20]
        context['stock_in_form'] = StockInForm()
        context['stock_out_form'] = StockOutForm()
        return context


class FabricCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Create a new fabric."""
    
    model = Fabric
    form_class = FabricForm
    template_name = 'inventory/fabric_form.html'
    success_url = reverse_lazy('inventory:fabric_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Fabric'
        return context
    
    def form_valid(self, form):
        fabric = InventoryService.create_fabric(
            name=form.cleaned_data['name'],
            color=form.cleaned_data.get('color', ''),
            pattern=form.cleaned_data.get('pattern', ''),
            quantity_in_stock=form.cleaned_data['quantity_in_stock'],
            cost_per_meter=form.cleaned_data['cost_per_meter'],
            reorder_threshold=form.cleaned_data['reorder_threshold'],
            created_by=self.request.user
        )
        messages.success(self.request, f'Fabric "{fabric.name}" added successfully.')
        return redirect(self.success_url)


class FabricEditView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Edit a fabric."""
    
    model = Fabric
    form_class = FabricForm
    template_name = 'inventory/fabric_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.name}'
        context['edit_fabric'] = self.object
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Check for low stock alert after update
        InventoryService._check_low_stock_alert(self.object)
        messages.success(self.request, 'Fabric updated successfully.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('inventory:fabric_detail', kwargs={'pk': self.object.pk})


class StockInView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Record stock in."""
    
    def post(self, request, pk):
        fabric = get_object_or_404(Fabric, pk=pk)
        form = StockInForm(request.POST)
        
        if form.is_valid():
            InventoryService.record_stock_in(
                fabric=fabric,
                quantity=form.cleaned_data['quantity'],
                recorded_by=request.user,
                notes=form.cleaned_data.get('notes', ''),
                request=request
            )
            messages.success(request, f'Added {form.cleaned_data["quantity"]}m to stock.')
        else:
            messages.error(request, 'Invalid quantity.')
        
        return redirect('inventory:fabric_detail', pk=pk)


class StockOutView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Record stock out (manual adjustment)."""
    
    def post(self, request, pk):
        fabric = get_object_or_404(Fabric, pk=pk)
        form = StockOutForm(request.POST)
        
        if form.is_valid():
            try:
                InventoryService.record_stock_out(
                    fabric=fabric,
                    quantity=form.cleaned_data['quantity'],
                    recorded_by=request.user,
                    notes=form.cleaned_data.get('notes', ''),
                    request=request
                )
                messages.success(request, f'Removed {form.cleaned_data["quantity"]}m from stock.')
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Invalid quantity.')
        
        return redirect('inventory:fabric_detail', pk=pk)


class LowStockAlertListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all unresolved low stock alerts."""
    
    model = LowStockAlert
    template_name = 'inventory/alert_list.html'
    context_object_name = 'alerts'
    
    def get_queryset(self):
        return LowStockAlert.objects.filter(
            is_resolved=False
        ).select_related('fabric').order_by('-alert_triggered_at')


class ResolveAlertView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Resolve a low stock alert."""
    
    def post(self, request, pk):
        alert = get_object_or_404(LowStockAlert, pk=pk)
        notes = request.POST.get('notes', '')
        
        InventoryService.resolve_alert(
            alert=alert,
            resolved_by=request.user,
            notes=notes
        )
        
        messages.success(request, f'Alert for "{alert.fabric.name}" resolved.')
        return redirect('inventory:alert_list')
