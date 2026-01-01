"""
Catalog App - Forms

Forms for catalog management.
"""

from django import forms
from .models import GarmentType, WorkType


class GarmentTypeForm(forms.ModelForm):
    """Form for creating/editing garment types."""
    
    class Meta:
        model = GarmentType
        fields = ['name', 'description', 'base_price', 'fabric_requirement_meters', 
                  'stitching_days_estimate', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fabric_requirement_meters': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stitching_days_estimate': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class WorkTypeForm(forms.ModelForm):
    """Form for creating/editing work types."""
    
    class Meta:
        model = WorkType
        fields = ['name', 'description', 'extra_charge', 'labor_hours_estimate']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'extra_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'labor_hours_estimate': forms.NumberInput(attrs={'class': 'form-control'}),
        }
