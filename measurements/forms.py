"""
Measurements App - Forms

Forms for measurement management.
"""

from django import forms
from django.forms import inlineformset_factory
from .models import MeasurementSet, MeasurementValue


class MeasurementSetForm(forms.ModelForm):
    """Form for measurement set metadata."""
    
    class Meta:
        model = MeasurementSet
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes...'}),
        }


class MeasurementValueForm(forms.ModelForm):
    """Form for individual measurement values."""
    
    class Meta:
        model = MeasurementValue
        fields = ['template', 'value']
        widgets = {
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }


MeasurementValueFormSet = inlineformset_factory(
    MeasurementSet,
    MeasurementValue,
    form=MeasurementValueForm,
    extra=0,
    can_delete=False,
)
