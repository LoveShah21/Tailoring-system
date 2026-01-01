"""
Inventory App - Forms

Forms for inventory management.
"""

from django import forms
from .models import Fabric


class FabricForm(forms.ModelForm):
    """Form for creating/editing fabrics."""
    
    class Meta:
        model = Fabric
        fields = ['name', 'color', 'pattern', 'cost_per_meter', 
                  'quantity_in_stock', 'reorder_threshold']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'pattern': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_in_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost_per_meter': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reorder_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class StockInForm(forms.Form):
    """Form for recording stock in."""
    
    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Quantity in meters'})
    )
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes (optional)'})
    )


class StockOutForm(forms.Form):
    """Form for recording stock out (manual adjustment)."""
    
    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Quantity in meters'})
    )
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reason for adjustment'})
    )
