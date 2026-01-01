"""
Designs App - Forms

Forms for design management.
"""

from django import forms
from .models import Design, CustomizationNote
from orders.models import Order


class DesignForm(forms.ModelForm):
    """Form for uploading designs."""
    
    class Meta:
        model = Design
        fields = ['order', 'name', 'description']
        widgets = {
            'order': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order'].queryset = Order.objects.filter(
            is_deleted=False
        ).select_related('customer__user')[:100]
        self.fields['order'].required = False


class CustomizationNoteForm(forms.ModelForm):
    """Form for adding customization notes."""
    
    class Meta:
        model = CustomizationNote
        fields = ['note_text']
        widgets = {
            'note_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a note...'}),
        }
