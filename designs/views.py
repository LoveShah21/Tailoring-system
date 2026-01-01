"""
Designs App - Views

Design management views.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy

from .models import Design, CustomizationNote
from .forms import DesignForm, CustomizationNoteForm
from users.permissions import StaffRequiredMixin


class DesignListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all designs."""
    
    model = Design
    template_name = 'designs/design_list.html'
    context_object_name = 'designs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Design.objects.select_related('order__customer__user').order_by('-uploaded_at')
        
        status = self.request.GET.get('status')
        if status == 'approved':
            queryset = queryset.filter(is_approved=True)
        elif status == 'pending':
            queryset = queryset.filter(is_approved=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_status'] = self.request.GET.get('status', '')
        context['pending_count'] = Design.objects.filter(is_approved=False).count()
        return context


class DesignDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View design details."""
    
    model = Design
    template_name = 'designs/design_detail.html'
    context_object_name = 'design'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['design_notes'] = self.object.notes.select_related('noted_by').order_by('-added_at')
        context['note_form'] = CustomizationNoteForm()
        return context


class DesignCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Upload a new design."""
    
    model = Design
    form_class = DesignForm
    template_name = 'designs/design_form.html'
    success_url = reverse_lazy('designs:design_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Upload Design'
        return context
    
    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Design uploaded successfully.')
        return super().form_valid(form)


class DesignStatusUpdateView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Update design status (approve/reject)."""
    
    def post(self, request, pk):
        design = get_object_or_404(Design, pk=pk)
        action = request.POST.get('action')
        
        if action == 'approve':
            design.is_approved = True
            messages.success(request, 'Design approved.')
        elif action == 'reject':
            design.is_approved = False
            messages.success(request, 'Design rejected.')
        
        design.save()
        return redirect('designs:design_detail', pk=pk)


class AddCustomizationNoteView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Add customization note to a design."""
    
    def post(self, request, design_pk):
        design = get_object_or_404(Design, pk=design_pk)
        form = CustomizationNoteForm(request.POST)
        
        if form.is_valid():
            note = form.save(commit=False)
            note.design = design
            note.noted_by = request.user
            note.save()
            messages.success(request, 'Note added.')
        
        return redirect('designs:design_detail', pk=design_pk)
