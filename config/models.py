"""
Config App - Models

System configuration and pricing rules.
Maps to: config_system_configuration, config_pricing_rule tables
"""

from django.db import models
from django.conf import settings
from decimal import Decimal


class SystemConfiguration(models.Model):
    """
    System-wide configuration settings.
    
    Maps to: config_system_configuration table
    
    Singleton pattern - only one record should exist.
    """
    
    # Pricing
    default_tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('18.00')
    )
    default_advance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('50.00')
    )
    
    # Delivery
    default_delivery_days = models.PositiveIntegerField(default=7)
    
    # Inventory
    low_stock_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('5.0')
    )
    
    # Urgency
    urgency_surcharge_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00')
    )
    
    # Razorpay (encrypted in production)
    razorpay_key_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_key_secret = models.CharField(max_length=255, blank=True, null=True)
    
    # Email/SMS providers
    sms_provider = models.CharField(max_length=50, blank=True, null=True)  # 'twilio', 'aws_sns'
    email_provider = models.CharField(max_length=50, blank=True, null=True)  # 'sendgrid', 'aws_ses'
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='config_updates'
    )
    
    class Meta:
        db_table = 'config_system_configuration'
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configuration'
        indexes = [
            models.Index(fields=['updated_at'], name='idx_config_updated'),
        ]
    
    def __str__(self):
        return "System Configuration"
    
    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration."""
        config, created = cls.objects.get_or_create(pk=1)
        return config


class PricingRule(models.Model):
    """
    Dynamic pricing rules.
    
    Maps to: config_pricing_rule table
    """
    
    RULE_TYPES = [
        ('GARMENT', 'Garment-based'),
        ('WORK_TYPE', 'Work Type-based'),
        ('SEASON', 'Seasonal'),
        ('BULK', 'Bulk Order'),
    ]
    
    ADJUSTMENT_TYPES = [
        ('FIXED', 'Fixed Amount'),
        ('PERCENTAGE', 'Percentage'),
    ]
    
    rule_name = models.CharField(max_length=150)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    
    # Conditions
    garment_type = models.ForeignKey(
        'catalog.GarmentType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pricing_rules'
    )
    work_type = models.ForeignKey(
        'catalog.WorkType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pricing_rules'
    )
    season = models.CharField(max_length=50, blank=True, null=True)  # 'summer', 'winter'
    min_quantity = models.PositiveIntegerField(null=True, blank=True)  # For bulk pricing
    
    # Effect
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2)
    adjustment_type = models.CharField(
        max_length=20,
        choices=ADJUSTMENT_TYPES,
        default='FIXED'
    )
    
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_until = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pricing_rule_updates'
    )
    
    class Meta:
        db_table = 'config_pricing_rule'
        indexes = [
            models.Index(fields=['is_active'], name='idx_rule_active'),
            models.Index(fields=['effective_from'], name='idx_rule_effective'),
        ]
    
    def __str__(self):
        return f"{self.rule_name} ({self.rule_type})"
    
    def is_currently_active(self):
        """Check if rule is currently in effect."""
        import datetime
        today = datetime.date.today()
        
        if not self.is_active:
            return False
        
        if self.effective_from and today < self.effective_from:
            return False
        
        if self.effective_until and today > self.effective_until:
            return False
        
        return True
