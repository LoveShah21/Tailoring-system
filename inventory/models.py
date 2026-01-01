"""
Inventory App - Models

Fabric inventory and stock management.
Maps to: inventory_fabric, inventory_stock_transaction, 
         inventory_low_stock_alert tables
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Fabric(models.Model):
    """
    Fabric inventory item.
    
    Maps to: inventory_fabric table
    """
    
    name = models.CharField(max_length=150)  # 'Cotton Silk Blend', 'Pure Cotton'
    color = models.CharField(max_length=100, blank=True, null=True)
    pattern = models.CharField(max_length=100, blank=True, null=True)  # 'Plain', 'Printed', 'Checkered'
    
    supplier_id = models.BigIntegerField(null=True, blank=True)  # External supplier reference
    
    cost_per_meter = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity_in_stock = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )
    reorder_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=5.0
    )
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_fabric'
        unique_together = ('name', 'color', 'pattern')
        indexes = [
            models.Index(fields=['quantity_in_stock'], name='idx_fabric_quantity'),
            models.Index(fields=['reorder_threshold'], name='idx_fabric_reorder'),
        ]
    
    def __str__(self):
        parts = [self.name]
        if self.color:
            parts.append(self.color)
        if self.pattern:
            parts.append(self.pattern)
        return ' - '.join(parts)
    
    def is_low_stock(self):
        """Check if stock is below reorder threshold."""
        return self.quantity_in_stock <= self.reorder_threshold
    
    def get_stock_value(self):
        """Calculate total value of stock."""
        return self.quantity_in_stock * self.cost_per_meter


class StockTransaction(models.Model):
    """
    Stock movement transactions.
    
    Maps to: inventory_stock_transaction table
    """
    
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Adjustment'),
        ('DAMAGE', 'Damage/Wastage'),
    ]
    
    fabric = models.ForeignKey(
        Fabric,
        on_delete=models.RESTRICT,
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity_meters = models.DecimalField(max_digits=10, decimal_places=3)
    previous_quantity = models.DecimalField(max_digits=10, decimal_places=3)
    new_quantity = models.DecimalField(max_digits=10, decimal_places=3)
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_transactions'
    )
    
    notes = models.TextField(blank=True, null=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='stock_transactions'
    )
    transaction_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_stock_transaction'
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['fabric'], name='idx_stock_tx_fabric'),
            models.Index(fields=['order'], name='idx_stock_tx_order'),
            models.Index(fields=['transaction_date'], name='idx_stock_tx_date'),
            models.Index(fields=['transaction_type'], name='idx_stock_tx_type'),
        ]
    
    def __str__(self):
        return f"{self.transaction_type}: {self.quantity_meters}m of {self.fabric.name}"


class LowStockAlert(models.Model):
    """
    Low stock alert tracking.
    
    Maps to: inventory_low_stock_alert table
    """
    
    fabric = models.OneToOneField(
        Fabric,
        on_delete=models.CASCADE,
        related_name='low_stock_alert'
    )
    alert_triggered_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'inventory_low_stock_alert'
        indexes = [
            models.Index(fields=['is_resolved'], name='idx_alert_resolved'),
        ]
    
    def __str__(self):
        status = 'Resolved' if self.is_resolved else 'Active'
        return f"Low stock alert for {self.fabric.name} ({status})"
