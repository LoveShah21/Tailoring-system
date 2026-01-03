"""
Trials App - Views

Trial scheduling and tracking views.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from .models import Trial, Alteration, RevisedDeliveryDate
from .forms import TrialForm, AlterationForm
from users.permissions import StaffRequiredMixin
from orders.models import Order


class TrialListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all trials."""
    
    model = Trial
    template_name = 'trials/trial_list.html'
    context_object_name = 'trials'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Trial.objects.select_related(
            'order__customer__user', 'order__garment_type'
        ).order_by('-trial_date')
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(trial_status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_status'] = self.request.GET.get('status', '')
        context['pending_count'] = Trial.objects.filter(trial_status='SCHEDULED').count()
        return context


class TrialDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View trial details."""
    
    model = Trial
    template_name = 'trials/trial_detail.html'
    context_object_name = 'trial'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alterations'] = self.object.alterations.order_by('-created_at')
        context['alteration_form'] = AlterationForm()
        return context


class TrialCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Schedule a new trial."""
    
    model = Trial
    form_class = TrialForm
    template_name = 'trials/trial_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Schedule Trial'
        order_id = self.request.GET.get('order')
        if order_id:
            context['preselected_order'] = Order.objects.filter(pk=order_id).first()
        return context
    
    def form_valid(self, form):
        form.instance.scheduled_by = self.request.user
        response = super().form_valid(form)
        
        from notifications.services import NotificationService
        NotificationService.notify_trial_scheduled(self.object)
        
        messages.success(self.request, 'Trial scheduled successfully.')
        return response
    
    def get_success_url(self):
        return reverse_lazy('trials:trial_detail', kwargs={'pk': self.object.pk})


class TrialUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Update trial status."""
    
    model = Trial
    fields = ['trial_status', 'customer_feedback', 'fit_issues']
    template_name = 'trials/trial_update.html'
    
    def form_valid(self, form):
        if form.instance.trial_status == 'COMPLETED':
            form.instance.conducted_by = self.request.user
        messages.success(self.request, 'Trial updated.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('trials:trial_detail', kwargs={'pk': self.object.pk})


class AddAlterationView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Add alteration to a trial."""
    
    def post(self, request, trial_pk):
        trial = get_object_or_404(Trial, pk=trial_pk)
        form = AlterationForm(request.POST)
        
        if form.is_valid():
            alteration = form.save(commit=False)
            alteration.trial = trial
            alteration.save()
            messages.success(request, 'Alteration added.')
        else:
            messages.error(request, 'Invalid alteration data.')
        
        return redirect('trials:trial_detail', pk=trial_pk)


class MarkAlterationCompleteView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Mark alteration as complete."""
    
    def post(self, request, pk):
        alteration = get_object_or_404(Alteration, pk=pk)
        alteration.status = 'COMPLETED'
        alteration.completed_date = timezone.now().date()
        alteration.completed_by = request.user
        alteration.save()
        messages.success(request, 'Alteration marked as complete.')
        return redirect('trials:trial_detail', pk=alteration.trial.pk)
