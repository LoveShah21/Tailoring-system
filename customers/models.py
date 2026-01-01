"""
Customers App - Models

Customer profile management.
Maps to: customers_customer_profile table
"""

from django.db import models
from django.conf import settings


class CustomerProfile(models.Model):
    """
    Customer profile linked to User.
    
    Maps to: customers_customer_profile table
    
    Contains:
    - Contact information
    - Address details
    - Privacy controls
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='customer_profile'
    )
    
    # Contact
    phone_number = models.CharField(max_length=20)
    
    # Address
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='India')
    
    # Privacy Controls
    allow_contact = models.BooleanField(default=True)
    allow_order_history_sharing = models.BooleanField(default=True)
    allow_recommendation = models.BooleanField(default=True)
    
    # Soft delete & timestamps
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers_customer_profile'
        indexes = [
            models.Index(fields=['phone_number'], name='idx_customer_phone'),
            models.Index(fields=['city'], name='idx_customer_city'),
            models.Index(fields=['is_deleted'], name='idx_customer_deleted'),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.phone_number}"
    
    def get_full_address(self):
        """Return formatted full address."""
        parts = [self.address_line_1]
        if self.address_line_2:
            parts.append(self.address_line_2)
        parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        parts.append(self.country)
        return ', '.join(parts)
    
    def soft_delete(self):
        """Soft delete the profile."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])
