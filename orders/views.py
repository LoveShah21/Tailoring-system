"""
Orders App - Views

Order management views for admin and staff.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse

from .models import Order, OrderStatus, OrderStatusTransition, OrderStatusHistory
from .forms import (
    OrderCreateForm, OrderEditForm, OrderStatusTransitionForm, 
    OrderAssignmentForm, OrderMaterialAllocationForm
)
from .services import OrderService, InvalidTransitionError
from users.permissions import StaffRequiredMixin


class OrderListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all orders with filters."""
    
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Order.objects.filter(is_deleted=False).select_related(
            'customer__user', 'garment_type', 'current_status'
        ).order_by('-created_at')
        
        # Search
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(customer__user__first_name__icontains=search) |
                Q(customer__user__last_name__icontains=search) |
                Q(customer__phone_number__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(current_status__status_name=status)
        
        # Urgency filter
        urgent = self.request.GET.get('urgent')
        if urgent == '1':
            queryset = queryset.filter(is_urgent=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_urgent'] = self.request.GET.get('urgent', '')
        context['statuses'] = OrderStatus.objects.all().order_by('sequence_order')
        context['total_orders'] = Order.objects.filter(is_deleted=False).count()
        context['pending_orders'] = Order.objects.filter(
            is_deleted=False,
            current_status__is_final_state=False
        ).count()
        return context


class OrderDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View order details."""
    
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(is_deleted=False).select_related(
            'customer__user', 'garment_type', 'current_status',
            'measurement_set', 'design'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        
        # Get valid transitions
        valid_transitions = OrderStatusTransition.objects.filter(
            from_status=order.current_status
        ).select_related('to_status')
        context['valid_transitions'] = valid_transitions
        
        # Status history
        context['status_history'] = order.status_history.select_related(
            'from_status', 'to_status', 'changed_by'
        ).order_by('-changed_at')
        
        # Assignments
        context['assignments'] = order.assignments.select_related('staff', 'assigned_by')
        
        # Work types
        context['work_types'] = order.order_work_types.select_related('work_type')
        
        # Material allocations
        context['allocations'] = order.material_allocations.select_related('fabric', 'allocated_by')
        
        # Forms
        context['transition_form'] = OrderStatusTransitionForm(order)
        context['assignment_form'] = OrderAssignmentForm()
        context['allocation_form'] = OrderMaterialAllocationForm()
        
        return context


class OrderCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Create a new order."""
    
    model = Order
    form_class = OrderCreateForm
    template_name = 'orders/order_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Order'
        return context
    
    def form_valid(self, form):
        # Use service to create order
        order = OrderService.create_order(
            customer=form.cleaned_data['customer'],
            garment_type=form.cleaned_data['garment_type'],
            expected_delivery_date=form.cleaned_data['expected_delivery_date'],
            measurement_set=form.cleaned_data.get('measurement_set'),
            work_types=form.cleaned_data.get('work_types', []),
            is_urgent=form.cleaned_data.get('is_urgent', False),
            special_instructions=form.cleaned_data.get('special_instructions', ''),
            created_by=self.request.user,
            request=self.request
        )
        
        messages.success(self.request, f'Order {order.order_number} created successfully.')
        return redirect('orders:order_detail', pk=order.pk)


class OrderEditView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Edit an existing order."""
    
    model = Order
    form_class = OrderEditForm
    template_name = 'orders/order_form.html'
    
    def get_queryset(self):
        return Order.objects.filter(is_deleted=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Order {self.object.order_number}'
        context['edit_order'] = self.object
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Order updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('orders:order_detail', kwargs={'pk': self.object.pk})


class OrderTransitionView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Handle order status transitions."""
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, is_deleted=False)
        
        new_status_id = request.POST.get('new_status')
        reason = request.POST.get('reason', '')
        
        try:
            new_status = OrderStatus.objects.get(pk=new_status_id)
            OrderService.transition_status(
                order=order,
                new_status=new_status,
                changed_by=request.user,
                reason=reason,
                request=request
            )
            messages.success(
                request, 
                f'Order status changed to "{new_status.display_label}".'
            )
        except OrderStatus.DoesNotExist:
            messages.error(request, 'Invalid status selected.')
        except InvalidTransitionError as e:
            messages.error(request, str(e))
        
        return redirect('orders:order_detail', pk=pk)


class OrderAssignView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Handle staff assignment to order."""
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, is_deleted=False)
        form = OrderAssignmentForm(request.POST)
        
        if form.is_valid():
            OrderService.assign_staff(
                order=order,
                staff=form.cleaned_data['staff'],
                role_type=form.cleaned_data['role_type'],
                assigned_by=request.user,
                notes=form.cleaned_data.get('notes', '')
            )
            messages.success(
                request, 
                f'{form.cleaned_data["staff"].get_full_name()} assigned as {form.cleaned_data["role_type"]}.'
            )
        else:
            messages.error(request, 'Invalid assignment data.')
        
        return redirect('orders:order_detail', pk=pk)


class OrderAllocateMaterialView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Handle material allocation."""
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, is_deleted=False)
        form = OrderMaterialAllocationForm(request.POST)
        
        if form.is_valid():
            try:
                from django.core.exceptions import ValidationError
                OrderService.allocate_material(
                    order=order,
                    fabric=form.cleaned_data['fabric'],
                    quantity_meters=form.cleaned_data['quantity'],
                    allocated_by=request.user,
                    request=request
                )
                messages.success(request, 'Material allocated successfully.')
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Invalid allocation data.')
            
        return redirect('orders:order_detail', pk=pk)


class OrderDeleteView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Soft delete an order."""
    
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        order.is_deleted = True
        order.save(update_fields=['is_deleted', 'updated_at'])
        messages.success(request, f'Order {order.order_number} deleted.')
        return redirect('orders:order_list')


# API Views for AJAX
class OrderMeasurementsAPI(LoginRequiredMixin, View):
    """Get measurement sets for a customer (AJAX)."""
    
    def get(self, request, customer_id):
        from measurements.models import MeasurementSet
        
        measurements = MeasurementSet.objects.filter(
            customer_id=customer_id
        ).values('id', 'version', 'is_current')
        
        return JsonResponse({'measurements': list(measurements)})


class OrderWorkTypesAPI(LoginRequiredMixin, View):
    """Get work types for a garment type (AJAX)."""
    
    def get(self, request, garment_type_id):
        from catalog.models import GarmentWorkType
        
        work_types = GarmentWorkType.objects.filter(
            garment_type_id=garment_type_id,
            is_supported=True
        ).select_related('work_type').values(
            'work_type__id', 'work_type__name', 'work_type__extra_charge'
        )
        
        return JsonResponse({'work_types': list(work_types)})


class CustomerOrderDetailView(LoginRequiredMixin, DetailView):
    """
    View order details for a customer.
    Ensures user can only view their own orders.
    """
    model = Order
    template_name = 'orders/customer_order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        # Filter orders belonging to the logged-in user
        return Order.objects.filter(
            customer__user=self.request.user,
            is_deleted=False
        ).select_related(
            'customer__user', 'garment_type', 'current_status',
            'measurement_set', 'design', 'bill__invoice'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        
        # Add basic status history
        context['status_history'] = order.status_history.select_related(
            'from_status', 'to_status'
        ).order_by('-changed_at')
        
        # Add work types
        context['work_types'] = order.order_work_types.select_related('work_type')
        
        return context
