"""
Orders App - Forms

Forms for order management.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Order, OrderWorkType
from customers.models import CustomerProfile
from catalog.models import GarmentType, WorkType
from measurements.models import MeasurementSet


class OrderCreateForm(forms.ModelForm):
    """Form for creating a new order."""
    
    customer = forms.ModelChoiceField(
        queryset=CustomerProfile.objects.select_related('user').all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Customer'
    )
    
    garment_type = forms.ModelChoiceField(
        queryset=GarmentType.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Garment Type'
    )
    
    work_types = forms.ModelMultipleChoiceField(
        queryset=WorkType.objects.filter(is_deleted=False),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Work Types'
    )
    
    measurement_set = forms.ModelChoiceField(
        queryset=MeasurementSet.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='Measurement Set'
    )
    
    class Meta:
        model = Order
        fields = ['customer', 'garment_type', 'expected_delivery_date', 
                  'is_urgent', 'special_instructions']
        widgets = {
            'expected_delivery_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'special_instructions': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing, populate measurement sets for customer
        if self.instance and self.instance.pk and self.instance.customer:
            self.fields['measurement_set'].queryset = MeasurementSet.objects.filter(
                customer=self.instance.customer
            )
        
        # Format customer choices
        self.fields['customer'].label_from_instance = lambda obj: (
            f"{obj.user.get_full_name() or obj.user.username} ({obj.phone_number})"
        )


class OrderEditForm(forms.ModelForm):
    """Form for editing an existing order."""
    
    class Meta:
        model = Order
        fields = ['expected_delivery_date', 'is_urgent', 'special_instructions']
        widgets = {
            'expected_delivery_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'is_urgent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'special_instructions': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }


class OrderStatusTransitionForm(forms.Form):
    """Form for transitioning order status."""
    
    new_status = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='New Status'
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False,
        label='Reason for Change'
    )
    
    def __init__(self, order, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order = order
        
        # Get valid transitions
        from .models import OrderStatusTransition
        valid_transitions = OrderStatusTransition.objects.filter(
            from_status=order.current_status
        ).select_related('to_status')
        
        choices = [(t.to_status.id, t.to_status.display_label) for t in valid_transitions]
        self.fields['new_status'].choices = choices


class OrderAssignmentForm(forms.Form):
    """Form for assigning staff to an order."""
    
    ROLE_TYPES = [
        ('tailor', 'Tailor'),
        ('delivery', 'Delivery'),
        ('designer', 'Designer'),
    ]
    
    staff = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Staff Member'
    )
    role_type = forms.ChoiceField(
        choices=ROLE_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Role'
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False,
        label='Notes'
    )
    
    def __init__(self, *args, **kwargs):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        super().__init__(*args, **kwargs)
        
        # Get staff users (non-customers)
        self.fields['staff'].queryset = User.objects.filter(
            is_active=True,
            is_deleted=False
        ).exclude(
            user_roles__role__name='customer'
        )
class OrderMaterialAllocationForm(forms.Form):
    """Form for allocating material to an order."""
    
    fabric = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Fabric'
    )
    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Quantity (meters)'
    )
    
    def __init__(self, *args, **kwargs):
        from inventory.models import Fabric
        super().__init__(*args, **kwargs)
        
        self.fields['fabric'].queryset = Fabric.objects.filter(
            is_deleted=False,
            quantity_in_stock__gt=0
        )
        self.fields['fabric'].label_from_instance = lambda f: f"{f.name} ({f.color}) - Available: {f.quantity_in_stock}m"
