"""
Audit App - Views

Audit trail views for admin.
"""

from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

from .models import ActivityLog, PaymentAuditLog
from users.permissions import AdminRequiredMixin


class ActivityLogListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List all activity logs."""
    
    model = ActivityLog
    template_name = 'audit/activity_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = ActivityLog.objects.select_related('user').order_by('-created_at')
        
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(resource__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_action'] = self.request.GET.get('action', '')
        context['search'] = self.request.GET.get('search', '')
        return context


class PaymentAuditListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List payment audit logs."""
    
    model = PaymentAuditLog
    template_name = 'audit/payment_audit_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        return PaymentAuditLog.objects.select_related(
            'payment__bill__order'
        ).order_by('-created_at')
