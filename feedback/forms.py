"""
Feedback App - Forms

Forms for feedback submission.
"""

from django import forms
from .models import Feedback


class FeedbackForm(forms.ModelForm):
    """Form for submitting feedback."""
    
    class Meta:
        model = Feedback
        fields = ['rating', 'comment_text', 'tailor_skill_rating', 'punctuality_rating', 'service_rating']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1, 
                'max': 5,
                'placeholder': 'Rate 1-5'
            }),
            'comment_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Share your experience...'
            }),
            'tailor_skill_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'punctuality_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'service_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }
