"""
Trials App - Models

Trials and alterations management.
Maps to: trials_trial, trials_alteration, trials_revised_delivery_date tables
"""

from django.db import models
from django.conf import settings


class Trial(models.Model):
    """
    Trial scheduling and tracking.
    
    Maps to: trials_trial table
    """
    
    LOCATION_CHOICES = [
        ('IN_SHOP', 'In Shop'),
        ('HOME', 'Home Visit'),
    ]
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('RESCHEDULED', 'Rescheduled'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='trial'
    )
    
    trial_location = models.CharField(
        max_length=20,
        choices=LOCATION_CHOICES,
        default='IN_SHOP'
    )
    trial_date = models.DateField()
    trial_time = models.TimeField(null=True, blank=True)
    
    scheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='scheduled_trials'
    )
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_trials'
    )
    
    trial_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED'
    )
    
    customer_feedback = models.TextField(blank=True, null=True)
    fit_issues = models.TextField(blank=True, null=True)  # JSON: ['sleeves_tight', 'length_short']
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trials_trial'
        indexes = [
            models.Index(fields=['order'], name='idx_trial_order'),
            models.Index(fields=['trial_date'], name='idx_trial_date'),
            models.Index(fields=['trial_status'], name='idx_trial_status'),
        ]
    
    def __str__(self):
        return f"Trial for {self.order.order_number} on {self.trial_date}"


class Alteration(models.Model):
    """
    Alterations required after trial.
    
    Maps to: trials_alteration table
    """
    
    STATUS_CHOICES = [
        ('PROPOSED', 'Proposed'),
        ('APPROVED', 'Approved'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]
    
    trial = models.ForeignKey(
        Trial,
        on_delete=models.CASCADE,
        related_name='alterations'
    )
    
    alteration_type = models.CharField(max_length=100)  # 'sleeve_shorten', 'waist_reduce'
    description = models.TextField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_days = models.PositiveIntegerField(default=3)
    is_included_in_original = models.BooleanField(default=False)  # Free vs additional charge
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PROPOSED'
    )
    completed_date = models.DateField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_alterations'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trials_alteration'
        indexes = [
            models.Index(fields=['trial'], name='idx_alteration_trial'),
            models.Index(fields=['status'], name='idx_alteration_status'),
        ]
    
    def __str__(self):
        return f"{self.alteration_type} for {self.trial.order.order_number}"


class RevisedDeliveryDate(models.Model):
    """
    Revised delivery dates after alterations.
    
    Maps to: trials_revised_delivery_date table
    """
    
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='revised_delivery'
    )
    
    original_delivery_date = models.DateField()
    revised_delivery_date = models.DateField()
    reason = models.TextField(blank=True, null=True)
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='delivery_date_updates'
    )
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trials_revised_delivery_date'
        indexes = [
            models.Index(fields=['order'], name='idx_revised_order'),
        ]
    
    def __str__(self):
        return f"{self.order.order_number}: {self.original_delivery_date} → {self.revised_delivery_date}"
