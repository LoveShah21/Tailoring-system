"""
Reporting App - Models

Analytics and reporting models.
Maps to: reporting_monthly_revenue, reporting_pending_orders_snapshot,
         reporting_staff_workload, reporting_inventory_consumption tables
"""

from django.db import models
from django.conf import settings


class MonthlyRevenue(models.Model):
    """
    Monthly revenue aggregation.
    
    Maps to: reporting_monthly_revenue table
    """
    
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField()  # 1-12
    
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    completed_orders_count = models.PositiveIntegerField()
    
    # JSON breakdowns
    by_garment_type = models.JSONField(null=True, blank=True)  # {garment_type_id: amount}
    by_work_type = models.JSONField(null=True, blank=True)  # {work_type_id: amount}
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reporting_monthly_revenue'
        unique_together = ('year', 'month')
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['year', 'month'], name='idx_revenue_year_month'),
        ]
    
    def __str__(self):
        return f"Revenue {self.year}-{self.month:02d}: ₹{self.total_revenue}"


class PendingOrdersSnapshot(models.Model):
    """
    Daily snapshot of pending orders.
    
    Maps to: reporting_pending_orders_snapshot table
    """
    
    snapshot_date = models.DateField(unique=True)
    
    total_pending = models.PositiveIntegerField()
    overdue_orders = models.PositiveIntegerField()
    pending_by_status = models.JSONField(null=True, blank=True)  # {status_id: count}
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reporting_pending_orders_snapshot'
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['snapshot_date'], name='idx_snapshot_date'),
        ]
    
    def __str__(self):
        return f"Pending Orders {self.snapshot_date}: {self.total_pending}"


class StaffWorkload(models.Model):
    """
    Staff workload metrics.
    
    Maps to: reporting_staff_workload table
    """
    
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workload_reports'
    )
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField()
    
    assigned_orders = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    pending_orders = models.PositiveIntegerField(default=0)
    average_days_per_order = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reporting_staff_workload'
        unique_together = ('staff', 'year', 'month')
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['staff'], name='idx_workload_staff'),
        ]
    
    def __str__(self):
        return f"{self.staff.username} {self.year}-{self.month:02d}"


class InventoryConsumption(models.Model):
    """
    Monthly inventory consumption tracking.
    
    Maps to: reporting_inventory_consumption table
    """
    
    fabric = models.ForeignKey(
        'inventory.Fabric',
        on_delete=models.CASCADE,
        related_name='consumption_reports'
    )
    year = models.PositiveIntegerField()
    month = models.PositiveSmallIntegerField()
    
    quantity_consumed = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    cost_of_consumption = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reporting_inventory_consumption'
        unique_together = ('fabric', 'year', 'month')
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['fabric'], name='idx_consumption_fabric'),
        ]
    
    def __str__(self):
        return f"{self.fabric.name} {self.year}-{self.month:02d}: {self.quantity_consumed}m"
