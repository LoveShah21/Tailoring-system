"""
Orders App - Models

Order lifecycle and state machine.
Maps to: orders_order_status, orders_order_status_transition, orders_order,
         orders_order_work_type, orders_order_status_history, 
         orders_order_assignment, orders_order_material_allocation tables
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import datetime


class OrderStatus(models.Model):
    """
    Immutable order status reference table.
    
    Maps to: orders_order_status table
    
    Statuses:
    1. Booked
    2. Fabric Allocated
    3. Stitching
    4. Trial Scheduled
    5. Alteration
    6. Ready
    7. Delivered
    8. Closed
    """
    
    status_name = models.CharField(max_length=50, unique=True)
    display_label = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    sequence_order = models.PositiveIntegerField()
    is_final_state = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'orders_order_status'
        ordering = ['sequence_order']
    
    def __str__(self):
        return self.display_label


class OrderStatusTransition(models.Model):
    """
    Valid status transitions for state machine.
    
    Maps to: orders_order_status_transition table
    
    Defines which status changes are allowed.
    """
    
    from_status = models.ForeignKey(
        OrderStatus,
        on_delete=models.CASCADE,
        related_name='transitions_from'
    )
    to_status = models.ForeignKey(
        OrderStatus,
        on_delete=models.CASCADE,
        related_name='transitions_to'
    )
    allowed_roles = models.CharField(max_length=255, blank=True, null=True)  # JSON: ['tailor', 'staff', 'admin']
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'orders_order_status_transition'
        unique_together = ('from_status', 'to_status')
        indexes = [
            models.Index(fields=['from_status'], name='idx_transition_from'),
        ]
    
    def __str__(self):
        return f"{self.from_status.display_label} → {self.to_status.display_label}"


class Order(models.Model):
    """
    Main order model.
    
    Maps to: orders_order table
    """
    
    order_number = models.CharField(max_length=50, unique=True)  # 'ORD-2026-001'
    
    customer = models.ForeignKey(
        'customers.CustomerProfile',
        on_delete=models.RESTRICT,
        related_name='orders'
    )
    garment_type = models.ForeignKey(
        'catalog.GarmentType',
        on_delete=models.RESTRICT,
        related_name='orders'
    )
    
    # Measurements & Design
    measurement_set = models.ForeignKey(
        'measurements.MeasurementSet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    design = models.ForeignKey(
        'designs.Design',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_in_orders'
    )
    
    # Status & Timeline
    current_status = models.ForeignKey(
        OrderStatus,
        on_delete=models.RESTRICT,
        related_name='orders',
        default=1  # Starts at 'Booked'
    )
    expected_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    # Urgency & Special Instructions
    is_urgent = models.BooleanField(default=False)
    urgency_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('1.00')
    )
    special_instructions = models.TextField(blank=True, null=True)
    
    # Soft Delete
    is_deleted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders_order'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number'], name='idx_order_number'),
            models.Index(fields=['customer'], name='idx_order_customer'),
            models.Index(fields=['current_status'], name='idx_order_status'),
            models.Index(fields=['created_at'], name='idx_order_created'),
            models.Index(fields=['expected_delivery_date'], name='idx_order_delivery'),
            models.Index(fields=['is_deleted'], name='idx_order_deleted'),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.user.get_full_name()}"
    
    @classmethod
    def generate_order_number(cls):
        """Generate a unique order number."""
        today = timezone.now()
        prefix = f"ORD-{today.year}-"
        
        # Get the latest order number for this year
        latest = cls.objects.filter(
            order_number__startswith=prefix
        ).order_by('-order_number').first()
        
        if latest:
            try:
                last_num = int(latest.order_number.split('-')[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}{new_num:04d}"
    
    def is_overdue(self):
        """Check if order is overdue."""
        if self.current_status.is_final_state:
            return False
        return datetime.date.today() > self.expected_delivery_date
    
    def get_total_work_type_charges(self):
        """Calculate total work type charges."""
        return sum(owt.extra_charge for owt in self.order_work_types.all())
    
    def can_transition_to(self, new_status):
        """Check if transition to new status is valid."""
        return OrderStatusTransition.objects.filter(
            from_status=self.current_status,
            to_status=new_status
        ).exists()


class OrderWorkType(models.Model):
    """
    Work types applied to an order.
    
    Maps to: orders_order_work_type table
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='order_work_types'
    )
    work_type = models.ForeignKey(
        'catalog.WorkType',
        on_delete=models.RESTRICT,
        related_name='order_work_types'
    )
    extra_charge = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'orders_order_work_type'
        unique_together = ('order', 'work_type')
        indexes = [
            models.Index(fields=['order'], name='idx_order_work_order'),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.work_type.name}"


class OrderStatusHistory(models.Model):
    """
    Audit log of order status changes.
    
    Maps to: orders_order_status_history table
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    from_status = models.ForeignKey(
        OrderStatus,
        on_delete=models.RESTRICT,
        related_name='history_from'
    )
    to_status = models.ForeignKey(
        OrderStatus,
        on_delete=models.RESTRICT,
        related_name='history_to'
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='order_status_changes'
    )
    change_reason = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'orders_order_status_history'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['order'], name='idx_status_history_order'),
            models.Index(fields=['changed_at'], name='idx_status_history_date'),
        ]
    
    def __str__(self):
        return f"{self.order.order_number}: {self.from_status} → {self.to_status}"


class OrderAssignment(models.Model):
    """
    Staff assignments to orders.
    
    Maps to: orders_order_assignment table
    """
    
    ROLE_TYPES = [
        ('tailor', 'Tailor'),
        ('delivery', 'Delivery'),
        ('designer', 'Designer'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='order_assignments'
    )
    role_type = models.CharField(max_length=20, choices=ROLE_TYPES)
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='assignments_made'
    )
    completion_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'orders_order_assignment'
        indexes = [
            models.Index(fields=['order'], name='idx_assignment_order'),
            models.Index(fields=['staff'], name='idx_assignment_staff'),
            models.Index(fields=['role_type'], name='idx_assignment_role'),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.staff.get_full_name()} ({self.role_type})"


class OrderMaterialAllocation(models.Model):
    """
    Fabric allocation for orders.
    
    Maps to: orders_order_material_allocation table
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='material_allocations'
    )
    fabric = models.ForeignKey(
        'inventory.Fabric',
        on_delete=models.RESTRICT,
        related_name='order_allocations'
    )
    quantity_meters = models.DecimalField(max_digits=10, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)  # Cost snapshot at allocation
    
    allocated_at = models.DateTimeField(auto_now_add=True)
    allocated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='material_allocations'
    )
    
    class Meta:
        db_table = 'orders_order_material_allocation'
        unique_together = ('order', 'fabric')
        indexes = [
            models.Index(fields=['order'], name='idx_allocation_order'),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.fabric.name}: {self.quantity_meters}m"
    
    def get_total_cost(self):
        """Calculate total cost of this allocation."""
        return self.quantity_meters * self.unit_cost
