"""
Trials App - Forms

Forms for trial management.
"""

from django import forms
from .models import Trial, Alteration
from orders.models import Order


class TrialForm(forms.ModelForm):
    """Form for scheduling trials."""
    
    class Meta:
        model = Trial
        fields = ['order', 'trial_date', 'trial_time', 'trial_location', 'customer_feedback']
        widgets = {
            'order': forms.Select(attrs={'class': 'form-select'}),
            'trial_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'trial_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'trial_location': forms.Select(attrs={'class': 'form-select'}),
            'customer_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show orders in trial-appropriate status
        self.fields['order'].queryset = Order.objects.filter(
            is_deleted=False,
            current_status__status_name__in=['stitching', 'trial_scheduled', 'alteration']
        ).select_related('customer__user', 'garment_type')


class AlterationForm(forms.ModelForm):
    """Form for adding alterations."""
    
    class Meta:
        model = Alteration
        fields = ['alteration_type', 'description', 'estimated_cost', 'estimated_days']
        widgets = {
            'alteration_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., sleeve_shorten'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estimated_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estimated_days': forms.NumberInput(attrs={'class': 'form-control'}),
        }
