"""
Configuration App - Views

System configuration views.
"""

from django.views.generic import ListView, UpdateView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy

from .models import SystemConfiguration, PricingRule
from .forms import SystemConfigurationForm, PricingRuleForm
from users.permissions import AdminRequiredMixin


class SystemConfigListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List all system configurations."""
    
    model = SystemConfiguration
    template_name = 'configuration/config_list.html'
    context_object_name = 'configs'
    
    def get_queryset(self):
        return SystemConfiguration.objects.order_by('category', 'key')


class SystemConfigUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Update a system configuration."""
    
    model = SystemConfiguration
    form_class = SystemConfigurationForm
    template_name = 'configuration/config_form.html'
    success_url = reverse_lazy('configuration:config_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Configuration updated.')
        return super().form_valid(form)


class PricingRuleListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List all pricing rules."""
    
    model = PricingRule
    template_name = 'configuration/pricing_list.html'
    context_object_name = 'rules'
    
    def get_queryset(self):
        return PricingRule.objects.filter(is_active=True).order_by('rule_name')


class PricingRuleCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Create a pricing rule."""
    
    model = PricingRule
    form_class = PricingRuleForm
    template_name = 'configuration/pricing_form.html'
    success_url = reverse_lazy('configuration:pricing_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Pricing Rule'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Pricing rule created.')
        return super().form_valid(form)


class PricingRuleUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Update a pricing rule."""
    
    model = PricingRule
    form_class = PricingRuleForm
    template_name = 'configuration/pricing_form.html'
    success_url = reverse_lazy('configuration:pricing_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.rule_name}'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Pricing rule updated.')
        return super().form_valid(form)
