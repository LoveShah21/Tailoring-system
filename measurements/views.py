"""
Measurements App - Views

Measurement management views.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone

from .models import MeasurementTemplate, MeasurementSet, MeasurementValue
from .forms import MeasurementSetForm, MeasurementValueFormSet
from users.permissions import StaffRequiredMixin
from customers.models import CustomerProfile
from catalog.models import GarmentType


class MeasurementTemplateListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all measurement templates."""
    
    model = MeasurementTemplate
    template_name = 'measurements/template_list.html'
    context_object_name = 'templates'
    
    def get_queryset(self):
        return MeasurementTemplate.objects.select_related('garment_type').order_by('garment_type__name', 'display_order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['garment_types'] = GarmentType.objects.filter(is_deleted=False, is_active=True)
        return context


class MeasurementSetListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List measurement sets for a customer."""
    
    model = MeasurementSet
    template_name = 'measurements/set_list.html'
    context_object_name = 'measurement_sets'
    
    def get_queryset(self):
        customer_id = self.request.GET.get('customer')
        queryset = MeasurementSet.objects.filter(is_deleted=False).select_related(
            'customer__user', 'garment_type'
        ).order_by('-created_at')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        return queryset[:50]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = CustomerProfile.objects.select_related('user').filter(is_deleted=False)[:100]
        context['selected_customer'] = self.request.GET.get('customer', '')
        return context


class MeasurementSetDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View measurement set details."""
    
    model = MeasurementSet
    template_name = 'measurements/set_detail.html'
    context_object_name = 'measurement_set'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['values'] = self.object.measurement_values.select_related('template').order_by('template__display_order')
        return context


class MeasurementSetCreateView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Create a new measurement set."""
    
    template_name = 'measurements/set_form.html'
    
    def get(self, request):
        customer_id = request.GET.get('customer')
        garment_type_id = request.GET.get('garment_type')
        
        context = {
            'customers': CustomerProfile.objects.select_related('user').filter(is_deleted=False)[:100],
            'garment_types': GarmentType.objects.filter(is_deleted=False, is_active=True),
            'selected_customer': customer_id,
            'selected_garment': garment_type_id,
            'title': 'Record Measurements',
        }
        
        if customer_id and garment_type_id:
            try:
                garment_type = GarmentType.objects.get(pk=garment_type_id)
                templates = MeasurementTemplate.objects.filter(
                    garment_type=garment_type
                ).order_by('display_order')
                context['templates'] = templates
                context['garment_type'] = garment_type
                context['customer'] = CustomerProfile.objects.get(pk=customer_id)
            except (GarmentType.DoesNotExist, CustomerProfile.DoesNotExist):
                pass
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        customer_id = request.POST.get('customer')
        garment_type_id = request.POST.get('garment_type')
        notes = request.POST.get('notes', '')
        
        try:
            customer = CustomerProfile.objects.get(pk=customer_id)
            garment_type = GarmentType.objects.get(pk=garment_type_id)
        except (CustomerProfile.DoesNotExist, GarmentType.DoesNotExist):
            messages.error(request, 'Invalid customer or garment type.')
            return redirect('measurements:set_create')
        
        # Create measurement set
        measurement_set = MeasurementSet.objects.create(
            customer=customer,
            garment_type=garment_type,
            measurement_date=timezone.now().date(),
            taken_by=request.user,
            notes=notes,
        )
        
        # Save measurement values
        templates = MeasurementTemplate.objects.filter(garment_type=garment_type)
        for template in templates:
            value = request.POST.get(f'measurement_{template.id}', '')
            if value:
                try:
                    MeasurementValue.objects.create(
                        measurement_set=measurement_set,
                        template=template,
                        value=float(value),
                    )
                except ValueError:
                    pass
        
        messages.success(request, f'Measurements recorded for {customer.user.get_full_name()}.')
        return redirect('measurements:set_detail', pk=measurement_set.pk)


class MeasurementSetEditView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Edit a measurement set."""
    
    template_name = 'measurements/set_edit.html'
    
    def get(self, request, pk):
        measurement_set = get_object_or_404(MeasurementSet, pk=pk)
        templates = MeasurementTemplate.objects.filter(
            garment_type=measurement_set.garment_type
        ).order_by('display_order')
        
        # Get existing values
        existing_values = {v.template_id: v.value for v in measurement_set.measurement_values.all()}
        
        context = {
            'measurement_set': measurement_set,
            'templates': templates,
            'existing_values': existing_values,
            'title': f'Edit Measurements - {measurement_set.customer.user.get_full_name()}',
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        measurement_set = get_object_or_404(MeasurementSet, pk=pk)
        templates = MeasurementTemplate.objects.filter(
            garment_type=measurement_set.garment_type
        )
        
        # Update measurement values
        for template in templates:
            value = request.POST.get(f'measurement_{template.id}', '')
            if value:
                try:
                    MeasurementValue.objects.update_or_create(
                        measurement_set=measurement_set,
                        template=template,
                        defaults={'value': float(value)}
                    )
                except ValueError:
                    pass
        
        messages.success(request, 'Measurements updated.')
        return redirect('measurements:set_detail', pk=pk)


# AJAX API for getting templates
class TemplatesAPIView(LoginRequiredMixin, View):
    """API to get measurement templates for a garment type."""
    
    def get(self, request, garment_type_id):
        templates = MeasurementTemplate.objects.filter(
            garment_type_id=garment_type_id
        ).order_by('display_order').values('id', 'measurement_field_name', 'display_label', 'unit', 'is_required')
        
        return JsonResponse({'templates': list(templates)})
