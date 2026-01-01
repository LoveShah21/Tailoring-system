"""
Delivery App - Forms

Forms for delivery management.
"""

from django import forms
from .models import Delivery, DeliveryZone
from orders.models import Order
from users.models import User


class DeliveryForm(forms.ModelForm):
    """Form for scheduling deliveries."""
    
    class Meta:
        model = Delivery
        fields = ['order', 'delivery_zone', 'delivery_staff', 'scheduled_delivery_date', 
                  'scheduled_delivery_time', 'delivery_notes']
        widgets = {
            'order': forms.Select(attrs={'class': 'form-select'}),
            'delivery_zone': forms.Select(attrs={'class': 'form-select'}),
            'delivery_staff': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'scheduled_delivery_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'delivery_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show orders ready for delivery
        self.fields['order'].queryset = Order.objects.filter(
            is_deleted=False,
            current_status__status_name='ready'
        ).select_related('customer__user')
        
        self.fields['delivery_zone'].queryset = DeliveryZone.objects.filter(is_active=True)
        
        # Only show delivery staff
        self.fields['delivery_staff'].queryset = User.objects.filter(
            is_active=True,
            user_roles__role__role_name='delivery'
        ).distinct()
        self.fields['delivery_staff'].required = False


class DeliveryUpdateForm(forms.ModelForm):
    """Form for updating delivery status."""
    
    class Meta:
        model = Delivery
        fields = ['delivery_status', 'delivery_notes']
        widgets = {
            'delivery_status': forms.Select(attrs={'class': 'form-select'}),
            'delivery_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
