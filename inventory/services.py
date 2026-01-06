"""
Inventory App - Services

Business logic for inventory management.
All critical operations wrapped in @transaction.atomic.
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from .models import Fabric, StockTransaction, LowStockAlert


class InventoryService:
    """Service class for inventory management operations."""
    
    @staticmethod
    @transaction.atomic
    def create_fabric(
        name,
        color,
        pattern,
        quantity_in_stock,
        cost_per_meter,
        reorder_threshold=5.0,
        created_by=None
    ):
        """Create a new fabric in inventory."""
        previous_qty = Decimal('0')
        new_qty = Decimal(str(quantity_in_stock))
        
        fabric = Fabric.objects.create(
            name=name,
            color=color,
            pattern=pattern,
            quantity_in_stock=new_qty,
            cost_per_meter=cost_per_meter,
            reorder_threshold=reorder_threshold,
        )
        
        # Log initial stock as IN transaction
        if created_by:
            StockTransaction.objects.create(
                fabric=fabric,
                transaction_type='IN',
                quantity_meters=new_qty,
                previous_quantity=previous_qty,
                new_quantity=new_qty,
                notes='Initial stock entry',
                recorded_by=created_by,
            )
            
        # Check for low stock alert
        InventoryService._check_low_stock_alert(fabric)
        
        return fabric
    
    @staticmethod
    @transaction.atomic
    def record_stock_in(fabric, quantity, recorded_by, notes='', request=None):
        """
        Record incoming stock.
        
        Args:
            fabric: Fabric instance
            quantity: Quantity to add (in meters)
            recorded_by: User recording the transaction
            notes: Optional notes
            request: HTTP request for audit
        
        Returns:
            StockTransaction instance
        """
        previous_qty = fabric.quantity_in_stock
        quantity = Decimal(str(quantity))
        new_qty = previous_qty + quantity
        
        # Update fabric stock
        fabric.quantity_in_stock = new_qty
        fabric.save(update_fields=['quantity_in_stock', 'updated_at'])
        
        # Create transaction record
        transaction_record = StockTransaction.objects.create(
            fabric=fabric,
            transaction_type='IN',
            quantity_meters=quantity,
            previous_quantity=previous_qty,
            new_quantity=new_qty,
            notes=notes,
            recorded_by=recorded_by,
        )
        
        return transaction_record
    
    @staticmethod
    @transaction.atomic
    def record_stock_out(
        fabric, 
        quantity, 
        order=None, 
        recorded_by=None, 
        notes='',
        request=None
    ):
        """
        Record outgoing stock (allocation).
        
        Args:
            fabric: Fabric instance
            quantity: Quantity to deduct (in meters)
            order: Optional Order this is allocated to
            recorded_by: User recording the transaction
            notes: Optional notes
            request: HTTP request for audit
        
        Returns:
            StockTransaction instance
        
        Raises:
            ValidationError: If insufficient stock
        """
        quantity = Decimal(str(quantity))
        previous_qty = fabric.quantity_in_stock
        
        if previous_qty < quantity:
            raise ValidationError(
                f'Insufficient stock. Available: {previous_qty}m, Required: {quantity}m'
            )
        
        new_qty = previous_qty - quantity
        
        # Update fabric stock
        fabric.quantity_in_stock = new_qty
        fabric.save(update_fields=['quantity_in_stock', 'updated_at'])
        
        # Create transaction record
        transaction_record = StockTransaction.objects.create(
            fabric=fabric,
            transaction_type='OUT',
            quantity_meters=quantity,
            previous_quantity=previous_qty,
            new_quantity=new_qty,
            order=order,
            notes=notes,
            recorded_by=recorded_by,
        )
        
        # Check for low stock alert
        InventoryService._check_low_stock_alert(fabric)
        
        return transaction_record
    
    @staticmethod
    @transaction.atomic
    def record_damage(fabric, quantity, recorded_by, notes=''):
        """Record damaged/unusable fabric."""
        quantity = Decimal(str(quantity))
        previous_qty = fabric.quantity_in_stock
        
        if previous_qty < quantity:
            raise ValidationError('Cannot record damage greater than available stock.')
        
        new_qty = previous_qty - quantity
        
        fabric.quantity_in_stock = new_qty
        fabric.save(update_fields=['quantity_in_stock', 'updated_at'])
        
        transaction_record = StockTransaction.objects.create(
            fabric=fabric,
            transaction_type='DAMAGE',
            quantity_meters=quantity,
            previous_quantity=previous_qty,
            new_quantity=new_qty,
            notes=notes,
            recorded_by=recorded_by,
        )
        
        InventoryService._check_low_stock_alert(fabric)
        
        return transaction_record
    
    @staticmethod
    def _check_low_stock_alert(fabric):
        """Check and create/update low stock alert if needed."""
        if fabric.quantity_in_stock <= fabric.reorder_threshold:
            # Use get_or_create to handle OneToOneField constraint
            alert, created = LowStockAlert.objects.get_or_create(
                fabric=fabric,
                defaults={'is_resolved': False}
            )
            # If alert existed but was resolved, reactivate it
            if not created and alert.is_resolved:
                alert.is_resolved = False
                alert.resolved_at = None
                alert.save()
    
    @staticmethod
    def get_low_stock_fabrics():
        """Get all fabrics below reorder threshold."""
        from django.db.models import F
        return Fabric.objects.filter(
            is_deleted=False,
            quantity_in_stock__lte=F('reorder_threshold')
        ).order_by('quantity_in_stock')
    
    @staticmethod
    def get_unresolved_alerts():
        """Get all unresolved low stock alerts."""
        return LowStockAlert.objects.filter(
            is_resolved=False
        ).select_related('fabric').order_by('-alert_triggered_at')
    
    @staticmethod
    @transaction.atomic
    def resolve_alert(alert, resolved_by=None, notes=''):
        """Mark a low stock alert as resolved."""
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        return alert
    
    @staticmethod
    def get_stock_value():
        """Calculate total inventory value."""
        from django.db.models import Sum, F
        result = Fabric.objects.filter(is_deleted=False).aggregate(
            total_value=Sum(F('quantity_in_stock') * F('cost_per_meter'))
        )
        return result['total_value'] or Decimal('0.00')
