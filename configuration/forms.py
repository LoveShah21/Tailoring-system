"""
Configuration App - Forms

Forms for configuration management.
"""

from django import forms
from .models import SystemConfiguration, PricingRule


class SystemConfigurationForm(forms.ModelForm):
    """Form for editing system configurations."""
    
    class Meta:
        model = SystemConfiguration
        fields = ['value', 'description']
        widgets = {
            'value': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PricingRuleForm(forms.ModelForm):
    """Form for pricing rules."""
    
    class Meta:
        model = PricingRule
        fields = ['rule_name', 'rule_type', 'value', 'description', 'is_active']
        widgets = {
            'rule_name': forms.TextInput(attrs={'class': 'form-control'}),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
