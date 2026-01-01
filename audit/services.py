"""
Audit App - Services

Centralized audit logging service.
Called explicitly from service layer, not blanket logging.
"""

import json
from django.db import transaction
from .models import ActivityLog, PaymentAuditLog


def get_client_ip(request):
    """Extract client IP from request."""
    if request is None:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip[:45]


class AuditService:
    """
    Centralized audit logging service.
    
    Called explicitly from business operations.
    Decouples audit concerns from business logic.
    """
    
    @staticmethod
    @transaction.atomic
    def log_activity(entity_type, entity_id, action_type, performed_by,
                     changes=None, description=None, request=None):
        """
        Log a business-critical activity.
        
        Args:
            entity_type: Type of entity (order, payment, inventory, user)
            entity_id: ID of the entity
            action_type: Type of action (CREATE, UPDATE, DELETE, STATUS_CHANGE)
            performed_by: User who performed the action
            changes: Dict of changes (old_value, new_value)
            description: Human-readable description
            request: HTTP request object for IP/user-agent capture
        
        Returns:
            ActivityLog instance
        """
        return ActivityLog.objects.create(
            entity_type=entity_type,
            entity_id=entity_id,
            action_type=action_type,
            action_description=description,
            changes_json=json.dumps(changes) if changes else None,
            performed_by=performed_by,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
        )
    
    @staticmethod
    @transaction.atomic
    def log_order_status_change(order, from_status, to_status, changed_by, 
                                 reason=None, request=None):
        """Log an order status transition."""
        return AuditService.log_activity(
            entity_type='order',
            entity_id=order.id,
            action_type='STATUS_CHANGE',
            performed_by=changed_by,
            changes={
                'status_from': str(from_status),
                'status_to': str(to_status),
            },
            description=reason or f'Status changed from {from_status} to {to_status}',
            request=request,
        )
    
    @staticmethod
    @transaction.atomic
    def log_payment(payment, action_type, performed_by, description=None, request=None):
        """Log a payment-related activity."""
        return AuditService.log_activity(
            entity_type='payment',
            entity_id=payment.id,
            action_type=action_type,
            performed_by=performed_by,
            changes={
                'amount': str(payment.amount_paid),
                'status': payment.status,
            },
            description=description,
            request=request,
        )
    
    @staticmethod
    @transaction.atomic
    def log_payment_status_change(payment, status_before, status_after,
                                   changed_by, reason=None):
        """Log a payment status change in payment audit log."""
        return PaymentAuditLog.objects.create(
            payment=payment,
            amount=payment.amount_paid,
            status_before=status_before,
            status_after=status_after,
            change_reason=reason,
            changed_by=changed_by,
        )
    
    @staticmethod
    @transaction.atomic
    def log_inventory_transaction(fabric, transaction_type, quantity, 
                                   performed_by, request=None):
        """Log an inventory transaction."""
        return AuditService.log_activity(
            entity_type='inventory',
            entity_id=fabric.id,
            action_type='UPDATE',
            performed_by=performed_by,
            changes={
                'transaction_type': transaction_type,
                'quantity': str(quantity),
            },
            description=f'{transaction_type}: {quantity} meters',
            request=request,
        )
    
    @staticmethod
    @transaction.atomic
    def log_user_action(user_id, action_type, performed_by, 
                        description=None, request=None):
        """Log a user-related action (role assignment, etc.)."""
        return AuditService.log_activity(
            entity_type='user',
            entity_id=user_id,
            action_type=action_type,
            performed_by=performed_by,
            description=description,
            request=request,
        )
    
    @staticmethod
    def get_entity_history(entity_type, entity_id, limit=50):
        """Get activity history for an entity."""
        return ActivityLog.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by('-performed_at')[:limit]
    
    @staticmethod
    def get_user_activity(user, limit=50):
        """Get activity performed by a user."""
        return ActivityLog.objects.filter(
            performed_by=user
        ).order_by('-performed_at')[:limit]
