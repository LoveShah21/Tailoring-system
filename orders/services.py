"""
Orders App - Services

Business logic for order management with state machine.
All critical operations wrapped in @transaction.atomic.
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from .models import (
    Order, OrderStatus, OrderStatusTransition, OrderStatusHistory,
    OrderWorkType, OrderAssignment, OrderMaterialAllocation
)
from audit.services import AuditService


class InvalidTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""
    pass


class OrderService:
    """Service class for order management operations."""
    
    @staticmethod
    @transaction.atomic
    def create_order(
        customer,
        garment_type,
        expected_delivery_date,
        measurement_set=None,
        design=None,
        work_types=None,
        is_urgent=False,
        special_instructions='',
        created_by=None,
        request=None
    ):
        """
        Create a new order with optional work types.
        
        Args:
            customer: CustomerProfile instance
            garment_type: GarmentType instance
            expected_delivery_date: Expected delivery date
            measurement_set: Optional MeasurementSet instance
            design: Optional Design instance
            work_types: List of WorkType instances
            is_urgent: Is this an urgent order
            special_instructions: Special instructions text
            created_by: User creating the order
            request: HTTP request for audit
        
        Returns:
            Order instance
        """
        # Get initial status (Booked)
        initial_status = OrderStatus.objects.get(status_name='booked')
        
        # Calculate urgency multiplier
        urgency_multiplier = Decimal('1.20') if is_urgent else Decimal('1.00')
        
        # Generate order number
        order_number = Order.generate_order_number()
        
        # Create order
        order = Order.objects.create(
            order_number=order_number,
            customer=customer,
            garment_type=garment_type,
            measurement_set=measurement_set,
            design=design,
            current_status=initial_status,
            expected_delivery_date=expected_delivery_date,
            is_urgent=is_urgent,
            urgency_multiplier=urgency_multiplier,
            special_instructions=special_instructions,
        )
        
        # Add work types
        if work_types:
            for wt in work_types:
                OrderWorkType.objects.create(
                    order=order,
                    work_type=wt,
                    extra_charge=wt.extra_charge
                )
        
        # Log audit
        if created_by:
            AuditService.log_activity(
                entity_type='order',
                entity_id=order.id,
                action_type='CREATE',
                performed_by=created_by,
                description=f'Order {order_number} created',
                request=request
            )
        
        # Generate Bill and Invoice
        from billing.services import BillingService
        bill = BillingService.generate_bill(order)
        BillingService.generate_invoice(bill, generated_by=created_by or customer.user)
        
        # Send notification
        from notifications.services import NotificationService
        NotificationService.notify_order_created(order)
        
        return order
    
    @staticmethod
    @transaction.atomic
    def transition_status(order, new_status, changed_by, reason=None, request=None):
        """
        Transition order to a new status with validation.
        
        Args:
            order: Order instance
            new_status: OrderStatus instance to transition to
            changed_by: User making the change
            reason: Optional reason for the transition
            request: HTTP request for audit
        
        Returns:
            Updated Order instance
        
        Raises:
            InvalidTransitionError: If transition is not allowed
        """
        old_status = order.current_status
        
        # Validate transition exists
        valid = OrderStatusTransition.objects.filter(
            from_status=old_status,
            to_status=new_status
        ).exists()
        
        if not valid:
            raise InvalidTransitionError(
                f'Cannot transition from "{old_status.display_label}" to "{new_status.display_label}"'
            )
        
        # Role-based transition restrictions
        user_roles = list(changed_by.get_roles().values_list('name', flat=True))
        from_name = old_status.status_name
        to_name = new_status.status_name
        
        # Admin can do anything
        if 'admin' not in user_roles and not changed_by.is_superuser:
            allowed = False
            
            # Tailor: fabric_allocated→stitching, stitching→trial_scheduled/ready, trial_scheduled→ready, alteration→ready
            if 'tailor' in user_roles:
                tailor_allowed = [
                    ('fabric_allocated', 'stitching'),
                    ('stitching', 'trial_scheduled'),
                    ('stitching', 'ready'),
                    ('trial_scheduled', 'ready'),
                    ('alteration', 'ready'),
                ]
                if (from_name, to_name) in tailor_allowed:
                    allowed = True
            
            # Designer: booked→fabric_allocated
            if 'designer' in user_roles:
                if (from_name, to_name) == ('booked', 'fabric_allocated'):
                    allowed = True
            
            # Delivery: ready→delivered
            if 'delivery' in user_roles:
                if (from_name, to_name) == ('ready', 'delivered'):
                    allowed = True
            
            # Staff can do same as admin
            if 'staff' in user_roles:
                allowed = True
            
            if not allowed:
                raise InvalidTransitionError(
                    f'Your role does not allow changing status from "{old_status.display_label}" to "{new_status.display_label}"'
                )
        
        # Check payment for delivered status
        if to_name == 'delivered':
            from payments.models import Payment
            has_payment = Payment.objects.filter(
                invoice__bill__order=order,
                status='COMPLETED'
            ).exists()
            if not has_payment:
                raise InvalidTransitionError(
                    'Cannot mark as delivered: Order has no completed payment. Customer must pay before delivery.'
                )
        
        # Update order status
        order.current_status = new_status
        order.save(update_fields=['current_status', 'updated_at'])
        
        # Create history entry
        OrderStatusHistory.objects.create(
            order=order,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            change_reason=reason
        )
        
        # Audit log
        AuditService.log_order_status_change(
            order=order,
            from_status=old_status.display_label,
            to_status=new_status.display_label,
            changed_by=changed_by,
            reason=reason,
            request=request
        )
        
        # Send notification
        from notifications.services import NotificationService
        NotificationService.notify_order_status_change(order, old_status, new_status)
        
        return order
    
    @staticmethod
    @transaction.atomic
    def assign_staff(order, staff, role_type, assigned_by, notes=None):
        """
        Assign staff to an order.
        
        Args:
            order: Order instance
            staff: User instance (tailor/delivery/designer)
            role_type: 'tailor', 'delivery', or 'designer'
            assigned_by: User making the assignment
            notes: Optional notes
        
        Returns:
            OrderAssignment instance
        """
        assignment = OrderAssignment.objects.create(
            order=order,
            staff=staff,
            role_type=role_type,
            assigned_by=assigned_by,
            notes=notes
        )
        
        AuditService.log_activity(
            entity_type='order',
            entity_id=order.id,
            action_type='UPDATE',
            performed_by=assigned_by,
            changes={'staff_assigned': staff.username, 'role': role_type},
            description=f'{role_type.title()} {staff.username} assigned'
        )
        
        return assignment
    
    @staticmethod
    @transaction.atomic
    def allocate_material(order, fabric, quantity_meters, allocated_by, request=None):
        """
        Allocate fabric material to an order.
        
        Args:
            order: Order instance
            fabric: Fabric instance
            quantity_meters: Quantity to allocate in meters
            allocated_by: User making the allocation
            request: HTTP request for audit
        
        Returns:
            OrderMaterialAllocation instance
        
        Raises:
            ValidationError: If insufficient stock
        """
        from inventory.services import InventoryService
        
        # Check stock availability
        if fabric.quantity_in_stock < quantity_meters:
            raise ValidationError(
                f'Insufficient stock. Available: {fabric.quantity_in_stock}m, Required: {quantity_meters}m'
            )
        
        # Create allocation
        allocation = OrderMaterialAllocation.objects.create(
            order=order,
            fabric=fabric,
            quantity_meters=quantity_meters,
            unit_cost=fabric.cost_per_meter,
            allocated_by=allocated_by
        )
        
        # Deduct from inventory
        InventoryService.record_stock_out(
            fabric=fabric,
            quantity=quantity_meters,
            order=order,
            recorded_by=allocated_by,
            notes=f'Allocated for order {order.order_number}',
            request=request
        )
        
        return allocation
    
    @staticmethod
    def get_pending_orders():
        """Get all pending (non-final) orders."""
        return Order.objects.filter(
            is_deleted=False,
            current_status__is_final_state=False
        ).order_by('expected_delivery_date')
    
    @staticmethod
    def get_overdue_orders():
        """Get all overdue orders."""
        import datetime
        today = datetime.date.today()
        return Order.objects.filter(
            is_deleted=False,
            current_status__is_final_state=False,
            expected_delivery_date__lt=today
        ).order_by('expected_delivery_date')
    
    @staticmethod
    def get_orders_by_status(status_name):
        """Get orders by status name."""
        return Order.objects.filter(
            is_deleted=False,
            current_status__status_name=status_name
        ).order_by('-created_at')
    
    @staticmethod
    def get_customer_orders(customer):
        """Get all orders for a customer."""
        return Order.objects.filter(
            customer=customer,
            is_deleted=False
        ).order_by('-created_at')
