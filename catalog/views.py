"""
Catalog App - Views

Catalog management views for admin.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import JsonResponse

from .models import GarmentType, WorkType, GarmentWorkType
from .forms import GarmentTypeForm, WorkTypeForm
from users.permissions import StaffRequiredMixin, AdminRequiredMixin


class GarmentTypeListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all garment types."""
    
    model = GarmentType
    template_name = 'catalog/garment_list.html'
    context_object_name = 'garments'
    
    def get_queryset(self):
        queryset = GarmentType.objects.filter(is_deleted=False).annotate(
            work_type_count=Count('garment_work_types', filter=Q(garment_work_types__is_supported=True))
        ).order_by('name')
        
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['total_garments'] = GarmentType.objects.filter(is_deleted=False).count()
        return context


class GarmentTypeDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View garment type details."""
    
    model = GarmentType
    template_name = 'catalog/garment_detail.html'
    context_object_name = 'garment'
    
    def get_queryset(self):
        return GarmentType.objects.filter(is_deleted=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['work_types'] = GarmentWorkType.objects.filter(
            garment_type=self.object,
            is_supported=True
        ).select_related('work_type')
        return context


class GarmentTypeCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Create a new garment type."""
    
    model = GarmentType
    form_class = GarmentTypeForm
    template_name = 'catalog/garment_form.html'
    success_url = reverse_lazy('catalog:garment_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Garment Type'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Garment type "{form.instance.name}" created.')
        return super().form_valid(form)


class GarmentTypeEditView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Edit a garment type."""
    
    model = GarmentType
    form_class = GarmentTypeForm
    template_name = 'catalog/garment_form.html'
    
    def get_queryset(self):
        return GarmentType.objects.filter(is_deleted=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.name}'
        context['edit_garment'] = self.object
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Garment type updated.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('catalog:garment_detail', kwargs={'pk': self.object.pk})


class WorkTypeListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all work types."""
    
    model = WorkType
    template_name = 'catalog/work_type_list.html'
    context_object_name = 'work_types'
    
    def get_queryset(self):
        return WorkType.objects.filter(is_deleted=False).order_by('name')


class WorkTypeCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Create a new work type."""
    
    model = WorkType
    form_class = WorkTypeForm
    template_name = 'catalog/work_type_form.html'
    success_url = reverse_lazy('catalog:work_type_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Work Type'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Work type "{form.instance.name}" created.')
        return super().form_valid(form)


class WorkTypeEditView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Edit a work type."""
    
    model = WorkType
    form_class = WorkTypeForm
    template_name = 'catalog/work_type_form.html'
    success_url = reverse_lazy('catalog:work_type_list')
    
    def get_queryset(self):
        return WorkType.objects.filter(is_deleted=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.name}'
        context['edit_work_type'] = self.object
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Work type updated.')
        return super().form_valid(form)


class GarmentWorkTypeMappingView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Toggle work type support for a garment type."""
    
    def post(self, request, garment_pk, work_type_pk):
        garment = get_object_or_404(GarmentType, pk=garment_pk, is_deleted=False)
        work_type = get_object_or_404(WorkType, pk=work_type_pk, is_deleted=False)
        
        mapping, created = GarmentWorkType.objects.get_or_create(
            garment_type=garment,
            work_type=work_type,
            defaults={'is_supported': True}
        )
        
        if not created:
            mapping.is_supported = not mapping.is_supported
            mapping.save()
        
        action = 'enabled' if mapping.is_supported else 'disabled'
        messages.success(request, f'{work_type.name} {action} for {garment.name}.')
        
        return redirect('catalog:garment_detail', pk=garment_pk)
