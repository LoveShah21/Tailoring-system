"""
Delivery App - Models

Delivery zones and delivery tracking.
Maps to: delivery_delivery_zone, delivery_delivery tables
"""

from django.db import models
from django.conf import settings


class DeliveryZone(models.Model):
    """
    Delivery zones for logistics.
    
    Maps to: delivery_delivery_zone table
    """
    
    name = models.CharField(max_length=100, unique=True)  # 'Zone A - Downtown'
    description = models.TextField(blank=True, null=True)
    base_delivery_days = models.PositiveIntegerField(default=2)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'delivery_delivery_zone'
        indexes = [
            models.Index(fields=['is_active'], name='idx_zone_active'),
        ]
    
    def __str__(self):
        return self.name


class Delivery(models.Model):
    """
    Delivery tracking.
    
    Maps to: delivery_delivery table
    """
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_TRANSIT', 'In Transit'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed'),
        ('RESCHEDULED', 'Rescheduled'),
    ]
    
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='delivery'
    )
    delivery_zone = models.ForeignKey(
        DeliveryZone,
        on_delete=models.RESTRICT,
        related_name='deliveries'
    )
    
    scheduled_delivery_date = models.DateField()
    scheduled_delivery_time = models.TimeField(null=True, blank=True)
    
    delivery_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_deliveries'
    )
    
    delivery_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED'
    )
    
    # Manual confirmation
    delivery_confirmed_date = models.DateTimeField(null=True, blank=True)
    delivery_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_deliveries'
    )
    
    delivery_notes = models.TextField(blank=True, null=True)
    signature_url = models.CharField(max_length=500, blank=True, null=True)  # Digital signature
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'delivery_delivery'
        indexes = [
            models.Index(fields=['order'], name='idx_delivery_order'),
            models.Index(fields=['delivery_status'], name='idx_delivery_status'),
            models.Index(fields=['scheduled_delivery_date'], name='idx_delivery_date'),
        ]
    
    def __str__(self):
        return f"Delivery for {self.order.order_number}"
