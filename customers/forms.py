"""
Customers App - Forms

Forms for customer management.
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import CustomerProfile

User = get_user_model()


class CustomerProfileForm(forms.ModelForm):
    """Form for creating/editing customer profile."""
    
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Leave blank to keep existing password'
    )
    
    class Meta:
        model = CustomerProfile
        fields = ['phone_number', 'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add form-control class to all fields
        for field_name in ['first_name', 'last_name', 'email', 'username']:
            self.fields[field_name].widget.attrs['class'] = 'form-control'
        
        # If editing existing customer, populate user fields
        if self.instance and self.instance.pk:
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['username'].initial = user.username
            self.fields['username'].widget.attrs['readonly'] = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.instance and self.instance.pk:
            # Editing existing customer
            user = self.instance.user
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                raise forms.ValidationError('This email is already in use.')
        else:
            # Creating new customer
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('This email is already in use.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if self.instance and self.instance.pk:
            # Editing - username cannot be changed
            return self.instance.user.username
        else:
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError('This username is already taken.')
        return username
    
    def save(self, commit=True):
        if self.instance and self.instance.pk:
            # Updating existing customer
            profile = super().save(commit=commit)
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            if self.cleaned_data.get('password'):
                user.set_password(self.cleaned_data['password'])
            if commit:
                user.save()
            return profile
        else:
            # Creating new customer
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data.get('password', 'temp123!'),
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data.get('last_name', ''),
            )
            
            profile = super().save(commit=False)
            profile.user = user
            if commit:
                profile.save()
            
            # Assign customer role
            from users.models import Role, UserRole
            try:
                customer_role = Role.objects.get(name='customer')
                UserRole.objects.get_or_create(user=user, role=customer_role)
            except Role.DoesNotExist:
                pass
            
            return profile
