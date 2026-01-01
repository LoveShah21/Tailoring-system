"""
Feedback App - Views

Customer feedback submission and moderation views.
"""

from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy

from .models import Feedback
from .forms import FeedbackForm
from users.permissions import StaffRequiredMixin
from orders.models import Order
from customers.models import CustomerProfile


class FeedbackListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all feedback."""
    
    model = Feedback
    template_name = 'feedback/feedback_list.html'
    context_object_name = 'feedbacks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Feedback.objects.select_related(
            'order__customer__user'
        ).order_by('-created_at')
        
        status = self.request.GET.get('status')
        if status == 'pending':
            queryset = queryset.filter(is_approved=False)
        elif status == 'approved':
            queryset = queryset.filter(is_approved=True)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_status'] = self.request.GET.get('status', '')
        context['pending_count'] = Feedback.objects.filter(is_approved=False, is_moderated=False).count()
        return context


class FeedbackDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """View feedback details."""
    
    model = Feedback
    template_name = 'feedback/feedback_detail.html'
    context_object_name = 'feedback'


class FeedbackCreateView(LoginRequiredMixin, CreateView):
    """Submit feedback for an order."""
    
    model = Feedback
    form_class = FeedbackForm
    template_name = 'feedback/feedback_form.html'
    success_url = reverse_lazy('customers:customer_dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.request.GET.get('order')
        if order_id:
            context['order'] = Order.objects.filter(
                pk=order_id,
                customer__user=self.request.user,
                current_status__status_name='delivered'
            ).first()
        return context
    
    def form_valid(self, form):
        order_id = self.request.POST.get('order')
        order = get_object_or_404(
            Order,
            pk=order_id,
            customer__user=self.request.user,
            current_status__status_name='delivered'
        )
        form.instance.order = order
        form.instance.customer = order.customer
        messages.success(self.request, 'Thank you for your feedback!')
        return super().form_valid(form)


class ApproveFeedbackView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Approve feedback for public display."""
    
    def post(self, request, pk):
        feedback = get_object_or_404(Feedback, pk=pk)
        feedback.is_approved = True
        feedback.is_moderated = True
        feedback.moderated_by = request.user
        feedback.save()
        messages.success(request, 'Feedback approved.')
        return redirect('feedback:feedback_list')


class RejectFeedbackView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Reject/hide feedback."""
    
    def post(self, request, pk):
        feedback = get_object_or_404(Feedback, pk=pk)
        feedback.is_approved = False
        feedback.is_moderated = True
        feedback.moderated_by = request.user
        feedback.save()
        messages.success(request, 'Feedback rejected.')
        return redirect('feedback:feedback_list')
